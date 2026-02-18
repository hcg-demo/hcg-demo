"""Ensure webhook Lambda can handle concurrent requests (fix: mouse works, laptop fails)."""
import boto3

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

try:
    lambda_client.put_function_concurrency(
        FunctionName='hcg-demo-webhook-handler',
        ReservedConcurrentExecutions=50
    )
    print("✅ hcg-demo-webhook-handler: Reserved 50 concurrent executions")
except Exception as e:
    print(f"⚠️  {e}")

# Also ensure supervisor has enough timeout (Bedrock can take 30+ sec)
try:
    lambda_client.update_function_configuration(
        FunctionName='hcg-demo-supervisor-agent',
        Timeout=60
    )
    print("✅ hcg-demo-supervisor-agent: Timeout set to 60 seconds")
except Exception as e:
    print(f"⚠️  Supervisor timeout: {e}")

# Webhook needs 60 sec too for sync processing
try:
    lambda_client.update_function_configuration(
        FunctionName='hcg-demo-webhook-handler',
        Timeout=60
    )
    print("✅ hcg-demo-webhook-handler: Timeout set to 60 seconds")
except Exception as e:
    print(f"⚠️  Webhook timeout: {e}")
