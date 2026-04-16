import os
import cv2
import numpy as np
from src.config import Config
from src.utils.logger import get_logger
from src.utils.exceptions import VisionAnalysisError
from src.models.building import DefectAnalysisResult

logger = get_logger(__name__)

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    logger.warning("ultralytics 라이브러리가 설치되지 않았습니다. YOLO 분석이 비활성화됩니다.")
    HAS_YOLO = False

def analyze_with_model(model_path, img_array):
    """YOLOv8 모델을 사용한 외벽 결함 세그먼테이션 분석"""
    if not HAS_YOLO:
        raise VisionAnalysisError("YOLO 라이브러리가 설치되어 있지 않습니다.")
    
    if not os.path.exists(model_path):
        logger.error(f"모델 파일을 찾을 수 없음: {model_path}")
        raise VisionAnalysisError(f"모델 파일을 찾을 수 없습니다: {model_path}")
    
    try:
        logger.info(f"YOLO 분석 시작 (Model: {os.path.basename(model_path)})")
        model = YOLO(model_path)
        results = model(img_array)
        result = results[0]
        
        defect_ratio = 0.0
        confidence = 0.0
        h, w = img_array.shape[:2]
        processed_img = img_array
        
        if result.masks is not None:
            processed_img = result.plot()[..., ::-1]
            masks_data = result.masks.data.cpu().numpy()
            if len(masks_data) > 0:
                combined_mask = np.max(masks_data, axis=0)
                combined_mask_resized = cv2.resize(combined_mask, (w, h), interpolation=cv2.INTER_NEAREST)
                defect_pixels = np.sum(combined_mask_resized > 0)
                defect_ratio = float(defect_pixels) / (h * w)
            
            if result.boxes is not None and len(result.boxes) > 0:
                confidence = float(result.boxes.conf.mean().cpu().numpy())
        
        severity = "정상"
        if defect_ratio > 0:
            if defect_ratio < 0.02: severity = "주의"
            elif defect_ratio < 0.08: severity = "경구"
            else: severity = "심각"
            
        validated_result = DefectAnalysisResult(
            defect_ratio=defect_ratio,
            confidence=confidence,
            severity=severity,
            processed_image=processed_img
        )
        
        logger.info(f"분석 완료: 비율={defect_ratio:.4f}, 심각도={severity}")
        return validated_result.dict()
        
    except Exception as e:
        logger.error(f"비전 분석 중 예외 발생: {str(e)}")
        raise VisionAnalysisError("이미지 분석 중 기술적인 오류가 발생했습니다.", details=str(e))
