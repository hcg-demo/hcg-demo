import boto3

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

agents = {
    'IEVMSZT1GY': 'HR',
    'ZMLHZEZZXO': 'IT',
    '8H5G4JZVXM': 'Finance',
    'RY3QRSI7VE': 'General'
}

new_aliases = {}

for agent_id, name in agents.items():
    # Prepare agent (creates a version)
    bedrock.prepare_agent(agentId=agent_id)
    print(f"✅ Prepared {name} agent")
    
    # Get latest version
    versions = bedrock.list_agent_versions(agentId=agent_id)
    version_num = max([int(v['agentVersion']) for v in versions['agentVersionSummaries'] if v['agentVersion'].isdigit()])
    print(f"✅ Latest {name} version: {version_num}")
    
    # Create alias pointing to this version
    alias = bedrock.create_agent_alias(
        agentId=agent_id,
        agentAliasName=f'{name}Prod',
        routingConfiguration=[{
            'agentVersion': str(version_num)
        }]
    )
    alias_id = alias['agentAlias']['agentAliasId']
    new_aliases[name.lower()] = alias_id
    print(f"✅ Created {name} alias: {alias_id}\n")

print(f"\n✅ Update supervisor with these aliases:")
print(new_aliases)
