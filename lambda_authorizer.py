import json
import hashlib
import hmac
import time
import boto3
import os

secrets_client = boto3.client('secretsmanager')
cached_secret = None

def get_signing_secret():
    global cached_secret
    if cached_secret:
        return cached_secret
    
    response = secrets_client.get_secret_value(SecretId='hcg-demo/slack/credentials')
    cached_secret = json.loads(response['SecretString'])
    return cached_secret

def lambda_handler(event, context):
    timestamp = event['headers'].get('x-slack-request-timestamp', '')
    signature = event['headers'].get('x-slack-signature', '')
    body = event['body']
    
    # Check timestamp (5-minute window)
    now = int(time.time())
    if abs(now - int(timestamp)) > 300:
        return generate_policy('Deny', event['methodArn'])
    
    # Calculate expected signature
    secrets = get_signing_secret()
    sig_basestring = f"v0:{timestamp}:{body}"
    expected_sig = 'v0=' + hmac.new(
        secrets['SLACK_SIGNING_SECRET'].encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    if hmac.compare_digest(signature, expected_sig):
        return generate_policy('Allow', event['methodArn'])
    
    return generate_policy('Deny', event['methodArn'])

def generate_policy(effect, resource):
    return {
        'principalId': 'slack',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }
