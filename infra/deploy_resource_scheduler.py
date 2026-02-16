import boto3
import json
import zipfile
from io import BytesIO

region = 'ap-southeast-1'
lambda_client = boto3.client('lambda', region_name=region)
events_client = boto3.client('events', region_name=region)
iam_client = boto3.client('iam', region_name=region)

# Create IAM role
role_name = 'hcg-demo-resource-scheduler-role'
try:
    role = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {'Service': ['lambda.amazonaws.com', 'events.amazonaws.com']},
                'Action': 'sts:AssumeRole'
            }]
        })
    )
    role_arn = role['Role']['Arn']
    
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='ResourceSchedulerPolicy',
        PolicyDocument=json.dumps({
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Action': ['ec2:DescribeInstances', 'ec2:StopInstances', 'ec2:StartInstances',
                          'rds:DescribeDBInstances', 'rds:StopDBInstance', 'rds:StartDBInstance',
                          'lambda:ListFunctions', 'lambda:PutFunctionConcurrency', 'lambda:DeleteFunctionConcurrency',
                          'aoss:ListCollections', 'aoss:UpdateCollection'],
                'Resource': '*'
            }]
        })
    )
except iam_client.exceptions.EntityAlreadyExistsException:
    role_arn = iam_client.get_role(RoleName=role_name)['Role']['Arn']

# Create Lambda function
with open('lambda_resource_scheduler.py', 'rb') as f:
    code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.writestr('lambda_function.py', code)
zip_buffer.seek(0)

function_name = 'hcg-demo-resource-scheduler'
try:
    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=300
    )
    function_arn = response['FunctionArn']
except lambda_client.exceptions.ResourceConflictException:
    function_arn = lambda_client.get_function(FunctionName=function_name)['Configuration']['FunctionArn']

# Create EventBridge rules
rules = [
    {'name': 'hcg-demo-stop-resources', 'schedule': 'cron(0 14 * * ? *)', 'action': 'stop'},  # 10 PM SGT
    {'name': 'hcg-demo-start-resources', 'schedule': 'cron(0 0 * * ? *)', 'action': 'start'}  # 8 AM SGT
]

for rule in rules:
    events_client.put_rule(Name=rule['name'], ScheduleExpression=rule['schedule'], State='ENABLED')
    events_client.put_targets(
        Rule=rule['name'],
        Targets=[{
            'Id': '1',
            'Arn': function_arn,
            'Input': json.dumps({'action': rule['action']})
        }]
    )
    lambda_client.add_permission(
        FunctionName=function_name,
        StatementId=f"{rule['name']}-permission",
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn=f"arn:aws:events:{region}:026138522123:rule/{rule['name']}"
    )

print(f"✅ Deployed: {function_name}")
print(f"✅ Stop schedule: 10 PM SGT (14:00 UTC)")
print(f"✅ Start schedule: 8 AM SGT (00:00 UTC)")
print(f"\n⚠️  Tag resources with 'AutoSchedule=true' to enable auto-scheduling")
