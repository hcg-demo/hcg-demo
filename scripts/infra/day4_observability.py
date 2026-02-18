import boto3

logs = boto3.client('logs', region_name='ap-southeast-1')
cloudtrail = boto3.client('cloudtrail', region_name='ap-southeast-1')
s3 = boto3.client('s3', region_name='ap-southeast-1')
ACCOUNT_ID = '026138522123'

print("=== Day 4: Observability ===\n")

# CloudWatch Log Groups
log_groups = [
    ('/aws/lambda/hcg-demo-webhook-handler', 30),
    ('/aws/lambda/hcg-demo-authorizer', 30),
    ('/aws/lambda/hcg-demo-agent-orchestrator', 90),
    ('/aws/apigateway/hcg-demo-api', 90),
    ('/hcg-demo/application', 365)
]

for log_group, retention in log_groups:
    try:
        logs.create_log_group(logGroupName=log_group)
        logs.put_retention_policy(logGroupName=log_group, retentionInDays=retention)
        print(f"✓ Created log group: {log_group} ({retention} days)")
    except logs.exceptions.ResourceAlreadyExistsException:
        print(f"✓ Log group exists: {log_group}")

# CloudTrail S3 Bucket
bucket_name = f'hcg-demo-cloudtrail-{ACCOUNT_ID}'
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"✓ CloudTrail bucket exists: {bucket_name}")
except:
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'}
    )
    s3.put_bucket_policy(Bucket=bucket_name, Policy=f'''{{
        "Version": "2012-10-17",
        "Statement": [{{
            "Sid": "AWSCloudTrailAclCheck",
            "Effect": "Allow",
            "Principal": {{"Service": "cloudtrail.amazonaws.com"}},
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::{bucket_name}"
        }}, {{
            "Sid": "AWSCloudTrailWrite",
            "Effect": "Allow",
            "Principal": {{"Service": "cloudtrail.amazonaws.com"}},
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::{bucket_name}/*",
            "Condition": {{"StringEquals": {{"s3:x-amz-acl": "bucket-owner-full-control"}}}}
        }}]
    }}''')
    print(f"✓ Created CloudTrail bucket: {bucket_name}")

# CloudTrail
try:
    cloudtrail.create_trail(
        Name='hcg-demo-audit-trail',
        S3BucketName=bucket_name,
        IsMultiRegionTrail=True,
        EnableLogFileValidation=True
    )
    cloudtrail.start_logging(Name='hcg-demo-audit-trail')
    print("✓ Created CloudTrail: hcg-demo-audit-trail")
except cloudtrail.exceptions.TrailAlreadyExistsException:
    print("✓ CloudTrail exists: hcg-demo-audit-trail")

print("\n=== CONSOLIDATED SUMMARY ===")
print("✅ Day 1-2: VPC (vpc-0382b710049feecd6)")
print("✅ Day 3: IAM Roles (4 roles)")
print("✅ Day 4: Observability")
print("  - CloudWatch Log Groups: 5")
print("  - CloudTrail: hcg-demo-audit-trail")
print("✅ Secrets Manager: 2 secrets")
