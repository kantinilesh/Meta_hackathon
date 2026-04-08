#!/bin/bash

echo "Starting FastAPI Backend..."
python -m uvicorn environment.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "Starting Next.js Frontend..."
cd /app/frontend
PORT=3000 npm start &
FRONTEND_PID=$!
cd /app

echo "Waiting for FastAPI..."
until curl -s http://127.0.0.1:8000 > /dev/null 2>&1; do
    sleep 1
done

echo "Waiting for Next.js..."
until curl -s http://127.0.0.1:3000 > /dev/null 2>&1; do
    sleep 1
done

echo "Starting Nginx..."
nginx -c /etc/nginx/nginx.conf
