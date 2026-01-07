FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md /app/
COPY src /app/src
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/

RUN uv pip install --system -e .

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /app/storage \
    && chown -R app:app /app

USER app

CMD ["uvicorn", "opus_blocks.app:app", "--host", "0.0.0.0", "--port", "8000"]
