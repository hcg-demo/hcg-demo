import boto3
import zipfile
from io import BytesIO
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')
iam = boto3.client('iam', region_name='ap-southeast-1')

print("1. Updating ServiceNow Lambda...")

with open('src/lambda_servicenow_simple.py', 'rb') as f:
    code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', code)
zip_buffer.seek(0)

lambda_client.update_function_code(
    FunctionName='hcg-demo-servicenow-action',
    ZipFile=zip_buffer.read()
)
print("✅ Lambda updated")

print("\n2. Creating Action Group for IT Agent...")

# Create Action Group schema
schema = {
    "openapi": "3.0.0",
    "info": {"title": "ServiceNow API", "version": "1.0.0"},
    "paths": {
        "/create_incident": {
            "post": {
                "description": "Create a ServiceNow incident ticket",
                "parameters": [
                    {
                        "name": "short_description",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Brief description of the issue"
                    },
                    {
                        "name": "description",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Detailed description"
                    }
                ],
                "responses": {"200": {"description": "Incident created"}}
            }
        }
    }
}

try:
    bedrock.create_agent_action_group(
        agentId='ZMLHZEZZXO',
        agentVersion='DRAFT',
        actionGroupName='servicenow-actions',
        actionGroupExecutor={
            'lambda': 'arn:aws:lambda:ap-southeast-1:026138522123:function:hcg-demo-servicenow-action'
        },
        apiSchema={'payload': json.dumps(schema)},
        description='ServiceNow incident management'
    )
    print("✅ Action Group created")
except Exception as e:
    if 'ConflictException' in str(e):
        print("⚠️  Action Group already exists")
    else:
        print(f"❌ Error: {e}")

print("\n3. Preparing IT Agent...")
bedrock.prepare_agent(agentId='ZMLHZEZZXO')
print("✅ IT Agent prepared")

print("\n✅ ServiceNow integration complete!")
print("\nTest: @hcg_demo Create a ticket for password reset issue")
