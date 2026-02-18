import json
import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

# Agent configurations - use TSTALIASID or update with aliases from: aws bedrock-agent list-agent-aliases --agent-id <ID>
AGENTS = {
    'hr': {'id': 'GDR3BCGCZM', 'alias': 'TSTALIASID', 'kb': 'H0LFPBHIAK'},
    'it': {'id': 'ZMLHZEZZXO', 'alias': 'TSTALIASID', 'kb': 'X1VW7AMIK8'},
    'finance': {'id': '8H5G4JZVXM', 'alias': 'TSTALIASID', 'kb': '1MFT5GZYTT'},
    'general': {'id': 'RY3QRSI7VE', 'alias': 'TSTALIASID', 'kb': 'BOLGBDCUAZ'}
}

def _sanitize_for_api(text):
    """Normalize text for safe API handling (smart quotes, Unicode, etc.)"""
    if not text or not isinstance(text, str):
        return str(text or "")
    for old, new in [('\u2018', "'"), ('\u2019', "'"), ('\u201c', '"'), ('\u201d', '"'), ('\u00a0', ' ')]:
        text = text.replace(old, new)
    return text.strip()


def is_ticket_request(query):
    """Check if query is requesting ticket creation"""
    query_lower = query.lower()
    ticket_keywords = [
        'create ticket', 'create a ticket', 'crate ticket', 'crate a ticket',  # incl. typo
        'open ticket', 'open a ticket', 'raise ticket', 'log ticket', 'log a ticket',
        'submit ticket', 'submit a ticket', 'need help', 'urgent', 'please help',
        'need a software', 'need software'  # software request = ticket
    ]
    return any(kw in query_lower for kw in ticket_keywords)

def create_servicenow_ticket(description):
    """Create ServiceNow ticket via Lambda (supports both direct and Bedrock Action Group formats)"""
    try:
        response = lambda_client.invoke(
            FunctionName='hcg-demo-servicenow-action',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'actionGroup': 'ServiceNowActions',
                'apiPath': '/create_incident',
                'parameters': [
                    {'name': 'short_description', 'value': description[:100]},
                    {'name': 'description', 'value': description}
                ]
            })
        )
        result = json.loads(response['Payload'].read())
        # Lambda returns Bedrock Action Group format: {response: {responseBody: {TEXT: {body: ...}}}}
        resp = result.get('response', {})
        if resp.get('httpStatusCode') == 200:
            body_obj = resp.get('responseBody', {})
            # Support both TEXT and application/json formats
            text_body = body_obj.get('TEXT', {}).get('body') or body_obj.get('application/json', {}).get('body', '')
            if isinstance(text_body, dict):
                ticket_num = text_body.get('incident_number') or text_body.get('ticket_number') or 'N/A'
            else:
                # TEXT body is string like "✅ Incident created: INC0010001"
                ticket_num = str(text_body).split(':')[-1].strip() if text_body else 'N/A'
            return f"✓ Ticket created successfully! Ticket Number: {ticket_num}. Our IT team will contact you shortly."
        else:
            err_body = resp.get('responseBody', {}).get('TEXT', {}).get('body', '')
            print(f"ServiceNow returned error: {err_body}")
            return "I've noted your issue. Please contact IT Support at itsupport@starhub.com or +65 6825 3000."
    except Exception as e:
        print(f"ServiceNow error: {e}")
        return "I've noted your issue. Please contact IT Support at itsupport@starhub.com or +65 6825 3000."

def classify_query(query):
    """Classify user query to appropriate domain"""
    query_lower = query.lower()
    
    hr_keywords = ['leave', 'vacation', 'holiday', 'holidays', 'maternity', 'paternity', 'benefit', 'insurance', 'medical', 'salary', 'bonus', 'hr', 'employee', 'onboarding']
    if any(kw in query_lower for kw in hr_keywords):
        return 'hr', 0.9
    
    it_keywords = ['password', 'laptop', 'vpn', 'software', 'install', 'computer', 'network', 'login', 'access', 'it support', 'troubleshoot', 'reset', 'ticket', 'create ticket', 'incident', 'issue', 'problem', 'help']
    if any(kw in query_lower for kw in it_keywords):
        return 'it', 0.9
    
    finance_keywords = ['expense', 'reimbursement', 'procurement', 'purchase', 'invoice', 'payment', 'budget', 'finance', 'cost']
    if any(kw in query_lower for kw in finance_keywords):
        return 'finance', 0.9
    
    return 'general', 0.7

def invoke_agent_with_fallback(agent_id, alias_id, kb_id, query, session_id):
    """Try agent first, fallback to direct KB retrieval"""
    try:
        # Try agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=query
        )
        
        completion = ""
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                completion += event['chunk']['bytes'].decode('utf-8')
        
        if completion:
            return {'response': completion, 'score': 0.9, 'source': 'agent'}
    except Exception as e:
        print(f"Agent failed: {e}, falling back to KB")
    
    # Fallback to direct KB retrieval
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query}
        )
        
        if response['retrievalResults']:
            top_result = response['retrievalResults'][0]
            return {
                'response': top_result['content']['text'],
                'score': top_result['score'],
                'source': 'kb_direct'
            }
    except Exception as e:
        print(f"KB retrieval failed: {e}")
    
    return None

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')
        session_id = body.get('session_id', 'default-session')
        
        if not query:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Query is required'})}
        
        # Check if this is a ticket creation request
        if is_ticket_request(query):
            ticket_response = create_servicenow_ticket(_sanitize_for_api(query))
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'query': query,
                    'domain': 'it',
                    'confidence': 1.0,
                    'confidence_level': 'high',
                    'safe_to_respond': True,
                    'response': ticket_response,
                    'source': 'servicenow',
                    'citations': []
                })
            }
        
        domain, confidence = classify_query(query)
        agent_config = AGENTS[domain]
        
        result = invoke_agent_with_fallback(
            agent_config['id'],
            agent_config['alias'],
            agent_config['kb'],
            query,
            session_id
        )
        
        if result and result['score'] > 0.5:
            response_data = {
                'query': query,
                'domain': domain,
                'confidence': result['score'],
                'confidence_level': 'high' if result['score'] > 0.7 else 'medium',
                'safe_to_respond': True,
                'response': result['response'],
                'source': result['source'],
                'citations': []
            }
        else:
            response_data = {
                'query': query,
                'domain': domain,
                'confidence': 0.3,
                'confidence_level': 'low',
                'safe_to_respond': False,
                'response': f"I don't have enough information to answer that confidently. Please contact the {domain.upper()} team directly.",
                'source': 'fallback',
                'citations': []
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
