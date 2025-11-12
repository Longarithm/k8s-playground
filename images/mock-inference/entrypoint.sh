#!/usr/bin/env bash
set -euo pipefail

SSH_PORT="${SSH_PORT:-2222}"
MODEL_PORT="${MODEL_PORT:-8080}"

# Generate host keys if missing
/usr/bin/ssh-keygen -A

echo "Starting mock inference server on port ${MODEL_PORT}..."
python -u /opt/app/app.py &

echo "Starting sshd on port ${SSH_PORT}..."
exec /usr/sbin/sshd -D -e \
  -o ListenAddress=0.0.0.0 \
  -o Port="${SSH_PORT}" \
  -o PermitRootLogin=no \
  -o PasswordAuthentication=no \
  -o PubkeyAuthentication=yes \
  -o AuthorizedKeysFile=".ssh/authorized_keys"


