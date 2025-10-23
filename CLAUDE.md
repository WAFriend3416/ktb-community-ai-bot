# CLAUDE.md

## Project Documents
@docs/PRD.md
@docs/PLAN.md
@docs/RESOURCE.md
@docs/LLD.md

프로젝트 목표 : 커뮤니티 URL만 입력하면, AI 에이전트가 스스로 회원가입부터 LLM을 이용한 글/댓글 작성까지 사람처럼 수행하는 자동화 시스템을 구축하는 것
프로젝트 핵심 : 규칙 기반(Clickable-First) 탐색의 안정성과 봇 탐지 회피 기술(운영 강화)을 결합하여, 실제 환경에서도 견고하게 작동하는 하이브리드 AI를 구현

## 문서 개요

### 📋 PRD.md (v1.6.1)
**요구사항 명세서** - 상태머신 플로우, 기능 요구사항 (FR1-FR13), 비기능 요구사항 (NFR), QA 시나리오, 수용 기준
- v1.6.1: 휴리스틱 테이블 강화 (CTA 키워드 확장, CSS 셀렉터 문법 수정, 접근성 속성 추가)

### 🎯 PLAN.md (v2.0)
**구현 계획** - 8개 단계 로드맵, 컴포넌트 맵, 우선순위
- v2.0: "Phase" → "단계"로 변경, 단계별 요약 추가
- v1.1: 중복 제거 (40% 감소), 다른 문서로 참조 이동

### 📦 RESOURCE.md (v1.2)
**자원 & 의존성** - Python 라이브러리, 환경변수 설정, 폴더 구조, 설정 파일 사양
- v1.2: 중복 제거 (10% 감소), 문서 간 상호 참조 추가

### 🏗️ LLD.md (v1.1)
**저수준 설계** - 핵심 컴포넌트 인터페이스, 데이터 구조 (TypedDict), 동시성 패턴 (asyncio), 에러 처리
- v1.1: 중복 제거 (15% 감소), 개요 부분 PRD 참조로 변경

## 완료된 작업

### 🔧 설계 결정사항
- ✅ **프로필 확장성**: 3개 고정 → 1~100개 동적 생성 (환경변수 `NUM_PROFILES`)
- ✅ **LLM API 공통화**: 프로필별 모델 → 공통 1개 API (Gemini/Claude/OpenAI)
- ✅ **다양성 확보**: Temperature 변화(0.5-0.9), Persona, Few-shot으로 프로필 개성 유지
- ✅ **문서 최적화**: 중복 내용 ~25% 감소, SSOT(Single Source of Truth) 원칙 적용
- ✅ **휴리스틱 정교화**: 모호한 키워드 제거, CSS 문법 표준 준수, 접근성 속성 추가

### 📚 문서 구조 (SSOT 원칙)
- **PRD.md**: 요구사항 정의 (프로젝트 목표, 아키텍처 전략, 수용 기준) ← SSOT
- **PLAN.md**: 구현 계획 (8단계 로드맵, 우선순위) → PRD, LLD, RESOURCE 참조
- **RESOURCE.md**: 자원 명세 (의존성, 설정 파일, 환경변수) ← SSOT for configs
- **LLD.md**: 설계 상세 (인터페이스, 데이터 구조, 동시성) ← SSOT for design

### 🔄 문서 간 참조 관계
```
CLAUDE.md (진입점)
  ├── PRD.md (요구사항, SSOT for goals/AC)
  │     ↑ 참조: PLAN.md, LLD.md, RESOURCE.md
  ├── PLAN.md (구현 계획)
  │     → 참조: PRD.md, LLD.md, RESOURCE.md
  ├── RESOURCE.md (자원 명세)
  │     → 참조: PLAN.md, LLD.md
  ├── LLD.md (설계 상세)
  │     → 참조: PRD.md, PLAN.md, RESOURCE.md
```

## 다음 단계

### 1단계: 기초 인프라 구현 (예정)
**요약**: 프로젝트 기본 설정, N개 프로필 동시 실행 코루틴, Playwright 세션 관리, 클릭 요소 수집 & 스코어링

- [ ] requirements.txt 작성
- [ ] .env.example 생성
- [ ] config/keywords.json 작성
- [ ] config/profiles.yaml 작성 (동적 생성 스키마)
- [ ] config/llm_api.yaml 작성 (공통 API)
- [ ] main.py 스켈레톤 (N 프로필 코루틴)
- [ ] executor.py 기초 (Playwright 세션)
- [ ] heuristics.py 기초 (스코어링)



