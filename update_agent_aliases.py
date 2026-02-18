import boto3

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

agents = {
    'IEVMSZT1GY': ('TSTALIASID', 'HR'),
    'ZMLHZEZZXO': ('BFBSNUNZUA', 'IT'),
    '8H5G4JZVXM': ('1ZFUCWCS1K', 'Finance'),
    'RY3QRSI7VE': ('9CP8PGSKFQ', 'General')
}

for agent_id, (alias_id, name) in agents.items():
    # Get alias name
    alias_info = bedrock.get_agent_alias(agentId=agent_id, agentAliasId=alias_id)
    alias_name = alias_info['agentAlias']['agentAliasName']
    
    # Get latest agent version
    versions = bedrock.list_agent_versions(agentId=agent_id, maxResults=10)
    latest = max([int(v['agentVersion']) for v in versions['agentVersionSummaries'] if v['agentVersion'].isdigit()])
    
    # Update alias to point to latest version
    bedrock.update_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id,
        agentAliasName=alias_name,
        routingConfiguration=[{
            'agentVersion': str(latest)
        }]
    )
    print(f"✅ Updated {name} alias to version {latest}")

print("\n✅ All aliases updated! Test now in Slack.")
