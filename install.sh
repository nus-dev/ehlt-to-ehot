#!/bin/bash
# 됬→됐 / 떄→때 교정 설치 스크립트 (macOS, Slack 데스크톱 전용)
# 로컬 폰트로 패치 폰트를 생성→설치하고, Slack 반영 방법을 안내한다.
# 폰트 파일을 재배포하지 않으므로(각자 로컬 생성) 저작권 문제가 없다.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FONTDIR="$HOME/Library/Fonts"
OUT="$HERE/dist-fonts"

echo "══ 됬→됐 교정 설치 ══"

# 1) fonttools 준비 (프로젝트 venv)
if [ ! -x "$HERE/.venv/bin/python" ]; then
  echo "• fonttools 설치(가상환경)"
  python3 -m venv "$HERE/.venv"
  "$HERE/.venv/bin/pip" -q install fonttools >/dev/null
fi
PY="$HERE/.venv/bin/python"

# 2) 로컬 폰트로 패치 폰트 생성 (추가 옵션은 build_fonts.py로 그대로 전달)
#    예: ./install.sh --only 됬,떄   |   ./install.sh --groups 되다,때
echo "• 패치 폰트 생성(로컬 시스템 폰트 기반)"
"$PY" "$HERE/build_fonts.py" "$OUT" "$@"

# 3) Consolas 충돌 감지 (MS Office 등으로 진짜 Consolas가 있으면 코드블록 트릭 영향)
REAL_CONSOLAS=""
for d in "$HOME/Library/Fonts" "/Library/Fonts" "/System/Library/Fonts"; do
  ls "$d"/[Cc]onsola*.ttf "$d"/[Cc]onsola*.ttc >/dev/null 2>&1 && REAL_CONSOLAS="$d"
done

# 4) 설치
echo "• ~/Library/Fonts 로 설치"
mkdir -p "$FONTDIR"
cp "$OUT"/*.ttc "$FONTDIR"/ 2>/dev/null || true
ls "$FONTDIR" | grep -iE "DwaetFix|Consolas-Korean" || true

cat <<'GUIDE'

══ Slack 반영 방법 (앱 수정·재서명 없음) ══

1) Slack 메시지 입력창에 입력(Slack 내장 명령):
       /slackfont Apple SD Gothic Neo DwaetFix
   → 일반 텍스트의 됬/떄 교정. (Slack 경고 문구는 무해.)

2) 코드블록/인라인코드는 "Consolas-Korean" 폰트가 자동 처리
   (한글만 교정, 영문은 Monaco 그대로 유지 — 추가 조작 불필요).

3) 적용하려면 Slack 완전 종료(Cmd+Q) 후 재시작.
   되돌리기: /slackfont  (인자 없이 입력)
GUIDE

if [ -n "$REAL_CONSOLAS" ]; then
  echo "⚠️  진짜 Consolas 폰트가 발견됨($REAL_CONSOLAS)."
  echo "    MS Office 등이 설치한 Consolas와 충돌해 코드블록 한글 교정이 안 될 수 있습니다."
  echo "    코드블록까지 필요하면 Slack 코드 폰트 스택(Consolas,Monaco,...)의 다른 이름으로"
  echo "    build_fonts.py의 Consolas 생성 패밀리명을 바꿔 재설치하세요."
fi
echo "✔ 완료."
