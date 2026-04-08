FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Bake in the /api dynamic base URL so the frontend knows to call our Nginx endpoints
ENV NEXT_PUBLIC_API_URL=/api
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Install Node.js, Nginx, and process dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Setup backend Python environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend /app/frontend

# Setup Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Add start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Environment config
ENV PORT=7860
ENV NODE_ENV=production
EXPOSE 7860

# Start supervisor / bash script mapping
CMD ["/start.sh"]
