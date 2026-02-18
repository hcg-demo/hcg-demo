"""
Slack webhook handler - v4 fast-ack - fixes:
1. Return 200 within 3 sec to prevent Slack retries (no duplicate tickets)
2. Process async after ack
3. Idempotency via channel_ts
"""
WEBHOOK_VERSION = "v4-fast-ack"  # Log this to verify deployed code
import json
import re
import time
import boto3

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
secrets_client = boto3.client('secretsmanager', region_name='ap-southeast-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')

PROCESSED_EVENTS_TABLE = 'hcg-demo-processed-events'


def get_slack_token():
    response = secrets_client.get_secret_value(SecretId='hcg-demo/slack/credentials')
    secret = json.loads(response['SecretString'])
    return secret.get('SLACK_BOT_TOKEN') or secret.get('bot_token')


def post_slack_message(channel, text, thread_ts=None):
    import urllib.request
    token = get_slack_token()
    
    payload = {'channel': channel, 'text': text}
    if thread_ts:
        payload['thread_ts'] = thread_ts
    
    req = urllib.request.Request(
        'https://slack.com/api/chat.postMessage',
        data=json.dumps(payload).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode())


def process_event(body):
    """
    Process Slack event asynchronously - invoked by self with async=True.
    Runs the full flow: post thinking -> invoke supervisor -> post response.
    """
    slack_event = body['event']
    channel_id = slack_event.get('channel')
    text = slack_event.get('text', '')
    thread_ts = slack_event.get('ts')
    
    # Remove bot mention from text
    text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    text = _sanitize_text(text)
    
    # Skip empty messages (user sent just @mention)
    if not text:
        post_slack_message(channel_id, "I didn't catch that. Try asking something like: What are the company holidays? or Create a ticket: My laptop won't boot.", thread_ts)
        return
    
    # Post thinking message
    post_slack_message(channel_id, '🤔 Thinking...', thread_ts)
    
    # Invoke supervisor agent
    try:
        response = lambda_client.invoke(
            FunctionName='hcg-demo-supervisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({
                    'query': text,
                    'session_id': f'{channel_id}_{thread_ts}'
                })
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body_str = result.get('body', '{}')
            data = json.loads(body_str) if isinstance(body_str, str) else body_str
            response_text = data.get('response', 'Sorry, I could not generate a response.')
            post_slack_message(channel_id, response_text, thread_ts)
        else:
            err_msg = result.get('body', '')
            try:
                err_data = json.loads(err_msg) if isinstance(err_msg, str) else {}
                err_text = err_data.get('error', str(err_msg))[:200]
            except Exception:
                err_text = 'Sorry, I encountered an error. Please try again.'
            post_slack_message(channel_id, err_text, thread_ts)
    except Exception as e:
        print(f"Supervisor error: {e}")
        err_msg = str(e)[:300]  # Truncate for Slack
        post_slack_message(channel_id, f'Sorry, I encountered an error. Please try again. (Error: {err_msg})', thread_ts)


def try_mark_event_processed(event_id):
    """
    Atomically mark event as processed. Returns True if we won the race (first to process),
    False if another Lambda already processed it (duplicate).
    """
    try:
        table = dynamodb.Table(PROCESSED_EVENTS_TABLE)
        table.put_item(
            Item={
                'eventId': event_id,
                'ttl': int(time.time()) + 3600  # Expire in 1 hour
            },
            ConditionExpression='attribute_not_exists(eventId)'
        )
        return True
    except Exception as e:
        if getattr(e, 'response', {}).get('Error', {}).get('Code') == 'ConditionalCheckFailedException':
            return False  # Already processed
        print(f"DynamoDB idempotency failed: {e}, proceeding (degraded)")
        return True


def _sanitize_text(text):
    """Normalize text for safe API/JSON handling (smart quotes, Unicode apostrophes, etc.)"""
    if not text or not isinstance(text, str):
        return text or ""
    # Replace curly/smart quotes and apostrophes with ASCII equivalents
    replacements = [
        ('\u2018', "'"), ('\u2019', "'"), ('\u201c', '"'), ('\u201d', '"'),
        ('\u00a0', ' '),  # non-breaking space
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip()


def lambda_handler(event, context):
    print(f"[{WEBHOOK_VERSION}] Webhook invoked")
    # Handle async self-invoke (process event after fast ack)
    if event.get('source') == 'async':
        body = event.get('body')
        if body:
            process_event(body)
        return {'statusCode': 200, 'body': 'ok'}
    body = json.loads(event.get('body', '{}'))
    
    # Handle URL verification (Slack app setup)
    if body.get('type') == 'url_verification':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': body['challenge']
        }
    
    # Handle events
    if body.get('type') == 'event_callback':
        slack_event = body['event']
        
        # Ignore bot messages and message subtypes (e.g. channel_join, message_changed)
        if slack_event.get('bot_id') or slack_event.get('subtype'):
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        # Only process app_mention (channels) or message (DMs) - prevents duplicates when
        # Slack sends both app_mention and message for the same @mention
        ev_type = slack_event.get('type', '')
        channel = slack_event.get('channel', '') or ''
        if ev_type == 'app_mention':
            pass  # Process @mention in channel
        elif ev_type == 'message' and str(channel).startswith('D'):
            pass  # Process DM to bot
        else:
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        # Idempotency: use channel_ts (not just event_id) - Slack sends app_mention AND
        # message for same @mention with different event_ids, but same channel+ts
        channel = slack_event.get('channel', '') or ''
        msg_ts = slack_event.get('ts', '') or ''
        dedup_key = f"{channel}_{msg_ts}"
        if not try_mark_event_processed(dedup_key):
            print(f"Duplicate message {dedup_key}, skipping")
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        # Fast ack: return 200 immediately so Slack doesn't retry. Process async.
        lambda_client.invoke(
            FunctionName=context.function_name,
            InvocationType='Event',
            Payload=json.dumps({'source': 'async', 'body': body})
        )
        return {'statusCode': 200, 'body': json.dumps({'ok': True})}
    
    return {'statusCode': 200, 'body': json.dumps({'ok': True})}
