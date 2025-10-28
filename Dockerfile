ARG BASE_IMAGE=nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/Daniel-OS01/speaches"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash --uid 1000 ubuntu || true
USER ubuntu
WORKDIR /home/ubuntu/app

ENV VIRTUAL_ENV=/home/ubuntu/app/.venv
RUN python3.12 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/ubuntu/.local/bin:${PATH}"

COPY --chown=ubuntu:ubuntu pyproject.toml uv.lock ./
COPY --chown=ubuntu:ubuntu runpod_requirements.txt ./

RUN /home/ubuntu/.local/bin/uv sync --frozen --compile-bytecode --extra ui
RUN pip install -r runpod_requirements.txt

COPY --chown=ubuntu:ubuntu src/ ./src
COPY --chown=ubuntu:ubuntu realtime-console/ ./realtime-console
COPY --chown=ubuntu:ubuntu handler.py ./
COPY --chown=ubuntu:ubuntu model_aliases.json ./

ENV UVICORN_HOST=127.0.0.1
ENV UVICORN_PORT=8000
ENV HF_HUB_ENABLE_HF_TRANSFER=0

CMD ["python", "-u", "handler.py"]
