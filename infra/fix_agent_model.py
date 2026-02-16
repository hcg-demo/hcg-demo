import boto3

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

agent_id = 'DP6QVL8GPS'

# Update agent to use cross-region inference profile
response = bedrock_agent.update_agent(
    agentId=agent_id,
    agentName='hcg-demo-supervisor',
    agentResourceRoleArn='arn:aws:iam::026138522123:role/hcg-demo-bedrock-agent',
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',  # Regional model
    instruction='''You are a supervisor agent that routes employee queries to specialist agents.

Classify queries into domains:
- HR: benefits, leave, payroll, policies
- IT: laptop, password, VPN, technical issues  
- Finance: expenses, reimbursement, invoices
- General: office, facilities, general questions

Route to the appropriate specialist agent.'''
)

print(f"✅ Updated agent to use cross-region inference profile")
print(f"   Model: us.anthropic.claude-3-sonnet-20240229-v1:0")

# Prepare agent
print(f"\nPreparing agent...")
bedrock_agent.prepare_agent(agentId=agent_id)
print(f"✅ Agent preparation initiated")
