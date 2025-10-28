ARG BASE_IMAGE=nvidia/cuda:12.4.1-cudnn-runtime-ubuntu24.04
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/Daniel-OS01/speaches"
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies as root (keep this single apt-get block)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    python3-pip \
    python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user 'ubuntu' and switch to them for app-level operations
RUN useradd --create-home --shell /bin/bash --uid 1000 ubuntu || true
USER ubuntu
WORKDIR /home/ubuntu/app

# Set up a virtual environment as the ubuntu user
ENV VIRTUAL_ENV=/home/ubuntu/app/.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install 'uv' for Python package management (install script requires curl, which is already installed)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/ubuntu/.cargo/bin:${PATH}"

# Copy dependency definition files
COPY --chown=ubuntu:ubuntu pyproject.toml uv.lock ./
COPY --chown=ubuntu:ubuntu runpod_requirements.txt ./

# Install uv into the venv and sync Python dependencies (run as ubuntu so venv is owned by the user)
RUN pip install --upgrade pip
RUN pip install uv
RUN uv sync --frozen --compile-bytecode --extra ui

# Then, install Runpod-specific dependencies into the venv
RUN pip install -r runpod_requirements.txt

# Copy the application source code and necessary files
COPY --chown=ubuntu:ubuntu src/ ./src
COPY --chown=ubuntu:ubuntu realtime-console/ ./realtime-console
COPY --chown=ubuntu:ubuntu handler.py ./
COPY --chown=ubuntu:ubuntu model_aliases.json ./

ENV UVICORN_HOST=127.0.0.1
ENV UVICORN_PORT=8000
ENV HF_HUB_ENABLE_HF_TRANSFER=0

CMD ["python", "-u", "handler.py"]
