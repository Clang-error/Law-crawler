# 실행 방법

## 1. 가상환경 켜기 (필수)

```bash
cd /Users/gohyeonseok/law-crawler
source venv/bin/activate
```

프롬프트에 `(venv)` 가 보이면 됩니다.

## 2. 법령 검색 실행

```bash
python main.py --type law --query "병역법"
```

또는

```bash
python main.py --type law --query "지방재정법"
```

## 3. 실행 오류가 날 때
  - 맥: 터미널 앱)을 직접 열고, `cd law-crawler` → `source venv/bin/activate` → `python main.py ...` 로 실행해 보세요. (Cursor/IDE 내장 터미널이 아닌 **시스템 터미널**에서 실행.)
  - 그래도 안 되면: **시스템 설정 > 개인 정보 보호 및 보안 > 전체 디스크 접근 권한에 사용하는 터미널 앱을 추가한 뒤 다시 실행.
  - Chrome을 최신 버전으로 업데이트한 뒤 다시 시도.

- 프록시 오류 ("Tunnel connection failed: 403" 등):
  ```bash
  no_proxy='*' python main.py --type law --query "병역법"
  ```

- ChromeDriver는 이제 프로젝트 폴더 안 `.wdm` 에 저장됩니다. 홈 폴더(`~`) 권한이 없어도 동작하도록 바뀌었습니다.

## 4. 판례 검색

```bash
python main.py --type precedent --query "병역법"
```
