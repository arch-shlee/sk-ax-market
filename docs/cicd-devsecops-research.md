# CI/CD · DevSecOps 자료조사

> **목적**: 온프렘(Private Cloud) GitLab을 중심축으로 AX App Market의 CI/CD를 연계하고 DevSecOps를 적용하기 위한 최신 트렌드·사례 조사.
> **조사일**: 2026-09-10
> **전제**: GitLab이 온프렘 Private Cloud 영역에 구성되어 있음. 배포 대상 런타임은 Private Cloud(VKS)와 Databricks Apps 2종.
> **표기**: ✅ 공식 문서 근거 / ⚠️ 확인 필요 / 💡 AX App Market 적용 제언

---

## 1. 2026년 DevSecOps 흐름 요약

지금 업계의 무게중심은 **"스캔을 돌렸는가"에서 "무엇이 어디서 어떻게 만들어졌는지 증명할 수 있는가"** 로 이동했다. CI/CD 파이프라인 자체가 주요 공격면(primary attack surface)으로 분류되면서 나타난 변화다.

### 1-1. 공급망 보안 3종 세트 — SBOM + SLSA + Sigstore

세 요소가 역할을 나눠 신뢰 사슬을 구성한다.

| 요소 | 역할 | 실무 표준 |
|---|---|---|
| **SBOM** | 무엇이 들어있는가 (인벤토리) | CycloneDX 또는 SPDX. 의존성·전이 패키지·컨테이너 레이어까지 암호학적으로 연결 |
| **SLSA Provenance** | 어떻게 만들어졌는가 (빌드 출처) | **SLSA L3**: 실행 중인 컨테이너를 소스 커밋과 CI 워크플로에 연결. 리포지토리 소유자도 위조 불가 |
| **Sigstore** | 신뢰된 빌더가 만든 것이 맞는가 (서명) | `cosign`(서명) + `Fulcio`(CA) + `Rekor`(투명성 로그). 프로덕션 검증 완료, 광범위 채택 |

빌드 단계 표준 조합: **SBOM 생성 → Cosign 서명 → Trivy 이미지 스캔 → SLSA provenance 검증**

**위협 규모**: Sonatype 기준 2025년 신규 악성 패키지 **454,600개 이상**, 이 중 **99%가 npm**에 집중.

### 1-2. 시크릿리스(Secretless) 인증 — OIDC / Workload Identity Federation

장기 자격증명을 CI에 저장하는 방식이 사실상 안티패턴이 되었다. 대신 **CI가 발급한 단기 ID 토큰을 클라우드 측이 검증하고 임시 자격증명으로 교환**한다.

- 정적 키 발급 불필요 → 장기 키 관리와 주기적 로테이션 컴플라이언스 부담 제거
- 유출 위험 최소화(단기 토큰), 서비스 계정 사용처를 CI 환경에 결박 가능

### 1-3. Policy as Code — 개발자가 우회할 수 없는 강제

보안 잡을 개발자 재량에 맡기지 않고 **플랫폼이 주입**하는 방향으로 정착했다. "개발자가 작성하지 않고, 안전하게 제거할 수 없으며, `[skip ci]`로 건너뛸 수 없는" 구조가 핵심 요건이다.

### 1-4. ASPM + Reachability Analysis — 노이즈 제거

ASPM(Application Security Posture Management)이 단순 스캐너 결과 취합에서 **예방적·맥락 인식 컨트롤 플레인**으로 진화했다. 취약점을 런타임 컨텍스트·비즈니스 영향·악용 가능성과 상관 분석한다.

- **Reachability analysis**: 해당 취약점이 실제로 도달 가능하고 악용 가능한지 판정 → **취약점 노이즈를 최대 95% 감소**
- 우선순위 기준: 도달 가능성(reachability), 악용 가능성(exploitability), 명확한 책임자(ownership)

### 1-5. AI 애플리케이션 보안 — 새로운 검증 축

**OWASP GenAI LLM Top 10 2026** (실무자 투표 75% + 실제 사고 6,639건 기반 25%의 하이브리드 스코어링)

- **LLM01 프롬프트 인젝션** — 1위 유지
- **LLM02 민감정보 노출** — 2위 유지
- **LLM03 과도한 권한(Excessive Agency)** — 대폭 상승. 모델 출력이 자율적으로 셸 명령 실행·외부 API 호출·DB 트랜잭션을 수행하는 에이전트 시스템에 사고가 집중
- **Unbounded Consumption** — 4계단 상승. 추론 자원 고갈형 가용성·재무적 DoS

**OWASP Top 10 for Agentic Applications 2026**도 별도 발표. 모델이 텍스트 생성기를 넘어 "목표·자격증명·도구·메모리를 가지고 여러 단계를 연쇄하는 행위자"가 될 때의 위험을 다룬다.

> **핵심 인식**: "2026년에 AI 모델은 또 하나의 서드파티 의존성이지만, 기존 스캐너가 읽을 수 없는 의존성이다."

대응 수단으로 **AI-BOM**(estate 내 모델·에이전트·AI 구성요소 인벤토리), 모델 위험/에이전트 설정 위험 스캔, 시스템 프롬프트 하드닝, 레드팀, 런타임 보호가 제시된다.

### 1-6. 규제 압력 — EU CRA

직접 적용 대상이 아니더라도 **SBOM 의무화의 사실상 기준선**이 되므로 참고 가치가 있다.

| 시점 | 내용 |
|---|---|
| **2026-09-11** | Article 14 발효. 활발히 악용되는 취약점을 ENISA SRP·국가 CSIRT에 보고 의무 |
| **2027-12-11** | 전면 적용. secure-by-design, 적합성 평가, 기술문서, CE 마킹, **SBOM 생성**, 취약점 처리 프로세스, 지원 기간 내 보안 업데이트 제공 의무 |

- 디지털 요소를 가진 **모든 제품에 SBOM 의무**. 형식은 미지정이나 사실상 SPDX / CycloneDX.
- 최소 요건: 최상위 레벨의 기계 판독 가능 인벤토리(오픈소스 의존성, 서드파티 라이브러리 포함)

---

## 2. GitLab 기반 DevSecOps 구현 수단

온프렘 GitLab(self-managed)이 이미 있으므로, 별도 도구 도입 없이 상당 부분을 커버할 수 있다.

### 2-1. 내장 보안 스캐너

| 스캐너 | 내용 | 산출물 |
|---|---|---|
| **SAST** | 소스코드 취약점 탐지. CI/CD에 직접 통합 | 취약점 리포트 |
| **GitLab Advanced SAST** | 고급 분석 (별도 기능) | — |
| **Dependency Scanning (SBOM 방식)** | 파이프라인이 생성한 **CycloneDX SBOM**을 GitLab Advisory Database와 대조. **신규 프로젝트 권장 방식이자 GitLab의 장기 방향** | CycloneDX SBOM |
| **Container Scanning** | 의존 이미지 취약점 스캔 | JSON 리포트 + **`gl-sbom-report.cdx.json`** (CycloneDX SBOM) |
| **Secret Detection** | 기본 브랜치 커밋의 시크릿 탐지 | 탐지 리포트 |
| **License 승인 정책** | 라이선스 컴플라이언스 | — |

💡 PDF 기획서의 검증 항목(빌드·테스트, SAST/SCA, Secret Scan, SBOM)은 **GitLab 기본 기능으로 거의 그대로 매핑된다.** 별도 도구 도입 논의보다 GitLab 라이선스 tier 확인이 우선이다(다수 기능이 Ultimate).

### 2-2. 정책 강제 메커니즘 — 여기가 핵심

PDF의 "공통 검증 기준·절차 정립" 목표를 **기술적으로 강제**하는 수단이다.

| 정책 유형 | 기능 |
|---|---|
| **Scan Execution Policy** | 프로덕션 대상 모든 파이프라인에 SAST·SCA·Secret Detection 잡을 **강제 주입**. 개발자가 작성하지 않고, 안전하게 제거할 수 없으며, `[skip ci]`로 건너뛸 수 없음 |
| **Pipeline Execution Policy** | 정책의 `.gitlab-ci.yml` 잡을 **격리된 파이프라인**에서 실행 후 대상 프로젝트 파이프라인에 병합 |
| **Merge Request Approval Policy** | **스캔 결과에 기반한** 승인 규칙 강제. 예) 기본 브랜치 대상 MR은 Developer·Maintainer 복수 승인 필요 |
| **Compliance Framework** | 최상위 그룹에 생성. Ultimate에서 **적용된 프로젝트에 컴플라이언스 파이프라인 설정과 보안 정책을 강제** |
| **Security Policy Project** | 정책을 코드로 관리하는 전용 프로젝트 |

**적용 전략 2가지**
- `inject`: 기존 프로젝트 CI 설정을 유지하며 추가 단계만 주입 — 기존 파이프라인 확장에 적합
- `override_project_ci`: 프로젝트 CI 설정을 정책 정의로 **완전 대체** — 파이프라인 전체를 표준화해야 할 때

정책 범위(scope)는 프로젝트·그룹·**컴플라이언스 프레임워크 레이블** 단위로 포함/제외 지정 가능.

> ⚠️ Compliance pipelines는 **deprecated**. 신규 설계는 Pipeline Execution Policy 기반으로 갈 것.

💡 **AX App Market 적용**: 앱 유형(일반 Web App / Agent App)과 런타임(Private Cloud / Databricks)을 **컴플라이언스 프레임워크 레이블**로 표현하고, 레이블별로 다른 정책 세트를 강제하는 구조가 자연스럽다. 앱마켓 등록 시 선택한 유형이 곧 적용될 검증 게이트를 결정하게 된다.

### 2-3. 클라우드 인증 — GitLab ID Token

- 잡마다 **ID Token**(JWT)을 CI/CD 변수로 발급받아 OIDC 지원 클라우드(AWS·Azure·GCP·Vault)에 인증
- 온디맨드 단기 자격증명 생성, **시크릿 저장 불필요**

---

## 3. 두 런타임에 대한 배포 아키텍처

### 3-1. Private Cloud (VKS) 트랙 — Pull 기반 GitOps 권장

GitLab 공식 권고는 **명확히 pull 기반(GitOps)** 이다.

| 방식 | 평가 |
|---|---|
| **Pull (GitOps)** — Flux + `agentk` | ✅ **권장.** Flux가 클러스터 상태를 소스와 동기화, agentk가 Flux 설정 단순화 + 클러스터↔GitLab 접근 관리 + GitLab UI에서 클러스터 상태 시각화 |
| **Push — 수동 구성 K8s 타깃** | ❌ **"보안 모델이 약하므로 프로덕션에 사용하지 말 것."** 방화벽 개방과 cluster admin 권한 사용으로 위험 유발 |
| **Push — Kubernetes Agent 경유** | 웹소켓 인터페이스로 안전한 연결 수립 후 CI/CD가 변경을 푸시 |

**온프렘 이점**: 에이전트가 클러스터 내부에서 실행되며 **KAS(Kubernetes Agent Server)로 양방향 채널을 여는** 구조라, **방화벽·NAT 뒤의 클러스터와도 통신 가능**하다. 인바운드 방화벽 개방이 불필요하다.

**배포 게이트 (Admission)**
- **Kyverno** — 2026-03-16 **CNCF Graduated** 프로젝트. Cosign과 통합해 **admission 시점에 이미지 서명과 어테스테이션을 검증**하여 미서명·변조 이미지를 차단
- `ImageValidatingPolicy` / `VerifyImages`로 Cosign 서명 + **SLSA provenance를 Kubernetes admission에서 직접 검증**
- ArgoCD로 검증 정책을 배포하면 **GitOps로 관리되는 공급망 보안 게이트**가 성립
- 참고: Argo CD v3.3.6(2026-03-27)부터 릴리스 자체가 Cosign 서명 + SLSA L3 provenance 제공

> **도입 실무 권고**: 정책을 **먼저 Audit 모드로 배포**하여 어떤 이미지가 차단될지 관찰한 뒤, 각 팀이 CI에서 이미지 서명을 하도록 유도하고 나서 Enforce로 전환할 것.

### 3-2. Databricks Apps 트랙 — Workload Identity Federation

✅ **Databricks가 GitLab CI/CD용 워크로드 아이덴티티 페더레이션을 공식 지원한다.** Databricks 시크릿 없이 인증 가능하며, Databricks는 자동화 워크로드 인증에 **이 방식을 강력히 권장**한다.

**동작**: GitLab CI/CD가 발급한 워크로드 아이덴티티 토큰을 Databricks SDK/CLI가 자동으로 가져와 **Databricks OAuth 토큰으로 교환**한다.

**페더레이션 정책 파라미터**

| 항목 | 내용 |
|---|---|
| Issuer URL | GitLab 인스턴스 URL (예: `https://gitlab.com/example-group`) |
| Audiences | 기대하는 `aud` 값. **Databricks는 계정 ID 사용을 권장** |
| Subject | 프로젝트·브랜치·태그·MR을 식별하는 잡 컨텍스트 값의 조합 |
| Subject Claim | GitLab은 통상 `sub` |

```bash
databricks account service-principal-federation-policy create <sp-id> \
  --json '{"oidc_policy": {"issuer": "...", "audiences": ["..."], "subject": "..."}}'
```

```yaml
variables:
  DATABRICKS_AUTH_TYPE: env-oidc
  DATABRICKS_HOST: $[[ inputs.databricks-host ]]
  DATABRICKS_CLIENT_ID: $[[ inputs.databricks-client-id ]]

my_job:
  id_tokens:
    DATABRICKS_OIDC_TOKEN:
      aud: $[[ inputs.databricks-account-id ]]
```

### ⚠️ 온프렘 GitLab의 Issuer 도달성 — 확인 필요

**공식 문서는 self-managed GitLab 지원 여부를 명시하지 않으며, 예시는 `https://gitlab.com`만 참조한다.**

OIDC 토큰 검증은 검증자(Databricks 컨트롤 플레인)가 **issuer의 OIDC discovery 엔드포인트(`/.well-known/openid-configuration`)와 JWKS를 조회**하는 것이 전제다. **방화벽 안쪽의 온프렘 GitLab은 Databricks 클라우드에서 도달할 수 없으므로 WIF가 성립하지 않을 가능성이 높다.**

> 이 판단은 OIDC 프로토콜 동작에 근거한 **추론**이며 공식 문서의 명시적 진술이 아니다. 확정 전 Databricks 확인 필수.

**성립하지 않을 경우의 대안 (우선순위순)**
1. GitLab의 OIDC discovery/JWKS 엔드포인트만 리버스 프록시로 제한 공개 (issuer URL 일치 필요 — 난이도 있음)
2. 배포 잡을 **클라우드 측 Runner**에서 실행하고, GitLab ID 토큰 대신 **해당 클라우드의 워크로드 아이덴티티**(공개 issuer)로 Databricks에 페더레이션
   - ⚠️ Runner를 클라우드로 옮기는 것만으로는 해결되지 않는다. Runner 위치와 무관하게 GitLab ID 토큰의 발급자는 여전히 온프렘 GitLab이므로, **issuer를 클라우드 아이덴티티로 바꾸는 것이 핵심**이다.
3. Databricks 서비스 프린시펄 **OAuth 시크릿을 GitLab CI 변수로 관리** (Vault 연계 + 자동 로테이션) — 트렌드 역행이므로 최후 수단

> 각 대안의 장단점과 검증 절차는 `01-gitlab-databricks-wif-verification.md` §5 참조.

💡 이 항목은 **CI/CD 아키텍처의 최우선 검증 대상**이다. 결과에 따라 Databricks 트랙의 배포 경로 전체가 달라진다.

### 3-3. 트랙 비교 정리

| 구분 | Private Cloud (VKS) | Databricks Apps |
|---|---|---|
| 배포 산출물 | 컨테이너 이미지 | 소스 + `databricks.yml` 번들 |
| 배포 방식 | Flux/ArgoCD **pull 기반 GitOps** | `databricks bundle deploy` → **`bundle run`** (push) |
| 인증 | agentk ↔ KAS 양방향 채널 (방화벽 친화) | **WIF (OIDC)** ⚠️ 온프렘 issuer 도달성 확인 필요 |
| 배포 게이트 | **Kyverno + Cosign** admission 검증 | 워크스페이스 관리자의 리소스 접근 승인 |
| 무결성 증적 | 이미지 서명 + SLSA provenance | 커밋 해시 + 번들 배포 기록 (**동등 증적 별도 정의 필요**) |
| 배포 완료 판정 | Flux 동기화 상태 | **헬스체크 통과** (`bundle deploy`만으로는 구버전 서빙) |

---

## 4. 플랫폼 엔지니어링 관점 — AX App Market은 IDP다

조사 과정에서 확인된 가장 중요한 프레이밍이다. **AX App Market이 하려는 일은 업계에서 이미 이름이 붙어 있는 것 — Internal Developer Portal(IDP)과 Golden Path다.**

- **Golden Path / Paved Road**: 사전 구성된 의견 있는(opinionated) 워크플로로 모범사례를 코드화. Netflix가 "paved road", Spotify가 "golden path"로 명명.
- **Developer Portal**: 개발자가 서비스·API·템플릿·문서를 발견하는 중앙 UI
- **Self-service**: 티켓 없이 프로비저닝과 day-2 운영 수행

> **핵심 패턴**: 플랫폼 팀이 **프로젝트 템플릿 + CI/CD 파이프라인 + 인프라 설정 + 보안 통제 + 관측성 배선**을 미리 만들어 두고, 그 전체 여정을 포털의 셀프서비스 워크플로로 노출한다. 결과는 몇 주 걸리던 신규 서비스 셋업이 몇 분으로 줄고, **컴플라이언스가 최초 커밋부터 내장된다.**

**시장 성숙도**: Gartner는 대규모 소프트웨어 엔지니어링 조직의 **80%가 2026년까지 플랫폼 엔지니어링 팀을 보유**할 것으로 전망(2022년 45% 대비).

💡 **AX App Market 적용**

1. **AX Playground = Golden Path의 시작점**으로 재정의하는 것이 좋다. PDF의 "표준 템플릿·가이드"는 단순 문서가 아니라 **파이프라인·보안 정책·로깅 배선이 이미 결선된 실행 가능한 스캐폴드**여야 한다. 그래야 "공통 검증 기준"이 개발자에게 부담이 아니라 기본값이 된다.
2. Databricks Apps의 **로그 비영속** 특성(→ `databricks-apps-reference.md` §8)도 템플릿에 구조화 로깅을 기본 탑재하는 방식으로 흡수하는 것이 개별 개발자에게 맡기는 것보다 안전하다.
3. 앱마켓의 '앱 탐색'은 IDP의 **서비스 카탈로그**에 해당한다. 소유자(owner), 지원 상태, SLA, 의존성 정보를 함께 노출하는 것이 업계 표준이다.

---

## 5. AX App Market 검증 게이트 설계 제언

PDF의 검증 파이프라인 항목을 조사 결과에 맞춰 구체화한 안이다.

| 단계 | 게이트 | 구현 수단 | 트랙 |
|---|---|---|---|
| 커밋 | Secret Detection | GitLab Secret Detection (Scan Execution Policy로 강제) | 공통 |
| 빌드 | SAST | GitLab SAST / Advanced SAST | 공통 |
| 빌드 | SCA + **SBOM 생성** | GitLab Dependency Scanning (**CycloneDX**) | 공통 |
| 빌드 | 라이선스 검증 | License Approval Policy | 공통 |
| 빌드 | 컨테이너 스캔 | GitLab Container Scanning (`gl-sbom-report.cdx.json`) | Private Cloud |
| 빌드 | **서명 + Provenance** | Cosign 서명 + SLSA provenance 생성 | Private Cloud |
| 빌드 | **동등 증적** | 커밋 해시 + 번들 배포 기록 + 파이프라인 서명 | Databricks |
| 승인 | 스캔 결과 기반 승인 | **Merge Request Approval Policy** | 공통 |
| 배포 | **서명 검증 후 실행 허용** | Kyverno `ImageValidatingPolicy` (Audit → Enforce) | Private Cloud |
| 배포 | 리소스 접근 승인 | 워크스페이스 관리자 승인 | Databricks |
| 배포 | **배포 완료 판정** | 헬스체크 통과 기준 | 공통 |
| Agent App | **프롬프트 인젝션 / 과도한 권한 / 자원 소모** | OWASP LLM Top 10 2026 + Agentic Top 10 기반 체크리스트, Databricks Agent Evaluation | Agent App |
| Agent App | **AI-BOM** | 사용 모델·에이전트·툴 인벤토리 등록 | Agent App |
| 운영 | 취약점 우선순위 | ASPM / reachability 기반 트리아지 (도구 도입 시) | 공통 |

**설계 원칙 3가지**

1. **강제는 플랫폼이, 작성은 개발자가 하지 않는다.** 모든 필수 게이트는 Scan Execution / Pipeline Execution Policy로 주입하여 `[skip ci]` 우회를 차단한다.
2. **Audit 먼저, Enforce 나중.** 특히 Kyverno 서명 검증은 차단 대상을 먼저 관찰하고 팀들이 서명을 붙이게 한 뒤 전환한다.
3. **두 트랙의 증적은 형태가 달라도 등급은 같아야 한다.** "공통 검증 기준"의 실질은 도구 통일이 아니라 **증적 등급의 동등성**이다.

---

## 6. 확인 필요 사항

| # | 항목 | 영향 |
|---|---|---|
| 1 | **온프렘 GitLab을 OIDC issuer로 하는 Databricks WIF 성립 여부** | Databricks 트랙 배포 경로 전체 (§3-2) |
| 2 | **GitLab 라이선스 tier (Ultimate 여부)** | 보안 정책·컴플라이언스 프레임워크·다수 스캐너가 Ultimate 전용 |
| 3 | 온프렘 GitLab Runner의 인터넷 아웃바운드 허용 범위 | PyPI/npm 의존성 설치, Databricks CLI 호출 가능 여부 |
| 4 | 기존 Jenkins·ArgoCD·Harbor와 GitLab CI의 역할 분담 | PDF 참고 구성도에 4종이 병존 — 중복 정리 필요 |
| 5 | Cosign 서명 키 관리 방식 (KMS / Fulcio keyless) | 온프렘에서 Fulcio·Rekor 접근이 막히면 keyless 불가 → 자체 키 관리 필요 |
| 6 | EU CRA 적용 대상 여부 | 대상이면 SBOM·취약점 보고가 선택이 아닌 의무 |
| 7 | ASPM 도구 도입 계획 유무 | 미도입 시 스캔 결과 트리아지를 수동 운영해야 함 |

---

## 7. 참고 링크

### GitLab 공식 문서

- [Static application security testing (SAST)](https://docs.gitlab.com/user/application_security/sast/)
- [GitLab Advanced SAST](https://docs.gitlab.com/user/application_security/sast/gitlab_advanced_sast/)
- [Dependency scanning by using SBOM](https://docs.gitlab.com/user/application_security/dependency_scanning/dependency_scanning_sbom/)
- [Container scanning](https://docs.gitlab.com/user/application_security/container_scanning/)
- [Secret detection](https://docs.gitlab.com/user/application_security/secret_detection/)
- [Policies (개요)](https://docs.gitlab.com/user/application_security/policies/)
- [Scan execution policies](https://docs.gitlab.com/user/application_security/policies/scan_execution_policies/)
- [Pipeline execution policies](https://docs.gitlab.com/user/application_security/policies/pipeline_execution_policies/)
- [Merge request approval policies](https://docs.gitlab.com/user/application_security/policies/merge_request_approval_policies/)
- [Compliance frameworks](https://docs.gitlab.com/user/compliance/compliance_frameworks/)
- [License approval policies](https://docs.gitlab.com/user/compliance/license_approval_policies/)
- [OpenID Connect (OIDC) Authentication Using ID Tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/)
- [Connect to cloud services](https://docs.gitlab.com/ci/cloud_services/)
- [Connecting a Kubernetes cluster with GitLab](https://docs.gitlab.com/user/clusters/agent/)
- [Using GitOps with a Kubernetes cluster](https://docs.gitlab.com/user/clusters/agent/gitops/)
- [Best practices for using the GitLab integration with Kubernetes](https://docs.gitlab.com/user/clusters/agent/enterprise_considerations/)

### Databricks 공식 문서

- [Enable workload identity federation for GitLab CI/CD](https://docs.databricks.com/aws/en/dev-tools/auth/provider-gitlab)
- [Enable workload identity federation in CI/CD](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-provider)
- [Configure a federation policy](https://docs.databricks.com/gcp/en/dev-tools/auth/oauth-federation-policy)

### 공급망 보안 · 정책

- [Kyverno ImageValidatingPolicy](https://kyverno.io/docs/policy-types/image-validating-policy/)
- [Verification of Argo CD Artifacts](https://argo-cd.readthedocs.io/en/stable/operator-manual/signed-release-assets/)
- [Argo CD + Kyverno: the GitOps policy as code your cluster was missing](https://blog.stephane-robert.info/en/post/argo-cd-kyverno-gitops-policy-as-code/)
- [The 2026 Guide to Software Supply Chain Security (Cloudsmith)](https://cloudsmith.com/blog/the-2026-guide-to-software-supply-chain-security-from-static-sboms-to-agentic-governance)
- [Supply Chain Security: SBOM, Sigstore and Admission Control](https://stribog.com/blog/oss-supply-chain-security-sbom-sigstore-slsa-kubernetes)
- [CI/CD Pipeline Supply Chain Attacks Surge 2026](https://dev.to/x4nent/cicd-pipeline-supply-chain-attacks-surge-2026-security-response-strategy-3n44)

### AI 보안

- [OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [OWASP LLM Top 10 2026: 3 shifts security teams must act on (Mend)](https://www.mend.io/blog/owasp-llm-top-10-2026/)

### 규제 · ASPM · 플랫폼 엔지니어링

- [EU Cyber Resilience Act: 2026 Compliance Guide (Mend)](https://www.mend.io/blog/eu-cyber-resilience-act-compliance-guide/)
- [SBOM Requirements in the EU's CRA (FOSSA)](https://fossa.com/blog/sbom-requirements-cra-cyber-resilience-act/)
- [Application Security Trends Every DevSecOps Team Should Watch in 2026 (OX Security)](https://www.ox.security/blog/application-security-trends-in-2026/)
- [ASPM with Reachability Analysis (Phoenix Security)](https://phoenix.security/aspm-reachability-analysis-overview/)
- [Platform engineering and internal developer portals: a multivocal literature review (Frontiers)](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2026.1814498/full)
- [Platform Engineering, IDPs, and Golden Paths (digital.ai)](https://digital.ai/catalyst-blog/platform-engineering-idps-and-golden-paths/)

---

## 관련 문서

- `docs/AX앱마켓구성1.pdf` — AX App Market 기획 초안
- `docs/databricks-apps-reference.md` — Databricks Apps 기술 레퍼런스
