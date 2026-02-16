import boto3
import json
from datetime import datetime

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

# Knowledge Base IDs
KBS = {
    'hr': 'H0LFPBHIAK',
    'it': 'X1VW7AMIK8',
    'finance': '1MFT5GZYTT',
    'general': 'BOLGBDCUAZ'
}

# Test queries with expected results
TEST_QUERIES = [
    {
        'kb': 'hr',
        'query': 'What is the parental leave policy?',
        'expected_keywords': ['leave', 'parental', 'maternity', 'paternity', 'weeks', 'days'],
        'min_faithfulness': 0.95
    },
    {
        'kb': 'hr',
        'query': 'What health insurance benefits are available?',
        'expected_keywords': ['health', 'insurance', 'medical', 'coverage', 'benefits'],
        'min_faithfulness': 0.95
    },
    {
        'kb': 'it',
        'query': 'How do I reset my password?',
        'expected_keywords': ['password', 'reset', 'account', 'login'],
        'min_faithfulness': 0.95
    },
    {
        'kb': 'it',
        'query': 'How do I set up VPN access?',
        'expected_keywords': ['vpn', 'access', 'remote', 'connection', 'setup'],
        'min_faithfulness': 0.95
    },
    {
        'kb': 'finance',
        'query': 'How do I submit an expense report?',
        'expected_keywords': ['expense', 'report', 'submit', 'reimbursement'],
        'min_faithfulness': 0.95
    },
    {
        'kb': 'general',
        'query': 'Where is the Singapore office located?',
        'expected_keywords': ['singapore', 'office', 'location', 'address'],
        'min_faithfulness': 0.95
    }
]

def test_kb_retrieval():
    print("="*70)
    print("KNOWLEDGE BASE RETRIEVAL TEST")
    print("="*70)
    print(f"\nKnowledge Bases: {len(KBS)}")
    print(f"Test Queries: {len(TEST_QUERIES)}\n")
    
    results = []
    
    for i, test in enumerate(TEST_QUERIES, 1):
        kb_id = KBS[test['kb']]
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(TEST_QUERIES)}: {test['query']}")
        print(f"Knowledge Base: {test['kb'].upper()} ({kb_id})")
        print(f"{'='*70}")
        
        try:
            # Retrieve from Knowledge Base
            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': test['query']},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            )
            
            # Parse results
            retrieval_results = response.get('retrievalResults', [])
            
            if not retrieval_results:
                print(f"\n❌ No results retrieved")
                results.append({
                    'query': test['query'],
                    'kb': test['kb'],
                    'success': False,
                    'error': 'No results'
                })
                continue
            
            # Extract content and citations
            retrieved_text = ''
            citations = []
            
            for result in retrieval_results:
                content = result.get('content', {}).get('text', '')
                retrieved_text += content + ' '
                
                location = result.get('location', {})
                score = result.get('score', 0)
                
                citation = {
                    'text': content[:100] + '...' if len(content) > 100 else content,
                    'score': round(score, 3),
                    'source': location.get('s3Location', {}).get('uri', 'Unknown')
                }
                citations.append(citation)
            
            # Validate results
            keywords_found = sum(1 for kw in test['expected_keywords'] 
                                if kw.lower() in retrieved_text.lower())
            keyword_match_rate = keywords_found / len(test['expected_keywords'])
            
            has_citations = len(citations) > 0
            top_score = citations[0]['score'] if citations else 0
            faithfulness_ok = top_score >= test['min_faithfulness']
            
            result = {
                'query': test['query'],
                'kb': test['kb'],
                'kb_id': kb_id,
                'results_count': len(retrieval_results),
                'citations': citations,
                'top_score': top_score,
                'keywords_found': keywords_found,
                'keyword_match_rate': round(keyword_match_rate, 2),
                'faithfulness_ok': faithfulness_ok,
                'has_citations': has_citations,
                'success': has_citations and keyword_match_rate >= 0.5
            }
            
            results.append(result)
            
            # Print results
            print(f"\n✅ Retrieved {len(retrieval_results)} results")
            print(f"\nTop 3 Citations:")
            for j, citation in enumerate(citations[:3], 1):
                print(f"  [{j}] Score: {citation['score']}")
                print(f"      Text: {citation['text']}")
                print(f"      Source: {citation['source'].split('/')[-1]}")
            
            print(f"\nValidation:")
            print(f"  {'✅' if has_citations else '❌'} Has citations ({len(citations)})")
            print(f"  {'✅' if faithfulness_ok else '❌'} Faithfulness score ≥{test['min_faithfulness']} (actual: {top_score})")
            print(f"  {'✅' if keyword_match_rate >= 0.5 else '❌'} Keywords found ({keywords_found}/{len(test['expected_keywords'])})")
            print(f"\n{'✅ PASS' if result['success'] else '❌ FAIL'}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            results.append({
                'query': test['query'],
                'kb': test['kb'],
                'error': str(e),
                'success': False
            })
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = '✅ PASS' if result.get('success', False) else '❌ FAIL'
        kb = result['kb'].upper()
        print(f"  {i}. [{kb:7}] {result['query'][:45]:45} {status}")
        if 'top_score' in result:
            print(f"     Score: {result['top_score']}, Results: {result['results_count']}, Keywords: {result['keywords_found']}")
    
    # KB-specific summary
    print(f"\nKnowledge Base Performance:")
    for kb_name, kb_id in KBS.items():
        kb_results = [r for r in results if r.get('kb') == kb_name]
        kb_passed = sum(1 for r in kb_results if r.get('success', False))
        kb_total = len(kb_results)
        if kb_total > 0:
            print(f"  {kb_name.upper():8} ({kb_id}): {kb_passed}/{kb_total} passed")
    
    # Save results
    with open('kb_retrieval_test_results.json', 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'knowledge_bases': KBS,
            'total_tests': total,
            'passed': passed,
            'success_rate': f"{passed/total*100:.1f}%",
            'results': results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to kb_retrieval_test_results.json")
    
    # Final status
    print(f"\n{'='*70}")
    if passed == total:
        print("✅ ALL TESTS PASSED - Knowledge Base retrieval working correctly!")
    elif passed >= total * 0.8:
        print(f"⚠️ MOSTLY PASSED - {total - passed} test(s) failed")
    else:
        print(f"❌ FAILED - {total - passed} test(s) failed")
    print(f"{'='*70}\n")
    
    return passed >= total * 0.8

if __name__ == '__main__':
    success = test_kb_retrieval()
    exit(0 if success else 1)
