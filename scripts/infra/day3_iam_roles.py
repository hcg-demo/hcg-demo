import boto3
import json

iam = boto3.client('iam')
ACCOUNT_ID = '026138522123'

print("=== Day 3: IAM Roles ===\n")

roles = [
    {
        'name': 'hcg-demo-lambda-exec',
        'service': 'lambda.amazonaws.com',
        'policy': {
            'Version': '2012-10-17',
            'Statement': [
                {'Effect': 'Allow', 'Action': ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
                 'Resource': f'arn:aws:logs:ap-southeast-1:{ACCOUNT_ID}:log-group:/aws/lambda/hcg-demo-*'},
                {'Effect': 'Allow', 'Action': ['ec2:CreateNetworkInterface', 'ec2:DescribeNetworkInterfaces', 'ec2:DeleteNetworkInterface'],
                 'Resource': '*'},
                {'Effect': 'Allow', 'Action': 'secretsmanager:GetSecretValue',
                 'Resource': f'arn:aws:secretsmanager:ap-southeast-1:{ACCOUNT_ID}:secret:hcg-demo/*'}
            ]
        }
    },
    {
        'name': 'hcg-demo-lambda-bedrock',
        'service': 'lambda.amazonaws.com',
        'policy': {
            'Version': '2012-10-17',
            'Statement': [
                {'Effect': 'Allow', 'Action': ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
                 'Resource': f'arn:aws:logs:ap-southeast-1:{ACCOUNT_ID}:log-group:/aws/lambda/hcg-demo-*'},
                {'Effect': 'Allow', 'Action': ['ec2:CreateNetworkInterface', 'ec2:DescribeNetworkInterfaces', 'ec2:DeleteNetworkInterface'],
                 'Resource': '*'},
                {'Effect': 'Allow', 'Action': ['bedrock:InvokeModel', 'bedrock:InvokeAgent', 'bedrock:Retrieve'],
                 'Resource': '*'},
                {'Effect': 'Allow', 'Action': ['dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:UpdateItem', 'dynamodb:Query'],
                 'Resource': f'arn:aws:dynamodb:ap-southeast-1:{ACCOUNT_ID}:table/hcg-demo-*'},
                {'Effect': 'Allow', 'Action': 'secretsmanager:GetSecretValue',
                 'Resource': f'arn:aws:secretsmanager:ap-southeast-1:{ACCOUNT_ID}:secret:hcg-demo/*'}
            ]
        }
    },
    {
        'name': 'hcg-demo-stepfunctions',
        'service': 'states.amazonaws.com',
        'policy': {
            'Version': '2012-10-17',
            'Statement': [
                {'Effect': 'Allow', 'Action': 'lambda:InvokeFunction',
                 'Resource': f'arn:aws:lambda:ap-southeast-1:{ACCOUNT_ID}:function:hcg-demo-*'},
                {'Effect': 'Allow', 'Action': ['xray:PutTraceSegments', 'xray:PutTelemetryRecords'], 'Resource': '*'}
            ]
        }
    },
    {
        'name': 'hcg-demo-bedrock-agent',
        'service': 'bedrock.amazonaws.com',
        'policy': {
            'Version': '2012-10-17',
            'Statement': [
                {'Effect': 'Allow', 'Action': 'bedrock:Retrieve', 'Resource': '*'},
                {'Effect': 'Allow', 'Action': 'lambda:InvokeFunction',
                 'Resource': f'arn:aws:lambda:ap-southeast-1:{ACCOUNT_ID}:function:hcg-demo-tool-*'},
                {'Effect': 'Allow', 'Action': 's3:GetObject',
                 'Resource': f'arn:aws:s3:::hcg-demo-knowledge-{ACCOUNT_ID}/*'}
            ]
        }
    }
]

for role_config in roles:
    try:
        iam.get_role(RoleName=role_config['name'])
        print(f"✓ Role exists: {role_config['name']}")
    except iam.exceptions.NoSuchEntityException:
        trust_policy = {
            'Version': '2012-10-17',
            'Statement': [{'Effect': 'Allow', 'Principal': {'Service': role_config['service']}, 'Action': 'sts:AssumeRole'}]
        }
        iam.create_role(
            RoleName=role_config['name'],
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Tags=[{'Key': 'Project', 'Value': 'HCG_Demo'}]
        )
        iam.put_role_policy(
            RoleName=role_config['name'],
            PolicyName=f"{role_config['name']}-policy",
            PolicyDocument=json.dumps(role_config['policy'])
        )
        print(f"✓ Created role: {role_config['name']}")

print("\n=== CONSOLIDATED SUMMARY ===")
print("✅ Day 1-2: VPC Infrastructure")
print("  - VPC: vpc-0382b710049feecd6")
print("  - Subnets: 4 (2 public, 2 private)")
print("  - NAT Gateway: nat-01b8dfbb36ae3f811")
print("  - VPC Endpoints: S3 + DynamoDB")
print("\n✅ Day 3: IAM Roles")
print("  - hcg-demo-lambda-exec")
print("  - hcg-demo-lambda-bedrock")
print("  - hcg-demo-stepfunctions")
print("  - hcg-demo-bedrock-agent")
print("\n✅ Secrets Manager")
print("  - hcg-demo/slack/credentials")
print("  - hcg-demo/servicenow/oauth")
