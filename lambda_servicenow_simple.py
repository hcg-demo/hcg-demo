"""
ServiceNow incident creation - supports Secrets Manager and SSM Parameter Store.
"""
import json
import boto3
import urllib.request
import base64
import ssl

secrets_client = boto3.client('secretsmanager', region_name='ap-southeast-1')
ssm_client = boto3.client('ssm', region_name='ap-southeast-1')

# Dev instances may use self-signed certs
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def get_servicenow_credentials():
    """Try Secrets Manager first, fallback to SSM Parameter Store"""
    # 1. Secrets Manager: hcg-demo/servicenow/creds with JSON {instance_url, username, password}
    try:
        resp = secrets_client.get_secret_value(SecretId='hcg-demo/servicenow/creds')
        creds = json.loads(resp['SecretString'])
        if creds.get('instance_url') and creds.get('username') and creds.get('password'):
            return creds
    except Exception as e:
        print(f"Secrets Manager fallback: {e}")

    # 2. SSM Parameter Store: /hcg-demo/servicenow/instance-url, username, password
    try:
        resp = ssm_client.get_parameters(
            Names=[
                '/hcg-demo/servicenow/instance-url',
                '/hcg-demo/servicenow/username',
                '/hcg-demo/servicenow/password'
            ],
            WithDecryption=True
        )
        params = {p['Name'].split('/')[-1]: p['Value'] for p in resp.get('Parameters', [])}
        instance_url = params.get('instance-url') or params.get('instance_url')
        if instance_url and params.get('username') and params.get('password'):
            return {
                'instance_url': instance_url.rstrip('/'),
                'username': params['username'],
                'password': params['password']
            }
    except Exception as e:
        print(f"SSM credentials: {e}")

    return None


def create_incident(short_description, description):
    creds = get_servicenow_credentials()
    if not creds:
        raise ValueError("ServiceNow credentials not configured. Add to Secrets Manager (hcg-demo/servicenow/creds) or SSM (/hcg-demo/servicenow/instance-url, username, password).")

    url = f"{creds['instance_url'].rstrip('/')}/api/now/table/incident"
    payload = {
        'short_description': short_description,
        'description': description,
        'urgency': '3',
        'impact': '3'
    }
    auth = base64.b64encode(f"{creds['username']}:{creds['password']}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx) as response:
        result = json.loads(response.read().decode())['result']
    return {
        'incident_number': result['number'],
        'sys_id': result['sys_id']
    }


def lambda_handler(event, context):
    try:
        action = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        parameters = event.get('parameters', [])
        params = {p['name']: p['value'] for p in parameters}

        if api_path in ('/create_incident', '/create-incident'):
            result = create_incident(
                short_description=params.get('short_description', 'IT Support Request'),
                description=params.get('description', '')
            )
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': action,
                    'apiPath': api_path,
                    'httpMethod': 'POST',
                    'httpStatusCode': 200,
                    'responseBody': {
                        'TEXT': {'body': f"✅ Incident created: {result['incident_number']}"}
                    }
                }
            }
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'apiPath': api_path,
                'httpMethod': 'POST',
                'httpStatusCode': 400,
                'responseBody': {'TEXT': {'body': f"Unknown action: {api_path}"}}
            }
        }
    except Exception as e:
        err = str(e)
        print(f"ServiceNow error: {err}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'apiPath': event.get('apiPath', ''),
                'httpMethod': 'POST',
                'httpStatusCode': 500,
                'responseBody': {'TEXT': {'body': f"Error: {err}"}}
            }
        }
