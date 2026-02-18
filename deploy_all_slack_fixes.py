"""
Deploy ALL Slack-related fixes in correct order.
Run: python deploy_all_slack_fixes.py
"""
import boto3
import zipfile
from io import BytesIO

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

def deploy(name, src_path, zip_name):
    with open(src_path, 'rb') as f:
        code = f.read()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(zip_name, code)
    buf.seek(0)
    lambda_client.update_function_code(FunctionName=name, ZipFile=buf.read())
    print(f"  OK {name}")

print("=" * 60)
print("DEPLOYING ALL SLACK FIXES")
print("=" * 60)

print("\n1. Authorizer (Slack signature + url_verification bypass)...")
deploy('hcg-demo-authorizer', 'src/lambda_authorizer.py', 'lambda_authorizer.py')

print("\n2. Webhook (sync processing, timeout 60)...")
deploy('hcg-demo-webhook-handler', 'src/lambda_webhook_handler.py', 'lambda_webhook_handler.py')

print("\n3. Supervisor (ServiceNow + sanitization)...")
deploy('hcg-demo-supervisor-agent', 'src/lambda_supervisor_agent.py', 'lambda_supervisor_agent.py')

print("\n4. ServiceNow Lambda...")
deploy('hcg-demo-servicenow-action', 'lambda_servicenow_simple.py', 'lambda_function.py')
# Ensure handler matches deployed code (was lambda_servicenow_v2, now lambda_function)
try:
    lambda_client.update_function_configuration(
        FunctionName='hcg-demo-servicenow-action',
        Handler='lambda_function.lambda_handler'
    )
    print("  OK handler -> lambda_function.lambda_handler")
except Exception as e:
    print(f"  Skip handler update: {e}")

print("\n5. Timeouts and concurrency...")
for func, timeout in [('hcg-demo-webhook-handler', 60), ('hcg-demo-supervisor-agent', 60)]:
    try:
        lambda_client.update_function_configuration(FunctionName=func, Timeout=timeout)
        print(f"  OK {func} -> {timeout}s")
    except Exception as e:
        print(f"  Skip {func}: {e}")

try:
    lambda_client.put_function_concurrency(
        FunctionName='hcg-demo-webhook-handler',
        ReservedConcurrentExecutions=50
    )
    print("  OK webhook concurrency = 50")
except Exception as e:
    print(f"  Skip concurrency: {e}")

print("\n6. ServiceNow Lambda: ensure SSM permissions (for credential fallback)...")
try:
    import subprocess
    subprocess.run(['python', 'infra/add_servicenow_ssm_permission.py'], check=False, capture_output=True, cwd='.')
    print("  OK SSM permissions")
except Exception as e:
    print(f"  Skip (run: python infra/add_servicenow_ssm_permission.py): {e}")

print("\n" + "=" * 60)
print("DONE. Verify in Slack - send: @hcg_demo Create a ticket: My laptop won't boot up")
print("Check CloudWatch for [v4-fast-ack] to confirm new webhook is deployed.")
print("If ticket creation fails: ensure credentials in Secrets Manager (hcg-demo/servicenow/creds)")
print("or SSM (/hcg-demo/servicenow/instance-url, username, password). Run infra/setup_servicenow.py")
print("=" * 60)
