import logging
import os
from datetime import datetime
from src.config import Config

def get_logger(name):
    """중앙 집중식 로깅 인스턴스 생성"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # 콘솔 출력 설정
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 파일 출력 설정
        log_filename = f"appraisal_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join(Config.LOG_DIR, log_filename)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    return logger
