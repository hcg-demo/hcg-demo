# HCG_DEMO Architecture Documentation

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SLACK WORKSPACE                                 │
│                         (User sends message)                                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS CLOUD (ap-southeast-1)                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        API GATEWAY (arep4vvhlc)                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ GET /health  │  │POST /slack/  │  │  Custom      │             │    │
│  │  │   (Mock)     │  │   events     │  │ Authorizer   │             │    │
│  │  └──────────────┘  └──────┬───────┘  └──────┬───────┘             │    │
│  └────────────────────────────┼──────────────────┼──────────────────────┘    │
│                               │                  │                           │
│                               │                  │                           │
│  ┌────────────────────────────▼──────────────────▼──────────────────────┐   │
│  │                    VPC (vpc-0382b710049feecd6)                        │   │
│  │                         CIDR: 10.0.0.0/16                             │   │
│  │                                                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │              PUBLIC SUBNETS (2 AZs)                             │ │   │
│  │  │  ┌──────────────────┐         ┌──────────────────┐             │ │   │
│  │  │  │ public-1a        │         │ public-1b        │             │ │   │
│  │  │  │ 10.0.1.0/24      │         │ 10.0.2.0/24      │             │ │   │
│  │  │  │                  │         │                  │             │ │   │
│  │  │  │ ┌──────────────┐ │         │                  │             │ │   │
│  │  │  │ │ NAT Gateway  │ │         │                  │             │ │   │
│  │  │  │ │ (nat-01b8d..)│ │         │                  │             │ │   │
│  │  │  │ └──────────────┘ │         │                  │             │ │   │
│  │  │  └──────────────────┘         └──────────────────┘             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                               │                                       │   │
│  │                               │ Internet Gateway                      │   │
│  │                               │ (igw-0bc65b8..)                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │              PRIVATE SUBNETS (2 AZs)                            │ │   │
│  │  │  ┌──────────────────┐         ┌──────────────────┐             │ │   │
│  │  │  │ private-1a       │         │ private-1b       │             │ │   │
│  │  │  │ 10.0.10.0/24     │         │ 10.0.11.0/24     │             │ │   │
│  │  │  │                  │         │                  │             │ │   │
│  │  │  │ ┌──────────────┐ │         │ ┌──────────────┐ │             │ │   │
│  │  │  │ │   Lambda     │ │         │ │   Lambda     │ │             │ │   │
│  │  │  │ │ - Authorizer │ │         │ │  (Standby)   │ │             │ │   │
│  │  │  │ │ - Webhook    │ │         │ │              │ │             │ │   │
│  │  │  │ │   Handler    │ │         │ │              │ │             │ │   │
│  │  │  │ └──────────────┘ │         │ └──────────────┘ │             │ │   │
│  │  │  └──────────────────┘         └──────────────────┘             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    VPC ENDPOINTS                                 │ │   │
│  │  │  • S3 Gateway Endpoint                                           │ │   │
│  │  │  • DynamoDB Gateway Endpoint                                     │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      LAMBDA FUNCTIONS                               │    │
│  │  ┌──────────────────────┐    ┌──────────────────────┐              │    │
│  │  │ hcg-demo-authorizer  │    │ hcg-demo-webhook-    │              │    │
│  │  │ • Validates Slack    │    │      handler         │              │    │
│  │  │   signatures         │    │ • Processes events   │              │    │
│  │  │ • Returns Allow/Deny │    │ • Stores sessions    │              │    │
│  │  └──────────┬───────────┘    └──────────┬───────────┘              │    │
│  └─────────────┼──────────────────────────┼──────────────────────────────┘    │
│                │                          │                                   │
│                ▼                          ▼                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    SECRETS MANAGER                                  │    │
│  │  • hcg-demo/slack/credentials                                       │    │
│  │  • hcg-demo/servicenow/oauth                                        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      BEDROCK AGENTS                                 │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │  Supervisor Agent (DP6QVL8GPS)                               │  │    │
│  │  │  • Intent Classification                                      │  │    │
│  │  │  • Routes to specialist agents                               │  │    │
│  │  └────────────┬─────────────────────────────────────────────────┘  │    │
│  │               │                                                     │    │
│  │       ┌───────┴───────┬──────────┬──────────┬──────────┐          │    │
│  │       ▼               ▼          ▼          ▼          ▼          │    │
│  │  ┌────────┐    ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │    │
│  │  │   HR   │    │   IT   │  │Finance │  │General │  │        │   │    │
│  │  │ Agent  │    │ Agent  │  │ Agent  │  │ Agent  │  │        │   │    │
│  │  │(IEVMS..)│   │(ZMLHZ..)│ │(8H5G4..)│ │(RY3QR..)│ │        │   │    │
│  │  └────┬───┘    └────┬───┘  └────┬───┘  └────┬───┘  └────────┘   │    │
│  │       │             │           │           │                     │    │
│  │       └─────────────┴───────────┴───────────┘                     │    │
│  │                     │                                              │    │
│  │                     ▼                                              │    │
│  │  ┌──────────────────────────────────────────────────────────────┐ │    │
│  │  │         BEDROCK KNOWLEDGE BASES (To be created)              │ │    │
│  │  │  • HR KB  • IT KB  • Finance KB  • General KB                │ │    │
│  │  └────────────────────────┬─────────────────────────────────────┘ │    │
│  └───────────────────────────┼───────────────────────────────────────┘    │
│                               │                                            │
│                               ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │              OPENSEARCH SERVERLESS (y3f4j35z37u9awc6sqkc)          │   │
│  │              • Vector Search Collection                             │   │
│  │              • Stores embeddings for RAG                            │   │
│  │              • Cost: $175/month (can be deleted)                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                         DYNAMODB TABLES                             │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │   │
│  │  │ hcg-demo-        │  │ hcg-demo-        │  │ hcg-demo-        │ │   │
│  │  │   sessions       │  │   users          │  │   feedback       │ │   │
│  │  │ • Session state  │  │ • User mapping   │  │ • User feedback  │ │   │
│  │  │ • TTL: 8 hours   │  │ • GSI: email     │  │ • GSI: session   │ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                           S3 BUCKETS                                │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │   │
│  │  │ hcg-demo-        │  │ hcg-demo-        │  │ hcg-demo-        │ │   │
│  │  │  knowledge-...   │  │  logs-...        │  │  cloudtrail-...  │ │   │
│  │  │ • hr/            │  │ • access-logs/   │  │ • Audit logs     │ │   │
│  │  │ • it/            │  │ • app-logs/      │  │                  │ │   │
│  │  │ • finance/       │  │                  │  │                  │ │   │
│  │  │ • general/       │  │                  │  │                  │ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                      OBSERVABILITY                                  │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │   │
│  │  │  CloudWatch      │  │  CloudTrail      │  │  Cognito         │ │   │
│  │  │  • 5 Log Groups  │  │  • Audit trail   │  │  • User Pool     │ │   │
│  │  │  • Metrics       │  │  • Compliance    │  │  • SSO (future)  │ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVICENOW (dev355778)                               │
│                    • Create tickets (future)                                 │
│                    • Query tickets                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
USER QUERY FLOW:
═══════════════

1. User sends message in Slack
   │
   ▼
2. Slack → API Gateway POST /slack/events
   │
   ▼
3. API Gateway → Lambda Authorizer
   │  (Validates Slack signature)
   ▼
4. Lambda Authorizer → Secrets Manager
   │  (Gets signing secret)
   ▼
5. Returns Allow/Deny → API Gateway
   │
   ▼
6. API Gateway → Lambda Webhook Handler
   │
   ▼
7. Lambda Webhook Handler:
   │  • Parses event
   │  • Stores session in DynamoDB
   │  • Invokes Bedrock Supervisor Agent
   │
   ▼
8. Bedrock Supervisor Agent:
   │  • Classifies intent (HR/IT/Finance/General)
   │  • Routes to specialist agent
   │
   ▼
9. Specialist Agent (e.g., IT Agent):
   │  • Queries Knowledge Base
   │  • Retrieves from OpenSearch
   │  • Generates response
   │  • (Optional) Creates ServiceNow ticket
   │
   ▼
10. Response → Lambda → API Gateway → Slack
    │
    ▼
11. User sees response in Slack thread
```

## Network Architecture

```
INTERNET
   │
   ▼
┌──────────────────┐
│ Internet Gateway │
│ (igw-0bc65b8..)  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Public │ │Public │
│Subnet │ │Subnet │
│  1a   │ │  1b   │
└───┬───┘ └───────┘
    │
┌───▼────────┐
│NAT Gateway │
│(nat-01b8d..)│
└───┬────────┘
    │
    ▼
┌────────────┐ ┌────────────┐
│  Private   │ │  Private   │
│  Subnet 1a │ │  Subnet 1b │
│            │ │            │
│  Lambda    │ │  Lambda    │
│  Functions │ │  (Standby) │
└────┬───────┘ └────────────┘
     │
     ├─→ VPC Endpoint (S3)
     ├─→ VPC Endpoint (DynamoDB)
     └─→ NAT Gateway → Internet (Bedrock, Slack)
```

## Security Architecture

```
┌─────────────────────────────────────────┐
│         SECURITY LAYERS                 │
├─────────────────────────────────────────┤
│                                         │
│  1. API Gateway                         │
│     └─→ Custom Authorizer               │
│         └─→ Slack Signature Validation  │
│                                         │
│  2. VPC Isolation                       │
│     └─→ Private Subnets                 │
│         └─→ No direct internet access   │
│                                         │
│  3. IAM Roles (Least Privilege)         │
│     ├─→ Lambda execution role           │
│     ├─→ Bedrock agent role              │
│     └─→ Step Functions role             │
│                                         │
│  4. Secrets Manager                     │
│     └─→ Encrypted credentials           │
│                                         │
│  5. CloudTrail                          │
│     └─→ Audit all API calls             │
│                                         │
│  6. S3 Bucket Policies                  │
│     └─→ Block public access             │
│                                         │
└─────────────────────────────────────────┘
```

## Component Inventory

| Layer | Component | ID/Name | Status |
|-------|-----------|---------|--------|
| **Network** | VPC | vpc-0382b710049feecd6 | ✅ Active |
| | NAT Gateway | nat-01b8dfbb36ae3f811 | ✅ Active |
| | Internet Gateway | igw-0bc65b8460df32470 | ✅ Active |
| **API** | API Gateway | arep4vvhlc | ✅ Active |
| | Custom Authorizer | 3kf3gf | ✅ Active |
| **Compute** | Lambda Authorizer | hcg-demo-authorizer | ✅ Active |
| | Lambda Webhook | hcg-demo-webhook-handler | ✅ Active |
| **AI/ML** | Supervisor Agent | DP6QVL8GPS | ✅ Active |
| | HR Agent | IEVMSZT1GY | ✅ Active |
| | IT Agent | ZMLHZEZZXO | ✅ Active |
| | Finance Agent | 8H5G4JZVXM | ✅ Active |
| | General Agent | RY3QRSI7VE | ✅ Active |
| **Data** | OpenSearch Collection | y3f4j35z37u9awc6sqkc | ✅ Active |
| | DynamoDB Sessions | hcg-demo-sessions | ✅ Active |
| | DynamoDB Users | hcg-demo-users | ✅ Active |
| | DynamoDB Feedback | hcg-demo-feedback | ✅ Active |
| **Storage** | S3 Knowledge | hcg-demo-knowledge-026138522123 | ✅ Active |
| | S3 Logs | hcg-demo-logs-026138522123 | ✅ Active |
| | S3 CloudTrail | hcg-demo-cloudtrail-026138522123 | ✅ Active |
| **Security** | Secrets Manager | hcg-demo/slack/credentials | ✅ Active |
| | Secrets Manager | hcg-demo/servicenow/oauth | ✅ Active |
| | Cognito User Pool | ap-southeast-1_ONwFGintc | ✅ Active |
| **Observability** | CloudWatch Logs | 5 log groups | ✅ Active |
| | CloudTrail | hcg-demo-audit-trail | ✅ Active |

---

**Total Components**: 40+ AWS resources
**Monthly Cost**: $231 (with OpenSearch) or $56 (without OpenSearch)
**Region**: ap-southeast-1 (Singapore)
