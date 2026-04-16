import requests
import streamlit as st
from src.config import Config
from src.utils.logger import get_logger
from src.utils.exceptions import LLMServiceError

logger = get_logger(__name__)

@st.cache_data(show_spinner=False)
def generate_appraisal_report(defect_ratio, severity, confidence, structure_type, elapsed_years, is_official_data=False):
    """베테랑 감정평가사 페르소나를 사용한 리포트 생성"""
    env_type = Config.ENV_TYPE
    system_prompt = (
        "당신은 10년 차 베테랑 감정평가사이며 건축물 구조 진단 전문가입니다. "
        "분석된 수치 데이터를 기반으로 전문적인 감정평가 의견서(Narrative Generation)를 작성하십시오. "
        "신뢰감 있고 정교한 법률/감정평가 용어를 사용하십시오."
    )
    disclaimer = "본 의견서는 공공데이터포털의 공식 건축물대장 정보와 AI Vision 분석 결과를 결합하여 작성되었습니다." if is_official_data else ""
    
    user_prompt = f"""
    {disclaimer}
    [건축물 분석 데이터]
    - 구조: {structure_type}
    - 경과연수: {elapsed_years}년
    - 결함 심각도: {severity}
    - AI 탐지 신뢰도: {confidence:.2%}
    - 물리적 결함률: {defect_ratio:.2%}

    상기 데이터를 바탕으로 다음 항목을 포함한 '전문 감정평가 의견서'를 작성하십시오.
    1. 대상 건축물에 대한 종합 감정 평가 의견
    2. 물리적 상태(결함률)를 고려한 시점 수정 및 감가 수정 내역
    3. 관리 상태에 따른 미래 가치 보전 관련 전문가 제언
    """

    try:
        logger.info(f"LLM 리포트 생성 요청 (Env: {env_type})")
        
        if env_type == "LOCAL":
            url = "http://localhost:11434/api/generate"
            payload = {"model": "llama3", "prompt": f"{system_prompt}\n\n{user_prompt}", "stream": False}
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200: 
                return response.json().get("response", "의견서를 생성할 수 없습니다.")
        else:
            if not Config.LLM_API_KEY:
                raise LLMServiceError("배포 환경 API 키가 설정되지 않았습니다.")
                
            headers = {"Authorization": f"Bearer {Config.LLM_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-instruct", 
                "messages": [
                    {"role": "system", "content": system_prompt}, 
                    {"role": "user", "content": user_prompt}
                ]
            }
            response = requests.post(Config.LLM_API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200: 
                return response.json()["choices"][0]["message"]["content"]
                
        raise LLMServiceError(f"LLM 서비스 응답 오류: {response.status_code}")
        
    except Exception as e:
        logger.error(f"LLM 서비스 오류: {str(e)}")
        return f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
