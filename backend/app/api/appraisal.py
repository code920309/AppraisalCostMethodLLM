from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.appraisal_service import calculate_appraisal
from app.services.llm_service import generate_appraisal_report
from app.services.pdf_service import export_to_pdf
from app.utils.logger import get_logger
from fastapi.responses import FileResponse

router = APIRouter()
logger = get_logger(__name__)

class AppraisalRequest(BaseModel):
    # 계산을 위한 물리 데이터
    address: str
    total_area: float
    usage_name: str
    elapsed_years: int
    
    # AI 분석 데이터
    defect_ratio: float
    severity: str
    confidence: float
    is_official_data: bool = False
    llm_content: str = "" # PDF 전용
    
    # 이미지 및 결과 데이터 (추가)
    main_image: str = ""   # 오리지널 전경 사진
    defect_image: str = "" # 결함 탐지된 사진
    total_value: float = 0 # 최종 산정된 금액
    replacement_cost: float = 0
    physical_depreciation: float = 0
    observation_depreciation: float = 0

@router.post("/export/pdf")
async def export_report_pdf(req: AppraisalRequest):
    """결과 데이터를 PDF 파일로 내보내기"""
    try:
        building_info = {
            "address": req.address,
            "structure": req.usage_name,
            "age": req.elapsed_years,
            "total_value": req.total_value,
            "replacement_cost": req.replacement_cost,
            "physical_depreciation": req.physical_depreciation,
            "observation_depreciation": req.observation_depreciation
        }
        analysis_result = {
            "defect_ratio": req.defect_ratio,
            "severity": req.severity
        }
        
        from fastapi.concurrency import run_in_threadpool
        file_path, file_name = await run_in_threadpool(
            export_to_pdf, 
            building_info, 
            analysis_result, 
            req.llm_content,
            req.main_image,
            req.defect_image
        )
        
        return FileResponse(
            path=file_path, 
            filename=file_name,
            media_type='application/pdf'
        )
    except Exception as e:
        logger.error(f"PDF Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate")
async def calculate_value(req: AppraisalRequest):
    """표준단가 데이터 기반 적산가액 계산"""
    try:
        result = calculate_appraisal(
            req.total_area,
            req.usage_name,
            req.elapsed_years,
            req.defect_ratio,
            req.severity
        )
        return result
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report")
async def create_report(req: AppraisalRequest):
    """LLM을 이용한 감정평가 리포트 생성"""
    try:
        report = generate_appraisal_report(
            req.defect_ratio,
            req.severity,
            req.confidence,
            req.usage_name, 
            req.elapsed_years,
            req.address,
            req.is_official_data
        )
        return {"report": report}
    except Exception as e:
        logger.error(f"Report API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
