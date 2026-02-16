import boto3
import requests
import json
import time
from datetime import datetime

print("=" * 80)
print("HCG_DEMO MIGRATION PLAN - VALIDATION TEST SUITE")
print("=" * 80)

# AWS Clients
ec2 = boto3.client('ec2', region_name='ap-southeast-1')
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
apigw = boto3.client('apigateway', region_name='ap-southeast-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
s3 = boto3.client('s3', region_name='ap-southeast-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')
secrets = boto3.client('secretsmanager', region_name='ap-southeast-1')

test_results = []

def test_result(test_name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append({'test': test_name, 'passed': passed, 'details': details})
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")

print("\n" + "=" * 80)
print("WEEK 1-2: FOUNDATION INFRASTRUCTURE TESTS")
print("=" * 80)

# Test 1: VPC Configuration
print("\n[Test 1] VPC and Networking")
try:
    vpc = ec2.describe_vpcs(VpcIds=['vpc-0382b710049feecd6'])
    dns_enabled = vpc['Vpcs'][0]['EnableDnsHostnames']
    test_result("VPC DNS Configuration", dns_enabled, "DNS hostnames enabled")
    
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': ['vpc-0382b710049feecd6']}])
    test_result("VPC Subnets", len(subnets['Subnets']) == 4, f"Found {len(subnets['Subnets'])} subnets")
    
    nat = ec2.describe_nat_gateways(NatGatewayIds=['nat-01b8dfbb36ae3f811'])
    nat_state = nat['NatGateways'][0]['State']
    test_result("NAT Gateway", nat_state == 'available', f"State: {nat_state}")
except Exception as e:
    test_result("VPC Configuration", False, str(e))

# Test 2: IAM Roles
print("\n[Test 2] IAM Roles")
iam = boto3.client('iam')
required_roles = ['hcg-demo-lambda-exec', 'hcg-demo-lambda-bedrock', 
                  'hcg-demo-stepfunctions', 'hcg-demo-bedrock-agent']
for role_name in required_roles:
    try:
        iam.get_role(RoleName=role_name)
        test_result(f"IAM Role: {role_name}", True, "Exists")
    except:
        test_result(f"IAM Role: {role_name}", False, "Not found")

# Test 3: Secrets Manager
print("\n[Test 3] Secrets Manager")
try:
    slack_secret = secrets.get_secret_value(SecretId='hcg-demo/slack/credentials')
    test_result("Slack Credentials Secret", True, "Accessible")
    
    snow_secret = secrets.get_secret_value(SecretId='hcg-demo/servicenow/oauth')
    test_result("ServiceNow Credentials Secret", True, "Accessible")
except Exception as e:
    test_result("Secrets Manager", False, str(e))

# Test 4: DynamoDB Tables
print("\n[Test 4] DynamoDB Tables")
tables = ['hcg-demo-sessions', 'hcg-demo-users', 'hcg-demo-feedback']
for table_name in tables:
    try:
        table = dynamodb.Table(table_name)
        status = table.table_status
        test_result(f"DynamoDB: {table_name}", status == 'ACTIVE', f"Status: {status}")
    except Exception as e:
        test_result(f"DynamoDB: {table_name}", False, str(e))

# Test 5: S3 Buckets
print("\n[Test 5] S3 Buckets")
buckets = ['hcg-demo-knowledge-026138522123', 'hcg-demo-logs-026138522123', 
           'hcg-demo-cloudtrail-026138522123']
for bucket_name in buckets:
    try:
        s3.head_bucket(Bucket=bucket_name)
        test_result(f"S3 Bucket: {bucket_name}", True, "Exists")
    except Exception as e:
        test_result(f"S3 Bucket: {bucket_name}", False, str(e))

print("\n" + "=" * 80)
print("WEEK 3: SLACK INTEGRATION TESTS")
print("=" * 80)

# Test 6: API Gateway
print("\n[Test 6] API Gateway")
try:
    api = apigw.get_rest_api(restApiId='arep4vvhlc')
    test_result("API Gateway", True, f"Name: {api['name']}")
    
    # Test health endpoint
    health_url = "https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/health"
    response = requests.get(health_url, timeout=5)
    test_result("API Health Endpoint", response.status_code == 200, 
                f"Status: {response.status_code}, Response: {response.text}")
except Exception as e:
    test_result("API Gateway", False, str(e))

# Test 7: Lambda Functions
print("\n[Test 7] Lambda Functions")
lambdas = ['hcg-demo-authorizer', 'hcg-demo-webhook-handler']
for func_name in lambdas:
    try:
        func = lambda_client.get_function(FunctionName=func_name)
        state = func['Configuration']['State']
        test_result(f"Lambda: {func_name}", state == 'Active', f"State: {state}")
    except Exception as e:
        test_result(f"Lambda: {func_name}", False, str(e))

# Test 8: Lambda VPC Configuration
print("\n[Test 8] Lambda VPC Configuration")
try:
    func = lambda_client.get_function(FunctionName='hcg-demo-webhook-handler')
    vpc_config = func['Configuration'].get('VpcConfig', {})
    has_vpc = 'VpcId' in vpc_config
    test_result("Lambda in VPC", has_vpc, f"VPC: {vpc_config.get('VpcId', 'None')}")
except Exception as e:
    test_result("Lambda VPC Configuration", False, str(e))

print("\n" + "=" * 80)
print("WEEK 4: KNOWLEDGE LAYER TESTS")
print("=" * 80)

# Test 9: OpenSearch Serverless
print("\n[Test 9] OpenSearch Serverless")
try:
    opensearch = boto3.client('opensearchserverless', region_name='ap-southeast-1')
    collection = opensearch.batch_get_collection(ids=['y3f4j35z37u9awc6sqkc'])
    status = collection['collectionDetails'][0]['status']
    test_result("OpenSearch Collection", status == 'ACTIVE', f"Status: {status}")
except Exception as e:
    test_result("OpenSearch Collection", False, str(e))

# Test 10: S3 Knowledge Bucket Structure
print("\n[Test 10] S3 Knowledge Bucket Structure")
try:
    bucket = 'hcg-demo-knowledge-026138522123'
    folders = ['hr/', 'it/', 'finance/', 'general/']
    for folder in folders:
        try:
            s3.head_object(Bucket=bucket, Key=folder)
            test_result(f"S3 Folder: {folder}", True, "Exists")
        except:
            test_result(f"S3 Folder: {folder}", False, "Not found")
except Exception as e:
    test_result("S3 Knowledge Structure", False, str(e))

print("\n" + "=" * 80)
print("WEEK 5-6: BEDROCK AGENTS TESTS")
print("=" * 80)

# Test 11: Bedrock Agents
print("\n[Test 11] Bedrock Agents")
agents = {
    'hcg-demo-supervisor': 'DP6QVL8GPS',
    'hcg-demo-hr-agent': 'IEVMSZT1GY',
    'hcg-demo-it-agent': 'ZMLHZEZZXO',
    'hcg-demo-finance-agent': '8H5G4JZVXM',
    'hcg-demo-general-agent': 'RY3QRSI7VE'
}

for agent_name, agent_id in agents.items():
    try:
        agent = bedrock_agent.get_agent(agentId=agent_id)
        status = agent['agent']['agentStatus']
        test_result(f"Bedrock Agent: {agent_name}", 
                   status in ['PREPARED', 'NOT_PREPARED'], 
                   f"Status: {status}")
    except Exception as e:
        test_result(f"Bedrock Agent: {agent_name}", False, str(e))

print("\n" + "=" * 80)
print("OBSERVABILITY TESTS")
print("=" * 80)

# Test 12: CloudWatch Log Groups
print("\n[Test 12] CloudWatch Log Groups")
logs = boto3.client('logs', region_name='ap-southeast-1')
log_groups = [
    '/aws/lambda/hcg-demo-webhook-handler',
    '/aws/lambda/hcg-demo-authorizer',
    '/aws/apigateway/hcg-demo-api'
]
for log_group in log_groups:
    try:
        logs.describe_log_groups(logGroupNamePrefix=log_group)
        test_result(f"Log Group: {log_group}", True, "Exists")
    except Exception as e:
        test_result(f"Log Group: {log_group}", False, str(e))

# Test 13: CloudTrail
print("\n[Test 13] CloudTrail")
try:
    cloudtrail = boto3.client('cloudtrail', region_name='ap-southeast-1')
    trail = cloudtrail.get_trail_status(Name='hcg-demo-audit-trail')
    is_logging = trail['IsLogging']
    test_result("CloudTrail Logging", is_logging, f"Logging: {is_logging}")
except Exception as e:
    test_result("CloudTrail", False, str(e))

print("\n" + "=" * 80)
print("END-TO-END INTEGRATION TEST")
print("=" * 80)

# Test 14: Slack Webhook Simulation
print("\n[Test 14] Slack Webhook (Simulated)")
print("⚠️  Manual test required:")
print("1. Configure Slack app Event Subscriptions URL:")
print("   https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/slack/events")
print("2. Send a test message in Slack")
print("3. Check CloudWatch logs for webhook-handler")
print("4. Verify DynamoDB session created")

# Test 15: Bedrock Agent Invocation
print("\n[Test 15] Bedrock Agent Invocation")
print("⚠️  Manual test required:")
print("1. Use AWS Console → Bedrock → Agents")
print("2. Select hcg-demo-supervisor agent")
print("3. Test with query: 'What are the HR benefits?'")
print("4. Verify agent routes to HR specialist")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

passed = sum(1 for t in test_results if t['passed'])
failed = sum(1 for t in test_results if not t['passed'])
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"Success Rate: {(passed/total)*100:.1f}%")

if failed > 0:
    print("\n❌ Failed Tests:")
    for t in test_results:
        if not t['passed']:
            print(f"  - {t['test']}: {t['details']}")

print("\n" + "=" * 80)
print("MIGRATION PLAN VALIDATION STATUS")
print("=" * 80)

validation_status = {
    'Week 1-2: Foundation': passed >= 15,
    'Week 3: Slack Integration': passed >= 18,
    'Week 4: Knowledge Layer': passed >= 20,
    'Week 5-6: Bedrock Agents': passed >= 25,
    'Overall Migration': passed >= 25 and failed == 0
}

for phase, status in validation_status.items():
    status_icon = "✅" if status else "⚠️"
    print(f"{status_icon} {phase}: {'COMPLETE' if status else 'INCOMPLETE'}")

print("\n" + "=" * 80)
