import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* 사이드바 폭 확장 (주소 검색창 잘림 방지) */
    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.8);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid #dee2e6;
    }
    
    .report-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        border-left: 6px solid #1a73e8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-top: 20px;
    }
    
    h1, h2, h3 {
        color: #202124;
        font-weight: 700 !important;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
        height: 3rem;
    }

    .step-header {
        background-color: #f1f3f4;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 5px solid #1a73e8;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
