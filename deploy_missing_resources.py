import boto3
import json
import zipfile
from io import BytesIO

region = 'ap-southeast-1'
account_id = '026138522123'

lambda_client = boto3.client('lambda', region_name=region)
dynamodb = boto3.client('dynamodb', region_name=region)
iam_client = boto3.client('iam', region_name=region)

print("Deploying missing resources...\n")

# 1. Create DynamoDB tables
tables = [
    {'name': 'hcg-demo-conversations', 'key': 'conversation_id'},
    {'name': 'hcg-demo-user-feedback', 'key': 'feedback_id'}
]

for table in tables:
    try:
        dynamodb.create_table(
            TableName=table['name'],
            KeySchema=[{'AttributeName': table['key'], 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': table['key'], 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table['name']}")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Table exists: {table['name']}")

# 2. Get IAM role
role_arn = f"arn:aws:iam::{account_id}:role/hcg-demo-lambda-role"

# 3. Deploy supervisor Lambda
with open('lambda_supervisor_agent.py', 'rb') as f:
    supervisor_code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', supervisor_code)
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
    print("✅ Created Lambda: hcg-demo-supervisor-agent")
except lambda_client.exceptions.ResourceConflictException:
    print("⚠️  Lambda exists: hcg-demo-supervisor-agent")

# 4. Deploy evaluator Lambda
with open('llm_evaluator.py', 'rb') as f:
    evaluator_code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', evaluator_code)
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
    print("✅ Created Lambda: hcg-demo-llm-evaluator")
except lambda_client.exceptions.ResourceConflictException:
    print("⚠️  Lambda exists: hcg-demo-llm-evaluator")

print("\n✅ Deployment complete!")
