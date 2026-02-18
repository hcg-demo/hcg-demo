"""Test ServiceNow API with SSM credentials"""
import boto3
import json
import urllib.request
import base64
import ssl

# Dev instances often use self-signed certs
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ssm = boto3.client('ssm', region_name='ap-southeast-1')
r = ssm.get_parameters(
    Names=[
        '/hcg-demo/servicenow/instance-url',
        '/hcg-demo/servicenow/username',
        '/hcg-demo/servicenow/password'
    ],
    WithDecryption=True
)
params = {p['Name'].split('/')[-1]: p['Value'] for p in r['Parameters']}
url = params.get('instance-url', '').rstrip('/') + '/api/now/table/incident'
auth = base64.b64encode(
    f"{params['username']}:{params['password']}".encode()
).decode()

print(f"URL: {url}")
print(f"User: {params['username']}")

req = urllib.request.Request(
    url,
    data=json.dumps({'short_description': 'Test', 'description': 'Test'}).encode(),
    headers={
        'Authorization': 'Basic ' + auth,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        data = json.loads(resp.read().decode())
        print("SUCCESS - Ticket:", data.get('result', {}).get('number'))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code} {e.reason}")
    print("Body:", e.read().decode()[:600])
except Exception as e:
    print(f"Error: {e}")
