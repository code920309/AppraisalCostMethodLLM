from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.api_service import get_building_official_data, search_address_kakao
from app.models.building import BuildingOfficialData
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/search")
async def search_address(q: str = Query(..., min_length=2)):
    """카카오 API를 이용한 주소 검색"""
    results = search_address_kakao(q)
    return {"results": results}

@router.get("/info", response_model=BuildingOfficialData)
async def get_building_info(
    sigunguCd: str, 
    bjdongCd: str, 
    bun: str, 
    ji: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """건축물대장 정보 조회 및 로드뷰 이미지 수집"""
    data_dict = get_building_official_data(sigunguCd, bjdongCd, bun, ji)
    if not data_dict:
        raise HTTPException(status_code=404, detail="건축물 정보를 찾을 수 없습니다.")
    
    # 위경도가 있으면 구글 로드뷰 수집
    import base64
    from app.services.api_service import get_building_panorama_google
    
    panorama_base64 = None
    if lat and lon:
        img_content = get_building_panorama_google(lat, lon)
        if img_content:
            panorama_base64 = base64.b64encode(img_content).decode('utf-8')
    
    data_dict['panorama_image'] = panorama_base64
    return data_dict
