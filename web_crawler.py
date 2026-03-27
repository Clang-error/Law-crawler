"""
법령 크롤러 - 처음부터 단순하게.
국가법령정보센터 법령 검색 → 목록 수집 → 상세 본문 수집.
"""
import sys
import time
from urllib.parse import quote
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

def _log(msg: str) -> None:
    print(f"[DEBUG] {msg}", flush=True)
    sys.stdout.flush()

# URL (고정)
BASE = "https://www.law.go.kr/LSW"
# section: law(법령), admrul(행정규칙), ordin(자치법규)
SEARCH_URL = BASE + "/lsSc.do?section={section}&menuId=1&subMenuId=15&tabMenuId=81&eventGubun=060101&query={q}"
DETAIL_URL = BASE + "/lsInfoP.do?lsiSeq={id}"


def _new_driver():
    _log("드라이버 생성 시도 (ChromeDriverManager)...")
    opt = Options()
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1920,1080")
    try:
        path = ChromeDriverManager().install()
        _log(f"드라이버 경로: {path}")
        d = webdriver.Chrome(service=Service(path), options=opt)
        _log("드라이버 생성 완료 (Service 사용)")
        return d
    except Exception as e:
        _log(f"ChromeDriverManager 실패: {e}")
        _log("webdriver.Chrome() 직접 시도...")
        d = webdriver.Chrome(options=opt)
        _log("드라이버 생성 완료 (기본)")
        return d


class LawCrawler:
    def __init__(self):
        _log("LawCrawler.__init__ 시작")
        self.driver = _new_driver()
        _log("LawCrawler.__init__ 완료")

    def __del__(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def search_law_page(self, query: str, page: int = 1, section: str = "law") -> Optional[Dict]:
        """검색 페이지 열고, 목록에서 (ID, 법령명) 추출."""
        q = quote(query, safe="")
        url = SEARCH_URL.format(section=section, q=q)

        _log(f"search_law_page: query='{query}' page={page} section={section}")
        
        # 페이지가 1이면 새로 접속, 아니면 현재 페이지에서 movePage 호출 시도
        if page == 1 or self.driver.current_url == "data:,":
            _log(f"search_law_page: URL 열기 -> {url}")
            self.driver.get(url)
        else:
            _log(f"search_law_page: movePage({page}) 호출 시도")
            # 모든 윈도우/프레임을 훑어서 movePage를 찾고, 없으면 그냥 검색 결과가 끝난 것으로 간주
            found_and_called = self.driver.execute_script(f"""
                function triggerMovePage(win, p) {{
                    try {{
                        if (win.movePage && typeof win.movePage === 'function') {{
                            win.movePage(p);
                            return true;
                        }}
                    }} catch(e) {{}}
                    for (var i = 0; i < win.frames.length; i++) {{
                        if (triggerMovePage(win.frames[i], p)) return true;
                    }}
                    return false;
                }}
                return triggerMovePage(window, '{page}');
            """)
            if not found_and_called:
                _log(f"search_law_page: movePage({page})를 찾을 수 없음 -> 마지막 페이지로 간주")
                return {"items": [], "raw_total": 0}

        self.driver.switch_to.default_content()
        _log("search_law_page: default_content 전환 완료")

        # 결과가 DOM에 들어올 때까지 대기 (최대 15초)
        poll_count = [0]
        def has_law_links(driver):
            poll_count[0] += 1
            try:
                r = driver.execute_script("""
                    function find(win) {
                        try {
                            var doc = win.document;
                            var a = doc.querySelectorAll('a');
                            for (var i = 0; i < a.length; i++) {
                                var h = (a[i].href || '') + (a[i].getAttribute('onclick') || '');
                                if (h.indexOf('lsiSeq') !== -1 || h.indexOf('lsViewWideAll') !== -1) return true;
                            }
                        } catch(e) {}
                        for (var j = 0; j < win.frames.length; j++) {
                            if (find(win.frames[j])) return true;
                        }
                        return false;
                    }
                    return find(window);
                """)
                if poll_count[0] <= 3 or poll_count[0] % 3 == 0:
                    _log(f"search_law_page: has_law_links 폴링 #{poll_count[0]} -> {r}")
                return r is True
            except Exception as ex:
                if poll_count[0] <= 3:
                    _log(f"search_law_page: has_law_links 예외 #{poll_count[0]} -> {ex}")
                return False

        try:
            WebDriverWait(self.driver, 15).until(has_law_links)
            _log("search_law_page: has_law_links 성공 (lsiSeq 링크 발견)")
        except Exception as e:
            _log(f"search_law_page: WebDriverWait 타임아웃/종료 (15초) -> {e}")

        _log("search_law_page: 추가 대기 1초 후 JS 수집 실행")
        time.sleep(1)

        # 전체(문서+모든 프레임)에서 lsiSeq 링크 수집
        rows = self.driver.execute_script("""
            var out = [];
            function scan(doc) {
                if (!doc || !doc.querySelectorAll) return;
                var list = doc.querySelectorAll('a');
                for (var i = 0; i < list.length; i++) {
                    var a = list[i];
                    var h = (a.getAttribute('href') || '') + ' ' + (a.getAttribute('onclick') || '');
                    
                    // lsiSeq를 찾는 다양한 패턴 (href=..., lsViewWideAll('...', ...), etc.)
                    var lid = null;
                    var m = h.match(/lsiSeq[=:](\\d+)/i);
                    if (m) {
                        lid = m[1];
                    } else {
                        // lsViewWideAll('269919', ...) 패턴 대응
                        var m2 = h.match(/lsViewWideAll\\(['"](\\d+)['"]/i);
                        if (m2) lid = m2[1];
                    }
                    
                    if (!lid) continue;
                    
                    var name = (a.textContent || a.innerText || '').trim();
                    // 법령명만 깔끔하게 (시행일 등 뒤의 텍스트 제거 시도)
                    name = name.split('\\n')[0].split('[')[0].trim();
                    
                    if (name.length < 2) continue;
                    
                    var ok = true;
                    for (var j = 0; j < out.length; j++) { if (out[j][0] === lid) { ok = false; break; } }
                    if (ok) out.push([lid, name]);
                }
            }
            scan(document);
            for (var f = 0; f < (window.frames && window.frames.length) || 0; f++) {
                try { scan(window.frames[f].document); } catch(e) {}
            }
            return out;
        """)

        _log(f"search_law_page: JS 수집 반환값 타입={type(rows).__name__} len={len(rows) if isinstance(rows, list) else 'N/A'}")
        if isinstance(rows, list) and rows:
            for i, r in enumerate(rows[:5]):
                _log(f"search_law_page:   [{i}] {r}")
            if len(rows) > 5:
                _log(f"search_law_page:   ... 외 {len(rows)-5}건")

        if not rows or not isinstance(rows, list):
            _log("search_law_page: 수집 결과 없음 -> items=[], raw_total=0 반환")
            return {"items": [], "raw_total": 0}

        items = [{"ID": str(r[0]), "법령명": str(r[1])} for r in rows if len(r) >= 2]
        _log(f"search_law_page: 반환 items 수={len(items)}")
        return {"items": items, "raw_total": len(items)}

    def get_law_detail(self, law_id: str) -> Optional[Dict]:
        """상세 페이지 열고 본문 텍스트 추출."""
        detail_url = DETAIL_URL.format(id=law_id)
        _log(f"get_law_detail: law_id={law_id} URL={detail_url}")
        self.driver.get(detail_url)
        self.driver.switch_to.default_content()
        time.sleep(2)

        text = self.driver.execute_script("""
            function getText(doc) {
                if (!doc) return '';
                var sel = ['#contentBody', '#lawContent', '.textLayer', '.law_content'];
                for (var i = 0; i < sel.length; i++) {
                    var el = doc.querySelector(sel[i]);
                    if (el && el.innerText && el.innerText.trim().length > 50)
                        return el.innerText.trim();
                }
                if (doc.body && doc.body.innerText) return doc.body.innerText.trim();
                return '';
            }
            var t = getText(document);
            if (t) return t;
            for (var f = 0; f < (window.frames && window.frames.length) || 0; f++) {
                try {
                    t = getText(window.frames[f].document);
                    if (t) return t;
                } catch(e) {}
            }
            return '';
        """)

        text_len = len(text) if isinstance(text, str) else 0
        _log(f"get_law_detail: 본문 길이={text_len} (타입={type(text).__name__})")
        if isinstance(text, str) and len(text) > 10:
            _log(f"get_law_detail: 본문 앞 80자 -> {text[:80]}...")
            return {"법령ID": law_id, "본문": text}
        _log("get_law_detail: 본문 없음 또는 짧음 -> 빈 본문 반환")
        return {"법령ID": law_id, "본문": ""}
