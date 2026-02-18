"""
Add SSM GetParameters permission to hcg-demo-servicenow-action for reading
/hcg-demo/servicenow/* parameters (credential fallback).
"""
import boto3
import json

REGION = 'ap-southeast-1'
lambda_client = boto3.client('lambda', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)

func = lambda_client.get_function(FunctionName='hcg-demo-servicenow-action')
role_arn = func['Configuration']['Role']
role_name = role_arn.split('/')[-1]
account_id = role_arn.split(':')[4]

policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': ['ssm:GetParameter', 'ssm:GetParameters'],
            'Resource': f'arn:aws:ssm:{REGION}:{account_id}:parameter/hcg-demo/servicenow/*'
        }
    ]
}

iam.put_role_policy(
    RoleName=role_name,
    PolicyName='HCGDemoServiceNowSSM',
    PolicyDocument=json.dumps(policy)
)
print(f"✓ Added SSM permissions to {role_name} for hcg-demo-servicenow-action")
