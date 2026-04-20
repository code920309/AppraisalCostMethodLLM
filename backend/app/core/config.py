import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """애플리케이션 환경 설정 로더"""
    
    # API Keys
    PUBLIC_DATA_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")
    KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    
    # LLM Config
    ENV_TYPE = os.getenv("ENV_TYPE", "LOCAL")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    
    # Model Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "yolov8m-seg.pt")
    
    # Log Config
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
