# Databricks Apps 기술 레퍼런스

> **목적**: AX App Market의 운영 Runtime 후보인 Databricks Apps의 기술적 사실관계를 정리하여, 런타임 선정·아키텍처 설계 시 반복 조사 없이 참조할 수 있도록 함.
> **조사일**: 2026-09-10
> **1차 출처**: Databricks 공식 문서 (AWS / Azure). 커뮤니티 출처는 별도 표기.
> **주의**: Databricks는 기능 변경이 잦음. 6개월 이상 경과 시 §11의 확인 필요 항목부터 재검증할 것.

---

## 1. 개요

Databricks Apps는 Databricks **서버리스 플랫폼 위에서 동작하는 컨테이너화된 웹 서비스**다. 별도 인프라 없이 데이터·AI 애플리케이션을 배포할 수 있고, Unity Catalog(거버넌스), Databricks SQL(질의), OAuth(인증)와 기본 통합된다.

- 앱은 **특정 워크스페이스에 종속**된다. 워크스페이스 레벨 자원(SQL Warehouse 등)과 계정 레벨 자원(Unity Catalog)에 접근 가능.
- 주 용도: 인터랙티브 대시보드, RAG 챗 앱, 데이터 입력 폼, 운영용 커스텀 UI.

### 앱 생애주기

`Create` → `Deploy` → `Running` → `Stopped` → (`Crashed`)

- 앱은 UI 또는 CLI에서 템플릿으로 생성.
- 배포 시 필요 자원을 선언하고 워크스페이스 관리자가 접근 권한을 승인 (최소 권한 원칙).
- 중지된 앱은 접근 불가하나 설정은 보존되며 과금되지 않음.

---

## 2. 런타임 환경

| 항목 | 내용 |
|---|---|
| OS / 베이스 | Ubuntu 22.04 LTS (관리형, 자원 할당·네트워킹 자동 처리) |
| Python | 3.11, 격리된 가상환경. `uv` 0.10.2로 의존성 관리 (`uv` 사용 시 다른 Python 버전 지정 가능) |
| Node.js | 22.16, `npm` 또는 `pnpm` + `package.json` |
| 지원 프레임워크 | Streamlit, Dash, Gradio, Flask, FastAPI / Express (Node), React·Angular·Svelte |
| 의존성 선언 | `requirements.txt` / `package.json` — **Node 라이브러리는 사전설치된 것이 없음** |
| 기본 환경변수 | `DATABRICKS_APP_NAME`, `DATABRICKS_WORKSPACE_ID`, `DATABRICKS_HOST`, `DATABRICKS_APP_PORT`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` |
| 포트/호스트 | 지원 프레임워크에 대해 런타임이 자동 설정 |
| 상태 저장 | **재시작 시 인메모리 데이터 소실.** 영속화는 Databricks 테이블, 워크스페이스 파일, UC 볼륨, Lakebase 사용 |

### ⚠️ 배포 단위는 "소스 + 설정"이지 "컨테이너 이미지"가 아니다

공식 문서상 배포 산출물은 **소스 코드와 설정 파일**이며, 사용자가 빌드한 커스텀 Docker 이미지를 레지스트리에서 가져와 실행하는 경로는 문서에 기술되어 있지 않다.

**AX App Market 설계 함의** — 앱 등록 메타데이터의 "실행 이미지" 필드와 검증 항목의 "이미지 서명"은 Private Cloud(Harbor / ArgoCD) 트랙 전용이다. Databricks 트랙은 **커밋 해시 + 번들 배포 기록 + 파이프라인 서명**으로 동등 수준의 증적을 별도 정의해야 "공통 검증 기준"이라는 목표가 성립한다.

---

## 3. 컴퓨트 / 비용 / 한도

### 인스턴스 크기

| 크기 | vCPU | 메모리 | 비용 | 권장 용도 |
|---|---|---|---|---|
| **Medium** (기본값) | 최대 2 | 6 GB | **0.5 DBU/시간** | 대시보드, 단순 시각화, 폼 등 일반적인 앱 |
| **Large** | 최대 4 | 12 GB | **1 DBU/시간** | 대용량 인메모리 처리, 고동시성, 연산 집약 |

- 크기 미지정 시 Medium 자동 할당.
- **실행 중인 시간에 대해서만 과금.** 중지 시 과금 없음.
- 수평 확장(horizontal scaling)은 **Beta** 단계.
- 문서 권고: Medium으로 시작하고, 성능 문제가 실제로 나타날 때만 Large로 올릴 것.

### ⚠️ "실행 중에만 과금"의 함정 — Apps에는 auto-stop이 없다

위의 "실행 중인 시간에 대해서만 과금"은 사실이지만, **"실행을 언제 멈추는가"에 해당하는 기능이 Apps에는 없다.** SQL Warehouse와 달리 유휴 자동 정지(auto-stop)나 scale-to-zero 설정이 존재하지 않으므로, 시작·정지를 스케줄 잡이나 외부 스케줄러로 직접 호출해야 한다. 방치하면 실질적으로 24/7 과금이다.

> 출처 등급: 커뮤니티·MVP 글. **공식 문서에 해당 설정이 부재하다는 사실 자체가 근거**이며, 기능 추가 시 재확인 대상(§11).

**AX App Market 설계 함의** — 앱마켓은 정의상 롱테일 앱이 많은 카탈로그이므로 이 낭비가 예외가 아니라 기본값이 된다. 유휴 정지를 플랫폼 의무로 두어야 한다. → **`04-cost-model.md` §1-1, §6-1**

### 한도

- **워크스페이스당 Databricks App 100개 — 조정 불가(fixed)**
- 참고: **워크스페이스 자체는 계정당 Enterprise 50개 / Premium 10개이며 조정 가능**하다. 따라서 실질 천장은 (워크스페이스 수 × 100)이고, 늘릴 수 있는 쪽은 워크스페이스뿐이다.
- ⚠️ **에이전트는 이 한도에 걸리지 않는다.** 에이전트는 UC 자원(계정 레벨)이므로 워크스페이스 경계를 타지 않는다 → `AXM-0012`

**AX App Market 설계 함의** — 전사 앱마켓이 수백 개 앱을 목표로 한다면 **워크스페이스 분할 전략이 초기 설계에 포함되어야 한다.** 앱마켓이 여러 워크스페이스에 걸쳐 앱을 등록·조회·실행하는 구조를 전제로 메타데이터 스키마(워크스페이스 ID 포함)를 잡아야 나중에 뒤집지 않는다.

> 💰 **비용 관점에서는 반대로 읽어야 한다.** 한 워크스페이스를 상시 구동 앱 100개로 채우는 것은 연 3~6억원 규모의 의사결정이다. 즉 100개 한도는 용량 제약이 아니라 **예산 가드레일**이고, 워크스페이스 증설은 그 제동장치를 해제하는 행위다. → **`04-cost-model.md` §3, §5-b**

### 이 절이 다루지 않는 비용

여기 적힌 DBU는 **앱 컨테이너 몫뿐**이다. 실제 청구서에서 이것은 가장 작은 항목이며, UC 데이터를 쓰는 앱 뒤에 붙는 **SQL Warehouse(서버리스 Small = 12 DBU/h, 앱 Medium의 24배)** 가 지배 항목이다. 전체 비용 구조는 `04-cost-model.md` §2 참조.

---

## 4. 인증 · 권한 (Authorization)

Databricks Apps는 OAuth 2.0 기반의 **두 가지 권한 모델을 병행**한다.

### 4-1. 앱 권한 (App Authorization — 서비스 프린시펄)

- 앱마다 **전용 서비스 프린시펄이 자동 생성**된다. 앱 인스턴스별로 고유하며 재사용·변경 불가. 앱 삭제 시 함께 제거된다.
- 접근 수단: 환경변수 `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`
- 적합한 경우: 백그라운드 작업, 공용 설정 접근, 로깅, 사용자 신원이 무관한 외부 서비스 호출
- 특성: **모든 사용자에게 동일한 권한**이 적용됨

### 4-2. 사용자 권한 (User Authorization — On-Behalf-Of, OBO)

- 앱이 **현재 로그인한 사용자의 신원으로 동작**한다.
- Databricks가 사용자 액세스 토큰을 **`x-forwarded-access-token` HTTP 헤더**로 앱에 전달한다.
- **Unity Catalog의 기존 권한이 그대로 적용된다 — 행 수준 필터(row filter), 컬럼 마스킹(column mask) 포함.**
- 적합한 경우: 카탈로그 질의, 컴퓨트 기동, 개인별 접근 통제가 필요한 모든 작업

**활성화 방법**: 워크스페이스의 Apps 설정에서 `On-Behalf-Of User Authorization`을 켠 뒤, 앱 생성·수정 시 필요한 사용자 API 스코프를 선택한다.

### 4-3. OAuth 스코프

- OBO를 쓰는 앱은 **사용할 스코프를 명시적으로 선언**해야 한다.
- 주요 스코프: `sql`, `files`, `genie`, `model-serving`, `vector-search`
- 기본 스코프: `iam.access-control:read`, `iam.current-user:read` — 사용자 신원 조회용이며 **데이터·컴퓨트 접근 권한은 없다.**
- **선언하지 않은 기능은 사용자에게 권한이 있어도 Databricks가 차단한다** (최소 권한 강제).
- 개발자가 추가할 수 있는 스코프 범위는 워크스페이스 관리자가 제한하며, 계정 관리자가 최종 재정의 권한을 가진다.

### 4-4. 앱 자체에 대한 접근 통제

권한 등급은 **2단계뿐**이다.

| 권한 | 대상 |
|---|---|
| `CAN_USE` | 승인된 사용자 / 그룹 (읽기·실행) |
| `CAN_MANAGE` | 신뢰된 개발자 (관리) |

**AX App Market 설계 함의**

1. 앱마켓의 "권한에 따라 실행"을 Databricks 트랙에 투영하는 실질적 수단은 **`CAN_USE` 부여/회수**다. 앱마켓 RBAC → Databricks 그룹 → `CAN_USE` 로 이어지는 매핑 규칙과 **회수 시 반영 지연(동기화 주기)** 을 명시해야 한다.
2. 앱 권한 등급이 2단계뿐이므로, 앱 내부의 세분화된 역할(예: 조회자/승인자/관리자)은 **앱마켓이 제공하는 권한 정보 또는 UC 권한**으로 처리해야 한다. Databricks 앱 권한만으로는 표현할 수 없다.
3. **OBO를 기본 정책으로 못 박고 SP 모드는 예외 승인 대상으로 두는 것**을 권장한다. OBO는 UC의 행·열 보안까지 자동 상속하므로 데이터 거버넌스 책임을 플랫폼이 대신 져 준다. SP 모드는 모든 사용자가 동일 권한이 되어 데이터 접근 통제가 앱 코드 책임으로 넘어온다 — 검증 파이프라인에서 잡아내기 가장 어려운 유형의 위험이다.

---

## 5. SSO / ID 연동

- 계정 레벨에서 **SAML 2.0 또는 OIDC** 지원. IdP가 둘 중 하나를 지원하면 연동 가능.
- **Unified login**이 대부분의 계정에서 기본 활성 — 계정과 모든 워크스페이스에 단일 SSO 설정이 적용된다.
- 사용자·그룹 동기화: **automatic identity management** 권장, 미지원 IdP는 **SCIM 프로비저닝**.
- **JIT 프로비저닝**: 최초 로그인 시 사용자 계정 자동 생성 가능.

**AX App Market 설계 함의**

- ✅ **AWS Databricks로 확정(`03` 문서 F1)** — Azure의 Entra ID 고정 제약에 해당하지 않으므로 임의의 OIDC IdP를 계정 SSO로 쓸 수 있다.
- **SSO 중계는 Amazon Cognito**(`AXM-0014`). Cognito를 계정 SSO의 OIDC IdP로 등록한다. Keycloak 가정은 철회.
- ⚠️ **Cognito는 SCIM·automatic identity management를 제공하지 않는다.** JIT는 사용자만 만든다. Databricks 그룹은 원천 그룹을 SCIM API로 넣는 별도 동기화 작업이 채워야 한다.

---

## 6. CI/CD

공식 경로는 **Declarative Automation Bundles** (`databricks.yml`) 이다. GitHub Actions 가이드가 제공되지만, GitLab 등 다른 CI에서도 `databricks bundle` CLI를 호출하면 동일하게 동작한다.

### 요구사항

- 배포된 앱을 소유할 **Databricks 서비스 프린시펄**
- 리포지토리 루트의 **`databricks.yml`** — 앱을 리소스로 선언
- 워크스페이스 접속 변수를 담을 **배포 환경(deployment environment)** — 배포 전 수동 승인 요구 설정도 여기서 가능
- 인증은 **workload identity federation** 사용

### ⚠️ 파이프라인 설계 시 반드시 반영할 두 가지 함정

1. **`databricks bundle deploy`는 소스를 올리고 리소스를 갱신할 뿐, 앱 프로세스를 재시작하지 않는다.** 마지막 `databricks bundle run` 단계를 빠뜨리면 **CI는 성공으로 끝나는데 앱은 이전 코드를 계속 서빙한다.** 배포 후 반드시 `bundle run`을 실행할 것.
2. **`databricks bundle run`은 시작 신호를 보낸 직후 종료된다.** 앱은 아직 기동 전일 수 있고, 의존성 누락·환경변수 누락·포트 충돌로 기동 중 실패할 수 있다. **배포 후 상태 폴링 + 최신 코드 서빙 확인 헬스체크**를 파이프라인에 넣을 것.

**AX App Market 설계 함의** — 앱마켓의 "배포 상태" 표시는 `bundle deploy` 성공이 아니라 **헬스체크 통과**를 기준으로 삼아야 한다. 그렇지 않으면 마켓에는 신버전으로 표시되는데 실제로는 구버전이 도는 상태가 발생한다.

---

## 7. 네트워크

### 인바운드 (Ingress)

- **IP 액세스 리스트**: 워크스페이스·앱 접근을 신뢰된 IP 대역으로 제한 (워크스페이스 레벨)
- **프론트엔드 프라이빗 연결(front-end PrivateLink)**: 인바운드 트래픽을 공용 인터넷 대신 VPC 인터페이스 엔드포인트로 라우팅. **`databricksapps.com` 도메인에 대한 조건부 DNS 포워딩 필요.**
- 온프렘 → 워크스페이스 인바운드 PrivateLink는 온프렘 네트워크를 **Direct Connect 또는 VPN**으로 클라우드 VPC에 연결하면 구성 가능.

### 아웃바운드 (Egress)

- **NCC (Network Connectivity Configuration)**: 안정적인 아웃바운드 고정 IP 부여, private destination(S3 버킷, NLB 등)에 대한 PrivateLink 연결 지원
- **네트워크 정책(Network policies)**: **Enterprise tier 전용** — ✅ 우리 계약은 Enterprise이므로 사용 가능(`03` 문서 F3). 앱을 포함한 서버리스 워크로드의 이그레스를 제한.
  - ⚠️ 패키지 저장소(`pypi.org`, `registry.npmjs.org`)와 클라우드 서비스 엔드포인트를 **허용목록에 넣어야 한다.** 누락이 앱 배포 실패의 흔한 원인이다.
  - 앱은 빌드 시점과 런타임 모두 특정 Databricks 도메인에 대한 아웃바운드 접근이 필요하다.

### ✅ 온프렘 시스템으로의 아웃바운드 — 경로 성립 (2026-09-12 갱신)

> **종전 기술 (2026-09-10)**: "NCC / PrivateLink는 클라우드 사업자 인프라에 의존하며 온프렘으로 확장되지 않으므로, 서버리스에서 온프렘으로의 직접 연동이 성립하지 않는다"(커뮤니티 답변 근거). 우회책으로 스테이징 계층 방식을 제시했었다.
>
> **이 기술은 절반만 맞았다.** PrivateLink가 온프렘까지 직접 가지 않는 것은 사실이나, **우리 VPC를 중계점으로 두면 나머지 구간은 기구축 DX가 처리한다.**

**Apps 네트워킹 공식 문서**에 다음이 명시되어 있다.

> "To restrict egress to private destinations such as an S3 bucket or **a network load balancer (NLB)**, configure PrivateLink connections as part of your NCC setup."

따라서 다음 경로가 성립한다.

```
Databricks App (서버리스, Databricks 계정)
   → NCC 사설 엔드포인트 (PrivateLink)
   → 우리 VPC의 내부 NLB  ← VPC 엔드포인트 서비스로 노출
   → NLB 타깃 → TGW → Direct Connect
   → 온프렘 MES / SRM / ERP / Wehub / CRM
```

**요구사항과 한도**

| 항목 | 내용 |
|---|---|
| **tier** | **Enterprise 전용.** VPC 내부 리소스로의 사설 연결은 Enterprise tier 워크스페이스에서만 가능 |
| 구성요소 | 내부 스킴 NLB + VPC 엔드포인트 서비스 + 워크스페이스와 동일 리전의 NCC 객체 |
| 한도 | 리전·계정당 NCC 10개 / 리전당 사설 엔드포인트 30개 / NCC당 워크스페이스 50개 / 엔드포인트 규칙당 도메인 100개 |
| 제약 | **DNS chasing·DNS redirect 미지원** — 모든 도메인이 백엔드 리소스로 직접 해석되어야 한다 |

**⚠️ 검증이 남은 단 한 구간** — **NLB 타깃을 온프렘 IP로 두는 구성**. AWS NLB의 IP 타입 타깃은 DX/VPN 너머 주소를 지원하므로 성립할 것으로 보나, **이 구간은 Databricks 문서 범위 밖**이며 네트워크 담당 확인이 필요하다.

**AX App Market 설계 함의** — 종전에 "사내 시스템 연동 앱 = 구조적으로 Private Cloud"라고 적었던 판정 근거가 무효화된다. Q1은 **물리적 불가**가 아니라 **"사내 시스템을 내부 NLB 뒤에 노출하는 것에 대한 보안 승인 여부"** 로 재정의된다. → `03` 문서 §3 Q1, `05` 문서 §3

그 결과 **"런타임 분기의 배경과 명분"을 지탱하는 축이 Q1에서 Q5(UC 행·열 보안 상속)로 이동한다.** 물리적으로 막혀서 갈라지는 것이 아니라 통제 이점 때문에 선택하는 구조가 되므로, 명분 자체는 오히려 단단해진다.

인바운드(사내 사용자 → Databricks 앱)는 종전 기술대로 Direct Connect/VPN + 프론트엔드 PrivateLink로 해결된다.

---

## 8. 운영 · 모니터링 · 감사

| 필요 기능 (PDF 기준) | Databricks 제공 수단 |
|---|---|
| 보안·감사 (누가 등록·승인·배포·실행했는지) | **`system.access.audit`** — 앱 관련 사용자 행위, 앱 설정 변경, 보안 이벤트 |
| 비용 확인 | **`system.billing.usage`** — Apps에 대해 `created_by` 필드에 앱 생성자 이메일이 기록됨 |
| 사용 현황 / 상태 | 앱 상세 페이지의 **Insights 탭** — 사용자 참여도, 앱 가용성, **Viewers 테이블**(접근 사용자 추적) |

### ⚠️ 로그 비영속

**앱 컴퓨트가 종료되면 로그가 보존되지 않는다.** 영속 로깅이 필요하면 외부 로깅 서비스와 통합하거나 UC 볼륨/테이블에 기록해야 한다. 문서 권고: 로그를 **JSON 등 기계 판독 가능 형식**으로 포맷하고 APM·로그 수집 도구와 연계하여 실시간 알림, 보안 사고 대응, 사용·성능 분석에 활용할 것.

**AX App Market 설계 함의**

1. 앱마켓의 '운영 관리'(상태·장애·로그·사용자 수·호출량·비용)는 **Databricks 시스템 테이블을 질의하는 수집 계층**으로 구현 가능하다. 다만 Private Cloud 트랙은 Grafana/Prometheus/Loki 기반이므로 **두 소스를 통합하는 지표 정규화 계층**이 필요하다.
2. **비용 지표는 단위가 다르다.** Databricks는 DBU/시간, Private Cloud는 자원 점유 기반이다. 앱마켓에서 나란히 보여주려면 공통 환산 기준(예: 월 원화 환산)을 먼저 정의해야 한다.
3. 로그 비영속 특성상, **앱 템플릿 자체에 구조화 로깅 + UC 볼륨 출력을 기본 탑재**하는 것이 개별 개발자에게 맡기는 것보다 안전하다. AX Playground의 표준 템플릿에 반영할 항목.

---

## 9. Agent 활용 App

PDF의 AX App 정의는 일반 Web App뿐 아니라 **Databricks Agent 연계 대화형·자동화 앱**을 포함한다. 관련 구성요소는 다음과 같다.

- **Agent Bricks Custom Agents / Agent Framework**: 임의의 LLM으로 프로덕션 규모 에이전트를 구축. RAG 애플리케이션 등.
- **Agent Evaluation**: AI 보조 평가 + 사람 피드백 UI로 에이전트 출력 품질을 검증하는 별도 기능.
- **Genie space**: 에이전트가 UC 테이블을 질의해야 할 때 권장되는 방식. **테이블·뷰 30개/space (조정 가능, 2026-09-11 기준)** 를 컨텍스트로 유지하며 자연어 질의 처리. 에이전트는 **사전 구성된 MCP URL**로 Genie space에 접근.
- **Genie Conversation API**: 애플리케이션·챗봇·에이전트 프레임워크에서 자연어 데이터 질의를 수행하는 Chat 모드 API.
- 표준 조합: **Databricks Apps(React 등 프런트엔드) + Databricks Agents(백엔드)** — 외부 호스팅 인프라 없이 플랫폼의 보안·컴플라이언스·자원 관리를 상속.

**AX App Market 설계 함의** — 앞서 지적한 **"Agent App 전용 검증 게이트"** 를 Agent Evaluation 위에 얹을 수 있다. 일반 코드 검증(SAST/SCA/Secret/SBOM)만으로는 프롬프트 주입, 툴 권한 범위, 데이터 반출, 응답 품질을 잡아내지 못한다. Genie space의 30 테이블 상한도 Agent App 설계 제약으로 문서화해 둘 것.

---

## 10. AX App Market 설계 함의 요약

| # | 사실 | 설계 반영 사항 |
|---|---|---|
| 1 | 배포 단위가 소스+설정, 커스텀 이미지 경로 없음 | "실행 이미지"/"이미지 서명"은 Private Cloud 전용. Databricks 트랙은 커밋 해시+번들 배포 기록으로 동등 증적 정의 |
| 2 | 워크스페이스당 앱 **100개 고정** | 워크스페이스 분할 전략을 초기 설계에 포함. 메타데이터에 워크스페이스 ID 포함 |
| 3 | OBO 시 **UC 행·열 보안 자동 상속** | OBO를 기본 정책으로 확정, SP 모드는 예외 승인 대상 |
| 4 | 앱 권한이 `CAN_USE`/`CAN_MANAGE` 2단계뿐 | 앱마켓 RBAC → Databricks 그룹 → `CAN_USE` 매핑 규칙 + 회수 반영 지연 명시. 세분 역할은 앱마켓/UC가 담당 |
| 5 | 계정 SSO가 SAML/OIDC 지원 | Cognito를 OIDC IdP로 연계(`AXM-0014`). 그룹은 SCIM API 동기화 별도 구현 |
| 6 | `bundle deploy`는 앱을 재시작하지 않음 | 배포 상태 판정 기준을 **헬스체크 통과**로 정의. `bundle run` + 상태 폴링 필수 |
| 7 | 서버리스 → 온프렘 아웃바운드 제약 (확인 필요) | 사실 확인 시 **사내 시스템 직접 연동 앱 = Private Cloud 트랙**. 런타임 분기의 핵심 근거 |
| 8 | 시스템 테이블로 감사·비용·사용현황 수집 가능 | 두 런타임의 지표 정규화 계층 + 비용 환산 기준 정의 |
| 9 | 앱 종료 시 로그 소실 | 구조화 로깅 + UC 볼륨 출력을 **표준 앱 템플릿에 기본 탑재** |
| 10 | Agent Evaluation, Genie space(30 테이블) | Agent App 전용 검증 게이트를 Agent Evaluation 기반으로 설계 |

---

## 11. 확인 필요 사항 (Databricks 측 확인 권장)

아키텍처 확정 전 반드시 답을 받아야 하는 항목이다.

1. ~~어느 클라우드의 Databricks인가~~ → ✅ **해소: AWS · ap-northeast-2 · 별도 전용 계정** (`03` 문서 F1·F2)
2. ~~계약 tier가 Enterprise인가~~ → ✅ **해소: Enterprise** (`03` 문서 F3). 네트워크 정책과 **VPC 내부 리소스로의 사설 연결**을 모두 사용할 수 있다.
3. ~~서버리스 → 온프렘 아웃바운드 연결 가능 여부~~ → ✅ **경로 확인 완료** (§7). **남은 검증은 NLB 타깃을 온프렘 IP로 두는 구성 한 가지**이며, 이는 Databricks가 아니라 네트워크 담당 확인 사항이다.
4. **커스텀 컨테이너 이미지 배포 지원 여부** — 문서에 없으나 로드맵/프리뷰 존재 가능성.
5. **앱 100개 한도의 예외 협의 가능 여부** 및 멀티 워크스페이스 운영 시 권장 패턴.
6. **수평 확장(Beta)의 GA 시점** — 전사 앱의 동시 사용자 규모를 감당하려면 필요.
7. **Amazon Cognito를 OIDC IdP로 한 unified login 구성의 레퍼런스 사례** 유무 (Keycloak 가정은 `AXM-0014`로 철회).
8. **Apps의 유휴 자동 정지(auto-stop) 기능 로드맵** — 현재 부재(§3). 제공되면 `04-cost-model.md` §6-1의 자체 구현이 불필요해진다.
9. **Apps SKU의 실효 단가와 과금 최소 단위** — 공표 가격 페이지가 동적 로딩이라 정적 확인 불가. `04-cost-model.md` §1-2의 `system.billing.list_prices` 쿼리로 확정할 것.

---

## 12. 참고 링크

### 공식 문서

- [Databricks Apps 개요](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [Key concepts in Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts)
- [Configure authorization in a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth)
- [Configure compute resources for a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/compute-size)
- [Databricks Apps environment](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/system-env)
- [CI/CD for Databricks Apps with GitHub Actions](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/cicd-github-actions)
- [Configure networking for Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/networking)
- [Logging and Monitoring for Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/monitor)
- [Resource limits](https://docs.databricks.com/aws/en/resources/limits)
- [Configure SSO in Databricks](https://docs.databricks.com/aws/en/security/auth/single-sign-on/)
- [Billable usage system table reference](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Use agents on Databricks](https://docs.databricks.com/aws/en/agents/agent-framework/build-agents)
- [Use the Genie Agents API](https://docs.databricks.com/aws/en/genie-agents/conversation-api)
- [Configure inbound PrivateLink for workspaces](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)

### 블로그 / 커뮤니티 (참고 등급)

- [Building Databricks Apps with React and Databricks Agents for Enterprise Chat Solutions](https://www.databricks.com/blog/building-databricks-apps-react-and-mosaic-ai-agents-enterprise-chat-solutions)
- [Implement fine-grained permissions for Databricks Apps with on-behalf-of-user authorization](https://community.databricks.com/t5/technical-blog/implement-fine-grained-permissions-for-databricks-apps-with-on/ba-p/116884)
- [Networking Challenges with Databricks Serverless Compute When Connecting to On-Prem](https://community.databricks.com/t5/administration-architecture/networking-challenges-with-databricks-serverless-compute-control/td-p/117532) — §7의 온프렘 제약 근거

---

## 관련 문서

- `docs/source/AX앱마켓구성1.pdf` — AX App Market 기획 초안 (전체 구성, As-Is/To-Be, 주요 기능)
- `docs/design/04-cost-model.md` — 운영 비용 모델. §3의 DBU는 앱 컨테이너 몫뿐이며, 전체 비용 구조는 이 문서를 볼 것
- `docs/design/05-physical-architecture.md` — 물리 아키텍처. §7 네트워크의 경로를 물리 자원에 매핑
- `docs/adr/` — 아키텍처 결정 기록 (`AXM-` 시리즈). 각 결정의 근거와 기각된 대안
