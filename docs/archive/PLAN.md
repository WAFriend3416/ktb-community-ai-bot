# 구현 계획 (Implementation Plan)

**문서 버전**: v1.1 (중복 제거: 2025-10-23)  
**기준**: PRD v1.6 (Clickable-First + Hybrid AI + Ops-Hardening)  
**작성일**: 2025-10-23

---

## 📋 프로젝트 개요

**목표 및 전략**: [@docs/PRD.md](PRD.md#0-목적--범위) 참조

**핵심 요구사항**:
- N개 프로필 동시 실행 (1~100개 확장 가능)
- Clickable-First 탐색 + Hybrid AI 콘텐츠 생성
- Anti-Bot 우회 기술

---

## 🎯 구현 단계 (Phases)

### Phase 1: 기초 인프라 & 상태 관리
**목표**: 프로젝트 구조, 기본 Playwright 세션, 설정 시스템 구축  
**산출물**:
- 프로젝트 폴더 구조 (profiles/, config/, logs/)
- main.py 스켈레톤 (코루틴 루프, 프로필 관리)
- executor.py 기초 (Playwright 세션, 페이지 로딩)
- config/keywords.json (CTA, 성공/실패 키워드)
- config/profiles.yaml (동적 프로필 생성 스키마, 1~100개 프로필 지원)
- config/llm_api.yaml (공통 LLM API 설정)

**핵심 구현**: [@docs/LLD.md](LLD.md#1️⃣-mainpy-오케스트레이터) 참조

**주요 작업**:
- main.py: N 프로필 코루틴, 전역 레이트 리미터, Stop 플래그
- executor.py: Playwright 세션, 클릭 후보 수집, 로그인 상태 판별
- heuristics.py: CTA/Curiosity 스코어링, 텍스트 정규화
- config/keywords.json: [@docs/RESOURCE.md](RESOURCE.md#1-configkeywordsjson) 참조

---

### Phase 2: Clickable-First 탐색 & 루프 방지
**목표**: 안정적인 UI 탐색, 루프 방지, 백오프 메커니즘  
**산출물**:
- executor.select_next_action() 구현
- Loop Prevention System (1분 TTL, 정규화 텍스트 중복 검사)
- Backoff Logic (지수 백오프: 1→2→4→8→16s)
- Anti-Bot Jitter (2-45s 랜덤 지연)

**핵심 구현**:
```
executor.py:
  - async select_next_action(page, clickables): 점수 기반 선택
  - async select_top_candidates(scored): 상위 1~3위 중 확률 선택
  - loop_key(href, text) 생성 및 검사
  - async execute_action(selector, action_type): 클릭/타입/제출
  - async with_backoff(func, max_retries=5): 지수 백오프 래퍼

main.py:
  - 액션별 시도 상한 관리 (페이지당 CTA ≤3, 동일 CTA ≤2)
  - 전역/프로필 레이트 리미터 적용
  - history.back() / 홈 복귀 로직
```

---

### Phase 3: 폼 바운더리 & 자동완성 (Auth / Write / Comment)
**목표**: 정확한 폼 범위 감지, 역할별 자동완성  
**산출물**:
- executor.form_scope_from_submit() 구현
- Auth/Write/Comment 폼 자동완성 로직
- 인라인 오류 감지 & 재시도 (≤2회)
- Inline → Global 2단계 성공 신호

**핵심 구현**: [@docs/LLD.md](LLD.md#2️⃣-executorpy-playwright-실행자) 참조

**주요 작업**:
- Form scope 추출 (submit 조상 `<form>`)
- 폼별 자동완성 (Auth/Write/Comment 분리)
- 인라인 오류 자동 보정 (≤2회)
- 크레덴셜 관리: `creds.py` 생성

---

### Phase 4: LLM 통합 & 콘텐츠 생성
**목표**: 페르소나 기반 콘텐츠 생성, 안전 필터, 다양성 보장 (공통 LLM API 기반)  
**산출물**:
- ai_brain.py 구현 (LLM 호출, 프롬프트)
- Safety Filter (금칙어, PII, 금지 태그)
- Deduplication (로컬 해시)
- Profile-specific Persona/Temperature/Few-shot (LLM은 공통)

**핵심 구현**: [@docs/LLD.md](LLD.md#4️⃣-보조-컴포넌트-인터페이스) 참조

**주요 작업**:
- LLM API 통합 (Gemini/Claude/OpenAI 중 1개)
- 페르소나 로딩 및 프롬프트 생성
- 안전 필터 & 중복 제거
- config/: [@docs/RESOURCE.md](RESOURCE.md#3-configllm_apiyaml-공통-llm-api-설정) 참조

---

### Phase 5: 비동기 액션 판별 (FR10)
**목표**: API 응답 기반 성공 판별, fetch/XHR 감지  
**산출물**:
- executor.wait_for_action_effect() 구현
- API 모니터링 (정규식: /api/(like|vote|comment|follow|post|login)/)
- 타임아웃/재시도 로직 (2.5s, 재시도 1회)

**핵심 구현**: [@docs/LLD.md](LLD.md#22-헬퍼-함수) 참조

**주요 작업**:
- API 응답 감지 (page.wait_for_response)
- DOM/URL 변화 감지 (스냅샷 비교)
- 버튼 상태/카운트 변경 감지
- 타임아웃 처리 & 재시도

---

### Phase 6: 로그인 상태 이중화 & 보호창 (FR11)
**목표**: 안정적인 로그인 상태 판별, 무한 루프 방지  
**산출물**:
- executor.check_login_status() 다중 신호 구현
- main.py 보호창 로직 (로그인/가입 직후 60s)
- N사이클 재검사 (예: 3사이클마다)

**핵심 구현**: [@docs/LLD.md](LLD.md#21-executor-클래스) 참조

**주요 작업**:
- 다중 신호 판별 (로그아웃 버튼, 쿠키, 세션 파일)
- 보호창 관리 (protection_window)
- 주기적 재검사 로직

---

### Phase 7: 로그 & 메트릭
**목표**: 구조화된 로깅, 모니터링 인프라  
**산출물**:
- JSONL 로깅 (time, actor, state, intent, action, result, latency)
- 메트릭 수집 (처리량, 오류, 차단, 지연 p50/p95)

**핵심 구현**: [@docs/LLD.md](LLD.md#4️⃣-보조-컴포넌트-인터페이스) 참조

**로그 포맷**: [@docs/RESOURCE.md](RESOURCE.md#📊-로그-포맷-logsactions_yyyymmddjsonl) 참조

**주요 작업**:
- JSONL 로깅 시스템 구축
- 메트릭 수집기 구현
- 주기적 스냅샷 저장

---

### Phase 8: 테스트 & 안정화
**목표**: QA 시나리오 검증, 엣지 케이스 처리  
**산출물**:
- 테스트 보드 환경 구성
- QA 시나리오 실행 (T-Scope-1, T-Inline-1, T-Async-1, T-Lock-1, T-LLM-1 등)
- 버그 수정 & 성능 최적화

---

## 🔧 구성요소 맵

**상세 폴더 구조**: [@docs/RESOURCE.md](RESOURCE.md#프로젝트-폴더-구조-n-프로필-1100개) 참조

**핵심 컴포넌트**:
- `main.py`: 오케스트레이터 (Phase 1, 6)
- `executor.py`: Playwright 실행자 (Phase 1-5, 7)
- `heuristics.py`: 스코어링 (Phase 2)
- `ai_brain.py`: LLM 통합 (Phase 4)
- `config/`: 설정 파일 (keywords.json, profiles.yaml, llm_api.yaml)
- `profiles/`: N개 프로필 런타임 데이터

---

## 🚀 구현 순서 (우선순위)

1. **Phase 1** (필수 기초)
   - main.py 코루틴 루프
   - executor.py 세션 & 페이지 로딩
   - config/ 초기화

2. **Phase 2** (안정성)
   - Clickable-First 탐색
   - Loop Prevention
   - Backoff & Jitter

3. **Phase 3** (핵심 기능)
   - 폼 바운더리 & 자동완성
   - Auth/Write/Comment 분리
   - Inline→Global 신호

4. **Phase 4** (AI 통합)
   - LLM 호출
   - 안전 필터
   - 페르소나 로딩

5. **Phase 5** (고급 기능)
   - Async Action Detection
   - API 모니터링

6. **Phase 6** (안정성 강화)
   - 로그인 상태 이중화
   - 보호창 & 재검사

7. **Phase 7** (운영성)
   - 로그 & 메트릭

8. **Phase 8** (검증)
   - QA 시나리오
   - 버그 수정

---

## ✅ 완료 기준 (Acceptance Criteria)

**상세 기준**: [@docs/PRD.md](PRD.md#7-수용-기준ac) 참조

**핵심 지표**:
- 폼 경계 정확도: 혼동 0건
- 실패 판별: Inline→Global 준수
- 동시성: 1분 내 ≥2 프로필 액션
- AI 다양성: n-gram 중첩 ≤40%

---

## 📝 주요 의존성

- **Playwright**: UI 자동화 & 세션 관리
- **OpenAI/Anthropic/Google Gemini**: LLM 호출 (프로필별 다양화)
- **aiohttp**: 비동기 HTTP (API 응답 모니터링)
- **pydantic**: 설정 검증
- **python-dotenv**: 환경변수 관리

---

## 🔴 주의사항 (Risk)

1. **Clickable-First 신뢰도**: 패턴 매칭 실패 시 대체 전략 필요 (fallback CTA)
2. **LLM 금칙어 필터**: 프로필별로 다른 모델 사용 시 필터 효과 편차 가능
3. **Anti-Bot 우회**: 서버가 더 강화될 경우 대응 필요 (예: JS 렌더링, 지연 증가)
4. **세션 영속성**: 쿠키/스토리지 만료 시 자동 재로그인 로직 필수
5. **Async 액션 감지**: API 패턴이 서비스마다 다를 경우 확장 필요

---

**다음 문서**: [@docs/RESOURCE.md](RESOURCE.md) - 의존성, 라이브러리, 운영 파라미터
