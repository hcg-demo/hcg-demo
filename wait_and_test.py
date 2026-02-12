import boto3
import time

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

agent_id = 'DP6QVL8GPS'

print(f"Waiting for agent {agent_id} to be prepared...")

for i in range(30):
    response = bedrock_agent.get_agent(agentId=agent_id)
    status = response['agent']['agentStatus']
    
    print(f"  [{i+1}/30] Status: {status}")
    
    if status == 'PREPARED':
        print(f"\n✅ Agent is PREPARED and ready for testing!")
        break
    elif status in ['FAILED', 'DELETING']:
        print(f"\n❌ Agent preparation failed with status: {status}")
        exit(1)
    
    time.sleep(10)
else:
    print(f"\n⚠️ Timeout waiting for agent preparation")
    exit(1)

print("\nRunning routing tests...")
import subprocess
result = subprocess.run(['python', 'test_agent_routing.py'])
exit(result.returncode)
