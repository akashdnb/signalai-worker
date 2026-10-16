FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY signalai_worker ./signalai_worker

RUN pip install --upgrade pip && pip install .

RUN useradd --create-home --uid 10001 signalai
USER signalai

CMD ["python", "-m", "signalai_worker.worker"]
