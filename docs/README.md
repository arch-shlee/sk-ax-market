# AX App Market — 설계 문서

원 기획서(`source/AX앱마켓구성1.pdf`)의 "전체 구성을 그려보자"에서 출발한 설계 문서 모음이다.

## 폴더

| 폴더 | 내용 |
|---|---|
| [`design/`](design/) | 설계 문서 (01~06). **번호는 안정적 ID**이며 읽는 순서가 아니다 |
| [`adr/`](adr/README.md) | 아키텍처 결정 기록. `AXM-` 접두어 |
| [`reference/`](reference/) | 기술 사실관계와 자료조사. 설계의 근거 |
| [`diagrams/`](diagrams/) | draw.io 도면. mermaid 도면은 각 설계 문서 안에 있다 |
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

> 1~3번은 한 묶음이다. 셋 다 Q1(사내 시스템 연동 앱을 Databricks에 둘 수 있는가)에 걸려 있다.

## 도면

| 도면 | 위치 |
|---|---|
| 런타임 판정 트리 | `design/03` §2 (mermaid) |
| To-Be 전체 논리 구성 | `design/03` §4 (mermaid) |
| 앱 실행 경로 | `design/03` §4-1 (mermaid) |
| 엔티티·관계 | `design/06` §2 (mermaid) |
| 조정 루프 | `design/06` §4 (mermaid) |
| 앱 수명주기 상태 머신 | `design/06` §6 (mermaid) |
| DevSecOps 통제 지도 | `design/07` §1 (mermaid) |
| **목표 인프라 · 경로 · 보안** | [`diagrams/ax-market_target 아키텍처.drawio.xml`](diagrams/) (3페이지) |
| Playground PoC | [`diagrams/axplayground_PoC 아키텍처.drawio.xml`](diagrams/) (2페이지) |

> 논리·흐름 도면은 **mermaid로 문서 안에** 둔다(diff가 읽히고 수정이 빠름). 물리 배치는 **draw.io**로 둔다.

## 규칙

- 설계 문서 번호는 **바꾸지 않는다**. 새 문서는 다음 번호를 받는다
- 결정은 문서 본문이 아니라 **ADR에 기록**한다. 결정을 바꿀 때는 새 ADR을 쓰고 기존 것을 `Superseded`로 표시한다
- 사실과 추정을 구분해 표기한다 — ✅ 공식 문서 / ⚠️ 확인 필요 / 💡 제언
- 확인되지 않은 것은 **가정으로 명시**하고, 확정되면 사실로 교체하며 영향받는 절을 함께 고친다
