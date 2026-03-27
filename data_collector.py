"""
법령 수집 모듈 (법령만 담당, 단순 설계)
"""
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
from web_crawler import LawCrawler
from pdf_converter import PDFConverter
from utils import get_logger

logger = get_logger(__name__)


def _log(msg: str) -> None:
    print(f"[DEBUG] {msg}", flush=True)
    sys.stdout.flush()


class DataCollector:
    """법령 검색 → 목록 추출 → 상세 수집 → PDF 저장"""

    def __init__(self, crawler: Optional[LawCrawler] = None):
        _log("DataCollector.__init__ 시작")
        self.crawler = crawler or LawCrawler()
        self.pdf_converter = PDFConverter(font_path="NanumGothic.ttf")
        os.makedirs("output/pdfs", exist_ok=True)
        _log("DataCollector.__init__ 완료")

    def collect_laws(
        self,
        query: str,
        max_results: Optional[int] = None,
        collect_details: bool = True,
    ) -> List[Dict]:
        """
        1) 법령/행정규칙/자치법규 순차적 검색
        2) 목록에서 (ID, 법령명) 추출
        3) 각 항목 상세 페이지에서 본문 수집
        4) PDF로 저장
        """
        print(f"\n[시스템] '{query}' 검색을 시작합니다. (법령 -> 행정규칙 -> 자치법규 순)\n")
        _log(f"collect_laws: query='{query}' max_results={max_results} collect_details={collect_details}")
        results: List[Dict] = []
        collected_ids: set = set()

        try:
            # 섹션 순회: 법령(law) -> 행정규칙(admrul) -> 자치법규(ordin)
            sections = ["law", "admrul", "ordin"]
            
            for current_section in sections:
                if max_results and len(results) >= max_results:
                    break
                
                page = 1
                _log(f"collect_laws: 섹션 '{current_section}' 탐색 시작")
                
                while True:
                    if max_results and len(results) >= max_results:
                        _log("collect_laws: max_results 도달 -> 루프 종료")
                        break

                    section_name = "법령" if current_section == "law" else "행정규칙" if current_section == "admrul" else "자치법규"
                    print(f"  >> [{section_name}] {page}페이지 스캔 중...")
                    
                    response = self.crawler.search_law_page(query=query, page=page, section=current_section)
                    
                    if not response:
                        _log(f"collect_laws: [{current_section}] response 없음 -> 섹션 종료")
                        break

                    items = response.get("items", [])
                    total = response.get("raw_total", 0)

                    if total == 0:
                        _log(f"collect_laws: [{current_section}] raw_total=0 -> 다음 섹션으로")
                        break

                    if not items:
                        _log(f"collect_laws: [{current_section}] items 비어있음 -> page 증가 후 continue")
                        page += 1
                        continue

                    for idx, item in enumerate(items):
                        lid = item.get("ID")
                        name = item.get("법령명", "")
                        
                        if not lid or lid in collected_ids:
                            continue
                        collected_ids.add(lid)

                        if collect_details:
                            print(f"  수집: {name}")
                            detail = self.crawler.get_law_detail(lid)
                            if detail:
                                item["detail"] = detail
                        
                        # 섹션 정보를 법령명 앞에 표시 (구분을 위해)
                        prefix = f"[{section_name}]"
                        item["법령ID"] = lid
                        item["법령명"] = f"{prefix} {name}"
                        results.append(item)

                        if max_results and len(results) >= max_results:
                            break

                    if max_results and len(results) >= max_results:
                        break
                    page += 1

        except KeyboardInterrupt:
            print("\n[!!!] 사용자 중단.")
            _log("collect_laws: KeyboardInterrupt")

        # 저장
        _log(f"collect_laws: 루프 종료 results 수={len(results)}")
        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"output/pdfs/law_{query}_{timestamp}.pdf"
            self.pdf_converter.convert_laws_to_pdf(
                results, filename, title=f"검색 결과 - {query}"
            )
            print(f"\n[완료] {len(results)}건 저장 -> {filename}")
        else:
            print(f"\n[결과] '{query}' 관련 수집된 데이터가 없습니다.")

        return results


# =============================================================================
# 판례 수집 (일단 주석 처리. 나중에 법령 안정화 후 재활성화)
# =============================================================================
#
# def collect_precedents(self, query: str = "", max_results: Optional[int] = None, ...):
#     ...
# def _state_path(self, query: str) -> str: ...
# def _load_state(self, query: str) -> Optional[Dict]: ...
# def _save_state(...): ...
# def _clear_state(self, query: str): ...
# def _save_temp_batch(self, items, query, count): ...
# def _merge_all_pdfs(self, query): ...
# def _cleanup_temp_files(self, query): ...
