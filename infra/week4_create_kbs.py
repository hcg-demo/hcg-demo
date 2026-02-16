import boto3
import json
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')
session = boto3.Session()
credentials = session.get_credentials()

ACCOUNT_ID = '026138522123'
COLLECTION_ID = 'y3f4j35z37u9awc6sqkc'
COLLECTION_ENDPOINT = f'https://{COLLECTION_ID}.ap-southeast-1.aoss.amazonaws.com'

print("=== Week 4: Creating Knowledge Bases ===\n")

# Setup OpenSearch client
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    'ap-southeast-1',
    'aoss',
    session_token=credentials.token
)

os_client = OpenSearch(
    hosts=[{'host': COLLECTION_ENDPOINT.replace('https://', ''), 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

# Create indexes for each knowledge base
indexes = [
    {'name': 'hcg_demo_kb_hr', 'kb_name': 'hcg-demo-kb-hr', 's3_prefix': 'hr/'},
    {'name': 'hcg_demo_kb_it', 'kb_name': 'hcg-demo-kb-it', 's3_prefix': 'it/'},
    {'name': 'hcg_demo_kb_finance', 'kb_name': 'hcg-demo-kb-finance', 's3_prefix': 'finance/'},
    {'name': 'hcg_demo_kb_general', 'kb_name': 'hcg-demo-kb-general', 's3_prefix': 'general/'}
]

index_mapping = {
    'settings': {'index': {'knn': True}},
    'mappings': {
        'properties': {
            'vector': {'type': 'knn_vector', 'dimension': 1536},
            'text': {'type': 'text'},
            'metadata': {'type': 'text'}
        }
    }
}

for idx in indexes:
    if not os_client.indices.exists(idx['name']):
        os_client.indices.create(idx['name'], body=index_mapping)
        print(f"✓ Created index: {idx['name']}")
    else:
        print(f"✓ Index exists: {idx['name']}")

# Create Knowledge Bases
kb_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"
s3_bucket = f"hcg-demo-knowledge-{ACCOUNT_ID}"
kb_ids = {}

for idx in indexes:
    existing_kbs = bedrock_agent.list_knowledge_bases()
    kb_id = None
    for kb in existing_kbs.get('knowledgeBaseSummaries', []):
        if kb['name'] == idx['kb_name']:
            kb_id = kb['knowledgeBaseId']
            print(f"✓ KB exists: {idx['kb_name']} ({kb_id})")
            break
    
    if not kb_id:
        kb = bedrock_agent.create_knowledge_base(
            name=idx['kb_name'],
            description=f"Knowledge base for {idx['s3_prefix']}",
            roleArn=kb_role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': 'arn:aws:bedrock:ap-southeast-1::foundation-model/amazon.titan-embed-text-v1'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': f'arn:aws:aoss:ap-southeast-1:{ACCOUNT_ID}:collection/{COLLECTION_ID}',
                    'vectorIndexName': idx['name'],
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        kb_id = kb['knowledgeBase']['knowledgeBaseId']
        print(f"✓ Created KB: {idx['kb_name']} ({kb_id})")
        
        # Create data source
        bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"{idx['kb_name']}-s3",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{s3_bucket}',
                    'inclusionPrefixes': [idx['s3_prefix']]
                }
            }
        )
        print(f"  ✓ Created data source for {idx['s3_prefix']}")
    
    kb_ids[idx['kb_name']] = kb_id

print("\n✅ Knowledge Bases Ready")
for name, kb_id in kb_ids.items():
    print(f"  {name}: {kb_id}")
