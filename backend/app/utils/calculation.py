from datetime import datetime
from src.constants import STRUCTURE_DURABLE_LIFE

def calculate_elapsed_years(use_aprv_de):
    """건물 사용승인일 기반 경과 연수 계산"""
    if not use_aprv_de or len(str(use_aprv_de)) < 4:
        return 15.0
    try:
        today = datetime.now()
        aprv_date = datetime.strptime(str(use_aprv_de), '%Y%m%d')
        diff = today.year - aprv_date.year
        return float(diff)
    except:
        return 15.0

def calculate_appraisal_value(total_area, reconstruction_cost_sqm, elapsed_years, structure_type, defect_results):
    """
    원가법 기반 최종 가치 산정 로직
    재조달원가 - (기본 감가 + AI 보정 감가) = 최종 적산가액
    """
    durable_life = STRUCTURE_DURABLE_LIFE.get(structure_type, 30)
    
    # 1. 재조달원가
    reconstruction_cost = total_area * reconstruction_cost_sqm
    
    # 2. 기본 감가 (정액법 원리)
    basic_depreciation = reconstruction_cost * (elapsed_years / durable_life)
    if basic_depreciation > reconstruction_cost:
        basic_depreciation = reconstruction_cost
    
    # 3. AI 보정 감가 (물리적 상태 반영)
    defect_ratio = defect_results.get("defect_ratio", 0.0)
    confidence = defect_results.get("confidence", 0.0)
    severity = defect_results.get("severity", "정상")
    
    severity_weight = {"정상": 0.0, "주의": 0.05, "경구": 0.15, "심각": 0.30}
    weight = severity_weight.get(severity, 0.1)
    
    ai_correction_depreciation = reconstruction_cost * (defect_ratio * confidence * weight)
    
    # 최종 가치
    final_value = reconstruction_cost - (basic_depreciation + ai_correction_depreciation)
    
    return {
        "reconstruction_cost": reconstruction_cost,
        "basic_depreciation": basic_depreciation,
        "ai_correction_depreciation": ai_correction_depreciation,
        "final_value": max(0, final_value)
    }
