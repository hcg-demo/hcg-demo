# Repository Structure

**Single repo**: Local folder `C:\Users\ppandya\Git_DB_Cursor\desktop-tutorial-1` ↔ GitHub [hcg-demo/hcg-demo](https://github.com/hcg-demo/hcg-demo).  
See [REPO_SETUP.md](REPO_SETUP.md) for details.

```
.github/
  workflows/          # CI/CD pipelines
    ci.yml            # Lint, structure validation

docs/                 # Documentation
  ARCHITECTURE.md           # HCG Demo (Slack, Bedrock, ServiceNow)
  ARCHITECTURE_MULTITENANT.md  # Multi-tenant Aurora + Lambda API
  LESSONS_LEARNED.md        # Slack/ServiceNow
  LESSONS_LEARNED_MULTITENANT.md
  DOS_AND_DONTS.md
  DOS_AND_DONTS_MULTITENANT.md
  ...

gates/                # Quality gates, pre-deploy validation
  validate_config.py
  README.md

scripts/              # Deployment, setup, utilities
  deploy_all_slack_fixes.py
  deploy_slack_fixes.py
  setup_webhook_api.py
  upload_kb_docs.py
  ...
  infra/              # Infrastructure scripts
    setup_servicenow.py
    add_webhook_permissions.py
    ...
  eval/               # Evaluation scripts

src/                  # Lambda source code
  lambda_webhook_handler.py
  lambda_supervisor_agent.py
  lambda_servicenow_simple.py
  lambda_authorizer.py
  ...

tests/                # Test scripts
  test_kb_retrieval.py
  test_servicenow_direct.py
  test_slack_flow.py
  ...

Sample Data/          # Sample documents for KB ingestion
  hr/
  it/
  finance/
  general/
```

## Run from project root

- Deploy: `python scripts/deploy_all_slack_fixes.py`
- Setup ServiceNow: `python scripts/infra/setup_servicenow.py`
- Run tests: `python tests/test_kb_retrieval.py`
