# mprime (Prime95) wrapper image

This image wraps `nelsonjchen/mprime` to be compatible with the server operator:

- Starts an SSH server on `$SSH_PORT` (default: 2222) with key-only auth using `/home/ubuntu/.ssh/authorized_keys`.
- Exposes a simple HTTP health endpoint on `$MODEL_PORT` (default: 8080) that returns `200 OK`.
- Runs `mprime` in torture-test mode (`-t`) for continuous CPU load.

The operator will mount an `authorized_keys` file at `/home/ubuntu/.ssh/authorized_keys` via a K8s Secret.

## Build

```bash
cd /Users/Aleksandr1/code/k8s-playground/images/mprime
docker build -t your-registry/mprime-wrapper:latest .
```

## Push

```bash
docker push your-registry/mprime-wrapper:latest
```

## Use with server_operator

Send a provision request with the image you pushed:

```bash
curl -X POST http://localhost:8088/provision \
  -H 'content-type: application/json' \
  -d '{
    "container_img_url": "your-registry/mprime-wrapper:latest",
    "ssh_public_key": "ssh-ed25519 AAAA... user@host"
  }'
```

The operator will:
- Mount your SSH key into `/home/ubuntu/.ssh/authorized_keys`.
- Map NodePorts (HTTP: 30080, SSH: 30022) by default.

Then you can:

```bash
# HTTP health
curl http://<node-ip>:30080/

# SSH access
ssh -p 30022 ubuntu@<node-ip>
```

## Notes

- Container lifecycle is tied to `mprime` (if it exits, the container exits).
- SSH and HTTP servers are stopped when `mprime` ends or the pod receives SIGTERM.


