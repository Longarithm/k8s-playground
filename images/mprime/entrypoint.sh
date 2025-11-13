#!/usr/bin/env bash
set -euo pipefail

MODEL_PORT="${MODEL_PORT:-8080}"
SSH_PORT="${SSH_PORT:-2222}"

# Ensure SSH directory and permisssions for ubuntu user
mkdir -p /home/ubuntu/.ssh
touch /home/ubuntu/.ssh/authorized_keys || true
chown -R ubuntu:ubuntu /home/ubuntu/.ssh || true
chmod 700 /home/ubuntu/.ssh || true
chmod 600 /home/ubuntu/.ssh/authorized_keys || true

# Generate host keys if missing
ssh-keygen -A

# Start a minimal HTTP/status server
python3 /usr/local/bin/status_server.py &
p_http=$!

# Start SSHD on the requested port
/usr/sbin/sshd -D -p "${SSH_PORT}" &
p_sshd=$!

# Start mprime in torture test mode (continuous CPU load)
/opt/mprime/mprime -t &
p_mprime=$!

trap 'kill -TERM "$p_http" "$p_sshd" "$p_mprime" 2>/dev/null || true' TERM INT

# Prefer container lifecycle tied to mprime
set +e
wait "$p_mprime"
status=$?
set -e

kill -TERM "$p_http" "$p_sshd" 2>/dev/null || true
wait || true
exit "$status"


