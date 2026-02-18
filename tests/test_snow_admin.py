import urllib.request
import json
import base64
import ssl

# Bypass SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

instance_url = "https://dev310376.service-now.com"
username = "admin"
password = "JaiShreeganesh@2026"

print(f"Testing connection to: {instance_url}")
print(f"Username: {username}")

# Create basic auth header
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Test connection
url = f"{instance_url}/api/now/table/incident?sysparm_limit=1"
req = urllib.request.Request(
    url,
    headers={
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        print(f"\n✓ Connection successful! Status: {response.status}")
        data = json.loads(response.read().decode())
        print(f"✓ Can access incident table")
        print(f"✓ ServiceNow API is working!")
except Exception as e:
    print(f"\n✗ Connection failed: {e}")
