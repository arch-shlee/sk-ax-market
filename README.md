# sk-ax-market

AX App Market 플랫폼 설계.

AX App은 AX Playground에서 개발되어 Git 기반의 검증·승인 절차를 거친 뒤 승인된 Runtime(**Databricks Apps** 또는 **Private Cloud**)에 배포되고, 임직원이 **AX App Market**을 통해 검색하고 권한에 따라 실행하는 업무용 웹서비스다. 일반 Web App뿐 아니라 Databricks Agent와 연계한 대화형·자동화 App을 포함한다.

## 문서

**→ [docs/README.md](docs/README.md)** 에서 시작한다. 읽는 순서, 문서별 역할, 확정된 전제, 막혀 있는 항목이 정리되어 있다.

```
docs/
├── design/      설계 문서 01~06
├── adr/         아키텍처 결정 기록 (AXM-)
├── reference/   기술 사실관계 · 자료조사
├── diagrams/    draw.io 도면
└── source/      원 기획서
```

## 현재 상태

설계 단계. 구현 코드 없음.

- 확정 전제 7건, ADR 16건(확정 11 · 제안 5)
- 최우선 미결: 망분리·데이터 등급, NLB 온프렘 도달 검증, 사내 시스템 노출 보안 승인
