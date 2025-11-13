## Server Operator (provisioner)

A lightweight HTTP service that provisions a Pod + Service on your Kubernetes cluster from a client request. It:

- Creates/updates the `ssh-authorized-keys` secret with the provided public key
- Generates and applies a Pod manifest using the provided container image
- Exposes HTTP (8080) and SSH (default 22, configurable) via a NodePort Service
- Cleans up any existing Pod/Service with the same generated names

### Prerequisites
- Python 3.10+
- `kubectl` installed and configured to point to the target cluster/context

### Install

```bash
cd operator
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python server_operator.py
# listens on 0.0.0.0:8088 by default
```

Environment variables:
- `HOST` (default `0.0.0.0`) – bind address
- `PORT` (default `8088`) – listen port
- `NAMESPACE` (default `default`) – namespace to create resources in

### Provisioning API

`POST /provision`

Body:
```json
{
  "container_img_url": "docker.io/looogarithm/mock-inference:latest",
  "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI.... user@example",
  "port": 22
}
```

Notes:
- HTTP container port is always 8080.
- SSH container port defaults to 22 unless specified in `port`.
- The Service type is `NodePort`. NodePorts are assigned automatically by the cluster.

Example:
```bash
curl -sS -X POST http://127.0.0.1:8088/provision \
  -H 'Content-Type: application/json' \
  -d '{
    "container_img_url": "docker.io/looogarithm/mock-inference:latest",
    "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... user@example",
    "port": 22
  }' | jq .
```

Example response:
```json
{
  "pod_name": "client-mock-inference-67c5f2f8-pod",
  "service_name": "client-mock-inference-67c5f2f8-svc",
  "secret_name": "ssh-authorized-keys",
  "http_port": 8080,
  "ssh_port": 22,
  "external_ip": "10.0.0.123",
  "service_type": "LoadBalancer",
  "namespace": "default"
}
```

### Behavior
- Default Service type is `LoadBalancer` so the external ports are 8080 and 22/custom. Set `SERVICE_TYPE=NodePort` to use NodePort instead (then external access is via high nodePort range).
- Secret upsert uses `kubectl create secret ... --dry-run=client -o yaml | kubectl apply -f -`
- Pod mounts the secret at `/home/ubuntu/.ssh/authorized_keys` via `subPath`
- Pod sets env `MODEL_PORT=8080` and `SSH_PORT=<port>`
- Existing resources with the same generated names are deleted before applying


