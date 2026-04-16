from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class BuildingOfficialData(BaseModel):
    """건축물대장 공공데이터 모델"""
    strctCdNm: str = Field(..., description="구조명")
    totArea: float = Field(..., description="연면적")
    useAprvDe: str = Field(..., description="사용승인일 (YYYYMMDD)")

    @validator('totArea')
    def area_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('연면적은 0보다 커야 합니다.')
        return v

class DefectAnalysisResult(BaseModel):
    """AI 비전 분석 결과 모델"""
    defect_ratio: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: str
    processed_image: Optional[object] = None # numpy array

class AppraisalValueSummary(BaseModel):
    """최종 적산가액 산출 요약 모델"""
    reconstruction_cost: float
    basic_depreciation: float
    ai_correction_depreciation: float
    final_value: float
