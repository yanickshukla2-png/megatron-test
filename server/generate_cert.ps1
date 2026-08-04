# PowerShell script to generate a self-signed certificate (using OpenSSL) and run uvicorn with HTTPS
# Requirements: OpenSSL in PATH, Python env with dependencies installed
param()
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sslDir = Join-Path $scriptDir 'ssl'
if (-not (Test-Path $sslDir)) { New-Item -ItemType Directory -Path $sslDir | Out-Null }

$cert = Join-Path $sslDir 'cert.pem'
$key = Join-Path $sslDir 'key.pem'

if (-not (Test-Path $cert) -or -not (Test-Path $key)) {
    Write-Host "Generating self-signed certificate (CN=localhost) ..."
    $args = "req -x509 -newkey rsa:4096 -sha256 -nodes -keyout `"$key`" -out `"$cert`" -days 365 -subj `/CN=localhost`"
    & openssl $args
    Write-Host "Certificate generated at $cert and key at $key"
} else {
    Write-Host "Using existing cert and key in $sslDir"
}

Write-Host "Starting uvicorn with HTTPS on https://localhost:8000"
# Start uvicorn
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile "$key" --ssl-certfile "$cert"
