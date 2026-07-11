from __future__ import annotations

import io
import json
import os
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

BASE_URL = "https://opendart.fss.or.kr/api"
# 앱 폴더가 아닌 시스템 임시 폴더에 캐싱한다 (서버리스 배포 환경은 앱 폴더가 읽기 전용).
CACHE_FILE = Path(tempfile.gettempdir()) / "dart_corp_code_cache.json"
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
