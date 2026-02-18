"""
Add required permissions to hcg-demo-webhook-handler's role for:
- Self-invoke (async processing)
- Supervisor invoke  
- DynamoDB idempotency (hcg-demo-processed-events)
"""
import boto3
import json

ACCOUNT_ID = '026138522123'
REGION = 'ap-southeast-1'

iam = boto3.client('iam')
lambda_client = boto3.client('lambda', region_name=REGION)

# Get webhook's current role
func = lambda_client.get_function(FunctionName='hcg-demo-webhook-handler')
role_arn = func['Configuration']['Role']
role_name = role_arn.split('/')[-1]

policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': 'lambda:InvokeFunction',
            'Resource': [
                f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:hcg-demo-webhook-handler',
                f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:hcg-demo-supervisor-agent'
            ]
        },
        {
            'Effect': 'Allow',
            'Action': 'dynamodb:PutItem',
            'Resource': f'arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/hcg-demo-processed-events'
        }
    ]
}

iam.put_role_policy(
    RoleName=role_name,
    PolicyName='HCGDemoWebhookSlackPermissions',
    PolicyDocument=json.dumps(policy)
)
print(f"✓ Added permissions to {role_name}")
print("  - lambda:InvokeFunction (self + supervisor)")
print("  - dynamodb:PutItem on hcg-demo-processed-events")
