import boto3
import time

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

agents = {
    'DP6QVL8GPS': 'Supervisor',
    'IEVMSZT1GY': 'HR',
    'ZMLHZEZZXO': 'IT',
    '8H5G4JZVXM': 'Finance',
    'RY3QRSI7VE': 'General'
}

inference_profile = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

for agent_id, name in agents.items():
    print(f"\nUpdating {name} Agent ({agent_id})...")
    
    # Get current config
    agent = bedrock.get_agent(agentId=agent_id)
    
    # Update with inference profile
    bedrock.update_agent(
        agentId=agent_id,
        agentName=agent['agent']['agentName'],
        agentResourceRoleArn=agent['agent']['agentResourceRoleArn'],
        foundationModel=inference_profile,
        instruction=agent['agent'].get('instruction', 'You are a helpful assistant.')
    )
    print(f"✅ Updated {name} agent")
    
    # Prepare agent
    bedrock.prepare_agent(agentId=agent_id)
    print(f"✅ Preparing {name} agent...")
    
    time.sleep(2)

print("\n⏳ Wait 30 seconds for all agents to be ready...")
time.sleep(30)

print("\n✅ All agents updated! Test in Slack now.")
