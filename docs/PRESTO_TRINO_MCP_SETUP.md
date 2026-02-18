# Presto/Trino MCP Server Setup for Cursor

Query Databricks Delta Lake tables and other S3 outputs from Cursor using natural language, via the **Trino MCP Server** connected to a Trino/Presto cluster.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────────────┐
│     Cursor      │────▶│  mcp-trino (MCP)  │────▶│  Trino Cluster                   │
│                 │     │  Execute queries  │     │  - Delta Lake connector (S3)     │
│  Natural lang   │     │  List tables      │     │  - Hive connector (Parquet/CSV)  │
│  → SQL          │     │  Get schemas      │     │  - AWS Glue metastore            │
└─────────────────┘     └──────────────────┘     └─────────────────┬───────────────┘
                                                                      │
                                                                      ▼
                                                         ┌───────────────────────────┐
                                                         │  S3 Bucket                │
                                                         │  - Delta Lake tables      │
                                                         │  - Parquet / CSV outputs  │
                                                         │  (from Databricks)        │
                                                         └───────────────────────────┘
```

## Prerequisites

- **Trino cluster** that can access your S3 bucket (via EMR, Docker, or managed service)
- **AWS Glue** as metastore (or Hive metastore) for Delta Lake table metadata
- **AWS credentials** configured for S3 and Glue access
- **Java 17+** (for Trino if running locally)

---

## Option A: Amazon EMR with Trino (Recommended for Production)

Use EMR's Trino when tables are (or will be) registered in AWS Glue.

### 1. Create EMR Cluster with Trino

```bash
aws emr create-cluster \
  --name "trino-delta-s3" \
  --release-label emr-7.0.0 \
  --applications Name=Trino \
  --ec2-attributes KeyName=your-key,SubnetId=subnet-xxx \
  --instance-groups InstanceGroupType=MASTER,InstanceCount=1,InstanceType=m5.xlarge \
                   InstanceGroupType=CORE,InstanceCount=2,InstanceType=m5.xlarge \
  --configurations file://trino-config.json \
  --log-uri s3://your-bucket/emr-logs/
```

### 2. EMR Trino Delta Lake Configuration

Create `trino-config.json`:

```json
[
  {
    "Classification": "trino-connector-delta-lake",
    "Properties": {
      "connector.name": "delta_lake",
      "hive.metastore": "glue",
      "hive.metastore.glue.region": "ap-southeast-1",
      "fs.native-s3.enabled": "true",
      "s3.region": "ap-southeast-1"
    }
  }
]
```

### 3. Register Delta Tables in Glue

If Databricks writes Delta tables to S3 but they are **not** in Glue, register them via Trino:

```sql
-- Connect to Trino and run (replace with your S3 path):
CALL delta_lake.system.register_table(
  schema_name => 'mydb',
  table_name  => 'my_delta_table',
  table_location => 's3://your-bucket/databricks/delta/my_table/'
);
```

---

## Option B: Trino in Docker (Local Development)

For local development against real S3 data.

### 1. Create Trino Catalog for Delta Lake + S3

Create `trino-delta-catalog.properties`:

```properties
connector.name=delta_lake
hive.metastore=glue
hive.metastore.glue.region=ap-southeast-1
fs.native-s3.enabled=true
s3.region=ap-southeast-1
```

### 2. Run Trino with Docker

```bash
docker run -d \
  --name trino \
  -p 8080:8080 \
  -v $(pwd)/trino-delta-catalog.properties:/opt/trino/etc/catalog/delta.properties \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  trinodb/trino:456
```

---

## Install mcp-trino on Windows

### Step 1: Download mcp-trino Binary

```powershell
# Create directory for MCP tools
$mcpDir = "$env:USERPROFILE\.cursor\mcp-tools"
New-Item -ItemType Directory -Force -Path $mcpDir | Out-Null

# Download (adjust URL for latest release)
$version = "4.2.1"
$url = "https://github.com/tuannvm/mcp-trino/releases/download/v$version/mcp-trino_${version}_windows_amd64.zip"
Invoke-WebRequest -Uri $url -OutFile "$mcpDir\mcp-trino.zip" -UseBasicParsing

# Extract
Expand-Archive -Path "$mcpDir\mcp-trino.zip" -DestinationPath $mcpDir -Force
Move-Item "$mcpDir\mcp-trino.exe" "$mcpDir\mcp-trino.exe" -Force -ErrorAction SilentlyContinue
```

Or run the provided script (run from project root; may need to run outside sandbox):

```powershell
.\scripts\install_mcp_trino.ps1
```

The script installs to `%USERPROFILE%\.cursor\mcp-tools` or, if that fails, to `<project>\.mcp-tools`.

### Step 2: Add mcp-trino to Cursor MCP Config

Edit `%USERPROFILE%\.cursor\mcp.json` and add the `trino` server:

```json
{
  "mcpServers": {
    "awslabs.aws-api-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "timeout": 120000,
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "ap-southeast-1",
        "AWS_API_MCP_PROFILE_NAME": "default"
      }
    },
    "trino": {
      "command": "C:\\Users\\YOUR_USERNAME\\.cursor\\mcp-tools\\mcp-trino.exe",
      "args": [],
      "timeout": 60000,
      "env": {
        "TRINO_HOST": "localhost",
        "TRINO_PORT": "8080",
        "TRINO_USER": "trino",
        "TRINO_SCHEME": "http",
        "TRINO_CATALOG": "delta_lake",
        "TRINO_SCHEMA": "default",
        "TRINO_QUERY_TIMEOUT": "60",
        "TRINO_ALLOW_WRITE_QUERIES": "false"
      }
    }
  }
}
```

**For EMR Trino**, use:
- `TRINO_HOST`: EMR master node DNS (e.g. `ec2-xx-xx-xx-xx.ap-southeast-1.compute.amazonaws.com`)
- `TRINO_PORT`: `443` (if behind ALB) or `8889` (EMR default)
- `TRINO_SCHEME`: `https` or `http`

---

## Databricks Delta Lake on S3 – Integration

### Sync Databricks Delta to Glue (if using Unity Catalog)

Databricks can sync Delta tables to AWS Glue. See [Delta Lake to Glue sync](https://docs.databricks.com/delta/sharing/concepts.html).

### Using register_table (no Glue sync)

If Delta tables exist only in S3, register each table in Trino:

```sql
CALL delta_lake.system.register_table(
  schema_name => 'mydb',
  table_name  => 'customers',
  table_location => 's3://your-bucket/path/to/delta/table/'
);
```

Ensure the S3 path contains a valid Delta Lake structure (`_delta_log/` directory).

### Query Parquet/CSV (non-Delta) Outputs

Use the **Hive connector** instead of Delta Lake for raw Parquet/CSV files:

```properties
connector.name=hive
hive.metastore=glue
hive.s3.enabled=true
```

---

## Usage in Cursor

Once configured, you can ask in natural language:

- *"Show me all schemas in the delta_lake catalog"*
- *"How many rows are in my_delta_table?"*
- *"List tables in the default schema"*
- *"What is the schema of my_delta_table?"*
- *"Run: SELECT * FROM delta_lake.default.my_table LIMIT 10"*

The MCP server translates these to Trino SQL and returns the results.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `mcp-trino` not found | Use full path in `command` and ensure the binary is executable |
| Connection refused | Check Trino is running and `TRINO_HOST`/`TRINO_PORT` are correct |
| S3 access denied | Verify IAM/credentials have `s3:GetObject`, `glue:Get*` |
| Delta table not found | Register with `register_table` or ensure it exists in Glue |
| Timeout | Increase `TRINO_QUERY_TIMEOUT` and `timeout` in mcp.json |

---

## References

- [mcp-trino GitHub](https://github.com/tuannvm/mcp-trino)
- [Trino Delta Lake Connector](https://trino.io/docs/current/connector/delta-lake.html)
- [Delta Lake + Presto/Trino](https://docs.delta.io/latest/delta-trino-integration.html)
- [Trino on EMR](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-trino.html)
