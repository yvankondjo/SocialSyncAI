FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Outils de base + clients utiles
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git jq tree wget sudo locales ca-certificates gnupg lsb-release \
    libpq-dev postgresql-client socat iproute2 netcat-openbsd unzip xz-utils \
 && rm -rf /var/lib/apt/lists/*

# Node 20 + Corepack
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g npm@latest && corepack enable

# Docker CLI + Compose v2 (plugin officiel)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg \
      | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable" \
      > /etc/apt/sources.list.d/docker.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
 && docker --version && docker compose version

# Locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# Dépendances Python (en root, avant de switch user)
WORKDIR /workspace
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Utilisateur non-root
ARG USERNAME=dev
ARG USER_UID=1000
RUN useradd -ms /bin/bash -u ${USER_UID} ${USERNAME} \
 && mkdir -p /etc/sudoers.d \
 && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
 && chmod 0440 /etc/sudoers.d/${USERNAME} \
 && groupadd -f docker || true \
 && usermod -aG docker ${USERNAME}

# Configure npm global directory for non-root user
RUN mkdir -p /home/${USERNAME}/.npm-global \
 && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.npm-global

USER ${USERNAME}

# Set npm prefix to user's home directory
RUN npm config set prefix "/home/${USERNAME}/.npm-global"

# Update PATH for npm global binaries
ENV PATH="/home/${USERNAME}/.npm-global/bin:${PATH}"

# Install Claude Code via npm
RUN npm install -g @anthropic-ai/claude-code \
 && claude --version

WORKDIR /workspace

CMD ["bash"]