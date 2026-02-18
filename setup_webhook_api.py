import boto3

api_client = boto3.client('apigateway', region_name='ap-southeast-1')
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

api_id = 'arep4vvhlc'
region = 'ap-southeast-1'
account_id = '026138522123'

resources = api_client.get_resources(restApiId=api_id)
root_id = [r['id'] for r in resources['items'] if r['path'] == '/'][0]

try:
    webhook_resource = api_client.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart='webhook'
    )
    resource_id = webhook_resource['id']
    print(f"✅ Created /webhook: {resource_id}")
except:
    resource_id = [r['id'] for r in resources['items'] if r['path'] == '/webhook'][0]
    print(f"⚠️  /webhook exists: {resource_id}")

try:
    api_client.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='POST',
        authorizationType='NONE'
    )
    print("✅ POST method created")
except:
    print("⚠️  POST exists")

lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:hcg-demo-webhook-handler"

api_client.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
)
print("✅ Lambda integration configured")

try:
    lambda_client.add_permission(
        FunctionName='hcg-demo-webhook-handler',
        StatementId='apigateway-webhook',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*/webhook"
    )
    print("✅ Lambda permission added")
except:
    print("⚠️  Permission exists")

api_client.create_deployment(restApiId=api_id, stageName='prod')
print("✅ Deployed to prod")
print(f"\n🎉 URL: https://{api_id}.execute-api.{region}.amazonaws.com/prod/webhook")
