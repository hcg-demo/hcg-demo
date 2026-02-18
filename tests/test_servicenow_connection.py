import urllib.request
import json
import base64
import ssl

# Bypass SSL verification for testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

instance_url = "https://dev310376.service-now.com"
# Test credentials 1
username1 = "Admin"
password1 = "BF,M0PH,:Vxs<2@EJA_IYG(b71:?+%}0ia_QglE9iB0ya9or2*76!2vGfl2gz6qzYt89<dzNK>QU;aB(;2f4xzTT!VcKj8orAg"

# Test credentials 2
username2 = "ppandya@hcg.com"
password2 = "BF,M0PH,:Vxs<2@EJA_IYG(b71:?+%}0ia_QglE9iB0ya9or2*76!2vGfl2gz6qzYt89<dzNK>QU;aB(;2f4xzTT!VcKj8orAg"

print("Testing credential set 1: Admin")
username = username1
password = password1

# Create basic auth header
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Test connection by getting incident table
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
        print(f"✓ Connection successful! Status: {response.status}")
        data = json.loads(response.read().decode())
        print(f"✓ Can access incident table")
except Exception as e:
    print(f"✗ Credential 1 failed: {e}")
    print("\nTesting credential set 2: ppandya@hcg.com")
    username = username2
    password = password2
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
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
            print(f"✓ Connection successful! Status: {response.status}")
            data = json.loads(response.read().decode())
            print(f"✓ Can access incident table")
    except Exception as e2:
        print(f"✗ Credential 2 also failed: {e2}")
