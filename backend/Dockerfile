FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

# Use sh explicitly to avoid CRLF shebang issues on Windows checkouts.
CMD ["sh", "-c", "alembic -c alembic.ini upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
