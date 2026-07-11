# 재무제표 비교 분석기 — PRD

## 1. 개요 / 목적
회사명으로 검색해 최대 3개 기업의 최근 3개년 재무제표(매출액·영업이익·당기순이익·자산/부채/자본총계)를 비교하고, 파생 비율(영업이익률·순이익률·부채비율·ROE)까지 계산해 엑셀 파일로 저장하는 도구. CLI와 웹앱 두 가지 형태를 제공하며, 핵심 로직은 `analysis.py`/`dart_client.py`에 공유되어 있다.

## 2. 요구사항
- 회사명으로 검색한다. 동명 회사가 여러 개 검색되면 선택한다 (CLI: 번호 입력, 웹: 선택 화면).
- 3개 회사 x 3개년(당기/전기/전전기)을 비교한다.
- 항목: 매출액, 영업이익, 당기순이익, 자산총계, 부채총계, 자본총계 (모두 **조원 단위**, 소수점 2자리)
- 각 금액 항목 바로 옆에 **전년 대비 증감률(%)**을 함께 표시한다 (가장 오래된 연도는 비교 대상 연도가 없어 `-`로 표시).
- 파생 비율: 영업이익률(%), 순이익률(%), 부채비율(%), ROE(%)
- 결과를 `.xlsx` 파일로 저장한다 (헤더 굵게, 금액은 소수점 2자리, 비율·증감률은 소수점 2자리, 증감률은 +/- 부호 표시).
- 같은 연도끼리 한눈에 구분되도록 **연도별로 시각적으로 묶어서** 보여준다 (웹: 연도 구분 헤더 행, 엑셀: 연도별 배경색 교대).
- (웹) 회사명 입력 시 자동완성으로 쉽게 검색할 수 있어야 한다.
- (웹) 결과를 브라우저에서 표로 보고, 엑셀로도 다운로드할 수 있어야 한다.

## 3. 데이터 소스
[OpenDART](https://opendart.fss.or.kr) (금융감독원 전자공시시스템 오픈API)
- `corpCode.xml` — 전체 회사 코드/이름 목록 (7일 캐싱)
- `fnlttSinglAcntAll.json` — 단일회사 전체 재무제표. 사업보고서(reprt_code=11011) 기준 1회 호출로 당기·전기·전전기 3개년 금액이 함께 응답되어, 회사당 API 호출 1회로 3개년 데이터를 모두 얻는다.
- 연결재무제표(CFS)가 없는 회사는 자동으로 별도재무제표(OFS)로 재시도한다.

## 4. 파일 구조
| 파일 | 역할 |
|---|---|
| `dart_client.py` | DART API 통신: 회사 검색, 재무제표 조회 |
| `analysis.py` | 공유 비즈니스 로직: 계정 추출, 억원 변환, 비율 계산, 엑셀 저장 (CLI·웹 공용) |
| `main.py` | CLI 진입점: 입력 → 조회 → 엑셀 저장 |
| `webapp.py` | 웹앱(FastAPI) 진입점: 검색·비교·다운로드 라우트 |
| `templates/` | Jinja2 HTML 템플릿 (검색폼/선택화면/결과화면) |
| `static/` | CSS, 자동완성 JS |
| `downloads/` | 웹에서 생성된 엑셀 임시 저장 (30분 후 자동 삭제, git 제외) |
| `requirements.txt` | 의존 패키지 |
| `.env` / `.env.example` | API 키 저장 (`.env`는 git에서 제외, 절대 공유 금지) |
| `.gitignore` | `.env`, 캐시 파일, 결과 엑셀, `downloads/` 등 제외 |
| `Dockerfile` | 웹앱 배포용 컨테이너 이미지 정의 |
| `setup_key.py` | API 키를 화면에 노출하지 않고 `.env`에 저장하는 도우미 스크립트 |

## 5. 사용법 (CLI)
```
cd C:\Users\User\finance_analyzer
pip install -r requirements.txt
python setup_key.py          # 또는 .env.example을 .env로 복사 후 직접 편집
python main.py
```
연도(예: 2024)와 회사명 3개를 순서대로 입력한다. 동명 회사가 여럿이면 번호로 선택한다. 완료되면 `재무제표_비교_YYYYMMDD_HHMMSS.xlsx` 파일이 같은 폴더에 생성된다.

## 6. 사용법 (웹앱)
```
cd C:\Users\User\finance_analyzer
pip install -r requirements.txt
uvicorn webapp:app --host 127.0.0.1 --port 8000
```
브라우저에서 `http://127.0.0.1:8000` 접속 → 연도 + 회사명 3개 입력(입력 중 자동완성 목록에서 선택 가능) → 비교하기 → 결과 표 확인 및 엑셀 다운로드.

동명 회사가 여러 건이고 자동완성에서 선택하지 않은 경우, 선택 화면이 나타나 정확한 회사를 고른 뒤 계속 진행한다.

### 배포 (외부 공개)
- `Dockerfile`로 컨테이너 빌드 후 Render/Railway/Fly.io 등에 배포 가능.
- 배포 환경에는 `.env` 파일 대신 호스팅 플랫폼의 환경변수 설정 화면에서 `OPENDART_API_KEY`를 등록한다 (절대 코드/저장소에 커밋하지 않는다).
- 모든 방문자가 서버에 저장된 하나의 API 키를 공유하므로, 트래픽이 많아지면 OpenDART 일일 호출 한도(기본 20,000회)를 고려해야 한다.
- `downloads/` 파일은 요청 시점에 30분 지난 파일을 자동 정리하지만, 별도의 백그라운드 정리 스케줄러는 없다.

## 7. 향후 고려 사항 (Out of scope, 현재 미구현)
- 유동비율, EPS 등 추가 지표
- 3개 회사 고정이 아닌 임의 개수 비교
- 엑셀 차트 자동 삽입
- 공용 API 키 보호를 위한 요청 빈도 제한(rate limiting)

---

## 8. 전체 소스코드

### `dart_client.py`
```python
from __future__ import annotations

import io
import json
import os
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

BASE_URL = "https://opendart.fss.or.kr/api"
CACHE_FILE = Path(__file__).parent / "corp_code_cache.json"
CACHE_MAX_AGE_SECONDS = 7 * 24 * 3600


class DartApiError(Exception):
    pass


def _get_api_key() -> str:
    key = os.environ.get("OPENDART_API_KEY")
    if not key:
        raise DartApiError(
            "OPENDART_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일에 발급받은 키를 넣어주세요 (.env.example 참고)."
        )
    return key


def _download_corp_codes(api_key: str) -> list[dict]:
    resp = requests.get(f"{BASE_URL}/corpCode.xml", params={"crtfc_key": api_key}, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        xml_bytes = zf.read("CORPCODE.xml")
    root = ET.fromstring(xml_bytes)
    corps = []
    for node in root.iter("list"):
        corps.append(
            {
                "corp_code": (node.findtext("corp_code") or "").strip(),
                "corp_name": (node.findtext("corp_name") or "").strip(),
                "stock_code": (node.findtext("stock_code") or "").strip(),
            }
        )
    return corps


def load_corp_codes(force_refresh: bool = False) -> list[dict]:
    if not force_refresh and CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < CACHE_MAX_AGE_SECONDS:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    api_key = _get_api_key()
    corps = _download_corp_codes(api_key)
    CACHE_FILE.write_text(json.dumps(corps, ensure_ascii=False), encoding="utf-8")
    return corps


def search_company(name: str) -> list[dict]:
    corps = load_corp_codes()
    name = name.strip()
    matches = [c for c in corps if name in c["corp_name"]]
    # 상장사(종목코드 있음) 우선, 이름 가나다순
    matches.sort(key=lambda c: (c["stock_code"] == "", c["corp_name"]))
    return matches


def get_financial_statements(
    corp_code: str,
    year: str,
    reprt_code: str = "11011",
    fs_div: str = "CFS",
) -> list[dict]:
    """단일회사 전체 재무제표 조회. 당기/전기/전전기(최근 3개년) 금액이 한 번에 포함된다."""
    api_key = _get_api_key()
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": reprt_code,
        "fs_div": fs_div,
    }
    resp = requests.get(f"{BASE_URL}/fnlttSinglAcntAll.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    status = data.get("status")
    if status != "000":
        if status == "013" and fs_div == "CFS":
            # 연결재무제표가 없으면 별도재무제표로 재시도
            return get_financial_statements(corp_code, year, reprt_code, fs_div="OFS")
        raise DartApiError(f"{data.get('message')} (status={status}, corp_code={corp_code}, year={year})")
    return data.get("list", [])
```

### `analysis.py`
```python
from __future__ import annotations

from typing import Optional

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

UNIT_DIVISOR = 1_000_000_000_000  # 1조원

# (표시명, 대상 재무제표 구분(sj_div), 후보 계정명들)
METRICS = [
    ("매출액(조원)", ("IS", "CIS"), ("매출액", "수익(매출액)", "영업수익")),
    ("영업이익(조원)", ("IS", "CIS"), ("영업이익", "영업이익(손실)")),
    ("당기순이익(조원)", ("IS", "CIS"), ("당기순이익", "당기순이익(손실)")),
    ("자산총계(조원)", ("BS",), ("자산총계",)),
    ("부채총계(조원)", ("BS",), ("부채총계",)),
    ("자본총계(조원)", ("BS",), ("자본총계",)),
]

YEAR_ROW_FILLS = [
    PatternFill(start_color="FFFFFFFF", end_color="FFFFFFFF", fill_type="solid"),
    PatternFill(start_color="FFF2F5FA", end_color="FFF2F5FA", fill_type="solid"),
]


def to_number(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    text = text.replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def to_jo(text: Optional[str]) -> Optional[float]:
    value = to_number(text)
    if value is None:
        return None
    return round(value / UNIT_DIVISOR, 2)


def extract_metrics(items: list[dict]) -> dict:
    result = {}
    for label, sj_divs, names in METRICS:
        found = None
        # 1차: 정확히 일치하는 계정명
        for item in items:
            if item.get("sj_div") in sj_divs and item.get("account_nm", "").strip() in names:
                found = item
                break
        # 2차: 계정명에 후보 단어가 포함
        if found is None:
            for item in items:
                if item.get("sj_div") in sj_divs and any(n in item.get("account_nm", "") for n in names):
                    found = item
                    break
        result[label] = found
    return result


def build_rows(corp_name: str, year: int, items: list[dict]) -> list[dict]:
    metrics = extract_metrics(items)
    periods = [
        ("thstrm_amount", year),
        ("frmtrm_amount", year - 1),
        ("bfefrmtrm_amount", year - 2),
    ]
    rows = []
    for amount_key, yr in periods:
        row = {"회사명": corp_name, "연도": yr}
        for label, _, _ in METRICS:
            item = metrics[label]
            row[label] = to_jo(item.get(amount_key)) if item else None
        rows.append(row)
    return rows


def add_growth_rates(df: pd.DataFrame) -> pd.DataFrame:
    """회사별로 전년 대비 증감률(%) 컬럼을 각 금액 컬럼 바로 뒤에 추가한다."""
    df = df.sort_values(["회사명", "연도"]).reset_index(drop=True)
    metric_labels = [label for label, _, _ in METRICS]
    growth_col_of = {}
    for label in metric_labels:
        base_name = label.split("(")[0]
        growth_col = f"{base_name} 증감률(%)"
        growth_col_of[label] = growth_col
        df[growth_col] = df.groupby("회사명")[label].pct_change().mul(100).round(2)

    ordered = ["회사명", "연도"]
    for label in metric_labels:
        ordered.append(label)
        ordered.append(growth_col_of[label])
    return df[ordered]


def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df["영업이익률(%)"] = (df["영업이익(조원)"] / df["매출액(조원)"] * 100).round(2)
    df["순이익률(%)"] = (df["당기순이익(조원)"] / df["매출액(조원)"] * 100).round(2)
    df["부채비율(%)"] = (df["부채총계(조원)"] / df["자본총계(조원)"] * 100).round(2)
    df["ROE(%)"] = (df["당기순이익(조원)"] / df["자본총계(조원)"] * 100).round(2)
    return df


def build_comparison_df(companies: list[tuple[str, list[dict]]], year: int) -> pd.DataFrame:
    """companies: [(회사명, get_financial_statements() 결과), ...]"""
    all_rows: list[dict] = []
    for corp_name, items in companies:
        all_rows.extend(build_rows(corp_name, year, items))
    df = pd.DataFrame(all_rows)
    df = add_growth_rates(df)
    df = add_ratios(df)
    df = df.sort_values(["연도", "회사명"], ascending=[False, True]).reset_index(drop=True)
    return df


def export_excel(df: pd.DataFrame, path: str) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="재무비교", index=False)
        ws = writer.sheets["재무비교"]
        columns = list(df.columns)

        for col_idx, col_name in enumerate(columns, 1):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(12, len(col_name) + 4)

        prev_year = None
        fill_idx = -1
        for i, row in enumerate(df.itertuples(index=False)):
            row_idx = i + 2
            year_value = getattr(row, "연도")
            if year_value != prev_year:
                fill_idx = (fill_idx + 1) % 2
                prev_year = year_value
            for col_idx, col_name in enumerate(columns, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.fill = YEAR_ROW_FILLS[fill_idx]
                if "증감률" in col_name:
                    cell.number_format = "+0.00;-0.00;0.00"
                elif col_name.endswith("(%)"):
                    cell.number_format = "0.00"
                elif col_name not in ("회사명", "연도"):
                    cell.number_format = "#,##0.00"

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
```

### `main.py` (CLI)
```python
from __future__ import annotations

from datetime import datetime

from analysis import build_comparison_df, export_excel
from dart_client import DartApiError, get_financial_statements, search_company


def pick_company(name: str) -> dict:
    matches = search_company(name)
    if not matches:
        raise SystemExit(f"'{name}'에 해당하는 회사를 찾을 수 없습니다.")
    if len(matches) == 1:
        return matches[0]

    print(f"\n'{name}' 검색 결과가 여러 건입니다. 번호를 선택하세요:")
    shown = matches[:15]
    for i, m in enumerate(shown, 1):
        tag = "상장" if m["stock_code"] else "비상장"
        print(f"  {i}. {m['corp_name']} ({tag})")
    while True:
        choice = input("번호 입력: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(shown):
            return shown[int(choice) - 1]
        print("올바른 번호를 입력하세요.")


def main() -> None:
    print("=== 회사 재무제표 비교 분석기 (DART 오픈API 기반) ===")
    year_input = input("기준 연도(사업보고서 기준, 예: 2024): ").strip()
    try:
        year = int(year_input)
    except ValueError:
        raise SystemExit("연도는 숫자로 입력해주세요.")

    company_names = []
    for i in range(1, 4):
        name = input(f"비교할 회사 {i} 이름: ").strip()
        if not name:
            raise SystemExit("회사명을 입력해주세요.")
        company_names.append(name)

    companies: list[tuple[str, list[dict]]] = []
    for name in company_names:
        try:
            corp = pick_company(name)
        except DartApiError as e:
            print(f"   [오류] {e}")
            continue
        print(f"-> {corp['corp_name']} ({corp['corp_code']}) 재무제표 조회 중...")
        try:
            items = get_financial_statements(corp["corp_code"], str(year))
        except DartApiError as e:
            print(f"   [오류] {e}")
            continue
        companies.append((corp["corp_name"], items))

    if not companies:
        raise SystemExit("가져온 재무 데이터가 없습니다.")

    df = build_comparison_df(companies, year)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"재무제표_비교_{timestamp}.xlsx"
    export_excel(df, out_path)
    print(f"\n완료! 저장된 파일: {out_path}")


if __name__ == "__main__":
    main()
```

### `webapp.py`
```python
from __future__ import annotations

import math
import re
import time
import uuid
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from analysis import build_comparison_df, export_excel
from dart_client import DartApiError, get_financial_statements, search_company

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)
DOWNLOAD_MAX_AGE_SECONDS = 30 * 60
SAFE_FILENAME = re.compile(r"^[\w\-]+\.xlsx$", re.UNICODE)

app = FastAPI(title="재무제표 비교 분석기")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _records_with_none(df: pd.DataFrame) -> list[dict]:
    records = df.to_dict(orient="records")
    for row in records:
        for key, value in row.items():
            if isinstance(value, float) and math.isnan(value):
                row[key] = None
    return records


def _cleanup_downloads() -> None:
    now = time.time()
    for f in DOWNLOAD_DIR.glob("*.xlsx"):
        try:
            if now - f.stat().st_mtime > DOWNLOAD_MAX_AGE_SECONDS:
                f.unlink()
        except OSError:
            pass


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"year": "", "names": ["", "", ""], "errors": []},
    )


@app.get("/api/search")
def api_search(q: str = ""):
    q = q.strip()
    if len(q) < 2:
        return []
    try:
        matches = search_company(q)
    except DartApiError:
        return []
    return [
        {"corp_name": m["corp_name"], "corp_code": m["corp_code"], "stock_code": m["stock_code"]}
        for m in matches[:10]
    ]


@app.post("/compare", response_class=HTMLResponse)
def compare(
    request: Request,
    year: str = Form(...),
    name1: str = Form(""),
    name2: str = Form(""),
    name3: str = Form(""),
    code1: str = Form(""),
    code2: str = Form(""),
    code3: str = Form(""),
    corpname1: str = Form(""),
    corpname2: str = Form(""),
    corpname3: str = Form(""),
):
    names = [name1, name2, name3]
    codes = [code1, code2, code3]
    corpnames = [corpname1, corpname2, corpname3]

    if not year.strip().isdigit():
        return templates.TemplateResponse(
            request,
            "index.html",
            {"year": year, "names": names, "errors": ["연도는 숫자로 입력해주세요."]},
        )
    year_int = int(year.strip())

    errors: list[str] = []
    slots = []
    for i in range(3):
        idx = i + 1
        name = names[i].strip()
        code = codes[i].strip()
        if not name and not code:
            errors.append(f"회사 {idx} 이름을 입력해주세요.")
            continue
        if code:
            slots.append({"status": "resolved", "idx": idx, "code": code, "name": corpnames[i] or name})
            continue
        try:
            matches = search_company(name)
        except DartApiError as e:
            errors.append(f"회사 {idx}('{name}') 검색 오류: {e}")
            continue
        if not matches:
            errors.append(f"'{name}'에 해당하는 회사를 찾을 수 없습니다.")
            continue
        if len(matches) == 1:
            m = matches[0]
            slots.append({"status": "resolved", "idx": idx, "code": m["corp_code"], "name": m["corp_name"]})
        else:
            slots.append(
                {
                    "status": "pending",
                    "idx": idx,
                    "name": name,
                    "matches": [
                        {
                            "corp_code": m["corp_code"],
                            "corp_name": m["corp_name"],
                            "stock_code": m["stock_code"],
                        }
                        for m in matches[:15]
                    ],
                }
            )

    if errors:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"year": year, "names": names, "errors": errors},
        )

    if any(s["status"] == "pending" for s in slots):
        return templates.TemplateResponse(
            request,
            "select.html",
            {"year": year_int, "slots": slots},
        )

    companies: list[tuple[str, list[dict]]] = []
    fetch_errors: list[str] = []
    for s in slots:
        try:
            items = get_financial_statements(s["code"], str(year_int))
        except DartApiError as e:
            fetch_errors.append(f"{s['name']}: {e}")
            continue
        companies.append((s["name"], items))

    if not companies:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "year": year,
                "names": names,
                "errors": fetch_errors or ["가져온 재무 데이터가 없습니다."],
            },
        )

    df = build_comparison_df(companies, year_int)

    _cleanup_downloads()
    filename = f"재무제표_비교_{year_int}_{uuid.uuid4().hex[:8]}.xlsx"
    export_excel(df, str(DOWNLOAD_DIR / filename))

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "year": year_int,
            "columns": list(df.columns),
            "rows": _records_with_none(df),
            "filename": filename,
            "warnings": fetch_errors,
        },
    )


@app.get("/download/{filename}")
def download(filename: str):
    if not SAFE_FILENAME.match(filename):
        return HTMLResponse("잘못된 파일명입니다.", status_code=400)
    path = DOWNLOAD_DIR / filename
    if not path.exists():
        return HTMLResponse("파일을 찾을 수 없습니다. (30분 후 자동 삭제됩니다)", status_code=404)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )
```

### `templates/base.html`
```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{% block title %}재무제표 비교 분석기{% endblock %}</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="container">
  <header>
    <h1><a href="/">재무제표 비교 분석기</a></h1>
    <p class="subtitle">회사명으로 검색해 최대 3개 기업의 최근 3개년 재무제표를 비교합니다 (OpenDART 기반)</p>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
  <footer>
    <p>데이터 출처: <a href="https://opendart.fss.or.kr" target="_blank" rel="noopener">OpenDART</a></p>
  </footer>
</div>
</body>
</html>
```

### `templates/index.html`
```html
{% extends "base.html" %}
{% block content %}
{% if errors %}
<div class="alert">
  <ul>
  {% for e in errors %}<li>{{ e }}</li>{% endfor %}
  </ul>
</div>
{% endif %}
<form method="post" action="/compare" class="search-form">
  <label>
    기준 연도 (사업보고서 기준)
    <input type="number" name="year" value="{{ year }}" placeholder="예: 2024" required>
  </label>

  {% for i in range(1, 4) %}
  <div class="company-field" data-idx="{{ i }}">
    <label>비교할 회사 {{ i }}</label>
    <input type="text" class="company-input" name="name{{ i }}" value="{{ names[i-1] }}" autocomplete="off" placeholder="회사명 입력 (예: 삼성전자)" required>
    <input type="hidden" class="company-code" name="code{{ i }}" value="">
    <input type="hidden" class="company-corpname" name="corpname{{ i }}" value="">
    <ul class="suggestions"></ul>
  </div>
  {% endfor %}

  <button type="submit">비교하기</button>
</form>
<script src="/static/app.js"></script>
{% endblock %}
```

### `templates/select.html`
```html
{% extends "base.html" %}
{% block content %}
<p>이름이 같은 회사가 여러 건 검색됐습니다. 각 항목에서 정확한 회사를 선택해주세요.</p>
<form method="post" action="/compare">
  <input type="hidden" name="year" value="{{ year }}">
  {% for s in slots %}
    {% if s.status == "resolved" %}
      <input type="hidden" name="name{{ s.idx }}" value="{{ s.name }}">
      <input type="hidden" name="code{{ s.idx }}" value="{{ s.code }}">
      <input type="hidden" name="corpname{{ s.idx }}" value="{{ s.name }}">
      <p class="resolved">회사 {{ s.idx }}: <strong>{{ s.name }}</strong> (확인됨)</p>
    {% else %}
      <fieldset>
        <legend>회사 {{ s.idx }} — '{{ s.name }}' 검색 결과</legend>
        <input type="hidden" name="name{{ s.idx }}" value="{{ s.name }}">
        {% for m in s.matches %}
        <label class="radio-option">
          <input type="radio" name="code{{ s.idx }}" value="{{ m.corp_code }}" data-name="{{ m.corp_name }}" required>
          {{ m.corp_name }}
          {% if m.stock_code %}<span class="tag">상장 {{ m.stock_code }}</span>{% else %}<span class="tag muted">비상장</span>{% endif %}
        </label>
        {% endfor %}
        <input type="hidden" class="corpname-hidden" name="corpname{{ s.idx }}" value="">
      </fieldset>
    {% endif %}
  {% endfor %}
  <button type="submit">선택 완료</button>
</form>
<script>
document.querySelectorAll("fieldset").forEach(function (fs) {
  var hidden = fs.querySelector(".corpname-hidden");
  fs.querySelectorAll("input[type=radio]").forEach(function (radio) {
    radio.addEventListener("change", function () {
      hidden.value = radio.dataset.name;
    });
  });
});
</script>
{% endblock %}
```

### `templates/result.html`
```html
{% extends "base.html" %}
{% block content %}
{% if warnings %}
<div class="alert">
  <ul>{% for w in warnings %}<li>{{ w }}</li>{% endfor %}</ul>
</div>
{% endif %}
<div class="result-actions">
  <a class="button" href="/download/{{ filename }}">엑셀 다운로드</a>
  <a class="button secondary" href="/">다시 검색</a>
</div>
<div class="table-wrap">
<table>
  <thead>
    <tr>{% for c in columns %}<th>{{ c }}</th>{% endfor %}</tr>
  </thead>
  <tbody>
    {% set ns = namespace(prev_year=None) %}
    {% for row in rows %}
      {% if row['연도'] != ns.prev_year %}
      <tr class="year-header"><td colspan="{{ columns|length }}">{{ row['연도'] }}년</td></tr>
      {% set ns.prev_year = row['연도'] %}
      {% endif %}
    <tr>
      {% for c in columns %}
      <td>
        {% set v = row[c] %}
        {% if v is none %}-
        {% elif c in ("회사명", "연도") %}{{ v }}
        {% elif "증감률" in c %}{{ "%+.2f"|format(v) }}
        {% elif c.endswith("(%)") %}{{ "%.2f"|format(v) }}
        {% else %}{{ "%.2f"|format(v) }}
        {% endif %}
      </td>
      {% endfor %}
    </tr>
    {% endfor %}
  </tbody>
</table>
</div>
{% endblock %}
```

### `static/style.css`
```css
:root {
  color-scheme: light dark;
  --bg: #f7f7f8;
  --fg: #1a1a1a;
  --card-bg: #ffffff;
  --border: #e2e2e2;
  --accent: #2563eb;
  --accent-fg: #ffffff;
  --muted: #6b7280;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14161a;
    --fg: #e6e6e6;
    --card-bg: #1d2025;
    --border: #2c2f36;
    --accent: #3b82f6;
    --accent-fg: #0b0e14;
    --muted: #9aa0aa;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Malgun Gothic", sans-serif;
  background: var(--bg);
  color: var(--fg);
}
.container { max-width: 900px; margin: 0 auto; padding: 24px 16px 64px; }
header h1 { font-size: 1.5rem; margin-bottom: 4px; }
header h1 a { color: var(--fg); text-decoration: none; }
.subtitle { color: var(--muted); margin-top: 0; font-size: 0.9rem; }

.search-form, form { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-top: 16px; }
.search-form label, form > label { display: block; font-weight: 600; margin-bottom: 6px; margin-top: 16px; }
.company-field { position: relative; margin-top: 16px; }
input[type=text], input[type=number] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--fg);
  font-size: 1rem;
}
.suggestions {
  list-style: none;
  margin: 4px 0 0;
  padding: 0;
  position: absolute;
  z-index: 10;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  width: 100%;
  max-height: 220px;
  overflow-y: auto;
}
.suggestions li { padding: 8px 12px; cursor: pointer; }
.suggestions li:hover { background: var(--bg); }

button, .button {
  display: inline-block;
  background: var(--accent);
  color: var(--accent-fg);
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-size: 1rem;
  cursor: pointer;
  text-decoration: none;
  margin-top: 20px;
}
.button.secondary { background: transparent; color: var(--fg); border: 1px solid var(--border); }

fieldset { border: 1px solid var(--border); border-radius: 8px; margin-top: 16px; padding: 12px; }
.radio-option { display: block; padding: 6px 0; }
.tag { font-size: 0.8rem; color: var(--muted); margin-left: 6px; }
.resolved { color: var(--muted); }

.alert { background: #fee2e2; color: #991b1b; border-radius: 8px; padding: 12px 16px; margin-top: 16px; }
@media (prefers-color-scheme: dark) {
  .alert { background: #3f1d1d; color: #fca5a5; }
}

.result-actions { margin: 16px 0; display: flex; gap: 12px; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; background: var(--card-bg); border-radius: 8px; overflow: hidden; }
th, td { border: 1px solid var(--border); padding: 8px 10px; text-align: right; white-space: nowrap; }
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) { text-align: left; }
th { background: var(--bg); position: sticky; top: 0; }
tr.year-header td {
  background: var(--accent);
  color: var(--accent-fg);
  font-weight: 700;
  text-align: left;
  padding: 10px 12px;
  border-top: 2px solid var(--accent);
}

footer { margin-top: 40px; color: var(--muted); font-size: 0.85rem; }
footer a { color: var(--muted); }
```

### `static/app.js`
```javascript
document.querySelectorAll(".company-field").forEach(function (field) {
  var input = field.querySelector(".company-input");
  var hiddenCode = field.querySelector(".company-code");
  var hiddenCorpname = field.querySelector(".company-corpname");
  var list = field.querySelector(".suggestions");
  var debounceTimer;

  input.addEventListener("input", function () {
    hiddenCode.value = "";
    hiddenCorpname.value = "";
    var q = input.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 2) {
      list.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(function () {
      fetch("/api/search?q=" + encodeURIComponent(q))
        .then(function (res) { return res.json(); })
        .then(function (items) {
          list.innerHTML = "";
          items.forEach(function (item) {
            var li = document.createElement("li");
            li.textContent = item.stock_code
              ? item.corp_name + " (상장 " + item.stock_code + ")"
              : item.corp_name + " (비상장)";
            li.addEventListener("click", function () {
              input.value = item.corp_name;
              hiddenCode.value = item.corp_code;
              hiddenCorpname.value = item.corp_name;
              list.innerHTML = "";
            });
            list.appendChild(li);
          });
        })
        .catch(function () { list.innerHTML = ""; });
    }, 250);
  });

  document.addEventListener("click", function (e) {
    if (!field.contains(e.target)) {
      list.innerHTML = "";
    }
  });
});
```

### `requirements.txt`
```
requests
pandas
openpyxl
python-dotenv
fastapi
uvicorn[standard]
jinja2
python-multipart
```

### `.env.example`
```
OPENDART_API_KEY=여기에_본인의_API_키를_붙여넣으세요
```

### `.gitignore`
```
.env
corp_code_cache.json
*.xlsx
__pycache__/
downloads/
```

### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn webapp:app --host 0.0.0.0 --port ${PORT}"]
```
