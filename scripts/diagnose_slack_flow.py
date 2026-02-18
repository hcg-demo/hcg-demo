"""
Diagnose Slack flow - run to find where it breaks.
Usage: python diagnose_slack_flow.py
"""
import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

# Test queries - the ones that fail
TEST_QUERIES = [
    "Create a ticket: My laptop won't boot up",
    "Create a ticket: My mouse is not working",
    "What are the company holidays for 2025?",
]

print("=" * 70)
print("DIAGNOSING SLACK FLOW")
print("=" * 70)

for query in TEST_QUERIES:
    print(f"\n--- Testing: '{query[:50]}...' ---")
    try:
        # 1. Invoke supervisor directly (same as webhook does)
        payload = {
            'body': json.dumps({
                'query': query,
                'session_id': 'diagnose_test_session'
            })
        }
        response = lambda_client.invoke(
            FunctionName='hcg-demo-supervisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        result = json.loads(response['Payload'].read())
        
        print(f"  Supervisor status: {result.get('statusCode')}")
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            resp_text = body.get('response', '')[:100]
            print(f"  Response: {resp_text}...")
        else:
            print(f"  Error body: {result.get('body', '')[:200]}")
            
    except Exception as e:
        print(f"  FAILED: {e}")

# 2. Invoke ServiceNow Lambda directly
print("\n" + "=" * 70)
print("Testing ServiceNow Lambda directly")
print("=" * 70)
for desc in ["My mouse is not working", "My laptop won't boot up"]:
    print(f"\n--- ServiceNow: '{desc}' ---")
    try:
        payload = {
            'actionGroup': 'ServiceNowActions',
            'apiPath': '/create_incident',
            'parameters': [
                {'name': 'short_description', 'value': desc[:100]},
                {'name': 'description', 'value': desc}
            ]
        }
        response = lambda_client.invoke(
            FunctionName='hcg-demo-servicenow-action',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        result = json.loads(response['Payload'].read())
        resp = result.get('response', {})
        print(f"  HTTP Status: {resp.get('httpStatusCode')}")
        print(f"  Body: {resp.get('responseBody', {})}")
    except Exception as e:
        print(f"  FAILED: {e}")

# 3. Check webhook Lambda config
print("\n" + "=" * 70)
print("Webhook Lambda Configuration")
print("=" * 70)
try:
    cfg = lambda_client.get_function_configuration(FunctionName='hcg-demo-webhook-handler')
    print(f"  Timeout: {cfg.get('Timeout')} sec")
    print(f"  Handler: {cfg.get('Handler')}")
    concurrency = lambda_client.get_function_concurrency(FunctionName='hcg-demo-webhook-handler')
    print(f"  Reserved concurrency: {concurrency.get('ReservedConcurrentExecutions', 'unreserved')}")
except Exception as e:
    print(f"  {e}")

# 4. Invoke webhook with test event (will fail to post - need real channel - but shows if it runs)
print("\n" + "=" * 70)
print("Invoking Webhook Lambda (simulated Slack event)")
print("=" * 70)
test_event = {
    "body": json.dumps({
        "type": "event_callback",
        "event_id": "EvDiagnoseTest" + str(__import__('time').time()),
        "event": {
            "type": "app_mention",
            "user": "U123",
            "text": "<@BOT123> Create a ticket: My laptop won't boot up",
            "ts": "1234567890.123",
            "channel": "C123",
            "channel_type": "channel"
        }
    })
}
try:
    import time as t
    start = t.time()
    response = lambda_client.invoke(
        FunctionName='hcg-demo-webhook-handler',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    elapsed = t.time() - start
    result = json.loads(response['Payload'].read())
    print(f"  Completed in {elapsed:.1f} sec (timeout is 30 - may have been killed)")
    print(f"  Status: {result.get('statusCode')}")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n" + "=" * 70)
print("RECOMMENDATION: Webhook timeout is 30 sec but supervisor takes ~25 sec.")
print("Run: python scripts/infra/ensure_webhook_concurrency.py")
print("     (Sets timeout to 60 sec)")
print("=" * 70)
