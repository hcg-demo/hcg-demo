"""
Deploy fixes for Slack no-response issue (KB + ServiceNow flows).
Run: python deploy_slack_fixes.py
"""
import boto3
import zipfile
from io import BytesIO

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

def deploy_lambda(name, source_file, zip_name):
    with open(source_file, 'rb') as f:
        code = f.read()
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(zip_name, code)
    zip_buffer.seek(0)
    lambda_client.update_function_code(FunctionName=name, ZipFile=zip_buffer.read())
    print(f"✅ Updated {name}")

print("Deploying Slack/Agent fixes...\n")

# 1. Webhook handler (async fallback + robust parsing)
deploy_lambda('hcg-demo-webhook-handler', 'src/lambda_webhook_handler.py', 'lambda_webhook_handler.py')

# 2. Supervisor (ServiceNow payload + response parsing)
deploy_lambda('hcg-demo-supervisor-agent', 'src/lambda_supervisor_agent.py', 'lambda_function.py')

# 3. ServiceNow Lambda (accept both apiPath formats)
deploy_lambda('hcg-demo-servicenow-action', 'lambda_servicenow_simple.py', 'lambda_function.py')

print("\n5. Run to ensure concurrency & timeout: python infra/ensure_webhook_concurrency.py")
print("\n✅ Deployments complete. Test in Slack:")
print("   @hcg_demo What are the company holidays for 2025?")
print("   @hcg_demo How do I reset my password?")
print("   @hcg_demo Create a ticket: My laptop won't boot up")
