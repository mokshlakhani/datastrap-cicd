# Jenkins with everything our pipeline needs already installed:
# Docker CLI, Python 3 (+venv), Node.js, make, curl and the SonarQube scanner.
FROM jenkins/jenkins:2.580.2-lts-jdk21

USER root

# Python (for tests/lint), curl (for smoke tests), unzip/xz (to unpack the downloads below), make.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip curl unzip xz-utils make \
 && rm -rf /var/lib/apt/lists/*

# Docker CLI only (the Docker engine itself is the one on your computer, reached through a socket).
COPY --from=docker:27.5.1-cli /usr/local/bin/docker /usr/local/bin/docker

# Node.js and the SonarQube scanner: pick the download that matches this CPU (Intel/AMD or Apple Silicon).
ARG NODE_VERSION=22.20.0
ARG SCANNER_VERSION=7.1.0.4889
RUN arch="$(dpkg --print-architecture)" \
 && if [ "$arch" = "arm64" ]; then node_arch=arm64; scan_arch=aarch64; else node_arch=x64; scan_arch=x64; fi \
 && curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" | tar -xJ -C /usr/local --strip-components=1 \
 && curl -fsSL -o /tmp/scanner.zip "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SCANNER_VERSION}-linux-${scan_arch}.zip" \
 && unzip -q /tmp/scanner.zip -d /opt \
 && ln -s "/opt/sonar-scanner-${SCANNER_VERSION}-linux-${scan_arch}/bin/sonar-scanner" /usr/local/bin/sonar-scanner \
 && rm /tmp/scanner.zip

# Install the Jenkins plugins up front so you do not have to click through the plugin manager.
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Compose runs this container as root so it may use the Docker socket (see docker-compose.yml).
