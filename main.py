"""
국가법령정보센터 법령 크롤러 - 진입점
법령만 수집. (판례는 추후 재추가 예정)
"""
import argparse
from data_collector import DataCollector
from utils import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="국가법령정보센터 법령 크롤러")
    parser.add_argument("--query", type=str, required=True, help="검색어 (예: 병역법, 지방재정법)")
    parser.add_argument("--max-results", type=int, default=None, help="최대 수집 개수 (기본: 무제한)")

    # 판례는 일단 주석. 필요 시 다시 활성화
    # parser.add_argument("--type", choices=["law", "precedent"], default="law")
    # parser.add_argument("--no-resume", action="store_true", help="판례 재개 시 1페이지부터")

    args = parser.parse_args()

    logger.info("============================================================")
    logger.info(f"법령 수집 시작: 검색어='{args.query}'")
    logger.info("============================================================")
    print("[DEBUG] main: DataCollector 생성 직전", flush=True)

    collector = DataCollector()
    print("[DEBUG] main: collect_laws 호출 직전", flush=True)
    try:
        collector.collect_laws(
            query=args.query,
            max_results=args.max_results,
        )
    except Exception as e:
        print(f"[DEBUG] main: 예외 발생 -> {e}", flush=True)
        logger.error(f"오류: {e}")
        raise

    print("[DEBUG] main: collect_laws 완료", flush=True)
    logger.info("============================================================")
    logger.info("종료. output/pdfs 폴더를 확인하세요.")
    logger.info("============================================================")


if __name__ == "__main__":
    main()
