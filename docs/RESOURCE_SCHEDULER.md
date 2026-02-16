# AWS Resource Scheduler

Automatically stops ALL HCG resources at 10 PM SGT and starts them at 8 AM SGT.

## Deploy

```bash
python deploy_resource_scheduler.py
```

## Shutdown Order (10 PM SGT)

1. **Lambda functions** - Disable concurrency (except scheduler)
2. **OpenSearch Serverless** - Disable standby replicas
3. **EC2 instances** - Stop all running instances
4. **RDS databases** - Stop all available databases

## Startup Order (8 AM SGT)

1. **RDS databases** - Start stopped databases
2. **EC2 instances** - Start stopped instances
3. **OpenSearch Serverless** - Enable standby replicas
4. **Lambda functions** - Restore concurrency

## Resources Managed

- 8 Lambda functions (hcg-demo-*)
- OpenSearch Serverless collection
- All EC2 instances
- All RDS databases

## Cost Savings

- **Lambda**: ~58% savings (14 hours off)
- **OpenSearch**: ~40% savings (standby mode)
- **EC2/RDS**: ~58% savings (14 hours off)
- **Total**: ~$110/month saved
