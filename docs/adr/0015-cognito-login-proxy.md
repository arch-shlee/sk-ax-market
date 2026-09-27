# AXM-0015: Cognito 로그인 경로는 split-horizon DNS + 사내 L4 리버스 프록시

- **상태**: Accepted
- **일자**: 2026-09-27
- **결정자**: 아키텍처
- **관련 문서**: `05` §4·§5-3-1, `AXM-0003`, `AXM-0013`, `AXM-0014`, `AXM-0016`

## 맥락

`AXM-0014`로 Cognito를 SSO 중계로 정했다. 그러나 Cognito의 로그인·토큰 엔드포인트는 **사내망 안에 둘 수 없다.** AWS 공식 문서로 확인한 사실은 다음과 같다.

| 사실 | 출처 |
|---|---|
| managed login, `/oauth2/authorize`·`/oauth2/token`, SAML·OIDC 페더레이션 응답은 **사용자 풀 도메인에서만 제공**된다. OIDC 공급자로 쓰려면 도메인이 필수다 | ✅ User pool endpoints reference |
| 도메인 엔드포인트는 **PrivateLink로 도달할 수 없다.** 도메인이 붙은 풀은 PrivateLink와 호환되지 않는다 | ✅ PrivateLink |
| 커스텀 도메인은 **CloudFront로 구현되며 private hosted zone을 지원하지 않는다.** us-east-1 퍼블릭 ACM 인증서가 필요하다 | ✅ Custom domain |
| WAF는 managed login·OAuth 엔드포인트를 포함한 **모든 요청에 IP 허용목록을 걸 수 있다** | ✅ WAF |
| 2025-11 PrivateLink 지원은 **관리 API와 로컬 사용자 인증**만 대상이다. 페더레이션은 제외 | ✅ What's New 2025-11 |

그대로 쓰면 VDI 브라우저, 온프렘 GitLab, VKS forward-auth, Coder, 앱마켓이 **각자 인터넷으로** Cognito에 나가야 한다. 사내 인터넷 출구는 우리가 관리하지 않는다.

## 결정

> Cognito 커스텀 도메인(`auth.<사내도메인>`)을 **split-horizon DNS**로 운영한다. 사내 DNS에서는 **사내 L4 리버스 프록시**로, 퍼블릭 DNS에서는 CloudFront로 해석되게 한다. 인터넷으로 나가는 지점은 프록시 하나로 모은다.

```
VDI · GitLab · VKS · Coder · 앱마켓
      │  auth.<사내도메인> → 사내 DNS / Route53 PHZ → 내부 NLB 고정 사설 IP
      ▼
내부 NLB :443 ──▶ auth-proxy (ECS Fargate, nginx stream + ssl_preread, TLS 패스스루)
                        │  upstream = Cognito가 발급한 CloudFront 별칭 대상 (dxxxx.cloudfront.net)
                        ▼
                  NAT GW ×2 (EIP) ──▶ Cognito CloudFront ── WAF: NAT EIP 2개 + Databricks CP 출구 IP만 허용

Databricks 컨트롤 플레인 ──퍼블릭 DNS──▶ Cognito CloudFront (토큰 교환)
원천 IdP ──SAML POST(브라우저 경유)──▶ auth.<사내도메인>/saml2/idpresponse → 프록시
```

| 구성요소 | 내용 |
|---|---|
| **프록시 방식** | **L4 SNI 패스스루.** TLS를 종료하지 않는다. 브라우저는 CloudFront의 ACM 인증서를 그대로 받는다 |
| **프록시 upstream** | `auth.<사내도메인>`이 아니라 **CloudFront 별칭 대상**. 사내 DNS로 조회하면 자기 자신으로 돌아오는 루프가 생긴다 |
| **실행** | 전용 ECS 클러스터 `auth-proxy`, Fargate 0.25 vCPU / 0.5 GB × 2 (AZ 분산) — `AXM-0016` |
| **진입** | 내부 NLB. AZ별 사설 IP가 고정되므로 온프렘 DNS는 **A 레코드만으로** 가리킨다 |
| **이그레스** | 이그레스 전용 NAT GW × 2. **EIP = WAF 허용목록.** 인바운드 퍼블릭 경로 없음 |
| **앱마켓 VPC** | Route53 private hosted zone에 같은 레코드. 앱마켓의 토큰 교환도 프록시를 거친다 |

## 근거

- **사내 사용자·서버는 인터넷에 직접 나가지 않는다.** F5의 취지가 유지된다. 퍼블릭 쪽에 남는 것은 두 종류의 IP만 허용한 Cognito 도메인이다
- **호스트명이 원본과 같다.** Cognito 쿠키·리다이렉트가 그대로 동작하고, 토큰 `iss`는 도메인과 무관하게 `cognito-idp.<region>.amazonaws.com/<poolId>`로 고정된다. 클라이언트 설정은 바뀌지 않는다
- **원천 IdP가 사내에만 있어도 SAML 연계가 성립한다** (`AXM-0014` 미결 — SAML 권장과 정합)
- **L4 패스스루라서** 별도 인증서 발급·VDI 신뢰 배포가 없고, managed login 쿠키가 프록시 헤더 한도에 걸리지 않는다
- **NAT EIP는 우리가 소유한 고정 IP다.** 사내 인터넷 출구는 원천 IdP와 같은 이유(타 조직 관리, 변경 통제권 없음)로 기대지 않는다
- **폴백이 DNS 한 줄이다.** 사내 DNS 레코드를 지우면 퍼블릭 경로(직접 인터넷)로 내려간다

## 결과

**얻는 것**
- 인터넷 이그레스 지점 1곳, WAF 허용목록 최소화
- VDI · 온프렘 서버의 인터넷 정책 변경 불필요

**감수하는 것**
- **프록시가 전사 로그인의 단일 경로다.** 앱마켓 · Databricks · GitLab · Coder · VKS 로그인이 모두 거친다. 최소 2 태스크, NLB 헬스체크, 앱마켓과 클러스터·배포 파이프라인 분리
- **Cognito에서 모든 사용자가 NAT IP 2개로 보인다.** WAF의 IP 기반 rate 규칙은 전 직원을 한꺼번에 차단할 수 있으므로 쓰지 않는다. Cognito threat protection의 IP 기반 위험 판단도 무력화된다. 사용자 단위 방어는 원천 IdP에 맡긴다
- 앱마켓 운영 계정에 IGW가 생긴다(이그레스 전용 NAT용). **인바운드 퍼블릭 경로 0**으로 기준을 재정의한다 — `AXM-0013` ①
- **CloudFront 별칭 대상은 Cognito가 발급하는 값**이다. 커스텀 도메인을 재생성하면 바뀌므로 IaC로 결선한다
- AWS 공식 가이드 패턴은 아니다. AWS 문서는 "커스텀 도메인 앞의 ALB 같은 중간 서비스"를 쿠키 크기 주의사항에서 언급할 뿐이다

## 검토한 대안

| 대안 | 평가 | 기각 사유 |
|---|---|---|
| 커스텀 도메인 + WAF, 각자 인터넷 도달 | 공식 방식, 가장 단순 | VDI · 온프렘 서버 전부에 인터넷 출구 필요. **폴백으로 유지** |
| 도메인 없이 API만 사용 (PrivateLink) | 완전 사설 | OIDC 공급자·페더레이션이 사라져 SSO 중계로 쓸 수 없다 |
| L7 프록시 (TLS 종료) | 헤더 삽입·로깅 풍부 | 인증서 발급·VDI 신뢰 배포, 쿠키·헤더 크기 한도 문제 |
| API Gateway 사설 API 중계 | 관리형 | L7 종료라 위와 같은 문제 |
| EC2 위 nginx | 익숙함 | 노드 운영 부담 — `AXM-0013` ⑤ |
| 앱마켓 서비스에 프록시 동거 | 자원 절약 | 앱마켓 배포·장애가 전사 로그인에 영향 |
| 사내 인터넷 출구 경유 | IGW 불필요 | 타 조직 관리. 허용목록 변경 통제권 없음 |
| NLB가 CloudFront를 직접 타깃 | 프록시 불필요 | 불가 — NLB IP 타깃은 사설 대역만 허용 |

## 미결 / 후속

- **PoC 검증** — 테스트 사용자 풀 + 커스텀 도메인 + split-horizon + 프록시로 VDI 로그인 → Databricks 계정 SSO 결선까지
- **Databricks 서울 리전 컨트롤 플레인 출구 IP** 확인 — WAF 허용목록에 필요 ⚠️
- AWS 담당 SA에 구성 공유 — 지원 범위 확인
- 프록시 배치 계정: 공유 네트워크 계정이 생기면 이전 후보 (`05` §1-2와 같은 논점)
- 운영 절차: 폴백(DNS 레코드 삭제) 조건과 담당자 — 단, 폴백은 VDI에 인터넷 출구가 있을 때만 유효

## 참고

- [User pool endpoints and managed login reference — 공식](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-userpools-server-contract-reference.html)
- [Access Amazon Cognito using an interface endpoint (AWS PrivateLink) — 공식](https://docs.aws.amazon.com/cognito/latest/developerguide/vpc-interface-endpoints.html)
- [Using your own domain for managed login — 공식](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html)
- [Associate an AWS WAF web ACL with a user pool — 공식](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html)
- [Amazon Cognito user pools now supports private connectivity with AWS PrivateLink (2025-11)](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-cognito-user-pools-private-connectivity-aws-privatelink)
