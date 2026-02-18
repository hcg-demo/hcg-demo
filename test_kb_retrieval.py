"""
Test KB retrieval: direct Bedrock retrieve + full supervisor flow.
"""
import boto3
import json

bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

KBS = {
    'hr': 'H0LFPBHIAK',
    'it': 'X1VW7AMIK8',
    'finance': '1MFT5GZYTT',
    'general': 'BOLGBDCUAZ'
}

QUERIES = {
    'hr': ['What are the company holidays for 2025?', 'How do I apply for leave?', 'Maternity leave policy'],
    'it': ['How do I reset my password?', 'VPN setup guide', 'My laptop wont boot'],
    'finance': ['Expense reimbursement process', 'How to submit an invoice?', 'Procurement policy'],
    'general': ['Office locations', 'Employee FAQ', 'Company policies']
}


def test_direct_retrieve(kb_id, query):
    """Direct Bedrock KB retrieve"""
    try:
        r = bedrock.retrieve(knowledgeBaseId=kb_id, retrievalQuery={'text': query})
        results = r.get('retrievalResults', [])
        if not results:
            return None, 0
        top = results[0]
        return top['content']['text'][:250] + ('...' if len(top['content']['text']) > 250 else ''), top['score']
    except Exception as e:
        return None, 0


def test_supervisor(query):
    """Full flow via supervisor"""
    try:
        r = lambda_client.invoke(
            FunctionName='hcg-demo-supervisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({'query': query, 'session_id': 'test-kb'})
            })
        )
        d = json.loads(r['Payload'].read())
        if d.get('statusCode') != 200:
            return None, d.get('body', 'err')
        body = json.loads(d.get('body', '{}'))
        resp = body.get('response', '')[:300]
        domain = body.get('domain', '')
        source = body.get('source', '')
        return f"[{domain}] {source}: {resp}...", body.get('confidence', 0)
    except Exception as e:
        return str(e), 0


print("=" * 70)
print("KB RETRIEVAL TEST")
print("=" * 70)

print("\n--- 1. Direct KB retrieve (Bedrock) ---")
for domain, kb_id in KBS.items():
    query = QUERIES[domain][0]
    text, score = test_direct_retrieve(kb_id, query)
    status = "OK" if text and score > 0.3 else "FAIL"
    print(f"\n[{domain}] {query}")
    print(f"  {status} score={score:.2f}" if score else f"  {status} no results")
    if text:
        print(f"  Preview: {text[:120]}...")

print("\n--- 2. Full flow via Supervisor ---")
for domain in KBS:
    query = QUERIES[domain][0]
    resp, conf = test_supervisor(query)
    status = "OK" if resp and conf > 0.5 else "FAIL"
    print(f"\n[{domain}] {query}")
    print(f"  {status} conf={conf:.2f}")
    if resp:
        print(f"  Preview: {resp[:150]}...")

print("\n" + "=" * 70)
print("Done. Try in Slack: @hcg_demo What are the company holidays for 2025?")
print("=" * 70)
