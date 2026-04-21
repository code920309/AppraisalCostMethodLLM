# Stage 1: Build React frontend
FROM node:22-slim AS build-stage
WORKDIR /app/frontend
# package.json + package-lock.json 함께 복사 → npm ci 사용
COPY frontend/package*.json ./
RUN npm ci --include=optional
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with FastAPI
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for YOLO/AI (OpenCV, etc.)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# 빈 디렉터리 사전 생성 (모델/폰트는 런타임에 자동 다운로드)
RUN mkdir -p /app/models /app/assets/fonts

# backend/assets 복사 (.gitkeep 포함, 실제 폰트는 런타임 다운로드)
COPY backend/assets ./assets

# Copy static files (React build artifacts)
COPY --from=build-stage /app/frontend/dist ./static

# Environment variables
ENV ENV_TYPE=production
ENV PYTHONPATH=/app
ENV PORT=7860

# Expose port (Hugging Face Spaces default)
EXPOSE 7860

# Playwright에 필요한 라이브러리 및 브라우저 설치 (CMD 이전에 배치)
RUN pip install playwright
RUN playwright install chromium --with-deps

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]