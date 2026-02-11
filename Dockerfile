FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

RUN useradd -m -u 1000 appuser

RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser --chmod=755 scripts/entrypoint.sh /entrypoint.sh

RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O- http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
