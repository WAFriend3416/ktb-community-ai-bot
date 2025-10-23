# 자원 및 의존성 (Resource & Dependencies)

**문서 버전**: v1.2 (중복 제거: 2025-10-23)  
**기준**: PRD v1.6 + PLAN.md v1.1 (N 프로필, 공통 LLM API)

**구현 계획**: [@docs/PLAN.md](PLAN.md) 참조  
**설계 상세**: [@docs/LLD.md](LLD.md) 참조  
**작성일**: 2025-10-23  
**수정**: 2025-10-23 (프로필 확장성 & LLM API 공통화)

---

## 📦 Python 의존성

### 1. 핵심 라이브러리

| 라이브러리 | 버전 | 목적 | 설치 |
|-----------|------|------|------|
| **playwright** | >=1.40.0 | UI 자동화, 세션 관리 | `pip install playwright` |
| **python-dotenv** | >=1.0.0 | 환경변수 관리 (.env) | `pip install python-dotenv` |
| **pydantic** | >=2.0.0 | 설정 검증 & 직렬화 | `pip install pydantic` |
| **aiohttp** | >=3.9.0 | 비동기 HTTP (API 응답 모니터링) | `pip install aiohttp` |
| **PyYAML** | >=6.0 | YAML 파싱 (프로필, 페르소나) | `pip install PyYAML` |

### 2. LLM 공급자 SDK (공통, 1개만 선택)

**공통 LLM API를 사용합니다. 아래 3개 중 1개만 선택하여 설치하세요:**

| SDK | 버전 | 모델 | 설치 | 비용 |
|-----|------|------|------|------|
| **google-generativeai** | >=0.3.0 | Gemini | `pip install google-generativeai` | ✅ 권장 (무료 tier) |
| **anthropic** | >=0.7.0 | Claude 3 | `pip install anthropic` | 유료 (높은 품질) |
| **openai** | >=1.3.0 | GPT-4 | `pip install openai` | 유료 (대안) |

**설계 원칙**: 
- 모든 프로필(1~100개)은 **동일한 LLM API** 사용
- 프로필별 다양성은 **persona/temperature/few-shot**으로 확보
- API 비용 예측 가능 & 관리 용이

### 3. 로깅 & 모니터링

| 라이브러리 | 버전 | 목적 | 설치 |
|-----------|------|------|------|
| **structlog** | >=23.1.0 | 구조화된 JSON 로깅 | `pip install structlog` |
| **python-json-logger** | >=2.0.0 | JSONL 출력 | `pip install python-json-logger` |

### 4. 유틸리티

| 라이브러리 | 버전 | 목적 | 설치 |
|-----------|------|------|------|
| **requests** | >=2.31.0 | HTTP 클라이언트 (fallback) | `pip install requests` |
| **httpx** | >=0.24.0 | 비동기 HTTP (대체) | `pip install httpx` |
| **rich** | >=13.5.0 | CLI 출력 포매팅 | `pip install rich` |

### 5. 테스트 (Phase 8)

| 라이브러리 | 버전 | 목적 | 설치 |
|-----------|------|------|------|
| **pytest** | >=7.4.0 | 테스트 프레임워크 | `pip install pytest` |
| **pytest-asyncio** | >=0.21.0 | 비동기 테스트 | `pip install pytest-asyncio` |
| **pytest-cov** | >=4.1.0 | 커버리지 분석 | `pip install pytest-cov` |

---

## 📋 requirements.txt

```
# Core
playwright>=1.40.0
python-dotenv>=1.0.0
pydantic>=2.0.0
aiohttp>=3.9.0
PyYAML>=6.0
httpx>=0.24.0

# LLM Provider (선택: 1개만)
# 다음 중 1개만 주석 해제:
google-generativeai>=0.3.0
# anthropic>=0.7.0
# openai>=1.3.0

# Logging
structlog>=23.1.0
python-json-logger>=2.0.0

# Utilities
requests>=2.31.0
rich>=13.5.0

# Testing (optional)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

---

## 🔧 환경변수 (.env)

필수 설정값:

```env
# Playwright
PLAYWRIGHT_HEADLESS=false          # 개발 시 true → headless mode
PLAYWRIGHT_TIMEOUT_MS=30000        # 페이지 로딩 타임아웃 (ms)
PLAYWRIGHT_SLOW_MO_MS=0           # 개발 디버깅 시 지연 (ms)

# LLM API (공통 설정, 1개만)
# Google Gemini 사용 시:
GEMINI_API_KEY=xxx
# 또는 Anthropic Claude 사용 시:
# ANTHROPIC_API_KEY=xxx
# 또는 OpenAI 사용 시:
# OPENAI_API_KEY=xxx

# 프로필 설정
NUM_PROFILES=10                   # 프로필 개수 (1~100)
PROFILE_ID_FORMAT="profile_{:03d}" # 프로필 ID 포맷 (profile_001, profile_002, ...)

# 레이트 리미터 (PRD FR6)
GLOBAL_READ_RPS=1                # 전역 읽기 1 QPS
GLOBAL_WRITE_QPM=6               # 전역 쓰기 6 QPM
ACTOR_DEFAULT_LIMIT_PER_HOUR=2   # 기본 프로필 상한: 2/h (조정 가능)

# 상태 관리
PROTECTION_WINDOW_SECONDS=60      # 로그인 직후 보호창 (s)
RECHECK_LOGIN_INTERVAL=3          # N사이클마다 로그인 재검사
LOOP_TTL_SECONDS=60               # 루프 방지 TTL (s)
BACKOFF_MULTIPLIER=2              # 지수 백오프 계수
MAX_BACKOFF_SECONDS=16            # 최대 백오프 (s)
MAX_RETRIES=5                     # 최대 재시도 횟수

# Anti-Bot
JITTER_MIN_SECONDS=2              # Jitter 최소 (s)
JITTER_MAX_SECONDS=45             # Jitter 최대 (s)

# 로깅
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=jsonl                  # jsonl or text
METRICS_INTERVAL_SECONDS=300      # 메트릭 주기 (s)

# 개발/테스트
DEBUG_MODE=false                  # 상세 디버그 출력
TEST_COMMUNITY_URL=https://example.com  # 테스트 대상 URL
```

---

## 📁 프로젝트 폴더 구조 (N 프로필, 1~100개)

```
community-ai-bot/
│
├── .env                          # 환경변수 (gitignore)
├── .env.example                  # 환경변수 템플릿
├── requirements.txt              # Python 의존성
├── pyproject.toml                # (선택) Poetry 설정
│
├── main.py                       # 오케스트레이터 (N 프로필 동적 실행)
├── executor.py                   # Playwright 실행자
├── heuristics.py                 # 스코어링 휴리스틱
├── ai_brain.py                   # LLM 어댑터 (공통 API)
├── creds.py                      # 크레덴셜 관리
├── action_logger.py              # JSONL 로깅
├── metrics_collector.py           # 메트릭 수집
│
├── config/
│   ├── keywords.json             # CTA/성공/실패 키워드
│   ├── profiles.yaml             # 프로필 생성 스키마 (동적)
│   ├── llm_api.yaml              # 공통 LLM API 설정
│   └── personas/
│       ├── default.yaml          # 기본 페르소나 템플릿
│       ├── profile_001.yaml      # 프로필 1 페르소나
│       ├── profile_002.yaml      # 프로필 2 페르소나
│       └── ...                   # profile_NNN.yaml (1~100)
│
├── profiles/                      # 프로필 상태 (런타임, N개 동적)
│   ├── profile_001/
│   │   ├── session.json          # Playwright 세션 (자동 생성)
│   │   ├── creds.json            # 크레덴셜 (자동 생성)
│   │   └── persona.yaml          # 페르소나 (캐시)
│   ├── profile_002/
│   │   └── ... (동일 구조)
│   └── ...                       # profile_NNN/
│
├── logs/
│   ├── actions_20251023.jsonl    # 액션 로그 (일별)
│   ├── metrics_20251023.json     # 메트릭 (일별)
│   └── error.log                 # 에러 로그
│
├── tests/                        # QA 테스트 (Phase 8)
│   ├── test_executor.py
│   ├── test_heuristics.py
│   ├── test_ai_brain.py
│   └── test_integration.py
│
├── docs/
│   ├── PRD.md                    # 요구사항 명세
│   ├── PLAN.md                   # 구현 계획
│   └── RESOURCE.md               # 이 파일
│
├── scripts/                      # 유틸리티 스크립트
│   ├── setup_playwright.py       # Playwright 브라우저 설치
│   ├── init_profiles.py          # 프로필 초기화 (N개 생성)
│   └── test_run.py               # 수동 테스트 실행
│
└── .gitignore                    # Git 무시 목록
```

---

## 🎯 config/ 파일 사양

### 1. config/keywords.json

```json
{
  "cta_patterns": {
    "signup": {
      "text": ["회원가입", "가입", "계정 생성", "Sign up", "Create account", "Join now"],
      "url": ["/signup", "/register", "/join", "/users/sign_up"]
    },
    "login": {
      "text": ["로그인", "Sign in", "Log in", "Continue", "로그인하기"],
      "url": ["/login", "/signin", "/session", "/users/sign_in"]
    },
    "logout": {
      "text": ["로그아웃", "Sign out", "Logout"],
      "url": ["/logout", "/sign_out"]
    },
    "write_post": {
      "text": ["글쓰기", "새 글", "작성", "Publish", "Write Post"],
      "url": ["/new", "/write", "/post/new", "/posts/new", "/compose"]
    },
    "comment": {
      "text": ["댓글", "답글", "Comment", "Reply", "Add comment"],
      "url": ["/comment", "#comment", "/replies", "/comments"]
    }
  },
  "curiosity_patterns": {
    "post_view": ["/post/", "/posts/", "/view/", "/entry/", "/topic/"],
    "pagination": ["?page=", "/page/", "/p/"],
    "like": ["/like", "/vote", "/upvote"],
    "follow": ["/follow", "/subscribe"]
  },
  "success_keywords": [
    "환영합니다", "성공", "로그인되었습니다", "작성되었습니다", 
    "등록됨", "완료", "posted", "published", "saved",
    "로그인 성공", "가입 완료"
  ],
  "fail_keywords": [
    "에러", "오류", "실패", "비밀번호가 틀렸습니다", 
    "필수 항목", "중복된", "이미 사용", "error", "failed", "invalid", "required",
    "8자 이상", "특수문자", "최소/최대", "형식/포맷", "too short", "weak", "mismatch"
  ],
  "banned_words": [
    "광고", "스팸", "성인", "폭력", "테스트", "봇", "자동",
    "광고주", "마케팅", "홍보", "판매"
  ]
}
```

### 2. config/profiles.yaml (동적 프로필 생성 스키마)

```yaml
# 프로필 생성 규칙 (NUM_PROFILES 환경변수로 개수 결정)
profiles:
  # 동적 생성: profile_001, profile_002, ..., profile_NNN
  # 각 프로필은 다음 구조를 자동으로 생성:
  # 
  # profile_XXX:
  #   name: "Profile XXX"
  #   actor_id: "profile_XXX"
  #   temperature: 0.5 + random(0, 0.4)  # 0.5 ~ 0.9 범위에서 무작위
  #   max_hourly_actions: 2  # 프로필별 기본값
  #   persona_file: "personas/profile_XXX.yaml"
  
# 프로필 생성 파라미터
num_profiles: 10  # 또는 환경변수 NUM_PROFILES로 오버라이드
base_temperature: 0.5  # 기본 온도
temperature_variance: 0.4  # 온도 편차 (±)
base_hourly_limit: 2  # 기본 시간당 액션 상한
profile_id_format: "profile_{:03d}"  # 프로필 ID 포맷
```

### 3. config/llm_api.yaml (공통 LLM API 설정)

```yaml
# 공통 LLM API 설정 (모든 프로필이 사용)
llm:
  # 사용할 LLM 공급자 선택: gemini, claude, openai
  provider: "gemini"  # 환경변수로 오버라이드 가능
  
  # Gemini 설정
  gemini:
    model: "gemini-pro"
    api_key_env: "GEMINI_API_KEY"
    temperature: 0.5  # 기본값 (프로필별로 override)
    max_tokens: 500
    top_p: 0.9
    top_k: 40
    timeout_seconds: 30
    retry_count: 2
  
  # Claude 설정
  claude:
    model: "claude-3-haiku"  # haiku (빠름), sonnet, opus
    api_key_env: "ANTHROPIC_API_KEY"
    temperature: 0.5
    max_tokens: 500
    timeout_seconds: 30
    retry_count: 2
  
  # OpenAI 설정
  openai:
    model: "gpt-4-turbo"  # gpt-4-turbo, gpt-4, gpt-3.5-turbo
    api_key_env: "OPENAI_API_KEY"
    temperature: 0.5
    max_tokens: 500
    timeout_seconds: 30
    retry_count: 2
```

### 4. config/personas/default.yaml (기본 페르소나 템플릿)

```yaml
name: "Default Persona"
tone: "friendly"
length: "medium"
topics: ["general", "tech", "life"]
few_shot_style: "casual"
negative_phrases:
  - "광고"
  - "스팸"
  - "구매해야"
  - "지금 가입하세요"
min_length: 50
max_length: 500
sampling_params:
  top_k: 40
  top_p: 0.9
  presence_penalty: 0.2
  frequency_penalty: 0.1
```

### 5. config/personas/profile_001.yaml (프로필 별 개성)

```yaml
name: "Alice"
tone: "friendly_and_curious"
length: "medium"
topics: ["tech", "design", "productivity"]
few_shot_style: "casual_expert"
negative_phrases:
  - "광고"
  - "스팸"
  - "구매해야"
min_length: 50
max_length: 500
sampling_params:
  top_k: 40
  top_p: 0.95  # 좀 더 창의적
  presence_penalty: 0.1  # 더 다양한 표현
  frequency_penalty: 0.2
```

---

## 🔐 크레덴셜 관리 (profiles/<profile_id>/creds.json)

```json
{
  "actor_id": "profile_001",
  "created_at": "2025-10-23T10:00:00Z",
  "email": "profile_001_test_20251023@example.com",
  "username": "profile_001_user_autumn_2025",
  "password": "SecureP@ssw0rd123!",
  "signup_url": "https://example.com/signup",
  "signup_timestamp": "2025-10-23T10:05:00Z",
  "status": "verified"
}
```

---

## 📊 로그 포맷 (logs/actions_YYYYMMDD.jsonl)

```json
{
  "timestamp": "2025-10-23T10:05:30.123Z",
  "actor_id": "profile_001",
  "state_before": "UI_SCAN",
  "intent": "cta",
  "action": "click",
  "scope": "global",
  "selector": "button[data-testid='signup-btn']",
  "text": "회원가입",
  "url_before": "https://example.com/",
  "url_after": "https://example.com/signup",
  "result": "ok",
  "latency_ms": 850,
  "network_signals": ["url_changed"],
  "login_proof": [],
  "llm_profile": "profile_001",
  "anti_bot_actions": ["ua_randomized", "jitter_applied"],
  "note": "Successfully navigated to signup page"
}
```

---

## 📈 메트릭 (logs/metrics_YYYYMMDD.json)

```json
{
  "timestamp": "2025-10-23T10:30:00Z",
  "period_seconds": 300,
  "throughput": {
    "total_actions": 30,
    "actions_per_profile": {
      "profile_001": 3,
      "profile_002": 3,
      "profile_003": 3,
      "...": "..."
    }
  },
  "errors": {
    "total": 1,
    "by_type": {
      "timeout": 1,
      "navigation_failed": 0,
      "llm_error": 0
    }
  },
  "rate_limited": {
    "global_read": 0,
    "global_write": 0,
    "profile_limited": 0
  },
  "latency": {
    "p50_ms": 800,
    "p95_ms": 2100,
    "p99_ms": 2800
  },
  "dedup_blocked": 2,
  "loop_blocked": 1,
  "api_success_rate": 0.95
}
```

---

## 🛠️ 초기 설정 체크리스트

### 1. 환경 준비
- [ ] Python 3.9+ 설치
- [ ] 프로젝트 폴더 생성
- [ ] `pip install -r requirements.txt`
- [ ] Playwright 브라우저: `python -m playwright install`

### 2. 설정 파일
- [ ] `.env` 생성 (`.env.example` 기반)
- [ ] LLM API Key 설정 (Gemini, Claude, 또는 OpenAI 중 1개)
- [ ] `NUM_PROFILES` 환경변수 설정 (예: 10)

### 3. 프로필 생성
- [ ] `python scripts/init_profiles.py` 실행
  - config/profiles.yaml 기반으로 N개 프로필 폴더 생성
  - config/personas/profile_*.yaml 생성
  - profiles/profile_*/creds.json 준비

### 4. 검증
- [ ] `python -c "import main; print('Ready')"` ✅
- [ ] `python -m pytest tests/ -v` (모든 테스트 통과)
- [ ] 로그 디렉토리 권한 확인: `ls -la logs/`

---

## 💾 저장소 제약

### Git Ignore 권장

```gitignore
# 환경 & 크레덴셜
.env
.env.local
.env.*.local
profiles/*/creds.json

# 런타임
logs/
profiles/*/session.json
*.pyc
__pycache__/
.pytest_cache/
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## 🚀 배포 체크리스트

- [ ] 모든 테스트 통과 (`pytest`)
- [ ] 코드 스타일 검증 (선택사항)
- [ ] 환경변수 검증 (필수 항목 모두 설정)
- [ ] 로그 디렉토리 권한 확인
- [ ] 메모리 & CPU 제약 확인 (동시 N Playwright 세션)
- [ ] 네트워크 안정성 확인 (LLM API + 대상 커뮤니티)
- [ ] 에러 알림 설정 (선택사항)

---

## 📊 성능 고려사항

### 동시 프로필 실행 (N 프로필)

| 프로필 수 | 권장 메모리 | 권장 CPU | 주의사항 |
|----------|----------|--------|---------|
| 1~5 | 4 GB | 2 cores | 개발/테스트 |
| 6~20 | 8 GB | 4 cores | 일반적 운영 |
| 21~50 | 16 GB | 8 cores | 고부하 운영 |
| 51~100 | 32 GB | 16 cores | 대규모 운영 |

**주의**: Playwright는 각 세션마다 ~100-150MB 메모리 사용

### API 비용 예측 (공통 LLM API 기준)

예: Gemini 무료 tier (월 60회 요청 제한)

```
프로필 수: 10
시간당 액션: 10 × 2 = 20 액션
일일 액션: 20 × 24 = 480 액션
월간 액션: 480 × 30 = 14,400 액션
LLM 호출: 14,400 × 0.5 = 7,200회 (게시글/댓글만)
월간 비용: 무료 (Gemini) / ~$7-20 (Claude/GPT-4)
```

---

## 📚 참고 자료

| 주제 | 문서 |
|------|------|
| Playwright 공식 | https://playwright.dev/python/ |
| Google Gemini API | https://ai.google.dev/tutorials/python_quickstart |
| Anthropic Claude | https://docs.anthropic.com/en/docs/getting-started/quickstart-guide |
| OpenAI API | https://platform.openai.com/docs/guides/gpt-4 |
| Async Python | https://docs.python.org/3/library/asyncio.html |

---

---

**관련 문서**:  
- 요구사항: [@docs/PRD.md](PRD.md)  
- 구현 계획: [@docs/PLAN.md](PLAN.md)  
- 설계 상세: [@docs/LLD.md](LLD.md)

**프로젝트 시작**: 초기 설정 체크리스트를 완료하세요.
