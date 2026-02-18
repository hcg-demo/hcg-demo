import boto3
import time

s3 = boto3.client('s3', region_name='ap-southeast-1')
bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

bucket_name = 'hcg-demo-kb-docs'

# Create bucket
try:
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'}
    )
    print(f"✅ Created bucket: {bucket_name}")
except:
    print(f"⚠️  Bucket exists: {bucket_name}")

# Upload documents
docs = [
    ('sample_documents/hr_holidays.txt', 'hr/holidays.txt'),
    ('sample_documents/it_support.txt', 'it/support.txt')
]

for local, s3_key in docs:
    s3.upload_file(local, bucket_name, s3_key)
    print(f"✅ Uploaded: {s3_key}")

# Update KB data sources
kbs = {
    'H0LFPBHIAK': 'hr',  # HR KB
    'X1VW7AMIK8': 'it'   # IT KB
}

for kb_id, prefix in kbs.items():
    try:
        # Get data source
        ds_response = bedrock.list_data_sources(knowledgeBaseId=kb_id)
        if ds_response['dataSourceSummaries']:
            ds_id = ds_response['dataSourceSummaries'][0]['dataSourceId']
            
            # Start ingestion
            bedrock.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id
            )
            print(f"✅ Started ingestion for {prefix} KB")
        else:
            print(f"⚠️  No data source for {prefix} KB")
    except Exception as e:
        print(f"❌ Error with {prefix} KB: {e}")

print("\n⏳ Wait 2-3 minutes for ingestion to complete, then test in Slack!")
