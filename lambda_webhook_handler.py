import json
import boto3

dynamodb = boto3.resource('dynamodb')
sessions_table = dynamodb.Table('hcg-demo-sessions')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    
    # Handle URL verification
    if body.get('type') == 'url_verification':
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': body['challenge']})
        }
    
    # Handle events
    if body.get('type') == 'event_callback':
        slack_event = body['event']
        
        # Ignore bot messages
        if slack_event.get('bot_id'):
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        # Process message
        user_id = slack_event.get('user')
        channel_id = slack_event.get('channel')
        text = slack_event.get('text', '')
        thread_ts = slack_event.get('thread_ts', slack_event.get('ts'))
        
        # Store session
        session_id = f"{channel_id}_{thread_ts}"
        sessions_table.put_item(Item={
            'sessionId': session_id,
            'userId': user_id,
            'query': text,
            'ttl': int(time.time()) + 28800  # 8 hours
        })
        
        # TODO: Invoke Bedrock Agent (Week 5-6)
        # For now, acknowledge receipt
        return {
            'statusCode': 200,
            'body': json.dumps({'ok': True})
        }
    
    return {'statusCode': 200, 'body': json.dumps({'ok': True})}
