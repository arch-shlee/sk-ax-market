#!/usr/bin/env python3
"""`ax-market_target 아키텍처.drawio.xml`에 인프라 뷰 v0.5(7페이지)를 추가한다.

v0.4의 배치·경로를 그대로 두고 **글자와 강조 체계만** 다시 잡은 판이다.

글자 — v0.4는 캔버스 2960px에 11px 글자를 써서 상대 크기가 참고 도면의 절반이었다.
  · 계정 · 영역 이름 20px 굵게 → 논리 묶음 칩 15px 굵게 → 구성요소 15px → 선 13px
  · 긴 라벨은 두 줄로 끊어 가로 번짐을 막는다

강조 — 이 도면을 보는 사람이 가장 먼저 찾아야 하는 셋을 시각적으로 분리한다.
  1. **무엇을 새로 만드는가** — 앱마켓 운영 계정. 굵은 테두리 + 옅은 배경
  2. **통제 경계가 어디서 끊기는가** — Databricks 소유 계정. 점선 + 옅은 배경
  3. **어디에 결정이 필요한가** — ⚠ 표시와 계정별 상태 배지(신규 구축 / 기존 / 확인 필요 …)

재생성: python3 docs/diagrams/tools/build_target_aws_v5.py
"""
from pathlib import Path
import base64
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent
ICONS = DIAG / "assets" / "icons"
TARGET = DIAG / "ax-market_target 아키텍처.drawio.xml"

PAGE_ID = "infra-aws-v5"
PAGE_NAME = "인프라 뷰 v0.5 · AWS 아이콘"
W, H = 2960, 1800

C_COMPUTE = "#ED7100"
C_NET = "#8C4FFF"
C_DB = "#C925D1"
C_STORAGE = "#7AA116"
C_ML = "#01A88D"
C_GENERAL = "#232F3D"

INK = "#37474F"        # 구조선 · 얇은 경계
E_USER = "#1A66C9"     # 사용자 진입 · 앱 실행
E_LEGACY = "#2E7D32"   # 앱 → 사내 시스템
E_SUPPLY = "#C2185B"   # 소스 · 배포
ACCENT = "#C2185B"     # 신규 구축 — 이 프로젝트가 만드는 것
WARN = "#B7791F"       # 미확정 · 통제 밖
NEUTRAL = "#78909C"    # 기구축 · 기존

cells = None
origins = {}

PTS = ("points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],"
       "[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],"
       "[1,0.5,0],[1,0.75,0]];")


def st_service(res_icon, fill):
    return ("sketch=0;" + PTS + "outlineConnect=0;fontColor=#232F3E;"
            f"fillColor={fill};strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;"
            "verticalAlign=top;align=center;html=1;fontSize=15;fontStyle=0;aspect=fixed;"
            f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{res_icon};")


def st_resource(shape, fill):
    return ("sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;"
            f"fillColor={fill};strokeColor=none;dashed=0;verticalLabelPosition=bottom;"
            "verticalAlign=top;align=center;html=1;fontSize=15;fontStyle=0;"
            f"shape=mxgraph.aws4.{shape};")


def st_group(gr_icon, stroke, font, dashed=0, fill="none", sw=1.5):
    """계정 · 영역 경계. 강조 대상만 굵은 테두리와 옅은 배경을 받는다."""
    return ("sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
            "fontSize=20;fontStyle=1;container=1;dropTarget=1;collapsible=0;pointerEvents=0;"
            f"recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.{gr_icon};"
            f"strokeColor={stroke};fillColor={fill};strokeWidth={sw};verticalAlign=top;"
            f"align=left;spacingLeft=38;fontColor={font};dashed={dashed};")


ST_PLAINBOX = ("rounded=0;html=1;fillColor=none;strokeColor=" + INK + ";strokeWidth=1;"
               "container=1;dropTarget=1;collapsible=0;pointerEvents=0;recursiveResize=0;")
ST_CHIP = ("rounded=0;html=1;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor=" + INK + ";"
           "strokeWidth=1;align=center;verticalAlign=middle;fontSize=15;fontStyle=1;"
           "fontColor=" + INK + ";")
ST_BOX = ("rounded=0;whiteSpace=wrap;html=1;fontSize=15;fontStyle=1;fillColor=#FFFFFF;"
          f"strokeColor={INK};fontColor={INK};")
ST_TEXT = "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=13;spacing=2;"


def st_edge(color=INK, dashed=0, width=1.5):
    return ("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeWidth={width};strokeColor={color};dashed={dashed};endArrow=block;endFill=1;"
            f"endSize=7;fontSize=13;fontColor={color};labelBackgroundColor=#FFFFFF;")


GROW = 8  # 참고 도면 수준으로 아이콘 비중을 올린다. 중심 좌표는 보존한다.


def node(cid, value, x, y, w, h, style, parent="1"):
    if "shape=image;" in style or ("mxgraph.aws4." in style and "grIcon=" not in style):
        x, y, w, h = x - GROW / 2, y - GROW / 2, w + GROW, h + GROW
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


def boxed(cid, label, x, y, w, h, chip_w, parent="1"):
    """얇은 사각형 + 상단 중앙 라벨 칩. 참고 도면의 논리 묶음 표기."""
    node(cid, "", x, y, w, h, ST_PLAINBOX, parent)
    origins[cid] = (x, y)
    node(cid + "_t", label, x + (w - chip_w) / 2, y - 15, chip_w, 30, ST_CHIP, "1")
    return cid


def badge(cid, text, x, y, w, color=NEUTRAL):
    """계정 상태 배지. 무엇을 새로 만들고 무엇이 이미 있는지 한눈에 가른다."""
    return node(cid, text, x, y, w, 28,
                f"rounded=1;arcSize=45;html=1;whiteSpace=wrap;fillColor={color};"
                "strokeColor=none;fontColor=#FFFFFF;fontSize=13;fontStyle=1;"
                "align=center;verticalAlign=middle;")


def brand(cid, value, name, x, y, size, parent="1"):
    raw = (ICONS / name).read_bytes()
    mime = "image/png" if name.endswith(".png") else "image/svg+xml"
    if name == "gitlab.svg":
        asset = E.fromstring(raw)
        asset.set("viewBox", "100 105 180 170")
        raw = E.tostring(asset, encoding="utf-8")
    data = base64.b64encode(raw).decode()
    style = ("shape=image;imageAspect=1;aspect=fixed;html=1;verticalLabelPosition=bottom;"
             "verticalAlign=top;align=center;fontSize=15;fontColor=#232F3E;"
             f"image=data:{mime},{data};")
    return node(cid, value, x, y, size, size, style, parent)


def edge(cid, src, tgt, color=INK, label="", dashed=0, width=1.5,
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


WARN_G = "<font color='#B7791F'>⚠</font>"


def build(model_root):
    global cells
    cells = model_root
    E.SubElement(cells, "mxCell", id="0")
    E.SubElement(cells, "mxCell", id="1", parent="0")

    node("bg", "", 0, 0, W, H,
         "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=none;")
    node("title", "AX App Market · 목표 인프라 v0.5", 40, 30, 760, 40,
         "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=26;"
         "fontStyle=1;fontColor=#182C46;spacing=0;")
    node("subtitle", "2026-09-12 · 05 물리 아키텍처 §1~§5 · 03 확정 전제 F1~F7",
         40, 74, 760, 22,
         "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=13;"
         "fontColor=#64748B;spacing=0;")
    node("awslabel", "AWS · ap-northeast-2 (서울)", 840, 78, 460, 28,
         "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=17;"
         "fontStyle=1;fontColor=#232F3E;spacing=0;")
    node("key", (
        f"<b>선</b>&nbsp;&nbsp; <font color='{E_USER}'><b>———</b></font> 사용자 진입 · 앱 실행"
        f"&nbsp;&nbsp; <font color='{E_LEGACY}'><b>———</b></font> 앱 → 사내 시스템"
        f"&nbsp;&nbsp; <font color='{E_SUPPLY}'><b>———</b></font> 소스 · 배포"
        f"&nbsp;&nbsp; <font color='{INK}'><b>┄┄┄</b></font> 조정 루프 · 인증<br>"
        f"<b>강조</b>&nbsp;&nbsp; <font color='{ACCENT}'><b>굵은 테두리</b></font> = 신규 구축 대상"
        f"&nbsp;&nbsp; <font color='{WARN}'><b>점선 테두리</b></font> = 우리 통제 밖"
        f"&nbsp;&nbsp; {WARN_G} = 미확정 · 결정 필요<br>"
        "<b>302</b>&nbsp;&nbsp; 실행 리다이렉트. 이후 마켓은 경로에서 빠진다"),
        40, 1385, 770, 96,
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=13;"
        "fontColor=#37474F;spacing=2;")

    # ── 온프렘 ─────────────────────────────────────────────────────────────
    group("g_onp", "온프렘 · 사내망", 40, 120, 660, 1210,
          st_group("group_on_premise", "#5A6C86", "#5A6C86"))
    node("vdi", "임직원 VDI", 90, 200, 78, 78,
         st_resource("client", C_GENERAL), "g_onp")
    brand("idp", "AD → Keycloak", "keycloak.svg", 90, 400, 70, "g_onp")
    brand("dns", "사내 DNS", "generic-server.svg", 310, 400, 70, "g_onp")
    brand("gl", "GitLab + Runner", "gitlab.svg", 530, 400, 70, "g_onp")

    boxed("b_vks", "Private Cloud (VKS)", 70, 560, 600, 420, 190, "g_onp")
    brand("harbor", "Harbor", "harbor.svg", 120, 630, 70, "b_vks")
    brand("flux", "Flux + agentk", "flux.svg", 330, 630, 70, "b_vks")
    brand("kyverno", "Kyverno", "kyverno.svg", 540, 630, 70, "b_vks")
    brand("k8s", "Kubernetes", "kubernetes.svg", 120, 830, 70, "b_vks")
    brand("iap", "Ingress<br>forward-auth", "generic-shield.svg", 330, 830, 70, "b_vks")
    brand("pcapp", "VKS Web App", "generic-app.svg", 540, 830, 70, "b_vks")

    boxed("b_sys", "사내 업무 시스템", 70, 1060, 600, 200, 155, "g_onp")
    node("sys1", "MES · SRM · ERP", 160, 1110, 78, 78,
         st_resource("traditional_server", C_GENERAL), "b_sys")
    node("sys2", "Wehub · CRM", 420, 1110, 78, 78,
         st_resource("traditional_server", C_GENERAL), "b_sys")

    node("dx", "Direct Connect<br>+ VPN", 736, 205, 78, 78,
         st_service("direct_connect", C_NET))

    # ── 계정 ───────────────────────────────────────────────────────────────
    group("g_net", "공유 네트워크 계정", 840, 120, 1560, 240,
          st_group("group_account", "#CD2264", "#CD2264"))
    node("tgw", "Transit Gateway", 900, 170, 78, 78,
         st_service("transit_gateway", C_NET), "g_net")
    node("nlb", "내부 NLB", 1250, 170, 78, 78,
         st_resource("network_load_balancer", C_NET), "g_net")
    node("vpces", "VPC 엔드포인트<br>서비스", 1600, 170, 78, 78,
         st_resource("endpoints", C_NET), "g_net")
    node("r53", "Route53 Resolver", 1950, 170, 78, 78,
         st_resource("route_53_resolver", C_NET), "g_net")

    group("g_mkt", "앱마켓 운영 계정", 840, 410, 900, 620,
          st_group("group_account", ACCENT, ACCENT, fill="#FFF5F8", sw=3))
    boxed("b_vpc", "전용 VPC " + WARN_G, 870, 480, 840, 520, 150, "g_mkt")
    node("alb", "내부 ALB", 915, 540, 78, 78,
         st_resource("application_load_balancer", C_NET), "b_vpc")
    node("db", "관리형 DB " + WARN_G, 1140, 540, 78, 78,
         st_service("database", C_DB), "b_vpc")
    node("s3", "S3 · 증적", 1365, 540, 78, 78,
         st_service("s3", C_STORAGE), "b_vpc")
    node("mep", "VPC 인터페이스<br>EP", 1590, 540, 78, 78,
         st_resource("endpoints", C_NET), "b_vpc")
    boxed("b_aza", "Private Subnet · AZ-a", 900, 700, 380, 200, 195, "b_vpc")
    node("web_a", "앱마켓 web", 935, 750, 70, 70,
         st_service("compute", C_COMPUTE), "b_aza")
    node("wrk_a", "조정 워커", 1145, 750, 70, 70,
         st_service("compute", C_COMPUTE), "b_aza")
    boxed("b_azc", "Private Subnet · AZ-c", 1320, 700, 380, 200, 195, "b_vpc")
    node("web_c", "앱마켓 web", 1355, 750, 70, 70,
         st_service("compute", C_COMPUTE), "b_azc")
    node("wrk_c", "조정 워커", 1565, 750, 70, 70,
         st_service("compute", C_COMPUTE), "b_azc")

    group("g_dbx", "Databricks 전용 계정", 1790, 410, 610, 620,
          st_group("group_account", "#CD2264", "#CD2264"))
    node("fep", "front-end<br>PrivateLink EP", 1845, 480, 78, 78,
         st_service("vpc_privatelink", C_NET), "g_dbx")
    brand("ws", "Databricks<br>워크스페이스", "databricks.png", 1845, 700, 70, "g_dbx")
    brand("uc", "Unity Catalog", "unity-catalog.svg", 2050, 700, 70, "g_dbx")
    brand("wh", "공용<br>SQL Warehouse", "databricks-sql.svg", 2255, 700, 70, "g_dbx")

    group("g_srv", "Databricks 소유 계정", 2450, 410, 470, 620,
          st_group("group_account", WARN, WARN, dashed=1, fill="#FFFBF0", sw=2))
    brand("apps", "Databricks Apps", "databricks.png", 2495, 480, 70, "g_srv")
    brand("agsv", "Agent 서빙 EP", "generic-app.svg", 2705, 480, 70, "g_srv")
    node("ncc", "NCC 사설 엔드포인트", 2485, 690, 350, 60, ST_BOX, "g_srv")
    brand("genie", "Genie space", "genie.svg", 2495, 810, 70, "g_srv")
    brand("ms", "Model Serving", "generic-server.svg", 2705, 810, 70, "g_srv")

    group("g_pg", "AX Playground 계정", 840, 1080, 1560, 640,
          st_group("group_account", "#CD2264", "#CD2264"))
    boxed("b_pgvpc", "Playground VPC " + WARN_G, 870, 1150, 1360, 540, 180, "g_pg")
    boxed("b_pub", "Public Subnet", 900, 1210, 420, 180, 140, "b_pgvpc")
    node("nat", "NAT Gateway", 935, 1250, 70, 70,
         st_resource("nat_gateway", C_NET), "b_pub")
    node("igw", "Internet Gateway", 1145, 1250, 70, 70,
         st_resource("internet_gateway", C_NET), "b_pub")
    boxed("b_ep", "VPC 엔드포인트 · 연결", 1360, 1210, 640, 180, 195, "b_pgvpc")
    node("s3ep", "S3 Gateway EP", 1400, 1250, 70, 70,
         st_resource("endpoints", C_NET), "b_ep")
    node("tgwatt", "TGW Attachment", 1600, 1250, 70, 70,
         st_resource("transit_gateway_attachment", C_NET), "b_ep")
    node("bedep", "Bedrock<br>인터페이스 EP", 1800, 1250, 70, 70,
         st_resource("endpoints", C_NET), "b_ep")
    boxed("b_pria", "Private Subnet · AZ-a", 900, 1430, 620, 210, 195, "b_pgvpc")
    node("ebs", "영속 EBS", 940, 1470, 70, 70,
         st_service("elastic_block_store", C_STORAGE), "b_pria")
    node("coder", "Coder Server<br>(EC2)", 1140, 1470, 70, 70,
         st_service("ec2", C_COMPUTE), "b_pria")
    node("ws1", "워크스페이스 EC2", 1340, 1470, 70, 70,
         st_service("ec2", C_COMPUTE), "b_pria")
    boxed("b_pric", "Private Subnet · AZ-c", 1560, 1430, 620, 210, 195, "b_pgvpc")
    node("ws2", "워크스페이스 EC2", 1600, 1470, 70, 70,
         st_service("ec2", C_COMPUTE), "b_pric")
    node("ws3", "워크스페이스 EC2", 1800, 1470, 70, 70,
         st_service("ec2", C_COMPUTE), "b_pric")
    node("resv", "예비 (HA)", 2000, 1470, 70, 70,
         st_service("ec2", C_COMPUTE), "b_pric")
    node("bedrock", "Amazon Bedrock", 2270, 1470, 78, 78,
         st_service("bedrock", C_ML), "g_pg")

    # ── 상태 배지 — 무엇을 만들고 무엇이 이미 있는가 ───────────────────────
    badge("bg_onp", "기구축", 252, 130, 74)
    badge("bg_net", "확인 필요", 1064, 130, 94, WARN)
    badge("bg_mkt", "신규 구축", 1052, 420, 94, ACCENT)
    badge("bg_dbx", "기존", 2044, 420, 64)
    badge("bg_srv", "통제 밖", 2702, 420, 84, WARN)
    badge("bg_pg", "PoC 가동", 1078, 1090, 94)

    # ── 사용자 진입 · 앱 실행 ──────────────────────────────────────────────
    edge("a1", "vdi", "dx", E_USER, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a2", "dx", "tgw", E_USER, "DX", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a3", "tgw", "alb", E_USER, "", exit_=(0.25, 1), entry=(0.5, 0))
    edge("a4", "tgw", "fep", E_USER, "", exit_=(0.75, 1), entry=(0.5, 0),
         points=[(960, 385), (1884, 385)])
    edge("a5", "fep", "apps", E_USER, "PrivateLink", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a6", "vdi", "iap", E_USER, "", exit_=(1, 0.75), entry=(0, 0.5),
         points=[(250, 258), (250, 865)])
    edge("e1", "web_a", "apps", E_USER, "302", dashed=1, exit_=(0.5, 0), entry=(0.5, 1),
         points=[(970, 678), (2530, 678)])
    edge("e2", "web_a", "pcapp", E_USER, "302", dashed=1, exit_=(0, 0.5), entry=(1, 0.5),
         points=[(828, 785), (828, 865)])

    # ── 앱 → 사내 시스템 ───────────────────────────────────────────────────
    edge("b1", "apps", "ncc", E_LEGACY, "", exit_=(0.25, 1), entry=(0.1, 0))
    edge("b2", "ncc", "vpces", E_LEGACY, "PrivateLink", exit_=(0, 0.5), entry=(0.5, 1),
         points=[(2425, 720), (2425, 320), (1639, 320)])
    edge("b3", "vpces", "nlb", E_LEGACY, "", exit_=(0, 0.5), entry=(1, 0.5))
    edge("b4", "nlb", "dx", E_LEGACY, "IP 타깃 ⚠", dashed=1,
         exit_=(0.5, 1), entry=(0.7, 1), points=[(1289, 340), (790, 340)])
    edge("b5", "dx", "sys2", E_LEGACY, "", exit_=(0, 0.75), entry=(1, 0.5),
         points=[(714, 263), (714, 1149)])

    # ── 조정 루프 · 인증 ───────────────────────────────────────────────────
    edge("c1", "wrk_c", "mep", INK, "", dashed=1, exit_=(0.5, 0), entry=(0.5, 1))
    edge("c2", "mep", "fep", INK, "", dashed=1, exit_=(1, 0.5), entry=(0, 0.5))
    edge("c3", "wrk_a", "gl", INK, "조회 pull", dashed=1, exit_=(0.5, 1), entry=(0.25, 0),
         points=[(1180, 940), (774, 940), (774, 352), (548, 352)])
    edge("f1", "idp", "vdi", INK, "SSO", dashed=1, exit_=(0.5, 0), entry=(0.5, 1))

    # ── 소스 · 배포 ────────────────────────────────────────────────────────
    edge("d1", "gl", "harbor", E_SUPPLY, "", exit_=(0.25, 1), entry=(0.5, 0),
         points=[(548, 530), (155, 530)])
    edge("d2", "flux", "harbor", E_SUPPLY, "", exit_=(0, 0.5), entry=(1, 0.5))
    edge("d3", "flux", "k8s", E_SUPPLY, "", exit_=(0.5, 1), entry=(0.5, 0),
         points=[(365, 790), (155, 790)])
    edge("d4", "kyverno", "pcapp", E_SUPPLY, "", exit_=(0.5, 1), entry=(0.5, 0))
    edge("d5", "iap", "pcapp", E_SUPPLY, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("d6", "gl", "ws", E_SUPPLY, "bundle deploy", exit_=(1, 0.5), entry=(0.5, 1),
         points=[(804, 435), (804, 1062), (1880, 1062)])
    edge("g1", "ws1", "gl", E_SUPPLY, "git push", exit_=(0.5, 1), entry=(0.75, 0),
         points=[(1375, 1665), (744, 1665), (744, 376), (583, 376)])
    edge("g2", "coder", "ws1", E_SUPPLY, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("g3", "coder", "ebs", E_SUPPLY, "", exit_=(0, 0.5), entry=(1, 0.5))
    edge("g4", "ws1", "nat", INK, "", exit_=(0.5, 0), entry=(0.5, 1),
         points=[(1375, 1405), (970, 1405)])
    edge("g5", "nat", "igw", INK, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("g6", "ws2", "bedep", INK, "", exit_=(0.5, 0), entry=(0.5, 1),
         points=[(1635, 1405), (1835, 1405)])
    edge("g7", "bedep", "bedrock", INK, "", exit_=(1, 0.5), entry=(0.5, 0),
         points=[(2309, 1285)])


def main():
    tree = E.parse(TARGET)
    root = tree.getroot()
    for d in list(root.findall("diagram")):
        if d.get("id") == PAGE_ID:
            root.remove(d)

    page = E.SubElement(root, "diagram", id=PAGE_ID, name=PAGE_NAME)
    model = E.SubElement(page, "mxGraphModel", dx="2400", dy="1400", grid="1",
                         gridSize="10", guides="1", tooltips="1", connect="1",
                         arrows="1", fold="1", page="1", pageScale="1",
                         pageWidth=str(W), pageHeight=str(H), math="0", shadow="0",
                         background="#FFFFFF")
    build(E.SubElement(model, "root"))

    root.set("pages", str(len(root.findall("diagram"))))
    E.indent(tree, space="  ")
    tree.write(TARGET, encoding="UTF-8", xml_declaration=True)
    print(f"wrote page '{PAGE_NAME}' → {TARGET}")


if __name__ == "__main__":
    main()
