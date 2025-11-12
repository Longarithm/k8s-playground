#!/usr/bin/env bash
set -euo pipefail

SSH_PORT="${SSH_PORT:-2222}"

# Generate host keys if missing
/usr/bin/ssh-keygen -A

echo "Starting sshd on port ${SSH_PORT}..."
exec /usr/sbin/sshd -D -e \
  -o ListenAddress=0.0.0.0 \
  -o Port="${SSH_PORT}" \
  -o PermitRootLogin=no \
  -o PasswordAuthentication=no \
  -o PubkeyAuthentication=yes \
  -o AuthorizedKeysFile=".ssh/authorized_keys"


