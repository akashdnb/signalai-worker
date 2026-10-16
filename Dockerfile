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

EXPOSE 8000

CMD ["uvicorn", "signalai_worker.app:app", "--host", "0.0.0.0", "--port", "8000"]
