"""
국가법령센터 웹 크롤링 설정 모듈
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 웹사이트 기본 URL
BASE_URL = "https://www.law.go.kr"
SEARCH_URL = f"{BASE_URL}/LSW/lsInfoP.do"
LAW_DETAIL_URL = f"{BASE_URL}/LSW/lsInfoP.do"
PRECEDENT_SEARCH_URL = f"{BASE_URL}/LSW/precSc.do"
PRECEDENT_DETAIL_URL = f"{BASE_URL}/LSW/precInfoP.do"

# 기본 요청 설정
DEFAULT_PAGE_SIZE = 20  # 기본 결과 개수
MAX_PAGE_SIZE = 100     # 최대 결과 개수
DEFAULT_PAGE = 1        # 기본 페이지 번호

# 요청 딜레이 설정 (초)
REQUEST_DELAY = 2.0     # 웹 요청 간 딜레이 (서버 부하 방지)

# 출력 디렉토리 설정
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
PDF_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "pdfs")

# 로그 설정
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "law_crawler.log")
DEBUG_LOG_FILE = os.path.join(LOG_DIR, "crawler_debug.log")
# 환경변수 DEBUG_CRAWLER=1 이면 상세 디버그 로그 기록
DEBUG_CRAWLER = os.environ.get("DEBUG_CRAWLER", "1") == "1"

# 한글 폰트 경로 (시스템에 따라 조정 필요)
# macOS: /System/Library/Fonts/AppleGothic.ttf
# Windows: C:/Windows/Fonts/malgun.ttf
# Linux: /usr/share/fonts/truetype/nanum/NanumGothic.ttf
FONT_PATH = os.getenv("FONT_PATH", "")

def validate_config():
    """설정 유효성 검사"""
    # 출력 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    return True
