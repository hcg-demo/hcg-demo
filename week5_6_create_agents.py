import boto3
import json

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')
ACCOUNT_ID = '026138522123'

print("=== Week 5-6: Bedrock Agents ===\n")

# Agent configurations
agents = [
    {
        'name': 'hcg-demo-supervisor',
        'description': 'Supervisor agent for intent classification and routing',
        'instruction': '''You are a supervisor agent that classifies user queries and routes them to specialist agents.
        
Analyze the user's question and determine which domain it belongs to:
- HR: Benefits, leave, onboarding, policies, payroll
- IT: Technical issues, software, hardware, access requests
- Finance: Expenses, procurement, budgets, invoices
- General: Company info, facilities, general questions

Respond with the domain name only: HR, IT, Finance, or General.'''
    },
    {
        'name': 'hcg-demo-hr-agent',
        'description': 'HR specialist agent',
        'instruction': '''You are an HR specialist assistant. Help employees with:
- Benefits and compensation questions
- Leave policies and requests
- Onboarding procedures
- HR policies and guidelines
- Payroll inquiries

Provide accurate, helpful responses based on company HR policies. Be professional and empathetic.'''
    },
    {
        'name': 'hcg-demo-it-agent',
        'description': 'IT specialist agent',
        'instruction': '''You are an IT support specialist. Help employees with:
- Technical troubleshooting
- Software and hardware issues
- Access requests and permissions
- IT policies and procedures
- System status and outages

Provide clear technical guidance. Offer to create ServiceNow tickets for complex issues.'''
    },
    {
        'name': 'hcg-demo-finance-agent',
        'description': 'Finance specialist agent',
        'instruction': '''You are a Finance specialist assistant. Help employees with:
- Expense reporting and reimbursement
- Procurement processes
- Budget inquiries
- Invoice questions
- Financial policies

Provide accurate financial guidance following company policies.'''
    },
    {
        'name': 'hcg-demo-general-agent',
        'description': 'General information agent',
        'instruction': '''You are a general company assistant. Help employees with:
- Company information and culture
- Facilities and office locations
- General policies
- Events and announcements
- Other non-specialized questions

Be friendly and helpful. Route to specialists if needed.'''
    }
]

agent_ids = {}
role_arn = f'arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent'

for agent_config in agents:
    # Check if agent exists
    existing_agents = bedrock_agent.list_agents()
    agent_id = None
    for agent in existing_agents.get('agentSummaries', []):
        if agent['agentName'] == agent_config['name']:
            agent_id = agent['agentId']
            print(f"✓ Agent exists: {agent_config['name']} ({agent_id})")
            break
    
    if not agent_id:
        # Create agent
        agent = bedrock_agent.create_agent(
            agentName=agent_config['name'],
            agentResourceRoleArn=role_arn,
            description=agent_config['description'],
            instruction=agent_config['instruction'],
            foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
            idleSessionTTLInSeconds=1800
        )
        agent_id = agent['agent']['agentId']
        print(f"✓ Created agent: {agent_config['name']} ({agent_id})")
        
        # Wait for agent to be ready
        import time
        time.sleep(5)
        
        # Prepare agent
        try:
            bedrock_agent.prepare_agent(agentId=agent_id)
            print(f"  ✓ Prepared agent")
        except:
            print(f"  ⚠ Agent preparing (will be ready shortly)")
    
    agent_ids[agent_config['name']] = agent_id

print("\n=== FINAL CONSOLIDATED SUMMARY ===")
print("\n✅ WEEK 1-2: Foundation Infrastructure")
print("  - VPC, Subnets, NAT Gateway")
print("  - IAM Roles, Secrets Manager")
print("  - CloudWatch, CloudTrail")
print("  - DynamoDB Tables, S3 Buckets")
print("  - Cognito User Pool")

print("\n✅ WEEK 3: Slack Integration")
print("  - API Gateway: arep4vvhlc")
print("  - Lambda Functions: 2")
print("  - Webhook: https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/slack/events")

print("\n✅ WEEK 4: Knowledge Layer")
print("  - OpenSearch Collection: y3f4j35z37u9awc6sqkc")
print("  - S3 Knowledge Bucket: hcg-demo-knowledge-026138522123")

print("\n✅ WEEK 5-6: Bedrock Agents")
for name, agent_id in agent_ids.items():
    print(f"  - {name}: {agent_id}")

print("\n📝 Next Steps:")
print("1. Upload documents to S3 knowledge bucket")
print("2. Create Knowledge Bases via AWS Console:")
print("   - Go to Bedrock → Knowledge bases → Create")
print("   - Link to OpenSearch collection: y3f4j35z37u9awc6sqkc")
print("   - Add S3 data sources")
print("3. Associate Knowledge Bases with agents")
print("4. Create ServiceNow Action Group Lambda")
print("5. Test end-to-end in Slack")

# Save agent IDs
with open('hcg_demo_agents.json', 'w') as f:
    json.dump(agent_ids, f, indent=2)
print("\n✅ Agent IDs saved to: hcg_demo_agents.json")
