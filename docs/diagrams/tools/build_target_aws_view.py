#!/usr/bin/env python3
"""`ax-market_target 아키텍처.drawio.xml`에 AWS 공식 아이콘 기반 인프라 뷰(4페이지)를 추가한다.

- AWS 자원은 draw.io 내장 `mxgraph.aws4` 스텐실(AWS Architecture Icons)을 쓴다.
- AWS 외 제품(GitLab · Harbor · Flux · Kyverno · Keycloak · Kubernetes · Databricks)은
  `assets/icons/`의 원본 자산을 data URI로 내장한다. 외부 이미지 링크에 의존하지 않는다.
- 앱마켓 컴퓨트와 관리형 DB는 제품이 미정이므로(`05` §5-2) AWS의 **범주 아이콘**을 쓴다.
  ECS·Aurora 등의 선택을 의미하지 않는다.

재생성: python3 docs/diagrams/tools/build_target_aws_view.py
"""
from pathlib import Path
import base64
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent
ICONS = DIAG / "assets" / "icons"
TARGET = DIAG / "ax-market_target 아키텍처.drawio.xml"

PAGE_ID = "infra-aws"
PAGE_NAME = "인프라 뷰 v0.2 · AWS 아이콘"
W, H = 3400, 1960

# ── 색 ─────────────────────────────────────────────────────────────────────
C_COMPUTE = "#ED7100"
C_NET = "#8C4FFF"
C_DB = "#C925D1"
C_STORAGE = "#7AA116"
C_ML = "#01A88D"
C_GENERAL = "#232F3D"

E_ENTER = "#1A66C9"   # A 사용자 진입
E_LEGACY = "#2E7D32"  # B 앱 → 사내 시스템
E_PULL = "#E07B39"    # C 조정 루프 (pull)
E_DEPLOY = "#6A3FBF"  # D 배포
E_REDIR = "#5F6B7A"   # E 실행 리다이렉트
E_AUTH = "#0E8A8A"    # F 인증

cells = None
origins = {}


# ── 스타일 ─────────────────────────────────────────────────────────────────
PTS = ("points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],"
       "[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],"
       "[1,0.5,0],[1,0.75,0]];")


def st_service(res_icon, fill):
    """서비스 레벨 아이콘 (resourceIcon 프레임). strokeColor=#ffffff 필수."""
    return ("sketch=0;" + PTS + "outlineConnect=0;fontColor=#232F3E;"
            f"fillColor={fill};strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;"
            "verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;"
            f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{res_icon};")


def st_resource(shape, fill):
    """자원 레벨 아이콘 (단독 도형). strokeColor=none 필수."""
    return ("sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;"
            f"fillColor={fill};strokeColor=none;dashed=0;verticalLabelPosition=bottom;"
            "verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;"
            f"shape=mxgraph.aws4.{shape};")


def st_group(gr_icon, stroke, font, dashed=0):
    return ("sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
            "fontSize=12;fontStyle=1;container=1;dropTarget=1;collapsible=0;pointerEvents=0;"
            f"recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.{gr_icon};"
            f"strokeColor={stroke};fillColor=none;verticalAlign=top;align=left;spacingLeft=30;"
            f"fontColor={font};dashed={dashed};")


def st_plain(stroke, font, dashed=1):
    return ("rounded=0;whiteSpace=wrap;html=1;container=1;dropTarget=1;collapsible=0;"
            f"pointerEvents=0;recursiveResize=0;fillColor=none;strokeColor={stroke};"
            f"dashed={dashed};verticalAlign=top;align=left;spacingLeft=10;fontSize=12;"
            f"fontStyle=1;fontColor={font};")


ST_NOTE = ("shape=note;whiteSpace=wrap;html=1;fontSize=10;align=left;verticalAlign=top;"
           "fillColor=#FFF7E0;strokeColor=#D6B656;size=14;spacingLeft=4;spacingTop=2;")
ST_BOX = ("rounded=1;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;"
          "strokeColor=#B0BEC5;arcSize=12;")


def st_edge(color, dashed=0, width=2):
    return (f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeWidth={width};strokeColor={color};dashed={dashed};endArrow=block;endFill=1;"
            f"fontSize=10;fontColor={color};labelBackgroundColor=#F5F5F5;")


# ── 셀 생성 ────────────────────────────────────────────────────────────────
def node(cid, value, x, y, w, h, style, parent="1"):
    ox, oy = origins.get(parent, (0, 0))
    c = E.SubElement(cells, "mxCell", id=cid, value=value, style=style,
                     vertex="1", parent=parent)
    E.SubElement(c, "mxGeometry", x=str(x - ox), y=str(y - oy),
                 width=str(w), height=str(h), **{"as": "geometry"})
    return cid


def group(cid, value, x, y, w, h, style, parent="1"):
    node(cid, value, x, y, w, h, style, parent)
    origins[cid] = (x, y)
    return cid


def brand(cid, value, name, x, y, size, parent="1"):
    raw = (ICONS / name).read_bytes()
    mime = "image/png" if name.endswith(".png") else "image/svg+xml"
    if name == "gitlab.svg":
        asset = E.fromstring(raw)
        asset.set("viewBox", "100 105 180 170")
        raw = E.tostring(asset, encoding="utf-8")
    data = base64.b64encode(raw).decode()
    style = ("shape=image;imageAspect=1;aspect=fixed;html=1;verticalLabelPosition=bottom;"
             "verticalAlign=top;align=center;fontSize=11;fontColor=#232F3E;"
             f"image=data:{mime},{data};")
    return node(cid, value, x, y, size, size, style, parent)


def edge(cid, src, tgt, color, label="", dashed=0, width=2,
         exit_=None, entry=None, points=None):
    style = st_edge(color, dashed, width)
    if exit_:
        style += f"exitX={exit_[0]};exitY={exit_[1]};exitDx=0;exitDy=0;"
    if entry:
        style += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    c = E.SubElement(cells, "mxCell", id=cid, value=label, style=style,
                     edge="1", parent="1", source=src, target=tgt)
    g = E.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
    if points:
        arr = E.SubElement(g, "Array", **{"as": "points"})
        for px, py in points:
            E.SubElement(arr, "mxPoint", x=str(px), y=str(py))
    return cid


# ── 페이지 구성 ────────────────────────────────────────────────────────────
def build(model_root):
    global cells
    cells = model_root
    E.SubElement(cells, "mxCell", id="0")
    E.SubElement(cells, "mxCell", id="1", parent="0")

    node("bg", "", 0, 0, W, H,
         "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=none;")

    node("title", (
        "<b style='font-size:19px'>AX App Market — 목표 인프라 뷰 v0.2 · AWS 공식 아이콘</b><br>"
        "2026-09-12 · <b>05</b> 물리 아키텍처 §1~§5, <b>03</b> 확정 전제 F1~F7 기준. "
        "1페이지(v0.1)와 같은 내용을 AWS Architecture Icons로 다시 그린 판이다.<br>"
        "<span style='color:#B7791F'>⚠ 표시와 점선 테두리는 미확정 · 검증 대기 항목이다. "
        "경로별 흐름은 2페이지 경로 뷰, 신뢰 경계는 3페이지 보안 뷰.</span>"),
        40, 24, 1320, 96,
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=12;spacing=6;")

    # ── 범례 ───────────────────────────────────────────────────────────────
    node("legend", (
        "<b>범례 — 선의 의미</b><br><br>"
        f"<font color='{E_ENTER}'><b>━━</b></font> <b>A 사용자 진입</b> — VDI → DX → 내부 ALB / "
        "front-end PrivateLink. <b>인터넷 구간 없음</b> (AXM-0003 · F5)<br>"
        f"<font color='{E_LEGACY}'><b>━━</b></font> <b>B 앱 → 사내 시스템</b> — NCC 사설EP → "
        "VPC 엔드포인트 서비스 → 내부 NLB → TGW → DX (AXM-0004 · 05 §3)<br>"
        f"<font color='{E_PULL}'><b>┅┅</b></font> <b>C 조정 루프</b> — <b>마켓이 조회한다.</b> "
        "런타임이 밀어 넣지 않는다 (AXM-0008)<br>"
        f"<font color='{E_DEPLOY}'><b>━━</b></font> <b>D 배포</b> — 승인 이후 파이프라인만. "
        "VKS는 pull GitOps, Databricks는 bundle deploy (02 §5)<br>"
        f"<font color='{E_REDIR}'><b>┅┅</b></font> <b>E 실행 302</b> — 마켓은 한 번 넘기고 "
        "<b>경로에서 빠진다</b> (AXM-0009)<br>"
        f"<font color='{E_AUTH}'><b>┅┅</b></font> <b>F 인증</b> — AD가 권한의 단일 소스 (03 §5-1)"),
        2800, 150, 560, 372,
        "rounded=1;whiteSpace=wrap;html=1;fontSize=10;align=left;verticalAlign=top;"
        "fillColor=#FFFFFF;strokeColor=#90A4AE;arcSize=6;spacing=8;")

    # ── 온프렘 ─────────────────────────────────────────────────────────────
    group("g_onp", "온프렘 · 사내망 (우리 통제)", 40, 130, 780, 1760,
          st_group("group_on_premise", "#5A6C86", "#5A6C86"))

    node("vdi", "임직원 VDI<br>사내망", 110, 230, 78, 78,
         st_resource("client", C_GENERAL), "g_onp")
    brand("idp", "AD → Keycloak<br>SSO · RBAC · 권한 단일 소스", "keycloak.svg", 135, 430, 68, "g_onp")
    brand("dns", "사내 DNS<br>조건부 포워딩", "generic-server.svg", 375, 430, 68, "g_onp")
    brand("gl", "GitLab + Runner<br>형상관리 · CI · 정책 강제", "gitlab.svg", 645, 430, 68, "g_onp")

    group("g_vks", "Private Cloud (VKS) · 운영 런타임 ①", 75, 590, 710, 450,
          st_plain("#5A6C86", "#5A6C86"), "g_onp")
    brand("harbor", "Harbor<br>이미지 + Cosign 서명", "harbor.svg", 135, 670, 60, "g_vks")
    brand("flux", "Flux + agentk<br>pull 기반 GitOps", "flux.svg", 405, 670, 60, "g_vks")
    brand("kyverno", "Kyverno admission<br>미서명 · 변조 이미지 차단", "kyverno.svg", 675, 670, 60, "g_vks")
    brand("k8s", "Kubernetes 워크로드", "kubernetes.svg", 135, 880, 60, "g_vks")
    brand("iap", "Ingress forward-auth<br>신원 헤더 주입 (AXM-0011)", "generic-shield.svg", 405, 880, 60, "g_vks")
    brand("pcapp", "VKS Web App 실행", "generic-app.svg", 675, 880, 60, "g_vks")

    group("g_sys", "사내 업무 시스템", 75, 1100, 710, 220,
          st_plain("#5A6C86", "#5A6C86"), "g_onp")
    node("sys1", "MES · SRM · ERP", 180, 1170, 78, 78,
         st_resource("traditional_server", C_GENERAL), "g_sys")
    node("sys2", "Wehub · CRM", 520, 1170, 78, 78,
         st_resource("traditional_server", C_GENERAL), "g_sys")

    node("n_onp", (
        "<b>⚠ 온프렘 쪽 미확정</b><br>"
        "· <b>A3 GitLab Ultimate tier</b> — Security Policy Project로 스캔을 강제하는 근거. "
        "미확보 시 개발자가 <code>include</code>를 지울 수 있어 통제 등급이 내려간다 (07 §5-4)<br>"
        "· <b>A4 WIF 성립</b> — 컨트롤 플레인의 JWKS 조회는 <b>DX를 타지 않는다.</b> "
        "F4로 해결되지 않는다 (01 · 07 §5-5)<br>"
        "· <b>Cosign 서명 키 관리</b> 방식 미정 (KMS / keyless) — 07 §6-3"),
        75, 1380, 710, 190, ST_NOTE, "g_onp")
    node("n_onp2", (
        "<b>Q1의 실질 판정 기준은 “보안 승인 가능 여부”다.</b> 사내 시스템을 내부 NLB 뒤에 "
        "노출하는 것에 대한 승인이 나야 사내 연동 앱을 Databricks에 둘 수 있다. "
        "물리적 불가는 F3·F4로 이미 해소되었다 (03 §3 · 07 §6-1)."),
        75, 1620, 710, 140, ST_NOTE, "g_onp")

    # ── 연결 회랑 ───────────────────────────────────────────────────────────
    node("dx", "Direct Connect<br>+ VPN", 876, 240, 78, 78,
         st_service("direct_connect", C_NET))
    node("n_dx", (
        "<b>기구축 · 라우팅 완료</b> (F4)<br>VPN + DX + TGW<br><br>"
        "<b>사용자 진입에<br>인터넷 구간이 없다</b> (F5)"),
        850, 600, 158, 236, ST_NOTE)

    # ── AWS ────────────────────────────────────────────────────────────────
    group("g_aws", "AWS 클라우드 · ap-northeast-2 (서울) — 우리 계정", 1010, 130, 1730, 1760,
          st_group("group_aws_cloud_alt", "#232F3E", "#232F3E"))

    # 공유 네트워크 계정
    group("g_net", "공유 네트워크 계정 ⚠ 존재 여부 · TGW 소유 방식 확인 필요", 1040, 190, 1670, 320,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    node("tgw", "Transit Gateway", 1100, 280, 78, 78,
         st_service("transit_gateway", C_NET), "g_net")
    node("nlb", "내부 NLB<br>NCC 사설EP 종단", 1420, 280, 78, 78,
         st_resource("network_load_balancer", C_NET), "g_net")
    node("vpces", "VPC 엔드포인트 서비스<br>PrivateLink 수신", 1740, 280, 78, 78,
         st_resource("endpoints", C_NET), "g_net")
    node("r53", "Route53 Resolver<br>inbound / outbound", 2060, 280, 78, 78,
         st_resource("route_53_resolver", C_NET), "g_net")
    node("n_net", (
        "<b>⚠ 내부 NLB를 어느 계정에 둘 것인가</b> — 모든 Databricks App의 사내 접근이 "
        "통과하는 단일 지점. 기준은 “누가 노출을 운영·감사하는가” (05 §1-2)<br>"
        "<b>⚠ NLB IP 타깃 → 온프렘 도달 검증</b> — Databricks 문서 범위 밖 (05 §3-3)<br>"
        "<b>DNS</b> databricksapps.com 조건부 포워딩 · DNS chasing 미지원 (05 §4)"),
        2340, 250, 340, 150, ST_NOTE, "g_net")

    # 앱마켓 운영 계정
    group("g_mkt", "앱마켓 운영 계정 (신규) ⚠ CIDR 확보 리드타임 최장", 1040, 560, 1020, 840,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    group("g_vpc", "전용 VPC · private subnet 전용 (IGW 없음)", 1070, 640, 960, 730,
          st_group("group_vpc", "#8C4FFF", "#8C4FFF"), "g_mkt")
    node("alb", "내부 ALB · 2 AZ<br>ACM + 사내 도메인", 1120, 720, 78, 78,
         st_resource("application_load_balancer", C_NET), "g_vpc")
    node("mep", "VPC 인터페이스 EP<br>Databricks REST", 1420, 720, 78, 78,
         st_resource("endpoints", C_NET), "g_vpc")

    group("g_aza", "Private Subnet · AZ-a", 1100, 870, 410, 200,
          st_group("group_private_subnet", "#147EBA", "#147EBA"), "g_vpc")
    node("web_a", "앱마켓 web<br>카탈로그 · /launch", 1140, 935, 65, 65,
         st_service("compute", C_COMPUTE), "g_aza")
    node("wrk_a", "조정 워커<br>동일 이미지", 1350, 935, 65, 65,
         st_service("compute", C_COMPUTE), "g_aza")

    group("g_azc", "Private Subnet · AZ-c", 1560, 870, 410, 200,
          st_group("group_private_subnet", "#147EBA", "#147EBA"), "g_vpc")
    node("web_c", "앱마켓 web<br>카탈로그 · /launch", 1600, 935, 65, 65,
         st_service("compute", C_COMPUTE), "g_azc")
    node("wrk_c", "조정 워커<br>분리는 선택 (06 §5-2)", 1810, 935, 65, 65,
         st_service("compute", C_COMPUTE), "g_azc")

    node("db", "관리형 DB · Multi-AZ<br>레지스트리 = 진실의 원천", 1120, 1140, 78, 78,
         st_service("database", C_DB), "g_vpc")
    node("s3", "S3 · 증적 저장<br>버전관리 · 삭제 방지", 1420, 1140, 78, 78,
         st_service("s3", C_STORAGE), "g_vpc")
    node("n_mkt", (
        "<b>⚠ 컴퓨트·DB 제품 미정</b> (05 §5-2, §8-2)<br>"
        "ECS Fargate / EKS / EC2, RDS / Aurora 중 미결이므로 "
        "<b>AWS 범주 아이콘</b>을 쓴다. 특정 제품 선택을 뜻하지 않는다."),
        1700, 1130, 310, 120, ST_NOTE, "g_vpc")

    # Playground 계정
    group("g_pg", "Playground 계정 259537089696 (PoC 가동 중)", 1040, 1470, 1670, 380,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    node("coder", "Coder Server (EC2)<br>컨트롤 플레인", 1090, 1540, 78, 78,
         st_service("ec2", C_COMPUTE), "g_pg")
    node("wsec2", "워크스페이스 EC2<br>VS Code · Claude Code", 1370, 1540, 78, 78,
         st_service("ec2", C_COMPUTE), "g_pg")
    node("bed", "Amazon Bedrock<br>코딩 어시스턴트 LLM", 1650, 1540, 78, 78,
         st_service("bedrock", C_ML), "g_pg")
    node("bedep", "Bedrock VPC EP<br>⚠ 현재 NAT 경유", 1930, 1540, 78, 78,
         st_resource("endpoints", C_NET), "g_pg")
    node("n_pg", (
        "<b>PoC 구성을 그대로 운영 전환할 수 없다</b> (05 §7) — /22 공용 VPC · IGW+EIP 퍼블릭 진입 · "
        "SG IP allowlist · 자체서명 TLS · 단일 EC2 · built-in PostgreSQL. "
        "운영은 전용 VPC · DX 사설 진입 · ACM · Multi-AZ · 관리형 DB로 교체한다. "
        "<b>Agent App이 실행 시 호출할 LLM</b>(Bedrock인가 Databricks 모델서빙인가)은 별도 결정 (05 §8-2)."),
        2230, 1520, 460, 310, ST_NOTE, "g_pg")

    # Databricks 전용 계정
    group("g_dbx", "Databricks 전용 계정 (기존) · Enterprise tier — F2 · F3", 2110, 560, 600, 870,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    brand("ws", "Databricks 워크스페이스<br>계정 SSO + SCIM ← AD", "databricks.png", 2160, 655, 68, "g_dbx")
    node("fep", "front-end<br>PrivateLink EP", 2460, 650, 78, 78,
         st_service("vpc_privatelink", C_NET), "g_dbx")
    brand("uc", "Unity Catalog<br>계정 레벨 · 행·열 보안", "unity-catalog.svg", 2160, 900, 68, "g_dbx")
    brand("wh", "공용 SQL Warehouse<br>앱 전용 금지 (AXM-0005)", "databricks-sql.svg", 2460, 900, 68, "g_dbx")
    node("n_dbx", (
        "<b>워크스페이스당 앱 100개 — 조정 불가(fixed).</b> 한도 초과 시 워크스페이스 증설 "
        "검토, 불가하면 Private Cloud (03 §3 Q4).<br><br>"
        "<b>Enterprise tier</b>라서 NCC 사설 엔드포인트와 네트워크 정책을 쓸 수 있다. "
        "Q1 재정의가 여기에 걸려 있다 (F3 · AXM-0004)."),
        2150, 1030, 520, 170, ST_NOTE, "g_dbx")
    node("n_dbx2", (
        "<b>여기는 “워크스페이스가 귀속된 우리 계정”이다.</b> Apps·에이전트의 "
        "<b>서버리스 컴퓨트는 이 계정에 없다</b> — 오른쪽 Databricks 소유 계정에서 실행된다 "
        "(05 §1-1 · 07 §4-1)."),
        2150, 1225, 520, 170, ST_NOTE, "g_dbx")

    # ── Databricks 소유 계정 ───────────────────────────────────────────────
    group("g_srv", "Databricks 소유 계정 — 우리 통제 밖", 2800, 560, 560, 1290,
          st_group("group_account", "#D6336C", "#D6336C", dashed=1))
    brand("apps", "Databricks Apps<br>서버리스 · OBO", "databricks.png", 2860, 655, 68, "g_srv")
    brand("agsv", "Agent 서빙 EP<br>UC 등록 모델", "generic-app.svg", 3140, 655, 68, "g_srv")
    node("ncc", "<b>NCC 사설 엔드포인트 규칙</b><br>Enterprise tier 필요 · 한도 있음",
         2850, 950, 300, 80, ST_BOX, "g_srv")
    brand("genie", "Genie space<br>MCP URL", "genie.svg", 2860, 1120, 68, "g_srv")
    brand("ms", "Model Serving<br>엔드포인트", "generic-server.svg", 3140, 1120, 68, "g_srv")
    node("n_srv", (
        "<b>신뢰 경계가 여기서 끊긴다.</b> 서버리스 컴퓨트는 Databricks 계정에서 돈다. "
        "우리가 거는 통제는 <b>UC 권한 · OBO · 네트워크 정책 · NCC 규칙</b>이며, "
        "호스트 자체는 우리 것이 아니다 (07 §4-1).<br><br>"
        "<b>Apps에는 auto-stop이 없다.</b> 실행 중 상시 과금이므로 유휴 정지 정책이 "
        "3층 기본값의 전제다 (AXM-0005 · 04 §5)."),
        2840, 1300, 470, 230, ST_NOTE, "g_srv")
    node("n_srv2", (
        "<b>에이전트는 계정 레벨 UC 자원이다.</b> 워크스페이스 앱 100개 한도와 무관하고, "
        "권한 집행·감사는 UC에 위임한다 (AXM-0012)."),
        2840, 1590, 470, 130, ST_NOTE, "g_srv")

    # ── 선 ─────────────────────────────────────────────────────────────────
    # A 사용자 진입
    edge("a1", "vdi", "dx", E_ENTER, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a2", "dx", "tgw", E_ENTER, "DX / VPN", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a3", "tgw", "alb", E_ENTER, "앱마켓", exit_=(0.25, 1), entry=(0.5, 0),
         points=[(1119, 640)])
    edge("a4", "tgw", "fep", E_ENTER, "Databricks 워크스페이스 · Apps",
         exit_=(0.75, 1), entry=(0.5, 0), points=[(1158, 530), (2499, 530)])
    edge("a5", "fep", "apps", E_ENTER, "PrivateLink", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a6", "vdi", "iap", E_ENTER, "VKS 앱 직통",
         exit_=(1, 0.75), entry=(0.5, 0), points=[(330, 288), (330, 845), (435, 845)])

    # B 앱 → 사내 시스템
    edge("b1", "apps", "ncc", E_LEGACY, "egress", exit_=(0.2, 1), entry=(0.15, 0))
    edge("b2", "ncc", "vpces", E_LEGACY, "PrivateLink", exit_=(0, 0.5), entry=(0.5, 1),
         points=[(2770, 990), (2770, 440), (1779, 440)])
    edge("b3", "vpces", "nlb", E_LEGACY, "", exit_=(0, 0.5), entry=(1, 0.5))
    edge("b4", "nlb", "dx", E_LEGACY, "IP 타깃 ⚠ 검증", dashed=1,
         exit_=(0.5, 1), entry=(0.75, 1), points=[(1459, 470), (934, 470)])
    edge("b5", "dx", "sys2", E_LEGACY, "특정 포트만", exit_=(0, 0.75), entry=(1, 0.5),
         points=[(835, 298), (835, 1209)])

    # C 조정 루프 (pull)
    edge("c1", "wrk_a", "mep", E_PULL, "", dashed=1, exit_=(0.5, 0), entry=(0.5, 1))
    edge("c2", "mep", "fep", E_PULL, "Databricks REST · 시스템 테이블", dashed=1,
         exit_=(1, 0.5), entry=(0.5, 1), points=[(1560, 759), (1560, 810), (2499, 810)])
    edge("c3", "wrk_a", "gl", E_PULL, "조회 pull — GitLab · VKS API", dashed=1,
         exit_=(0.5, 1), entry=(0.5, 0),
         points=[(1382, 1100), (1025, 1100), (1025, 400), (679, 400)])

    # D 배포
    edge("d1", "gl", "harbor", E_DEPLOY, "이미지 push", exit_=(0.5, 1), entry=(0.5, 0),
         points=[(679, 620), (165, 620)])
    edge("d2", "flux", "harbor", E_DEPLOY, "pull", exit_=(0, 0.5), entry=(1, 0.5))
    edge("d3", "flux", "k8s", E_DEPLOY, "동기화", exit_=(0.5, 1), entry=(0.5, 0),
         points=[(435, 800), (165, 800)])
    edge("d4", "kyverno", "pcapp", E_DEPLOY, "admission", exit_=(0.5, 1), entry=(0.5, 0))
    edge("d5", "iap", "pcapp", E_DEPLOY, "신원 주입", exit_=(1, 0.5), entry=(0, 0.5))
    edge("d6", "gl", "ws", E_DEPLOY, "bundle deploy + run · WIF 단기 토큰",
         exit_=(1, 0.5), entry=(0.5, 0), points=[(985, 464), (985, 548), (2194, 548)])

    # E 실행 302
    edge("e1", "web_a", "apps", E_REDIR, "302 후 사용자 직통", dashed=1,
         exit_=(0.5, 0), entry=(0.8, 1), points=[(1172, 860), (2914, 860)])
    edge("e2", "web_a", "pcapp", E_REDIR, "302 후 사용자 직통", dashed=1,
         exit_=(0, 0.5), entry=(1, 0.5), points=[(1000, 967), (1000, 910)])

    # F 인증
    edge("f1", "idp", "vdi", E_AUTH, "SSO", dashed=1, exit_=(0.5, 0), entry=(0.5, 1))


def main():
    tree = E.parse(TARGET)
    root = tree.getroot()
    for d in list(root.findall("diagram")):
        if d.get("id") == PAGE_ID:
            root.remove(d)

    page = E.SubElement(root, "diagram", id=PAGE_ID, name=PAGE_NAME)
    model = E.SubElement(page, "mxGraphModel", dx="2600", dy="1500", grid="1",
                         gridSize="10", guides="1", tooltips="1", connect="1",
                         arrows="1", fold="1", page="1", pageScale="1",
                         pageWidth=str(W), pageHeight=str(H), math="0", shadow="0")
    build(E.SubElement(model, "root"))

    root.set("pages", str(len(root.findall("diagram"))))
    E.indent(tree, space="  ")
    tree.write(TARGET, encoding="UTF-8", xml_declaration=True)
    print(f"wrote page '{PAGE_NAME}' → {TARGET}")


if __name__ == "__main__":
    main()
