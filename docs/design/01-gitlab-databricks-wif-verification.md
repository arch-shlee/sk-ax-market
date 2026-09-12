# ① 온프렘 GitLab ↔ Databricks WIF 검증 설계

> **목적**: 온프렘 GitLab을 OIDC issuer로 하는 Databricks Workload Identity Federation(WIF)의 성립 여부를 **최소 비용으로 확정**하고, 결과에 따른 후속 설계 분기를 미리 정의한다.
> **작성일**: 2026-09-10
> **선행 문서**: `cicd-devsecops-research.md` §3-2
> **소요 예상**: Phase 1~2 반나절, Phase 3 1~2일 (Databricks 계정 관리자 협조 필요)

---

## 1. 왜 이것부터인가

CI/CD 아키텍처에서 **Databricks 트랙의 인증 방식이 결정되지 않으면 파이프라인 설계를 시작할 수 없다.** WIF가 성립하면 시크릿리스로 깔끔하게 가지만, 불가하면 시크릿 관리 체계(Vault 연계, 로테이션 정책, 감사)를 별도로 설계해야 하고 이는 전체 일정에 영향을 준다.

### 문제의 구조 — 방향이 반대인 두 개의 흐름

이 문제의 본질은 **데이터 흐름과 인증 검증 흐름의 방향이 반대**라는 데 있다.

| 흐름 | 방향 | 상태 |
|---|---|---|
| 코드·번들 배포 (`databricks bundle deploy`) | 온프렘 Runner → Databricks (아웃바운드) | ✅ 문제 없음 |
| **OIDC 토큰 검증 (JWKS 조회)** | **Databricks → 온프렘 GitLab (인바운드)** | ⚠️ **여기가 막힌다** |

배포 자체는 온프렘에서 밀어내는(push) 방식이므로 아무 문제가 없다. **오직 인증 검증만 반대 방향을 요구한다.**

### 검증 대상 가설

> **H1**: Databricks 컨트롤 플레인이 온프렘 GitLab의 OIDC discovery / JWKS 엔드포인트에 도달할 수 없으므로, GitLab을 issuer로 하는 WIF 정책은 성립하지 않는다.

**근거**: OIDC 토큰 검증은 검증자가 issuer의 `/.well-known/openid-configuration`을 조회해 `jwks_uri`를 얻고, 그 JWKS로 토큰 서명(RS256)을 검증하는 것이 전제다. Databricks 공식 문서는 self-managed GitLab 지원 여부를 명시하지 않으며 예시는 `https://gitlab.com`만 참조한다.

**H1이 참일 경우의 부수 영향** (검증 시 함께 확인할 것)
- **Databricks Git folders / Repos 연동도 동일하게 불가**하다. Databricks 컨트롤 플레인이 Git 제공자에서 소스를 가져오는 구조이므로 같은 인바운드 도달성을 요구한다.
- → 이 경우 **"온프렘 Runner가 번들을 push한다"가 유일한 배포 경로**로 확정된다. 설계 선택지가 줄어드는 것이므로 오히려 명확해진다.

---

## 2. 사전 준비

### 2-1. 수집할 정보

| 항목 | 확보처 | 비고 |
|---|---|---|
| GitLab `external_url` 설정값 | GitLab 관리자 | issuer 값의 기준. 정확한 스킴·호스트·포트 필요 |
| GitLab 버전 | `/help` 또는 관리자 | ID Token 기능 지원 버전 확인 |
| GitLab 라이선스 tier | 관리자 | (WIF 자체는 무관하나 후속 정책 설계에 필요) |
| Databricks 클라우드 (AWS/Azure/GCP) | 인프라 담당 | `databricks-apps-reference.md` §11-1과 동일 항목 |
| Databricks 계정 ID | 계정 콘솔 | 페더레이션 정책의 `audiences` 권장값 |
| Databricks 워크스페이스 URL | 계정 콘솔 | `DATABRICKS_HOST` |
| Runner의 아웃바운드 허용 정책 | 네트워크 담당 | Databricks 도메인 접근 가능 여부 |

### 2-2. 필요 권한

- **Databricks 계정 관리자** — `service-principal-federation-policy create`는 계정 레벨 권한이 필요하다. 이 협조 확보가 Phase 3의 실질적 리드타임이다.
- **GitLab 프로젝트 Maintainer** — 테스트 프로젝트 생성 및 CI 실행

### 2-3. 테스트 자원

| 자원 | 용도 | 정리 |
|---|---|---|
| GitLab 테스트 프로젝트 (`ax-wif-probe`) | 파일럿 파이프라인 | 검증 후 보존 (회귀 확인용) |
| Databricks 서비스 프린시펄 (`sp-ax-wif-probe`) | 페더레이션 대상 | **검증 후 삭제** |
| 페더레이션 정책 | 검증 | **검증 후 삭제** |

> 테스트 SP에는 **어떤 워크스페이스 권한도 부여하지 않는다.** `current-user me` 호출만으로 인증 성립 여부를 판정할 수 있으므로 데이터 접근 권한이 불필요하다.

---

## 3. 검증 절차

### Phase 1 — GitLab 측 OIDC 메타데이터 확인 (온프렘 내부, ~10분)

**목적**: GitLab이 OIDC 메타데이터를 정상 노출하는지, issuer 값이 정확히 무엇인지 확정한다.

```bash
# 온프렘 네트워크 내부에서 실행
curl -s https://<gitlab-host>/.well-known/openid-configuration | jq '{issuer, jwks_uri}'
```

**확인 사항**
- `issuer` 값 — 이 문자열이 **페더레이션 정책의 issuer와 정확히 일치**해야 한다. 후행 슬래시, 포트 포함 여부까지 그대로 사용할 것.
- `jwks_uri` 값 — Phase 2에서 사용

```bash
# JWKS 정상 응답 확인
curl -s <위에서 얻은 jwks_uri> | jq '.keys | length'
```

**판정**

| 결과 | 해석 | 조치 |
|---|---|---|
| `issuer`·`jwks_uri` 정상, 키 1개 이상 | 정상 | Phase 2 진행 |
| 404 / 빈 응답 | GitLab OIDC provider 기능 문제 | GitLab 관리자와 설정 확인 후 재시도 |

> 참고: GitLab CI ID 토큰은 **RS256으로 인코딩되고 전용 개인키로 서명**되며, 잡 타임아웃 또는 기본 5분 후 만료된다.

---

### Phase 2 — 외부 도달성 확인 (~30분, **핵심 단계**)

**목적**: H1을 저비용으로 조기 판정한다. 여기서 차단이 확인되면 Phase 3을 생략할 수 있다.

온프렘 네트워크 **바깥**에서 Phase 1과 동일한 두 URL을 호출한다.

**권장 실행 위치 (우선순위순)**

1. **Databricks가 위치한 클라우드의 VM** — 컨트롤 플레인과 네트워크 경로가 가장 유사. 가장 신뢰도 높음.
2. **사외 인터넷 회선의 임의 호스트** — 차선. 인터넷 노출 여부만 확인 가능.
3. ~~공개 온라인 도구~~ — **비권장.** 내부 URL을 외부 서비스에 노출하게 되므로 보안팀 승인 없이 사용 금지.

```bash
# 외부 호스트에서 실행
curl -sv --max-time 10 https://<gitlab-host>/.well-known/openid-configuration
```

**판정**

| 결과 | H1 판정 | 다음 단계 |
|---|---|---|
| 타임아웃 / connection refused / DNS 실패 | **H1 지지 (강)** | Phase 3 생략 가능 → §5 시나리오 B |
| TLS 오류 (사설 CA 등) | **H1 지지 (중)** | 인증서 체인 문제일 수 있으므로 §4 참고 후 판단 |
| 200 + 정상 JSON | **H1 기각 후보** | Phase 3으로 결정적 검증 |

> ⚠️ **Phase 2 결과만으로 확정하지 말 것.** 200이 나와도 Databricks 컨트롤 플레인의 이그레스 정책은 우리가 제어하지 않는다. 반대로 차단이 나와도 특정 대역만 허용된 경로가 존재할 수 있다. **결정적 판정은 Phase 3이다.**

---

### Phase 3 — 결정적 검증: 실제 페더레이션 정책 + 파일럿 파이프라인 (1~2일)

#### 3-1. 서비스 프린시펄 및 페더레이션 정책 생성

테스트 프로젝트의 `sub` 클레임 값을 먼저 확정한다. GitLab의 기본 형식은 다음과 같다.

```
project_path:{group}/{project}:ref_type:{type}:ref:{branch_name}
```

예: `project_path:ax/ax-wif-probe:ref_type:branch:ref:main`

```bash
databricks account service-principal-federation-policy create <sp-id> \
  --json '{
    "oidc_policy": {
      "issuer": "<Phase 1에서 확인한 issuer 값 그대로>",
      "audiences": ["<Databricks 계정 ID>"],
      "subject": "project_path:ax/ax-wif-probe:ref_type:branch:ref:main"
    }
  }'
```

#### 3-2. 최소 파일럿 파이프라인

```yaml
# .gitlab-ci.yml
variables:
  DATABRICKS_AUTH_TYPE: env-oidc
  DATABRICKS_HOST: "<워크스페이스 URL>"
  DATABRICKS_CLIENT_ID: "<서비스 프린시펄 ID>"

wif-probe:
  id_tokens:
    DATABRICKS_OIDC_TOKEN:
      aud: "<Databricks 계정 ID>"
  script:
    # (a) 토큰이 발급되었는지 형태만 확인 — 값은 절대 출력하지 말 것
    - echo "token length: ${#DATABRICKS_OIDC_TOKEN}"
    # (b) 결정적 판정: 인증이 성립하면 성공
    - databricks current-user me
```

> 🔒 **주의**: `DATABRICKS_OIDC_TOKEN` 값 자체를 로그로 출력하지 말 것. 짧은 수명이지만 유효한 자격증명이다. 길이만 확인한다.

#### 3-3. 판정

| 결과 | 판정 |
|---|---|
| `current-user me`가 SP 정보 반환 | ✅ **WIF 성립. H1 기각.** → §5 시나리오 A |
| 인증 실패 | §4의 원인 판별로 이동 |

---

## 4. 실패 시 원인 판별 — 도달성 문제인가, 설정 문제인가

**이 단계를 건너뛰면 안 된다.** 단순 설정 실수를 "온프렘이라 불가능"으로 오판하면 잘못된 아키텍처 결정으로 이어진다.

| 증상 | 추정 원인 | 확인 방법 | 조치 |
|---|---|---|---|
| 타임아웃, issuer 조회 실패, discovery 관련 오류 | **도달성 문제 (H1 참)** | Phase 2 결과와 일치하는지 대조 | §5 시나리오 B |
| TLS / 인증서 검증 오류 | 사설 CA 인증서를 Databricks가 신뢰하지 않음 | GitLab 인증서 발급자 확인 | 공인 CA 인증서로 교체 후 재시도 → 해결되면 H1 기각 |
| subject 불일치 오류 | `sub` 문자열 불일치 | 잡 로그에서 실제 토큰의 `sub` 확인 (디코딩은 **로컬에서만**) | 정책의 subject 수정 후 재시도 |
| audience 불일치 오류 | `aud` 값 불일치 | `.gitlab-ci.yml`의 `aud`와 정책의 `audiences` 대조 | 일치시킨 후 재시도 |
| 인증은 되나 권한 오류 | **인증 성공.** SP 권한 없음 | 오류 메시지가 권한 관련인지 확인 | ✅ **WIF는 성립한 것.** 시나리오 A |

> 💡 마지막 행이 중요하다. **권한 오류는 인증 성공의 증거다.** 토큰 교환이 되지 않았다면 권한 판정 단계까지 가지 못한다.

**재시도 원칙**: 한 번에 한 변수만 바꾼다. issuer·audience·subject를 동시에 수정하면 원인을 특정할 수 없다.

---

## 5. 결과별 후속 설계 분기

### 시나리오 A — WIF 성립 (H1 기각)

시크릿리스로 진행한다. 검증 성공 후 다음을 설계에 반영한다.

1. **subject를 좁힌다.** 테스트에서는 단일 브랜치로 검증했지만, 실제로는 **배포 대상 브랜치·환경 단위로 정책을 분리**해야 한다. 운영 배포용 SP는 보호된 브랜치(`ref_protected`)에서만 토큰을 받도록 subject를 구성한다.
2. **SP를 환경별로 분리한다.** 개발/운영 워크스페이스에 각각 별도 SP와 페더레이션 정책을 둔다.
3. **GitLab 환경(environment) 보호와 결합한다.** 운영 배포 잡은 보호된 환경에서만 실행되게 하여, ID 토큰 발급 자체를 승인 게이트 뒤로 보낸다.

### 시나리오 B — WIF 불가 (H1 참)

대안을 우선순위대로 검토한다.

#### 대안 B-1. OIDC 메타데이터 엔드포인트만 제한 공개 ⭐ 권장

DMZ 리버스 프록시로 **discovery와 JWKS 두 경로만** 외부에 노출한다.

| 항목 | 내용 |
|---|---|
| 노출 대상 | `/.well-known/openid-configuration`, `jwks_uri` 경로 **2개만** |
| 노출 정보 | OIDC 메타데이터와 **공개키**. 개인키·소스코드·사용자 정보는 포함되지 않음 |
| 제약 | **issuer URL과 동일한 호스트명**으로 외부에서 해석·도달 가능해야 한다. 다른 도메인으로 프록시하면 issuer 불일치로 실패 |
| 추가 요건 | 공인 CA 인증서, 나머지 모든 경로 차단, 접근 로깅 |
| 난이도 | 중 — 외부 DNS와 보안팀 승인 필요 |

**보안 관점**: JWKS는 설계상 공개되도록 만들어진 데이터다(공개키). 노출 위험 자체는 낮으나, **GitLab 호스트명이 외부에 드러난다는 점**이 보안팀 검토 포인트가 된다. 접근 소스를 Databricks 대역으로 제한할 수 있는지 함께 확인한다.

#### 대안 B-2. 클라우드 Runner + 클라우드 네이티브 아이덴티티

> ⚠️ **정정**: 선행 문서(`cicd-devsecops-research.md`)에 "클라우드 중계 Runner"를 대안으로 적었으나, **Runner를 옮기는 것만으로는 해결되지 않는다.** Runner 위치와 무관하게 GitLab ID 토큰의 발급자는 여전히 온프렘 GitLab이고, Databricks는 그 JWKS에 도달해야 한다.

**성립하는 형태**는 다음과 같다.

- 배포 잡을 **클라우드 측 Runner**에서 실행하고,
- **GitLab ID 토큰 대신 해당 클라우드의 워크로드 아이덴티티**(공개 issuer를 가짐)로 Databricks에 페더레이션한다.

| 항목 | 내용 |
|---|---|
| 장점 | 시크릿리스 유지. issuer가 클라우드 공개 엔드포인트라 도달성 문제 없음 |
| 단점 | 클라우드에 Runner 인프라 운영 부담. **GitLab의 세밀한 subject 조건(프로젝트/브랜치/환경)을 인증 경계로 쓸 수 없음** — 해당 Runner에 접근 가능한 모든 잡이 동일 아이덴티티를 갖게 됨 |
| 완화책 | 배포 전용 Runner를 태그로 격리하고, 보호된 브랜치·환경에서만 해당 태그를 쓰도록 제한 |

#### 대안 B-3. OAuth 시크릿 + Vault (최후 수단)

Databricks SP의 OAuth 시크릿을 GitLab CI 변수 또는 Vault로 관리한다.

| 항목 | 내용 |
|---|---|
| 장점 | 확실히 동작함. 추가 인프라 최소 |
| 단점 | **2026년 트렌드 역행.** 장기 자격증명 보관·로테이션·감사 부담이 그대로 남음 |
| 필수 통제 | Vault 연계, 자동 로테이션 주기 정의, masked·protected 변수, 보호된 브랜치 한정, 접근 감사 로그 |

**선택 기준**: B-1이 보안팀 승인을 받을 수 있으면 B-1. 클라우드 Runner 운영 여력이 있고 subject 세분화를 포기할 수 있으면 B-2. 둘 다 어려우면 B-3에 통제를 강하게 걸고 가되, **로테이션 자동화를 반드시 포함**한다.

---

## 6. 함께 확인할 부수 항목

Phase 3을 진행하는 김에 같이 확인하면 별도 작업이 절약된다.

| # | 확인 항목 | 방법 | 영향 |
|---|---|---|---|
| 1 | **Databricks Git folders 연동 가능 여부** | Databricks UI에서 온프렘 GitLab 리포 연결 시도 | 불가 시 "Runner push가 유일한 배포 경로"로 확정 |
| 2 | Runner의 Databricks 도메인 아웃바운드 | Runner에서 `databricks --version` 후 API 호출 | 막히면 방화벽 정책 추가 필요 |
| 3 | Runner의 PyPI / npm 아웃바운드 | 테스트 잡에서 패키지 설치 | 막히면 사내 미러 필요 |
| 4 | Databricks 클라우드 확정 (AWS/Azure/GCP) | 계정 콘솔 | **인증 설계 전체의 분기점** (`databricks-apps-reference.md` §11-1) |
| 5 | Databricks 계약 tier (Enterprise 여부) | 계정 콘솔 / 계약서 | 네트워크 정책 사용 가능 여부 |

---

## 7. 실행 체크리스트

```
[ ] Phase 0  Databricks 계정 관리자 협조 요청 (리드타임 최장)
[ ] Phase 0  §2-1 정보 수집 완료
[ ] Phase 1  GitLab discovery 엔드포인트 정상 응답 확인
[ ] Phase 1  issuer 값 정확히 기록 (후행 슬래시·포트 포함)
[ ] Phase 1  JWKS 키 존재 확인
[ ] Phase 2  외부 호스트에서 도달성 테스트 (권장: 클라우드 VM)
[ ] Phase 2  결과 기록 → 차단이면 Phase 3 생략 판단
[ ] Phase 3  테스트 SP 생성 (권한 부여 없음)
[ ] Phase 3  페더레이션 정책 생성
[ ] Phase 3  파일럿 파이프라인 실행
[ ] Phase 4  실패 시 원인 판별표로 도달성/설정 구분
[ ] Phase 5  시나리오 확정 및 후속 설계 반영
[ ] 정리     테스트 SP·정책 삭제
[ ] 부수     §6 항목 5건 확인
```

---

## 8. 판정 결과 기록란

> 검증 수행 후 이 절을 채운다. 이후 설계 문서들이 이 결론을 참조한다.

| 항목 | 결과 | 확인일 | 확인자 |
|---|---|---|---|
| GitLab issuer 값 | | | |
| Phase 2 외부 도달성 | | | |
| Phase 3 WIF 성립 여부 | | | |
| **확정 시나리오 (A / B-1 / B-2 / B-3)** | | | |
| Databricks Git folders 연동 | | | |
| Databricks 클라우드 | | | |
| Databricks tier | | | |

---

## 참고

- [Enable workload identity federation for GitLab CI/CD (Databricks)](https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab)
- [Configure a federation policy (Databricks)](https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-policy)
- [OpenID Connect (OIDC) Authentication Using ID Tokens (GitLab)](https://docs.gitlab.com/ci/secrets/id_token_authentication/)
- [GitLab as OpenID Connect identity provider](https://docs.gitlab.com/integration/openid_connect_provider/)

## 관련 문서

- `docs/reference/cicd-devsecops-research.md` — CI/CD·DevSecOps 자료조사
- `docs/reference/databricks-apps-reference.md` — Databricks Apps 기술 레퍼런스
