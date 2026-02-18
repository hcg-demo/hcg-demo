import boto3
import zipfile
from io import BytesIO

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

with open('src/lambda_supervisor_agent.py', 'rb') as f:
    code = f.read()

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', code)
zip_buffer.seek(0)

lambda_client.update_function_code(
    FunctionName='hcg-demo-supervisor-agent',
    ZipFile=zip_buffer.read()
)

print("✅ Updated hcg-demo-supervisor-agent")
