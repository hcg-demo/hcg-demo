"""Test password reset and ticket response"""
import boto3
import json

lc = boto3.client('lambda', region_name='ap-southeast-1')

# Test 1: Password reset
print("1. Password reset query...")
r1 = lc.invoke(
    FunctionName='hcg-demo-supervisor-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({'body': json.dumps({'query': 'How do I reset my password?', 'session_id': 'test1'})})
)
d1 = json.loads(r1['Payload'].read())
body1 = json.loads(d1.get('body', '{}')) if d1.get('statusCode') == 200 else {}
print(f"   Status: {d1.get('statusCode')}")
print(f"   Response: {(body1.get('response') or '')[:300]}")

# Test 2: ServiceNow - raw response
print("\n2. ServiceNow Lambda direct invoke...")
r2 = lc.invoke(
    FunctionName='hcg-demo-servicenow-action',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'actionGroup': 'S',
        'apiPath': '/create_incident',
        'parameters': [
            {'name': 'short_description', 'value': 'Test ticket'},
            {'name': 'description', 'value': 'Laptop boot test'}
        ]
    })
)
d2 = json.loads(r2['Payload'].read())
print("   Raw response:", json.dumps(d2, indent=2)[:600])
