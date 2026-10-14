#!/usr/bin/env python3
"""
로컬에 설치된 폰트로부터 교정용 패치 폰트를 '생성'한다. (폰트 파일을 재배포하지
않고, 각자 자기 Mac의 폰트로 만들기 위한 스크립트. Apple SD Gothic Neo 등 독점
폰트의 재배포를 피한다.)

생성물 (출력 폴더 dist-fonts/) — Slack 데스크톱 전용:
  1. Apple SD Gothic Neo DwaetFix ← AppleSDGothicNeo.ttc (Slack 일반 텍스트용)
  2. Consolas (한글 전용)     ← AppleSDGothicNeo.ttc (Slack 코드블록용)
                               ASCII를 빼서 코드 영문은 원래 폰트(Monaco)로 폴백

교정 쌍은 PAIRS에 정의. (잘못, 올바름) — 한 줄 추가로 확장 가능.

사용:  python3 build_fonts.py [출력폴더]
필요:  fonttools  (pip install fonttools)
"""
import os
import sys

from fontTools.ttLib import TTFont, TTCollection

# 잘못된 표기 → 올바른 표기 (각 글자는 완성형 1코드포인트).
# 새 쌍은 여기에 "잘못": "올바름" 한 줄 추가하면 된다.
CHAR_REPLACEMENTS = {
    # 되다 계열
    "됬": "됐", "됀": "된", "됄": "될", "됌": "됨", "됍": "됩",
    # 뵈다·뵙다 계열
    "뵜": "뵀", "봰": "뵌", "봴": "뵐", "봼": "뵘", "봽": "뵙",
    # 했다·겠다 계열
    "헀": "했", "곘": "겠",
    # 겹받침 오류
    "젋": "젊", "읇": "읊", "읆": "읊",
    # 깨 계열
    "꺠": "깨", "꺤": "깬", "꺨": "깰", "꺰": "깸", "꺱": "깹", "꺴": "깼", "꺵": "깽",
    # 때 계열
    "떄": "때", "떈": "땐", "떌": "땔", "떔": "땜", "떕": "땝", "떘": "땠", "떙": "땡",
    # 빼 계열
    "뺴": "빼", "뺵": "빽", "뺸": "뺀", "뺼": "뺄", "뻄": "뺌", "뻅": "뺍", "뻈": "뺐", "뻉": "뺑",
    # 째 계열
    "쨰": "째", "쨴": "짼", "쨸": "쨀", "쩀": "쨈", "쩁": "쨉", "쩄": "쨌", "쩅": "쨍",
    # 께 계열
    "꼐": "께", "꼔": "껜",
    # 떼 계열
    "뗴": "떼", "뗸": "뗀", "뗼": "뗄", "똄": "뗌", "똅": "뗍", "똈": "뗐",
}

# (잘못된 코드포인트, 올바른 코드포인트)
PAIRS = []
for _bad, _good in CHAR_REPLACEMENTS.items():
    assert len(_bad) == 1 and len(_good) == 1, f"단일 글자가 아님: {_bad!r}->{_good!r}"
    PAIRS.append((ord(_bad), ord(_good)))

SYS_APPLE_SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def remap(font):
    """잘못된 코드포인트를 올바른 코드포인트의 글리프로 리맵."""
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
    """ASCII(U+0020~U+007E) cmap 매핑 제거 → 영문은 다음 폰트로 폴백."""
    n = 0
    for t in font["cmap"].tables:
        for cp in range(0x0020, 0x007F):
            if cp in t.cmap:
                del t.cmap[cp]
                n += 1
    return n


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


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "dist-fonts"
    os.makedirs(outdir, exist_ok=True)
    print(f"교정 쌍: " + ", ".join(f"U+{a:04X}->U+{b:04X}" for a, b in PAIRS))
    print(f"출력 폴더: {outdir}\n")

    if not os.path.exists(SYS_APPLE_SD):
        sys.exit(f"[오류] {SYS_APPLE_SD} 없음 — macOS에서 실행해야 합니다.")

    # 1) Slack 일반 텍스트용 (Apple SD Gothic Neo 패치본, 영문 포함)
    build_from_ttc(SYS_APPLE_SD, "Apple SD Gothic Neo DwaetFix",
                   os.path.join(outdir, "AppleSDGothicNeo-DwaetFix.ttc"))
    # 2) Slack 코드블록용 ("Consolas" 한글 전용, ASCII 제거 → 영문은 Monaco로 폴백)
    build_from_ttc(SYS_APPLE_SD, "Consolas",
                   os.path.join(outdir, "Consolas-Korean.ttc"), ascii_strip=True)

    print("\n완료. 설치: dist-fonts/*.ttc 를 ~/Library/Fonts/ 로 복사.")


if __name__ == "__main__":
    main()
