import boto3
import json
import time
from datetime import datetime

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

# Test configuration
SUPERVISOR_AGENT_ID = 'DP6QVL8GPS'
SUPERVISOR_ALIAS_ID = 'TSTALIASID'  # AgentTestAlias

# Test queries with expected routing
TEST_QUERIES = [
    {
        'query': 'What are the HR benefits?',
        'expected_agent': 'HR',
        'expected_kb': 'H0LFPBHIAK',
        'keywords': ['benefits', 'health', 'insurance', 'leave']
    },
    {
        'query': 'My laptop is broken',
        'expected_agent': 'IT',
        'expected_kb': 'X1VW7AMIK8',
        'keywords': ['laptop', 'troubleshoot', 'support', 'it']
    },
    {
        'query': 'How do I submit expenses?',
        'expected_agent': 'Finance',
        'expected_kb': '1MFT5GZYTT',
        'keywords': ['expense', 'reimbursement', 'submit', 'receipt']
    },
    {
        'query': 'Where is the office?',
        'expected_agent': 'General',
        'expected_kb': 'BOLGBDCUAZ',
        'keywords': ['office', 'location', 'address', 'building']
    }
]

def test_agent_routing():
    print("="*70)
    print("BEDROCK AGENT ROUTING TEST")
    print("="*70)
    print(f"\nSupervisor Agent: {SUPERVISOR_AGENT_ID}")
    print(f"Alias: {SUPERVISOR_ALIAS_ID}")
    print(f"Test Queries: {len(TEST_QUERIES)}\n")
    
    results = []
    
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(TEST_QUERIES)}: {test['query']}")
        print(f"Expected Agent: {test['expected_agent']}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        try:
            # Invoke agent
            response = bedrock_agent_runtime.invoke_agent(
                agentId=SUPERVISOR_AGENT_ID,
                agentAliasId=SUPERVISOR_ALIAS_ID,
                sessionId=f'test-session-{int(time.time())}',
                inputText=test['query']
            )
            
            # Parse response
            response_text = ''
            citations = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    trace = event['trace'].get('trace', {})
                    if 'orchestrationTrace' in trace:
                        orch = trace['orchestrationTrace']
                        if 'observation' in orch:
                            obs = orch['observation']
                            if 'knowledgeBaseLookupOutput' in obs:
                                kb_output = obs['knowledgeBaseLookupOutput']
                                if 'retrievedReferences' in kb_output:
                                    citations.extend(kb_output['retrievedReferences'])
            
            elapsed_time = time.time() - start_time
            
            # Validate results
            routing_correct = any(keyword in response_text.lower() for keyword in test['keywords'])
            has_citations = len(citations) > 0
            response_time_ok = elapsed_time < 15
            
            result = {
                'query': test['query'],
                'expected_agent': test['expected_agent'],
                'response_text': response_text[:200] + '...' if len(response_text) > 200 else response_text,
                'citations_count': len(citations),
                'response_time': round(elapsed_time, 2),
                'routing_correct': routing_correct,
                'has_citations': has_citations,
                'response_time_ok': response_time_ok,
                'overall_pass': routing_correct and response_time_ok
            }
            
            results.append(result)
            
            # Print results
            print(f"\n✅ Response received in {elapsed_time:.2f}s")
            print(f"\nResponse Preview:")
            print(f"  {response_text[:150]}...")
            print(f"\nCitations: {len(citations)}")
            if citations:
                for j, citation in enumerate(citations[:2], 1):
                    if 'content' in citation:
                        print(f"  [{j}] {citation['content'].get('text', '')[:80]}...")
            
            print(f"\nValidation:")
            print(f"  {'✅' if routing_correct else '❌'} Routing correct (keywords found)")
            print(f"  {'✅' if has_citations else '❌'} Has citations")
            print(f"  {'✅' if response_time_ok else '❌'} Response time < 15s ({elapsed_time:.2f}s)")
            print(f"\n{'✅ PASS' if result['overall_pass'] else '❌ FAIL'}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            results.append({
                'query': test['query'],
                'expected_agent': test['expected_agent'],
                'error': str(e),
                'overall_pass': False
            })
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for r in results if r.get('overall_pass', False))
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = '✅ PASS' if result.get('overall_pass', False) else '❌ FAIL'
        print(f"  {i}. {result['query'][:40]:40} → {result['expected_agent']:10} {status}")
        if 'response_time' in result:
            print(f"     Time: {result['response_time']}s, Citations: {result['citations_count']}")
    
    # Save results
    with open('agent_routing_test_results.json', 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'supervisor_agent_id': SUPERVISOR_AGENT_ID,
            'total_tests': total,
            'passed': passed,
            'success_rate': f"{passed/total*100:.1f}%",
            'results': results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to agent_routing_test_results.json")
    
    # Final status
    print(f"\n{'='*70}")
    if passed == total:
        print("✅ ALL TESTS PASSED - Agent routing working correctly!")
    else:
        print(f"⚠️ {total - passed} test(s) failed - Review results above")
    print(f"{'='*70}\n")
    
    return passed == total

if __name__ == '__main__':
    success = test_agent_routing()
    exit(0 if success else 1)
