#!/usr/bin/env bash
# JobMatch backend — one-shot setup on Oracle Cloud Always Free (Ubuntu).
# Jalankan SETELAH SSH masuk ke VM:   bash deploy_oracle.sh
set -euo pipefail

echo "==> [1/6] Install base packages"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git curl

echo "==> [2/6] Clone repo"
cd "$HOME"
if [ ! -d jobmatch ]; then
  git clone https://github.com/Anggito007/jobmatch.git
fi

echo "==> [3/6] Python venv + deps"
cd "$HOME/jobmatch/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> [4/6] Pre-download embedding model (~470MB)"
python -m scripts.warmup_model

echo "==> [5/6] Install systemd service (always-on)"
sudo tee /etc/systemd/system/jobmatch.service > /dev/null <<EOF
[Unit]
Description=JobMatch backend API
After=network.target

[Service]
User=$USER
WorkingDirectory=$HOME/jobmatch/backend
Environment=CORS_ORIGINS=*
Environment=DATABASE_URL=sqlite:///$HOME/jobmatch/backend/jobmatch.db
Environment=FETCH_INTERVAL_HOURS=6
ExecStart=$HOME/jobmatch/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jobmatch
sudo systemctl start jobmatch

echo "==> [6/6] Done"
echo "Cek status:  sudo systemctl status jobmatch"
echo "Test lokal:  curl http://localhost:8000/health"
echo "Selanjutnya: pasang HTTPS (deploy_https.sh) lalu buka port di VCN security list."
