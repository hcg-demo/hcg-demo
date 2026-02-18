# Multi-Tenant Aurora + Lambda API – Lessons Learned

From Amazon Q setup: Python Flask API, AWS Lambda, API Gateway, Aurora Serverless PostgreSQL, AWS SAM. No MCP.

---

## 1. Architecture

### Flow
```
Client (Web/Mobile) → API Gateway (REST) → Lambda (Python/Flask) → Aurora Serverless PostgreSQL
                                                      ↓
                                            Secrets Manager (DB creds)
```

### Key Choices
- **Single Aurora instance**, multiple schemas per tenant (shared infrastructure)
- **Schema model**: `db` schema for tenant-specific tables (e.g. `tenant_{id}.items`), `public` for shared
- **Tenant context**: `X-Tenant-ID` header on every request
- **Compute**: Lambda with Flask adapter; no container needed for simple CRUD

---

## 2. Infrastructure

### Aurora Serverless PostgreSQL
- Use CloudFormation `AWS::RDS::DBCluster` with `engineMode: serverless`
- Configure scaling (min/max ACUs)
- Security group on port 5432
- Store credentials in Secrets Manager; reference by ARN
- DB Subnet Group for VPC placement

### Secrets Manager
- One secret per RDS cluster (username, password, host, etc.)
- Lambda: `get_secret_value()` with `boto3`
- Cache secret values across warm invocations to avoid repeated calls
- IAM: `secretsmanager:GetSecretValue` on the secret ARN

### Lambda + VPC vs RDS Data API
- **psycopg2**: Lambda must run in VPC to reach Aurora; requires VPC config and longer cold start
- **RDS Data API**: Lambda can run without VPC; uses HTTPS; needs `AmazonRDSDataFullAccess` (or similar)
- Be consistent: if using `psycopg2`, attach Lambda to VPC; if using Data API, do not configure VPC

---

## 3. Code

### CRUD Pattern
- Parse API Gateway event → extract `X-Tenant-ID` → build table/schema name (`tenant_{id}.items`)
- Validate tenant_id before use
- Use parameterized queries; never string-concatenate user input into SQL

### Lambda Handler
- Single handler (e.g. `lambda_handler`) that routes by HTTP method: POST (create), GET (read), PUT (update), DELETE (delete)
- Parse `event['httpMethod']` and `event['pathParameters']` for routing
- Return proper status codes (200, 201, 400, 404, 500) and JSON body

### Connection Handling
- Reuse connections in warm Lambda invocations
- Use context vars or module-level caching for connection
- Handle connection failures and retries cleanly

---

## 4. Deployment

### AWS SAM
- `template.yaml`: `Transform: AWS::Serverless-2016-10-31`
- Function: `Handler: app.lambda_handler`, `Runtime: python3.9`, `CodeUri: ./`
- Environment: `DB_SECRET_ARN`, `DB_NAME`, `DB_CLUSTER_ARN` (from Aurora stack outputs)
- API Gateway: e.g. `/items/{item_id}` with `any` method → single Lambda
- Order: Deploy Aurora + Secrets first → get ARNs → pass into SAM template

### SAM CLI
```
sam init
sam build
sam deploy --guided
```

---

## 5. Multi-Tenancy

### Schema Strategy
- One schema per tenant: `tenant_<id>`
- Shared metadata in `public`
- Create schema and tables on first tenant access or during provisioning

### Tenant Isolation
- Always validate `X-Tenant-ID` before any DB access
- Reject or 400 if missing/invalid
- Use tenant_id only from header, never from body/path alone

---

## 6. Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Lambda can't reach Aurora | Lambda not in VPC | Add VPC config to Lambda or switch to RDS Data API |
| Slow cold starts | VPC + psycopg2 | Use RDS Data API or provisioned concurrency |
| Secret fetch on every request | No caching | Cache secret in module/global; refresh on expiry |
| Wrong tenant data | Missing X-Tenant-ID check | Validate header; fail fast if missing |
| SAM deploy fails | Missing env vars | Ensure Aurora outputs (ARNs) passed to SAM |
