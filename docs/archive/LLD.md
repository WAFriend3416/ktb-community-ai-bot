# 🏗️ LLD (Low-Level Design)

**문서 버전**: v1.1 (중복 제거: 2025-10-23)  
**기준**: PRD v1.6 + PLAN.md  
**작성일**: 2025-10-23  
**상태**: ✅ Draft

---

## 📋 개요

### 🎯 목적
본 문서는 **community-ai-bot** 프로젝트의 저수준 설계(Low-Level Design)를 정의합니다.

**프로젝트 개요**: [@docs/PRD.md](PRD.md#0-목적--범위) 참조  
**구현 계획**: [@docs/PLAN.md](PLAN.md) 참조

**본 문서의 범위**:
- 핵심 컴포넌트의 인터페이스 및 책임 명확화
- 모듈 간 데이터 흐름 및 계약 정의
- 동시성 패턴 및 에러 처리 전략 수립

### 🔍 범위
**포함**:
- 핵심 컴포넌트: `main.py`, `executor.py`, `heuristics.py`
- 보조 컴포넌트: 인터페이스만 (ai_brain, creds, logging, metrics)
- 데이터 구조 및 타입 정의
- 동시성/에러 처리 패턴

**제외**:
- 세부 구현 로직 (알고리즘 내부)
- 테스트 코드 설계
- 인프라 설정 → [@docs/RESOURCE.md](RESOURCE.md) 참조
- 요구사항 상세 → [@docs/PRD.md](PRD.md) 참조

### 🧭 설계 원칙

| 원칙 | 설명 |
|------|------|
| **관심사 분리** | UI 탐색(executor), 스코어링(heuristics), 오케스트레이션(main) 명확히 분리 |
| **인터페이스 우선** | 모듈 간 계약을 먼저 정의, 구현은 독립적 변경 가능 |
| **비동기 우선** | asyncio 기반 동시성, I/O 블로킹 최소화 |
| **설정 외부화** | 하드코딩 금지, config/ 파일로 모든 파라미터 관리 |
| **오류 투명성** | 명시적 예외 처리, 실패 시 상태 복구 가능 |

---

## 🏛️ 아키텍처 개요

### 컴포넌트 관계

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│  (오케스트레이터)                                             │
│  - N 프로필 코루틴 관리                                       │
│  - 전역/프로필 레이트 리미터                                  │
│  - Stop 플래그 제어                                          │
└──────────┬──────────────────────────────────────────────────┘
           │
           │ uses
           ↓
┌──────────────────────────────────────────────────────────────┐
│                      executor.py                             │
│  (Playwright 실행자)                                          │
│  - UI 스캔 (collect_clickables)                              │
│  - 폼 처리 (Auth/Write/Comment)                              │
│  - 성공/실패 판별 (Inline→Global)                            │
│  - 세션 영속화                                                │
└──────────┬───────────────────────────────────────────────────┘
           │
           │ uses
           ↓
┌──────────────────────────────────────────────────────────────┐
│                    heuristics.py                             │
│  (휴리스틱 스코어링)                                          │
│  - CTA 스코어링 (score_cta)                                   │
│  - Curiosity 스코어링 (score_curiosity)                       │
│  - 상위 후보 선택 (select_top_candidates)                     │
│  - 루프 방지 키 생성 (loop_key)                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  보조 컴포넌트 (인터페이스)                     │
│  - ai_brain.py: LLM 콘텐츠 생성                               │
│  - creds.py: 크레덴셜 관리                                     │
│  - action_logger.py: JSONL 로깅                               │
│  - metrics_collector.py: 메트릭 수집                          │
└──────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

```
1. main.py
     ↓ (프로필 설정)
2. executor.py.collect_clickables()
     ↓ (클릭 후보)
3. heuristics.py.score_*()
     ↓ (스코어링 결과)
4. heuristics.py.select_top_candidates()
     ↓ (선택된 액션)
5. executor.py.execute_action()
     ↓ (액션 실행)
6. executor.py.check_success_signals()
     ↓ (성공/실패)
7. main.py (다음 사이클 또는 백오프)
```

---

## 1️⃣ main.py (오케스트레이터)

### 📌 책임
- N개 프로필 코루틴 동시 실행 관리
- 전역 레이트 리미터 적용 (1 QPS 읽기, 6 QPM 쓰기)
- 프로필별 레이트 리미터 적용 (2/h 기본)
- Stop 플래그 제어 (`STOP_ALL`, `STOP_ACTOR`)
- 로그인 보호창 관리 (로그인 직후 60초)
- 로그/메트릭 집계

### 🔌 주요 인터페이스

#### 1.1 엔트리포인트

```python
async def main() -> None:
    """
    메인 엔트리포인트.
    - 설정 로딩 (config/profiles.yaml, config/llm_api.yaml)
    - N개 프로필 코루틴 생성 및 실행
    - 전역 Stop 플래그 감지
    """
```

#### 1.2 프로필 루프

```python
async def run_actor(
    actor_id: str,
    profile_config: ProfileConfig,
    global_state: GlobalState,
    stop_event: asyncio.Event
) -> None:
    """
    단일 프로필의 무한 루프.
    
    Args:
        actor_id: 프로필 ID (profile_001, profile_002, ...)
        profile_config: 프로필 설정 (온도, 시간당 상한 등)
        global_state: 전역 상태 (레이트 리미터, 보호창)
        stop_event: Stop 플래그 이벤트
    
    Flow:
        1. check_login_status() → 로그인 상태 판별
        2. 로그인 안 됨 → SIGN_UP/LOGIN 플로우
        3. 로그인 됨 → ACTION_HUB (WRITE_POST/WRITE_COMMENT/EXPLORE)
        4. 실패 시 백오프 + 재시도 (≤5회)
        5. Stop 플래그 확인 후 종료
    """
```

#### 1.3 레이트 리미터

```python
class RateLimiter:
    """
    전역 및 프로필별 레이트 리미터.
    
    Methods:
        async acquire_read() -> bool:
            전역 읽기 (1 QPS) 허용 확인
        
        async acquire_write(actor_id: str) -> bool:
            전역 쓰기 (6 QPM) 및 프로필별 상한 (2/h) 확인
        
        reset_window() -> None:
            시간 윈도우 리셋 (1분마다)
    """
```

#### 1.4 Stop 컨트롤러

```python
class StopController:
    """
    Stop 플래그 관리.
    
    Attributes:
        stop_all: asyncio.Event (전체 중단)
        stop_actors: Dict[str, asyncio.Event] (프로필별 중단)
    
    Methods:
        signal_stop_all() -> None:
            전체 중단 신호
        
        signal_stop_actor(actor_id: str) -> None:
            특정 프로필 중단 신호
        
        should_stop(actor_id: str) -> bool:
            중단 여부 확인
    """
```

### 📦 데이터 구조

```python
from typing import TypedDict, Dict
from datetime import datetime

class ProfileConfig(TypedDict):
    """프로필 설정"""
    actor_id: str
    name: str
    temperature: float  # 0.5 ~ 0.9
    max_hourly_actions: int  # 기본 2
    persona_file: str  # config/personas/profile_NNN.yaml

class GlobalState(TypedDict):
    """전역 상태"""
    rate_limiter: RateLimiter
    stop_controller: StopController
    protection_windows: Dict[str, datetime]  # {actor_id: expiry_time}
    metrics_collector: MetricsCollector
```

---

## 2️⃣ executor.py (Playwright 실행자)

### 📌 책임
- Playwright 세션 관리 (UA/Viewport 무작위화)
- UI 스캔 및 클릭 후보 수집
- 폼 범위(FORM SCOPE) 추출 (submit 조상 `<form>`)
- Auth/Write/Comment 폼 처리 분리
- 성공/실패 신호 2단계 판별 (Inline → Global)
- 비동기 액션 판별 (API 응답, DOM/URL 변화)
- 세션 영속화 (`profiles/<profile_id>/session.json`)
- 루프 방지 (1분 TTL, 동일 href/텍스트 2회 초과 금지)

### 🔌 주요 인터페이스

#### 2.1 Executor 클래스

```python
class Executor:
    """
    Playwright 기반 UI 자동화 실행자.
    
    Attributes:
        profile_id: str
        page: playwright.async_api.Page
        session_path: str  # profiles/<profile_id>/session.json
        loop_tracker: LoopTracker  # 루프 방지
    """
    
    async def __init__(self, profile_id: str, profile_config: ProfileConfig):
        """
        Playwright 세션 초기화.
        - UA/Viewport 무작위화
        - 세션 복구 (session.json 존재 시)
        """
    
    async def collect_clickables(self) -> List[Clickable]:
        """
        페이지의 클릭 후보 수집.
        
        Returns:
            List[Clickable]: 버튼/링크/submit 요소의 메타데이터
        
        수집 대상:
            - button[type=submit]
            - input[type=submit]
            - a[href]
            - [role=button]
            - [onclick]
        
        메타데이터:
            - selector (CSS 셀렉터)
            - text (텍스트 내용)
            - href (링크 URL)
            - role (ARIA role)
            - is_visible (가시성)
            - bounding_box (좌표/면적)
            - dom_path (DOM 경로)
        """
    
    async def check_login_status(self) -> bool:
        """
        로그인 상태 판별 (FR11: 다중 신호).
        
        Returns:
            bool: 로그인 상태 (True=로그인됨)
        
        신호:
            (A) 로그아웃 버튼 존재 여부
            (B) 인증 쿠키/LocalStorage (auth_token, user_id 등)
            (C) 세션 파일 최신성 (session.json mtime)
        
        로직:
            - 3개 신호 중 2개 이상 True → 로그인됨
            - 보호창 기간 (60s) 내 → 강제 True
        """
    
    async def handle_auth_form(
        self, 
        state: Literal["SIGN_UP", "LOGIN"], 
        creds: Optional[Credentials]
    ) -> ActionResult:
        """
        Auth 폼 처리 (FR3).
        
        Args:
            state: SIGN_UP 또는 LOGIN
            creds: 크레덴셜 (LOGIN 시 필수)
        
        Returns:
            ActionResult: 성공/실패 결과
        
        Flow:
            1. form_scope_from_submit() → <form> 범위 추출
            2. SIGN_UP:
               - generate_new_credentials()
               - fill_auth_fields(email, username, pw1, pw2, terms)
               - save_creds(profile_id, creds)
            3. LOGIN:
               - fill_login_fields(email, pw)
            4. submit(form)
            5. check_success_signals(Inline → Global)
        """
    
    async def handle_write_form(
        self, 
        action_type: Literal["WRITE_POST", "WRITE_COMMENT"],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        Write/Comment 폼 처리 (FR9).
        
        Args:
            action_type: WRITE_POST 또는 WRITE_COMMENT
            context: 탐색 컨텍스트 (최근 방문 URL, 게시글 제목 등)
        
        Returns:
            ActionResult: 성공/실패 결과
        
        Flow:
            1. form_scope_from_submit() → <form> 범위 추출
            2. ai_brain.generate_content(persona, context)
            3. guard_and_dedupe(content) → 금칙어/중복 필터
            4. fill_write_fields(title, body) 또는 fill_comment_field(comment)
            5. submit(form)
            6. check_success_signals(Inline → Global)
        """
    
    async def wait_for_action_effect(
        self,
        action_type: str,
        timeout: int = 2500
    ) -> bool:
        """
        비동기 액션 판별 (FR10).
        
        Args:
            action_type: like, vote, comment, follow 등
            timeout: 타임아웃 (ms)
        
        Returns:
            bool: 성공 여부
        
        성공 판정 (하나 이상):
            (A) DOM/URL 변화 (snapshot 비교)
            (B) API 응답 성공: /api/(like|vote|comment|...)/i && r.ok
            (C) 버튼 상태/카운트/라벨 변경
        
        타임아웃 시:
            - 재시도 1회
            - 그 외 unknown → skip
        """
```

#### 2.2 헬퍼 함수

```python
async def form_scope_from_submit(page: Page) -> Optional[Locator]:
    """
    Submit 버튼의 조상 <form> 찾기.
    
    Returns:
        Optional[Locator]: <form> 요소 (없으면 None)
    
    로직:
        1. button[type=submit] | input[type=submit] 탐색
        2. locator.evaluate_handle("el => el.closest('form')")
        3. <form> 없으면 body를 폼 범위로 간주 (fallback)
    """

async def check_success_signals(
    page: Page, 
    form: Locator,
    scope: Literal["inline", "global"] = "inline"
) -> Tuple[bool, str]:
    """
    성공/실패 신호 판별 (FR4).
    
    Args:
        page: Playwright Page
        form: 폼 범위 (Locator)
        scope: inline (폼 내부) 또는 global (페이지 전체)
    
    Returns:
        Tuple[bool, str]: (성공 여부, 메시지)
    
    Inline (폼 내부):
        - [aria-invalid], .error, .error-message 탐색
        - "필수", "형식", "8자", "중복" 등 오류 메시지
        - 있으면 inline_fail → 즉시 수정/재시도 (≤2회)
    
    Global (페이지 전체):
        - 성공: 로그아웃 버튼, URL 변화, 쿠키/스토리지 증가, 성공 키워드
        - 실패: 실패 키워드 (에러, 오류, 실패, ...)
    """
```

### 📦 데이터 구조

```python
from typing import TypedDict, Literal, Optional
from playwright.async_api import Page, Locator

class Clickable(TypedDict):
    """클릭 후보 메타데이터"""
    selector: str
    text: str
    href: Optional[str]
    role: Optional[str]
    is_visible: bool
    bounding_box: Dict[str, float]  # {x, y, width, height}
    dom_path: str

class FormScope(TypedDict):
    """폼 범위"""
    form: Locator
    submit_button: Locator
    fields: List[Locator]

class ActionResult(TypedDict):
    """액션 실행 결과"""
    success: bool
    state_after: str  # UI_SCAN, SIGN_UP, LOGIN, ACTION_HUB, ...
    message: str
    url_after: str
    latency_ms: int

class Credentials(TypedDict):
    """크레덴셜"""
    email: str
    username: str
    password: str
```

---

## 3️⃣ heuristics.py (휴리스틱 스코어링)

### 📌 책임
- CTA 스코어링 (가입, 로그인, 글쓰기, 댓글, 제출, 로그아웃)
- Curiosity 스코어링 (상세 페이지, 페이지네이션, 좋아요)
- 상위 후보 선택 (1~3위 중 확률 선택, 무작위 가중치)
- 텍스트 정규화 (중복 검사용)
- 루프 키 생성 (href + 정규화 텍스트)

### 🔌 주요 인터페이스

```python
def score_cta(
    clickable: Clickable,
    keywords: CTAKeywords,
    is_logged_in: bool
) -> float:
    """
    CTA 스코어링 (FR2).
    
    Args:
        clickable: 클릭 후보
        keywords: CTA 키워드 (config/keywords.json)
        is_logged_in: 로그인 상태
    
    Returns:
        float: CTA 점수 (0.0 ~ 100.0)
    
    로직:
        1. 텍스트 매칭: clickable.text in keywords["signup"]["text"]
        2. URL 매칭: clickable.href ~= keywords["signup"]["url"]
        3. 로그인 상태 반영:
           - 로그인됨 + LOGIN CTA → 강한 페널티 (-50점)
           - 로그인 안 됨 + SIGN_UP CTA → 높은 점수 (+30점)
        4. 소량 무작위 가중치: +random.uniform(0, 5)
    """

def score_curiosity(
    clickable: Clickable,
    patterns: CuriosityPatterns
) -> float:
    """
    Curiosity 스코어링 (FR2).
    
    Args:
        clickable: 클릭 후보
        patterns: Curiosity 패턴 (config/keywords.json)
    
    Returns:
        float: Curiosity 점수 (0.0 ~ 50.0)
    
    우선순위:
        1. POST_VIEW (/post/, /view/) → 40점
        2. PAGINATION (?page=, /page/) → 20점
        3. LIKE (/like, /vote) → 10점
    
    로직:
        - href 패턴 매칭
        - 가중치 차등
        - 소량 무작위 가중치: +random.uniform(0, 5)
    """

def select_top_candidates(
    scored_actions: List[ScoredAction],
    top_n: int = 3
) -> ScoredAction:
    """
    상위 후보 중 확률 선택 (FR2).
    
    Args:
        scored_actions: 스코어링 결과 리스트 (정렬됨)
        top_n: 상위 N개 (기본 3)
    
    Returns:
        ScoredAction: 선택된 액션
    
    로직:
        1. 상위 1~3위 추출
        2. 점수 기반 확률 가중치 계산
        3. random.choices(weights) → 확률 선택
    """

def normalize_text(text: str) -> str:
    """
    텍스트 정규화 (루프 방지용).
    
    Args:
        text: 원본 텍스트
    
    Returns:
        str: 정규화된 텍스트
    
    로직:
        1. 소문자 변환
        2. 공백 정규화 (연속 공백 → 단일)
        3. 특수문자 제거 (일부 허용: -, _, .)
    """

def loop_key(clickable: Clickable) -> str:
    """
    루프 키 생성 (FR5).
    
    Args:
        clickable: 클릭 후보
    
    Returns:
        str: 루프 키 (href + 정규화 텍스트)
    
    로직:
        href + "|" + normalize_text(text)
    """
```

### 📦 데이터 구조

```python
from typing import TypedDict, List

class ScoredAction(TypedDict):
    """스코어링 결과"""
    clickable: Clickable
    cta_score: float
    curiosity_score: float
    total_score: float
    intent: Literal["cta", "curiosity"]

class CTAKeywords(TypedDict):
    """CTA 키워드 (config/keywords.json)"""
    signup: Dict[str, List[str]]  # {"text": [...], "url": [...]}
    login: Dict[str, List[str]]
    logout: Dict[str, List[str]]
    write_post: Dict[str, List[str]]
    comment: Dict[str, List[str]]

class CuriosityPatterns(TypedDict):
    """Curiosity 패턴 (config/keywords.json)"""
    post_view: List[str]
    pagination: List[str]
    like: List[str]
```

---

## 4️⃣ 보조 컴포넌트 (인터페이스)

### 4.1 ai_brain.py

```python
async def generate_content(
    persona: Persona,
    context: Dict[str, Any],
    action_type: Literal["WRITE_POST", "WRITE_COMMENT"]
) -> Union[PostContent, CommentContent]:
    """
    LLM 기반 콘텐츠 생성 (FR9).
    
    Args:
        persona: 페르소나 (config/personas/profile_NNN.yaml)
        context: 탐색 컨텍스트 (최근 URL, 게시글 제목 등)
        action_type: WRITE_POST 또는 WRITE_COMMENT
    
    Returns:
        PostContent: {"title": "...", "body": "..."}
        CommentContent: {"comment": "..."}
    
    Flow:
        1. 프롬프트 생성: persona + context + few-shot
        2. LLM 호출 (공통 API: Gemini/Claude/OpenAI 중 1개)
        3. 안전 필터: 금칙어, PII, 광고, 금지 태그
        4. 중복 필터: 로컬 해시, 유사도
    """
```

### 4.2 creds.py

```python
def generate_new_credentials(actor_id: str) -> Credentials:
    """
    새 크레덴셜 생성.
    
    Returns:
        Credentials: {email, username, password}
    
    로직:
        - email: {actor_id}_test_{timestamp}@example.com
        - username: {actor_id}_user_{random}
        - password: 무작위 8~16자 (숫자+문자+특수문자)
    """

def save_creds(profile_id: str, creds: Credentials) -> None:
    """
    크레덴셜 저장: profiles/<profile_id>/creds.json
    """

def load_creds(profile_id: str) -> Optional[Credentials]:
    """
    크레덴셜 로딩: profiles/<profile_id>/creds.json
    """
```

### 4.3 action_logger.py

```python
async def log_action(
    actor_id: str,
    state_before: str,
    intent: Literal["cta", "curiosity"],
    action: Literal["click", "type", "submit"],
    result: ActionResult,
    **kwargs
) -> None:
    """
    JSONL 로깅 (FR7).
    
    파일: logs/actions_YYYYMMDD.jsonl
    
    포맷:
        {
          "time": "ISO8601",
          "actor": "profile_001",
          "state_before": "UI_SCAN",
          "intent": "cta",
          "action": "click",
          "selector": "...",
          "url_before": "...",
          "url_after": "...",
          "result": "ok",
          "latency_ms": 850,
          "note": "..."
        }
    """
```

### 4.4 metrics_collector.py

```python
class MetricsCollector:
    """
    메트릭 수집 (FR7).
    
    Attributes:
        throughput: Dict[str, int]  # {actor_id: count}
        errors: Dict[str, int]  # {error_type: count}
        latencies: List[float]  # p50, p95 계산용
    
    Methods:
        record_action(actor_id: str, latency_ms: int) -> None
        record_error(error_type: str) -> None
        snapshot() -> MetricsSnapshot
            - 주기적으로 호출 (300s)
            - logs/metrics_YYYYMMDD.json 저장
    """
```

---

## 5️⃣ 데이터 구조 총정리

### 5.1 TypedDict/Dataclass 정의

```python
from typing import TypedDict, Literal, Optional, Dict, List, Any
from datetime import datetime

# ========== 프로필 설정 ==========
class ProfileConfig(TypedDict):
    actor_id: str
    name: str
    temperature: float
    max_hourly_actions: int
    persona_file: str

class Persona(TypedDict):
    name: str
    tone: str
    length: str
    topics: List[str]
    few_shot_style: str
    negative_phrases: List[str]
    min_length: int
    max_length: int

# ========== UI 탐색 ==========
class Clickable(TypedDict):
    selector: str
    text: str
    href: Optional[str]
    role: Optional[str]
    is_visible: bool
    bounding_box: Dict[str, float]
    dom_path: str

class ScoredAction(TypedDict):
    clickable: Clickable
    cta_score: float
    curiosity_score: float
    total_score: float
    intent: Literal["cta", "curiosity"]

# ========== 크레덴셜 ==========
class Credentials(TypedDict):
    email: str
    username: str
    password: str

# ========== 액션 결과 ==========
class ActionResult(TypedDict):
    success: bool
    state_after: str
    message: str
    url_after: str
    latency_ms: int

# ========== LLM 콘텐츠 ==========
class PostContent(TypedDict):
    title: str
    body: str

class CommentContent(TypedDict):
    comment: str

# ========== 전역 상태 ==========
class GlobalState(TypedDict):
    rate_limiter: Any  # RateLimiter 인스턴스
    stop_controller: Any  # StopController 인스턴스
    protection_windows: Dict[str, datetime]
    metrics_collector: Any  # MetricsCollector 인스턴스
```

### 5.2 주요 Literal/Enum

```python
from typing import Literal

# 상태
State = Literal[
    "START",
    "UI_SCAN",
    "SIGN_UP",
    "LOGIN",
    "ACTION_HUB",
    "WRITE_POST",
    "WRITE_COMMENT",
    "EXPLORE"
]

# 액션 타입
ActionType = Literal["click", "type", "submit"]

# 인텐트
Intent = Literal["cta", "curiosity"]

# 결과
Result = Literal["ok", "inline_fail", "fail", "rate_limited", "unknown"]
```

---

## 6️⃣ 동시성 패턴

### 6.1 asyncio 코루틴 관리

```python
# main.py
async def main() -> None:
    # N개 프로필 코루틴 생성
    profiles = load_profiles()  # config/profiles.yaml
    global_state = GlobalState(...)
    stop_event = asyncio.Event()
    
    tasks = [
        asyncio.create_task(
            run_actor(profile["actor_id"], profile, global_state, stop_event)
        )
        for profile in profiles
    ]
    
    # 모든 코루틴 동시 실행
    await asyncio.gather(*tasks, return_exceptions=True)
```

### 6.2 레이트 리미터

```python
class RateLimiter:
    def __init__(self):
        self.global_read_window = deque()  # 1초 윈도우
        self.global_write_window = deque()  # 60초 윈도우
        self.profile_windows = defaultdict(deque)  # 3600초 윈도우
        self.lock = asyncio.Lock()
    
    async def acquire_read(self) -> bool:
        async with self.lock:
            now = time.time()
            # 1초 이전 항목 제거
            while self.global_read_window and self.global_read_window[0] < now - 1:
                self.global_read_window.popleft()
            
            # 1 QPS 체크
            if len(self.global_read_window) < 1:
                self.global_read_window.append(now)
                return True
            return False
    
    async def acquire_write(self, actor_id: str) -> bool:
        async with self.lock:
            now = time.time()
            # 전역 쓰기: 6 QPM
            # 프로필별: 2/h
            # ... (구현 로직)
```

### 6.3 백오프

```python
async def with_backoff(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 16.0
) -> Any:
    """
    지수 백오프 (FR5).
    
    Delays: 1 → 2 → 4 → 8 → 16초
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = min(base_delay * (multiplier ** attempt), max_delay)
            await asyncio.sleep(delay)
```

---

## 7️⃣ 에러 처리 전략

### 7.1 예외 계층

```python
class BotError(Exception):
    """Base exception"""

class NavigationError(BotError):
    """페이지 로딩 실패, 타임아웃"""

class FormError(BotError):
    """폼 찾기 실패, 필드 누락"""

class RateLimitError(BotError):
    """레이트 리미터 차단"""

class StopSignalError(BotError):
    """Stop 플래그 감지"""
```

### 7.2 에러 복구

```python
# executor.py
async def execute_action(clickable: Clickable) -> ActionResult:
    try:
        await page.click(clickable["selector"], timeout=5000)
        return await check_success_signals(page, scope="global")
    
    except playwright.TimeoutError:
        # 타임아웃 → 백오프 + 재시도
        raise NavigationError("Click timeout")
    
    except playwright.Error as e:
        # 요소 찾기 실패 → 스킵
        return ActionResult(success=False, message=f"Element error: {e}")
    
    except Exception as e:
        # 예상치 못한 오류 → 로그 + 롤백
        await logger.error(f"Unexpected error: {e}")
        await page.go_back()
        raise
```

### 7.3 상태 복구

```python
# main.py - run_actor()
async def run_actor(...):
    while not stop_event.is_set():
        try:
            # 정상 플로우
            await execute_cycle(...)
        
        except RateLimitError:
            # 레이트 제한 → 대기
            await asyncio.sleep(60)
        
        except NavigationError:
            # 탐색 실패 → 백오프 + 홈 복귀
            await with_backoff(page.goto, url=home_url)
        
        except StopSignalError:
            # Stop 플래그 → 즉시 종료
            break
        
        except Exception as e:
            # 기타 오류 → 로그 + 짧은 대기
            await logger.error(f"Cycle error: {e}")
            await asyncio.sleep(10)
```

---

## 8️⃣ 모듈 간 계약

### 8.1 호출 관계

```
main.py
  ↓ (프로필 설정)
executor.py
  ↓ (클릭 후보)
heuristics.py
  ↓ (스코어링 결과)
executor.py
  ↓ (액션 실행)
ai_brain.py (필요 시)
  ↓ (LLM 콘텐츠)
executor.py
  ↓ (성공/실패)
main.py
```

### 8.2 데이터 계약

| From | To | Data | Contract |
|------|----|----|----------|
| main.py | executor.py | ProfileConfig | actor_id, temperature, persona_file 필수 |
| executor.py | heuristics.py | List[Clickable] | selector, text, href 필수 |
| heuristics.py | executor.py | ScoredAction | total_score > 0, intent 명시 |
| executor.py | ai_brain.py | Persona, context | persona.tone, context.url 필수 |
| ai_brain.py | executor.py | PostContent/CommentContent | title+body 또는 comment 필수 |
| executor.py | main.py | ActionResult | success, state_after 필수 |

### 8.3 에러 전파

```python
# 에러 전파 규칙
1. executor.py → main.py:
   - FormError → 로그 + 스킵 (다음 사이클)
   - NavigationError → 백오프 + 재시도
   - RateLimitError → 대기
   - StopSignalError → 즉시 종료

2. ai_brain.py → executor.py:
   - LLMError → 로그 + 기본 콘텐츠 사용
   - FilterError → 재시도 (≤2회)

3. heuristics.py → executor.py:
   - ValueError → 로그 + 기본 액션 (홈 복귀)
```

---

## 📌 다음 단계

1. **Phase 1 구현**: main.py 스켈레톤 + executor.py 기초
2. **Phase 2 구현**: heuristics.py 스코어링 + 루프 방지
3. **Phase 3 구현**: executor.py 폼 처리 + 성공/실패 신호

---

**문서 승인**: ✅ Draft  
**관련 문서**: [@docs/PRD.md](PRD.md), [@docs/PLAN.md](PLAN.md), [@docs/RESOURCE.md](RESOURCE.md)
