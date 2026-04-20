---
title: AppraisalAI-Suite
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# AppraisalCost AI Suite

AI 기반 건물 가치 산정 및 외벽 결함 분석 솔루션입니다.

## 주요 기능
- **외벽 결함 분석**: YOLOv8m-seg를 활용한 균열 및 결함 탐지.
- **가치 산정**: 원가법 기반의 감정평가 로직 적용.
- **리포트 생성**: Llama 3.3을 활용한 전문 감정평가 의견서 자동 생성.

## 기술 스택
- **Frontend**: React (Vite)
- **Backend**: FastAPI
- **AI Models**: YOLOv8, EfficientNet
- **Deployment**: Docker on Hugging Face Spaces
