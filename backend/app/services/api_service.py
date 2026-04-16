import requests
import base64
from app.core.config import Config
from app.utils.logger import get_logger
from app.utils.exceptions import APIConnectionError, DataNotFoundError
from app.models.building import BuildingOfficialData

logger = get_logger(__name__)

def get_building_official_data(sigunguCd, bjdongCd, bun, ji):
    """건축물대장 표제부 정보 조회 API"""
    url = "http://apis.data.go.kr/1613000/BldRgstService_v2/getBrTitleInfo"
    """건축물대장 표제부 정보 조회 API (건축HUB 버전)"""
    # 사용자가 신청한 건축HUB 전용 엔드포인트로 변경
    base_url = "https://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"
    
    from urllib.parse import unquote
    # Decoding 키를 사용하여 requests가 내부적으로 인코딩하게 함
    service_key = unquote(Config.PUBLIC_DATA_API_KEY)
    
    params = {
        'serviceKey': service_key,
        'sigunguCd': sigunguCd,
        'bjdongCd': bjdongCd,
        'platGbCd': '0',
        'bun': bun.zfill(4),
        'ji': ji.zfill(4),
        '_type': 'json',
        'numOfRows': '1'
    }
    
    try:
        logger.info(f"건축물대장(건축HUB) API 호출: {sigunguCd}{bjdongCd} {bun}-{ji}")
        
        # 타임아웃을 30초로 연장하여 공공데이터 서버 지연에 대응
        response = requests.get(base_url, params=params, timeout=30)
        
        # 500 에러 시 상세 내용 기록
        if response.status_code == 500:
            logger.error(f"공공데이터 API 서버 오류(500): {response.text}")
            raise DataNotFoundError("건축HUB API 서버 내부 오류입니다. (활용 신청 상태 확인 필요)")
            
        response.raise_for_status()
        
        data = response.json()
        import json
        # API 응답 결과 전체를 로그에 상세히 기록 (가독성을 위해 인덴트 적용)
        logger.info(f"건축HUB API 응답 수신 성공:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
        
        items = data.get('response', {}).get('body', {}).get('items', {})
        
        if items and 'item' in items:
            item = items['item']
            if isinstance(item, list):
                item = item[0]
            
            # 데이터 추출 전 전체 키 확인을 위한 로그
            logger.info(f"추출된 item 데이터 키 목록: {list(item.keys())}")
            
            # 층수 및 날짜 필드 유연한 추출 (필드명 대소문자나 언더바 대응)
            def get_field(item, *keys):
                for key in keys:
                    val = item.get(key)
                    if val is not None:
                        return val
                return None

            strctCdNm = get_field(item, 'strctCdNm', 'strct_cd_nm') or '미분류'
            totArea = get_field(item, 'totArea', 'tot_area') or 0.0
            # 날짜 관련 필드 누락 시 허가일이나 착공일로 최대한 대체 (필드명 변종 대응: useAprDay 등)
            useAprvDe = get_field(item, 'useAprvDe', 'useAprDay', 'use_aprv_de', 'pmsDay', 'pms_day', 'stcnsDay', 'stcns_day') or ''
            grndFlrCnt = get_field(item, 'grndFlrCnt', 'grnd_flr_cnt') or 0
            ugndFlrCnt = get_field(item, 'ugndFlrCnt', 'ugnd_flr_cnt') or 0

            logger.info(f"매핑된 데이터: 구조={strctCdNm}, 면적={totArea}, 승인일={useAprvDe}, 지상층={grndFlrCnt}")

            validated_data = BuildingOfficialData(
                strctCdNm=str(strctCdNm),
                totArea=float(totArea),
                useAprvDe=str(useAprvDe),
                grndFlrCnt=int(grndFlrCnt),
                ugndFlrCnt=int(ugndFlrCnt)
            )
            return validated_data.dict()
        else:
            logger.warning("건축물대장 정보를 찾을 수 없음")
            raise DataNotFoundError("해당 주소의 건축물대장 정보를 찾을 수 없습니다.")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API 연결 오류: {str(e)}")
        raise APIConnectionError("공공데이터 API 서버와 통신 중 오류가 발생했습니다.", details=str(e))
    except Exception as e:
        logger.error(f"데이터 처리 오류: {str(e)}")
        return None
        
def search_address_kakao(query):
    """카카오 로컬 REST API를 사용한 주소 키워드 검색"""
    if not query:
        return []
    
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {Config.KAKAO_REST_API_KEY}"}
    params = {"query": query}
    
    try:
        logger.info(f"카카오 주소 검색 시작: {query}")
        response = requests.get(url, headers=headers, params=params, timeout=5)
        
        if response.status_code == 403:
            logger.error("카카오 API 권한 오류 (403): API 키 또는 도메인 설정을 확인하세요.")
            return []
            
        response.raise_for_status()
        
        documents = response.json().get("documents", [])
        logger.info(f"카카오 주소 검색 완료: {len(documents)}건 발견")
        
        results = []
        for doc in documents:
            addr_info = doc.get("address")
            if not addr_info: continue
            
            results.append({
                "address_name": doc.get("address_name"),
                "bcode": addr_info.get("b_code"),
                "h_code": addr_info.get("h_code"),
                "main_address_no": addr_info.get("main_address_no"),
                "sub_address_no": addr_info.get("sub_address_no", "0"),
                "lat": doc.get("y"),
                "lon": doc.get("x")
            })
        return results
    except Exception as e:
        logger.error(f"카카오 주소 검색 실패: {e}")
        return []

def get_building_panorama_google(lat, lon, size="600x400"):
    """위경도 좌표를 기반으로 구글 Street View Static 이미지 수집"""
    if not Config.GOOGLE_MAPS_API_KEY:
        logger.error("Google Maps API Key가 설정되지 않았습니다.")
        return None

    url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": size,
        "location": f"{lat},{lon}",
        "key": Config.GOOGLE_MAPS_API_KEY,
        "fov": 100,   # 시야각 (약간 넓게 설정)
        "pitch": 5    # 카메라 높이 각도 (건물 상단이 잘 보이도록 약간 위로 조절)
    }

    try:
        logger.info(f"구글 로드뷰 이미지 요청: {lat}, {lon}")
        response = requests.get(url, params=params, timeout=10)
        
        # HTTP 200 OK이면서 응답 본문이 이미지 형태인 경우 성공으로 간주
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            return response.content
        else:
            logger.warning(f"로드뷰 이미지를 수집할 수 없습니다. (Status: {response.status_code})")
            return None
    except Exception as e:
        logger.error(f"구글 로드뷰 API 호출 중 예외 발생: {str(e)}")
        return None