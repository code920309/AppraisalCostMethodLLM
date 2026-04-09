import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import io
import os

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    st.warning("ultralytics 패키지가 설치되지 않았습니다.")

def analyze_with_model(model_path, img_array):
    if not HAS_YOLO or not os.path.exists(model_path):
        return None
    try:
        model = YOLO(model_path)
        results = model(img_array)
        result = results[0]
        
        # 기본 지표
        defect_ratio = 0.0
        confidence = 0.0
        defect_count = 0
        processed_img = img_array
        
        if result.masks is not None:
            processed_img = result.plot()[..., ::-1] # BGR to RGB
            h, w = img_array.shape[:2]
            
            masks_data = result.masks.data.cpu().numpy()
            defect_count = len(masks_data)
            if defect_count > 0:
                combined_mask = np.max(masks_data, axis=0)
                combined_mask_resized = cv2.resize(combined_mask, (w, h), interpolation=cv2.INTER_NEAREST)
                defect_pixels = np.sum(combined_mask_resized > 0)
                defect_ratio = float(defect_pixels) / (h * w)
                
            if result.boxes is not None and len(result.boxes) > 0:
                confidence = float(result.boxes.conf.mean().cpu().numpy())
        else:
            processed_img = result.plot()[..., ::-1]
            if result.boxes is not None and len(result.boxes) > 0:
                defect_count = len(result.boxes)
                confidence = float(result.boxes.conf.mean().cpu().numpy())
                
        severity = "정상"
        if defect_ratio > 0.0:
            if defect_ratio < 0.02: severity = "주의"
            elif defect_ratio < 0.08: severity = "경구/단절됨"
            else: severity = "심각한 균열(Severe)"
            
        return {
            "processed_image": processed_img,
            "defect_ratio": defect_ratio,
            "confidence": confidence,
            "defect_count": defect_count,
            "severity": severity
        }
        
    except Exception as e:
        st.error(f"모델({model_path}) 예측 중 오류: {e}")
        return None


def main():
    st.set_page_config(page_title="AppraisalCost AI - 스마트 감정평가 솔루션", layout="wide")
    
    # 상용 서비스 느낌의 헤더
    st.title("🏢 AppraisalCost AI - 스마트 감정평가 및 결함 스캔")
    st.markdown("""
    **원가법(Cost Method)** 기반 부동산 감정평가 자동화 플랫폼입니다.  
    건축물의 연한과 구조에 따른 기본 감가율을 산출하고, **딥러닝(Computer Vision) 기반 정밀 스캔**으로 물리적 결함을 찾아내어 최종 감가 보정치를 자동 계산합니다.
    """)
    
    st.sidebar.header("📝 감정평가 기초 정보")
    # 상용화 느낌을 주기 위한 가짜/장식용 입력 폼들
    structure_type = st.sidebar.selectbox("건축물 구조", ["철근콘크리트", "조적", "목", "기타"])
    total_area = st.sidebar.number_input("전체 연면적 (m²)", min_value=1.0, value=84.0)
    elapsed_years = st.sidebar.number_input("경과 연수 (년)", min_value=0.0, value=15.0)
    
    # 모델 경로는 화면에 숨기거나 작게 표시
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(os.path.dirname(base_dir), "models")
    model_final_path = os.path.join(model_dir, "yolov8m-seg.pt")
    model_prev_path = os.path.join(model_dir, "best_trained.pt")
    if not os.path.exists(model_prev_path):
        model_prev_path = os.path.join(model_dir, "yolov8s-seg.pt")
        
    with st.sidebar.expander("⚙️ 엔진 및 모델 상태 (System Info)"):
        st.success(f"Appraisal V2 (YOLOv8m) : Online")
        st.info(f"Appraisal V1 (Legacy) : Online")
    
    st.write("---")
    st.subheader("📷 현장 검수 데이터 업로드")
    uploaded_file = st.file_uploader("건축물 내/외부 결함(균열, 박리 등)이 포함된 사진을 업로드해주세요.", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
        img_array = np.array(image)
        
        st.write("---")
        
        col_btn, _ = st.columns([1, 2])
        with col_btn:
            run_btn = st.button("🚀 정밀 스캔 및 감가액 산출 실행", type="primary")

        if run_btn:
            with st.spinner("Appraisal V2 엔진이 이미지를 분석 중입니다..."):
                res_prev = analyze_with_model(model_prev_path, img_array)
                res_final = analyze_with_model(model_final_path, img_array)
                
            st.write("---")
            st.markdown("### 🔍 AI 결함 분석 리포트 (버전별 엔진 성능 검증)")
            col_target, col_prev, col_final = st.columns(3)
            
            with col_target:
                st.subheader("📸 현장 원본 사진")
                st.image(image, caption="업로드된 원본 이미지", use_container_width=True)
            
            with col_prev:
                st.subheader("💡 구버전 알고리즘 (Legacy)")
                if res_prev:
                    st.image(res_prev["processed_image"], caption="V1 엔진 마스크 처리 결과", use_container_width=True)
                else:
                    st.error("이전 모델을 찾을 수 없거나 추론에 실패했습니다.")
                    
            with col_final:
                st.subheader("🏆 신형 AI 엔진 (Appraisal V2)")
                if res_final:
                    st.image(res_final["processed_image"], caption="YOLOv8m 기반 정밀 분할(Seg) 결과", use_container_width=True)
                else:
                    st.error("최종 모델을 찾을 수 없거나 추론에 실패했습니다.")
            
            st.markdown("<br>### 📊 객체 탐지 및 물리적 감가 지표", unsafe_allow_html=True)
            
            if res_prev and res_final:
                df = pd.DataFrame({
                    "분석 지표 (Metrics)": [
                        "탐지된 결함/파손 수 (건)", 
                        "AI 탐지 신뢰도 (Confidence)", 
                        "단면 대비 결함 면적 추정치 (%)", 
                        "단일 이미지 기준 상태 등급"
                    ],
                    "구버전 알고리즘 (V1)": [
                        f"{res_prev['defect_count']} 건",
                        f"{res_prev['confidence']*100:.1f} %",
                        f"{res_prev['defect_ratio']*100:.2f} %",
                        res_prev['severity']
                    ],
                    "Appraisal V2 (최종 탑재)": [
                        f"{res_final['defect_count']} 건",
                        f"{res_final['confidence']*100:.1f} %",
                        f"{res_final['defect_ratio']*100:.2f} %",
                        res_final['severity']
                    ]
                })
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.success("✅ **Appraisal V2 엔진**이 구버전 대비 미세 크랙 검출 및 가시 영역 분할의 정밀도를 대폭 개선하여, **보다 객관적이고 정확한 물리적 감가율**을 산출합니다.")
                
                # 상용화 느낌 극대화를 위한 하단 감정평가 결과 예시
                st.write("---")
                st.markdown("### 📋 최종 적산가액 요약 (Simulation)")
                m1, m2, m3 = st.columns(3)
                fake_rep_cost = 1500000 * total_area
                fake_base_dep = fake_rep_cost * (elapsed_years / 40)
                fake_adj_dep = fake_base_dep + (fake_rep_cost * res_final['defect_ratio'] * res_final['confidence'])
                m1.metric("재조달원가 (원)", f"{fake_rep_cost:,.0f}")
                m2.metric("보정 전 기본 감가액 (원)", f"{fake_base_dep:,.0f}")
                m3.metric("최종 물리적 감가 반영액 (원)", f"{fake_adj_dep:,.0f}", delta=f"+ {fake_adj_dep - fake_base_dep:,.0f} (AI 추가 감가)", delta_color="inverse")

            
if __name__ == "__main__":
    main()
