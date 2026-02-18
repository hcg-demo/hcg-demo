import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

# Test supervisor with HR query
print("Testing HR query...")
response = lambda_client.invoke(
    FunctionName='hcg-demo-supervisor-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'body': json.dumps({
            'query': 'What are the company holidays for 2025?',
            'session_id': 'test-123'
        })
    })
)

result = json.loads(response['Payload'].read())
if result['statusCode'] == 200:
    data = json.loads(result['body'])
    print(f"✅ Domain: {data['domain']}")
    print(f"✅ Confidence: {data['confidence']}")
    print(f"✅ Response: {data['response'][:200]}...")
else:
    print(f"❌ Error: {result}")

print("\n" + "="*50 + "\n")

# Test IT query
print("Testing IT query...")
response = lambda_client.invoke(
    FunctionName='hcg-demo-supervisor-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'body': json.dumps({
            'query': 'How do I reset my password?',
            'session_id': 'test-456'
        })
    })
)

result = json.loads(response['Payload'].read())
if result['statusCode'] == 200:
    data = json.loads(result['body'])
    print(f"✅ Domain: {data['domain']}")
    print(f"✅ Confidence: {data['confidence']}")
    print(f"✅ Response: {data['response'][:200]}...")
else:
    print(f"❌ Error: {result}")
