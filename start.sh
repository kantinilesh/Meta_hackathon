#!/bin/bash

# Terminate all processes if one fails
set -e

echo "Starting FastAPI Backend..."
# Run FastAPI on internal port 8000
python -m uvicorn environment.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "Starting Next.js Frontend..."
# Run Next.js on internal port 3000
cd /app/frontend
npm start &
FRONTEND_PID=$!
cd /app

echo "Starting Nginx (Reverse Proxy)..."
# Start Nginx in foreground to keep container running on 7860
nginx -c /etc/nginx/nginx.conf

# If Nginx crashes, kill the background processes
kill $BACKEND_PID
kill $FRONTEND_PID
