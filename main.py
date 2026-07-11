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
