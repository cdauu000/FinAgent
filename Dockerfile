# Tag checked in Docker Official Images on 2026-11-02; build not yet run locally.
FROM python:3.12.16-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements-lock.txt ./
COPY finagent ./finagent
RUN python -m pip install --no-cache-dir -c requirements-lock.txt .
RUN useradd --create-home --uid 10001 finagent
USER finagent
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "finagent.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

