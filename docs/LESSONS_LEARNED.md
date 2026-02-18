# HCG Demo – Lessons Learned

Setup and integration lessons from Slack + ServiceNow + Bedrock KB implementation.

---

## 1. Infrastructure

### Slack Webhook
- **API Gateway timeout**: Default 29s. Increase to 60s for sync processing; or use fast-ack to return 200 quickly.
- **Lambda timeout**: Set webhook and supervisor to 60s.
- **Concurrency**: Reserve concurrency (e.g. 50) to avoid throttling under load.
- **DynamoDB idempotency**: Use a table (e.g. `hcg-demo-processed-events`) with `eventId` as partition key and TTL for cleanup.
- **Idempotency key**: Prefer `channel_ts` over `event_id` because Slack can send both `app_mention` and `message` with different `event_id`s for the same message.

### ServiceNow
- **Credentials**: Lambda checks Secrets Manager first, then SSM. Keep both aligned or only one populated.
- **Secret format**: JSON with `instance_url`, `username`, `password`.
- **SSM parameters**: `/hcg-demo/servicenow/instance-url`, `username`, `password`.
- **SSL**: Dev instances often use self-signed certs; use `ssl.CERT_NONE` in requests.
- **IAM**: Lambda needs `ssm:GetParameters` (with decryption) and `secretsmanager:GetSecretValue` if using both.

### Bedrock Agents & KBs
- **KB IDs**: HR H0LFPBHIAK, IT X1VW7AMIK8, Finance 1MFT5GZYTT, General BOLGBDCUAZ.
- **Alias**: Agents use `TSTALIASID`.
- **Fallback**: If agent invoke fails, use direct KB `retrieve()`.
- **Score threshold**: 0.5+ for KB; General KB may score lower and need 0.4 if desired.

---

## 2. Code

### Webhook Handler
- **Fast-ack**: Return 200 within ~3 seconds; do the work in an async self-invoke to avoid Slack retries and duplicate tickets.
- **Event filtering**: Process only `app_mention` (channels) or `message` where channel starts with `D` (DMs).
- **Text sanitization**: Normalize smart quotes and Unicode apostrophes before sending to Bedrock.
- **Self-invoke**: Lambda needs `lambda:InvokeFunction` on itself for async processing.

### Supervisor / Routing
- **Ticket detection**: Support typos (`crate` → `create`) and phrases like `need a software`.
- **ServiceNow payload**: Lambda uses Bedrock-style format: `response.responseBody.TEXT.body`.
- **Keyword routing**: HR (holidays, leave, benefits), IT (password, laptop, VPN, ticket), Finance (expense, invoice, procurement), General (fallback).

### ServiceNow Lambda
- **Handler**: Ensure deployed handler matches packaged module (e.g. `lambda_function.lambda_handler`).
- **Response format**: Return `{ response: { responseBody: { TEXT: { body: "✅ Incident created: INC0010001" } } } }`.
- **Dual credentials**: Try Secrets Manager first, then SSM for flexibility.

---

## 3. Testing

### Local Tests
- **Direct KB retrieve**: Use `bedrock.retrieve()` for KB-only checks.
- **Supervisor flow**: Invoke `hcg-demo-supervisor-agent` with `{ body: { query, session_id } }`.
- **ServiceNow**: Call Lambda directly with `actionGroup`, `apiPath`, `parameters`.
- **SSL**: Use `ssl.CERT_NONE` when testing against dev instances locally.

### Test Scripts
- `test_kb_retrieval.py` – KB and supervisor flows.
- `test_servicenow_direct.py` – ServiceNow API with SSM creds.
- `test_slack_flow.py` – Simulated Slack flow.

### Verification
- Check CloudWatch logs for `[v4-fast-ack]` to confirm deployed webhook version.
- Verify ticket creation in ServiceNow UI.
- Confirm no duplicate Slack messages.

---

## 4. Deployment

### Order
1. DynamoDB processed-events table.
2. Lambda IAM permissions (webhook self-invoke, SSM, Secrets Manager).
3. Webhook, supervisor, ServiceNow Lambda.
4. Handler config (ServiceNow Lambda).
5. Timeouts and concurrency.

### Single Deploy
- `python deploy_all_slack_fixes.py` – deploys authorizer, webhook, supervisor, ServiceNow Lambda.
- Retry config updates after code deploy; `ResourceConflictException` means Lambda is still updating.

### Credentials
- Run `python scripts/infra/setup_servicenow.py` for interactive SSM setup.
- Or update Secrets Manager `hcg-demo/servicenow/creds` directly.

---

## 5. Slack Configuration

### Event Subscriptions
- Subscribe to `app_mention` and `message.im` (DMs).
- Avoid `message.channels` if it causes duplicates with `app_mention`.

### OAuth Scopes
- `chat:write`, `app_mentions:read`, `channels:history` (for channels), `im:history` (for DMs).

### URL Verification
- Authorizer must allow `url_verification` and return the challenge body.

---

## 6. Common Issues

| Issue              | Cause                        | Fix                                                  |
|--------------------|------------------------------|------------------------------------------------------|
| Duplicate tickets  | Slack retries (slow response)| Fast-ack: return 200 quickly, process async          |
| Duplicate replies  | app_mention + message        | Filter event types; use channel_ts for idempotency   |
| 401 ServiceNow     | Wrong creds or wrong source  | Update Secrets Manager and/or SSM                     |
| No ticket details  | Wrong response parsing       | Parse `response.responseBody.TEXT.body`              |
| Password reset fails| IT KB not matching          | Ensure password_reset doc is in IT KB                |
| “Crate” not recognized | Typo                    | Add “crate a ticket” to ticket keywords             |
