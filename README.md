# Community AI Bot

커뮤니티 URL만 입력하면 AI 에이전트가 자동으로 회원가입, 로그인, 글/댓글 작성을 수행하는 자동화 시스템

## 🚀 빠른 시작

### 1. 가상환경 생성 (권장)

```bash
# 가상환경 생성
python -m venv venv

# 활성화
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 2. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 3. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 편집 (선택사항)
# - GEMINI_API_KEY는 4단계부터 필요
# - NUM_PROFILES: 동시 실행 프로필 수 (1~100)
```

### 4. 실행

```bash
python main.py
```

**입력 예시:**
```
타겟 커뮤니티 URL: https://news.ycombinator.com
```

---

## 📋 구현 현황

### ✅ 1단계: 기초 인프라 (완료)
- [x] N개 프로필 동시 실행 (asyncio)
- [x] Playwright 세션 관리
- [x] 클릭 요소 수집 & 스코어링
- [x] 레이트 리미팅 (1 RPS 읽기, 6 QPM 쓰기)

### 🚧 다음 단계
- 2단계: 탐색 & 안정성 (루프 방지, 백오프, Anti-Bot)
- 3단계: 폼 처리 (회원가입, 로그인, 글쓰기)
- 4단계: AI 콘텐츠 생성 (LLM 통합)

---

## ⚠️ 의존성 충돌 해결

### 문제: FastAPI/Starlette anyio 충돌

**증상:**
```
fastapi 0.104.1 has requirement anyio<4.0.0,>=3.7.1, but you have anyio 4.0.0
```

**원인:**
- 이 프로젝트는 FastAPI를 사용하지 않음
- FastAPI가 다른 프로젝트/시스템 패키지로 설치됨
- Playwright는 anyio 4.x 권장, FastAPI 0.104.x는 anyio <4.0.0 요구

**해결 방법:**

#### 방법 1: 가상환경 사용 (권장) ⭐

```bash
# 1. 새 가상환경 생성
python -m venv venv

# 2. 활성화
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 4. 확인
pip check
# "No broken requirements found." 출력되어야 함
```

#### 방법 2: FastAPI 업그레이드

```bash
# FastAPI 0.109.0+는 anyio 4.x 지원
pip install --upgrade "fastapi>=0.109.0" "starlette>=0.29.0"
```

#### 방법 3: anyio 다운그레이드 (비권장)

```bash
# Playwright 성능 저하 가능
pip install "anyio>=3.7.1,<4.0.0"
```

---

## 📂 프로젝트 구조

```
community-ai-bot/
├── main.py              # 메인 엔트리포인트
├── executor.py          # Playwright 실행 엔진
├── heuristics.py        # 스코어링 로직
├── requirements.txt     # Python 의존성
├── .env.example         # 환경변수 템플릿
├── config/
│   ├── keywords.json    # CTA/Curiosity 키워드
│   ├── profiles.yaml    # 프로필 설정
│   ├── llm_api.yaml     # LLM API 설정
│   └── personas/
│       └── default.yaml # 기본 페르소나
├── profiles/            # 프로필별 세션 (런타임 생성)
├── logs/                # 로그 파일 (런타임 생성)
└── docs/
    ├── PRD.md          # 요구사항 명세
    ├── PLAN.md         # 구현 계획
    ├── RESOURCE.md     # 자원 & 의존성
    └── LLD.md          # 저수준 설계
```

---

## 🛠️ 기술 스택

- **Python 3.9+**: 비동기 프로그래밍
- **Playwright**: 브라우저 자동화
- **asyncio**: N개 프로필 동시 실행
- **Gemini API**: LLM 기반 콘텐츠 생성 (4단계부터)

---

## 📖 문서

자세한 내용은 [CLAUDE.md](CLAUDE.md) 및 `docs/` 디렉토리 참조

- [PRD.md](docs/PRD.md): 기능 요구사항 (FR1-FR13)
- [PLAN.md](docs/PLAN.md): 8단계 구현 로드맵
- [RESOURCE.md](docs/RESOURCE.md): 의존성 & 환경변수
- [LLD.md](docs/LLD.md): 컴포넌트 인터페이스

---

## 🔒 주의사항

- **봇 탐지**: 실제 커뮤니티에서 사용 시 계정 차단 가능
- **레이트 제한**: 기본 설정 (1 RPS 읽기, 6 QPM 쓰기) 준수
- **테스트 환경**: 개발/테스트 환경에서만 사용 권장

---

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로만 사용해야 합니다.
