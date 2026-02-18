import urllib.request
import json
import ssl

# Bypass SSL verification for testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

payload = {
    "token": "test",
    "challenge": "test123",
    "type": "url_verification"
}
req = urllib.request.Request(
    'https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/webhook',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        print(f"Status: {response.status}")
        print(f"Response: {response.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
