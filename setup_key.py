from __future__ import annotations

import getpass
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"


def _read_key() -> str:
    try:
        return getpass.getpass("발급받은 OPENDART API 키를 붙여넣고 Enter (입력값은 화면에 보이지 않습니다): ")
    except Exception:
        # 일부 터미널 환경은 getpass를 지원하지 않으므로 일반 입력으로 대체
        return input("발급받은 OPENDART API 키를 붙여넣고 Enter: ")


def main() -> None:
    print("=== OpenDART API 키 설정 ===")
    key = _read_key().strip()
    if not key:
        print("입력한 값이 없어 취소했습니다.")
        return
    ENV_PATH.write_text(f"OPENDART_API_KEY={key}\n", encoding="utf-8-sig")
    print(f"저장 완료: {ENV_PATH}")
    print("이제 'python main.py'로 실행하시면 됩니다.")


if __name__ == "__main__":
    main()
