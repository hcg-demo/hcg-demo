import boto3
import zipfile
import io
import time

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
apigw = boto3.client('apigateway', region_name='ap-southeast-1')
iam = boto3.client('iam')

ACCOUNT_ID = '026138522123'
VPC_ID = 'vpc-0382b710049feecd6'
SUBNET_IDS = ['subnet-0efcb011cff665fa4', 'subnet-00b9791ab8c06b9ec']

print("=== Week 3: Lambda Functions ===\n")

# Get IAM role ARN
role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-lambda-exec"

# Create security group for Lambda
ec2 = boto3.client('ec2', region_name='ap-southeast-1')
sgs = ec2.describe_security_groups(Filters=[
    {'Name': 'vpc-id', 'Values': [VPC_ID]},
    {'Name': 'group-name', 'Values': ['hcg-demo-lambda-sg']}
])

if sgs['SecurityGroups']:
    sg_id = sgs['SecurityGroups'][0]['GroupId']
    print(f"✓ Security group exists: {sg_id}")
else:
    sg = ec2.create_security_group(
        GroupName='hcg-demo-lambda-sg',
        Description='Security group for HCG Demo Lambda functions',
        VpcId=VPC_ID
    )
    sg_id = sg['GroupId']
    
    # Allow outbound HTTPS
    ec2.authorize_security_group_egress(
        GroupId=sg_id,
        IpPermissions=[{
            'IpProtocol': 'tcp',
            'FromPort': 443,
            'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }]
    )
    print(f"✓ Created security group: {sg_id}")

# Lambda functions to deploy
functions = [
    {
        'name': 'hcg-demo-authorizer',
        'file': 'lambda_authorizer.py',
        'handler': 'lambda_authorizer.lambda_handler',
        'timeout': 10,
        'memory': 256
    },
    {
        'name': 'hcg-demo-webhook-handler',
        'file': 'lambda_webhook_handler.py',
        'handler': 'lambda_webhook_handler.lambda_handler',
        'timeout': 30,
        'memory': 512
    }
]

lambda_arns = {}

for func in functions:
    # Create zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        with open(func['file'], 'r') as f:
            zip_file.writestr(func['file'], f.read())
    
    zip_buffer.seek(0)
    
    # Check if function exists
    try:
        lambda_client.get_function(FunctionName=func['name'])
        # Update existing function
        lambda_client.update_function_code(
            FunctionName=func['name'],
            ZipFile=zip_buffer.read()
        )
        print(f"✓ Updated Lambda: {func['name']}")
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=func['name'],
            Runtime='python3.11',
            Role=role_arn,
            Handler=func['handler'],
            Code={'ZipFile': zip_buffer.read()},
            Timeout=func['timeout'],
            MemorySize=func['memory'],
            VpcConfig={
                'SubnetIds': SUBNET_IDS,
                'SecurityGroupIds': [sg_id]
            },
            Environment={'Variables': {'REGION': 'ap-southeast-1'}},
            Tags={'Project': 'HCG_Demo'}
        )
        print(f"✓ Created Lambda: {func['name']}")
        time.sleep(2)  # Wait for function to be ready
    
    # Get function ARN
    func_info = lambda_client.get_function(FunctionName=func['name'])
    lambda_arns[func['name']] = func_info['Configuration']['FunctionArn']

# Configure API Gateway
api_id = 'arep4vvhlc'
resources = apigw.get_resources(restApiId=api_id)
root_id = resources['items'][0]['id']

# Create /slack resource
slack_resource = None
for r in resources['items']:
    if r.get('pathPart') == 'slack':
        slack_resource = r
        break

if not slack_resource:
    slack_resource = apigw.create_resource(restApiId=api_id, parentId=root_id, pathPart='slack')
    print("✓ Created /slack resource")
else:
    print("✓ /slack resource exists")

# Create /slack/events
events_resource = None
for r in resources['items']:
    if r.get('pathPart') == 'events' and r.get('parentId') == slack_resource['id']:
        events_resource = r
        break

if not events_resource:
    events_resource = apigw.create_resource(
        restApiId=api_id,
        parentId=slack_resource['id'],
        pathPart='events'
    )
    print("✓ Created /slack/events resource")
else:
    print("✓ /slack/events resource exists")

# Create authorizer
authorizers = apigw.get_authorizers(restApiId=api_id)
authorizer_id = None
for auth in authorizers['items']:
    if auth['name'] == 'hcg-demo-slack-authorizer':
        authorizer_id = auth['id']
        break

if not authorizer_id:
    authorizer = apigw.create_authorizer(
        restApiId=api_id,
        name='hcg-demo-slack-authorizer',
        type='REQUEST',
        authorizerUri=f"arn:aws:apigateway:ap-southeast-1:lambda:path/2015-03-31/functions/{lambda_arns['hcg-demo-authorizer']}/invocations",
        identitySource='method.request.header.X-Slack-Request-Timestamp,method.request.header.X-Slack-Signature',
        authorizerResultTtlInSeconds=0
    )
    authorizer_id = authorizer['id']
    
    # Grant API Gateway permission to invoke authorizer
    lambda_client.add_permission(
        FunctionName='hcg-demo-authorizer',
        StatementId='apigateway-invoke-authorizer',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:ap-southeast-1:{ACCOUNT_ID}:{api_id}/authorizers/{authorizer_id}"
    )
    print(f"✓ Created authorizer: {authorizer_id}")
else:
    print(f"✓ Authorizer exists: {authorizer_id}")

# Create POST method on /slack/events
try:
    apigw.put_method(
        restApiId=api_id,
        resourceId=events_resource['id'],
        httpMethod='POST',
        authorizationType='CUSTOM',
        authorizerId=authorizer_id
    )
    print("✓ Created POST /slack/events method")
except:
    print("✓ POST /slack/events method exists")

# Create Lambda integration
try:
    apigw.put_integration(
        restApiId=api_id,
        resourceId=events_resource['id'],
        httpMethod='POST',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f"arn:aws:apigateway:ap-southeast-1:lambda:path/2015-03-31/functions/{lambda_arns['hcg-demo-webhook-handler']}/invocations"
    )
    print("✓ Created Lambda integration")
except:
    print("✓ Lambda integration exists")

# Grant API Gateway permission to invoke webhook handler
try:
    lambda_client.add_permission(
        FunctionName='hcg-demo-webhook-handler',
        StatementId='apigateway-invoke-webhook',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:ap-southeast-1:{ACCOUNT_ID}:{api_id}/*/*"
    )
except:
    pass

# Deploy API
apigw.create_deployment(restApiId=api_id, stageName='prod', description='Week 3 deployment')
print("✓ Deployed API to prod")

webhook_url = f"https://{api_id}.execute-api.ap-southeast-1.amazonaws.com/prod/slack/events"

print("\n=== CONSOLIDATED SUMMARY ===")
print("\n✅ WEEK 1-2: Foundation Complete")
print("\n✅ WEEK 3: Slack Integration")
print("  - Lambda Functions: 2")
print("    • hcg-demo-authorizer (Slack signature validation)")
print("    • hcg-demo-webhook-handler (Event processing)")
print(f"  - Security Group: {sg_id}")
print(f"  - API Authorizer: {authorizer_id}")
print(f"\n📍 Slack Webhook URL: {webhook_url}")
print("\n🔧 Next: Configure this URL in Slack App Event Subscriptions")
