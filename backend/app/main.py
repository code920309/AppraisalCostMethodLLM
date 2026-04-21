import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import appraisal, analysis, registry
from app.core.config import Config
from app.utils.logger import get_logger
import os

# Windows에서 Playwright(서브프로세스) 사용을 위한 루프 정책 설정
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = get_logger(__name__)

# 서버 시작 시 필요한 파일 자동 다운로드 (모델, 폰트)
Config.ensure_model_exists()
Config.ensure_fonts_exist()
# 필수 환경변수 누락 여부 경고 출력
Config.validate_env()

app = FastAPI(
    title="AppraisalCost AI API",
    description="建物(건물) 가치 산정 및 외벽 결함 분석 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production 환경에서는 화이트리스트 관리 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(registry.router, prefix="/api/v1/registry", tags=["Building Registry"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Vision Analysis"])
app.include_router(appraisal.router, prefix="/api/v1/appraisal", tags=["Appraisal Report"])

@app.get("/health")
async def health():
    return {"message": "AppraisalCost AI API is running", "status": "healthy"}

# 정적 파일 서버 (React 빌드 결과물) - 반드시 가장 마지막에 배치
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import os
    # 로컬 개발 환경(8000)과 클라우드 배포 환경(PORT 환경변수) 모두 대응
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
