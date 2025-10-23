# 자원 및 의존성

**버전**: v2.0 (압축)
**작성일**: 2025-10-23
**완전판**: `docs/archive/RESOURCE.md`

---

## requirements.txt

```
# Core
playwright>=1.40.0
python-dotenv>=1.0.0
pydantic>=2.0.0
aiohttp>=3.9.0
PyYAML>=6.0
httpx>=0.24.0

# LLM (1개 선택)
google-generativeai>=0.3.0  # 권장
# anthropic>=0.7.0
# openai>=1.3.0

# Logging
structlog>=23.1.0
python-json-logger>=2.0.0

# Utilities
requests>=2.31.0
rich>=13.5.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

---

## 환경변수 (.env)

```env
# Playwright
PLAYWRIGHT_HEADLESS=false
PLAYWRIGHT_TIMEOUT_MS=30000

# LLM (1개만)
GEMINI_API_KEY=xxx
# ANTHROPIC_API_KEY=xxx
# OPENAI_API_KEY=xxx

# 프로필
NUM_PROFILES=10  # 1~100

# 레이트
GLOBAL_READ_RPS=1
GLOBAL_WRITE_QPM=6
ACTOR_DEFAULT_LIMIT_PER_HOUR=2

# 상태
PROTECTION_WINDOW_SECONDS=60
LOOP_TTL_SECONDS=60
BACKOFF_MULTIPLIER=2
MAX_BACKOFF_SECONDS=16
MAX_RETRIES=5

# Anti-Bot
JITTER_MIN_SECONDS=2
JITTER_MAX_SECONDS=45

# 로깅
LOG_LEVEL=INFO
LOG_FORMAT=jsonl
```

---

## 폴더 구조

```
community-ai-bot/
├── .env
├── requirements.txt
├── main.py
├── executor.py
├── heuristics.py
├── ai_brain.py
├── creds.py
├── action_logger.py
├── metrics_collector.py
├── config/
│   ├── keywords.json
│   ├── profiles.yaml
│   ├── llm_api.yaml
│   └── personas/
│       ├── default.yaml
│       └── profile_NNN.yaml
├── profiles/
│   └── profile_NNN/
│       ├── session.json
│       ├── creds.json
│       └── persona.yaml
├── logs/
│   ├── actions_YYYYMMDD.jsonl
│   └── metrics_YYYYMMDD.json
└── tests/
```

---

## 설정 파일 스키마

### config/keywords.json
```json
{
  "cta_patterns": {
    "signup": {"text": [...], "url": [...]},
    "login": {"text": [...], "url": [...]}
  },
  "curiosity_patterns": {
    "post_view": [...],
    "pagination": [...]
  },
  "success_keywords": [...],
  "fail_keywords": [...]
}
```

### config/profiles.yaml
```yaml
num_profiles: 10
base_temperature: 0.5
temperature_variance: 0.4
base_hourly_limit: 2
```

### config/llm_api.yaml
```yaml
llm:
  provider: "gemini"
  gemini:
    model: "gemini-pro"
    api_key_env: "GEMINI_API_KEY"
    temperature: 0.5
    max_tokens: 500
```

### config/personas/default.yaml
```yaml
name: "Default"
tone: "friendly"
length: "medium"
topics: ["general", "tech"]
few_shot_style: "casual"
negative_phrases: ["광고", "스팸"]
```

---

## 로그 포맷

### logs/actions_YYYYMMDD.jsonl
```json
{
  "time": "ISO8601",
  "actor": "profile_001",
  "state": "UI_SCAN",
  "intent": "cta",
  "action": "click",
  "result": "ok",
  "latency_ms": 850
}
```

### logs/metrics_YYYYMMDD.json
```json
{
  "timestamp": "ISO8601",
  "throughput": {"total": 30},
  "errors": {"total": 1},
  "latency": {"p50_ms": 800, "p95_ms": 2100}
}
```

---

**참조**: [@docs/PRD.md](PRD.md), [@docs/PLAN.md](PLAN.md), [@docs/LLD.md](LLD.md)
