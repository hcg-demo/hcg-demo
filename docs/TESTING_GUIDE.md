# HCG_DEMO Testing Guide

## Automated Test Results

**Overall Success Rate**: 93.8% (30/32 tests passed)

Run automated tests:
```bash
python test_migration.py
```

---

## Manual Testing Checklist

### 1. Slack Integration Test (Week 3)

**Prerequisites**:
- Slack app created at https://api.slack.com/apps
- Bot token and signing secret configured

**Steps**:
1. Configure Slack Event Subscriptions:
   - URL: `https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/slack/events`
   - Subscribe to events: `message.channels`, `app_mention`

2. Install app to workspace

3. Send test message in Slack channel where bot is added:
   ```
   @HCG_Demo What are the company benefits?
   ```

4. **Expected Results**:
   - ✅ Slack shows "Verified" on Event Subscriptions URL
   - ✅ Bot responds within 15 seconds
   - ✅ CloudWatch logs show webhook-handler execution
   - ✅ DynamoDB `hcg-demo-sessions` table has new entry

**Validation**:
```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/hcg-demo-webhook-handler --follow

# Check DynamoDB
aws dynamodb scan --table-name hcg-demo-sessions --limit 5
```

---

### 2. Bedrock Agent Test (Week 5-6)

**Test Supervisor Agent Routing**:

1. Go to AWS Console → Bedrock → Agents
2. Select `hcg-demo-supervisor` (DP6QVL8GPS)
3. Click "Test" button

**Test Cases**:

| Query | Expected Agent | Expected Response |
|-------|---------------|-------------------|
| "What are the HR benefits?" | HR Agent | Information about benefits |
| "My laptop is not working" | IT Agent | Troubleshooting steps |
| "How do I submit expenses?" | Finance Agent | Expense submission process |
| "Where is the office located?" | General Agent | Office location info |

**Validation**:
- ✅ Supervisor correctly identifies intent
- ✅ Routes to appropriate specialist agent
- ✅ Agent provides relevant response
- ✅ Response time < 15 seconds

---

### 3. Knowledge Base Test (Week 4)

**Prerequisites**:
- Upload sample documents to S3:
  ```bash
  aws s3 cp hr_policy.pdf s3://hcg-demo-knowledge-026138522123/hr/
  aws s3 cp it_guide.pdf s3://hcg-demo-knowledge-026138522123/it/
  ```

**Steps**:
1. Create Knowledge Bases via AWS Console:
   - Go to Bedrock → Knowledge bases → Create
   - Link to OpenSearch collection: `y3f4j35z37u9awc6sqkc`
   - Add S3 data source

2. Sync Knowledge Base

3. Test retrieval:
   - Query agent with question from uploaded document
   - Verify agent cites source document

**Validation**:
- ✅ Knowledge Base sync completes successfully
- ✅ Agent retrieves relevant information
- ✅ Response includes citations

---

### 4. ServiceNow Integration Test (Week 7 - Future)

**Prerequisites**:
- ServiceNow instance: https://dev355778.service-now.com
- OAuth credentials configured

**Steps**:
1. Create ServiceNow Action Group Lambda
2. Attach to IT Agent
3. Test ticket creation:
   ```
   @HCG_Demo Create a ticket: My laptop screen is broken
   ```

**Expected Results**:
- ✅ Ticket created in ServiceNow
- ✅ Ticket number returned to user
- ✅ User can query ticket status

---

## Performance Testing

### Load Test (Week 8)

**Target**: 500 concurrent users

**Tool**: Apache JMeter or Locust

**Test Script**:
```python
# locust_test.py
from locust import HttpUser, task, between

class SlackWebhookUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def send_message(self):
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Test query",
                "user": "U123456",
                "channel": "C123456"
            }
        }
        self.client.post("/slack/events", json=payload)
```

**Run**:
```bash
locust -f locust_test.py --host https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod
```

**Success Criteria**:
- ✅ p95 latency < 15 seconds
- ✅ Error rate < 1%
- ✅ No Lambda throttling
- ✅ DynamoDB auto-scales

---

## Security Testing

### 1. API Gateway Authorization Test

**Test Invalid Signature**:
```bash
curl -X POST https://arep4vvhlc.execute-api.ap-southeast-1.amazonaws.com/prod/slack/events \
  -H "Content-Type: application/json" \
  -H "X-Slack-Request-Timestamp: $(date +%s)" \
  -H "X-Slack-Signature: v0=invalid_signature" \
  -d '{"type":"url_verification","challenge":"test"}'
```

**Expected**: 403 Forbidden

### 2. IAM Policy Test

**Verify Least Privilege**:
```bash
# Lambda should NOT be able to delete S3 buckets
aws lambda invoke --function-name hcg-demo-webhook-handler \
  --payload '{"test":"delete_bucket"}' response.json
```

**Expected**: Access Denied

### 3. Secrets Rotation Test

**Rotate ServiceNow Secret**:
```bash
aws secretsmanager rotate-secret \
  --secret-id hcg-demo/servicenow/oauth
```

**Expected**: ✅ Rotation successful, Lambda picks up new credentials

---

## Monitoring & Observability

### CloudWatch Dashboard

**Create Dashboard**:
1. Go to CloudWatch → Dashboards → Create
2. Add widgets:
   - API Gateway 4XX/5XX errors
   - Lambda invocations & errors
   - DynamoDB read/write capacity
   - Bedrock invocation count

### Alarms

**Set up alarms**:
```bash
# Lambda error rate > 5%
aws cloudwatch put-metric-alarm \
  --alarm-name hcg-demo-lambda-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting Common Issues

### Issue 1: Slack Webhook Verification Fails
**Cause**: Invalid signing secret
**Fix**: 
```bash
aws secretsmanager update-secret \
  --secret-id hcg-demo/slack/credentials \
  --secret-string '{"SLACK_SIGNING_SECRET":"correct_secret"}'
```

### Issue 2: Lambda Timeout
**Cause**: Cold start or slow Bedrock response
**Fix**: Increase timeout to 60 seconds
```bash
aws lambda update-function-configuration \
  --function-name hcg-demo-webhook-handler \
  --timeout 60
```

### Issue 3: Bedrock Agent Not Responding
**Cause**: Agent not prepared
**Fix**: Prepare agent
```bash
aws bedrock-agent prepare-agent --agent-id DP6QVL8GPS
```

---

## Test Results Log

| Test Date | Component | Status | Notes |
|-----------|-----------|--------|-------|
| 2025-02-04 | Automated Tests | ✅ 93.8% | 30/32 passed |
| | Slack Integration | ⏳ Pending | Awaiting Slack app config |
| | Bedrock Agents | ✅ Pass | All 5 agents active |
| | Knowledge Bases | ⏳ Pending | Awaiting document upload |
| | ServiceNow | ⏳ Pending | Week 7 implementation |

---

## Next Steps

1. ✅ Complete Slack app configuration
2. ✅ Upload knowledge documents to S3
3. ✅ Create and sync Knowledge Bases
4. ✅ Test end-to-end user flow
5. ⏳ Implement ServiceNow integration
6. ⏳ Conduct load testing
7. ⏳ Set up monitoring dashboards

---

**Test Status**: Ready for manual validation
**Automated Coverage**: 93.8%
**Manual Tests Required**: 5
