#!/usr/bin/env bash
# Pasang HTTPS untuk backend JobMatch via DuckDNS (subdomain gratis) + Caddy.
# Vercel (HTTPS) tidak bisa memanggil http://IP:8000 — browser blokir mixed
# content. Jadi backend WAJIB HTTPS. Script ini memakainya.
#
# Jalankan:   DOMAIN=xxx.duckdns.org DUCKDNS_TOKEN=token bash deploy_https.sh
set -euo pipefail

DOMAIN="${DOMAIN:-}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"

if [ -z "$DOMAIN" ]; then
  echo "Set DOMAIN dulu:  DOMAIN=xxx.duckdns.org DUCKDNS_TOKEN=token bash deploy_https.sh"
  exit 1
fi

echo "==> [1/3] Install Caddy"
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update -y
sudo apt-get install -y caddy

echo "==> [2/3] Konfigurasi reverse proxy + HTTPS otomatis (Let's Encrypt)"
sudo tee /etc/caddy/Caddyfile > /dev/null <<EOF
$DOMAIN {
    reverse_proxy 127.0.0.1:8000
}
EOF

echo "==> [3/3] DuckDNS auto-update (IP dinamis)"
if [ -n "$DUCKDNS_TOKEN" ]; then
  SUB="${DOMAIN%%.*}"
  sudo tee /usr/local/bin/duckdns-update > /dev/null <<EOF2
#!/usr/bin/env bash
curl -s "https://www.duckdns.org/update?domains=$SUB&token=$DUCKDNS_TOKEN&ip="
EOF2
  sudo chmod +x /usr/local/bin/duckdns-update
  (sudo crontab -l 2>/dev/null | grep -v duckdns; echo "*/5 * * * * /usr/local/bin/duckdns-update >/dev/null 2>&1") | sudo crontab -
  sudo /usr/local/bin/duckdns-update
  echo "DuckDNS domain $DOMAIN diarahkan ke IP VM ini."
else
  echo "DUCKDNS_TOKEN kosong — pastikan DNS $DOMAIN sudah menunjuk ke IP VM ini (A record)."
fi

sudo systemctl restart caddy
echo ""
echo "Selesai. Backend live di https://$DOMAIN"
echo "Tes:  curl https://$DOMAIN/health"
