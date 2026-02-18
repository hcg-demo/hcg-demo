# Multi-Tenant Aurora + Lambda API – Do's and Don'ts

---

## Infrastructure

| Do | Don't |
|----|-------|
| Use Aurora Serverless for auto-scaling | Use a fixed-size RDS instance without scaling needs |
| Store DB credentials in Secrets Manager | Hardcode credentials in code or env vars |
| Define Security Groups and Subnet Groups for Aurora | Expose Aurora on 0.0.0.0/0 |
| Pass secret ARN via environment into Lambda | Embed secret values in SAM template |
| Use RDS Data API if avoiding VPC | Mix psycopg2 (VPC) and Data API (non-VPC) without a clear strategy |

## Code

| Do | Don't |
|----|-------|
| Cache secrets in Lambda (module/global) | Fetch from Secrets Manager on every request |
| Validate `X-Tenant-ID` on every request | Trust tenant_id from path or body without header |
| Use parameterized queries (`%s`, `?`) | Concatenate user input into SQL strings |
| Use `tenant_{id}.items` for tenant tables | Put all tenants in one table without isolation |
| Return proper HTTP status codes (200, 201, 400, 404, 500) | Always return 200 with error text in body |

## Deployment

| Do | Don't |
|----|-------|
| Deploy Aurora + Secrets before SAM stack | Deploy Lambda before DB and secret exist |
| Use `sam build` before `sam deploy` | Deploy without building |
| Use `--guided` on first SAM deploy | Skip prompts and guess parameters |
| Wire env vars from Aurora stack outputs | Hardcode ARNs or region in template |

## Multi-Tenancy

| Do | Don't |
|----|-------|
| Use one schema per tenant (`tenant_<id>`) | Share tables without schema or tenant column |
| Enforce `X-Tenant-ID` header | Rely on path or query params for tenant context |
| Create schemas/tables on provisioning or first access | Assume schemas exist without provisioning |
| Keep shared data in `public` | Put tenant-specific data in shared schema |

## IAM & Security

| Do | Don't |
|----|-------|
| Use least-privilege IAM for Lambda | Use `*` or broad wildcards |
| Scope Secrets Manager access to specific secret ARN | Grant `secretsmanager:*` on all secrets |
| Use `AmazonRDSDataFullAccess` only if using Data API | Add RDS policies when using psycopg2 in VPC (not needed) |
