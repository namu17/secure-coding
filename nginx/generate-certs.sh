#!/bin/sh
# Generates a local self-signed TLS certificate for the nginx reverse proxy.
# Not for production use with a real domain -- swap nginx/certs/*.pem for
# certs from a real CA (e.g. Let's Encrypt) when deploying publicly.
set -e

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

if [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    echo "Certificates already exist in $CERT_DIR, skipping."
    exit 0
fi

openssl req -x509 -nodes -newkey rsa:2048 \
    -days 825 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Generated self-signed certificate at $CERT_DIR"
