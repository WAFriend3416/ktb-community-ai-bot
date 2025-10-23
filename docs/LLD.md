# 저수준 설계 (LLD)

**버전**: v2.0 (압축)
**작성일**: 2025-10-23
**완전판**: `docs/archive/LLD.md`

---

## 컴포넌트 인터페이스

### main.py

```python
async def main() -> None:
    """메인 엔트리포인트"""

async def run_actor(
    actor_id: str,
    profile_config: ProfileConfig,
    global_state: GlobalState,
    stop_event: asyncio.Event
) -> None:
    """단일 프로필 루프"""

class RateLimiter:
    async def acquire_read() -> bool
    async def acquire_write(actor_id: str) -> bool

class StopController:
    def signal_stop_all() -> None
    def signal_stop_actor(actor_id: str) -> None
    def should_stop(actor_id: str) -> bool
```

---

### executor.py

```python
class Executor:
    async def __init__(profile_id: str, profile_config: ProfileConfig)

    async def collect_clickables() -> List[Clickable]
    async def check_login_status() -> bool

    async def handle_auth_form(
        state: Literal["SIGN_UP", "LOGIN"],
        creds: Optional[Credentials]
    ) -> ActionResult

    async def handle_write_form(
        action_type: Literal["WRITE_POST", "WRITE_COMMENT"],
        context: Dict[str, Any]
    ) -> ActionResult

    async def wait_for_action_effect(
        action_type: str,
        timeout: int = 2500
    ) -> bool

# 헬퍼
async def form_scope_from_submit(page: Page) -> Optional[Locator]

async def check_success_signals(
    page: Page,
    form: Locator,
    scope: Literal["inline", "global"]
) -> Tuple[bool, str]
```

---

### heuristics.py

```python
def score_cta(
    clickable: Clickable,
    keywords: CTAKeywords,
    is_logged_in: bool
) -> float

def score_curiosity(
    clickable: Clickable,
    patterns: CuriosityPatterns
) -> float

def select_top_candidates(
    scored_actions: List[ScoredAction],
    top_n: int = 3
) -> ScoredAction

def normalize_text(text: str) -> str
def loop_key(clickable: Clickable) -> str
```

---

### ai_brain.py

```python
async def generate_content(
    persona: Persona,
    context: Dict[str, Any],
    action_type: Literal["WRITE_POST", "WRITE_COMMENT"]
) -> Union[PostContent, CommentContent]
```

---

### creds.py

```python
def generate_new_credentials(actor_id: str) -> Credentials
def save_creds(profile_id: str, creds: Credentials) -> None
def load_creds(profile_id: str) -> Optional[Credentials]
```

---

### action_logger.py

```python
async def log_action(
    actor_id: str,
    state_before: str,
    intent: Literal["cta", "curiosity"],
    action: Literal["click", "type", "submit"],
    result: ActionResult,
    **kwargs
) -> None
```

---

### metrics_collector.py

```python
class MetricsCollector:
    def record_action(actor_id: str, latency_ms: int) -> None
    def record_error(error_type: str) -> None
    def snapshot() -> MetricsSnapshot
```

---

## 데이터 구조

```python
from typing import TypedDict, Literal, Optional, Dict, List, Any

# 프로필
class ProfileConfig(TypedDict):
    actor_id: str
    temperature: float
    max_hourly_actions: int
    persona_file: str

class Persona(TypedDict):
    tone: str
    length: str
    topics: List[str]
    few_shot_style: str
    negative_phrases: List[str]

# UI
class Clickable(TypedDict):
    selector: str
    text: str
    href: Optional[str]
    role: Optional[str]
    is_visible: bool

class ScoredAction(TypedDict):
    clickable: Clickable
    total_score: float
    intent: Literal["cta", "curiosity"]

# 크레덴셜
class Credentials(TypedDict):
    email: str
    username: str
    password: str

# 결과
class ActionResult(TypedDict):
    success: bool
    state_after: str
    message: str
    url_after: str
    latency_ms: int

# LLM
class PostContent(TypedDict):
    title: str
    body: str

class CommentContent(TypedDict):
    comment: str

# 전역
class GlobalState(TypedDict):
    rate_limiter: Any
    stop_controller: Any
    protection_windows: Dict[str, datetime]
    metrics_collector: Any
```

---

## Literal/Enum

```python
State = Literal[
    "START", "UI_SCAN", "SIGN_UP", "LOGIN",
    "ACTION_HUB", "WRITE_POST", "WRITE_COMMENT", "EXPLORE"
]

ActionType = Literal["click", "type", "submit"]
Intent = Literal["cta", "curiosity"]
Result = Literal["ok", "inline_fail", "fail", "rate_limited"]
```

---

**참조**: [@docs/PRD.md](PRD.md), [@docs/PLAN.md](PLAN.md), [@docs/RESOURCE.md](RESOURCE.md)
