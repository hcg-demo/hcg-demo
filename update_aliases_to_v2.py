import boto3

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

aliases_to_update = {
    'IEVMSZT1GY': ('ZZTNB6K0PK', 'HRProd', 'HR'),
    'ZMLHZEZZXO': ('ZKFNRP9BFE', 'ITProd', 'IT'),
    '8H5G4JZVXM': ('YWDIOFELQQ', 'FinanceProd', 'Finance'),
    'RY3QRSI7VE': ('2PPAKMFK9T', 'GeneralProd', 'General')
}

for agent_id, (alias_id, alias_name, name) in aliases_to_update.items():
    # Get latest version
    versions = bedrock.list_agent_versions(agentId=agent_id)
    latest = max([int(v['agentVersion']) for v in versions['agentVersionSummaries'] if v['agentVersion'].isdigit()])
    
    # Update alias
    bedrock.update_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id,
        agentAliasName=alias_name,
        routingConfiguration=[{
            'agentVersion': str(latest)
        }]
    )
    print(f"✅ Updated {name} alias to version {latest}")

print("\n✅ All aliases updated to latest versions!")
