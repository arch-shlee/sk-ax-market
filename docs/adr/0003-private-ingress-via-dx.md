# AXM-0003: 사용자 진입은 Direct Connect 사설 경로

- **상태**: Accepted
- **일자**: 2026-09-12
- **결정자**: 인프라 / 보안
- **관련 문서**: `05-physical-architecture.md` §2·§4, `03` 확정된 전제 F4·F5

## 맥락

임직원(VDI)이 앱마켓과 각 앱에 어떻게 도달하는가. Playground PoC는 **퍼블릭 인터넷 진입 + SG IP allowlist**(사용자 → IGW → EIP)를 쓰고 있다. 운영도 같은 형태로 갈 것인가.

온프렘과 AWS는 이미 **VPN + Direct Connect + TGW로 연결되어 있고 라우팅 구성도 완료**되어 있다.

## 결정

> 앱마켓과 Databricks Apps 모두 **Direct Connect 경유 사설 경로로 진입**한다. **인터넷 노출은 없다.**

| 대상 | 진입 |
|---|---|
| 앱마켓 | 내부 ALB (private subnet) + ACM 인증서 + 사내 도메인 |
| Databricks 워크스페이스 · Apps | front-end PrivateLink 인터페이스 EP + **`databricksapps.com` 조건부 DNS 포워딩** |

## 근거

- DX가 이미 있으므로 **추가 비용 없이** 사설 경로를 쓸 수 있다
- 앱마켓만 퍼블릭이고 Databricks Apps는 PrivateLink라면 **사용자가 앱마켓에서 앱으로 이동할 때 경로 성격이 바뀐다.** 둘 다 사내망 안에서 끝내는 편이 일관되고 보안 심사도 한 번으로 끝난다
- Databricks 공식 문서상 front-end PrivateLink는 온프렘 네트워크를 DX 또는 VPN으로 연결하면 구성 가능하다

## 결과

**얻는 것**
- 인터넷 노출 0. 공격면이 사내망 도달성으로 축소된다
- IP allowlist 유지보수가 불필요하다 (사내망 도달 자체가 경계)

**감수하는 것**
- **DNS 설계가 성립 조건이 된다.** 조건부 포워딩과 Route53 Resolver inbound/outbound 엔드포인트가 필요하다 (`05` §4)
- DX 회선이 전사 앱 트래픽의 단일 경로가 된다 → 용량·이중화 확인 필요
- 사외(재택·모바일)에서의 접근은 별도 논의 대상이 된다

## 검토한 대안

| 대안 | 평가 | 기각 사유 |
|---|---|---|
| PoC와 동일하게 퍼블릭 진입 + IP allowlist | 구성 단순 | 전사 앱마켓을 인터넷에 노출하고 IP 목록으로만 방어. Databricks Apps 진입과 비대칭 |
| 퍼블릭 진입 + WAF·인증 게이트웨이 | 사외 접근 가능 | DX가 이미 있는데 굳이 인터넷 경로를 만들 이유가 없다. 보안 심사 부담만 증가 |

## 미결 / 후속

- PoC의 **"임시 외부 오픈" 회수** — PoC 종료 시점
- 사외 접근 요구(재택 등)가 있는지 확인. 있으면 VDI 경유로 통일할지 별도 경로를 둘지
- DX 회선 용량·이중화 확인
