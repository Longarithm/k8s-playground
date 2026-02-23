# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MODEL_PORT=8080
ENV DEBIAN_FRONTEND=noninteractive
ENV SSH_PORT=2222

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-server \
        ca-certificates \
        tini \
        bash \
        coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd /etc/ssh/sshd_config.d

RUN groupadd -g 1000 ubuntu \
    && useradd -m -u 1000 -g 1000 -s /bin/bash ubuntu \
    && mkdir -p /home/ubuntu/.ssh \
    && chmod 700 /home/ubuntu/.ssh \
    && chown -R ubuntu:ubuntu /home/ubuntu

# Optionally inject a public SSH key into ubuntu's authorized_keys using BuildKit secret.
# Build example:
#   docker buildx build --secret id=authorized_key,src=$HOME/.ssh/id_ed25519_2.pub ...
RUN --mount=type=secret,id=authorized_key,target=/run/secrets/authorized_key \
    if [ -s /run/secrets/authorized_key ]; then \
        cat /run/secrets/authorized_key > /home/ubuntu/.ssh/authorized_keys && \
        chown ubuntu:ubuntu /home/ubuntu/.ssh/authorized_keys && \
        chmod 600 /home/ubuntu/.ssh/authorized_keys ; \
    fi

WORKDIR /opt/app
COPY app.py /opt/app/app.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8080 2222
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]

