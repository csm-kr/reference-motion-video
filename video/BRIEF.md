# BRIEF: Claude Code 30초 3부작 (비공식)

## 1. 목적
- 무엇: Claude Code에 대한 30초 영상 3편, 장르마다 한 편.
  1. `launch`: 런칭 필름 (genre A, 팔레트 `drums_launch`, 100 BPM)
  2. `explainer`: 개념 설명 (genre C, 팔레트 `soft_pulse`, 96 BPM)
  3. `demo`: 데모 워크스루 (genre D, 팔레트 `bright_demo`, 100 BPM)
- 누가 보나: Claude Code를 들어봤지만 아직 안 써본 한국어 사용 개발자 [가정]
- 어디에: YouTube·SNS 공유용, 16:9 [가정]. 마감과 심사 기준 없음 [가정]
- 본 뒤 할 일: "말 한 줄로 이런 걸 맡길 수 있구나" 하고 써보고 싶어진다.

## 2. 메시지와 증거
- 한 문장: **"이 영상도 Claude Code가 만들었습니다."**
- 세 편의 각도:
  - `launch`: 약속. 말 한 줄이면 영상 한 편.
  - `explainer`: 원리. 화면의 모든 움직임이 악보가 된다 (큐 목록 = 악보).
  - `demo`: 실제 작업 하나를 순서대로. 요청에서 검사 통과까지.
- 증거 (모두 이 세션의 실제 출력을 다시 조판(re-typeset, 글자만 새로 앉힘)):
  1. 사용자의 실제 요청: "이 스킬을 /reference-to-video 이거 이용해서 클로드 코드에 대한거 30초짜리 하나 만들어보자. 이 스킬 이용해서"
  2. 셋업 점검: Chrome ok, ffmpeg 8.1.2 + rubberband, Node v26.4.0, Python 3.12.13
  3. 테스트: `31 passed in 81.30s`
  4. 인터뷰 답: 장르 "3개 다 하자", 메시지 "이 영상도 Claude Code가", 언어 "한국어"
  5. `cues.mjs`, `compose.py`, `synccheck.py` 결과: 실행한 뒤 실제 값으로 채움
- 하지 말 것: Anthropic 로고·브랜드 사용, 공식 영상처럼 보이기 (끝 카드에 비공식 표기), 실행하지 않은 결과나 지어낸 숫자. 줄이거나 건너뛴 시간은 화면에 표기.

## 3. 형식과 소리
- 각 30.0초, 1920×1080, 30 fps, H.264 MP4
- 카드 문구는 한국어 (Noto Sans KR), 터미널 출력은 원문 그대로
- 내레이션 없음, 자막 없음. 음악과 화면 글자만 (런칭 장르는 원래 음악만이고, TTS 도구가 묶여 있지 않음)
- 음악: 각 장르의 기본 팔레트로 화면 큐에 맞춰 작곡

## 4. 소스와 규칙
- 앱 녹화 없음, 터미널 출력만 재조판
- 사람 등장 없음, 브랜드 자산 없음
- 파일: `video/{launch,explainer,demo}/index.html`, 결과물 `out/video/{launch,explainer,demo}.mp4`
