import urllib.request
import json
import base64
import ssl
import html

# Bypass SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

instance_url = "https://dev310376.service-now.com"
username = "ppandya@hcg.com"
# Decode HTML entities: &lt; = < and &gt; = >
password_raw = "BF,M0PH,:Vxs&lt;2@EJA_IYG(b71:?+%}0ia_QglE9iB0ya9or2*76!2vGfl2gz6qzYt89&lt;dzNK&gt;QU;aB(;2f4xzTT!VcKj8orAg"
password = html.unescape(password_raw)

print(f"Decoded password: {password}")

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
        print(f"✓ Connection successful! Status: {response.status}")
        data = json.loads(response.read().decode())
        print(f"✓ Can access incident table")
        print(f"✓ Found {len(data.get('result', []))} incidents")
except Exception as e:
    print(f"✗ Connection failed: {e}")
