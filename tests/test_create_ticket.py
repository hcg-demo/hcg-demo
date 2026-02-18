import urllib.request
import json
import base64
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

instance_url = "https://dev310376.service-now.com"
username = "admin"
password = "JaiShreeganesh@2026"

credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Create incident
incident_data = {
    "short_description": "Test ticket from AWS Lambda",
    "description": "Testing ServiceNow integration with Bedrock agent",
    "urgency": "2",
    "impact": "2"
}

url = f"{instance_url}/api/now/table/incident"
req = urllib.request.Request(
    url,
    data=json.dumps(incident_data).encode(),
    headers={
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        result = json.loads(response.read().decode())
        ticket_number = result['result']['number']
        sys_id = result['result']['sys_id']
        print(f"✓ Ticket created successfully!")
        print(f"  Ticket Number: {ticket_number}")
        print(f"  Sys ID: {sys_id}")
        print(f"  URL: {instance_url}/nav_to.do?uri=incident.do?sys_id={sys_id}")
except Exception as e:
    print(f"✗ Failed to create ticket: {e}")
