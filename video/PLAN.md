# PLAN: Claude Code 30초 3부작

공통 규칙
- 무대: 1920×1080 `#stage`, 공용 `examples/claude-code/stage.js` + `stage.css`, 한국어 카드는 `video/ko.css` (Noto Sans KR).
- 주인공 물체(hero object, 영화 내내 이동하는 하나의 요소): 강조색 점 하나. 터미널의 프롬프트 표시에서 출발해, 마지막 문장 "만들었습니다"의 마침표로 착지하고 그 프레임에 마지막 타격음.
- 고정 틀(persistent frame): 어두운 터미널 카드. 내용만 바뀌고 틀은 그대로.
- 터미널 줄은 모두 이 세션의 실제 출력. `[실행 후]`는 파이프라인을 돌린 뒤 실제 값으로 채운다 (표시 글자만 바뀌고 큐 시각은 그대로라 음악은 변하지 않음).
- 끝 카드(무음): "비공식 샘플 · reference-motion-video 스킬로 만들었습니다. / Claude Code는 Anthropic이 만듭니다. 이 영상은 Anthropic과 관계없으며 보증받지 않았습니다."
- 줄인 시간은 화면에 표기: 터미널 장면 오른쪽 위 "▶▶ 압축 · 실제 순서 그대로".

## 1. `launch`: 런칭 필름, `drums_launch`, 100 BPM (박 0.6 s, 마디 2.4 s), 강조색 #4C6FFF

| 시간 | 마디 | 장면 | 화면 글자 | 증거 (실제 출력) | 구간 | 큐 |
|---|---|---|---|---|---|---|
| 0.0-2.4 | 0 | 터미널, 요청이 타이핑됨 | (프롬프트) | 사용자 요청 원문 첫 문장 | intro | key×글자, dot |
| 2.4-4.8 | 1 | 밝은 카드 | Claude Code에게 / 말 한 줄. | | build + riser, 4.2부터 breath | cut big, word×4, dot |
| 4.8-7.2 | 2 | 카드 | **영상 한 편.** | | groove e1.0 | **drop** |
| 7.2-9.6 | 3 | 터미널 조각 | 스킬을 읽고 | `cat SKILL.md` 첫 줄, 셋업 점검 4줄 | light | cut, word, chip, pop |
| 9.6-12.0 | 4 | 어둡게 멈춤 | 정할 수 없는 건, 묻고 | `AskUserQuestion` 답 3개 | **stop** (11.4-12.0 fill) | break, chip, pop |
| 12.0-14.4 | 5 | 터미널 조각 | 테스트부터 돌리고 | `31 passed in 81.30s` | groove e1.0 | reentry, chip, count |
| 14.4-16.8 | 6 | 터미널 조각 | 화면에 맞춰 작곡하고 | `compose.py` 결과 `[실행 후]` | groove | cut, chip, num |
| 16.8-19.2 | 7 | 터미널 조각 | 한 프레임씩 렌더하고 | `render.mjs` 결과 `[실행 후]` | groove | cut, chip, num |
| 19.2-21.6 | 8 | 큰 숫자 | 직접 검사한다. **N / N** | `synccheck.py` 결과 `[실행 후]` | groove e1.1 | cut big, num |
| 21.6-24.0 | 9 | 몽타주 | 장르 셋, 음악 셋. | 세 편의 실제 스틸 3장 | groove e1.1 | cut, pop×3 |
| 24.0-26.4 | 10 | 카드 | 이 영상도, | | build + riser, 25.8부터 breath | word×2 |
| 26.4-27.6 | 11 | 이름 카드 | **Claude Code가 만들었습니다.** (점이 마침표로 착지) | | (final 꼬리 1.2 s) | **final** |
| 27.6-30.0 | | 끝 카드 | 비공식 표기 | | end (무음) | |

## 2. `explainer`: 개념 설명, `soft_pulse`, 96 BPM (박 0.625 s, 마디 2.5 s), 강조색 #0FA38A

뼈대는 기존 30초 explainer 샘플과 같고 (훅 → 4단계 고리 → 멈춤 → 재진입 → 이름), 내용만 새로.

| 시간 | 마디 | 장면 | 화면 글자 | 증거 | 구간 | 큐 |
|---|---|---|---|---|---|---|
| 0.0-4.4 | 0-1 | 질문 카드 | 이 영상의 음악은 / **어떻게 화면에 맞췄을까?** | | intro | word×6 |
| 4.4-5.0 | 1 | 같은 카드 | | | breath | |
| 5.0-7.5 | 2 | 4칸 고리 + 조각 | Claude Code가 네 단계로. · ① 화면 | 이 영상의 `const T = {...}` 코드 | groove e0.5 | **drop**, node, chip, pop |
| 7.5-10.0 | 3 | 〃 | ② 큐 | `cues.mjs` 출력 일부와 큐 개수 `[실행 후]` | groove e0.65 | node, chip, pop |
| 10.0-12.5 | 4 | 〃 | ③ 작곡 | `compose.py` 결과 `[실행 후]` | groove e0.8 | node, chip, pop |
| 12.5-15.0 | 5 | 〃 | ④ 검사 | `synccheck.py` 결과 `[실행 후]` | groove e0.95 | node, chip, pop |
| 15.0-18.75 | 6-7 | 어둡게 멈춤 | 통과해도, 고르는 건 사람. | `SKILL.md` 규칙 5 원문 ("Machine gates are necessary, not sufficient...") | **stop** | break, chip, num |
| 18.75-20.0 | 7 | 〃 | | | build (fill) | |
| 20.0-25.0 | 8-9 | 고리, 점이 박마다 한 칸씩 | 듣고 고르면, 끝. | | groove e1.0 | reentry, pop |
| 25.0-27.5 | 10 | 이름 카드 | **Claude Code** / 이 영상도 이렇게 만들었습니다. | | | **final** |
| 27.5-30.0 | 11 | 끝 카드 | 비공식 표기 | | end | |

## 3. `demo`: 데모 워크스루, `bright_demo`, 100 BPM, 강조색 #7C5CFF

결과부터 보여주고, 이 세션에서 실제로 한 작업을 순서대로. 숫자는 세션 기록(`~/.claude/projects/.../<session>.jsonl`)에서 센 값.

| 시간 | 마디 | 장면 | 화면 글자 | 증거 | 구간 | 큐 |
|---|---|---|---|---|---|---|
| 0.0-2.4 | 0 | 결과부터 | 30초 영상 세 편. | 세 편의 실제 스틸 3장 | intro | pop×3, dot |
| 2.4-4.8 | 1 | 터미널 (고정 틀) | 시작은 말 한 줄. | 요청 원문 타이핑, 실제 시각 21:04 | tease | cut big, key×글자 |
| 4.8-7.2 | 2 | 터미널 | 읽고 | `Bash(cat SKILL.md README.md)`, 셋업 점검 | light | chip, pop |
| 7.2-9.6 | 3 | 터미널 | 묻고 | `AskUserQuestion` 답 3개 | light | chip, pop |
| 9.6-12.0 | 4 | 터미널 | 계획하고 | `31 passed in 81.30s`, `Write(video/BRIEF.md)`, `Write(video/PLAN.md)` | light | chip, count |
| 12.0-14.4 | 5 | 터미널 | 만들고 | `Write(video/demo/index.html)`, `cues.mjs`, `compose.py` | build + riser, 13.8부터 breath | chip |
| 14.4-16.8 | 6 | 터미널 | **음악까지 맞추고.** | compose 결과 `"miss": 0` `[실행 후]` | groove e1.0 | **drop** |
| 16.8-19.2 | 7 | 터미널 | 직접 검사한다. | render, synccheck 결과 `[실행 후]` | groove | chip, num |
| 19.2-21.6 | 8 | 큰 숫자 | 사람이 보낸 메시지 **N개** | 세션 기록 `[실행 후]` | groove e1.1 | cut, num |
| 21.6-24.0 | 9 | 큰 숫자 | Claude Code의 도구 호출 **M번** | 세션 기록 `[실행 후]` | groove e1.1 | cut, count |
| 24.0-26.4 | 10 | 큰 숫자 | 요청부터 이 렌더까지 **K분** (사람 답 기다린 시간 포함) | 세션 기록 시각 `[실행 후]` | groove e1.1 | cut, num |
| 26.4-27.6 | 11 | 이름 카드 | **Claude Code** / 이 영상도 Claude Code가 만들었습니다. | | | **final** |
| 27.6-30.0 | | 끝 카드 | 비공식 표기 | | end | |

## 만드는 순서와 확인

1. `video/ko.css` + 세 편의 `index.html` 작성 → 확인: 구간 경계마다 스틸(`stills.mjs`)을 보고 겹침·잘림 없음
2. 각 편 `cues.mjs` → `compose.py` → `render.mjs` → `synccheck.py` → 확인: 길이 30.0 s, 큐 전부 33 ms 안
3. `[실행 후]` 자리를 실제 값으로 채우고 다시 렌더 → 확인: `cues.json`이 1회차와 같음 (음악 불변), synccheck 같은 결과
4. 세 편 스틸로 launch 몽타주와 demo 첫 장면 채우기
5. 마지막 확인: 음량 -14 LUFS ±0.5, true peak ≤ -1 dBTP, 4초 간격 확인 장면(contact sheet)
6. 선택: 원하면 launch를 다른 두 팔레트로도 뽑아 블라인드로 들어보고 고르기 (기본은 장르별 팔레트)
