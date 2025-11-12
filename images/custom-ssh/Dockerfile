FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-server \
        ca-certificates \
        tini \
        bash \
        coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd /etc/ssh/sshd_config.d /data

# Create a fixed user at build-time
RUN groupadd -g 1000 ubuntu \
    && useradd -m -u 1000 -g 1000 -s /bin/bash ubuntu \
    && mkdir -p /home/ubuntu/.ssh /data \
    && chmod 700 /home/ubuntu/.ssh \
    && chown -R ubuntu:ubuntu /home/ubuntu /data

# Runtime-configurable port (optional)
ENV SSH_PORT=2222

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Provide a suggested mount point
VOLUME ["/data"]

EXPOSE 2222

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]


