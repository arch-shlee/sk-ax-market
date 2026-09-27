# AX App Market · 인프라 아키텍처 v1.0

> 📐 [PNG](ax-market_infra.drawio.png) · [SVG](ax-market_infra.drawio.svg) · [PDF](ax-market_infra.drawio.pdf) · [편집용 draw.io](ax-market_infra.drawio)
> 세 내보내기 파일에는 draw.io XML이 내장되어 있어 draw.io에서 바로 다시 열어 편집할 수 있다.
> **작성일**: 2026-09-27 · **재생성**: `python3 docs/diagrams/tools/build_market_infra.py`

앱마켓 운영 계정을 중심으로 그린 물리 구성이다. 온프렘·Databricks·Cognito는 앱마켓과 연결되는 지점만 표시한다.

| 반영 결정 | 도면에서 보이는 곳 |
|---|---|
| `AXM-0007` 모듈러 모놀리스 · 레지스트리/프로젝션 | `market` 클러스터 안의 `web`(catalog · evidence · launch · authz)과 `worker`(registry 조정 루프 · ingest). 같은 이미지, 모드만 분리 |
| `AXM-0008` 조정 루프 | `worker` → 프로바이더(GitLab · VKS · Databricks) 점선. 방향은 마켓이 조회하는 pull |
| `AXM-0009` 리다이렉트 | ALB 뒤에 앱 트래픽 경로가 없다. 302 이후 사용자는 런타임에 직통 |
| `AXM-0013` 인프라 특성 | 인바운드 퍼블릭 경로 0, 서브넷 3계층 + 이그레스 전용, 증적 Object Lock, 2 AZ |
| `AXM-0014` Cognito SSO 중계 | 오른쪽 위 "AWS 관리형 · 퍼블릭" 영역 |
| `AXM-0015` 로그인 프록시 | 보라 선 — 사내 DNS → 내부 NLB → proxy → NAT → IGW → CloudFront → Cognito |
| `AXM-0016` Fargate · 클러스터 2개 | 주황 점선(`market`)과 보라 점선(`auth-proxy`) |

## 흐름

**① 사용자 진입 (파랑)**
1. VDI 브라우저가 사내 DNS로 `market.<사내도메인>`을 해석한다 → 내부 ALB 사설 IP
2. Direct Connect → Transit Gateway → 내부 ALB → `web` (2 AZ)
3. `/launch/:app_id`가 권한 확인 후 런타임 주소로 302. 이후 트래픽은 마켓을 지나지 않는다

**② 로그인 (보라)**
1. 사내 DNS · 앱마켓 VPC의 Route 53 PHZ가 `auth.<사내도메인>`을 **내부 NLB 고정 사설 IP**로 해석한다 (split-horizon)
2. 내부 NLB :443 → `proxy` (nginx stream, `ssl_preread`) — TLS를 종료하지 않고 SNI만 보고 넘긴다
3. `proxy` → NAT GW(EIP) → IGW → Cognito 커스텀 도메인의 CloudFront → Cognito 사용자 풀
4. WAF는 NAT EIP 2개와 Databricks 컨트롤 플레인 출구 IP만 허용한다
5. 원천 IdP와 Cognito 사이의 SAML 어서션은 브라우저를 거쳐 전달된다. 원천 IdP는 사내에만 있어도 된다
6. Databricks 계정 SSO의 토큰 교환만 퍼블릭 DNS 경로로 CloudFront에 직접 온다

**③ 조정 루프 · 프로바이더 · 데이터 (회색 점선)**
1. `worker`(단일 리더)가 TGW → DX로 GitLab · VKS를 조회한다
2. `worker`가 Databricks front-end PrivateLink EP로 워크스페이스 API를 호출한다 — 상태 조회, SCIM 그룹 동기화, `CAN_USE`
3. `market` 클러스터 → Aurora PostgreSQL (writer). 리더 보장은 advisory lock
4. 증적은 S3 Gateway EP로 Object Lock 버킷에 쓴다

## 구성 요소

| 구성 요소 | 역할 | 근거 |
|---|---|---|
| 내부 ALB | 앱마켓 진입. `market.<사내도메인>`, ACM | `05` §2-2 |
| 내부 NLB :443 | 로그인 프록시 진입. AZ별 고정 사설 IP라 사내 DNS A 레코드로 충분 | `AXM-0015` |
| ECS `market` · `web` × 2 | catalog · evidence · launch · authz | `AXM-0007`, `AXM-0016` |
| ECS `market` · `worker` × 1 | 조정 루프 · ingest · 그룹 동기화. AZ c 반투명은 장애 시 재기동 위치 | `AXM-0008`, `AXM-0016` |
| ECS `auth-proxy` · `proxy` × 2 | 전사 로그인 경로. 앱마켓과 클러스터·배포 분리 | `AXM-0015`, `AXM-0016` |
| Aurora PostgreSQL | 레지스트리 · 프로젝션. writer / reader Multi-AZ | `05` §5-1 |
| VPC 엔드포인트 | ECR · S3 · Logs · Secrets · KMS · STS. 프라이빗 서브넷에서 이미지·비밀 조회 | `AXM-0016` |
| Databricks front-end PrivateLink EP | 앱마켓 → Databricks REST API 사설 경로 | `05` §5-3 |
| NAT GW × 2 + IGW | **auth-proxy 서브넷 전용** 이그레스. EIP = WAF 허용목록 | `AXM-0015` |
| S3 증적 (Object Lock) | SBOM · 서명 · 승인 이력. 삭제 불가 | `06` §4-4, `AXM-0013` ② |
| Route 53 PHZ | 앱마켓 VPC 안에서도 `auth.*` → 로그인 NLB | `AXM-0015` |
| Cognito · CloudFront · WAF | SSO 중계와 그 퍼블릭 도메인. 우리 VPC 밖 | `AXM-0014` |

## 핵심 설계 판단

- **퍼블릭에 닿는 것은 로그인 프록시 하나다.** `market` 서브넷에는 NAT 경로가 없다. 앱마켓 자신의 Cognito 토큰 교환도 PHZ를 통해 프록시를 거친다
- **로그인 프록시는 전사 로그인의 단일 경로다.** 앱마켓 · Databricks · GitLab · Coder · VKS 로그인이 모두 지난다. 그래서 클러스터를 분리하고 2 AZ로 운영한다
- **worker는 한 번에 하나.** 반투명 아이콘은 두 번째 태스크가 아니라 재기동 위치를 뜻한다
- **Cognito 입장에서는 전 사용자가 NAT IP 2개로 보인다.** WAF의 IP 기반 rate 규칙을 쓰지 않는다

## 미확정 ⚠

- 로그인 프록시 PoC (`AXM-0015`)
- Databricks 서울 리전 컨트롤 플레인 출구 IP
- 원천 IdP 종류와 SAML 연계 범위(그룹 속성 포함)
- 목표 수량(앱 수 · 동시 사용자 · SLA)에 따른 태스크 사양
- 공유 네트워크 계정 유무 — 있으면 auth-proxy · NAT 이전 후보

## 아이콘

AWS 서비스·리소스 아이콘은 **AWS Architecture Icons 2026-07-31 패키지**(현재 최신)의 공식 SVG를 내장했다. draw.io 내장 `mxgraph.aws4` 스텐실은 쓰지 않았다. 계정 · VPC · 서브넷 경계만 draw.io AWS 그룹 도형이다. 출처와 SHA-256은 [`assets/icons/sources.json`](assets/icons/sources.json)에 있다.
