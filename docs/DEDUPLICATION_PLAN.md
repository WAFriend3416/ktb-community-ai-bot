# 문서 중복 제거 계획 (Deduplication Plan)

**작성일**: 2025-10-23  
**버전**: v1.0  
**상태**: ✅ 분석 완료 → 실행 대기

---

## 📊 중복 내용 분석 결과

### 1. 프로젝트 개요/목표
**중복 위치**:
- ❌ PRD.md Section 0 (상세 버전)
- ❌ PLAN.md 프로젝트 개요 (요약 버전)
- ❌ LLD.md 개요 (간략 버전)

**Single Source of Truth**: **PRD.md** (요구사항 문서가 프로젝트 목표 소유)

**조치**:
- PRD.md: 유지 (상세 버전)
- PLAN.md: → `@docs/PRD.md#목적-범위` 참조로 변경
- LLD.md: → `@docs/PRD.md#목적-범위` 참조로 변경

---

### 2. 아키텍처 전략 (Clickable-First + Hybrid AI + Anti-Bot)
**중복 위치**:
- ❌ PRD.md Section 0 (요구사항)
- ❌ PLAN.md 프로젝트 개요 (구현 전략)

**Single Source of Truth**: **PRD.md** (아키텍처는 요구사항의 일부)

**조치**:
- PRD.md: 유지
- PLAN.md: → `@docs/PRD.md#목적-범위` 참조로 변경

---

### 3. 컴포넌트 책임 (main.py, executor.py, heuristics.py, ai_brain.py)
**중복 위치**:
- ❌ PRD.md Section 2 (고수준 책임)
- ❌ PLAN.md Phase 설명 (구현 계획)
- ❌ LLD.md Section 1-4 (상세 인터페이스)

**Single Source of Truth**: 
- **PRD.md** = 고수준 책임 (WHAT)
- **LLD.md** = 상세 인터페이스 (HOW)

**조치**:
- PRD.md: 유지 (간략한 책임 설명만)
- LLD.md: 유지 (상세 인터페이스)
- PLAN.md: → `@docs/PRD.md#구성요소-책임` + `@docs/LLD.md` 참조로 변경

---

### 4. 데이터 구조 (TypedDict 정의)
**중복 위치**:
- ❌ LLD.md Section 5.1 (완전한 정의)
- ❌ PLAN.md Phase 3-4 (부분 참조)
- ❌ PRD.md Section 2 (의사코드 내 암시적 구조)

**Single Source of Truth**: **LLD.md** (설계 문서가 데이터 구조 소유)

**조치**:
- LLD.md: 유지 (완전한 정의)
- PLAN.md: → `@docs/LLD.md#데이터-구조-총정리` 참조로 변경
- PRD.md: 유지 (의사코드는 요구사항의 일부)

---

### 5. 수용 기준 (Acceptance Criteria)
**중복 위치**:
- ❌ PRD.md Section 7 (완전한 체크리스트)
- ❌ PLAN.md 완료 기준 (동일 체크리스트)

**Single Source of Truth**: **PRD.md** (수용 기준은 요구사항의 일부)

**조치**:
- PRD.md: 유지
- PLAN.md: → `@docs/PRD.md#수용-기준` 참조로 변경

---

### 6. 설정 파일 예제 (keywords.json, profiles.yaml, llm_api.yaml)
**중복 위치**:
- ❌ RESOURCE.md Section 4 (완전한 YAML/JSON)
- ❌ PLAN.md Phase 1 (간략한 언급)

**Single Source of Truth**: **RESOURCE.md** (자원 문서가 설정 소유)

**조치**:
- RESOURCE.md: 유지 (완전한 예제)
- PLAN.md: → `@docs/RESOURCE.md#config-파일-사양` 참조로 변경

---

### 7. 레이트 리미터 값 (1 QPS, 6 QPM, etc.)
**중복 위치**:
- ❌ PRD.md Section 9 (운영 파라미터)
- ❌ RESOURCE.md .env (환경변수)
- ❌ PLAN.md Phase 1 (간략 언급)

**Single Source of Truth**: 
- **PRD.md** = 요구사항 (기본값)
- **RESOURCE.md** = 배포 설정 (실제 사용값)

**조치**:
- PRD.md: 유지 (요구사항으로서의 기본값)
- RESOURCE.md: 유지 (환경변수 형태)
- PLAN.md: → `@docs/PRD.md#운영-파라미터` 참조로 변경

---

### 8. 프로필 확장성 설계 (1-100 profiles, common LLM API)
**중복 위치**:
- ❌ PLAN.md Phase 1, Phase 4 (구현 접근법)
- ❌ RESOURCE.md profiles.yaml, llm_api.yaml (설정 스키마)

**Single Source of Truth**:
- **PLAN.md** = 설계 접근법
- **RESOURCE.md** = 구체적 설정

**조치**:
- PLAN.md: 유지 (설계 접근법)
- RESOURCE.md: 유지 (설정 스키마)
- 중복 최소화: PLAN.md에서 상세 YAML 제거, RESOURCE.md 참조만

---

### 9. 폴더 구조
**중복 위치**:
- ❌ PLAN.md 구성요소 맵 (완전한 트리)
- ❌ RESOURCE.md 프로젝트 폴더 구조 (동일 트리)

**Single Source of Truth**: **RESOURCE.md** (인프라 문서가 폴더 구조 소유)

**조치**:
- RESOURCE.md: 유지 (완전한 트리)
- PLAN.md: → `@docs/RESOURCE.md#프로젝트-폴더-구조` 참조로 변경

---

### 10. 로그/메트릭 포맷 (JSONL 예제)
**중복 위치**:
- ❌ PRD.md Section 7 (간략 설명)
- ❌ RESOURCE.md Section (완전한 JSON 예제)
- ❌ LLD.md Section 4.3-4.4 (인터페이스 정의)

**Single Source of Truth**:
- **RESOURCE.md** = 완전한 예제
- **LLD.md** = 인터페이스 정의

**조치**:
- PRD.md: 유지 (요구사항으로서의 필드 목록)
- RESOURCE.md: 유지 (JSON 예제)
- LLD.md: 유지 (함수 시그니처)
- 중복 최소화: PRD.md에서 JSON 예제 제거, RESOURCE.md 참조

---

## 🔄 순환 참조 체크

### 현재 참조 관계:
```
CLAUDE.md
  → PRD.md
  → PLAN.md
  → RESOURCE.md
  → LLD.md

PLAN.md
  → RESOURCE.md (하단)

RESOURCE.md
  → PLAN.md (하단)

LLD.md
  → PRD.md (하단)
  → PLAN.md (하단)
  → RESOURCE.md (하단)
```

**결과**: ✅ 순환 참조 없음 (탐색용 상호 참조만 존재)

---

## 📋 Single Source of Truth 원칙

| 주제 | SSOT | 이유 |
|------|------|------|
| 프로젝트 목표 | PRD.md | 요구사항 문서가 목표 소유 |
| 아키텍처 전략 | PRD.md | 아키텍처는 요구사항의 일부 |
| 컴포넌트 책임 (고수준) | PRD.md | 요구사항 관점의 책임 정의 |
| 컴포넌트 인터페이스 (상세) | LLD.md | 설계 문서가 인터페이스 소유 |
| 데이터 구조 | LLD.md | 설계 문서가 타입 정의 소유 |
| 수용 기준 | PRD.md | 요구사항의 일부 |
| 설정 파일 | RESOURCE.md | 자원 문서가 설정 소유 |
| 운영 파라미터 | PRD.md + RESOURCE.md | PRD=기본값, RESOURCE=배포값 |
| 구현 접근법 | PLAN.md | 계획 문서가 구현 전략 소유 |
| 폴더 구조 | RESOURCE.md | 인프라 문서가 폴더 구조 소유 |

---

## 🎯 리팩토링 실행 계획

### Phase 1: PLAN.md 간소화
1. ✅ 프로젝트 개요 → PRD.md 참조
2. ✅ 아키텍처 전략 → PRD.md 참조
3. ✅ 컴포넌트 책임 → PRD.md + LLD.md 참조
4. ✅ 데이터 구조 → LLD.md 참조
5. ✅ 수용 기준 → PRD.md 참조
6. ✅ 설정 파일 → RESOURCE.md 참조
7. ✅ 폴더 구조 → RESOURCE.md 참조

**예상 감소**: ~40% (중복 제거)

### Phase 2: LLD.md 간소화
1. ✅ 프로젝트 개요 → PRD.md 참조
2. ✅ 아키텍처 전략 → PRD.md 참조

**예상 감소**: ~15% (서론 부분 간소화)

### Phase 3: PRD.md 최소 조정
1. ✅ 로그 포맷 예제 → RESOURCE.md 참조 (간략한 설명만 유지)

**예상 감소**: ~5% (예제 코드 제거)

### Phase 4: RESOURCE.md 최소 조정
1. ✅ 구현 접근법 언급 → PLAN.md 참조

**예상 감소**: ~10% (중복 설명 제거)

---

## ✅ 예상 효과

### 문서별 변경:
- **PRD.md**: 95% 유지 (거의 변경 없음)
- **PLAN.md**: 60% 유지 (40% 감소)
- **RESOURCE.md**: 90% 유지 (10% 감소)
- **LLD.md**: 85% 유지 (15% 감소)

### 전체 이점:
- ✅ 중복 내용 ~25% 감소
- ✅ 문서 간 일관성 향상 (참조 기반)
- ✅ 유지보수성 향상 (수정 시 1곳만 변경)
- ✅ 순환 참조 없음 (계층적 구조 유지)

---

## 🔧 리팩토링 실행

다음 명령어로 리팩토링 실행:
```bash
# 1. PLAN.md 간소화
# 2. LLD.md 간소화
# 3. PRD.md 최소 조정
# 4. RESOURCE.md 최소 조정
```

**승인 후 진행**: 사용자 확인 필요

---

**다음 단계**: 
1. 사용자 승인 대기
2. 승인 시 Phase 1-4 순차 실행
3. 실행 후 문서 버전 업데이트 (v1.1, v1.2 등)
