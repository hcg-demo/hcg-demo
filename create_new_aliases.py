import boto3
import time

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

agents = {
    'IEVMSZT1GY': 'HR',
    'ZMLHZEZZXO': 'IT',
    '8H5G4JZVXM': 'Finance',
    'RY3QRSI7VE': 'General'
}

for agent_id, name in agents.items():
    # Create new alias pointing to DRAFT
    try:
        alias = bedrock.create_agent_alias(
            agentId=agent_id,
            agentAliasName=f'{name}WorkingAlias',
            routingConfiguration=[{
                'agentVersion': 'DRAFT'
            }]
        )
        alias_id = alias['agentAlias']['agentAliasId']
        print(f"✅ Created {name} alias: {alias_id}")
    except Exception as e:
        print(f"❌ {name}: {e}")

print("\n✅ Done! Update supervisor Lambda with new alias IDs.")
