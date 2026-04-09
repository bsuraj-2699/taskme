#!/bin/sh
set -e

echo "Running migrations..."
alembic -c alembic.ini upgrade head

echo "Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000

