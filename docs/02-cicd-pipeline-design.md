# ② CI/CD 파이프라인 상세 설계

> **목적**: 온프렘 GitLab을 중심축으로, Private Cloud(VKS)와 Databricks Apps 두 런타임에 대한 검증·승인·배포 파이프라인을 설계한다.
> **작성일**: 2026-09-10
> **선행 문서**: `cicd-devsecops-research.md`, `01-gitlab-databricks-wif-verification.md`
> **전제**: 인증은 시나리오 A(WIF 성립)를 기본으로 기술한다. 시나리오 B 확정 시 §7-2의 대체 설계를 적용한다.

---

## 1. 설계 원칙

선행 조사에서 도출한 세 가지를 설계 전반에 관통시킨다.

1. **강제는 플랫폼이, 작성은 개발자가 하지 않는다.** 필수 게이트는 Security Policy Project로 주입한다. 개발자의 `.gitlab-ci.yml`에는 보안 잡이 등장하지 않으며, `[skip ci]`로 우회할 수 없다.
2. **두 트랙의 증적은 형태가 달라도 등급은 같다.** "공통 검증 기준"의 실질은 도구 통일이 아니라 증적 등급의 동등성이다.
3. **Audit 먼저, Enforce 나중.** 특히 서명 검증은 차단 대상을 관찰한 뒤 전환한다.

여기에 앱마켓 고유 원칙을 하나 더한다.

4. **배포 완료의 정의는 "헬스체크 통과"다.** `bundle deploy` 성공이나 Flux 동기화 신호가 아니다. 앱마켓에 표시되는 상태는 실제 서빙 중인 버전을 반영해야 한다.

---

## 2. 저장소 구조

```
ax-platform/                          # 최상위 그룹 (컴플라이언스 프레임워크 부착 지점)
├── policies/
│   └── security-policies/            # Security Policy Project (정책 as code)
├── templates/
│   ├── ci-templates/                 # 공통 CI 템플릿 (스테이지 정의, 잡 추상화)
│   ├── app-scaffold-webapp/          # Golden Path: 일반 Web App
│   ├── app-scaffold-databricks/      # Golden Path: Databricks Apps
│   └── app-scaffold-agent/           # Golden Path: Agent App
├── apps/
│   ├── <app-name-1>/                 # 앱별 소스 저장소
│   └── <app-name-2>/
├── gitops/
│   └── vks-manifests/                # Private Cloud 트랙 배포 상태 (Flux 소스)
└── marketplace/
    └── app-market/                   # AX App Market 서비스 자체
```

**핵심**: 앱 저장소는 **컴플라이언스 프레임워크 레이블**을 부착받는다. 레이블이 곧 적용될 정책 세트를 결정한다.

| 레이블 | 의미 | 적용 정책 |
|---|---|---|
| `runtime:private-cloud` | VKS 배포 | 이미지 빌드·스캔·서명·admission 검증 |
| `runtime:databricks` | Databricks Apps 배포 | 번들 검증·배포 증적 |
| `type:agent` | Agent App (런타임 레이블과 **병행 부착**) | AI 보안 게이트 추가 |
| `tier:critical` | 중요 업무 앱 | 승인자 수 상향, 추가 심사 |

---

## 3. 브랜치 · 환경 전략

| 브랜치 | 대상 환경 | 배포 방식 | 승인 |
|---|---|---|---|
| feature/* | 없음 | 검증만 | — |
| `main` (보호) | dev | 자동 | MR 승인 (스캔 결과 기반) |
| `release/*` (보호) | staging | 자동 | MR 승인 |
| 태그 `v*` (보호) | **prod** | **수동 트리거** | **보호된 환경 승인** |

**보호된 환경(protected environment)을 승인 게이트로 쓰는 것이 핵심이다.** 운영 배포 잡은 보호된 환경에서만 실행되므로, ID 토큰 발급 자체가 승인 뒤로 밀린다. 승인받지 못한 파이프라인은 운영 자격증명을 **획득조차 하지 못한다.**

---

## 4. 공통 파이프라인 골격

두 트랙이 공유하는 스테이지다. 트랙별 차이는 `build` 이후에 나타난다.

```
┌─────────┬──────────┬──────────┬───────────┬─────────┬─────────┬──────────┬──────────┐
│ validate│ build    │ test     │ security  │ package │ approve │ deploy   │ verify   │
├─────────┼──────────┼──────────┼───────────┼─────────┼─────────┼──────────┼──────────┤
│ 메타데이터│ 빌드      │ 단위      │ SAST      │ 서명/    │ 환경     │ 트랙별    │ 헬스체크  │
│ 린트     │          │ 통합      │ SCA+SBOM  │ 증적     │ 승인     │ 배포     │ 증적등록  │
│         │          │          │ Secret    │         │         │          │          │
│         │          │          │ License   │         │         │          │          │
└─────────┴──────────┴──────────┴───────────┴─────────┴─────────┴──────────┴──────────┘
                                 ↑ 정책 주입 구간 (개발자 작성 아님)
```

### 4-1. 정책 주입 — Security Policy Project

`security` 스테이지 전체는 **Scan Execution Policy**로 주입한다. 앱 저장소의 `.gitlab-ci.yml`에는 이 잡들이 존재하지 않는다.

```yaml
# policies/security-policies/.gitlab/security-policies/policy.yml (개념 예시)
scan_execution_policy:
  - name: AX 공통 보안 스캔
    enabled: true
    rules:
      - type: pipeline
        branches: ["*"]
    actions:
      - scan: sast
      - scan: dependency_scanning     # CycloneDX SBOM 생성
      - scan: secret_detection
    policy_scope:
      compliance_frameworks:
        - id: ax-common

  - name: 컨테이너 스캔 (Private Cloud 트랙)
    enabled: true
    rules:
      - type: pipeline
        branches: ["*"]
    actions:
      - scan: container_scanning
    policy_scope:
      compliance_frameworks:
        - id: runtime-private-cloud
```

**승인 규칙**은 Merge Request Approval Policy로 스캔 결과에 연동한다.

```yaml
approval_policy:
  - name: 심각 취약점 발견 시 보안팀 승인 필수
    rules:
      - type: scan_finding
        scanners: [sast, dependency_scanning, container_scanning]
        severity_levels: [critical, high]
        vulnerabilities_allowed: 0
    actions:
      - type: require_approval
        approvals_required: 1
        role_approvers: [maintainer]
        # 실제로는 보안팀 그룹 지정
```

> ⚠️ **Compliance pipelines는 deprecated.** 신규 설계는 Pipeline Execution Policy 기반으로 간다. 파이프라인 전체를 표준화해야 하는 앱 유형에는 `override_project_ci`, 개발자 파이프라인을 확장만 하는 경우에는 `inject` 전략을 쓴다.

### 4-2. 개발자가 작성하는 부분

Golden Path 스캐폴드가 생성해 주는 최소 형태다.

```yaml
# apps/<app-name>/.gitlab-ci.yml — 개발자 저장소
include:
  - project: ax-platform/templates/ci-templates
    file: /databricks-app.yml          # 또는 /webapp.yml
    inputs:
      app_name: my-app
      databricks_host_dev: $DBX_HOST_DEV
      databricks_host_prod: $DBX_HOST_PROD

# 앱 고유 테스트만 개발자가 작성
unit-test:
  stage: test
  script:
    - pytest tests/
```

보안 잡이 보이지 않는 것이 의도된 설계다. 개발자는 자기 앱의 테스트만 신경 쓴다.

---

## 5. 트랙 A — Private Cloud (VKS)

### 5-1. 흐름

```
build ──▶ 이미지 빌드 (Kaniko/Buildah)
   │
security ─▶ SAST · SCA(SBOM) · Secret · License · Container Scan
   │
package ──▶ Harbor push
   │        Cosign 서명
   │        SLSA provenance 생성 + 첨부
   │
approve ──▶ 보호된 환경 승인 (prod)
   │
deploy ───▶ GitOps 저장소 매니페스트 갱신 (이미지 태그/다이제스트)
   │        Flux가 감지하여 동기화 (pull 기반)
   │        ┌─────────────────────────────┐
   │        │ Kyverno admission 검증       │
   │        │ - Cosign 서명 확인           │
   │        │ - SLSA provenance 확인       │
   │        │ - 미서명 이미지 차단          │
   │        └─────────────────────────────┘
   │
verify ───▶ 헬스체크 → 앱마켓 상태 등록
```

### 5-2. 배포 방식 — Pull 기반 GitOps

GitLab 공식 권고를 따른다. **수동 구성 push 방식은 "보안 모델이 약하므로 프로덕션 사용 금지"** 로 명시되어 있다.

- **Flux + `agentk`** 조합. Flux가 클러스터 상태를 동기화하고, agentk가 GitLab 접근 관리와 클러스터 상태 시각화를 담당한다.
- **온프렘 이점**: agentk가 클러스터 내부에서 KAS로 **양방향 채널**을 열므로 인바운드 방화벽 개방이 불필요하다.

파이프라인은 **클러스터를 직접 건드리지 않는다.** GitOps 저장소의 이미지 다이제스트만 갱신하고 끝난다.

```yaml
deploy:prod:
  stage: deploy
  environment:
    name: production          # 보호된 환경 → 승인 게이트
  rules:
    - if: $CI_COMMIT_TAG =~ /^v/
      when: manual
  script:
    # 태그가 아닌 다이제스트로 고정 — 태그는 변조 가능
    - yq -i '.spec.template.spec.containers[0].image = "'"$IMAGE_DIGEST"'"' \
        gitops/vks-manifests/apps/$APP_NAME/deployment.yaml
    - git commit -am "deploy($APP_NAME): $IMAGE_DIGEST"
    - git push
```

### 5-3. 서명과 admission 검증

**Kyverno**는 2026-03-16 CNCF Graduated 프로젝트로, Cosign과 통합해 admission 시점에 서명과 어테스테이션을 검증한다.

```yaml
# Kyverno ImageValidatingPolicy (개념)
# 1단계: Audit 모드로 배포 → 차단될 이미지 관찰
# 2단계: 각 팀이 CI에서 서명 적용
# 3단계: Enforce 전환
validationFailureAction: Audit   # → 이후 Enforce
```

> **도입 순서를 지킬 것.** 처음부터 Enforce로 걸면 기존 워크로드가 멈춘다. Audit으로 관찰 → 서명 적용 유도 → Enforce가 업계 표준 절차다.

**Cosign 키 관리**는 별도 결정이 필요하다.

| 방식 | 온프렘 적합성 |
|---|---|
| **Keyless (Fulcio + Rekor)** | ⚠️ 공용 Sigstore 인프라에 아웃바운드 접근 필요. 폐쇄망이면 불가 |
| **KMS 기반 키** | ✅ 온프렘 KMS/HSM 연계 가능 |
| **자체 Sigstore 스택** | 운영 부담 크나 폐쇄망에서 keyless 유지 가능 |

→ `01` 문서 §6과 함께 **Runner 아웃바운드 정책 확인 시 Sigstore 도달성도 같이 확인**할 것.

---

## 6. 트랙 B — Databricks Apps

### 6-1. 흐름

```
validate ─▶ app.yaml / databricks.yml 스키마 검증
   │        requirements.txt 고정 버전 확인
   │        권한 모드 검사 (SP 모드면 승인 레이블 필수) — §6-3
   │        SQL Warehouse 참조 검사 (공용 웨어하우스 강제) — `04` §6-2
   │
security ─▶ SAST · SCA(SBOM) · Secret · License
   │        (컨테이너 스캔 없음 — 이미지 배포가 아님)
   │
package ──▶ 동등 증적 생성
   │        - 커밋 해시
   │        - SBOM (CycloneDX)
   │        - 스캔 결과
   │        - 파이프라인 서명
   │
approve ──▶ 보호된 환경 승인 (prod)
   │
deploy ───▶ databricks bundle deploy    ← 소스 업로드만. 앱 재시작 안 함!
   │        databricks bundle run       ← 반드시 실행
   │
verify ───▶ 상태 폴링 (기동 완료까지)
   │        헬스체크 + 버전 확인
   │        앱마켓 상태 등록
```

### 6-2. ⚠️ 반드시 반영해야 할 두 함정

문서에 명시된 함정이며, 놓치면 **CI는 성공인데 앱은 구버전을 서빙**한다.

1. `databricks bundle deploy`는 소스를 올리고 리소스를 갱신할 뿐 **앱 프로세스를 재시작하지 않는다.**
2. `databricks bundle run`은 **시작 신호만 보내고 즉시 종료된다.** 앱은 아직 기동 전일 수 있고, 의존성 누락·환경변수 누락·포트 충돌로 기동 중 실패할 수 있다.

```yaml
deploy:databricks:prod:
  stage: deploy
  environment:
    name: production
  variables:
    DATABRICKS_AUTH_TYPE: env-oidc
    DATABRICKS_HOST: $DBX_HOST_PROD
    DATABRICKS_CLIENT_ID: $DBX_SP_PROD
  id_tokens:
    DATABRICKS_OIDC_TOKEN:
      aud: $DBX_ACCOUNT_ID
  rules:
    - if: $CI_COMMIT_TAG =~ /^v/
      when: manual
  script:
    - databricks bundle validate -t prod
    - databricks bundle deploy -t prod
    - databricks bundle run -t prod app_resource     # 필수
  # verify 스테이지에서 실제 기동 확인

verify:databricks:prod:
  stage: verify
  needs: [deploy:databricks:prod]
  script:
    - ./scripts/wait-for-app.sh                      # 상태 폴링
    - ./scripts/assert-version.sh "$CI_COMMIT_SHA"   # 서빙 중인 버전 확인
```

**`assert-version.sh`가 이 설계의 핵심이다.** 앱이 자신의 커밋 해시를 노출하는 엔드포인트(`/healthz` 등)를 갖게 하고, 파이프라인이 그 값을 배포한 커밋과 대조한다. 이것이 통과해야 배포 완료다. → **Golden Path 스캐폴드에 기본 탑재할 것.**

### 6-3. 권한 모델

`databricks-apps-reference.md` §4에서 정리한 원칙을 적용한다.

- **OBO(On-Behalf-Of)를 기본으로 강제한다.** UC의 행 필터·컬럼 마스킹이 자동 상속되므로 데이터 거버넌스 책임을 플랫폼이 진다.
- **SP 모드는 예외 승인 대상.** SP 모드는 모든 사용자가 동일 권한이 되어 데이터 접근 통제가 앱 코드 책임으로 넘어온다 — 스캐너로 잡아내기 가장 어려운 유형이다.
- `validate` 스테이지에서 **앱 설정의 권한 모드를 검사**하고, SP 모드면 승인 레이블 없이는 파이프라인을 실패시킨다.
- OAuth 스코프는 최소 원칙. 선언하지 않은 기능은 사용자에게 권한이 있어도 Databricks가 차단한다.

### 6-4. 로그 영속화

앱 컴퓨트 종료 시 로그가 소실되므로, **스캐폴드에 구조화 로깅 + UC 볼륨 출력을 기본 탑재**한다. 개별 개발자에게 맡기지 않는다.

---

## 7. 인증 · 시크릿 모델

### 7-1. 시나리오 A (WIF 성립) — 기본 설계

| 대상 | 방식 |
|---|---|
| Databricks (dev) | WIF. subject = `main` 브랜치 |
| Databricks (prod) | WIF. subject = **보호된 태그**, 보호된 환경 |
| VKS 클러스터 | agentk ↔ KAS 양방향 채널 (자격증명 CI에 없음) |
| Harbor | 배포 전용 로봇 계정, 보호된 변수 |
| Cosign 키 | KMS 참조 (§5-3) |

**환경별 SP 분리**가 원칙이다. dev SP는 prod 워크스페이스에 접근할 수 없어야 한다.

### 7-2. 시나리오 B (WIF 불가) — 대체 설계

`01` 문서 §5의 대안이 확정되면 위 표의 Databricks 행만 교체한다. **나머지 설계는 그대로 유효하다.**

- **B-1 (JWKS 제한 공개)**: 표 변경 없음. issuer 도달 경로만 확보된 것이므로 설계 동일.
- **B-2 (클라우드 Runner + 클라우드 아이덴티티)**: 배포 잡에 Runner 태그 지정 추가. subject 세분화를 못 하므로 **Runner 태그 접근 제어가 인증 경계**가 된다.
- **B-3 (OAuth 시크릿)**: Vault 연계 + 자동 로테이션 + 보호된 변수. 감사 로그 필수.

---

## 8. Agent App 추가 게이트

`type:agent` 레이블이 붙으면 다음 잡이 추가 주입된다. 일반 코드 스캔(SAST/SCA/Secret)은 프롬프트 인젝션이나 과도한 권한을 잡아내지 못한다.

| 게이트 | 근거 | 판정 |
|---|---|---|
| **AI-BOM 등록** | 사용 모델·에이전트·툴 인벤토리 | 미등록 시 실패 |
| **툴 권한 범위 검토** | OWASP LLM03 과도한 권한 — 모델 출력이 자율적으로 셸 실행·API 호출·DB 트랜잭션 수행 | 셸 실행/쓰기 권한 툴은 승인 필수 |
| **시스템 프롬프트 하드닝 확인** | OWASP LLM01 프롬프트 인젝션 | 체크리스트 |
| **데이터 반출 경로 검토** | OWASP LLM02 민감정보 노출 | Genie space 테이블 목록 검토 (최대 25개) |
| **자원 한도 설정** | Unbounded Consumption — 재무적 DoS | 토큰·호출 한도 설정 여부 |
| **품질 평가** | Databricks Agent Evaluation | 기준치 미달 시 승인 보류 |

> AI 모델은 **기존 스캐너가 읽을 수 없는 서드파티 의존성**이다. 별도 게이트 없이는 통제 공백이 생긴다.

---

## 9. 증적 수집과 앱마켓 연계

### 9-1. 트랙별 증적 대응표

동일 등급의 증적을 형태만 달리 확보한다.

| 증적 항목 | Private Cloud | Databricks |
|---|---|---|
| 무엇이 들어있나 | CycloneDX SBOM (소스 + 컨테이너) | CycloneDX SBOM (소스) |
| 어떻게 만들어졌나 | **SLSA provenance** | 커밋 해시 + 파이프라인 ID + 번들 배포 기록 |
| 신뢰된 빌더인가 | **Cosign 서명** | 파이프라인 서명 |
| 실행 허용 판정 | **Kyverno admission** | 워크스페이스 관리자 리소스 승인 |
| 누가 승인했나 | 보호된 환경 승인 이력 | 보호된 환경 승인 이력 |
| 실제 서빙 버전 | 매니페스트 다이제스트 | `assert-version` 결과 |

### 9-2. 앱마켓 등록

`verify` 스테이지 성공 시에만 앱마켓에 상태를 등록한다.

```yaml
register:marketplace:
  stage: verify
  needs: [verify:databricks:prod]     # 또는 verify:vks:prod
  script:
    - |
      curl -X POST "$APP_MARKET_API/apps/$APP_NAME/deployments" \
        -H "Authorization: Bearer $MARKET_TOKEN" \
        -d @- <<EOF
      {
        "runtime": "$RUNTIME",
        "workspace_id": "$DBX_WORKSPACE_ID",
        "version": "$CI_COMMIT_TAG",
        "commit": "$CI_COMMIT_SHA",
        "pipeline_url": "$CI_PIPELINE_URL",
        "evidence": {
          "sbom": "$SBOM_URL",
          "scan_report": "$SCAN_URL",
          "signature": "$SIGNATURE_REF",
          "approved_by": "$CI_ENVIRONMENT_ACTION_USER"
        },
        "health": "passed"
      }
      EOF
```

**`workspace_id`를 반드시 포함한다.** Databricks는 워크스페이스당 앱 100개 고정 한도가 있어 다중 워크스페이스 운영이 불가피하다. 메타데이터에 워크스페이스 정보가 없으면 나중에 스키마를 뒤집어야 한다.

### 9-3. 운영 지표 수집

| 지표 | Private Cloud | Databricks | 통합 |
|---|---|---|---|
| 상태·장애 | Prometheus / Grafana | Insights 탭 + 폴링 | 정규화 계층 |
| 로그 | Loki | UC 볼륨 (앱이 직접 기록) | 정규화 계층 |
| 감사 | GitLab 감사 로그 | `system.access.audit` | 정규화 계층 |
| 사용 현황 | Ingress 메트릭 | Insights Viewers | 정규화 계층 |
| **비용** | 자원 점유 기반 | `system.billing.usage` (DBU) | **공통 환산 기준 필요** |

**비용 지표는 단위가 다르다.** DBU/시간과 자원 점유를 나란히 보여주려면 월 원화 환산 등 공통 기준을 먼저 정의해야 한다.

> 💰 Databricks 측 입력값(DBU 소모 구조, 실효 단가, 규모별 총량)은 `04-cost-model.md`에 정리되어 있다. 수집 계층이 반드시 포함해야 할 것: **앱별 비용 귀속(showback)** — `system.billing.usage`의 Apps SKU + `created_by`로 앱 단위 집계가 가능하고, 소유 조직에 월 비용을 노출하는 것만으로 방치 앱이 줄어든다. Agent App은 모델 서빙·Genie 변동비를 별도 항목으로 분리할 것. → `04-cost-model.md` §6-4

---

## 10. 단계적 적용 로드맵

한 번에 다 하지 않는다. 각 단계가 독립적으로 가치를 낸다.

| 단계 | 범위 | 산출물 | 선행 조건 |
|---|---|---|---|
| **0** | WIF 검증 | 인증 방식 확정 | — |
| **1** | 공통 보안 스캔 주입 | Scan Execution Policy, 컴플라이언스 프레임워크 | GitLab Ultimate 확인 |
| **2** | Databricks 트랙 파이프라인 | 번들 배포 + `assert-version` + 스캐폴드 | 0단계 완료 |
| **3** | 승인 게이트 | 보호된 환경, MR Approval Policy | 1단계 |
| **4** | 앱마켓 연계 | 등록 API, 증적 저장 | 2·3단계 |
| **5** | Private Cloud 트랙 | 이미지 서명, Kyverno **Audit** | Cosign 키 방식 결정 |
| **6** | Kyverno **Enforce** 전환 | 공급망 게이트 완성 | 5단계 관찰 기간 경과 |
| **7** | Agent App 게이트 | AI-BOM, 툴 권한 검토 | 4단계 |
| **8** | 운영 지표 정규화 | 통합 대시보드, 비용 환산 | 4단계 |

**1안(Databricks Apps 우선)과 정합한다.** 0→1→2→3→4까지가 1안의 최소 실행 범위이고, Private Cloud 트랙(5·6)은 그 다음이다.

---

## 11. 미결 사항

| # | 항목 | 영향 | 참조 |
|---|---|---|---|
| 1 | WIF 성립 여부 | §7 인증 모델 전체 | `01` 문서 |
| 2 | GitLab Ultimate 여부 | §4 정책 주입 가능 여부 — **1단계가 막힘** | `cicd-devsecops-research.md` §6 |
| 3 | Cosign 키 관리 방식 | §5-3, 5단계 착수 조건 | 본 문서 §5-3 |
| 4 | Runner 아웃바운드 (PyPI/npm/Sigstore/Databricks) | 다수 잡의 실행 가능성 | `01` 문서 §6 |
| 5 | Jenkins·ArgoCD·Harbor와 GitLab CI 역할 분담 | 도구 중복 정리 | PDF 참고 구성도 |
| 6 | 앱마켓 등록 API 스펙 | §9-2 | ③ 문서에서 다룸 |
| 7 | 다중 워크스페이스 운영 방식 | §9-2 메타데이터 스키마 | ③ 문서에서 다룸 |

> ⚠️ **2번이 1단계를 막는 실질적 선행 조건이다.** 보안 정책·컴플라이언스 프레임워크 다수가 Ultimate 전용이므로, tier 확인이 WIF 검증과 병행되어야 한다.

---

## 관련 문서

- `docs/01-gitlab-databricks-wif-verification.md` — WIF 검증 설계
- `docs/04-cost-model.md` — 운영 비용 모델 (§6-2 공용 웨어하우스 강제, §6-4 앱별 비용 귀속)
- `docs/05-physical-architecture.md` — 물리 아키텍처 (계정·네트워크 경로, 앱마켓 배치)
- `docs/cicd-devsecops-research.md` — CI/CD·DevSecOps 자료조사
- `docs/databricks-apps-reference.md` — Databricks Apps 기술 레퍼런스
