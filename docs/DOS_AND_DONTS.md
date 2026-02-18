# HCG Demo – Do's and Don'ts

## Infrastructure

| Do | Don't |
|----|-------|
| Use `channel_ts` for idempotency (not just `event_id`) | Assume `event_id` is unique across Slack event types |
| Return 200 to Slack within 3 seconds | Block Slack response for 15+ seconds (causes retries) |
| Add TTL to idempotency table items | Leave idempotency rows indefinitely |
| Reserve Lambda concurrency for webhook | Rely on default (0 = account limit) |
| Store ServiceNow creds in SSM or Secrets Manager | Hardcode credentials in code |
| Use `ssl.CERT_NONE` for ServiceNow dev instances | Use strict SSL verification against self-signed certs |

## Code

| Do | Don't |
|----|-------|
| Sanitize text (smart quotes, Unicode) before Bedrock | Send raw Slack text that may break JSON/API |
| Handle both Secrets Manager and SSM for ServiceNow | Assume a single credential source |
| Support common typos (`crate` → `create`) | Match only exact phrases |
| Process only `app_mention` and `message` in DMs | Process every Slack event type |
| Add "need a software" to ticket keywords | Limit ticket detection to "create ticket" only |
| Match Lambda handler to deployed module name | Deploy `lambda_function.py` but keep handler as `lambda_servicenow_v2` |

## Testing

| Do | Don't |
|----|-------|
| Test ServiceNow with SSL disabled locally | Expect local SSL to work on dev instances |
| Verify both direct KB and supervisor flows | Test only one path |
| Run `deploy_all_slack_fixes.py` after changes | Manually update Lambdas one by one |
| Check CloudWatch for webhook version tag | Assume code is deployed without checking logs |
| Test ticket creation before going live | Assume ServiceNow works without a test call |

## Deployment

| Do | Don't |
|----|-------|
| Deploy in order: infra → Lambdas → config | Skip dependencies (e.g. DynamoDB, IAM) |
| Wait 15–20 seconds before re-running config updates | Retry immediately after code deploy |
| Run `infra/add_servicenow_ssm_permission.py` if using SSM | Forget SSM permissions for ServiceNow Lambda |
| Use `deploy_all_slack_fixes.py` for a full deploy | Deploy only some components |

## Secrets & Credentials

| Do | Don't |
|----|-------|
| Use `SecureString` for passwords in SSM | Store passwords as plain `String` |
| Keep Secrets Manager and SSM in sync if both used | Update one and leave the other stale |
| Rotate credentials periodically | Leave default/test passwords in production |
| Use API/integration users for ServiceNow | Use personal accounts with MFA |

## Slack

| Do | Don't |
|----|-------|
| Subscribe to `app_mention` for @mentions | Rely only on `message.channels` |
| Respond in the same thread (`thread_ts`) | Post only to the channel (hard to follow) |
| Handle `url_verification` in the authorizer | Block or fail URL verification |
| Use bot token with correct OAuth scopes | Use user token or missing scopes |
