import boto3
import zipfile
import io

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

print("Deploying mock ServiceNow Lambda for demo...")

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    with open('lambda_servicenow_mock.py', 'r') as f:
        zip_file.writestr('lambda_function.py', f.read())

zip_buffer.seek(0)

lambda_client.update_function_code(
    FunctionName='hcg-demo-servicenow-action',
    ZipFile=zip_buffer.read()
)

print("✅ Mock Lambda deployed")
print("\nThis will return mock incident numbers for demo purposes.")
print("To use real ServiceNow, activate your account at:")
print("https://dev355778.service-now.com")
