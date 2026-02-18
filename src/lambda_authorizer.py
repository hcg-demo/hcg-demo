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
    try:
        headers = event.get('headers') or {}
        # API Gateway may lowercase headers
        headers_lower = {k.lower(): v for k, v in headers.items()}
        timestamp = headers_lower.get('x-slack-request-timestamp', '') or ''
        signature = headers_lower.get('x-slack-signature', '') or ''
        body = event.get('body') or ''
        
        # Allow url_verification (Slack setup) - must pass before Events work
        if body and 'url_verification' in body:
            return generate_policy('Allow', event['methodArn'])
        
        if not timestamp or not signature:
            return generate_policy('Deny', event['methodArn'])
        
        # Check timestamp (5-minute window)
        try:
            ts = int(timestamp)
        except (ValueError, TypeError):
            return generate_policy('Deny', event['methodArn'])
        now = int(time.time())
        if abs(now - ts) > 300:
            return generate_policy('Deny', event['methodArn'])
        
        # Calculate expected signature
        secrets = get_signing_secret()
        signing_secret = secrets.get('SLACK_SIGNING_SECRET') or secrets.get('signing_secret')
        if not signing_secret:
            return generate_policy('Deny', event['methodArn'])
        
        sig_basestring = f"v0:{timestamp}:{body}"
        expected_sig = 'v0=' + hmac.new(
            signing_secret.encode() if isinstance(signing_secret, str) else str(signing_secret).encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        if hmac.compare_digest(signature, expected_sig):
            return generate_policy('Allow', event['methodArn'])
        
        return generate_policy('Deny', event['methodArn'])
    except Exception as e:
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
