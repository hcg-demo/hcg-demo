import boto3
import json
import time

ec2 = boto3.client('ec2', region_name='ap-southeast-1')

def check_vpc_exists():
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['hcg-demo-vpc']}])
    return vpcs['Vpcs'][0]['VpcId'] if vpcs['Vpcs'] else None

def create_vpc():
    vpc_id = check_vpc_exists()
    
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16', TagSpecifications=[{
        'ResourceType': 'vpc',
        'Tags': [{'Key': 'Name', 'Value': 'hcg-demo-vpc'}, {'Key': 'Project', 'Value': 'HCG_Demo'}]
    }])
    vpc_id = vpc['Vpc']['VpcId']
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    print(f"✓ Created VPC: {vpc_id}")
    return vpc_id

def create_igw(vpc_id):
    igws = ec2.describe_internet_gateways(Filters=[{'Name': 'tag:Name', 'Values': ['hcg-demo-igw']}])
    if igws['InternetGateways']:
        print(f"✓ IGW exists: {igws['InternetGateways'][0]['InternetGatewayId']}")
        return igws['InternetGateways'][0]['InternetGatewayId']
    
    igw = ec2.create_internet_gateway(TagSpecifications=[{
        'ResourceType': 'internet-gateway',
        'Tags': [{'Key': 'Name', 'Value': 'hcg-demo-igw'}]
    }])
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"✓ Created IGW: {igw_id}")
    return igw_id

def create_subnets(vpc_id):
    configs = [
        ('hcg-demo-public-1a', '10.0.1.0/24', 'ap-southeast-1a', True),
        ('hcg-demo-public-1b', '10.0.2.0/24', 'ap-southeast-1b', True),
        ('hcg-demo-private-1a', '10.0.10.0/24', 'ap-southeast-1a', False),
        ('hcg-demo-private-1b', '10.0.11.0/24', 'ap-southeast-1b', False),
    ]
    
    subnets = {}
    for name, cidr, az, is_public in configs:
        existing = ec2.describe_subnets(Filters=[{'Name': 'tag:Name', 'Values': [name]}])
        if existing['Subnets']:
            subnet_id = existing['Subnets'][0]['SubnetId']
            print(f"✓ Subnet exists: {name}")
        else:
            subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az,
                TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': name}]}])
            subnet_id = subnet['Subnet']['SubnetId']
            if is_public:
                ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': True})
            print(f"✓ Created subnet: {name}")
        subnets[name] = subnet_id
    
    return subnets

def create_nat_gateway(subnet_id):
    nats = ec2.describe_nat_gateways(Filters=[
        {'Name': 'tag:Name', 'Values': ['hcg-demo-nat']},
        {'Name': 'state', 'Values': ['available', 'pending']}
    ])
    if nats['NatGateways']:
        nat_id = nats['NatGateways'][0]['NatGatewayId']
        print(f"✓ NAT Gateway exists: {nat_id}")
        return nat_id
    
    eip = ec2.allocate_address(Domain='vpc', TagSpecifications=[{
        'ResourceType': 'elastic-ip', 'Tags': [{'Key': 'Name', 'Value': 'hcg-demo-nat-eip'}]
    }])
    
    nat = ec2.create_nat_gateway(SubnetId=subnet_id, AllocationId=eip['AllocationId'],
        TagSpecifications=[{'ResourceType': 'natgateway', 'Tags': [{'Key': 'Name', 'Value': 'hcg-demo-nat'}]}])
    nat_id = nat['NatGateway']['NatGatewayId']
    print(f"✓ Created NAT Gateway: {nat_id} (waiting...)")
    
    waiter = ec2.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds=[nat_id])
    print("✓ NAT Gateway available")
    return nat_id

def create_route_tables(vpc_id, igw_id, nat_id, subnets):
    # Public RT
    rts = ec2.describe_route_tables(Filters=[{'Name': 'tag:Name', 'Values': ['hcg-demo-rt-public']}])
    if rts['RouteTables']:
        public_rt_id = rts['RouteTables'][0]['RouteTableId']
        print(f"✓ Public RT exists: {public_rt_id}")
    else:
        rt = ec2.create_route_table(VpcId=vpc_id, TagSpecifications=[{
            'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'hcg-demo-rt-public'}]
        }])
        public_rt_id = rt['RouteTable']['RouteTableId']
        ec2.create_route(RouteTableId=public_rt_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
        print(f"✓ Created public RT: {public_rt_id}")
    
    for subnet_name in ['hcg-demo-public-1a', 'hcg-demo-public-1b']:
        try:
            ec2.associate_route_table(RouteTableId=public_rt_id, SubnetId=subnets[subnet_name])
        except:
            pass
    
    # Private RT
    rts = ec2.describe_route_tables(Filters=[{'Name': 'tag:Name', 'Values': ['hcg-demo-rt-private']}])
    if rts['RouteTables']:
        private_rt_id = rts['RouteTables'][0]['RouteTableId']
        print(f"✓ Private RT exists: {private_rt_id}")
    else:
        rt = ec2.create_route_table(VpcId=vpc_id, TagSpecifications=[{
            'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'hcg-demo-rt-private'}]
        }])
        private_rt_id = rt['RouteTable']['RouteTableId']
        ec2.create_route(RouteTableId=private_rt_id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_id)
        print(f"✓ Created private RT: {private_rt_id}")
    
    for subnet_name in ['hcg-demo-private-1a', 'hcg-demo-private-1b']:
        try:
            ec2.associate_route_table(RouteTableId=private_rt_id, SubnetId=subnets[subnet_name])
        except:
            pass
    
    return public_rt_id, private_rt_id

def create_vpc_endpoints(vpc_id, private_rt_id):
    # S3
    s3_eps = ec2.describe_vpc_endpoints(Filters=[
        {'Name': 'service-name', 'Values': ['com.amazonaws.ap-southeast-1.s3']},
        {'Name': 'vpc-id', 'Values': [vpc_id]}
    ])
    if not s3_eps['VpcEndpoints']:
        ec2.create_vpc_endpoint(VpcId=vpc_id, ServiceName='com.amazonaws.ap-southeast-1.s3',
            RouteTableIds=[private_rt_id], VpcEndpointType='Gateway')
        print("✓ Created S3 endpoint")
    else:
        print("✓ S3 endpoint exists")
    
    # DynamoDB
    ddb_eps = ec2.describe_vpc_endpoints(Filters=[
        {'Name': 'service-name', 'Values': ['com.amazonaws.ap-southeast-1.dynamodb']},
        {'Name': 'vpc-id', 'Values': [vpc_id]}
    ])
    if not ddb_eps['VpcEndpoints']:
        ec2.create_vpc_endpoint(VpcId=vpc_id, ServiceName='com.amazonaws.ap-southeast-1.dynamodb',
            RouteTableIds=[private_rt_id], VpcEndpointType='Gateway')
        print("✓ Created DynamoDB endpoint")
    else:
        print("✓ DynamoDB endpoint exists")

print("=== Day 1-2: VPC & Networking ===\n")

vpc_id = create_vpc()
igw_id = create_igw(vpc_id)
subnets = create_subnets(vpc_id)
nat_id = create_nat_gateway(subnets['hcg-demo-public-1a'])
public_rt, private_rt = create_route_tables(vpc_id, igw_id, nat_id, subnets)
create_vpc_endpoints(vpc_id, private_rt)

print("\n=== SUMMARY: VPC Infrastructure ===")
print(f"VPC: {vpc_id}")
print(f"NAT Gateway: {nat_id}")
print(f"Subnets: {len(subnets)} created")
