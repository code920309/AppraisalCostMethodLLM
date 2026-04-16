import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import appraisal, analysis, registry
from app.core.config import Config
from app.utils.logger import get_logger

# Windows에서 Playwright(서브프로세스) 사용을 위한 루프 정책 설정
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = get_logger(__name__)

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

@app.get("/")
async def root():
    return {"message": "AppraisalCost AI API is running", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
