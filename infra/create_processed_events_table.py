"""Create hcg-demo-processed-events table for Slack webhook idempotency."""
import boto3

dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')

try:
    dynamodb.create_table(
        TableName='hcg-demo-processed-events',
        KeySchema=[{'AttributeName': 'eventId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'eventId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    print("✓ Created hcg-demo-processed-events")
except dynamodb.exceptions.ResourceInUseException:
    print("✓ Table hcg-demo-processed-events already exists")

# Enable TTL
dynamodb.update_time_to_live(
    TableName='hcg-demo-processed-events',
    TimeToLiveSpecification={'Enabled': True, 'AttributeName': 'ttl'}
)
print("✓ TTL enabled on hcg-demo-processed-events")
