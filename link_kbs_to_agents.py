import boto3
import time

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

links = [
    ('IEVMSZT1GY', 'H0LFPBHIAK', 'HR'),
    ('ZMLHZEZZXO', 'X1VW7AMIK8', 'IT'),
    ('8H5G4JZVXM', '1MFT5GZYTT', 'Finance'),
    ('RY3QRSI7VE', 'BOLGBDCUAZ', 'General')
]

for agent_id, kb_id, name in links:
    try:
        bedrock.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            knowledgeBaseId=kb_id,
            description=f'{name} knowledge base',
            knowledgeBaseState='ENABLED'
        )
        print(f"✅ Linked {name} KB to {name} Agent")
        
        # Prepare agent
        bedrock.prepare_agent(agentId=agent_id)
        print(f"✅ Preparing {name} agent...")
        time.sleep(3)
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"⚠️  {name} KB already linked")
        else:
            print(f"❌ Error linking {name}: {e}")

print("\n✅ All KBs linked! Wait 30 seconds then test.")
