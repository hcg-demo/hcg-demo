import boto3
import json
import zipfile
from io import BytesIO
import time

region = 'ap-southeast-1'
lambda_client = boto3.client('lambda', region_name=region)
iam_client = boto3.client('iam', region_name=region)

# Create IAM role
role_name = 'hcg-demo-lambda-role'
try:
    role = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {'Service': 'lambda.amazonaws.com'},
                'Action': 'sts:AssumeRole'
            }]
        })
    )
    role_arn = role['Role']['Arn']
    print(f"✅ Created role: {role_name}")
    
    # Attach policies
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockDynamoDBPolicy',
        PolicyDocument=json.dumps({
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Action': ['bedrock:*', 'dynamodb:*'],
                'Resource': '*'
            }]
        })
    )
    time.sleep(10)
except iam_client.exceptions.EntityAlreadyExistsException:
    role_arn = iam_client.get_role(RoleName=role_name)['Role']['Arn']
    print(f"⚠️  Role exists: {role_name}")

# Deploy supervisor Lambda
with open('lambda_supervisor_agent.py', 'rb') as f:
    code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', code)
zip_buffer.seek(0)

try:
    lambda_client.create_function(
        FunctionName='hcg-demo-supervisor-agent',
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=60,
        MemorySize=512
    )
    print("✅ Created: hcg-demo-supervisor-agent")
except lambda_client.exceptions.ResourceConflictException:
    print("⚠️  Exists: hcg-demo-supervisor-agent")

# Deploy evaluator Lambda
with open('llm_evaluator.py', 'rb') as f:
    code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', code)
zip_buffer.seek(0)

try:
    lambda_client.create_function(
        FunctionName='hcg-demo-llm-evaluator',
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.evaluate_response',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=60,
        MemorySize=256
    )
    print("✅ Created: hcg-demo-llm-evaluator")
except lambda_client.exceptions.ResourceConflictException:
    print("⚠️  Exists: hcg-demo-llm-evaluator")

print("\n✅ All resources deployed!")
