---
name: Phase Progress Validator
description: PLAN.md Phase별 진행 상황을 자동 검증하고 체크박스를 업데이트
trigger:
  - manual: "PLAN 검증", "Phase 진행 확인", "체크박스 업데이트", "PLAN checker", "진행 상황 체크"
  - command: "/sc:validate-plan"
---

# Phase Progress Validator

PLAN.md Phase별 진행 상황을 자동 검증하고 체크박스를 업데이트하는 스킬입니다.

## 실행 프로세스

### 1. PLAN.md 파싱
```bash
# PLAN.md 읽기 및 Phase 구조 파싱
- Read tool로 PLAN.md 전체 읽기
- Phase별 체크리스트 항목 추출 (- [ ] 또는 - [x])
- 완료 조건 추출 (각 Phase 하단의 "완료 조건" 섹션)
```

### 2. 파일 존재 검증
```python
# Phase별 필수 파일 매핑
PHASE_FILES = {
    "Phase 1": {
        "checklist": {
            "브랜치 생성": "git branch | grep feature/thymeleaf-transition",
            "ViewController.java 생성": "src/main/java/com/ktb/community/controller/ViewController.java",
            "templates/ 디렉토리 구조 생성": "src/main/resources/templates/",
            "Thymeleaf 설정 확인": "src/main/resources/application.yaml",
            "Thymeleaf Layout Dialect 의존성": "build.gradle"
        },
        "completion": {
            "ViewController 메서드 1개 이상": "grep -r 'public String' src/main/java/com/ktb/community/controller/ViewController.java",
            "templates/ 디렉토리 생성 확인": "ls -d src/main/resources/templates/"
        }
    },
    "Phase 2": {
        "checklist": {
            "layout/default.html": "src/main/resources/templates/layout/default.html",
            "fragments/header.html": "src/main/resources/templates/fragments/header.html",
            "fragments/post-card.html": "src/main/resources/templates/fragments/post-card.html",
            "fragments/footer.html": "src/main/resources/templates/fragments/footer.html",
            "CSS/JS 경로 변경": "grep 'th:href=\\\"@{' src/main/resources/templates/layout/default.html"
        },
        "completion": {
            "layout 적용 확인": "grep 'layout:decorate' src/main/resources/templates/**/*.html",
            "Fragment 재사용 확인": "grep -r 'th:replace.*fragments' src/main/resources/templates/ | wc -l"
        }
    }
}
```

### 3. 검증 실행
```
각 Phase별로 다음 검증 수행:

1. **체크리스트 검증**
   - Glob/Grep으로 파일 존재 확인
   - Bash로 조건 실행 (예: git branch 확인)
   - 결과: ✅ 존재 / ❌ 없음

2. **완료 조건 검증**
   - 각 Phase의 "완료 조건" 항목 실행
   - Bash/Grep으로 조건 평가
   - 결과: ✅ 충족 / ⚠️ 불충족

3. **커밋 히스토리 확인** (선택)
   - git log --oneline --grep "Phase X" 실행
   - 해당 Phase 관련 커밋 존재 여부 확인
```

### 4. 체크박스 자동 업데이트
```python
def update_checkboxes(phase_num, checklist_results):
    """
    PLAN.md의 체크박스를 검증 결과에 따라 업데이트

    Args:
        phase_num: Phase 번호 (1, 2, 3, ...)
        checklist_results: {항목명: True/False} 딕셔너리
    """
    plan_content = read_file("docs/fe/PLAN.md")

    for item, is_complete in checklist_results.items():
        if is_complete:
            # - [ ] 항목명 → - [x] 항목명
            pattern = f"- \\[ \\] {re.escape(item)}"
            replacement = f"- [x] {item}"
            plan_content = re.sub(pattern, replacement, plan_content)

    # Edit tool로 PLAN.md 업데이트
    write_file("docs/fe/PLAN.md", plan_content)
```

### 5. 진행 상황 리포트 생성
```markdown
## 📋 Phase Progress Report

### Phase 1: 백엔드 Controller 설정 ✅ 완료
**체크리스트 (5/5):**
- [x] 브랜치 생성 ✅
- [x] ViewController.java 생성 ✅
- [x] templates/ 디렉토리 구조 생성 ✅
- [x] Thymeleaf 설정 확인 ✅
- [x] Thymeleaf Layout Dialect 의존성 ✅

**완료 조건:**
- ✅ ViewController 메서드 1개 이상: boardList() 존재
- ✅ templates/ 디렉토리 생성 확인: 3개 디렉토리 존재

---

### Phase 2: 레이아웃 및 Fragment ⚠️ 진행 중
**체크리스트 (4/5):**
- [x] layout/default.html ✅ (39줄)
- [x] fragments/header.html ✅ (83줄)
- [x] fragments/post-card.html ✅ (60줄)
- [x] fragments/footer.html ✅ (29줄)
- [ ] CSS/JS 경로 변경 ❌ (아직 th:href 사용 안 함)

**완료 조건:**
- ✅ layout/default.html 존재: 파일 확인됨
- ⚠️ Fragment 재사용 확인: 0곳 (board/list.html 미작성)

**다음 단계:**
- CSS/JS 경로를 th:href="@{/css/...}" 형식으로 변경
- board/list.html 작성하여 Fragment 재사용 검증

---

## 전체 진행률
- **완료:** Phase 1 ✅
- **진행 중:** Phase 2 (80%)
- **대기:** Phase 3-7
- **전체:** 2/7 Phases (28.6%)

## 최근 커밋
- ✅ feat: Phase 2 완료 - 레이아웃 및 Fragment 생성
- ✅ docs: PLAN.md IntersectionObserver 구현 세부사항 추가

## 권장 사항
1. Phase 2 완료를 위해 CSS/JS 경로 변경 필요
2. Phase 3 시작 전 board/list.html 작성하여 Fragment 재사용 테스트
```

## 도구 사용

### Read Tool
```
- PLAN.md 읽기
- Phase별 템플릿 파일 읽기 (검증용)
- build.gradle, application.yaml 읽기
```

### Glob Tool
```
- src/main/resources/templates/**/*.html
- src/main/java/com/ktb/community/controller/*.java
```

### Grep Tool
```
- 체크리스트 항목 검색
- Fragment 재사용 횟수 카운팅
- th:href, th:replace 패턴 검색
```

### Bash Tool
```
- git branch: 브랜치 존재 확인
- git log: Phase 커밋 히스토리 확인
- wc -l: 파일 라인 수 측정
- ls -d: 디렉토리 존재 확인
```

### Edit Tool
```
- PLAN.md 체크박스 업데이트 (- [ ] → - [x])
- Phase 완료 상태 표시 (✅ 완료, ⚠️ 진행 중)
```

## 실행 예시

**사용자 요청:**
> "Phase 2 진행 상황 확인해줘"

**스킬 실행 순서:**
1. Read PLAN.md
2. Phase 2 체크리스트 파싱:
   - layout/default.html
   - fragments/header.html
   - fragments/post-card.html
   - fragments/footer.html
   - CSS/JS 경로 변경
3. Glob으로 파일 존재 확인
4. Grep으로 Fragment 재사용 확인
5. 검증 결과 집계
6. Edit로 PLAN.md 체크박스 업데이트
7. 진행 상황 리포트 출력

## 검증 로직 상세

### Phase 1 검증
```bash
# 브랜치 확인
git branch | grep feature/thymeleaf-transition

# ViewController 메서드 확인
grep -c "public String" src/main/java/com/ktb/community/controller/ViewController.java

# templates 디렉토리 확인
ls -d src/main/resources/templates/layout src/main/resources/templates/fragments src/main/resources/templates/board
```

### Phase 2 검증
```bash
# 파일 존재 확인
test -f src/main/resources/templates/layout/default.html && echo "✅" || echo "❌"

# Fragment 재사용 횟수
grep -r "th:replace.*fragments" src/main/resources/templates/ | wc -l

# Thymeleaf 경로 표현식 사용 확인
grep -c 'th:href="@{' src/main/resources/templates/layout/default.html
```

### Phase 3 검증
```bash
# board/list.html 존재 확인
test -f src/main/resources/templates/board/list.html

# IntersectionObserver 구현 확인
grep -c "IntersectionObserver" src/main/resources/static/js/board/list-infinite-scroll.js

# Template 요소 존재 확인
grep -c '<template id="post-card-template">' src/main/resources/templates/board/list.html
```

## 출력 형식

### 성공 케이스
```
✅ Phase 2 검증 완료

**체크리스트:** 4/5 완료
- ✅ layout/default.html (39줄)
- ✅ fragments/header.html (83줄)
- ✅ fragments/post-card.html (60줄)
- ✅ fragments/footer.html (29줄)
- ❌ CSS/JS 경로 변경 (0개 발견)

**완료 조건:** 1/2 충족
- ✅ layout 적용 확인
- ⚠️ Fragment 재사용 확인: 0곳 (목표: 2곳 이상)

**PLAN.md 업데이트:** 4개 항목 체크박스 업데이트 완료
```

### 불완전 케이스
```
⚠️ Phase 3 진행 필요

**체크리스트:** 0/4 완료
- ❌ ViewController.getBoardList() 메서드 (파일 미생성)
- ❌ board/list.html 작성 (파일 미생성)
- ❌ JavaScript 최소화 (파일 미생성)

**다음 단계:**
1. ViewController에 boardList() 메서드 작성
2. board/list.html 템플릿 작성
3. list-infinite-scroll.js 작성

**예상 소요 시간:** 2.5시간
```

## 에러 처리

### PLAN.md 파일 없음
```
❌ PLAN.md를 찾을 수 없습니다.
경로: docs/fe/PLAN.md
해결: PLAN.md 파일이 존재하는지 확인하세요.
```

### 체크리스트 형식 오류
```
⚠️ Phase 2 체크리스트 파싱 실패
원인: - [ ] 또는 - [x] 형식이 아닌 항목 발견
줄 번호: 156
내용: "* layout/default.html"
해결: - [ ] layout/default.html 형식으로 수정 필요
```

## 제약 사항

1. **파일 시스템 접근만 검증**: 서버 실행이나 컴파일은 하지 않음
2. **정적 분석 위주**: 런타임 동작은 확인 불가
3. **체크리스트 형식 의존**: PLAN.md가 표준 형식을 따라야 함
4. **Phase별 독립 검증**: 이전 Phase 완료 여부는 검증하지 않음

## 개선 방향 (추후)

1. **테스트 자동 실행**: ./gradlew test 결과 반영
2. **코드 품질 검증**: SonarQube, CheckStyle 연동
3. **커버리지 확인**: JaCoCo 리포트 파싱
4. **배포 검증**: application.yaml 환경 변수 체크
