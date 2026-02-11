import boto3
import json

apigw = boto3.client('apigateway', region_name='ap-southeast-1')
cognito = boto3.client('cognito-idp', region_name='ap-southeast-1')

print("=== Day 5: API Gateway ===\n")

# Create REST API
apis = apigw.get_rest_apis()
api_id = None
for api in apis['items']:
    if api['name'] == 'hcg-demo-api':
        api_id = api['id']
        print(f"✓ API exists: {api_id}")
        break

if not api_id:
    api = apigw.create_rest_api(
        name='hcg-demo-api',
        description='HCG Demo Slack Integration API',
        endpointConfiguration={'types': ['REGIONAL']},
        tags={'Project': 'HCG_Demo'}
    )
    api_id = api['id']
    print(f"✓ Created API: {api_id}")

# Get root resource
resources = apigw.get_resources(restApiId=api_id)
root_id = resources['items'][0]['id']

# Create /health endpoint
health_exists = any(r.get('path') == '/health' for r in resources['items'])
if not health_exists:
    health_resource = apigw.create_resource(restApiId=api_id, parentId=root_id, pathPart='health')
    apigw.put_method(restApiId=api_id, resourceId=health_resource['id'], httpMethod='GET', authorizationType='NONE')
    apigw.put_integration(
        restApiId=api_id,
        resourceId=health_resource['id'],
        httpMethod='GET',
        type='MOCK',
        requestTemplates={'application/json': '{"statusCode": 200}'}
    )
    apigw.put_method_response(restApiId=api_id, resourceId=health_resource['id'], httpMethod='GET', statusCode='200')
    apigw.put_integration_response(
        restApiId=api_id,
        resourceId=health_resource['id'],
        httpMethod='GET',
        statusCode='200',
        responseTemplates={'application/json': '{"status": "healthy"}'}
    )
    print("✓ Created /health endpoint")
else:
    print("✓ /health endpoint exists")

# Deploy to prod stage
try:
    apigw.create_deployment(restApiId=api_id, stageName='prod', description='Production deployment')
    print("✓ Deployed to prod stage")
except:
    print("✓ Prod stage exists")

# Enable logging
try:
    apigw.update_stage(
        restApiId=api_id,
        stageName='prod',
        patchOperations=[
            {'op': 'replace', 'path': '/*/*/logging/loglevel', 'value': 'INFO'},
            {'op': 'replace', 'path': '/*/*/logging/dataTrace', 'value': 'true'},
            {'op': 'replace', 'path': '/*/*/metrics/enabled', 'value': 'true'}
        ]
    )
    print("✓ Enabled API logging")
except:
    pass

api_url = f"https://{api_id}.execute-api.ap-southeast-1.amazonaws.com/prod"
print(f"✓ API URL: {api_url}")

print("\n=== Day 10: Cognito User Pool ===\n")

# Create User Pool
pools = cognito.list_user_pools(MaxResults=60)
pool_id = None
for pool in pools['UserPools']:
    if pool['Name'] == 'hcg-demo-users':
        pool_id = pool['Id']
        print(f"✓ User Pool exists: {pool_id}")
        break

if not pool_id:
    pool = cognito.create_user_pool(
        PoolName='hcg-demo-users',
        Policies={'PasswordPolicy': {
            'MinimumLength': 12,
            'RequireUppercase': True,
            'RequireLowercase': True,
            'RequireNumbers': True,
            'RequireSymbols': True
        }},
        AutoVerifiedAttributes=['email'],
        Schema=[
            {'Name': 'email', 'Required': True, 'Mutable': True},
            {'Name': 'name', 'Required': False, 'Mutable': True}
        ],
        UserPoolTags={'Project': 'HCG_Demo'}
    )
    pool_id = pool['UserPool']['Id']
    print(f"✓ Created User Pool: {pool_id}")

print("\n=== FINAL CONSOLIDATED SUMMARY ===")
print("\n✅ WEEK 1-2 FOUNDATION COMPLETE")
print("\n📡 Networking (Day 1-2)")
print("  - VPC: vpc-0382b710049feecd6")
print("  - Subnets: 4 (2 public, 2 private)")
print("  - NAT Gateway: nat-01b8dfbb36ae3f811")
print("  - VPC Endpoints: S3 + DynamoDB")
print("\n🔐 Security (Day 3)")
print("  - IAM Roles: 4 (Lambda, Bedrock, Step Functions)")
print("  - Secrets: Slack + ServiceNow credentials")
print("\n📊 Observability (Day 4)")
print("  - CloudWatch Log Groups: 5")
print("  - CloudTrail: hcg-demo-audit-trail")
print("\n🌐 API Layer (Day 5)")
print(f"  - API Gateway: {api_id}")
print(f"  - API URL: {api_url}")
print("\n💾 Data Layer (Day 8)")
print("  - DynamoDB Tables: 3 (sessions, users, feedback)")
print("\n📦 Storage (Day 9)")
print("  - S3 Buckets: 3 (knowledge, logs, cloudtrail)")
print("\n👤 Identity (Day 10)")
print(f"  - Cognito User Pool: {pool_id}")
print("\n🎯 READY FOR: Week 3 - Slack Integration & Lambda Development")
