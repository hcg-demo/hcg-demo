import boto3
import json

s3 = boto3.client('s3', region_name='ap-southeast-1')
ACCOUNT_ID = '026138522123'

print("=== Day 9: S3 Buckets ===\n")

buckets = [
    {
        'name': f'hcg-demo-knowledge-{ACCOUNT_ID}',
        'versioning': True,
        'folders': ['hr/', 'it/', 'finance/', 'general/']
    },
    {
        'name': f'hcg-demo-logs-{ACCOUNT_ID}',
        'versioning': False,
        'folders': ['access-logs/', 'application-logs/']
    }
]

for bucket_config in buckets:
    bucket_name = bucket_config['name']
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket exists: {bucket_name}")
    except:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'}
        )
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        if bucket_config['versioning']:
            s3.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': 'Enabled'})
        
        # Create folders
        for folder in bucket_config['folders']:
            s3.put_object(Bucket=bucket_name, Key=folder)
        
        print(f"✓ Created bucket: {bucket_name}")

# Bucket policy for Bedrock
knowledge_bucket = f'hcg-demo-knowledge-{ACCOUNT_ID}'
policy = {
    'Version': '2012-10-17',
    'Statement': [{
        'Sid': 'BedrockKBAccess',
        'Effect': 'Allow',
        'Principal': {'Service': 'bedrock.amazonaws.com'},
        'Action': 's3:GetObject',
        'Resource': f'arn:aws:s3:::{knowledge_bucket}/*',
        'Condition': {'StringEquals': {'aws:SourceAccount': ACCOUNT_ID}}
    }]
}
s3.put_bucket_policy(Bucket=knowledge_bucket, Policy=json.dumps(policy))
print(f"✓ Applied Bedrock policy to {knowledge_bucket}")

# Enable EventBridge for knowledge bucket
s3.put_bucket_notification_configuration(
    Bucket=knowledge_bucket,
    NotificationConfiguration={'EventBridgeConfiguration': {}}
)
print(f"✓ Enabled EventBridge notifications on {knowledge_bucket}")

print("\n=== CONSOLIDATED SUMMARY ===")
print("✅ Day 1-2: VPC Infrastructure")
print("✅ Day 3: IAM Roles (4 roles)")
print("✅ Day 4: Observability")
print("✅ Day 8: DynamoDB Tables (3 tables)")
print("✅ Day 9: S3 Buckets")
print(f"  - hcg-demo-knowledge-{ACCOUNT_ID} (versioned, Bedrock-ready)")
print(f"  - hcg-demo-logs-{ACCOUNT_ID}")
print(f"  - hcg-demo-cloudtrail-{ACCOUNT_ID}")
print("✅ Secrets Manager: 2 secrets")
