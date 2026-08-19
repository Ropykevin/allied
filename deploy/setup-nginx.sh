#!/usr/bin/env bash
# Install / enable Nginx site for Allied (run on the VPS as a user with sudo).
# Usage:
#   ./deploy/setup-nginx.sh alliedtravelke.com
#   ./deploy/setup-nginx.sh alliedtravelke.com --ssl

set -euo pipefail

DOMAIN="${1:-}"
DO_SSL="${2:-}"

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: $0 yourdomain.com [--ssl]"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT_DIR/deploy/nginx-allied.conf"
DEST="/etc/nginx/sites-available/allied"

if [[ ! -f "$SRC" ]]; then
  echo "Missing $SRC"
  exit 1
fi

sudo apt-get update
sudo apt-get install -y nginx

TMP="$(mktemp)"
sed "s/YOUR_DOMAIN/${DOMAIN}/g" "$SRC" > "$TMP"
sudo cp "$TMP" "$DEST"
rm -f "$TMP"

sudo ln -sfn "$DEST" /etc/nginx/sites-enabled/allied
# Remove default site if present (optional)
if [[ -L /etc/nginx/sites-enabled/default ]]; then
  sudo rm -f /etc/nginx/sites-enabled/default
fi

# Global upload limit (covers Certbot HTTPS server blocks too)
UPLOAD_LIMIT_SRC="$ROOT_DIR/deploy/nginx-upload-limit.conf"
if [[ -f "$UPLOAD_LIMIT_SRC" ]]; then
  sudo cp "$UPLOAD_LIMIT_SRC" /etc/nginx/conf.d/allied-upload-limit.conf
fi

# Ensure every server block for this site has client_max_body_size (incl. SSL)
if sudo test -f "$DEST"; then
  if ! sudo grep -q "client_max_body_size" "$DEST"; then
    sudo sed -i '/server_name /a\    client_max_body_size 100m;' "$DEST"
  else
    sudo sed -i 's/client_max_body_size[[:space:]]*[0-9]\+[kKmMgG]\?;/client_max_body_size 100m;/g' "$DEST"
  fi
fi

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx

# Open HTTP/HTTPS if ufw is active
if command -v ufw >/dev/null 2>&1 && sudo ufw status | grep -q "Status: active"; then
  sudo ufw allow 'Nginx Full' || true
  sudo ufw allow 80/tcp || true
  sudo ufw allow 443/tcp || true
fi

echo "Nginx configured for http://${DOMAIN}"
echo "Test: curl -I http://${DOMAIN}"

if [[ "$DO_SSL" == "--ssl" ]]; then
  sudo apt-get install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email || \
    sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN"
  echo "HTTPS enabled for https://${DOMAIN}"
fi

echo "Done. Ensure app .env has TRUST_PROXY_HOPS=1 then: docker compose up -d web"
