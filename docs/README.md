# AX App Market — 설계 문서

원 기획서(`source/AX앱마켓구성1.pdf`)의 "전체 구성을 그려보자"에서 출발한 설계 문서 모음이다.

## 폴더

| 폴더 | 내용 |
|---|---|
| [`design/`](design/) | 설계 문서 (01~06). **번호는 안정적 ID**이며 읽는 순서가 아니다 |
| [`adr/`](adr/README.md) | 아키텍처 결정 기록. `AXM-` 접두어 |
| [`reference/`](reference/) | 기술 사실관계와 자료조사. 설계의 근거 |
| [`diagrams/`](diagrams/) | draw.io 도면. mermaid 도면은 각 설계 문서 안에 있다 |
| [`mockups/`](mockups/app-market/README.md) | 화면 목업 (경영진 보고용 4화면 · 앱 등록 프로세스) |
| [`source/`](source/) | 원 기획서 등 입력물 |

> **번호를 바꾸지 않는 이유**: 본문과 ADR 전체가 `` `03` §4 ``, `` `05` §8-1 `` 같은 짧은 형태로 서로를 참조한다. 번호는 생성 순서일 뿐 읽는 순서가 아니며, 읽는 순서는 아래에서 제공한다.

## 읽는 순서

**처음 보는 사람**

1. [`source/ax_extract.txt`](source/ax_extract.txt) — 기획 의도 (원문 발췌)
2. [`design/03`](design/03-runtime-decision-and-architecture.md) — **여기가 실질적 시작점.** 런타임 판정 기준과 To-Be 전체 구성
3. [`design/05`](design/05-physical-architecture.md) — 계정·네트워크 물리 배치
4. [`design/06`](design/06-app-market-architecture.md) — 앱마켓 내부 구조
5. [`adr/README.md`](adr/README.md) — 왜 그렇게 정했는지

**깊이 파는 경우**

- CI/CD·보안 게이트 → [`design/02`](design/02-cicd-pipeline-design.md)
- 보안 검토·통제 요약 → [`design/07`](design/07-secure-delivery.md)
- 비용 → [`design/04`](design/04-cost-model.md)
- Databricks 기술 제약 → [`reference/databricks-apps-reference.md`](reference/databricks-apps-reference.md)
- 업계 동향·근거 → [`reference/cicd-devsecops-research.md`](reference/cicd-devsecops-research.md)
- WIF 검증 절차 (실행 대기) → [`design/01`](design/01-gitlab-databricks-wif-verification.md)

## 문서별 역할

| # | 문서 | 역할 |
|---|---|---|
| 01 | [WIF 검증 설계](design/01-gitlab-databricks-wif-verification.md) | 온프렘 GitLab ↔ Databricks 인증 성립 여부 검증 **절차**. 결과 기록란 있음 |
| 02 | [CI/CD 파이프라인 설계](design/02-cicd-pipeline-design.md) | 두 트랙의 검증·승인·배포 파이프라인, 정책 강제 |
| 03 | [런타임 판정 · To-Be 구성](design/03-runtime-decision-and-architecture.md) | 판정 트리, 전체 논리 구성, 신원·권한, 메타데이터 스키마 |
| 04 | [비용 모델](design/04-cost-model.md) | 3층 비용 구조, 규모 시나리오, 통제 규칙 |
| 05 | [물리 아키텍처](design/05-physical-architecture.md) | 계정 토폴로지, 진입 경로, DNS, 앱마켓 배치 |
| 06 | [앱마켓 내부 아키텍처](design/06-app-market-architecture.md) | 엔티티·관계, 모듈, 조정 루프, 수명주기 상태 머신 |
| 07 | [DevSecOps 안전한 배포 경로](design/07-secure-delivery.md) | 통제 지도, 개발자가 할 수 없는 것, 신뢰 경계·자격증명, **보안팀 결정 요청** |

## 확정된 전제

`design/03`의 F1~F7. 요약하면:

- **AWS · ap-northeast-2** / Databricks는 **별도 전용 계정** / 계약 **Enterprise tier**
- 온프렘 ↔ AWS **VPN + Direct Connect + TGW 기구축**, 라우팅 구성 완료
- 사용자 진입은 **DX 경유. 인터넷 노출 없음**
- 앱마켓은 **AWS 전용 계정에 별도 구현**
- AX Playground = **Coder 기반 클라우드 개발환경** (PoC 가동 중)

2026-09-27 결정 (ADR): 인프라 특성 5개(`AXM-0013`) · SSO 중계 **Cognito**(`AXM-0014`) · 로그인 프록시 + split-horizon DNS(`AXM-0015`) · 컴퓨트 **ECS Fargate**(`AXM-0016`)

## 지금 막혀 있는 것

전체 목록은 [`design/03` §8](design/03-runtime-decision-and-architecture.md), 물리 항목은 [`design/05` §8](design/05-physical-architecture.md).

| 순위 | 항목 | 막는 것 |
|---|---|---|
| 1 | **망분리 대상 여부 · 데이터 등급 체계 (A5)** | 사내 시스템 노출 승인, Bedrock 엔드포인트, 판정 트리의 등급 축 |
| 2 | **NLB IP 타깃 → 온프렘 도달 검증** | Q1 성립의 마지막 조각 |
| 3 | **사내 시스템 노출 보안 승인** | Q1의 실질 판정 기준 |
| 4 | GitLab Ultimate 여부 | 정책 강제 — 로드맵 1단계 |
| 5 | WIF 성립 여부 | Databricks 트랙 배포 인증 |
| 6 | 앱마켓 운영 계정 CIDR 확보 | 물리 구성 착수 — **리드타임 최장** |
| 7 | 목표 수량 (앱 수 · 동시 사용자 · SLA 등급 정의) | 사이징 전반 |
| 8 | **원천 IdP 확인 + Cognito SAML 연계 (그룹 속성 포함)** | 전 시스템 SSO. 연계 1건 약 700만 원 — 한 번에 범위 확정 (`AXM-0014`) |
| 9 | **로그인 프록시 PoC** + Databricks 컨트롤 플레인 출구 IP | Cognito 로그인 경로 성립 (`AXM-0015`) |

> 1~3번은 한 묶음이다. 셋 다 Q1(사내 시스템 연동 앱을 Databricks에 둘 수 있는가)에 걸려 있다.

## 도면

| 도면 | 위치 |
|---|---|
| **앱마켓 인프라 아키텍처 v1.0 (최신)** | [PNG](diagrams/ax-market_infra.drawio.png) · [SVG](diagrams/ax-market_infra.drawio.svg) · [PDF](diagrams/ax-market_infra.drawio.pdf) · [편집용 draw.io](diagrams/ax-market_infra.drawio) · [해설](diagrams/ax-market_infra.md). 앱마켓 운영 계정 중심. `AXM-0007`·`0013`~`0016` 반영 — web/worker 모듈 배치, ECS 클러스터 2개, 로그인 프록시(split-horizon DNS), 증적 Object Lock. AWS 아이콘은 2026-07-31 공식 패키지 SVG. 재생성은 [`tools/build_market_infra.py`](diagrams/tools/build_market_infra.py) |
| **AX 앱 운영 체계 — 배치·DevSecOps 통합 뷰 (현재)** | [SVG](diagrams/ax-app-operating-devsecops.svg) · [PNG](diagrams/ax-app-operating-devsecops.png) · [PDF](diagrams/ax-app-operating-devsecops.pdf) · [편집용 draw.io](diagrams/ax-app-operating-devsecops.drawio.xml). 참고 이미지의 도메인·인프라 계층 표현을 반영. 검증·승인·배포 지시는 온프렘 GitLab에, 개발은 AWS Playground에, 실행 통제는 VKS·Databricks에 배치. VKS GitOps와 Databricks Bundle 배포 경로를 구분 |
| **AX 앱 운영 체계 — 논리·인프라 통합 뷰** | [SVG](diagrams/ax-app-operating-hybrid.svg) · [PNG](diagrams/ax-app-operating-hybrid.png) · [PDF](diagrams/ax-app-operating-hybrid.pdf) · [편집용 draw.io](diagrams/ax-app-operating-hybrid.drawio.xml). 온프렘·AWS 계정·Databricks 운영 경계 안에 논리 기능, 앱마켓 Multi-AZ, 저장소, 사설 진입·사내 연동 경로를 함께 표현. 자원 아이콘 수는 실제 수량과 무관 |
| **AX 앱 운영 체계 — 도메인·구성요소 뷰** | [SVG](diagrams/ax-app-operating-architecture.svg) · [PNG](diagrams/ax-app-operating-architecture.png) · [PDF](diagrams/ax-app-operating-architecture.pdf) · [편집용 draw.io](diagrams/ax-app-operating-architecture.drawio.xml). 참고 이미지의 도메인 경계·아이콘·인프라 계층 표현을 반영한 주요 구성도 |
| **AX 앱 운영 체계 — 경영진용 목표 구성도** | [SVG](diagrams/ax-app-operating-model.svg) · [편집용 draw.io](diagrams/ax-app-operating-model.drawio.xml). 개발·공급과 임직원 활용 흐름, 공통 관리·통제, 추진 조건을 한 장으로 요약 |
| 런타임 판정 트리 | `design/03` §2 (mermaid) |
| To-Be 전체 논리 구성 | `design/03` §4 (mermaid) |
| 앱 실행 경로 | `design/03` §4-1 (mermaid) |
| 엔티티·관계 | `design/06` §2 (mermaid) |
| 조정 루프 | `design/06` §4 (mermaid) |
| 앱 수명주기 상태 머신 | `design/06` §6 (mermaid) |
| DevSecOps 통제 지도 | `design/07` §1 (mermaid) |
| **목표 인프라 · 경로 · 보안** | [`diagrams/ax-market_target 아키텍처.drawio.xml`](diagrams/) (8페이지 — 인프라 / 경로 / 보안 / 인프라 v0.2~**v0.6**) |
| **목표 인프라 뷰 v0.6 — AWS 공식 아이콘 (현행)** | [SVG](diagrams/ax-market_target-infra-aws-v6.svg) · [PNG](diagrams/ax-market_target-infra-aws-v6.png) · [PDF](diagrams/ax-market_target-infra-aws-v6.pdf). 위 파일 **8페이지**. 구성요소·선 라벨을 굵게 하고, 사내 업무 시스템을 **MES · ERP · SRM · CRM · Wehub** 개별 시스템으로 펼치고 여섯 번째 칸을 `그 외`로 열어 둔 판. 재생성은 [`tools/build_target_aws_v6.py`](diagrams/tools/build_target_aws_v6.py) |
| 목표 인프라 뷰 v0.2 ~ v0.5 | 각각 위 파일 4~7페이지. [v0.5](diagrams/ax-market_target-infra-aws-v5.svg) 글자·강조 체계 도입, [v0.4](diagrams/ax-market_target-infra-aws-v4.svg) 현 배치의 원본, [v0.3](diagrams/ax-market_target-infra-aws-v3.svg) AWS 그룹 스텐실·7색, [v0.2](diagrams/ax-market_target-infra-aws-v2.svg) 근거·미결 주석 포함 |
| 목표 인프라 뷰 v0.2 — AWS 공식 아이콘 | [SVG](diagrams/ax-market_target-infra-aws-v2.svg) · [PNG](diagrams/ax-market_target-infra-aws-v2.png) · [PDF](diagrams/ax-market_target-infra-aws-v2.pdf). 위 파일 4페이지. v0.3과 같은 배치에 근거·미결 주석을 함께 실은 판. 재생성은 [`tools/build_target_aws_view.py`](diagrams/tools/build_target_aws_view.py) |
| **화면 목업 v1 — 경영진 보고용** | [해설 · 앱 등록 프로세스](mockups/app-market/README.md) · [캔버스](https://claude.ai/artifact/WS3m3U5Rm6G5k6WfEiuQHe). 앱 찾기 · 앱 상세 · 앱 등록 · 내 앱 4화면. 에이전트 · 운영 콘솔 제외 |
| Playground PoC | [`diagrams/axplayground_PoC 아키텍처.drawio.xml`](diagrams/) (2페이지) |

> ⚠️ `ax-market_infra` 외의 draw.io 도면에는 아직 **Keycloak**이 남아 있고 로그인 프록시가 없다. `AXM-0014`·`AXM-0015` 반영 전이다.

> 논리·흐름 도면은 **mermaid로 문서 안에** 둔다(diff가 읽히고 수정이 빠름). 물리 배치는 **draw.io**로 둔다.

현재 배치·DevSecOps 구성도의 제품 아이콘은 [공식 출처와 재생성 방법](diagrams/assets/icons/README.md)을 함께 관리한다. SVG·draw.io 파일에 아이콘을 내장해 외부 이미지 링크 없이 열 수 있다.

## 규칙

- 설계 문서 번호는 **바꾸지 않는다**. 새 문서는 다음 번호를 받는다
- 결정은 문서 본문이 아니라 **ADR에 기록**한다. 결정을 바꿀 때는 새 ADR을 쓰고 기존 것을 `Superseded`로 표시한다
- 사실과 추정을 구분해 표기한다 — ✅ 공식 문서 / ⚠️ 확인 필요 / 💡 제언
- 확인되지 않은 것은 **가정으로 명시**하고, 확정되면 사실로 교체하며 영향받는 절을 함께 고친다
