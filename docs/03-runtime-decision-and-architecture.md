# ③ 런타임 판정 기준 및 To-Be 전체 구성

> **목적**: AX App의 런타임 배치 기준을 판정 가능한 형태로 확정하고, AX App Market의 To-Be 전체 구성을 정의한다. 원 기획서(`AX앱마켓구성1.pdf`)의 "전체 구성을 그려보자"에 대한 산출물.
> **작성일**: 2026-09-10
> **선행 문서**: `databricks-apps-reference.md`, `cicd-devsecops-research.md`, `01`, `02`

### 전제 가정

미확정 항목이 있어 다음을 가정하고 작성한다. 확정 시 해당 절만 수정하면 되도록 국소화했다.

| # | 가정 | 미확정 시 영향 | 확정처 |
|---|---|---|---|
| A1 | Databricks 서버리스에서 온프렘 시스템으로의 **직접 아웃바운드는 불가** | §2 판정 기준 1번 | `databricks-apps-reference.md` §11-3 |
| A2 | Databricks 계정 SSO의 IdP를 **Keycloak(OIDC)로 연동 가능** | §5 인증 설계 | Azure Databricks면 Entra ID 고정 |
| A3 | GitLab **Ultimate** tier | §4 검증 게이트 강제 | `02` 문서 §11-2 |
| A4 | WIF 시나리오 A (성립) | §4 배포 인증 | `01` 문서 |

---

## 1. 판정 원칙

기획서의 "데이터브릭스 내 데이터가 필요한 경우"라는 기준은 실무에서 갈리지 않는다. 업무앱 대부분이 데이터를 필요로 하고, Databricks 데이터는 SQL Warehouse·JDBC로 Private Cloud에서도 접근 가능하기 때문이다.

따라서 판정을 **세 층으로 분리**한다.

```
1층. 차단 조건   — Databricks Apps로 "갈 수 없는" 이유가 있는가?     → 있으면 Private Cloud 확정
2층. 강한 선호   — Databricks Apps여야 "이득이 큰" 이유가 있는가?   → 있으면 Databricks 확정
3층. 기본값     — 둘 다 아니면 1안에 따라 Databricks Apps
```

**차단 조건을 먼저 보는 것이 핵심이다.** 선호도부터 따지면 물리적으로 불가능한 배치를 검토하느라 시간을 쓴다.

---

## 2. 런타임 판정 트리

```mermaid
flowchart TD
    START["AX App 등록 신청"]

    subgraph L1["1층 · 차단 조건 (하나라도 YES면 Private Cloud)"]
        Q1{"사내 시스템 직접 연동 필요?<br/>MES · SRM · ERP · Wehub · CRM"}
        Q2{"커스텀 컨테이너 이미지<br/>또는 특수 런타임 필요?"}
        Q3{"Python 3.11 · Node 22<br/>외 언어/런타임 필요?"}
        Q4{"대상 워크스페이스<br/>앱 100개 한도 초과?"}
    end

    subgraph L2["2층 · 강한 선호 (하나라도 YES면 Databricks)"]
        Q5{"UC 행·열 수준 보안<br/>상속이 필요한가?"}
        Q6{"Databricks Agent · Genie ·<br/>모델서빙이 앱 로직의 본체인가?"}
        Q7{"UC 대용량 데이터<br/>인메모리 처리가 핵심인가?"}
    end

    subgraph L3["3층 · 기본값"]
        Q8{"업무시간 외 정지 불가?<br/>(24×7 SLA) 또는<br/>동시 사용자가 단일 인스턴스 초과?"}
    end

    PC["Private Cloud (VKS)"]
    WS["워크스페이스 증설 검토<br/>불가 시 Private Cloud"]
    DBX["Databricks Apps"]
    DBX2["Databricks Apps<br/>(1안 기본값)"]
    COST["비용 비교 후 결정<br/>기본 성향: Private Cloud"]

    START --> Q1
    Q1 -->|YES| PC
    Q1 -->|NO| Q2
    Q2 -->|YES| PC
    Q2 -->|NO| Q3
    Q3 -->|YES| PC
    Q3 -->|NO| Q4
    Q4 -->|YES| WS
    Q4 -->|NO| Q5

    Q5 -->|YES| DBX
    Q5 -->|NO| Q6
    Q6 -->|YES| DBX
    Q6 -->|NO| Q7
    Q7 -->|YES| DBX
    Q7 -->|NO| Q8

    Q8 -->|YES| COST
    Q8 -->|NO| DBX2

    PC --> REG["앱마켓 등록<br/>runtime:private-cloud"]
    WS --> REG
    COST --> REG
    DBX --> REG2["앱마켓 등록<br/>runtime:databricks"]
    DBX2 --> REG2
```

---

## 3. 판정 기준 상세

각 분기의 근거다. **판정자가 "왜 이렇게 갈리는가"를 설명할 수 있어야** 기준이 유지된다.

### 1층 — 차단 조건

| # | 질문 | 근거 | 출처 |
|---|---|---|---|
| **Q1** | 사내 시스템 직접 연동 필요? | NCC/PrivateLink는 클라우드 사업자 인프라 기반이라 온프렘으로 확장되지 않는다. 서버리스에서 온프렘으로의 네트워크 레벨 직접 연동이 성립하지 않음 | ⚠️ A1 (커뮤니티 근거, 공식 확인 필요) |
| **Q2** | 커스텀 이미지·특수 런타임? | Databricks Apps의 배포 단위는 **소스 + 설정**이며, 커스텀 Docker 이미지를 레지스트리에서 가져와 실행하는 경로가 문서에 없음 | `databricks-apps-reference.md` §2 |
| **Q3** | 지원 외 언어/런타임? | Ubuntu 22.04 / Python 3.11 / Node.js 22.16 고정 | 동 §2 |
| **Q4** | 앱 100개 한도? | **워크스페이스당 100개, 조정 불가(fixed)** | 동 §3 |

> **Q1이 판정의 무게중심이다.** 이것이 "1안으로 Databricks Apps를 우선 적용한다"는 방침의 배경과 명분을 지탱한다. 기획서에 "좀더 배경과 명분을 강화해야 할 필요는 있다"고 적어 둔 부분에 대한 답이 여기에 있다 — 취향이나 정책이 아니라 **물리적 제약에서 도출되는 경계**이기 때문에 논쟁의 여지가 없다.
>
> ⚠️ 다만 A1이 아직 공식 확인 전이다. **확인이 뒤집히면 Q1은 "성능·지연 요구"로 완화**되고, 판정 트리의 무게중심이 2층으로 이동한다.

### 2층 — 강한 선호

| # | 질문 | 근거 |
|---|---|---|
| **Q5** | UC 행·열 보안 상속? | OBO 사용 시 **UC의 행 필터·컬럼 마스킹이 자동 적용**된다. Private Cloud에서 동등 통제를 구현하려면 앱 코드가 책임져야 하며, 이는 검증으로 잡아내기 가장 어려운 유형의 위험이다 |
| **Q6** | Agent·Genie·모델서빙이 본체? | Apps + Agents 조합이 표준. Genie space는 MCP URL로 접근, 최대 25개 UC 테이블 |
| **Q7** | 대용량 인메모리 처리? | 데이터 근접성. 단 Large도 4 vCPU / 12 GB 상한 |

> **Q5의 판정 가치가 가장 높다.** 데이터 거버넌스 책임을 앱 코드에서 플랫폼으로 옮길 수 있다는 것은 단순 편의가 아니라 **보안 통제 등급의 차이**다.

### 3층 — 기본값과 비용

| # | 질문 | 근거 |
|---|---|---|
| **Q8** | **업무시간 외 정지가 불가능한가(24×7 SLA)?** | Medium 0.5 DBU/h, Large 1 DBU/h로 **실행 중 상시 과금**이며 **Apps에는 auto-stop 기능이 없다.** 정지 불가 앱이 비용 게이트 대상 |
| **Q8′** | 동시 사용자 규모가 단일 인스턴스 한도를 넘는가? | Large도 최대 4 vCPU / 12 GB이고 **수평 확장은 Beta.** 이건 비용이 아니라 용량 천장이므로 사실상 1층 차단 조건에 가깝다 |

> ⚠️ **Q8은 원래 "상시 고트래픽?"이었으나 재정의했다.** 비용은 트래픽이 아니라 **앱 개수 × 구동 시간**에서 발생한다. 저트래픽 앱 100개가 고트래픽 앱 1개보다 훨씬 비싸다. → `04-cost-model.md` §5-d

**비용 비교는 공통 환산 기준이 정의된 후에야 가능하다.** 그전까지는 Q8을 "판단 보류 후 플랫폼팀 협의"로 처리한다.

> 💰 **3층 기본값은 조건부다.** "둘 다 NO → Databricks Apps"의 실제 비교 대상은 DBU 단가 vs 클라우드 VM 단가가 아니라 **연 수억원 vs 거의 0**이다(VKS는 기구축 온프렘 하드웨어이므로 파드 하나의 한계비용이 0에 가깝다). 따라서 **유휴 정지 정책과 공용 웨어하우스 규칙이 플랫폼에 구현되어 있는 동안에만 Databricks Apps를 기본값으로 한다.** 1단계(앱 10개 내외)에서는 1안이 타당하나, 미구현 상태에서 앱 수가 늘면 비용이 선형으로 따라 올라간다. → `04-cost-model.md` §5-a, §6

### 판정 체크리스트 (등록 신청서 양식용)

```
[1층 차단 조건]
[ ] Q1. 사내 시스템(MES/SRM/ERP/Wehub/CRM) 직접 연동이 필요합니까?
[ ] Q2. 커스텀 컨테이너 이미지나 특수 런타임이 필요합니까?
[ ] Q3. Python 3.11 / Node.js 22 외의 언어·런타임이 필요합니까?
[ ] Q4. (플랫폼팀 확인) 대상 워크스페이스 앱 수가 한도에 근접했습니까?

[2층 선호 조건]
[ ] Q5. Unity Catalog의 행·열 수준 보안을 그대로 적용받아야 합니까?
[ ] Q6. Databricks Agent/Genie/모델서빙이 앱 기능의 핵심입니까?
[ ] Q7. UC 대용량 데이터의 인메모리 처리가 핵심입니까?

[3층]
[ ] Q8.  업무시간 외 정지가 불가능합니까? (24×7 SLA 요구)
[ ] Q8′. 예상 동시 사용자가 단일 인스턴스(최대 4 vCPU) 한도를 넘습니까?

→ 1층 하나라도 YES: Private Cloud
→ 1층 전부 NO + 2층 하나라도 YES: Databricks Apps
→ 둘 다 NO + Q8·Q8′ 전부 NO: Databricks Apps (기본값, 단 §3 3층의 조건부 단서 적용)
→ 둘 다 NO + Q8 YES: 플랫폼팀 비용 협의
→ Q8′ YES: 용량 천장이므로 Private Cloud (수평 확장 GA 전까지)
```

---

## 4. To-Be 전체 구성

```mermaid
flowchart TB
    subgraph USERS["이용 주체"]
        DEV["앱 개발자<br/>(현업 · 개발자)"]
        EMP["임직원<br/>(앱 사용자)"]
        OWN["App Owner<br/>승인자 · 플랫폼팀"]
    end

    subgraph IDENTITY["신원 · 권한 (단일 소스)"]
        AD["Active Directory<br/>권한의 단일 소스"]
        KC["Keycloak<br/>SSO · RBAC"]
        DBXID["Databricks 계정<br/>SSO + SCIM"]
        AD --> KC
        AD --> DBXID
    end

    subgraph MAKE["MAKE · 개발"]
        PG["AX Playground<br/>Golden Path 시작점"]
        SCAF["표준 스캐폴드<br/>CI · 보안정책 · 로깅 결선"]
        PG --> SCAF
    end

    subgraph TRUST["TRUST · 형상관리 및 검증"]
        GL["GitLab (온프렘)<br/>중앙 형상관리"]
        POL["Security Policy Project<br/>스캔 · 승인 정책 강제"]
        CI["검증 파이프라인<br/>SAST · SCA · SBOM<br/>Secret · License"]
        AGATE["Agent App 게이트<br/>AI-BOM · 툴권한 · 평가"]
        APR["승인<br/>보호된 환경 · MR 승인"]
        GL --> CI
        POL -.강제 주입.-> CI
        CI --> AGATE
        AGATE --> APR
    end

    subgraph RUNTIME["ADOPT · 운영 런타임"]
        subgraph RT_PC["Private Cloud (VKS)"]
            HARBOR["Harbor<br/>이미지 + Cosign 서명"]
            FLUX["Flux + agentk<br/>Pull 기반 GitOps"]
            KYV["Kyverno<br/>서명 · provenance 검증"]
            PCAPP["Web App 실행"]
            HARBOR --> FLUX --> KYV --> PCAPP
        end
        subgraph RT_DBX["Databricks Apps"]
            BUNDLE["Bundle 배포<br/>deploy + run"]
            HEALTH["헬스체크<br/>서빙 버전 확인"]
            DBXAPP["App 실행 (OBO)"]
            UC["Unity Catalog<br/>행 · 열 보안"]
            AGENT["Agent · Genie<br/>모델서빙"]
            BUNDLE --> HEALTH --> DBXAPP
            DBXAPP -.OBO.-> UC
            DBXAPP -.-> AGENT
        end
    end

    subgraph MARKET["AX App Market"]
        CAT["앱 카탈로그<br/>검색 · 분류 · 상세"]
        PERM["권한 관리<br/>공개범위 · RBAC"]
        EVID["증적 저장소<br/>SBOM · 서명 · 승인이력"]
        OPS["운영 대시보드<br/>상태 · 사용량 · 비용"]
    end

    subgraph OBSERV["관측 · 감사"]
        NORM["지표 정규화 계층"]
        PROM["Prometheus · Grafana · Loki"]
        SYST["system.access.audit<br/>system.billing.usage"]
        PROM --> NORM
        SYST --> NORM
        NORM --> OPS
    end

    subgraph LEGACY["사내 업무 시스템"]
        SYS["MES · SRM · ERP<br/>Wehub · CRM"]
    end

    DEV --> PG
    SCAF --> GL
    APR -->|"runtime:private-cloud"| HARBOR
    APR -->|"runtime:databricks"| BUNDLE
    CI -.증적.-> EVID
    APR -.승인이력.-> EVID
    HEALTH -.배포완료 등록.-> CAT
    KYV -.배포완료 등록.-> CAT
    PCAPP <-->|"직접 연동 가능"| SYS
    DBXAPP -. "직접 연동 불가 (A1)" .-x SYS

    EMP --> CAT
    CAT --> PERM
    PERM -->|"실행: SSO + 권한"| PCAPP
    PERM -->|"실행: SSO + CAN_USE"| DBXAPP
    KC -.인증.-> CAT
    KC -.인증.-> PCAPP
    DBXID -.인증.-> DBXAPP
    OWN --> APR
    OWN --> PERM

    DBXAPP -.피드백 · 재배포.-> PG
    PCAPP -.피드백 · 재배포.-> PG
```

### 구성요소별 역할

| 영역 | 구성요소 | 역할 | 상태 |
|---|---|---|---|
| MAKE | **AX Playground** | Golden Path 시작점. 파이프라인·보안정책·로깅이 결선된 실행 가능한 스캐폴드 제공 | 재정의 필요 |
| TRUST | **GitLab (온프렘)** | 중앙 형상관리 + CI/CD + 보안 스캔 + 정책 강제 | 기구축 |
| TRUST | **Security Policy Project** | 스캔·승인 정책을 코드로 관리. `[skip ci]` 우회 차단 | 신규 |
| ADOPT | **Private Cloud (VKS)** | 사내 시스템 연동 앱, 커스텀 런타임 앱 | 기구축 |
| ADOPT | **Databricks Apps** | UC 데이터 앱, Agent App. **1안 우선 적용 대상** | 신규 |
| MARKET | **AX App Market** | 카탈로그 · 권한 · 증적 · 운영 지표 | 신규 |
| 신원 | **AD → Keycloak / Databricks** | 권한의 단일 소스 | 일부 기구축 |

---

## 5. 인증 · 권한 매핑

기획서에서 "SSO 그룹 연동" 한 줄로만 있던 부분을 구체화한다.

### 5-1. 신원 체계

**AD를 권한의 단일 소스로 두고, 양쪽이 이를 상속하는 구조**가 가장 단순하다.

```
Active Directory (단일 소스)
├─ Keycloak (OIDC/SAML)  ──▶ App Market 로그인
│                        ──▶ Private Cloud 앱 SSO + RBAC
└─ Databricks 계정 SSO   ──▶ Databricks 워크스페이스 로그인
   (SAML 2.0 / OIDC,        ──▶ Databricks 그룹 (SCIM 동기화)
    unified login)
```

⚠️ **A2 가정에 의존한다.** Azure Databricks라면 Entra ID로 고정되므로 Keycloak 직접 연동이 불가할 수 있다. 이 경우 AD → Entra ID → Databricks 경로가 되고, Keycloak과는 AD를 공통 상위로 두는 형태가 된다. **어느 클라우드인지 확정이 선행되어야 한다.**

### 5-2. 앱 실행 권한의 투영

앱마켓의 "권한에 따라 실행"이 각 런타임에 어떻게 투영되는지다.

| 단계 | Private Cloud | Databricks Apps |
|---|---|---|
| 앱마켓에서 공개범위 지정 | AD 그룹 / 조직 단위 지정 | 동일 |
| 런타임 권한 부여 | Keycloak RBAC + Ingress 인가 정책 | **Databricks 그룹에 `CAN_USE` 부여** |
| 사용자 인증 | Keycloak SSO | Databricks 계정 SSO |
| 데이터 접근 통제 | **앱 코드 책임** | **OBO → UC 행·열 보안 자동 적용** |
| 권한 회수 반영 | Keycloak 즉시 | 그룹 동기화 주기에 의존 |

**설계 결정 3가지**

1. **`CAN_USE`가 Databricks 트랙의 실질적 실행 권한 수단이다.** 앱마켓 RBAC → AD 그룹 → Databricks 그룹 → `CAN_USE` 경로를 API로 자동화한다.
2. **권한 회수 반영 지연을 명시한다.** SCIM 동기화 주기만큼 시차가 발생한다. 즉시 차단이 필요한 경우(퇴사·사고)의 별도 절차를 정의해야 한다.
3. **앱 권한이 `CAN_USE`/`CAN_MANAGE` 2단계뿐이므로**, 앱 내부의 세분 역할(조회자/승인자/관리자)은 앱마켓이 전달하는 권한 정보 또는 UC 권한으로 처리한다. Databricks 앱 권한만으로는 표현할 수 없다.

---

## 6. 앱마켓 메타데이터 스키마 (초안)

지금까지의 제약을 반영한 최소 스키마다. **`workspace_id`와 런타임별 조건부 필드가 핵심**이다.

```json
{
  "app_id": "ax-app-0001",
  "name": "설비 이상 조회",
  "description": "...",
  "owner": { "user": "...", "org": "...", "backup": "..." },
  "category": ["제조", "품질"],
  "tags": ["MES", "이상탐지"],

  "type": "webapp | agent",
  "runtime": "private-cloud | databricks",

  "decision": {
    "answers": { "q1": false, "q2": false, "q5": true, "...": "..." },
    "decided_by": "...",
    "decided_at": "2026-09-10"
  },

  "source": {
    "git_repo": "ax-platform/apps/...",
    "compliance_labels": ["runtime:databricks", "type:agent"]
  },

  "deployment": {
    "version": "v1.2.0",
    "commit": "abc1234",
    "workspace_id": "1234567890",        // ← Databricks 다중 워크스페이스 대응
    "runtime_url": "https://...",
    "status": "running | stopped | crashed",
    "health": "passed",
    "deployed_at": "..."
  },

  "authz": {
    "visibility": "전사 | 관계사 | 조직 | 지정사용자",
    "ad_groups": ["..."],
    "databricks_auth_mode": "obo | service_principal",   // SP는 예외 승인 필요
    "oauth_scopes": ["sql", "genie"],
    "approved_exception": null
  },

  "evidence": {
    "sbom_url": "...",
    "scan_report_url": "...",
    "signature_ref": "...",              // Private Cloud: cosign / Databricks: 파이프라인 서명
    "provenance": "...",                 // Private Cloud만
    "pipeline_url": "...",
    "approved_by": "...",
    "approved_at": "..."
  },

  "ai_bom": {                            // type:agent 인 경우 필수
    "models": ["..."],
    "agents": ["..."],
    "tools": [{ "name": "...", "permissions": "read|write|exec" }],
    "genie_spaces": ["..."],
    "eval_score": 0.0
  },

  "operations": {
    "cost_monthly_krw": 0,               // 공통 환산 기준 적용
    "usage_users_30d": 0,
    "sla_tier": "critical | standard",
    "deprecation": { "status": "active | deprecated | sunset", "eol_date": null }
  }
}
```

**설계 의도**

- `workspace_id`: 100개 한도 때문에 다중 워크스페이스가 불가피하다. 나중에 추가하면 스키마를 뒤집어야 한다.
- `decision`: 판정 근거를 남긴다. 나중에 "왜 이 앱이 여기 있나"를 재구성할 수 있어야 한다.
- `databricks_auth_mode`: SP 모드를 예외로 관리하기 위한 필드. 기본은 `obo`.
- `deprecation`: 기획서에 없던 항목. 앱 일몰 절차가 없으면 카탈로그가 수년 내 방치된 앱으로 채워진다.
- `ai_bom`: AI 모델은 기존 스캐너가 읽을 수 없는 서드파티 의존성이다.
- `operations.cost_monthly_krw`: 앱 컨테이너 DBU만으로는 부족하다. 공용 웨어하우스 분담분과 Agent App의 변동비(모델 서빙·Genie)를 별도 항목으로 분리해야 showback이 성립한다. → `04-cost-model.md` §2, §6-4

---

## 7. 기획서 대비 변경·보완 사항

원 기획서에서 수정이 필요한 항목이다.

| 기획서 내용 | 변경 | 근거 |
|---|---|---|
| "Databricks Apps에 배포되고" (AX App 정의) | **"승인된 Runtime(Databricks Apps 또는 Private Cloud)에 배포되고"** | 런타임 2종 방침과 정의문 불일치 |
| 앱 실행: "Private Cloud App Runtime URL 연계" | **"승인된 Runtime URL 연계"** | 동일 비대칭 |
| 앱 등록 메타데이터: "실행 이미지" | **Private Cloud 트랙 조건부 필드로 분리** | Databricks는 이미지 배포 모델 아님 |
| 검증: "이미지 서명" | **트랙별 분리 — 이미지 서명 / 파이프라인 서명** | 동일 |
| "2. 주요 기능 및 추진 일정 — (2) 추진 일정" | **`02` 문서 §10 로드맵으로 대체** | 기획서에서 누락된 절 |
| (없음) | **앱 일몰(deprecation) 절차 추가** | 카탈로그 수명 관리 |
| (없음) | **Agent App 전용 검증 게이트 추가** | 일반 코드 스캔으로 커버 불가 |
| "databircks" 오타 | 수정 | — |

---

## 8. 미결 사항 종합

세 문서에 걸친 미결 항목을 우선순위로 통합한다.

| 순위 | 항목 | 막히는 것 | 확인처 |
|---|---|---|---|
| **1** | **Databricks 클라우드 (AWS/Azure/GCP)** | 인증 설계 전체 (§5) | 인프라 담당 |
| **2** | **온프렘 아웃바운드 제약 (A1)** | 판정 기준 Q1 (§3) — 판정 트리의 무게중심 | Databricks 문의 |
| **3** | **GitLab Ultimate 여부** | 검증 게이트 강제 — 로드맵 1단계 | GitLab 관리자 |
| **4** | **WIF 성립 여부** | Databricks 트랙 배포 인증 | `01` 문서 절차 |
| **5** | Databricks Enterprise tier | 네트워크 정책 | 계약 확인 |
| **6** | Cosign 키 관리 방식 | Private Cloud 트랙 5단계 | 보안팀 |
| **7** | Jenkins·ArgoCD·Harbor 역할 분담 | 도구 중복 정리 | 플랫폼팀 |
| **8** | 비용 공통 환산 기준 + **Apps SKU 실효 단가** | 판정 Q8, 운영 대시보드, 3층 기본값의 유효성 | 재무·플랫폼 협의 / `04` 문서 §1-2 쿼리 |

> **1~3번은 병렬로 즉시 착수 가능하다.** 4번은 3번과 무관하게 진행할 수 있다. 이 네 가지가 풀리면 설계 문서 전체의 가정이 사실로 대체된다.

---

## 관련 문서

- `docs/AX앱마켓구성1.pdf` — 원 기획서
- `docs/databricks-apps-reference.md` — Databricks Apps 기술 레퍼런스
- `docs/cicd-devsecops-research.md` — CI/CD·DevSecOps 자료조사
- `docs/01-gitlab-databricks-wif-verification.md` — WIF 검증 설계
- `docs/02-cicd-pipeline-design.md` — CI/CD 파이프라인 상세 설계
- `docs/04-cost-model.md` — 운영 비용 모델. §3 3층 판정과 §6 메타데이터의 비용 필드 근거
