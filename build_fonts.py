#!/usr/bin/env python3
"""
로컬에 설치된 폰트로부터 Slack 교정용 패치 폰트를 '생성'한다.
(폰트 파일을 재배포하지 않고 각자 자기 Mac의 폰트로 만들어 저작권 문제를 피한다.)

생성물 (출력 폴더, 기본 dist-fonts/):
  1. Apple SD Gothic Neo DwaetFix ← AppleSDGothicNeo.ttc (Slack 일반 텍스트용)
  2. Consolas (한글 전용)     ← AppleSDGothicNeo.ttc (Slack 코드블록용, ASCII 제거)

교정 쌍은 GROUPS에 그룹별로 정의. 원하는 글자/그룹만 골라 생성할 수 있다.

사용 예:
  python3 build_fonts.py                 # 전체(기본)
  python3 build_fonts.py --list          # 그룹/글자 목록만 보기
  python3 build_fonts.py --only 됬,떄     # 이 글자들만 (쉼표/공백/붙여쓰기 모두 가능: 됬떄)
  python3 build_fonts.py --groups 되다,때  # 이 그룹들만
  python3 build_fonts.py --exclude 읆     # 전체에서 이 글자만 빼고
  python3 build_fonts.py out-dir --only 됬 # 출력 폴더 지정 + 선택

필요: fonttools  (pip install fonttools)
"""
import argparse
import os
import re
import sys

from fontTools.ttLib import TTFont, TTCollection  # noqa: F401 (TTFont: 확장 여지)

SYS_APPLE_SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# 그룹별 교정 쌍 — "잘못된 표기": "올바른 표기" (각 글자는 완성형 1음절).
# 새 쌍은 알맞은 그룹에 한 줄 추가. 새 그룹이 필요하면 키를 추가.
GROUPS = {
    "되다": {"됬": "됐", "됀": "된", "됄": "될", "됌": "됨", "됍": "됩"},
    "뵈다": {"뵜": "뵀", "봰": "뵌", "봴": "뵐", "봼": "뵘", "봽": "뵙"},
    "했겠": {"헀": "했", "곘": "겠"},
    "겹받침": {"젋": "젊", "읇": "읊", "읆": "읊"},
    "깨": {"꺠": "깨", "꺤": "깬", "꺨": "깰", "꺰": "깸", "꺱": "깹", "꺴": "깼", "꺵": "깽"},
    "때": {"떄": "때", "떈": "땐", "떌": "땔", "떔": "땜", "떕": "땝", "떘": "땠", "떙": "땡"},
    "빼": {"뺴": "빼", "뺵": "빽", "뺸": "뺀", "뺼": "뺄", "뻄": "뺌", "뻅": "뺍", "뻈": "뺐", "뻉": "뺑"},
    "째": {"쨰": "째", "쨴": "짼", "쨸": "쨀", "쩀": "쨈", "쩁": "쨉", "쩄": "쨌", "쩅": "쨍"},
    "께": {"꼐": "께", "꼔": "껜"},
    "떼": {"뗴": "떼", "뗸": "뗀", "뗼": "뗄", "똄": "뗌", "똅": "뗍", "똈": "뗐"},
}

# 전체 (그룹을 평탄화)
CHAR_REPLACEMENTS = {k: v for g in GROUPS.values() for k, v in g.items()}

# main()이 선택 결과로 채운다. (잘못_코드포인트, 올바른_코드포인트)
PAIRS = []


def _split_chars(s):
    """'됬,떄' / '됬 떄' / '됬떄' 모두 글자 리스트로."""
    if not s:
        return []
    out = []
    for tok in re.split(r"[,\s]+", s.strip()):
        out.extend(list(tok))
    return out


def remap(font):
    changed = 0
    for frm, to in PAIRS:
        hit = False
        for t in font["cmap"].tables:
            if to in t.cmap and t.cmap.get(frm) != t.cmap[to]:
                t.cmap[frm] = t.cmap[to]
                hit = True
        changed += hit
    return changed


def strip_ascii(font):
    for t in font["cmap"].tables:
        for cp in range(0x0020, 0x007F):
            t.cmap.pop(cp, None)


def rename(font, family):
    name = font["name"]
    sub = name.getDebugName(2) or "Regular"
    for rec in name.names:
        enc = rec.getEncoding()
        if rec.nameID in (1, 16):
            rec.string = family.encode(enc)
        elif rec.nameID == 4:
            rec.string = (family if sub == "Regular" else f"{family} {sub}").encode(enc)
        elif rec.nameID == 6:
            rec.string = f"{family}-{sub}".replace(" ", "").encode(enc)


def build_from_ttc(src, family, out, ascii_strip=False):
    coll = TTCollection(src)
    for f in coll.fonts:
        remap(f)
        if ascii_strip:
            strip_ascii(f)
        rename(f, family)
    coll.save(out)
    print(f"  [OK] {family}  →  {out}")


def select(args):
    """CLI 옵션으로 적용할 교정 쌍 dict를 고른다."""
    if args.groups:
        chosen = {}
        for name in [n.strip() for n in args.groups.split(",") if n.strip()]:
            if name not in GROUPS:
                sys.exit(f"[오류] 없는 그룹: {name} (사용 가능: {', '.join(GROUPS)})")
            chosen.update(GROUPS[name])
    elif args.only:
        chosen = {}
        for ch in _split_chars(args.only):
            if ch in CHAR_REPLACEMENTS:
                chosen[ch] = CHAR_REPLACEMENTS[ch]
            else:
                print(f"  [무시] 목록에 없는 글자: {ch!r}")
    else:
        chosen = dict(CHAR_REPLACEMENTS)  # 기본: 전체

    for ch in _split_chars(args.exclude):
        chosen.pop(ch, None)

    if not chosen:
        sys.exit("[오류] 선택된 글자가 없습니다.")
    return chosen


def main():
    p = argparse.ArgumentParser(
        description="Slack 교정 패치 폰트 생성 (원하는 글자만 선택 가능)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("out", nargs="?", default="dist-fonts", help="출력 폴더 (기본 dist-fonts)")
    p.add_argument("--only", metavar="글자들", help="이 글자들만 (쉼표/공백/붙여쓰기)")
    p.add_argument("--groups", metavar="그룹들", help="이 그룹들만 (쉼표 구분)")
    p.add_argument("--exclude", metavar="글자들", help="제외할 글자들")
    p.add_argument("--list", action="store_true", help="그룹/글자 목록 출력 후 종료")
    args = p.parse_args()

    if args.list:
        print("사용 가능한 그룹과 글자:")
        for name, d in GROUPS.items():
            pairs = "  ".join(f"{k}→{v}" for k, v in d.items())
            print(f"  [{name}] {pairs}")
        print(f"\n전체 {len(CHAR_REPLACEMENTS)}개. 선택: --only 됬,떄  |  --groups 되다,때")
        return

    if not os.path.exists(SYS_APPLE_SD):
        sys.exit(f"[오류] {SYS_APPLE_SD} 없음 — macOS에서 실행해야 합니다.")

    chosen = select(args)
    global PAIRS
    PAIRS = []
    for bad, good in chosen.items():
        assert len(bad) == 1 and len(good) == 1, f"단일 글자 아님: {bad!r}->{good!r}"
        PAIRS.append((ord(bad), ord(good)))

    os.makedirs(args.out, exist_ok=True)
    print(f"선택된 교정 쌍 {len(PAIRS)}개 → {args.out}\n")
    build_from_ttc(SYS_APPLE_SD, "Apple SD Gothic Neo DwaetFix",
                   os.path.join(args.out, "AppleSDGothicNeo-DwaetFix.ttc"))
    build_from_ttc(SYS_APPLE_SD, "Consolas",
                   os.path.join(args.out, "Consolas-Korean.ttc"), ascii_strip=True)
    print("\n완료. 설치: 출력 폴더의 *.ttc 를 ~/Library/Fonts/ 로 복사.")


if __name__ == "__main__":
    main()
