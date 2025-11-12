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

WORKDIR /opt/app
COPY app.py /opt/app/app.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8080 2222
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]

