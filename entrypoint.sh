#!/bin/bash
echo "Starting SelinaAI..."
exec python -m uvicorn bot_constructor.app:app --host 0.0.0.0 --port ${PORT:-8080}
