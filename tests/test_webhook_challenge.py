import requests
import json

url = "https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/webhook"

payload = {
    "type": "url_verification",
    "challenge": "test_challenge_123"
}

response = requests.post(url, json=payload, verify=False)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print(f"Headers: {response.headers}")
