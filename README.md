# ehlt-to-ehot — Slack 한글 오타 교정 (됬→됐 등)

Slack 데스크톱에서 잘못된 한글 표기를 올바르게 보이게 한다.
**앱 수정·재서명·SIP 변경 없음.** 폰트 파일을 재배포하지 않아 저작권 문제도 없다.

> 이름 `ehlt-to-ehot`은 `됬→됐`을 영문 키보드로 친 키스트로크(ehlt→ehot)다.

> 이 문서는 사람과 **AI 에이전트** 모두를 위한 것이다. 에이전트는 아래 명령을 그대로
> 실행하면 되고, `/slackfont` 입력(2단계)만 사용자에게 안내한다(입력창 명령이라 대신 못 침).

교정 대상은 자주 틀리는 한글 음절들(되다/뵈다/했/겠/겹받침/깨·때·빼·째·께·떼 계열 등)이다.
전체 목록과 추가 방법은 `build_fonts.py`의 `CHAR_REPLACEMENTS`를 참고. 예:
- `됬` → `됐`,  `떄` → `때`,  `꺠` → `깨`,  `뺐`…

## 원리
Slack 데스크톱은 Electron(Chromium)이고 본문 텍스트는 CSS `font-family`로 그려진다.
- **일반 텍스트**: Slack 내장 명령 `/slackfont`로 한글 글리프를 리맵한 폰트를 지정 → 교정.
- **코드블록/인라인코드**: 코드 폰트 스택이 `Consolas, Monaco, …`인데 macOS에 Consolas가
  없다. 그래서 "Consolas"라는 이름의 **한글 전용** 패치 폰트를 설치해 가로챈다. 영문은
  글리프가 없어 다음 폰트(Monaco)로 폴백 → 영문 모양은 그대로, 한글만 교정.

> 왜 폰트 방식인가: Slack은 hardened Electron + asar 무결성 fuse로 제3자 코드 주입을 막고
> 원격 디버깅 fuse도 꺼져 있다. 반면 `/slackfont`는 **공식 기능**이라 안전하다. (Chromium
> per-script 폰트 설정은 Electron이 무시하므로 쓰지 않는다.)

## 사전 점검
1. **macOS** 여야 한다 — `/System/Library/Fonts/AppleSDGothicNeo.ttc` 존재 확인.
2. **진짜 Consolas 충돌** 확인 (MS Office 등이 설치했을 수 있음):
   ```
   ls ~/Library/Fonts /Library/Fonts /System/Library/Fonts 2>/dev/null | grep -i consolas
   ```
   결과가 있으면 코드블록 교정이 충돌할 수 있다 → 사용자에게 알리고, 필요 시
   `build_fonts.py`의 "Consolas" 패밀리명을 코드 스택의 다른 항목으로 바꿔 재생성.
   (현재 Slack 코드 스택: `Consolas, Monaco, 'Lucida Console', monospace`)

## 설치
```
./install.sh
```
fonttools 가상환경 준비 → 로컬 `Apple SD Gothic Neo`로 패치 폰트 2종 생성 →
`~/Library/Fonts` 설치 → Consolas 충돌 감지 → 안내 출력. (sudo 불필요.)

수동으로 하려면:
```
python3 -m venv .venv && .venv/bin/pip install fonttools
.venv/bin/python build_fonts.py dist-fonts
cp dist-fonts/*.ttc ~/Library/Fonts/
```

## Slack에 반영 (사용자가 직접)
1. Slack 메시지 입력창에 입력:
   ```
   /slackfont Apple SD Gothic Neo DwaetFix
   ```
   (Slack이 "이 글꼴은 해당 언어를 지원하지 않습니다" 경고를 띄울 수 있으나 무해.)
2. 코드블록/인라인코드는 설치된 `Consolas-Korean` 폰트가 자동 처리(추가 조작 불필요).
3. Slack 완전 종료(**Cmd+Q**) 후 재시작.
4. 확인: 일반 텍스트의 `됬`이 `됐`으로, 코드블록 `됬`도 `됐`으로, 코드 영문은 원래 모양(Monaco).

## 되돌리기
- Slack: 입력창에 `/slackfont` (인자 없이).
- 폰트: `rm ~/Library/Fonts/AppleSDGothicNeo-DwaetFix.ttc ~/Library/Fonts/Consolas-Korean.ttc`

## 생성물 (dist-fonts/)
| 폰트 패밀리 | 용도 | 원본 | 비고 |
|---|---|---|---|
| `Apple SD Gothic Neo DwaetFix` | Slack 일반 텍스트 | AppleSDGothicNeo.ttc | 모양 동일, 오타만 교정 |
| `Consolas` (한글 전용) | Slack 코드블록 | AppleSDGothicNeo.ttc | ASCII 제거→영문은 Monaco |

## 원하는 글자만 선택 (커스텀)
기본은 전체(52개)지만, 원하는 글자/그룹만 골라 생성할 수 있다. 옵션은 `install.sh`가
`build_fonts.py`로 그대로 전달한다.

```
./install.sh --list              # 그룹/글자 목록 보기
./install.sh --only 됬,떄         # 이 글자들만 (쉼표/공백/붙여쓰기: 됬떄 도 가능)
./install.sh --groups 되다,때      # 이 그룹들만
./install.sh --exclude 읆         # 전체에서 이 글자만 빼고
```

그룹: `되다 뵈다 했겠 겹받침 깨 때 빼 째 께 떼`.
(`build_fonts.py`만 단독 실행할 때도 같은 옵션을 쓴다: `python3 build_fonts.py --only 됬`.)

## 교정 쌍 추가/수정
`build_fonts.py`의 `GROUPS`에 `"잘못": "올바름"` 한 줄 추가 후 재설치.
(각 글자는 완성형 1음절이어야 한다.) 재설치 후 Slack을 Cmd+Q로 재시작.

## 한계
- Slack **데스크톱 앱** 전용. 네이티브 알림 토스트(창 밖 배너)는 시스템 폰트라 제외.
- MS Office 등으로 **진짜 Consolas**가 설치돼 있으면 코드블록 교정이 충돌 가능(위 사전 점검).
- `/slackfont`가 재시작 시 풀리면 다시 입력(Slack 버전 의존).

## 구성
```
build_fonts.py   로컬 폰트 → 패치 폰트 2종 생성 (fonttools)
install.sh       생성 + 설치 + 안내
README.md        이 문서 (사람 + 에이전트 공용)
```
