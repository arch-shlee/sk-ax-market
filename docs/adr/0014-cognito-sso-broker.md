# AXM-0014: SSO 중계는 Amazon Cognito — Keycloak을 쓰지 않는다

- **상태**: Accepted
- **일자**: 2026-09-27
- **결정자**: 아키텍처
- **관련 문서**: `03` §5, `05` §2·§5-3, `07`, `AXM-0015`, `AXM-0003`, `AXM-0009`, `AXM-0011`, `AXM-0013`, `databricks-apps-reference.md` §7

## 맥락

종전 설계는 **AD → Keycloak**을 신원 중계로 두고, Keycloak을 Databricks 계정 SSO의 OIDC IdP, 앱마켓 로그인, VKS Ingress forward-auth(`AXM-0011`)의 인증 주체로 가정했다(`03` §5). 구축 여부는 확인되지 않은 상태였다.

**원천 IdP는 우리가 관리하지 않는다.** 원천 IdP에 시스템을 하나 연계할 때마다 **약 700만 원의 비용**이 들고, 클레임 구성·클라이언트 추가 같은 변경도 우리 뜻대로 할 수 없다. 연계 대상이 늘어날 때마다 이 비용과 절차가 반복된다. → **중계 IdP가 필요한 이유다.** 원천 IdP와는 한 번만 연계하고, 그 뒤의 클라이언트 추가·클레임 설계는 우리가 직접 한다.

**Keycloak을 쓰지 않고 Amazon Cognito를 SSO 중계로 쓰는 계획이 제시되었다.** 연계 대상은 다음 전부다.

| 연계 대상 | 연계 방식(안) |
|---|---|
| AX App Market | OIDC (Cognito 앱 클라이언트) |
| Databricks 계정 SSO (Apps 포함) | OIDC |
| 온프렘 GitLab | OIDC (OmniAuth) |
| AX Playground (Coder) | OIDC |
| VKS 앱 (Ingress forward-auth) | OIDC (oauth2-proxy 계열) |

## 결정

> **Amazon Cognito 사용자 풀을 SSO 중계로 두고**, 사내 원천 IdP를 Cognito에 페더레이션한 뒤 모든 시스템은 Cognito에만 OIDC로 연계한다. Keycloak은 도입하지 않는다.

`AXM-0011`의 결정(Ingress 레벨 forward-auth)은 유지하되, 인증 주체를 Keycloak에서 Cognito로 바꾼다.

**로그인 경로**: Cognito 도메인은 사내망에 둘 수 없다(감수 1). 사내 사용자·서버는 **split-horizon DNS + 사내 L4 리버스 프록시**를 거쳐 도달한다 → `AXM-0015`. 프록시 PoC가 실패하면 각자 인터넷 도달(감수 1의 표)로 내려가며, 그것도 불가하면 이 ADR을 Superseded 처리하고 사설 경로가 완결되는 중계(Keycloak 등)를 재검토한다.

## 근거

- **원천 IdP 연계는 1회로 끝난다.** 직접 연계라면 앱마켓 · Databricks · GitLab · Coder · VKS forward-auth만으로 5건(약 3,500만 원)이고, 연계 대상이 늘 때마다 추가된다
- 클레임·그룹 매핑·클라이언트 구성을 우리가 통제한다
- 관리형 서비스라 IdP를 직접 운영하지 않는다 — `AXM-0013` ⑤ 운영 용이성
- 모든 연계 대상이 표준 OIDC를 지원한다. Databricks 계정 SSO는 SAML 2.0 / OIDC를 지원한다 ✅

## 결과

**얻는 것**
- IdP 서버 운영·패치·가용성 설계가 사라진다
- 연계 대상이 모두 한 발급자(issuer)를 바라본다

**감수하는 것** — 아래 세 가지는 승인 전에 해소되어야 한다

### ⚠️ 1. Cognito 로그인 엔드포인트는 인터넷 경로로만 도달한다 — F5와 충돌

✅ AWS 공식 문서: 사용자 풀 **도메인 엔드포인트**(managed login·hosted UI, `/oauth2/authorize`, `/oauth2/token`, 페더레이션 로그인)는 **PrivateLink로 접근할 수 없고 퍼블릭 경로로만 제공**된다. VPC 인터페이스 엔드포인트는 SDK·API 호출에만 쓰인다. 게다가 도메인이 할당된 사용자 풀은 PrivateLink와 호환되지 않는다.

따라서 OIDC 로그인을 쓰는 한 다음이 필요하다.

| 주체 | 필요한 인터넷 도달 |
|---|---|
| 임직원 VDI 브라우저 | `*.auth.ap-northeast-2.amazoncognito.com` (또는 커스텀 도메인) |
| 앱마켓 (토큰 교환·JWKS) | Cognito 도메인 — **NAT 필요**. `AXM-0013` "IGW·퍼블릭 IP 0"과 충돌 |
| 온프렘 GitLab · VKS oauth2-proxy | Cognito 도메인 — 사내 인터넷 아웃바운드 |
| Coder | Cognito 도메인 |
| Databricks 컨트롤 플레인 | Cognito 도메인 (Databricks 측 이그레스이므로 우리 쪽 조치 없음) |

**해소**: `AXM-0015` — 사내 DNS에서 Cognito 커스텀 도메인을 사내 리버스 프록시로 해석시켜, 인터넷 도달을 **프록시 한 곳(NAT EIP 2개)** 으로 모은다. WAF는 NAT EIP와 Databricks 컨트롤 플레인 출구 IP만 허용한다. 위 표는 프록시 PoC 실패 시의 폴백 구성이다. F5는 "사내 사용자·서버는 인터넷 직접 도달 없음, **IdP 도메인만 퍼블릭 + WAF IP 제한**"으로 재정의되며 **보안 승인 대상이다.**

### ⚠️ 2. Cognito는 SCIM 프로비저닝을 하지 않는다

Databricks 권한 모델은 **그룹**(`CAN_USE`, UC 권한)에 기대고, 그룹 동기화는 automatic identity management 또는 SCIM으로 이뤄진다. Cognito는 어느 쪽도 제공하지 않는다. JIT 프로비저닝은 사용자만 만든다.

→ **원천 IdP(또는 AD) → Databricks SCIM API로 그룹을 넣는 별도 동기화 작업**이 필요하다. 앱마켓 `authz` 모듈의 워커 작업으로 둘 수 있다. GitLab·Coder의 그룹 반영 방식도 같은 문제를 갖는다(제품 tier별 확인 필요).

### ⚠️ 3. 그룹 클레임은 자동으로 실리지 않는다

`cognito:groups`는 Cognito 내부 그룹이다. 페더레이션 사용자의 원천 그룹은 **속성 매핑(커스텀 속성) 또는 Pre token generation Lambda**로 토큰에 넣어야 한다. VKS forward-auth의 인가 판단이 이 클레임에 의존한다.

### 가용성 의존의 변화

종전 가정(온프렘 Keycloak = DX 경유)에서는 IdP가 사용자 진입 경로와 운명을 같이했다. 이제 로그인은 **Cognito 리전 서비스 + 원천 IdP + 로그인 프록시(`AXM-0015`) + NAT**에 의존한다. 프록시는 전사 로그인의 단일 경로이므로 앱마켓 이상의 가용성 등급으로 운영한다. `AXM-0013` ④의 상한이 이것으로 바뀐다.

## 검토한 대안

| 대안 | 평가 | 기각 사유 |
|---|---|---|
| Keycloak (종전 가정) | 사설 경로 완결, SCIM은 확장 필요 | 운영 부담. 도입하지 않기로 함 |
| AWS IAM Identity Center | Databricks 공식 SSO 가이드 존재, SCIM 지원 | 검토 필요 — 워크포스 SSO 용도이며 앱 OIDC 발급자로서의 적합성 확인 전 |
| 원천 IdP에 각 시스템 직접 연계 | 중계가 없어 구조는 가장 단순 | **연계 1건당 약 700만 원**, 변경 통제권이 없다. 연계 대상이 늘수록 비용·절차가 반복된다 |

## 미결 / 후속

- **원천 IdP는 무엇인가** (온프렘 AD + AD FS? Entra ID? 사내 SSO 솔루션?) — 페더레이션 방식(SAML/OIDC)과 그룹 소스를 결정한다
- **원천 IdP ↔ Cognito는 SAML 권장.** OIDC 페더레이션은 Cognito가 원천 IdP의 토큰 엔드포인트를 서버 간 호출하므로 원천 IdP가 인터넷에서 도달 가능해야 한다. SAML은 어서션이 브라우저를 거쳐 전달되고 메타데이터는 파일로 등록할 수 있어, 원천 IdP가 사내망에만 있어도 성립한다 ⚠️ 원천 IdP 확인 후 검증
- 원천 IdP 연계 1건(약 700만 원)에 **그룹 속성 전달을 반드시 포함**시킬 것. 나중에 추가하면 비용이 또 든다 (감수 2·3)
- **로그인 프록시 PoC** — `AXM-0015`
- **F5 재정의에 대한 보안 승인** (감수 1)
- 그룹 동기화 작업 설계 (감수 2) — Databricks SCIM API 대상
- 사용자 풀 커스텀 도메인(`auth.<사내도메인>`) — `AXM-0015`의 전제. us-east-1 퍼블릭 ACM 인증서, 퍼블릭 DNS 레코드 필요
- 도면(`diagrams/`)의 Keycloak 아이콘·라벨 교체 — 문서 개정은 2026-09-27 반영 완료

## 참고

- [Access Amazon Cognito using an interface endpoint (AWS PrivateLink) — 공식](https://docs.aws.amazon.com/cognito/latest/developerguide/vpc-interface-endpoints.html)
- [Configure SSO in Databricks — 공식](https://docs.databricks.com/aws/en/security/auth/single-sign-on/)
- [Sync users and groups from your identity provider using SCIM — 공식](https://docs.databricks.com/aws/en/admin/users-groups/scim/)
