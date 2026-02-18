import boto3
import time

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

# Use Claude 3 Haiku - works without inference profiles
working_model = 'anthropic.claude-3-haiku-20240307-v1:0'

agents = {
    'GDR3BCGCZM': 'HR',
    'ZMLHZEZZXO': 'IT',
    '8H5G4JZVXM': 'Finance',
    'RY3QRSI7VE': 'General'
}

for agent_id, name in agents.items():
    print(f"\nUpdating {name} Agent with working model...")
    
    agent = bedrock.get_agent(agentId=agent_id)
    
    bedrock.update_agent(
        agentId=agent_id,
        agentName=agent['agent']['agentName'],
        agentResourceRoleArn=agent['agent']['agentResourceRoleArn'],
        foundationModel=working_model,
        instruction=agent['agent'].get('instruction', 'You are a helpful assistant.')
    )
    print(f"✅ Updated {name}")
    
    bedrock.prepare_agent(agentId=agent_id)
    print(f"✅ Preparing {name}...")
    time.sleep(2)

print("\n⏳ Wait 30 seconds for all agents to be ready...")
time.sleep(30)

print("\n✅ All agents updated with working model!")
print("Test in Slack now: @hcg_demo What are the company holidays for 2025?")
