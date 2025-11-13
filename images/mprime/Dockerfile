FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends openssh-server python3 ca-certificates curl tar && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user expected by operator and prepare SSH
RUN useradd -ms /bin/bash ubuntu && \
    mkdir -p /home/ubuntu/.ssh /var/run/sshd && \
    chown -R ubuntu:ubuntu /home/ubuntu && \
    chmod 700 /home/ubuntu/.ssh

# Minimal SSHD configuration snippet suitable for key-only auth
RUN mkdir -p /etc/ssh/sshd_config.d && \
    printf "Port 2222\nPasswordAuthentication no\nPermitRootLogin no\nPubkeyAuthentication yes\nAuthorizedKeysFile /home/ubuntu/.ssh/authorized_keys\nSubsystem sftp /usr/lib/openssh/sftp-server\n" > /etc/ssh/sshd_config.d/99-operator.conf

COPY status_server.py /usr/local/bin/status_server.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV MODEL_PORT=8080 \
    SSH_PORT=2222

# Install mprime (Prime95) from upstream tarball
# Provide the URL at build time:
#   docker build --build-arg MPRIME_URL="https://www.mersenne.org/ftp_root/gimps/p95v308b17.linux64.tar.gz" ...
ARG MPRIME_URL
RUN test -n "$MPRIME_URL" || (echo "ERROR: Provide --build-arg MPRIME_URL=<url to mprime linux64 tar.gz>" && exit 1)
RUN mkdir -p /opt/mprime && \
    curl -fsSL "$MPRIME_URL" -o /tmp/mprime.tar.gz && \
    tar -xzf /tmp/mprime.tar.gz -C /opt/mprime && \
    rm -f /tmp/mprime.tar.gz && \
    chmod +x /opt/mprime/mprime || true

WORKDIR /opt/mprime

EXPOSE 8080 2222

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]


