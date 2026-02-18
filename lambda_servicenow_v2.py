import json
import boto3
import urllib.request
import base64

secrets_client = boto3.client('secretsmanager', region_name='ap-southeast-1')

def get_servicenow_creds():
    response = secrets_client.get_secret_value(SecretId='hcg-demo/servicenow/new-creds')
    return json.loads(response['SecretString'])

def create_incident(short_description, description):
    creds = get_servicenow_creds()
    
    credentials = f"{creds['username']}:{creds['password']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    incident_data = {
        "short_description": short_description,
        "description": description,
        "urgency": "2",
        "impact": "2"
    }
    
    url = f"{creds['instance_url']}/api/now/table/incident"
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
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        return result['result']

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    api_path = event.get('apiPath', '')
    parameters = event.get('parameters', [])
    
    if api_path == '/create-incident':
        # Extract parameters
        short_desc = next((p['value'] for p in parameters if p['name'] == 'short_description'), 'No description')
        desc = next((p['value'] for p in parameters if p['name'] == 'description'), '')
        
        try:
            ticket = create_incident(short_desc, desc)
            
            return {
                'statusCode': 200,
                'body': {
                    'application/json': {
                        'body': json.dumps({
                            'ticket_number': ticket['number'],
                            'sys_id': ticket['sys_id'],
                            'message': f"Ticket {ticket['number']} created successfully"
                        })
                    }
                }
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
    
    return {
        'statusCode': 400,
        'body': {
            'application/json': {
                'body': json.dumps({'error': 'Invalid API path'})
            }
        }
    }
