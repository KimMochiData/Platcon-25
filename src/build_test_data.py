#!/usr/bin/env python3
"""
build_test_data.py
  - 원시 EM 레코드(txt) → TEST_DATA(list[dict]) 변환
  - JSON 파일(test_data.json)로도 저장
"""

import re, json, pathlib, argparse
from pprint import pprint

# ---------- 설정 ----------
DEFAULT_TXT = "data/raw/raw_em(DBLP_Scholar_Structured).txt"
OUT_JSON    = "data/processed/test_data.json"

# ---------- 헬퍼 ----------
# ➊ COL … VAL … 사이에서 값만 추출하는 정규식
#    * 다음 COL 이나 줄 끝 직전까지 ☆게으른(match 최소) ☆대소문자 무시
VALUE_RE = re.compile(
    r'COL\s+\w+\s+VAL\s*(.*?)\s*(?=COL\s+\w+\s+VAL|$)',
    re.I | re.S           # 대소문자 무시, 줄바꿈 포함
)

def parse_entity(block: str) -> str:
    """'COL title VAL … COL manufacturer VAL …' 블록 → 값만 공백 연결"""
    values = [v.strip() for v in VALUE_RE.findall(block)]
    return re.sub(r"\s+", " ", " ".join(values)).strip()

def parse_line(line: str):
    """
    한 줄: <엔티티1>\t<엔티티2>\t<label(0/1)>
    → {"entity1": …, "entity2": …, "label": "YES|NO"}
    """
    # 기본은 탭(\t)으로 3등분, 예외적으로 공백 두 개 이상이 구분자로 들어간 줄도 처리
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 3:
        parts = re.split(r"\s{2,}", line.rstrip("\n"))
    if len(parts) != 3:
        raise ValueError(f"잘못된 형식: {line[:80]}…")
    ent1_raw, ent2_raw, lab_raw = parts
    return {
        "entity1": parse_entity(ent1_raw),
        "entity2": parse_entity(ent2_raw),
        "label"  : "YES" if lab_raw.strip() == "1" else "NO"
    }

# ---------- 메인 ----------
def main(txt_path: str, out_json: str):
    with open(txt_path, encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]      # 빈 줄 제거

    test_data = [parse_line(ln) for ln in lines]
    print(f"✔ 변환 완료: {len(test_data)} 개 레코드")

    # 메모리 상 TEST_DATA 변수로 노출
    global TEST_DATA        # pylint: disable=global-variable-not-assigned
    TEST_DATA = test_data   # 다른 모듈에서 import 할 수 있게

    # JSON 저장
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"→ {out_json} 저장 완료")

    # 첫 3개 미리보기
    pprint(test_data[:3], compact=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Raw EM lines → TEST_DATA list(dict) converter")
    ap.add_argument("-i", "--input",  default=DEFAULT_TXT,
                    help=f"원시 텍스트 파일 경로 (default: {DEFAULT_TXT})")
    ap.add_argument("-o", "--output", default=OUT_JSON,
                    help=f"내보낼 JSON 파일 경로 (default: {OUT_JSON})")
    args = ap.parse_args()

    if not pathlib.Path(args.input).is_file():
        raise SystemExit(f"❗ 입력 파일이 없습니다: {args.input}")
    main(args.input, args.output)
