# Stage 1: Build React frontend
FROM node:18 AS build-stage
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with FastAPI
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for YOLO/AI (OpenCV, etc.)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and required directories
# backend/app -> /app/app
COPY backend/app ./app
# backend/models -> /app/models (for AI inference)
COPY backend/models ./models
# backend/assets -> /app/assets (if needed)
COPY backend/assets ./assets

# Copy static files (React build artifacts)
COPY --from=build-stage /app/frontend/dist ./static

# Environment variables
ENV ENV_TYPE=production
ENV PYTHONPATH=/app
ENV PORT=7860

# Expose port (Hugging Face Spaces default)
EXPOSE 7860

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
