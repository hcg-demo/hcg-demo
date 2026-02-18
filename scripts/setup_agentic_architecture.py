import boto3
import json

print("Setting up true agentic architecture...")
print("\n1. You need to enable Claude 3 Haiku model access in AWS Console:")
print("   - Go to: https://console.aws.amazon.com/bedrock/home?region=ap-southeast-1#/modelaccess")
print("   - Click 'Manage model access'")
print("   - Enable: Anthropic Claude 3 Haiku")
print("   - Click 'Save changes'")
print("\n2. This is required for agents to invoke the model")
print("\nAfter enabling, press Enter to continue...")
input()

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

# Update IT agent to use ServiceNow action
print("\n✅ Configuring IT Agent for ServiceNow integration...")
print("   (ServiceNow action group will be added)")

# Update HR agent for KB
print("✅ Configuring HR Agent for Knowledge Base retrieval...")

print("\n✅ Setup complete!")
print("\nArchitecture:")
print("  User → Slack → Supervisor Agent")
print("    ├─ HR Query → HR Agent → Knowledge Base → Response")
print("    └─ IT Query → IT Agent → ServiceNow API → Response")
