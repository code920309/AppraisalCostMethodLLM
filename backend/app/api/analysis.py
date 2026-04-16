from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2
from PIL import Image
import io
import os
from app.services.vision_service import analyze_with_model
from app.core.config import Config
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/detect")
async def detect_defects(file: UploadFile = File(...)):
    """이미지를 업로드하여 외벽 결함 분석 수행"""
    try:
        content = await file.read()
        logger.info(f"이미지 수신 완료: {file.filename} ({len(content)} bytes)")
        
        image = Image.open(io.BytesIO(content)).convert("RGB")
        img_array = np.array(image)
        
        # 실제 설정된 모델 경로 사용
        model_path = Config.YOLO_MODEL_PATH
        logger.info(f"YOLO 모델 사용 경로: {model_path}")
        
        # 모델 분석 실행 (콘솔에 진행 로그 출력)
        print(f"\n[AI Analysis] Running inference on {file.filename}...")
        result = analyze_with_model(model_path, img_array)
        print(f"[AI Analysis] Result: {result['severity']} (Ratio: {result['defect_ratio']:.4f})\n")
        
        import base64
        _, buffer = cv2.imencode('.jpg', result['processed_image'])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "defect_ratio": result['defect_ratio'],
            "confidence": result['confidence'],
            "severity": result['severity'],
            "image_data": img_base64
        }
    except Exception as e:
        logger.error(f"Detection API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
