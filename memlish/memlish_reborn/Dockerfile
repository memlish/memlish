FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/data/hf-cache

RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY src ./src
COPY scripts ./scripts

# Index + templates are mounted at runtime under /data
ENV MEMLISH_DATA_DIR=/data
VOLUME ["/data"]

CMD ["python", "-m", "memlish_reborn.bot"]
