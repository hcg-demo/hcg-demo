import boto3
import time

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

inference_profile = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

agents = {
    'GDR3BCGCZM': 'HR',  # New HR agent
    'ZMLHZEZZXO': 'IT',
    '8H5G4JZVXM': 'Finance',
    'RY3QRSI7VE': 'General'
}

for agent_id, name in agents.items():
    print(f"\nUpdating {name} Agent...")
    
    agent = bedrock.get_agent(agentId=agent_id)
    
    bedrock.update_agent(
        agentId=agent_id,
        agentName=agent['agent']['agentName'],
        agentResourceRoleArn=agent['agent']['agentResourceRoleArn'],
        foundationModel=inference_profile,
        instruction=agent['agent'].get('instruction', 'You are a helpful assistant.')
    )
    print(f"✅ Updated {name}")
    
    bedrock.prepare_agent(agentId=agent_id)
    print(f"✅ Preparing {name}...")
    time.sleep(3)

print("\n✅ All agents updated! Now create aliases...")

# Create test aliases for new agents
new_aliases = {}
for agent_id, name in agents.items():
    try:
        alias = bedrock.create_agent_alias(
            agentId=agent_id,
            agentAliasName=f'{name}Test',
            routingConfiguration=[{'agentVersion': 'DRAFT'}]
        )
        alias_id = alias['agentAlias']['agentAliasId']
        new_aliases[name.lower()] = {'id': agent_id, 'alias': alias_id}
        print(f"✅ {name}: {alias_id}")
    except Exception as e:
        if 'ConflictException' in str(e):
            # Get existing alias
            aliases = bedrock.list_agent_aliases(agentId=agent_id)
            alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
            new_aliases[name.lower()] = {'id': agent_id, 'alias': alias_id}
            print(f"⚠️  {name}: {alias_id} (exists)")

print(f"\n✅ Update supervisor with:")
print(new_aliases)
