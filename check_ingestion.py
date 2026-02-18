import boto3

bedrock = boto3.client('bedrock-agent', region_name='ap-southeast-1')

kbs = {'H0LFPBHIAK': 'HR', 'X1VW7AMIK8': 'IT'}

for kb_id, name in kbs.items():
    ds = bedrock.list_data_sources(knowledgeBaseId=kb_id)
    if ds['dataSourceSummaries']:
        ds_id = ds['dataSourceSummaries'][0]['dataSourceId']
        jobs = bedrock.list_ingestion_jobs(knowledgeBaseId=kb_id, dataSourceId=ds_id, maxResults=1)
        if jobs['ingestionJobSummaries']:
            status = jobs['ingestionJobSummaries'][0]['status']
            print(f"{name} KB: {status}")
        else:
            print(f"{name} KB: No jobs")
