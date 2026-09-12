# 아키텍처 결정 기록 (ADR)

AX App Market 플랫폼의 아키텍처 결정을 기록한다. **왜 그렇게 정했는지**를 남기는 것이 목적이며, 나중에 "이건 왜 이렇게 되어 있나"를 재구성할 수 있어야 한다.

## 번호 체계

> ⚠️ **AX Playground PoC 프로젝트가 별도의 ADR 시리즈를 갖고 있다** (PoC 도면이 참조하는 `ADR-0002 dual-account`). 번호가 겹치므로 **본 시리즈는 `AXM-` 접두어를 사용**한다. 파일명은 관례대로 `NNNN-제목.md`를 유지한다.
>
> 문서 간 참조 시에는 반드시 접두어를 붙인다 — `AXM-0004`, `Playground ADR-0002`.

## 상태

| 상태 | 의미 |
|---|---|
| **Accepted** | 확정. 설계 문서가 이 결정을 전제로 작성된다 |
| **Proposed** | 제안. 근거는 정리되었으나 승인 전. 반대 근거가 나오면 바뀔 수 있다 |
| **Superseded by AXM-NNNN** | 다른 결정으로 대체됨. 본문은 이력을 위해 남긴다 |
| **Deprecated** | 더 이상 유효하지 않으나 대체 결정이 없음 |

## 목록

### 확정

| # | 제목 | 상태 | 일자 |
|---|---|---|---|
| [AXM-0001](0001-runtime-two-tracks.md) | 운영 런타임 2종 채택과 Databricks Apps 우선 적용 | Accepted | 2026-09-12 |
| [AXM-0002](0002-cloud-account-topology.md) | 클라우드·계정 토폴로지 | Accepted | 2026-09-12 |
| [AXM-0003](0003-private-ingress-via-dx.md) | 사용자 진입은 Direct Connect 사설 경로 | Accepted | 2026-09-12 |
| [AXM-0004](0004-q1-redefinition.md) | 런타임 판정 Q1 재정의 — 물리적 제약에서 보안 승인으로 | Accepted | 2026-09-12 |
| [AXM-0005](0005-app-cost-controls.md) | Databricks Apps 비용 통제 — 유휴 정지 의무와 공용 웨어하우스 강제 | Accepted | 2026-09-12 |
| [AXM-0006](0006-playground-on-coder.md) | AX Playground는 Coder 기반 클라우드 개발환경 | Accepted | 2026-09-12 |
| [AXM-0009](0009-app-launch-redirect.md) | 앱 실행은 리다이렉트 — 마켓 소유 실행 엔드포인트 경유 | Accepted | 2026-09-12 |

### 제안 — 승인 대기

| # | 제목 | 상태 | 일자 |
|---|---|---|---|
| [AXM-0007](0007-app-market-modular-monolith.md) | 앱마켓 아키텍처 스타일 — 모듈러 모놀리스 + 레지스트리/프로젝션 | Proposed | 2026-09-12 |
| [AXM-0008](0008-catalog-reconciliation.md) | 카탈로그 등록 모델 — 조정 루프 기반 | Proposed | 2026-09-12 |
| [AXM-0010](0010-no-backstage-framework.md) | Backstage를 프레임워크로 채택하지 않는다 | Proposed | 2026-09-12 |
| [AXM-0011](0011-vks-ingress-forward-auth.md) | Private Cloud 트랙의 신원 주입은 Ingress forward-auth로 | Proposed | 2026-09-12 |

## 작성 규칙

- 하나의 ADR은 **하나의 결정**만 다룬다
- 결정을 바꿀 때는 기존 문서를 수정하지 않고 **새 ADR을 쓰고 기존 것을 Superseded로 표시**한다
- 검토했으나 채택하지 않은 대안을 반드시 남긴다. **왜 안 골랐는지가 나중에 가장 필요한 정보다**
- 템플릿: [template.md](template.md)
