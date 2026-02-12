import boto3
import json
from urllib import request, error
import base64
import ssl

ssm = boto3.client('ssm', region_name='ap-southeast-1')

# Get credentials
response = ssm.get_parameters(
    Names=[
        '/hcg-demo/servicenow/instance-url',
        '/hcg-demo/servicenow/username',
        '/hcg-demo/servicenow/password'
    ],
    WithDecryption=True
)

params = {p['Name'].split('/')[-1]: p['Value'] for p in response['Parameters']}
instance_url = params['instance-url']
username = params['username']
password = params['password']

print(f"Testing: {instance_url}")
print(f"User: {username}\n")

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Test 1: Check if instance is accessible
print("Test 1: Instance accessibility...")
try:
    req = request.Request(f"{instance_url}/api/now/table/incident?sysparm_limit=1")
    req.add_header('Authorization', 'Basic ' + base64.b64encode(f"{username}:{password}".encode()).decode())
    req.add_header('Accept', 'application/json')
    
    with request.urlopen(req, timeout=10, context=ssl_context) as resp:
        print(f"✅ Instance accessible (HTTP {resp.status})")
        result = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Authentication successful")
        print(f"✅ Can read incidents: {len(result.get('result', []))} found\n")
        
        # Test 2: Try to create incident
        print("Test 2: Creating incident...")
        create_url = f"{instance_url}/api/now/table/incident"
        data = {
            'short_description': 'Test from HCG Demo',
            'description': 'Testing incident creation',
            'urgency': '3'
        }
        
        create_req = request.Request(
            create_url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Basic ' + base64.b64encode(f"{username}:{password}".encode()).decode()
            },
            method='POST'
        )
        
        with request.urlopen(create_req, timeout=10, context=ssl_context) as create_resp:
            incident = json.loads(create_resp.read().decode('utf-8')).get('result', {})
            print(f"✅ Incident created!")
            print(f"   Number: {incident.get('number')}")
            print(f"   Sys ID: {incident.get('sys_id')}")
            print(f"   Link: {instance_url}/nav_to.do?uri=incident.do?sys_id={incident.get('sys_id')}")
            
except error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
