import os
import traceback
from playwright.sync_api import sync_playwright
from jinja2 import Environment, FileSystemLoader
from app.utils.logger import get_logger
from app.core.config import Config

logger = get_logger(__name__)

def export_to_pdf(building_info: dict, analysis_result: dict, llm_content: str, main_image: str = "", defect_image: str = ""):
    """
    Playwright (Sync) 버전을 별도 스레드에서 실행하여 루프 충돌을 방지합니다.
    """
    try:
        def prepare_base64(img_str):
            if not img_str: return ""
            clean_str = img_str.strip().replace("\n", "").replace("\r", "")
            if not clean_str.startswith("data:image"):
                # 간단한 서명 체크 (PNG의 경우)
                if clean_str.startswith("iVBORw0KGgo"):
                    return f"data:image/png;base64,{clean_str}"
                return f"data:image/jpeg;base64,{clean_str}"
            return clean_str

        main_img_data = prepare_base64(main_image)
        defect_img_data = prepare_base64(defect_image)

        # 데이터 수신 확인 (상세 로깅)
        logger.info("="*50)
        logger.info("[PDF Data Verification]")
        logger.info(f"Main Image Len: {len(main_img_data)}")
        logger.info(f"Main Image Start: {main_img_data[:100]}...")
        logger.info(f"Defect Image Len: {len(defect_img_data)}")
        logger.info(f"Defect Image Start: {defect_img_data[:100]}...")
        logger.info("="*50)

        logger.info("[PDF Pipeline] Stage 1: Rendering HTML...")
        template_dir = os.path.join(os.getcwd(), "app", "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("report_template.html")
        
        font_dir = os.path.join(os.getcwd(), "assets", "fonts")
        normal_font_path = os.path.join(font_dir, "NanumGothic.ttf").replace(os.path.sep, '/')
        bold_font_path = os.path.join(font_dir, "NanumGothic-Bold.ttf").replace(os.path.sep, '/')

        # 숫자 포맷팅 (원화 콤마 추가)
        def fmt(v): return "{:,.0f}원".format(v) if v != 0 else "-"
        
        total_value = building_info.get("total_value", 0)
        formatted_value = fmt(total_value)
        formatted_replacement = fmt(building_info.get("replacement_cost", 0))
        formatted_physical = fmt(building_info.get("physical_depreciation", 0))
        formatted_observation = fmt(building_info.get("observation_depreciation", 0))

        html_out = template.render(
            address=building_info.get("address", "-"),
            structure_type=building_info.get("structure", "-"),
            elapsed_years=building_info.get("age", 0),
            total_value=formatted_value,
            replacement_cost=formatted_replacement,
            physical_depreciation=formatted_physical,
            observation_depreciation=formatted_observation,
            defect_ratio=f"{analysis_result.get('defect_ratio', 0) * 100:.2f}",
            severity=analysis_result.get("severity", "-"),
            llm_content=llm_content.replace("\n", "<br>"),
            normal_font_path=f"file:///{normal_font_path}",
            bold_font_path=f"file:///{bold_font_path}",
            main_image=main_img_data,
            defect_image=defect_img_data
        )

        logger.info("[PDF Pipeline] Stage 2: Starting Playwright (Thread-safe)...")
        report_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        safe_address = "".join([c for c in building_info.get('address', 'result') if c.isalnum() or c in ' _-']).replace(' ', '_')
        file_name = f"appraisal_{safe_address}.pdf"
        file_path = os.path.join(report_dir, file_name)

        # 동기(sync) 방식으로 작성하되, 호출부(API)에서 별도 스레드로 격리하여 실행합니다.
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_out, wait_until="networkidle")
            page.pdf(
                path=file_path,
                format="A4",
                print_background=True,
                margin={"top": "1.5cm", "right": "1.5cm", "bottom": "1.5cm", "left": "1.5cm"}
            )
            browser.close()
            
        logger.info(f"[PDF Pipeline] Final Success: {file_path}")
        return file_path, file_name
        
    except Exception as e:
        logger.error(f"[PDF Pipeline] CRITICAL FAILURE: {str(e)}")
        logger.error(traceback.format_exc())
        raise e
