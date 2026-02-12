import json
import random
from datetime import datetime

def lambda_handler(event, context):
    """Mock ServiceNow integration for demo"""
    
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    
    # Extract parameters
    parameters = event.get('parameters', [])
    params = {p['name']: p['value'] for p in parameters}
    
    request_body = event.get('requestBody', {})
    body_props = request_body.get('content', {}).get('application/json', {}).get('properties', [])
    body_params = {p['name']: p['value'] for p in body_props}
    
    all_params = {**params, **body_params}
    
    # Route to action
    if api_path == '/create_incident':
        # Generate mock incident
        incident_num = f"INC{random.randint(1000000, 9999999)}"
        sys_id = f"{random.randint(100000, 999999)}"
        
        result = {
            'success': True,
            'incident_number': incident_num,
            'sys_id': sys_id,
            'state': '1',
            'priority': '3',
            'short_description': all_params.get('short_description', 'Support request'),
            'category': all_params.get('category', 'General'),
            'link': f"https://dev355778.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id}",
            'created_at': datetime.now().isoformat()
        }
        
        response_body = json.dumps(result)
        status_code = 200
    
    elif api_path == '/get_incident_status':
        incident_number = all_params.get('incident_number', 'INC0000000')
        
        result = {
            'success': True,
            'incident_number': incident_number,
            'state': '2',
            'state_label': 'In Progress',
            'priority': '3',
            'assigned_to': 'IT Support Team',
            'short_description': 'Support request'
        }
        
        response_body = json.dumps(result)
        status_code = 200
    
    else:
        response_body = json.dumps({'error': f'Unknown action: {api_path}'})
        status_code = 500
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': response_body
                }
            }
        }
    }
