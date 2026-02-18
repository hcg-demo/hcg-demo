# Install mcp-trino for Cursor on Windows
# Run: .\scripts\install_mcp_trino.ps1

$ErrorActionPreference = "Stop"
$version = "4.2.1"

# Target directory: try .cursor first, fallback to project .mcp-tools
$mcpDir = "$env:USERPROFILE\.cursor\mcp-tools"
try {
    New-Item -ItemType Directory -Force -Path $mcpDir -ErrorAction Stop | Out-Null
} catch {
    $projectDir = Split-Path -Parent $PSScriptRoot
    $mcpDir = "$projectDir\.mcp-tools"
    New-Item -ItemType Directory -Force -Path $mcpDir | Out-Null
    Write-Host "Using project path: $mcpDir" -ForegroundColor Yellow
}
$binPath = "$mcpDir\mcp-trino.exe"

Write-Host "Installing mcp-trino v$version to $mcpDir" -ForegroundColor Cyan

$url = "https://github.com/tuannvm/mcp-trino/releases/download/v$version/mcp-trino_${version}_windows_amd64.zip"
$zipPath = "$mcpDir\mcp-trino.zip"

try {
    Write-Host "Downloading from $url ..."
    Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $mcpDir -Force
    Remove-Item $zipPath -Force
} catch {
    Write-Host "Download failed. Check your network or try manual download." -ForegroundColor Red
    exit 1
}

# Find extracted exe (may be in subdir or root)
$exe = Get-ChildItem -Path $mcpDir -Filter "mcp-trino*.exe" -Recurse | Select-Object -First 1
if ($exe) {
    if ($exe.DirectoryName -ne $mcpDir) {
        Move-Item $exe.FullName $binPath -Force
    }
}

Write-Host ""
Write-Host "Installation complete. Binary: $binPath" -ForegroundColor Green
Write-Host ""
Write-Host "Add to your Cursor MCP config (%USERPROFILE%\.cursor\mcp.json):" -ForegroundColor Yellow
Write-Host @"

    "trino": {
      "command": "$($binPath.Replace('\','\\'))",
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
"@
Write-Host ""
Write-Host "See docs\PRESTO_TRINO_MCP_SETUP.md for full setup (Trino + S3 + Delta Lake)." -ForegroundColor Cyan
