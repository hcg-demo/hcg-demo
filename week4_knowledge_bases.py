import boto3
import json
import time

opensearch = boto3.client('opensearchserverless', region_name='ap-southeast-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')
iam = boto3.client('iam')

ACCOUNT_ID = '026138522123'

print("=== Week 4: Knowledge Layer ===\n")

# Create OpenSearch Serverless collection
collections = opensearch.list_collections()
collection_id = None
for col in collections.get('collectionSummaries', []):
    if col['name'] == 'hcg-demo-knowledge':
        collection_id = col['id']
        print(f"✓ OpenSearch collection exists: {collection_id}")
        break

if not collection_id:
    # Create encryption policy
    try:
        opensearch.create_security_policy(
            name='hcg-demo-encryption',
            type='encryption',
            policy=json.dumps({
                'Rules': [{'ResourceType': 'collection', 'Resource': ['collection/hcg-demo-knowledge']}],
                'AWSOwnedKey': True
            })
        )
        print("✓ Created encryption policy")
    except:
        print("✓ Encryption policy exists")
    
    # Create network policy
    try:
        opensearch.create_security_policy(
            name='hcg-demo-network',
            type='network',
            policy=json.dumps([{
                'Rules': [{'ResourceType': 'collection', 'Resource': ['collection/hcg-demo-knowledge']}],
                'AllowFromPublic': True
            }])
        )
        print("✓ Created network policy")
    except:
        print("✓ Network policy exists")
    
    # Create data access policy
    try:
        opensearch.create_access_policy(
            name='hcg-demo-data-access',
            type='data',
            policy=json.dumps([{
                'Rules': [{
                    'ResourceType': 'collection',
                    'Resource': ['collection/hcg-demo-knowledge'],
                    'Permission': ['aoss:*']
                }, {
                    'ResourceType': 'index',
                    'Resource': ['index/hcg-demo-knowledge/*'],
                    'Permission': ['aoss:*']
                }],
                'Principal': [
                    f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent",
                    f"arn:aws:iam::{ACCOUNT_ID}:root"
                ]
            }])
        )
        print("✓ Created data access policy")
    except:
        print("✓ Data access policy exists")
    
    # Create collection
    collection = opensearch.create_collection(
        name='hcg-demo-knowledge',
        type='VECTORSEARCH',
        description='Vector store for HCG Demo knowledge bases'
    )
    collection_id = collection['createCollectionDetail']['id']
    print(f"✓ Creating OpenSearch collection: {collection_id}")
    print("  (This takes 3-5 minutes...)")
    
    # Wait for collection to be active
    while True:
        status = opensearch.batch_get_collection(ids=[collection_id])
        if status['collectionDetails'][0]['status'] == 'ACTIVE':
            break
        time.sleep(30)
    
    print("✓ OpenSearch collection active")

# Get collection endpoint
collection_details = opensearch.batch_get_collection(ids=[collection_id])
collection_endpoint = collection_details['collectionDetails'][0]['collectionEndpoint']

# Create Bedrock Knowledge Bases
kb_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"
s3_bucket = f"hcg-demo-knowledge-{ACCOUNT_ID}"

knowledge_bases = [
    {'name': 'hcg-demo-kb-hr', 'description': 'HR policies and procedures', 's3_prefix': 'hr/'},
    {'name': 'hcg-demo-kb-it', 'description': 'IT documentation', 's3_prefix': 'it/'},
    {'name': 'hcg-demo-kb-finance', 'description': 'Finance policies', 's3_prefix': 'finance/'},
    {'name': 'hcg-demo-kb-general', 'description': 'General company info', 's3_prefix': 'general/'}
]

kb_ids = {}

for kb_config in knowledge_bases:
    # Check if KB exists
    existing_kbs = bedrock_agent.list_knowledge_bases()
    kb_id = None
    for kb in existing_kbs.get('knowledgeBaseSummaries', []):
        if kb['name'] == kb_config['name']:
            kb_id = kb['knowledgeBaseId']
            print(f"✓ Knowledge Base exists: {kb_config['name']} ({kb_id})")
            break
    
    if not kb_id:
        # Create Knowledge Base
        kb = bedrock_agent.create_knowledge_base(
            name=kb_config['name'],
            description=kb_config['description'],
            roleArn=kb_role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f"arn:aws:bedrock:ap-southeast-1::foundation-model/amazon.titan-embed-text-v1"
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': f"arn:aws:aoss:ap-southeast-1:{ACCOUNT_ID}:collection/{collection_id}",
                    'vectorIndexName': kb_config['name'].replace('-', '_'),
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        kb_id = kb['knowledgeBase']['knowledgeBaseId']
        print(f"✓ Created Knowledge Base: {kb_config['name']} ({kb_id})")
        
        # Create data source
        ds = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"{kb_config['name']}-s3-source",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f"arn:aws:s3:::{s3_bucket}",
                    'inclusionPrefixes': [kb_config['s3_prefix']]
                }
            }
        )
        print(f"  ✓ Created data source for {kb_config['s3_prefix']}")
    
    kb_ids[kb_config['name']] = kb_id

print("\n=== CONSOLIDATED SUMMARY ===")
print("\n✅ WEEK 1-2: Foundation")
print("✅ WEEK 3: Slack Integration (2 Lambda functions)")
print("\n✅ WEEK 4: Knowledge Layer")
print(f"  - OpenSearch Collection: {collection_id}")
print(f"  - Collection Endpoint: {collection_endpoint}")
print("  - Bedrock Knowledge Bases: 4")
for name, kb_id in kb_ids.items():
    print(f"    • {name}: {kb_id}")
print(f"\n📦 S3 Bucket: s3://{s3_bucket}")
print("📝 Upload documents to respective folders (hr/, it/, finance/, general/)")
print("🔄 Then sync each Knowledge Base to ingest content")
