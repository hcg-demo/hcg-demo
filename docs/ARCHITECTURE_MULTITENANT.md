# Multi-Tenant API Architecture

Python Flask API on AWS Lambda + API Gateway + Aurora Serverless PostgreSQL. Setup via Amazon Q (Cursor integration, no MCP).

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web App / Mobile App                                                        │
│  • Sends X-Tenant-ID header on every request                                 │
│  • REST API (GET, POST, PUT, DELETE)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Amazon API Gateway (REST API)                                                │
│  • /items/{item_id} – proxy to Lambda                                        │
│  • CORS, throttling, API keys (if needed)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPUTE LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  AWS Lambda (Python 3.9, Flask)                                               │
│  • Handler: app.lambda_handler                                                │
│  • Parses API Gateway event, extracts X-Tenant-ID                             │
│  • Routes by HTTP method (POST/GET/PUT/DELETE)                                │
│  • CRUD on tenant_{id}.items                                                 │
│  • Environment: DB_SECRET_ARN, DB_NAME, DB_CLUSTER_ARN                        │
└─────────────────────────────────────────────────────────────────────────────┘
                      ↓                                    ↓
┌──────────────────────────────┐    ┌──────────────────────────────────────────┐
│  AWS Secrets Manager          │    │  Amazon Aurora Serverless PostgreSQL     │
│  • DB credentials             │    │  • Single cluster                         │
│  • Cached in Lambda warm      │    │  • Multi-tenant schemas                   │
│  • Referenced by ARN           │    │  • tenant_{id}.items per tenant          │
└──────────────────────────────┘    │  • public schema for shared tables        │
                                     └──────────────────────────────────────────┘
                                    ↑
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING (optional)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Amazon CloudWatch, AWS X-Ray                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Stack

### 1. Aurora Serverless (CloudFormation)
- `AWS::RDS::DBCluster` (aurora-postgresql, serverless)
- `AWS::RDS::DBSubnetGroup`
- `AWS::EC2::SecurityGroup` (port 5432)
- `AWS::SecretsManager::Secret` (master credentials)
- Outputs: `DBClusterARN`, `DBSecretARN`

### 2. Lambda + API (AWS SAM)
- `AWS::Serverless::Function`: app.lambda_handler
- `AWS::Serverless::Api`: REST API
- Policies: `AWSLambdaBasicExecutionRole`, `SecretsManagerReadWrite`, optionally `AmazonRDSDataFullAccess`
- Environment variables from Aurora stack outputs

### 3. Deployment Order
1. Deploy Aurora + Secrets stack
2. Update SAM template with secret/cluster ARNs (or use parameters)
3. `sam build` → `sam deploy`

---

## Data Model

| Schema   | Purpose                     | Example                          |
|----------|-----------------------------|----------------------------------|
| `public` | Shared tables               | tenants, config                  |
| `tenant_<id>` | Tenant-specific tables | `tenant_123.items`               |

---

## Request Flow

1. Client sends request with `X-Tenant-ID: 123`
2. API Gateway forwards to Lambda
3. Lambda parses event → validates tenant_id → `tenant_123.items`
4. Lambda fetches secret (cached) → connects to Aurora
5. CRUD on `tenant_123.items` → JSON response
6. API Gateway returns to client

---

## Related Docs

- [LESSONS_LEARNED_MULTITENANT.md](LESSONS_LEARNED_MULTITENANT.md)
- [DOS_AND_DONTS_MULTITENANT.md](DOS_AND_DONTS_MULTITENANT.md)
