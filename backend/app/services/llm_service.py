import requests
from app.core.config import Config
from app.utils.logger import get_logger
from app.utils.exceptions import LLMServiceError

logger = get_logger(__name__)

def generate_appraisal_report(defect_ratio, severity, confidence, structure_type, elapsed_years, address="", is_official_data=False):
    """베테랑 감정평가사 페르소나를 사용한 리포트 생성"""
    env_type = Config.ENV_TYPE
    system_prompt = (
        "당신은 「감정평가 및 감정평가사에 관한 법률」을 준수하는 10년 차 베테랑 감정평가사 페르소나를 가진 AI 모델입니다. "
        "제공되는 데이터를 바탕으로 PDF 변환이 용이하도록 마크다운 형식을 사용하여 '전문 감정평가 의견서'를 작성하십시오. "
        "특정 인물이나 법인 명칭은 생략하고 객관적인 분석에 집중하십시오."
    )
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    user_prompt = f"""
    아래 [입력 데이터]를 바탕으로 [출력 형식]에 맞춰 전문 감정평가 의견서를 작성하십시오.

    ### [작성 가이드라인]
    1. 건물 평가의 핵심인 '원가법'을 중심으로 재조달원가와 감가수정 과정을 논리적으로 서술하십시오.
    2. AI Vision이 탐지한 {severity} 등급과 {defect_ratio:.2%}의 결함률을 '관찰감가법'에 의한 물리적 감가 요인으로 반드시 반영하십시오.
    3. 시각적 증거와 가치 산정의 연결성을 강화하는 전문 어조를 사용하십시오.

    ### [입력 데이터]
    - 소재지: {address}
    - 구조/연수: {structure_type} / {elapsed_years}년
    - AI 분석: 결함률 {defect_ratio:.2%}, 심각도 {severity}, 신뢰도 {confidence:.2%}

    ---

    ### [출력 형식 (마크다운)]

    # 감 정 평 가 의 견 서 (Appraisal Report)

    ## 1. 대상물건의 개요
    - **소재지:** {address}
    - **구조 및 용도:** {structure_type}
    - **경과연수:** {elapsed_years}년

    ## 2. 감정평가방법의 선정 및 근거
    (여기에 작성: 원가법 적용 이유와 기준시점 판단에 대한 전문적 소견)

    ## 3. AI Vision 분석에 따른 감가수정 내역
    - **물리적 상태 분석:** AI 탐지 결과 결함률 {defect_ratio:.2%} (심각도: {severity})
    - **감정평가 의견:** (여기에 작성: 관찰감가법 관점에서의 물리적 결함 해석)

    ## 4. 종합 감정 의견
    (여기에 작성: 건축물 상태와 AI 분석 결과를 종합한 총평)

    ## 5. 미래가치 보존을 위한 제언
    (여기에 작성: 향후 유지보수 및 경제적 잔존연수 관리를 위한 제언)

    ---
    기준시점: {current_date}
    작성기관: AI 건축물 자동 감정 시스템
    """

    try:
        logger.info(f"LLM 리포트 생성 요청 (Env: {env_type})")
        
        if env_type == "LOCAL":
            url = "http://localhost:11434/api/generate"
            payload = {"model": "gemma2", "prompt": f"{system_prompt}\n\n{user_prompt}", "stream": True}
            
            # 스트리밍 요청 처리 (터미널에서 실시간 확인 가능)
            full_response = ""
            logger.info(f"Ollama 요청 시작: {url} (Model: gemma2)")
            print("\n[AI Appraiser is thinking...]")
            
            try:
                with requests.post(url, json=payload, timeout=900, stream=True) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            import json
                            try:
                                chunk = json.loads(line)
                                text_chunk = chunk.get("response", "")
                                full_response += text_chunk
                                print(text_chunk, end="", flush=True) 
                                if chunk.get("done"): break
                            except json.JSONDecodeError as je:
                                logger.error(f"JSON 디코딩 오류: {line}")
                                continue
                
                print("\n[Report Generation Complete]\n")
                if not full_response:
                    logger.warning("Ollama 응답이 비어있습니다.")
                return full_response if full_response else "의견서를 생성할 수 없습니다. (AI 응답 공백)"
                
            except requests.exceptions.RequestException as re:
                logger.error(f"Ollama 연결 실패: {re}")
                return f"AI 서비스(Ollama) 연결에 실패했습니다: {str(re)}"
            
        else:
            if not Config.LLM_API_KEY:
                raise LLMServiceError("배포 환경 API 키가 설정되지 않았습니다.")
                
            headers = {"Authorization": f"Bearer {Config.LLM_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [
                    {"role": "system", "content": system_prompt}, 
                    {"role": "user", "content": user_prompt}
                ]
            }
            # 외부 API도 충분한 여유를 위해 300초 적용
            response = requests.post(Config.LLM_API_URL, headers=headers, json=payload, timeout=300)
            if response.status_code == 200: 
                return response.json()["choices"][0]["message"]["content"]
                
        raise LLMServiceError(f"LLM 서비스 응답 오류: {response.status_code}")
        
    except Exception as e:
        logger.error(f"LLM 서비스 오류: {str(e)}")
        return f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
