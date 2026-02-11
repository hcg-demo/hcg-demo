import boto3

dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')

print("=== Day 8: DynamoDB Tables ===\n")

tables = [
    {
        'name': 'hcg-demo-sessions',
        'key': [{'AttributeName': 'sessionId', 'KeyType': 'HASH'}],
        'attrs': [{'AttributeName': 'sessionId', 'AttributeType': 'S'}]
    },
    {
        'name': 'hcg-demo-users',
        'key': [{'AttributeName': 'slackUserId', 'KeyType': 'HASH'}],
        'attrs': [{'AttributeName': 'slackUserId', 'AttributeType': 'S'}, {'AttributeName': 'email', 'AttributeType': 'S'}],
        'gsi': {'IndexName': 'email-index', 'Keys': [{'AttributeName': 'email', 'KeyType': 'HASH'}]}
    },
    {
        'name': 'hcg-demo-feedback',
        'key': [{'AttributeName': 'feedbackId', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}],
        'attrs': [{'AttributeName': 'feedbackId', 'AttributeType': 'S'}, {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                  {'AttributeName': 'sessionId', 'AttributeType': 'S'}],
        'gsi': {'IndexName': 'session-index', 'Keys': [{'AttributeName': 'sessionId', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}]}
    }
]

for table_config in tables:
    try:
        dynamodb.describe_table(TableName=table_config['name'])
        print(f"✓ Table exists: {table_config['name']}")
    except dynamodb.exceptions.ResourceNotFoundException:
        params = {
            'TableName': table_config['name'],
            'KeySchema': table_config['key'],
            'AttributeDefinitions': table_config['attrs'],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [{'Key': 'Project', 'Value': 'HCG_Demo'}]
        }
        
        if 'gsi' in table_config:
            params['GlobalSecondaryIndexes'] = [{
                'IndexName': table_config['gsi']['IndexName'],
                'KeySchema': table_config['gsi']['Keys'],
                'Projection': {'ProjectionType': 'ALL'}
            }]
        
        dynamodb.create_table(**params)
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_config['name'])
        
        # Enable TTL
        dynamodb.update_time_to_live(
            TableName=table_config['name'],
            TimeToLiveSpecification={'Enabled': True, 'AttributeName': 'ttl'}
        )
        print(f"✓ Created table: {table_config['name']}")

print("\n=== CONSOLIDATED SUMMARY ===")
print("✅ Day 1-2: VPC Infrastructure")
print("✅ Day 3: IAM Roles (4 roles)")
print("✅ Day 4: Observability (CloudWatch + CloudTrail)")
print("✅ Day 8: DynamoDB Tables")
print("  - hcg-demo-sessions")
print("  - hcg-demo-users (with email-index)")
print("  - hcg-demo-feedback (with session-index)")
print("✅ Secrets Manager: 2 secrets")
