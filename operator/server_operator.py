#!/usr/bin/env python3
import base64
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import yaml


class ProvisionRequest(BaseModel):
    container_img_url: str = Field(..., description="Container image URL, e.g. docker.io/user/image:tag")
    ssh_public_key: str = Field(..., description="SSH public key (single line)")


class ProvisionResponse(BaseModel):
    pod_name: str
    service_name: str
    secret_name: str
    # Ports that clients should actually use when connecting from outside the cluster
    connect_http_port: int
    connect_ssh_port: int
    namespace: str


app = FastAPI(title="K8s Server Operator")


def run(cmd: list[str], *, input_str: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_str.encode("utf-8") if input_str is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sanitize_name(value: str, prefix: str) -> str:
    # K8s name: lowercase alphanumerics and '-', must start/end alphanumeric, <=63 chars
    base = re.sub(r"[^a-z0-9-]+", "-", value.lower())
    base = re.sub(r"^-+|-+$", "", base)
    if not base:
        base = "app"
    suffix = hex(int(time.time()))[2:]
    name = f"{prefix}-{base}-{suffix}"
    name = name[:63].rstrip("-")
    return name


def make_manifest_yaml(
    *,
    pod_name: str,
    app_label: str,
    svc_name: str,
    image: str,
    ssh_port: int,
    secret_name: str,
    http_node_port: Optional[int],
    ssh_node_port: Optional[int],
) -> str:
    pod_obj = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "labels": {"app": app_label},
        },
        "spec": {
            "containers": [
                {
                    "name": "app",
                    "image": image,
                    "imagePullPolicy": "IfNotPresent",
                    "env": [
                        {"name": "MODEL_PORT", "value": "8080"},
                        {"name": "SSH_PORT", "value": str(ssh_port)},
                    ],
                    "ports": [
                        {"containerPort": 8080},
                        {"containerPort": ssh_port},
                    ],
                    "volumeMounts": [
                        {
                            "name": "ssh-keys",
                            "mountPath": "/home/ubuntu/.ssh/authorized_keys",
                            "subPath": "authorized_keys",
                        }
                    ],
                }
            ],
            "volumes": [
                {
                    "name": "ssh-keys",
                    "secret": {
                        "secretName": secret_name,
                        "defaultMode": int("0644", 8),
                    },
                }
            ],
        },
    }
    svc_obj = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": svc_name},
        "spec": {
            "selector": {"app": app_label},
            "type": "NodePort",
            "ports": [
                {
                    "name": "http",
                    "protocol": "TCP",
                    "port": 8080,
                    "targetPort": 8080,
                },
                {
                    "name": "ssh",
                    "protocol": "TCP",
                    "port": ssh_port,
                    "targetPort": ssh_port,
                },
            ],
        },
    }
    # Pin nodePorts (required, we default them upstream)
    if http_node_port is not None:
        svc_obj["spec"]["ports"][0]["nodePort"] = http_node_port
    if ssh_node_port is not None:
        svc_obj["spec"]["ports"][1]["nodePort"] = ssh_node_port
    pieces = [
        yaml.safe_dump(pod_obj, sort_keys=False).rstrip(),
        yaml.safe_dump(svc_obj, sort_keys=False).rstrip(),
    ]
    return "\n---\n".join(pieces) + "\n"


def ensure_secret(secret_name: str, ssh_public_key: str, namespace: str) -> None:
    # Use kubectl to upsert secret with authorized_keys literal
    create_cmd = [
        "kubectl",
        "create",
        "secret",
        "generic",
        secret_name,
        f"--from-literal=authorized_keys={ssh_public_key}",
        "--dry-run=client",
        "-o",
        "yaml",
    ]
    created = run(create_cmd)
    if created.returncode != 0:
        raise RuntimeError(f"failed to render secret yaml: {created.stderr.decode()}")
    apply_cmd = ["kubectl", "apply", "-n", namespace, "-f", "-"]
    applied = run(apply_cmd, input_str=created.stdout.decode())
    if applied.returncode != 0:
        raise RuntimeError(f"failed to apply secret: {applied.stderr.decode()}")


def delete_if_exists(kind: str, name: str, namespace: str) -> None:
    cmd = ["kubectl", "delete", kind, name, "-n", namespace, "--ignore-not-found=true"]
    run(cmd)


def apply_manifest(manifest: str, namespace: str) -> None:
    cmd = ["kubectl", "apply", "-n", namespace, "-f", "-"]
    res = run(cmd, input_str=manifest)
    if res.returncode != 0:
        raise RuntimeError(f"failed to apply manifest: {res.stderr.decode()}")


def get_service_node_ports(name: str, namespace: str) -> Dict[str, Optional[int]]:
    cmd = ["kubectl", "get", "svc", name, "-n", namespace, "-o", "json"]
    res = run(cmd)
    if res.returncode != 0:
        return {"http": None, "ssh": None}
    try:
        data = json.loads(res.stdout.decode() or "{}")
        ports = data.get("spec", {}).get("ports", [])
        http_np = None
        ssh_np = None
        for p in ports:
            if p.get("name") == "http":
                http_np = p.get("nodePort")
            if p.get("name") == "ssh":
                ssh_np = p.get("nodePort")
        return {"http": http_np, "ssh": ssh_np}
    except Exception:
        return {"http": None, "ssh": None}


@app.post("/provision", response_model=ProvisionResponse)
def provision(req: ProvisionRequest) -> ProvisionResponse:
    namespace = os.getenv("NAMESPACE", "default")
    image = req.container_img_url.strip()
    if not image:
        raise HTTPException(status_code=400, detail="container_img_url is required")
    ssh_key = req.ssh_public_key.strip()
    if not ssh_key:
        raise HTTPException(status_code=400, detail="ssh_public_key is required")
    # Container SSH port is fixed to 22
    ssh_port = 22

    # Determine nodePorts from request or defaults when NodePort
    http_node_port = None
    ssh_node_port = None
    http_node_port = 30080
    ssh_node_port = 30022
    # Basic sanity range (typical default); cluster may differ
    for name, n in (("http_node_port", http_node_port), ("ssh_node_port", ssh_node_port)):
        if n is not None and not (30000 <= n <= 32767):
            raise HTTPException(status_code=400, detail=f"{name} must be within 30000..32767")

    base = sanitize_name(image.split("/")[-1], prefix="client")
    app_label = base
    pod_name = f"{base}-pod"
    svc_name = f"{base}-svc"
    secret_name = "ssh-authorized-keys"

    # Cleanup old resources with same names
    delete_if_exists("service", svc_name, namespace)
    delete_if_exists("pod", pod_name, namespace)

    # Secret upsert
    ensure_secret(secret_name, ssh_key, namespace)

    manifest = make_manifest_yaml(
        pod_name=pod_name,
        app_label=app_label,
        svc_name=svc_name,
        image=image,
        ssh_port=ssh_port,
        secret_name=secret_name,
        http_node_port=http_node_port,
        ssh_node_port=ssh_node_port,
    )
    apply_manifest(manifest, namespace)

    # Fetch assigned NodePorts
    ports = get_service_node_ports(svc_name, namespace)
    http_np = ports.get("http") or http_node_port
    ssh_np = ports.get("ssh") or ssh_node_port

    # Users connect via node IP and nodePorts
    connect_http_port = int(http_np)
    connect_ssh_port = int(ssh_np)

    return ProvisionResponse(
        pod_name=pod_name,
        service_name=svc_name,
        secret_name=secret_name,
        connect_http_port=connect_http_port,
        connect_ssh_port=connect_ssh_port,
        namespace=namespace,
    )


def main() -> None:
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port_str = os.getenv("PORT", "8088")
    try:
        port = int(port_str, 10)
    except Exception:
        port = 8088
    uvicorn.run("server_operator:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()


