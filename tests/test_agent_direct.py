import boto3
import json

bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

response = bedrock.invoke_agent(
    agentId='DP6QVL8GPS',
    agentAliasId='TSTALIASID',
    sessionId='test-session-001',
    inputText='What are the company holidays for 2025?'
)

print("Agent Response:")
for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode('utf-8'), end='')
