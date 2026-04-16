from typing import List, Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

# [표준신축단가 데이터] DB 대신 서버 내 상수로 관리
STANDARD_UNIT_COSTS = {
    "다가구주택": {"main": "단독주택", "cost": 2079879, "aircon": True, "elevator": True},
    "다중주택": {"main": "단독주택", "cost": 2127879, "aircon": True, "elevator": True},
    "단독주택": {"main": "단독주택", "cost": 2079879, "aircon": True, "elevator": True}, # 기본값
    "다세대주택": {"main": "공동주택", "cost": 2055379, "aircon": True, "elevator": True},
    "연립주택": {"main": "공동주택", "cost": 2329450, "aircon": True, "elevator": True},
    "아파트": {"main": "공동주택", "cost": 1927375, "aircon": True, "elevator": True},
    "오피스텔": {"main": "그 외", "cost": 1945741, "aircon": False, "elevator": True},
    "근린생활시설": {"main": "그 외", "cost": 1920997, "aircon": False, "elevator": True},
    "창고": {"main": "그 외", "cost": 860857, "aircon": False, "elevator": False},
    "공장": {"main": "그 외", "cost": 1053375, "aircon": False, "elevator": False},
}

def match_unit_cost(usage_name: str) -> Dict:
    """건축물대장 용도명 기반 단가 데이터 매칭"""
    # 1. 공백 제거 및 정규화
    clean_name = usage_name.replace(" ", "")
    
    # 2. 키워드 매칭
    for key, data in STANDARD_UNIT_COSTS.items():
        if key in clean_name:
            logger.info(f"단가 매칭 성공: {usage_name} -> {key}")
            return data
            
    # 3. 매칭 실패 시 기본값 (근린생활시설 기준)
    logger.warning(f"단가 매칭 실패: {usage_name}, 기본값 적용")
    return {"main": "그 외", "cost": 2000000, "aircon": False, "elevator": True}

def calculate_appraisal(
    total_area: float,
    usage_name: str,
    elapsed_years: int,
    defect_ratio: float,
    severity: str
) -> Dict:
    """원가법 기반 탁상감정 핵심 산식 구현"""
    
    # 1. 재조달원가 산정
    unit_info = match_unit_cost(usage_name)
    base_unit_cost = unit_info['cost']
    
    # 지수 보정 (예시: 2024년 대비 2025년 생산자물가지수 1.03 적용)
    reproduction_unit_cost = base_unit_cost * 1.03
    replacement_cost = reproduction_unit_cost * total_area
    
    # 2. 물리적 감가 (정액법: 내용년수 40년, 잔가율 10% 가정)
    useful_life = 40
    residual_rate = 0.1
    
    if elapsed_years >= useful_life:
        physical_depreciation_rate = 1.0 - residual_rate
    else:
        physical_depreciation_rate = (elapsed_years / useful_life) * (1.0 - residual_rate)
    
    physical_depreciation = replacement_cost * physical_depreciation_rate
    
    # 3. 관찰 감가 (AI 비전 분석 결과 기반 보정)
    # 심각도에 따른 추가 감가율 (심각: 5%, 경구: 2%, 주의: 0.5%)
    obs_depreciation_rate = 0.0
    if severity == "심각": obs_depreciation_rate = 0.05
    elif severity == "경구": obs_depreciation_rate = 0.02
    elif severity == "주의": obs_depreciation_rate = 0.005
    
    # 결함 면적 비중에 따른 가중치 추가
    obs_depreciation_rate += (defect_ratio * 0.1) 
    
    # 현재 가치(재조달원가 - 물리적감가)에 대해 관찰감가 적용
    current_physical_value = replacement_cost - physical_depreciation
    observation_depreciation = current_physical_value * obs_depreciation_rate
    
    # 4. 최종 적산가액
    total_depreciation = physical_depreciation + observation_depreciation
    final_value = replacement_cost - total_depreciation
    
    return {
        "replacement_cost": round(replacement_cost),
        "physical_depreciation": round(physical_depreciation),
        "observation_depreciation": round(observation_depreciation),
        "total_depreciation": round(total_depreciation),
        "final_value": round(final_value),
        "depreciation_rate": round((total_depreciation / replacement_cost) * 100, 2),
        "matched_unit_cost": round(reproduction_unit_cost)
    }
