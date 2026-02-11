import boto3
import json

print("=" * 70)
print("HCG_DEMO COST OPTIMIZATION ANALYSIS")
print("=" * 70)

# Current monthly costs
costs = {
    'NAT Gateway': {'cost': 32.85, 'required': True, 'can_optimize': True},
    'Lambda': {'cost': 0.20, 'required': True, 'can_optimize': False},
    'API Gateway': {'cost': 0.35, 'required': True, 'can_optimize': False},
    'DynamoDB': {'cost': 5.00, 'required': True, 'can_optimize': False},
    'S3': {'cost': 0.23, 'required': True, 'can_optimize': False},
    'CloudWatch': {'cost': 2.50, 'required': True, 'can_optimize': True},
    'Bedrock': {'cost': 15.00, 'required': True, 'can_optimize': False},
    'OpenSearch Serverless': {'cost': 175.00, 'required': False, 'can_optimize': True}
}

total_cost = sum(item['cost'] for item in costs.values())

print(f"\n📊 CURRENT MONTHLY COST: ${total_cost:.2f}")
print("\nBreakdown:")
for service, details in costs.items():
    status = "✅ Required" if details['required'] else "⚠️  Optional"
    optimize = "💡 Can optimize" if details['can_optimize'] else ""
    print(f"  {service}: ${details['cost']:.2f} {status} {optimize}")

print("\n" + "=" * 70)
print("OPTIMIZATION OPTIONS")
print("=" * 70)

print("\n🎯 OPTION 1: Remove OpenSearch Serverless (RECOMMENDED)")
print("  Current: $175/month")
print("  After: $0/month")
print("  Savings: $175/month (76% reduction)")
print("  Impact: Knowledge Bases won't work until alternative is set up")
print("  Alternative: Use Pinecone (free tier) or in-memory vector store")

print("\n🎯 OPTION 2: Optimize NAT Gateway")
print("  Current: $32.85/month")
print("  After: $0/month")
print("  Savings: $32.85/month")
print("  Impact: Lambda can't access internet (Bedrock still works via VPC endpoint)")
print("  Note: Need to add Bedrock VPC endpoint")

print("\n🎯 OPTION 3: Reduce CloudWatch Retention")
print("  Current: $2.50/month")
print("  After: $1.00/month")
print("  Savings: $1.50/month")
print("  Impact: Shorter log retention (7 days instead of 30-365)")

print("\n" + "=" * 70)
print("COST SCENARIOS")
print("=" * 70)

scenarios = {
    'Current (All services)': 231.13,
    'Remove OpenSearch only': 56.13,
    'Remove OpenSearch + Optimize NAT': 23.28,
    'Minimal (Remove OpenSearch + NAT + Reduce logs)': 21.78
}

print()
for scenario, cost in scenarios.items():
    print(f"  {scenario}: ${cost:.2f}/month")

print("\n" + "=" * 70)
print("RECOMMENDED ACTION")
print("=" * 70)
print("\n✅ Remove OpenSearch Serverless for demo/testing")
print("   - Saves $175/month (76% cost reduction)")
print("   - New monthly cost: $56.13")
print("   - Can add back later when needed for production")

print("\n" + "=" * 70)

choice = input("\nDo you want to DELETE OpenSearch Serverless collection? (yes/no): ").strip().lower()

if choice == 'yes':
    print("\n🗑️  Deleting OpenSearch Serverless collection...")
    
    opensearch = boto3.client('opensearchserverless', region_name='ap-southeast-1')
    collection_id = 'y3f4j35z37u9awc6sqkc'
    
    try:
        # Delete collection
        opensearch.delete_collection(id=collection_id)
        print(f"✓ Deleted collection: {collection_id}")
        
        # Delete security policies
        try:
            opensearch.delete_security_policy(name='hcg-demo-encryption', type='encryption')
            print("✓ Deleted encryption policy")
        except:
            pass
        
        try:
            opensearch.delete_security_policy(name='hcg-demo-network', type='network')
            print("✓ Deleted network policy")
        except:
            pass
        
        try:
            opensearch.delete_access_policy(name='hcg-demo-data-access', type='data')
            print("✓ Deleted data access policy")
        except:
            pass
        
        print("\n✅ OpenSearch Serverless removed successfully!")
        print(f"💰 New monthly cost: $56.13 (saved $175/month)")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
else:
    print("\n✓ No changes made. OpenSearch collection retained.")

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

if choice == 'yes':
    print("\n✅ Cost Optimization Applied")
    print("  - OpenSearch Serverless: DELETED")
    print("  - Monthly Cost: $56.13 (was $231.13)")
    print("  - Savings: $175/month (76%)")
    print("\n📝 Note: Bedrock Agents will work, but Knowledge Bases need alternative")
    print("  Options: Pinecone, Weaviate, or in-memory vector store")
else:
    print("\n✅ No Changes Made")
    print("  - All services retained")
    print("  - Monthly Cost: $231.13")
    print("\n💡 Tip: Delete OpenSearch when not actively testing to save costs")
