import boto3
import time

def lambda_handler(event, context):
    action = event.get('action')
    region = 'ap-southeast-1'
    
    lambda_client = boto3.client('lambda', region_name=region)
    aoss_client = boto3.client('opensearchserverless', region_name=region)
    ec2 = boto3.client('ec2', region_name=region)
    rds = boto3.client('rds', region_name=region)
    
    results = {'lambda': [], 'opensearch': [], 'ec2': [], 'rds': []}
    
    if action == 'stop':
        # Stop order: Lambda → OpenSearch → EC2 → RDS
        
        # 1. Disable Lambda functions (except this one)
        funcs = lambda_client.list_functions()['Functions']
        for f in funcs:
            if f['FunctionName'] != 'hcg-demo-resource-scheduler' and 'hcg-demo' in f['FunctionName']:
                lambda_client.put_function_concurrency(FunctionName=f['FunctionName'], ReservedConcurrentExecutions=0)
                results['lambda'].append(f['FunctionName'])
        
        time.sleep(5)
        
        # 2. Stop OpenSearch collection (standby mode)
        try:
            colls = aoss_client.list_collections()['collectionSummaries']
            for c in colls:
                if c['name'].startswith('hcg-demo'):
                    aoss_client.update_collection(id=c['id'], standbyReplicas='DISABLED')
                    results['opensearch'].append(c['name'])
        except: pass
        
        time.sleep(5)
        
        # 3. Stop EC2
        instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
        if instance_ids:
            ec2.stop_instances(InstanceIds=instance_ids)
            results['ec2'] = instance_ids
        
        time.sleep(5)
        
        # 4. Stop RDS
        dbs = rds.describe_db_instances()
        for db in dbs['DBInstances']:
            if db['DBInstanceStatus'] == 'available':
                rds.stop_db_instance(DBInstanceIdentifier=db['DBInstanceIdentifier'])
                results['rds'].append(db['DBInstanceIdentifier'])
    
    else:
        # Start order: RDS → EC2 → OpenSearch → Lambda
        
        # 1. Start RDS
        dbs = rds.describe_db_instances()
        for db in dbs['DBInstances']:
            if db['DBInstanceStatus'] == 'stopped':
                rds.start_db_instance(DBInstanceIdentifier=db['DBInstanceIdentifier'])
                results['rds'].append(db['DBInstanceIdentifier'])
        
        time.sleep(30)
        
        # 2. Start EC2
        instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
        instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
        if instance_ids:
            ec2.start_instances(InstanceIds=instance_ids)
            results['ec2'] = instance_ids
        
        time.sleep(30)
        
        # 3. Enable OpenSearch
        try:
            colls = aoss_client.list_collections()['collectionSummaries']
            for c in colls:
                if c['name'].startswith('hcg-demo'):
                    aoss_client.update_collection(id=c['id'], standbyReplicas='ENABLED')
                    results['opensearch'].append(c['name'])
        except: pass
        
        time.sleep(10)
        
        # 4. Enable Lambda functions
        funcs = lambda_client.list_functions()['Functions']
        for f in funcs:
            if f['FunctionName'] != 'hcg-demo-resource-scheduler' and 'hcg-demo' in f['FunctionName']:
                lambda_client.delete_function_concurrency(FunctionName=f['FunctionName'])
                results['lambda'].append(f['FunctionName'])
    
    return {'statusCode': 200, 'body': results}
