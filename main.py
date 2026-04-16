import subprocess
import sys
import os

def run_app():
    """Streamlit 앱 실행 스크립트"""
    # 현재 디렉토리를 Python Path에 추가
    os.environ["PYTHONPATH"] = os.getcwd()
    
    cmd = ["streamlit", "run", "src/app.py"]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nAppraisalCost AI 시스템을 종료합니다.")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    run_app()
