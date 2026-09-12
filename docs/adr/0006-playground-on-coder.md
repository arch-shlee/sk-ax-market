# AXM-0006: AX Playground는 Coder 기반 클라우드 개발환경

- **상태**: Accepted
- **일자**: 2026-09-12 (PoC는 선행 진행)
- **결정자**: 플랫폼 (PoC 주관)
- **관련 문서**: `axplayground_PoC 아키텍처.drawio.xml`, `03` 구성요소 표, `05` §7

## 맥락

기획서와 설계 문서는 AX Playground를 "Golden Path의 시작점"으로 규정했으나 **물리적 실체가 정의되지 않은 상태**였고, `03` 구성요소 표에 "재정의 필요"로 남아 있었다. 시작점의 실체가 없으면 개발자 여정이 비어 있는 것과 같다.

PoC가 이미 진행 중이며 도면이 존재한다.

## 결정

> AX Playground를 **Coder 기반 클라우드 개발환경**으로 한다.

| 구성요소 | 내용 |
|---|---|
| 컨트롤 플레인 | Coder Server + built-in PostgreSQL (PoC: EC2 단일) |
| 개발 워크스페이스 | EC2 · VS Code + **Claude Code Dev Container** |
| LLM (개발 도구) | Amazon Bedrock (Claude), IAM Role |
| 배치 | AWS 259537089696 · ap-northeast-2 · private subnet |

**Golden Path 스캐폴드는 Coder 워크스페이스 템플릿 + Dev Container 이미지에 결선한다.** 개발자가 처음부터 파이프라인·보안정책·로깅이 연결된 상태에서 시작하게 된다.

## 근거

- 개발 환경이 클라우드에 있으면 **표준 환경을 플랫폼이 통제**할 수 있다. "공통 검증 기준"이 개발자에게 부담이 아니라 기본값이 되려면 시작점이 통제 가능해야 한다
- 워크스페이스가 사내망 경로를 가지므로 **온프렘 GitLab으로의 push가 성립**한다(라우팅 구성 완료)
- PoC가 이미 가동 중이므로 채택 검증이 진행되고 있다

## 결과

**얻는 것**
- Golden Path의 시작점이 물리적 실체를 갖는다
- 스캐폴드 배포 경로가 확정된다 — GitLab 템플릿이 아니라 **Coder 템플릿 + Dev Container**

**감수하는 것**
- **`02` §4-2와 `03` MAKE 영역을 다시 써야 한다.** 종전에는 스캐폴드를 GitLab 템플릿으로 상정했다
- 워크스페이스 EC2도 상시 과금 대상이다. 수명주기·유휴 정지 정책이 필요하다 (`AXM-0005`와 같은 문제)
- PoC 구성(단일 EC2, built-in DB, 자체서명 TLS, 1인 운영)은 운영으로 그대로 갈 수 없다 → `05` §7 전환 체크리스트

## 검토한 대안

| 대안 | 평가 | 기각 사유 |
|---|---|---|
| 로컬 PC 개발 | 진입 장벽 낮음 | 표준 환경을 통제할 수 없다. 사내 정책·보안 도구 결선이 개발자 재량이 된다 |
| Databricks 노트북/워크스페이스를 Playground로 | 별도 인프라 불필요 | Web App 개발에 적합하지 않다. Git 연동도 온프렘 GitLab 도달성 문제에 걸린다 |

## 미결 / 후속

- **워크스페이스 → 온프렘 GitLab push 실제 확인** (라우팅은 구성됨)
- **Agent App 런타임의 LLM이 어디인가** — PoC의 Bedrock은 개발자용 코딩 어시스턴트로 보인다. AX Agent App **자체가 실행 시 호출할 LLM**(Databricks 모델서빙 / Bedrock)은 별도 결정 사항이며, `02` §8 Agent 게이트와 `04` §2-3 변동비가 여기에 달려 있다
- Bedrock 인터페이스 VPC 엔드포인트 (현재 NAT 경유)
- 운영 전환 시 Multi-AZ·관리형 DB·ACM 인증서
