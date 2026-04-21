import os
import logging
from dotenv import load_dotenv

# 시스템 환경변수(HF Secrets 등)를 .env보다 우선 적용
# override=False: 이미 시스템에 설정된 값이 있으면 .env로 덮어쓰지 않음
load_dotenv(override=False)

logger = logging.getLogger(__name__)

class Config:
    """애플리케이션 환경 설정 로더"""

    # API Keys — os.environ.get()으로 시스템 환경변수에서 직접 읽기
    @staticmethod
    def _get_env(key: str, default: str = None, required: bool = False) -> str:
        val = os.environ.get(key, default)
        if required and not val:
            logger.warning(f"[Config] 환경변수 '{key}'가 설정되지 않았습니다. HF Secrets 또는 .env를 확인하세요.")
        return val

    PUBLIC_DATA_API_KEY  = os.environ.get("PUBLIC_DATA_API_KEY")
    KAKAO_REST_API_KEY   = os.environ.get("KAKAO_REST_API_KEY")
    GOOGLE_MAPS_API_KEY  = os.environ.get("GOOGLE_MAPS_API_KEY")

    # LLM Config
    ENV_TYPE    = os.environ.get("ENV_TYPE", "LOCAL")
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")

    @classmethod
    def validate_env(cls):
        """필수 환경변수 누락 여부를 서버 시작 시 검사"""
        required_keys = {
            "KAKAO_REST_API_KEY":  cls.KAKAO_REST_API_KEY,
            "PUBLIC_DATA_API_KEY": cls.PUBLIC_DATA_API_KEY,
            "LLM_API_KEY":         cls.LLM_API_KEY,
        }
        for key, val in required_keys.items():
            if not val:
                logger.warning(f"[Config] '{key}' 환경변수가 비어 있습니다 (현재 값: {repr(val)})")
    
    # Model Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "yolov8m-seg.pt")
    FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")

    # NanumGothic - Google Fonts GitHub raw CDN
    _FONT_URLS = {
        "NanumGothic.ttf": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
        "NanumGothic-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
    }

    @classmethod
    def ensure_model_exists(cls):
        import urllib.request
        os.makedirs(os.path.dirname(cls.YOLO_MODEL_PATH), exist_ok=True)
        if not os.path.exists(cls.YOLO_MODEL_PATH):
            print(f"Downloading YOLO model to {cls.YOLO_MODEL_PATH}...")
            url = "https://huggingface.co/donggyuuu/yolo-v8-appraisal/resolve/main/yolov8m-seg.pt"
            urllib.request.urlretrieve(url, cls.YOLO_MODEL_PATH)
            print("YOLO model download complete.")

    @classmethod
    def ensure_fonts_exist(cls):
        import urllib.request
        os.makedirs(cls.FONT_DIR, exist_ok=True)
        for filename, url in cls._FONT_URLS.items():
            dest = os.path.join(cls.FONT_DIR, filename)
            if not os.path.exists(dest):
                print(f"Downloading font: {filename}...")
                urllib.request.urlretrieve(url, dest)
                print(f"Font downloaded: {filename}")

    # Log Config
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
