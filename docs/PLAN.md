# 구현 계획

**버전**: v2.0 (압축)
**작성일**: 2025-10-23
**완전판**: `docs/archive/PLAN.md`

---

## 단계별 구현 체크리스트

### 1단계: 기초 인프라
**요약**: 프로젝트 기본 설정, N개 프로필 동시 실행 코루틴, Playwright 세션 관리, 클릭 요소 수집 & 스코어링

- [ ] main.py: N 프로필 코루틴, 레이트 리미터, Stop
- [ ] executor.py: Playwright 세션, 클릭 수집
- [ ] heuristics.py: CTA/Curiosity 스코어링
- [ ] config/: keywords.json, profiles.yaml, llm_api.yaml

### 2단계: 탐색 & 안정성
**요약**: 점수 기반 액션 선택, 무한 루프 방지(TTL, 중복 차단), 재시도 백오프, 봇 탐지 회피

- [ ] executor.select_next_action(): 점수 기반 선택
- [ ] Loop Prevention (1분 TTL, 2회 금지)
- [ ] Backoff (1→2→4→8→16s)
- [ ] Jitter (2-45s)

### 3단계: 폼 처리 핵심
**요약**: 폼 경계 자동 인식, 회원가입/로그인/글쓰기/댓글 폼 분리, Inline→Global 오류 판별, 크레덴셜 관리

- [ ] executor.form_scope_from_submit()
- [ ] Auth/Write/Comment 폼 분리
- [ ] Inline→Global 신호 (≤2회 재시도)
- [ ] creds.py: 크레덴셜 관리

### 4단계: AI 콘텐츠 생성
**요약**: LLM API 통합, Persona 기반 콘텐츠 생성, 안전 필터, 다양성 확보

- [ ] ai_brain.py: LLM 호출 (Gemini/Claude/OpenAI)
- [ ] Persona 로딩
- [ ] Safety Filter (금칙어, PII, 중복)
- [ ] 다양화 (temperature, few-shot)

### 5단계: 비동기 액션 처리
**요약**: API 호출 모니터링(좋아요, 투표), DOM/URL 변화 감지, 타임아웃 & 재시도

- [ ] executor.wait_for_action_effect()
- [ ] API 모니터링 (/api/(like|vote|...)/)
- [ ] DOM/URL 변화 감지
- [ ] 타임아웃/재시도 (2.5s, 1회)

### 6단계: 로그인 상태 관리
**요약**: 다중 신호 기반 로그인 검증, 로그인 직후 보호창(60초), 무한 로그인 루프 방지

- [ ] executor.check_login_status() (다중 신호)
- [ ] main.py 보호창 (60s)
- [ ] N사이클 재검사

### 7단계: 운영 모니터링
**요약**: JSONL 구조화 로깅, 성능 메트릭 수집(처리량, 오류율, 지연)

- [ ] JSONL 로깅
- [ ] 메트릭 수집 (처리량, 오류, 지연)

### 8단계: 통합 검증
**요약**: QA 시나리오 실행, 버그 수정 & 최적화

- [ ] QA 시나리오 실행 (T-Scope-1, T-Inline-1, ...)
- [ ] 버그 수정 & 최적화

---

## 구현 순서

1. 1단계 (기초)
2. 2단계 (안정성)
3. 3단계 (핵심 기능)
4. 4단계 (AI)
5. 5-6단계 (고급)
6. 7단계 (운영)
7. 8단계 (검증)

---

**참조**: [@docs/PRD.md](PRD.md), [@docs/RESOURCE.md](RESOURCE.md), [@docs/LLD.md](LLD.md)
