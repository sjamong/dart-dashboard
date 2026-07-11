from __future__ import annotations

import base64
import math
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from analysis import build_comparison_df, export_excel_bytes
from dart_client import DartApiError, get_financial_statements, search_company

BASE_DIR = Path(__file__).parent
EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

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


def _excel_data_url(df: pd.DataFrame) -> str:
    """디스크에 파일을 남기지 않고, 브라우저가 직접 내려받는 data URI로 변환한다 (서버리스 배포 대응)."""
    encoded = base64.b64encode(export_excel_bytes(df)).decode("ascii")
    return f"data:{EXCEL_MEDIA_TYPE};base64,{encoded}"


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

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "year": year_int,
            "columns": list(df.columns),
            "rows": _records_with_none(df),
            "download_href": _excel_data_url(df),
            "filename": f"재무제표_비교_{year_int}.xlsx",
            "warnings": fetch_errors,
        },
    )
