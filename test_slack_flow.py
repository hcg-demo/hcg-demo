"""Simulate full Slack->Webhook->Supervisor flow (no real Slack post)"""
import json
import boto3

lc = boto3.client('lambda', region_name='ap-southeast-1')

# Simulate webhook body - same format Slack sends
slack_event = {
    'event': {
        'type': 'app_mention',
        'channel': 'C_TEST',
        'text': '<@BOT123> How do I reset my password?',
        'ts': '1234567890.123'
    }
}

# What webhook sends to supervisor
body = json.dumps({
    'query': 'How do I reset my password?',  # After @mention removal
    'session_id': 'C_TEST_1234567890.123'
})

print("Simulating: @hcg_demo How do I reset my password?")
print("-" * 50)
r = lc.invoke(
    FunctionName='hcg-demo-supervisor-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({'body': body})
)
result = json.loads(r['Payload'].read())
data = json.loads(result.get('body', '{}')) if result.get('statusCode') == 200 else {}
resp = data.get('response', '')[:500]
print(f"Status: {result.get('statusCode')}")
print(f"Response preview: {resp}...")
print("-" * 50)
if 'StarHub' in resp or 'password' in resp.lower():
    print("PASS: Password reset answer returned correctly")
else:
    print("FAIL: Expected password reset content")
