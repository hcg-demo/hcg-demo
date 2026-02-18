import boto3
import json

bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

response = bedrock.invoke_agent(
    agentId='GDR3BCGCZM',
    agentAliasId='TSTALIASID',
    sessionId='test-123',
    inputText='What are the company holidays for 2025?'
)

print("Response:")
for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode('utf-8'), end='')
print()
