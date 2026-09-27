# 구성도 아이콘 출처

`ax-app-operating-devsecops` 구성도, 그리고 `ax-market_target 아키텍처`의 **4~8페이지(인프라 뷰 v0.2~v0.6)** 에서 사용하는 원본 아이콘이다.

> 이 다섯 페이지는 **AWS 자원에 draw.io 내장 `mxgraph.aws4` 스텐실**(공식 AWS Architecture Icons)을 쓰고, AWS 외 제품(GitLab · Harbor · Flux · Kyverno · Keycloak · Kubernetes · Databricks 계열)만 이 폴더의 자산을 내장한다. 재생성은 `python3 docs/diagrams/tools/build_target_aws_view.py`(v0.2) · `python3 docs/diagrams/tools/build_target_aws_v3.py`(v0.3) · `python3 docs/diagrams/tools/build_target_aws_v4.py`(v0.4) · `python3 docs/diagrams/tools/build_target_aws_v5.py`(v0.5) · `python3 docs/diagrams/tools/build_target_aws_v6.py`(v0.6).

> **`ax-market_infra`(앱마켓 인프라 v1.0)** 는 방식이 다르다. `mxgraph.aws4` 스텐실 대신 **AWS Architecture Icons 2026-07-31 패키지의 공식 SVG를 이 폴더에서 내장**한다(스텐실은 패키지보다 늦게 갱신된다). 계정 · VPC · 서브넷 경계만 draw.io AWS 그룹 도형을 쓴다. 2026-09-27에 `aws-fargate.svg` · `aws-cognito.svg` 등 공식 SVG를 추가했다. 재생성은 `python3 docs/diagrams/tools/build_market_infra.py`.

아래는 이 폴더 자산의 출처다. 다운로드 일자는 2026-09-12이며, 개별 다운로드 URL·패키지 내부 경로·SHA-256은 [sources.json](sources.json)에 기록했다.

| 대상 | 공식 출처 |
|---|---|
| EC2, Bedrock, S3, ALB/NLB, PrivateLink, TGW, Route53 Resolver, Direct Connect, VPN, 중립 서버·DB·앱 아이콘 | [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) — 2026-07-31 패키지 |
| GitLab | [GitLab Press Kit](https://about.gitlab.com/press/press-kit/) — 컬러 logomark |
| Kubernetes, Flux, Kyverno, Keycloak, Prometheus, Harbor | [CNCF Artwork](https://github.com/cncf/artwork) — 프로젝트별 컬러 아이콘 |
| Cosign | [Sigstore Community Artwork](https://github.com/sigstore/community/tree/main/artwork) — 프로젝트 README에 사용된 컬러 로고 |
| Grafana | [Grafana Trademark List](https://grafana.com/trademark-policy/trademark-list/) |
| Loki | [Grafana Loki](https://grafana.com/oss/loki/) — 공식 사이트 내 아이콘 |
| Databricks | [Databricks Brand Guidelines](https://brand.databricks.com/iconography) — 공식 사이트의 컬러 심볼 |
| Unity Catalog, Genie, Databricks SQL | [Databricks](https://www.databricks.com/) — 제품 아이콘 |

## 적용 방식

- 원본의 색상·비율을 유지한다. 원본 파일은 수정하지 않는다. GitLab은 큰 투명 여백만 표시 영역에서 줄이며 마크 전체와 주변 여백을 보존한다.
- Kubernetes 로고는 VKS의 Kubernetes 실행 기반을 나타낸다. VKS 자체의 공식 브랜드 로고로 간주하지 않는다.
- 관리형 DB·마켓 컴퓨트의 제품은 미정이므로 AWS의 **일반 DB·서버 아이콘**을 쓴다. RDS·Aurora·ECS 등의 선택을 의미하지 않는다.
- 자체 서비스인 AX App Market, 네트워크 관계, Agent App 등은 기존 중립 도형을 유지한다. 사내 업무 시스템도 특정 공급자의 제품으로 단정하지 않는다.
- 아이콘은 SVG와 draw.io 내부에 데이터로 내장된다. 배포 파일을 다른 위치로 옮겨도 외부 이미지 서버나 이 폴더에 의존하지 않는다. Coder는 내부 구현 상세이므로 이 구성도에는 표시하지 않는다.
- 브랜드와 상표의 권리는 각 소유자에게 있으며, 해당 공식 배포처의 사용 지침을 따른다.

## 재생성

저장소 루트에서 실행한다. 네트워크 접근은 필요 없다.

```sh
python3 docs/diagrams/tools/build_devsecops.py
rsvg-convert -o docs/diagrams/ax-app-operating-devsecops.png docs/diagrams/ax-app-operating-devsecops.svg
rsvg-convert -f pdf -o docs/diagrams/ax-app-operating-devsecops.pdf docs/diagrams/ax-app-operating-devsecops.svg
```
