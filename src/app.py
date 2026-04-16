import streamlit as st
import pandas as pd
import numpy as np
import os
import io
from PIL import Image

# 모듈별 기능 임포트
from src.config import Config
from src.constants import STRUCTURE_DURABLE_LIFE
from src.styles.main_css import inject_custom_css
from src.utils.calculation import calculate_elapsed_years, calculate_appraisal_value
from src.utils.logger import get_logger
from src.utils.exceptions import AppraisalError
from src.services.api_service import get_building_official_data

from src.services.llm_service import generate_appraisal_report
from src.services.vision_service import analyze_with_model

logger = get_logger(__name__)

def main():
    st.set_page_config(page_title="AppraisalCost AI - 지능형 건물 가치 산정", layout="wide")
    inject_custom_css()
    
    # Session State 초기화
    if 'building_data' not in st.session_state:
        st.session_state.building_data = {
            "structure_type": "철근콘크리트",
            "total_area": 84.0,
            "elapsed_years": 15.0,
            "is_official": False,
            "address": "",
            "last_processed_bcode": ""
        }

    st.title("AppraisalCost AI - 지능형 건물 가치 산정 시스템")
    st.markdown("---")
    
    # 사이드바 레이아웃
    st.sidebar.header("Step 1: 주소 및 데이터 입력")
    
    # 카카오 REST API 기반 주소 검색 UI
    from src.services.api_service import search_address_kakao
    
    search_query = st.sidebar.text_input("주소 키워드 입력", placeholder="예: 판교역로 235", help="도로명 또는 지번 주소를 입력하세요.")
    
    if search_query:
        search_results = search_address_kakao(search_query)
        if search_results:
            selected_addr_name = st.sidebar.selectbox(
                "검색 결과 선택",
                options=[r["address_name"] for r in search_results],
                index=0
            )
            
            # 선택된 데이터 추출
            selected_data = next(r for r in search_results if r["address_name"] == selected_addr_name)
            
            if st.sidebar.button("건물 데이터 동기화", type="primary", use_container_width=True):
                with st.status("공식 데이터(건축물대장) 동기화 중...") as status:
                    try:
                        bcode = selected_data["bcode"]
                        bun = selected_data["main_address_no"]
                        ji = selected_data["sub_address_no"]
                        
                        official = get_building_official_data(bcode[:5], bcode[5:], bun, ji)
                        if official:
                            st.session_state.building_data.update({
                                "structure_type": official["strctCdNm"] if official["strctCdNm"] in STRUCTURE_DURABLE_LIFE else "철근콘크리트",
                                "total_area": official["totArea"],
                                "elapsed_years": calculate_elapsed_years(official["useAprvDe"]),
                                "is_official": True, 
                                "address": selected_data["address_name"], 
                                "last_processed_bcode": bcode
                            })
                            status.update(label=f"동기화 성공: {selected_data['address_name']}", state="complete", expanded=False)
                        else:
                            st.session_state.building_data.update({
                                "address": selected_data["address_name"],
                                "last_processed_bcode": bcode
                            })
                            status.update(label="건축물대장 정보를 찾을 수 없습니다.", state="error")
                    except AppraisalError as e:
                        status.update(label=f"오류: {str(e)}", state="error")
        else:
            st.sidebar.warning("검색 결과가 없습니다.")
    


    
    if st.session_state.building_data["address"]:
        st.sidebar.success(f"선택됨: {st.session_state.building_data['address']}")

    st.sidebar.divider()
    st.sidebar.header("감정평가 상세 설정")
    
    structure_type = st.sidebar.selectbox(
        "건축물 구조", 
        list(STRUCTURE_DURABLE_LIFE.keys()),
        index=list(STRUCTURE_DURABLE_LIFE.keys()).index(st.session_state.building_data["structure_type"])
    )
    total_area = st.sidebar.number_input(
        "연면적 (m²)", 
        min_value=1.0, 
        value=float(st.session_state.building_data["total_area"]), 
        step=0.1
    )
    elapsed_years = st.sidebar.number_input(
        "경과연수 (년)", 
        min_value=0.0, 
        max_value=100.0, 
        value=float(st.session_state.building_data["elapsed_years"])
    )
    reconstruction_cost_sqm = st.sidebar.number_input(
        "단위당 재조달원가 (원/m²)", 
        min_value=100000, 
        value=2500000, 
        step=10000
    )
    
    # 모델 경로 (Config 사용)
    model_path = Config.YOLO_MODEL_PATH
    
    # 메인 레이아웃
    st.markdown("<div class='step-header'>Step 2 & 3: 결함 분석 및 리포트 생성</div>", unsafe_allow_html=True)
    col_input, col_result = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("현장 분석 데이터")
        uploaded_file = st.file_uploader("건축물 외벽 결함 이미지 업로드", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
            st.image(image, caption="분석 대상 원본 이미지", use_container_width=True)
            run_btn = st.button("AI 정밀 진단 및 원가 산정 실행", type="primary", use_container_width=True)
        else:
            st.info("건축물 외벽의 결함(균열, 백화 등)을 분석할 이미지를 업로드하세요.")
            run_btn = False

    if uploaded_file and run_btn:
        img_array = np.array(image)
        try:
            with st.spinner("AI 엔진이 결합 면적을 정밀 분석 중입니다..."):
                res = analyze_with_model(model_path, img_array)
            
            with col_result:
                st.subheader("AI 분석 및 가치 산정 결과")
                st.image(res["processed_image"], caption="Defect Segmentation Result", use_container_width=True)
                
                # 원가법 계산
                valuation = calculate_appraisal_value(
                    total_area, reconstruction_cost_sqm, elapsed_years, structure_type, res
                )
                
                m1, m2 = st.columns(2)
                m1.metric("AI 탐지 신뢰도", f"{res['confidence']*100:.1f} %")
                m2.metric("물리적 결함 면적률", f"{res['defect_ratio']*100:.2f} %", delta=res["severity"], delta_color="inverse")
                
                st.markdown("<div class='report-card'>", unsafe_allow_html=True)
                st.markdown("#### 최종 산출 적산가액 요약")
                st.write(f"재조달원가: {valuation['reconstruction_cost']:,.0f} 원")
                st.write(f"기본 감가액: -{valuation['basic_depreciation']:,.0f} 원")
                st.write(f"AI 보정 감가액 (결함 가중): -{valuation['ai_correction_depreciation']:,.0f} 원")
                st.markdown(f"### 최종 적산가액: **{valuation['final_value']:,.0f} 원**")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.divider()
                st.subheader("베테랑 감정평가사 의견서")
                with st.spinner("종합 분석 의견 생성 중..."):
                    report = generate_appraisal_report(
                        res["defect_ratio"], res["severity"], res["confidence"], 
                        structure_type, elapsed_years, 
                        is_official_data=st.session_state.building_data["is_official"]
                    )
                st.info(report)
                
        except AppraisalError as e:
            st.error(f"분석 실패: {str(e)}")
            if e.details:
                st.expander("상세 오류 보기").code(e.details)
        except Exception as e:
            st.error(f"알 수 없는 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()
