"""
Update ServiceNow credentials in SSM Parameter Store.
Run: python scripts/infra/setup_servicenow.py
"""
import boto3
import json
import getpass

ssm = boto3.client('ssm', region_name='ap-southeast-1')

print("=" * 70)
print("SERVICENOW CREDENTIALS - SSM Parameter Store")
print("=" * 70)

instance_url = input("\nInstance URL (e.g. https://dev355778.service-now.com): ").strip()
if not instance_url:
    print("❌ Instance URL required")
    exit(1)
if not instance_url.startswith("http"):
    instance_url = "https://" + instance_url

username = input("Username (ServiceNow login or API user): ").strip()
if not username:
    print("❌ Username required")
    exit(1)

password = getpass.getpass("Password: ")
if not password:
    print("❌ Password required")
    exit(1)

print(f"\nStoring in SSM...")
try:
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/instance-url',
        Value=instance_url.rstrip('/'),
        Type='String',
        Overwrite=True
    )
    print("✅ /hcg-demo/servicenow/instance-url")
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/username',
        Value=username,
        Type='String',
        Overwrite=True
    )
    print("✅ /hcg-demo/servicenow/username")
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/password',
        Value=password,
        Type='SecureString',
        Overwrite=True
    )
    print("✅ /hcg-demo/servicenow/password (encrypted)")
    print("\n✅ Done. Try @hcg_demo Create a ticket: My laptop won't boot")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
