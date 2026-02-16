import boto3
import json

region = 'ap-southeast-1'

print("Checking HCG Demo AWS Resources...\n")

# Check Lambda functions
lambda_client = boto3.client('lambda', region_name=region)
expected_lambdas = [
    'hcg-demo-webhook-handler',
    'hcg-demo-supervisor-agent',
    'hcg-demo-servicenow-action',
    'hcg-demo-content-governance',
    'hcg-demo-content-sync',
    'hcg-demo-deep-linking',
    'hcg-demo-link-health-check',
    'hcg-demo-llm-evaluator'
]

print("Lambda Functions:")
for func in expected_lambdas:
    try:
        lambda_client.get_function(FunctionName=func)
        print(f"  ✅ {func}")
    except:
        print(f"  ❌ {func} - NOT FOUND")

# Check DynamoDB tables
dynamodb = boto3.client('dynamodb', region_name=region)
expected_tables = [
    'hcg-demo-conversations',
    'hcg-demo-user-feedback',
    'hcg-demo-content-governance',
    'hcg-demo-document-owners',
    'hcg-demo-resource-catalog',
    'hcg-demo-link-health'
]

print("\nDynamoDB Tables:")
for table in expected_tables:
    try:
        dynamodb.describe_table(TableName=table)
        print(f"  ✅ {table}")
    except:
        print(f"  ❌ {table} - NOT FOUND")

# Check Bedrock Agents
bedrock = boto3.client('bedrock-agent', region_name=region)
expected_agents = {
    'Supervisor': 'DP6QVL8GPS',
    'HR': 'IEVMSZT1GY',
    'IT': 'ZMLHZEZZXO',
    'Finance': '8H5G4JZVXM',
    'General': 'RY3QRSI7VE'
}

print("\nBedrock Agents:")
for name, agent_id in expected_agents.items():
    try:
        bedrock.get_agent(agentId=agent_id)
        print(f"  ✅ {name} Agent ({agent_id})")
    except:
        print(f"  ❌ {name} Agent ({agent_id}) - NOT FOUND")

# Check Knowledge Bases
expected_kbs = {
    'HR': 'H0LFPBHIAK',
    'IT': 'X1VW7AMIK8',
    'Finance': '1MFT5GZYTT',
    'General': 'BOLGBDCUAZ'
}

print("\nKnowledge Bases:")
for name, kb_id in expected_kbs.items():
    try:
        bedrock.get_knowledge_base(knowledgeBaseId=kb_id)
        print(f"  ✅ {name} KB ({kb_id})")
    except:
        print(f"  ❌ {name} KB ({kb_id}) - NOT FOUND")

print("\n" + "="*50)
print("Health check complete!")
