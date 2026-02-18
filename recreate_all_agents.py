import boto3
import time

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')
iam = boto3.client('iam', region_name='ap-southeast-1')

role_arn = 'arn:aws:iam::026138522123:role/hcg-demo-bedrock-agent'

inference_profile = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

agents_config = [
    {
        'name': 'hcg-demo-hr-agent',
        'instruction': 'You are an HR specialist. Answer questions about company holidays, leave policies, benefits, and HR procedures. Search the knowledge base for accurate information.',
        'kb_id': 'H0LFPBHIAK',
        'old_id': 'IEVMSZT1GY'
    },
    {
        'name': 'hcg-demo-it-agent',
        'instruction': 'You are an IT support specialist. Help with password resets, VPN access, laptop issues, and software installation. Search the knowledge base for IT procedures.',
        'kb_id': 'X1VW7AMIK8',
        'old_id': 'ZMLHZEZZXO'
    },
    {
        'name': 'hcg-demo-finance-agent',
        'instruction': 'You are a Finance specialist. Help with expense claims, reimbursements, procurement, and finance policies. Search the knowledge base for finance information.',
        'kb_id': '1MFT5GZYTT',
        'old_id': '8H5G4JZVXM'
    },
    {
        'name': 'hcg-demo-general-agent',
        'instruction': 'You are a general company assistant. Help with office locations, company policies, and general inquiries. Search the knowledge base for information.',
        'kb_id': 'BOLGBDCUAZ',
        'old_id': 'RY3QRSI7VE'
    }
]

new_agents = {}

for config in agents_config:
    print(f"\nCreating {config['name']}...")
    
    # Delete old agent
    try:
        bedrock.delete_agent(agentId=config['old_id'], skipResourceInUseCheck=True)
        print(f"  Deleted old agent {config['old_id']}")
        time.sleep(5)
    except:
        pass
    
    # Create new agent
    agent = bedrock.create_agent(
        agentName=config['name'],
        agentResourceRoleArn=role_arn,
        foundationModel=inference_profile,
        instruction=config['instruction']
    )
    agent_id = agent['agent']['agentId']
    print(f"  ✅ Created agent: {agent_id}")
    
    # Wait for agent to be ready
    for i in range(30):
        status = bedrock.get_agent(agentId=agent_id)['agent']['agentStatus']
        if status in ['NOT_PREPARED', 'PREPARED']:
            break
        time.sleep(2)
    print(f"  ✅ Agent ready")
    
    # Associate KB
    bedrock.associate_agent_knowledge_base(
        agentId=agent_id,
        agentVersion='DRAFT',
        knowledgeBaseId=config['kb_id'],
        description=f'{config["name"]} knowledge base',
        knowledgeBaseState='ENABLED'
    )
    print(f"  ✅ Linked KB")
    
    # Prepare agent
    bedrock.prepare_agent(agentId=agent_id)
    print(f"  ✅ Preparing...")
    time.sleep(3)
    
    # Create alias
    alias = bedrock.create_agent_alias(
        agentId=agent_id,
        agentAliasName='prod',
        routingConfiguration=[{'agentVersion': 'DRAFT'}]
    )
    alias_id = alias['agentAlias']['agentAliasId']
    print(f"  ✅ Created alias: {alias_id}")
    
    new_agents[config['name'].split('-')[-2]] = {'id': agent_id, 'alias': alias_id}

print(f"\n✅ All agents recreated!")
print(f"\nUpdate supervisor with:")
print(new_agents)
