FROM mcr.microsoft.com/devcontainers/python:3.11-trixie

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Set default shell to zsh
SHELL ["/bin/zsh", "-c"]
