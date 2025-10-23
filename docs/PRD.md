# PRD v2.0 — 핵심 요구사항

**버전**: v2.0 (압축)
**작성일**: 2025-10-23
**완전판**: `docs/archive/PRD.md`

---

## 목적 & 전략

### 목표
N개 프로필이 커뮤니티 URL만으로 회원가입 → 로그인 → 탐색 → 글/댓글 작성 자동화

### 전략
- **UI 탐색**: Clickable-First (버튼/링크 스코어링)
- **콘텐츠**: LLM + Persona
- **운영**: 비동기 판별, 로그인 이중화, Anti-Bot

---

## 상태머신 플로우

```
START → UI_SCAN → SIGN_UP/LOGIN → ACTION_HUB → WRITE_POST/WRITE_COMMENT/EXPLORE
```

---

## 기능 요구사항

### FR1. 클릭 후보 수집
- 버튼/링크/submit 메타데이터: selector, text, href, role, 가시성, 좌표
- 세션: `profiles/<id>/session.json`

### FR2. 스코어링
- **CTA**: 가입, 로그인, 글쓰기, 댓글, 제출 (로그인 상태 반영)
- **Curiosity**: 상세 페이지 > 페이지네이션 > 좋아요
- **선택**: 상위 1~3위 중 확률 선택 + 무작위 가중치

### FR3. FORM BOUNDARY
- submit 버튼 조상 `<form>` 기준
- Auth: email/user/pw1/pw2/terms
- Write/Comment: title/body/comment

### FR4. 성공/실패 신호 (순서 강제)
1. **Inline**: `[aria-invalid]`, `.error` → 즉시 수정 (≤2회)
2. **Global**: 로그아웃 버튼, URL 변화, 쿠키, 성공/실패 키워드

### FR5. 루프 방지 & 백오프
- 1분 TTL, 동일 href/텍스트 2회 초과 금지
- 백오프: 1→2→4→8→16s (최대 5회)
- 시도 상한: 페이지당 CTA ≤3, 동일 CTA ≤2

### FR6. 동시성/레이트/멱등
- 동시: ≥6 워커
- 레이트: 전역 1 QPS 읽기, 6 QPM 쓰기, 프로필 2/h
- 멱등: `Idempotency-Key` 또는 로컬 해시
- Stop: `STOP_ALL`, `STOP_ACTOR`

### FR7. 로그 & 메트릭
- JSONL: time, actor, state, intent, action, result, latency_ms
- 메트릭: 처리량, 오류, 차단, 지연 p50/p95

### FR8. 크레덴셜
- SIGN_UP: 새 creds 생성 → `profiles/<id>/creds.json`
- LOGIN: 저장된 creds 사용

### FR9. 콘텐츠 생성
- Persona + Context → LLM 호출
- 필터: 금칙어, PII, 광고, 중복
- 다양화: temperature(0.5~0.9), few-shot, negative

### FR10. 비동기 액션 판별
- API 응답 (`/api/(like|vote|comment|...)/ && 200`)
- DOM/URL 변화, 버튼 상태/카운트
- 타임아웃: 2.5s, 재시도 1회

### FR11. 로그인 상태 이중화
- 다중 신호: 로그아웃 버튼, 쿠키, 세션 파일
- 보호창: 로그인 직후 60s → 강제 `ACTION_HUB`

### FR12. AI 발자국 다양화
- Temperature, top_k, top_p, few-shot
- 무작위 가중치, 스타일 변주

### FR13. Anti-Bot
- UA/Viewport 무작위
- Jitter: 2~45s
- 선택: 상위 확률 선택

---

## 휴리스틱 테이블

### CTA 키워드
| CTA | 텍스트 | URL 패턴 |
|-----|--------|----------|
| SIGN_UP | 회원가입, 가입, Sign up | `/signup`, `/register` |
| LOGIN | 로그인, Sign in | `/login`, `/signin` |
| LOGOUT | 로그아웃, Sign out | `/logout` |
| WRITE_POST | 글쓰기, 새 글, Write | `/new`, `/write` |
| COMMENT | 댓글, Comment, Reply | `/comment`, `#comment` |

### Curiosity 패턴
| 패턴 | URL/Text | 가중치 |
|------|----------|--------|
| POST_VIEW | `/post/`, `/view/` | ⭐⭐⭐ |
| PAGINATION | ?page=, /page/ | ⭐ |
| LIKE | /like, /vote | ⭐ (최하) |

### 폼 셀렉터
| 필드 | CSS 셀렉터 |
|------|-----------|
| Email | `input[type=email]`, `[name*=email i]` |
| Username | `[name*=user i]`, `[name*=nick i]` |
| Password | `input[type=password]` |
| Terms | `input[type=checkbox][name*=term i]` |
| Title | `[name*=title i]` |
| Body | `textarea`, `[contenteditable=true]` |

### 성공/실패 키워드
- **Success**: 환영, 성공, 완료, posted, published
- **Fail**: 에러, 오류, 실패, 필수, 중복, invalid

---

## 수용 기준 (체크리스트)

- [ ] 폼 경계 정확도: 타 폼 혼동 0건
- [ ] 실패 판별: Inline→Global 순서 준수
- [ ] 루프 방지: 1분 내 동일 href 2회 초과 없음
- [ ] 동시성: 1분 내 ≥2 프로필 액션
- [ ] 작성 성공: 게시글 ≥1, 댓글 ≥1 (레이트 내)
- [ ] 세션 영속: 재실행 시 자동 로그인
- [ ] 비동기 판별: fetch/XHR 액션 인식 ≥95%
- [ ] 로그인 루프: 무한 로그인 0건
- [ ] AI 다양성: n-gram 중첩 ≤40%, 금지 문구 0건
- [ ] Anti-Bot: UA/지연/선택 다양화 확인

---

**다음**: [@docs/PLAN.md](PLAN.md), [@docs/RESOURCE.md](RESOURCE.md), [@docs/LLD.md](LLD.md)
