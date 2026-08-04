#!/usr/bin/env bash
# generate a self-signed cert and run uvicorn with HTTPS on localhost:8000
# Requirements: openssl, python env with dependencies installed

set -e
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
SSL_DIR="$ROOT_DIR/ssl"
mkdir -p "$SSL_DIR"

CERT="$SSL_DIR/cert.pem"
KEY="$SSL_DIR/key.pem"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
  echo "Generating self-signed certificate (CN=localhost) ..."
  openssl req -x509 -newkey rsa:4096 -sha256 -nodes \
    -keyout "$KEY" -out "$CERT" -days 365 \
    -subj "/CN=localhost"
  echo "Certificate generated at $CERT and key at $KEY"
else
  echo "Using existing cert and key in $SSL_DIR"
fi

echo "Starting uvicorn with HTTPS on https://localhost:8000"
# Run uvicorn pointing to the generated cert/key
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile "$KEY" --ssl-certfile "$CERT"
