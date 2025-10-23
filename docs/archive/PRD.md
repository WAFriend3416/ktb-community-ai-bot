# 📋 PRD v1.6 — Clickable-First + Hybrid AI + Ops-Hardening

**문서 버전**: v1.6 (최종)  
**작성일**: 2025-10-23  
---

## 0️⃣ 목적 및 범위

### 🎯 목적
커뮤니티 URL 하나만으로 **N개 프로필**이 동시에 다음 작업을 자동 수행:
- 회원가입
- 로그인
- 커뮤니티 탐색
- 댓글/게시글 작성

### 🔧 전략
| 영역 | 접근 방식 |
|------|-----------|
| **UI 탐색** | Clickable-First (버튼/링크/폼 탐색·스코어링·실행) |
| **콘텐츠 생성** | LLM 기반 하이브리드 AI (페르소나 + 컨텍스트) |
| **운영 강화** | 비동기 액션 판별, 로그인 상태 이중화, AI 발자국 다양화, Anti-Bot |

### ⚠️ 전제 조건
- ✅ 이메일 인증 없음
- ✅ 캡차 없음
- ✅ Express/바닐라 JS 계열 커뮤니티
- ⚠️ **테스트 보드에서만 운영** (윤리 준수)

---

## 1️⃣ 상위 플로우 (상태머신)

```
START
  ↓
UI_SCAN (클릭 후보 수집/스코어링)
  ├─→ SIGN_UP
  │     ↓
  │   AUTH_FORM_SCOPE → AUTH_AUTO_FILL → SUBMIT
  │     ↓
  │   SUCCESS_CHECK (Inline → Global)
  │
  ├─→ LOGIN
  │     ↓
  │   AUTH_FORM_SCOPE → AUTH_AUTO_FILL → SUBMIT
  │     ↓
  │   SUCCESS_CHECK (Inline → Global)
  │
  └─→ ACTION_HUB
        ├─→ WRITE_POST
        │     ↓
        │   WRITE_FORM_SCOPE → LLM_GENERATE → FILL → SUBMIT → SUCCESS_CHECK
        │
        ├─→ WRITE_COMMENT
        │     ↓
        │   COMMENT_FORM_SCOPE → LLM_GENERATE → FILL → SUBMIT → SUCCESS_CHECK
        │
        └─→ EXPLORE (High-Curiosity 링크 우선, 루프 방지)

↻ 실패 시: 백오프/대체 CTA/시도 상한/Stop-All
```

---

## 2️⃣ 구성요소 및 책임

| 파일 | 역할 | 핵심 기능 |
|------|------|----------|
| **main.py** | 오케스트레이터 | N 프로필 코루틴 동시 실행, 전역/프로필 레이트, 멱등, Stop-All, 로그인 상태 판별, 로그/메트릭 |
| **executor.py** | Playwright 실행자 | Clickable-First 탐색, FORM SCOPE 추출, Auth/Write/Comment 폼 분리, 성공/실패 2단계, 세션 영속화, 비동기 액션 판별 |
| **heuristics.py** | 휴리스틱 스코어링 | CTA/Curiosity 스코어링, 텍스트·URL 패턴, 소량 무작위 가중치, 루프 키 생성 |
| **ai_brain.py** | LLM 어댑터 | 페르소나+컨텍스트 기반 콘텐츠 생성, 금칙어/PII/중복 필터, 프로필별 다양화 |
| **config/keywords.json** | 패턴 데이터 | 키워드/패턴/성공·실패 문구 외부화 (핫스왑) |

---

## 3️⃣ 기능 요구사항 (FR)

### FR1. 클릭 후보 수집 & 세션

**수집 대상**:
- 버튼/링크/submit/role/onclick 요소

**메타데이터**:
- 텍스트, role, href, 가시성, 좌표, DOM 경로, 면적

**세션 관리**:
```
profiles/<profile_id>/session.json
```
- 저장·복구 지원

---

### FR2. 스코어링 (CTA + Curiosity)

#### CTA 스코어링
텍스트 및 URL 패턴 기반:
- 가입, 로그인, 글쓰기, 댓글, 제출, 로그아웃

#### Curiosity 스코어링
탐색 우선순위:
1. `/post|/view` 상세 페이지
2. 페이지네이션
3. 좋아요 (가중치 차등)

**로그인 상태 반영**:
- 로그인 CTA → 강한 페널티 (이미 로그인 시)

**선택 전략**:
- 상위 1~3위 중 확률 선택 (무작위 가중치)

---

### FR3. FORM BOUNDARY + 폼 자동완성

#### Auth 폼 (회원가입/로그인)
**범위**: `submit` 버튼의 조상 `<form>` 기준

**자동완성 필드**:
- 이메일
- 유저명
- 비밀번호 1·2
- 약관 동의

**오류 처리**:
- Inline 오류 즉시 수정 후 재제출 (≤2회)

#### Write/Comment 폼
**범위**: `submit` 버튼의 조상 `<form>` 내

**자동완성 필드**:
- 제목/본문 (LLM 결과 사용)
- 댓글 (LLM 결과 사용)

---

### FR4. 성공/실패 신호 2단계 (순서 강제)

#### 1단계: Inline (폼 내부)
**감지 대상**:
```css
[aria-invalid]
.error
.error-message
```

**오류 메시지**:
- "필수", "형식", "8자", "중복"

**처리**: `inline_fail` → 즉시 수정/재시도

#### 2단계: Global (페이지 전체)
**성공 신호**:
- ✅ 로그아웃 버튼 출현
- ✅ URL 변화
- ✅ 쿠키·스토리지 증가
- ✅ body 텍스트의 성공 키워드

**실패 신호**:
- ❌ body 텍스트의 실패 키워드

---

### FR5. 안전 내비게이션 (루프 방지/백오프)

#### 루프 방지
**모든 클릭 (CTA + Curiosity)**에 대해:
- 1분 TTL
- 동일 href/정규화 텍스트 **2회 초과 금지**

#### 시도 상한
| 제약 | 상한 |
|------|------|
| 페이지당 CTA 시도 | ≤ 3 |
| 동일 CTA 재시도 | ≤ 2 |

#### 백오프 전략
실패 시:
1. `history.back()` 또는 홈 복귀
2. 지수 백오프: **1 → 2 → 4 → 8 → 16초**

---

### FR6. 동시성/레이트/멱등/Stop

#### 동시성
- 동시 워커: **≥ 6** (N 프로필 × 2)

#### 레이트 리미터

| 제약 | 상한 |
|------|------|
| **전역 읽기** | 1 QPS |
| **전역 쓰기** | 6 QPM |
| **프로필 기본** | 2/h (설정 가능) |

#### 멱등성
- 서버 키 지원 시: `Idempotency-Key` 헤더
- 미지원 시: `sha1(title + "\n" + body)[:12]` 로컬 차단

#### Stop 플래그
- `STOP_ALL`: 즉시 반영 (write 차단)
- `STOP_ACTOR`: 특정 프로필 중단

---

### FR7. 로그 & 메트릭

#### JSONL 로그
```json
{
  "time": "ISO8601",
  "actor": "profile_001",
  "state_before": "UI_SCAN",
  "intent": "cta|curiosity",
  "action": "click|type|submit",
  "scope": "form|global",
  "selector": "...",
  "text": "...",
  "url_before": "...",
  "url_after": "...",
  "result": "ok|inline_fail|fail|rate_limited",
  "latency_ms": 850,
  "note": "..."
}
```

#### 메트릭
- 처리량 (actions/min)
- 오류율
- 차단 횟수
- 지연 p50/p95
- 중복 차단
- 루프 차단

---

### FR8. 크리덴셜 관리

#### SIGN_UP
1. 새 creds 생성
2. 저장: `profiles/<profile_id>/creds.json`

#### LOGIN
- 저장된 creds 사용

**파일 구조**:
```json
{
  "email": "...",
  "username": "...",
  "password": "..."
}
```

---

### FR9. 콘텐츠 생성 (Hybrid AI)

#### 프로세스

```
WRITE_POST/WRITE_COMMENT
  ↓
페르소나 로딩: profiles/<profile_id>/persona.yaml
  ↓
LLM 호출: 최근 탐색 컨텍스트 + 페르소나
  ↓
안전 필터: 금칙어/PII/광고/금지 태그/길이 제한
  ↓
중복 필터: 로컬 해시/유사도 (선택)
  ↓
출력: {"title": "...", "body": "..."} / {"comment": "..."}
```

#### 페르소나 구성
```yaml
tone: "friendly"
length: "medium"
topics: ["tech", "design"]
few_shot: "..."
negative_phrases: ["광고", "스팸"]
```

---

### FR10. 비동기 액션 판별 (Async Action Detection)

#### 성공 판정 기준 (하나 이상)

| 방법 | 설명 |
|------|------|
| **(A) DOM/URL 변화** | 기존 FR4 |
| **(B) API 응답 성공** | `page.wait_for_response()` |
| **(C) 버튼 상태/카운트 변경** | 라벨, 카운트, 비활성화 상태 |

#### API 패턴
```regex
/api/(like|vote|comment|follow|post|login)/i
```

#### 타임아웃
- 기본: **2.5초**
- 재시도: **1회**
- 그 외: `unknown` → skip

---

### FR11. 로그인 상태 이중화 & 상태 락 방지

#### check_login_status() 다중 신호

| 신호 | 설명 |
|------|------|
| **(A) 로그아웃 버튼** | 존재 여부 |
| **(B) 인증 쿠키/LocalStorage** | `auth_token`, `user_id` 등 |
| **(C) 세션 파일 최신성** | `session.json` mtime |

#### Fail-safe 보호창
**로그인/가입 성공 직후**:
- 보호창: **60초**
- 강제: `ACTION_HUB` 진입

**그 이후**:
- N사이클 (예: 3)마다 재검사

---

### FR12. AI 발자국 다양화

#### 프로필별 차등화

| 요소 | 다양화 방법 |
|------|-----------|
| **Temperature** | 0.5 ~ 0.9 범위에서 무작위 |
| **Sampling** | top_k, top_p, presence_penalty |
| **Few-shot** | 스타일 앵커 고정 |
| **Negative Prompt** | 금지 표현 억제 |

#### 랜덤성 가중치
- 표현 변주
- 스코어 소량 무작위 추가

---

### FR13. Anti-Bot 운영 정책

#### 기술적 회피

| 기법 | 설명 |
|------|------|
| **UA/Viewport** | 무작위화 |
| **액션 지연** | Jitter (2–45초) |
| **선택 전략** | 상위 1~3위 중 확률 선택 |
| **헤더** | 언어/시간대/DNT 랜덤화 |
| **회선** | 가능 시 다변화 |

#### 윤리 준수
- ⚠️ **테스트 보드 외 금지**
- ⚠️ 로그 PII 미기록
- ⚠️ 금칙어 필터

---

## 4️⃣ 휴리스틱 데이터 테이블 (v1.6.1 강화)

### 4.1 CTA 키워드 & URL 패턴 (우선순위 및 상태 기반)

> **참고**: `heuristics.py`는 현재 상태(STATE)에 따라 CTA 가중치를 조절합니다.

| CTA | 텍스트 키워드 (대소문자 무관) | URL 패턴 (정규식) | 우선순위 | 비고 |
|-----|----------------------------|-----------------|---------|------|
| **SIGN_UP** | 회원가입, 가입, **시작하기**, **무료 가입**, 계정 생성, Sign up, Create account, Join, Register | `/signup`, `/register`, `/join`, `/users/sign_up` | ⭐⭐⭐ | STATE=START 시 최고 우선순위 |
| **LOGIN** | 로그인, Sign in, Log in, 로그인하기 | `/login`, `/signin`, `/session`, `/users/sign_in` | ⭐⭐⭐ | STATE=START 시 최고 우선순위 |
| **LOGOUT** | 로그아웃, Sign out, Logout | `/logout`, `/sign_out` | ⭐ | 로그인 상태 판별용 |
| **WRITE_POST** | 글쓰기, 새 글, **게시하기**, **포스트 작성**, 작성, Write, New post, Create Post | `/new`, `/write`, `/post/new`, `/posts/new`, `/compose` | ⭐⭐ | STATE=ACTION_HUB 시 |
| **SUBMIT** | **등록**, **발행**, 제출, 보내기, 저장, 완료, Post, Submit, Publish, Save | (폼 내부만) | ⭐⭐⭐ | STATE=IN_FORM 시 |
| **COMMENT** | 댓글, **댓글 달기**, 답글, **답변하기**, Comment, Reply, Add comment | `/comment`, `#comment`, `/replies` | ⭐⭐ | POST_VIEW 내부 |

**주요 개선**:
- ✅ "시작하기", "무료 가입" 등 명확한 진입 키워드 추가
- ✅ WRITE_POST와 SUBMIT 역할 분리 (탐색 vs 폼 제출)
- ✅ 우선순위 시각화 (⭐ 개수)

### 4.2 Curiosity (탐색) 패턴 및 키워드

| 패턴 | 타입 | 값 (Selector / 정규식) | 가중치 | 비고 |
|------|------|----------------------|--------|------|
| **POST_VIEW** | URL | Regex: `/post/(?!new OR write)` 상세 URL, `/posts/(?!new)`, `/view/`, `/entry/`, `/topic/` | ⭐⭐⭐ (상) | COMMENT 기회, WRITE_POST URL 제외 |
| **USER_PROFILE** | URL | `/user/`, `/profile/`, `/author/`, `/member/` | ⭐⭐ (중) | 추가 탐색 경로 |
| **PAGINATION** | Text | 다음, 이전, more, next, prev, 페이지 | ⭐ (하) | **루프 방지 필수** (FR5) |
| **LIKE** | Text | 좋아요, 추천, upvote, like, 👍 | ⭐ (최하) | **비동기 판별 필수** (FR10), **루프 방지** |

**주요 개선**:
- ✅ POST_VIEW에 negative lookahead 개념 추가 → WRITE_POST와 충돌 방지
- ✅ USER_PROFILE 패턴 추가 (사용자 탐색)
- ✅ PAGINATION/LIKE를 URL → Text 기반으로 변경 (현실적)
- ✅ 가중치 명시 (⭐ 개수)

### 4.3 폼 자동완성 셀렉터 (접근성 강화)

> **문법**: Playwright는 쉼표(`,`)로 여러 셀렉터 조합. 파이프(`|`)는 CSS 표준이 아니므로 수정.

| 필드 | CSS 셀렉터 (우선순위 순) | 비고 |
|------|------------------------|------|
| **Email** | `input[type=email]`, `[id*=email i]`, `[name*=email i]`, `[autocomplete=email]`, `[placeholder*=이메일 i]`, `[aria-label*=email i]` | ✅ id, aria-label 추가 |
| **Username** | `[id*=user i]`, `[id*=nick i]`, `[name*=user i]`, `[name*=nick i]`, `[name*=name i]`, `[placeholder*=닉네임 i]`, `[placeholder*=username i]` | ✅ id 추가 |
| **Password(1)** | `input[type=password][autocomplete=current-password]`, `input[type=password]:not([name*=confirm i]):not([name*=재입력 i])` | ✅ autocomplete 우선 |
| **Password(2)** | `[name*=confirm i]`, `[name*=password_confirm i]`, `[name*=재입력 i]`, `[placeholder*=비밀번호 확인 i]`, `[placeholder*=재입력 i]` | ✅ 파이프 제거, 개별 셀렉터 |
| **Terms** | `input[type=checkbox][name*=term i]`, `input[type=checkbox][name*=agree i]`, `label:has-text('약관') input[type=checkbox]`, `label:has-text('동의') input[type=checkbox]` | ✅ label+input 조합 |
| **Title** | `[id*=title i]`, `[name*=title i]`, `[placeholder*=제목 i]`, `[aria-label*=제목 i]` | ✅ id, aria-label 추가 |
| **Body** | `textarea`, `[contenteditable=true]`, `[id*=body i]`, `[name*=body i]`, `[aria-label*=본문 i]` | ✅ aria-label 추가 |
| **Submit** | `button[type=submit]`, `input[type=submit]`, `[role=button]:text('등록')`, `[role=button]:text('발행')`, `[role=button]:text('submit')` | ✅ role=button + 텍스트 조합 |

**주요 개선**:
- ✅ **문법 수정**: 파이프(`|`) 제거, 쉼표 구분으로 개별 셀렉터 나열
- ✅ **접근성 속성**: `id`, `aria-label` 추가 (최신 웹 대응)
- ✅ **Terms 정교화**: `label:has-text('약관') input[type=checkbox]` (관계 명확화)
- ✅ **한글 패턴**: "재입력" 등 한국어 사이트 대응

> **중요**: 모든 탐색·입력은 **FORM SCOPE** (제출 버튼의 조상 `<form>` 영역) 내에서만 수행

### 4.4 성공/실패 키워드

| 타입 | 키워드 |
|------|--------|
| **Success** | 환영합니다, 성공, 로그인되었습니다, 작성되었습니다, 등록됨, 완료, posted, published, saved |
| **Fail (Global)** | 에러, 오류, 실패, 비밀번호가 틀렸습니다, 필수 항목, 중복된, 이미 사용, error, failed, invalid, required |
| **Inline Fail** | 8자 이상, 특수문자, 최소/최대, 형식/포맷, too short, weak, mismatch |

---

## 5️⃣ 의사코드 훅 (핵심)

### 5.1 로그인 상태 판별 (main.py)

```python
is_logged_in = await executor.check_login_status(page)

if last_action in ("LOGIN_SUCCESS", "SIGNUP_SUCCESS"):
    force_until = now + 60  # 보호창

if now < force_until:
    is_logged_in = True
```

### 5.2 Auth vs Write/Comment 분리 (executor.py)

```python
async def handle_auth_form(page, state, creds):
    form = await form_scope_from_submit(page)
    
    if state == "SIGN_UP":
        creds = generate_new_credentials()
        await fill_auth_fields(form, creds)  # email/user/pw1/pw2/terms
        save_creds(profile, creds)
    else:  # LOGIN
        await fill_login_fields(form, creds)  # email/pw
    
    await submit(form)
    return await check_success_signals(page, form)


async def handle_write_form(page, persona, context):
    form = await form_scope_from_submit(page)
    content = await ai_brain.generate_content(persona, context)  # FR9
    content = guard_and_dedupe(content)
    await fill_write_fields(form, content)
    await submit(form)
    return await check_success_signals(page, form)
```

### 5.3 비동기 액션 판별 (executor.py, FR10)

```python
API_SUCCESS = r"/api/(like|vote|comment|follow|post|login)"
resp_ok = await page.wait_for_response(
    lambda r: re.search(API_SUCCESS, r.url, re.I) and r.ok,
    timeout=2500
)

if resp_ok or await dom_or_url_changed(page) or await label_or_count_changed():
    status = "success"
```

### 5.4 Anti-Bot 랜덤화

```python
ua = random.choice(USER_AGENTS)
viewport = random.choice(VIEWPORTS)
score += random.uniform(0, 5)  # 상위 후보 간 무작위 가중치
await asyncio.sleep(random.uniform(2, 45))  # Jitter
```

---

## 6️⃣ 비기능 요구사항 (NFR)

| 영역 | 요구사항 |
|------|----------|
| **성능** | 화면 전환 p95 < 3s, 1 사이클 5–10분 |
| **회복성** | 지수 백오프 (1→2→4→8→16s, 최대 5회), CTA 시도 ≤3/페이지, 동일 CTA 재시도 ≤2 |
| **안전/윤리** | 테스트 보드 한정, 금칙어·PII 필터, 로그에 PII 미기록 |
| **운영성** | 키워드/페르소나/레이트/모델 파라미터 설정화 (재배포 없이 조정) |

---

## 7️⃣ 수용 기준 (AC)

### 필수 통과 기준

- [ ] **폼 경계 정확도**: 뉴스레터 등 타 폼과 혼동 0건 (가입/로그인/작성 모두 통과)
- [ ] **실패 판별 순서**: Inline→Global 준수, 오판율 ≤ 5%
- [ ] **Explore 루프 방지**: 1분 내 동일 href/텍스트 2회 초과 없음
- [ ] **동시성**: 1분 윈도우에서 서로 다른 프로필 액션 ≥ 2건
- [ ] **작성/댓글 성공**: 전역 6QPM·프로필 상한 준수 내 게시글 ≥1, 댓글 ≥1
- [ ] **세션 영속**: 최초 가입/로그인 후 재실행 시 자동 로그인 생략
- [ ] **Async 판별**: fetch/XHR 기반 액션 성공 인식 정확도 ≥ 95%
- [ ] **상태 락 방지**: 로그인 직후 무한 로그인 루프 0건
- [ ] **AI 다양성**: N 프로필 30건 샘플의 n-gram 중첩 ≤ 40%, Negative phrase 위반 0건
- [ ] **Anti-Bot**: UA/뷰포트/지연/선택 다양화로 서버 로그 편향 지표 < 임계

---

## 8️⃣ QA 시나리오

| ID | 시나리오 | 예상 결과 |
|----|---------|----------|
| **T-Scope-1** | 가입 페이지에 뉴스레터 폼 동시 존재 | 가입 폼만 채움 → 성공 |
| **T-Inline-1** | "8자 이상/특수문자" 인라인 오류 | 자동 보정 후 재제출 성공 |
| **T-Text-1** | URL 변화 없이 "환영합니다"만 노출 | success 판정 |
| **T-Async-1** | "좋아요" 클릭 후 `/api/like` 200 OK | URL 불변이어도 성공 |
| **T-Async-2** | 댓글 제출 `/api/comment` 500 | 재시도 1회 후 실패 기록·롤백 |
| **T-Lock-1** | 로그인 직후 로그아웃 버튼 숨김 | 쿠키/세션으로 로그인 판정, ACTION_HUB 진입 |
| **T-Loop-1** | 좋아요/페이지 2→3→4 반복 클릭 | 억제 확인 |
| **T-LLM-1** | N 프로필 각 10건 생성 | 다양성 지표 만족, 금지 문구 위반 0 |
| **T-Rate/Stop** | 6QPM 초과 시 | 차단 기록, STOP_ALL 즉시 write 중단 |
| **T-Idempotent** | 동일 본문 5회 제출 | 1회만 성공 |

---

## 9️⃣ 운영 파라미터 (초기값)

### 레이트 리미터

| 파라미터 | 초기값 |
|----------|--------|
| **전역 읽기** | 1 QPS |
| **전역 쓰기** | 6 QPM |
| **프로필 기본** | 2/h (설정 가능) |

### 백오프 & 루프

| 파라미터 | 값 |
|----------|-----|
| **백오프** | 1→2→4→8→16s (최대 5회) |
| **루프 TTL** | 60s (동일 key 2회 초과 금지) |
| **Jitter** | 2–45s |

### LLM 설정 (예시)

| 프로필 | 모델 | Temperature |
|--------|------|-------------|
| **공통** | Gemini/Claude/OpenAI (1개 선택) | 0.5 ~ 0.9 (프로필별 무작위) |

---

## 🔟 구현 체크리스트

### Phase별 필수 구현

- [ ] **FR10**: `executor.wait_for_action_effect()` 비동기 액션 판별
- [ ] **FR11**: `executor.check_login_status()` 다중 신호 + `main.py` 보호창
- [ ] **FR12**: `ai_brain` 프로필별 다양화 (temperature, negative prompt, few-shot)
- [ ] **FR13**: UA/Viewport 랜덤, 스코어 무작위, 지연 Jitter
- [ ] **FR3/FR4**: FORM SCOPE, Inline→Global 순서 준수
- [ ] **FR7**: 로그 확장 (network_signals, login_proof, llm_profile, anti_bot), 지표 집계

---

## 📌 다음 단계

1. **PLAN.md** 참조: 8개 Phase 로드맵
2. **RESOURCE.md** 참조: 의존성 및 설정
3. **Phase 1 구현 시작**: 기초 인프라 & 상태 관리

---

**문서 승인**: ✅  
**다음 문서**: [@docs/PLAN.md](PLAN.md), [@docs/RESOURCE.md](RESOURCE.md)
