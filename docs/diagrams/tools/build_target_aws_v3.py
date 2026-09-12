#!/usr/bin/env python3
"""`ax-market_target 아키텍처.drawio.xml`에 AWS 공식 아이콘 기반 인프라 뷰 v0.3(5페이지)을 추가한다.

v0.2와의 차이
- 설명 메모를 전부 뺐다. 남은 글자는 구성요소 이름, 그룹 이름, 선 이름뿐이다.
- 긴 선에 전용 차선(x·y 레인)을 배정해 교차를 줄였다.
- AX Playground 계정을 VPC · 서브넷 · 엔드포인트 수준으로 구체화했다.
- Playground 워크스페이스에서 만든 소스가 온프렘 GitLab으로 이어지는 경로를 그렸다.

재생성: python3 docs/diagrams/tools/build_target_aws_v3.py
"""
from pathlib import Path
import base64
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent
ICONS = DIAG / "assets" / "icons"
TARGET = DIAG / "ax-market_target 아키텍처.drawio.xml"

PAGE_ID = "infra-aws-v3"
PAGE_NAME = "인프라 뷰 v0.3 · AWS 아이콘"
W, H = 3400, 2120

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
E_REDIR = "#5F6B7A"   # E 실행 302
E_AUTH = "#0E8A8A"    # F 인증
E_SRC = "#C2185B"     # G 소스 · 개발

cells = None
origins = {}

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


ST_BOX = ("rounded=1;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;"
          "strokeColor=#B0BEC5;arcSize=12;")


def st_edge(color, dashed=0, width=2):
    return (f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeWidth={width};strokeColor={color};dashed={dashed};endArrow=block;endFill=1;"
            f"fontSize=10;fontColor={color};labelBackgroundColor=#F5F5F5;")


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


def build(model_root):
    global cells
    cells = model_root
    E.SubElement(cells, "mxCell", id="0")
    E.SubElement(cells, "mxCell", id="1", parent="0")

    node("bg", "", 0, 0, W, H,
         "rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=none;")
    node("title", (
        "<b style='font-size:19px'>AX App Market — 목표 인프라 뷰 v0.3 · AWS 공식 아이콘</b><br>"
        "2026-09-12 · ⚠ = 미확정"),
        40, 26, 900, 56,
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=12;spacing=4;")

    node("legend", (
        "<b>선</b><br>"
        f"<font color='{E_ENTER}'><b>━━</b></font> A 사용자 진입<br>"
        f"<font color='{E_LEGACY}'><b>━━</b></font> B 앱 → 사내 시스템<br>"
        f"<font color='{E_PULL}'><b>┅┅</b></font> C 조정 루프 (pull)<br>"
        f"<font color='{E_DEPLOY}'><b>━━</b></font> D 배포<br>"
        f"<font color='{E_REDIR}'><b>┅┅</b></font> E 실행 302<br>"
        f"<font color='{E_AUTH}'><b>┅┅</b></font> F 인증<br>"
        f"<font color='{E_SRC}'><b>━━</b></font> G 소스 · 개발"),
        2800, 200, 560, 232,
        "rounded=1;whiteSpace=wrap;html=1;fontSize=11;align=left;verticalAlign=top;"
        "fillColor=#FFFFFF;strokeColor=#90A4AE;arcSize=6;spacing=10;")

    # ── 온프렘 ─────────────────────────────────────────────────────────────
    group("g_onp", "온프렘 · 사내망", 40, 140, 780, 1500,
          st_group("group_on_premise", "#5A6C86", "#5A6C86"))
    node("vdi", "임직원 VDI", 110, 260, 78, 78,
         st_resource("client", C_GENERAL), "g_onp")
    brand("idp", "AD → Keycloak", "keycloak.svg", 110, 500, 68, "g_onp")
    brand("dns", "사내 DNS", "generic-server.svg", 390, 500, 68, "g_onp")
    brand("gl", "GitLab + Runner", "gitlab.svg", 660, 500, 68, "g_onp")

    group("g_vks", "Private Cloud (VKS)", 75, 700, 710, 520,
          st_plain("#5A6C86", "#5A6C86"), "g_onp")
    brand("harbor", "Harbor", "harbor.svg", 135, 790, 60, "g_vks")
    brand("flux", "Flux + agentk", "flux.svg", 405, 790, 60, "g_vks")
    brand("kyverno", "Kyverno", "kyverno.svg", 675, 790, 60, "g_vks")
    brand("k8s", "Kubernetes", "kubernetes.svg", 135, 1030, 60, "g_vks")
    brand("iap", "Ingress forward-auth", "generic-shield.svg", 405, 1030, 60, "g_vks")
    brand("pcapp", "VKS Web App", "generic-app.svg", 675, 1030, 60, "g_vks")

    group("g_sys", "사내 업무 시스템", 75, 1340, 710, 260,
          st_plain("#5A6C86", "#5A6C86"), "g_onp")
    node("sys1", "MES · SRM · ERP", 180, 1420, 78, 78,
         st_resource("traditional_server", C_GENERAL), "g_sys")
    node("sys2", "Wehub · CRM", 520, 1420, 78, 78,
         st_resource("traditional_server", C_GENERAL), "g_sys")

    node("dx", "Direct Connect<br>+ VPN", 872, 250, 78, 78,
         st_service("direct_connect", C_NET))

    # ── AWS ────────────────────────────────────────────────────────────────
    group("g_aws", "AWS · ap-northeast-2", 1030, 140, 1710, 1860,
          st_group("group_aws_cloud_alt", "#232F3E", "#232F3E"))

    group("g_net", "공유 네트워크 계정 ⚠", 1060, 200, 1650, 300,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    node("tgw", "Transit Gateway", 1150, 285, 78, 78,
         st_service("transit_gateway", C_NET), "g_net")
    node("nlb", "내부 NLB", 1470, 285, 78, 78,
         st_resource("network_load_balancer", C_NET), "g_net")
    node("vpces", "VPC 엔드포인트 서비스", 1790, 285, 78, 78,
         st_resource("endpoints", C_NET), "g_net")
    node("r53", "Route53 Resolver", 2110, 285, 78, 78,
         st_resource("route_53_resolver", C_NET), "g_net")

    group("g_mkt", "앱마켓 운영 계정 (신규)", 1060, 560, 960, 620,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    group("g_vpc", "전용 VPC ⚠", 1090, 630, 900, 520,
          st_group("group_vpc", "#8C4FFF", "#8C4FFF"), "g_mkt")
    node("alb", "내부 ALB", 1130, 700, 78, 78,
         st_resource("application_load_balancer", C_NET), "g_vpc")
    node("db", "관리형 DB ⚠", 1360, 700, 78, 78,
         st_service("database", C_DB), "g_vpc")
    node("s3", "S3 · 증적", 1600, 700, 78, 78,
         st_service("s3", C_STORAGE), "g_vpc")
    node("mep", "VPC 인터페이스 EP", 1840, 700, 78, 78,
         st_resource("endpoints", C_NET), "g_vpc")

    group("g_aza", "Private Subnet · AZ-a", 1120, 850, 400, 230,
          st_group("group_private_subnet", "#147EBA", "#147EBA"), "g_vpc")
    node("web_a", "앱마켓 web ⚠", 1160, 910, 65, 65,
         st_service("compute", C_COMPUTE), "g_aza")
    node("wrk_a", "조정 워커", 1380, 910, 65, 65,
         st_service("compute", C_COMPUTE), "g_aza")
    group("g_azc", "Private Subnet · AZ-c", 1560, 850, 400, 230,
          st_group("group_private_subnet", "#147EBA", "#147EBA"), "g_vpc")
    node("web_c", "앱마켓 web ⚠", 1600, 910, 65, 65,
         st_service("compute", C_COMPUTE), "g_azc")
    node("wrk_c", "조정 워커", 1820, 910, 65, 65,
         st_service("compute", C_COMPUTE), "g_azc")

    group("g_dbx", "Databricks 전용 계정", 2060, 560, 650, 620,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    node("fep", "front-end PrivateLink EP", 2110, 650, 78, 78,
         st_service("vpc_privatelink", C_NET), "g_dbx")
    brand("ws", "Databricks 워크스페이스", "databricks.png", 2110, 880, 68, "g_dbx")
    brand("uc", "Unity Catalog", "unity-catalog.svg", 2350, 880, 68, "g_dbx")
    brand("wh", "공용 SQL Warehouse", "databricks-sql.svg", 2590, 880, 68, "g_dbx")

    # ── AX Playground 계정 ─────────────────────────────────────────────────
    group("g_pg", "AX Playground 계정", 1060, 1240, 1650, 700,
          st_group("group_account", "#CD2264", "#CD2264"), "g_aws")
    group("g_pgvpc", "Playground VPC ⚠ 전용 신규 CIDR", 1090, 1310, 1450, 580,
          st_group("group_vpc", "#8C4FFF", "#8C4FFF"), "g_pg")

    group("g_pgpub", "Public Subnet", 1120, 1360, 640, 180,
          st_group("group_public_subnet", "#248814", "#248814"), "g_pgvpc")
    node("nat", "NAT Gateway", 1180, 1410, 65, 65,
         st_resource("nat_gateway", C_NET), "g_pgpub")
    node("igw", "Internet Gateway", 1420, 1410, 65, 65,
         st_resource("internet_gateway", C_NET), "g_pgpub")

    group("g_pgep", "VPC 엔드포인트 · 연결", 1800, 1360, 700, 180,
          st_plain("#8C4FFF", "#8C4FFF"), "g_pgvpc")
    node("s3ep", "S3 Gateway EP", 1860, 1410, 65, 65,
         st_resource("endpoints", C_NET), "g_pgep")
    node("tgwatt", "TGW Attachment", 2090, 1410, 65, 65,
         st_resource("transit_gateway_attachment", C_NET), "g_pgep")
    node("bedep", "Bedrock 인터페이스 EP", 2320, 1410, 65, 65,
         st_resource("endpoints", C_NET), "g_pgep")

    group("g_pgpria", "Private Subnet · AZ-a", 1120, 1600, 640, 250,
          st_group("group_private_subnet", "#147EBA", "#147EBA"), "g_pgvpc")
    node("ebs", "영속 EBS", 1180, 1660, 65, 65,
         st_service("elastic_block_store", C_STORAGE), "g_pgpria")
    node("coder", "Coder Server (EC2)", 1400, 1660, 65, 65,
         st_service("ec2", C_COMPUTE), "g_pgpria")
    node("ws1", "워크스페이스 EC2", 1620, 1660, 65, 65,
         st_service("ec2", C_COMPUTE), "g_pgpria")

    group("g_pgpric", "Private Subnet · AZ-c", 1800, 1600, 700, 250,
          st_group("group_private_subnet", "#147EBA", "#147EBA"), "g_pgvpc")
    node("ws2", "워크스페이스 EC2", 1860, 1660, 65, 65,
         st_service("ec2", C_COMPUTE), "g_pgpric")
    node("ws3", "워크스페이스 EC2", 2090, 1660, 65, 65,
         st_service("ec2", C_COMPUTE), "g_pgpric")
    node("resv", "예비 (HA)", 2320, 1660, 65, 65,
         st_service("ec2", C_COMPUTE), "g_pgpric")

    node("bedrock", "Amazon Bedrock", 2580, 1650, 78, 78,
         st_service("bedrock", C_ML), "g_pg")

    # ── Databricks 소유 계정 ───────────────────────────────────────────────
    group("g_srv", "Databricks 소유 계정 (통제 밖)", 2800, 560, 560, 680,
          st_group("group_account", "#D6336C", "#D6336C", dashed=1))
    brand("apps", "Databricks Apps", "databricks.png", 2860, 650, 68, "g_srv")
    brand("agsv", "Agent 서빙 EP", "generic-app.svg", 3140, 650, 68, "g_srv")
    node("ncc", "NCC 사설 엔드포인트", 2850, 880, 300, 80, ST_BOX, "g_srv")
    brand("genie", "Genie space", "genie.svg", 2860, 1060, 68, "g_srv")
    brand("ms", "Model Serving", "generic-server.svg", 3140, 1060, 68, "g_srv")

    # ── A 사용자 진입 ──────────────────────────────────────────────────────
    edge("a1", "vdi", "dx", E_ENTER, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a2", "dx", "tgw", E_ENTER, "DX", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a3", "tgw", "alb", E_ENTER, "", exit_=(0.25, 1), entry=(0.5, 0))
    edge("a4", "tgw", "fep", E_ENTER, "", exit_=(0.75, 1), entry=(0.5, 0),
         points=[(1208, 530), (2149, 530)])
    edge("a5", "fep", "apps", E_ENTER, "PrivateLink", exit_=(1, 0.5), entry=(0, 0.5))
    edge("a6", "vdi", "iap", E_ENTER, "", exit_=(1, 0.75), entry=(0, 0.5),
         points=[(300, 318), (300, 1060)])

    # ── B 앱 → 사내 시스템 ─────────────────────────────────────────────────
    edge("b1", "apps", "ncc", E_LEGACY, "", exit_=(0.25, 1), entry=(0.15, 0))
    edge("b2", "ncc", "vpces", E_LEGACY, "PrivateLink", exit_=(0, 0.5), entry=(0.5, 1),
         points=[(2765, 920), (2765, 430), (1829, 430)])
    edge("b3", "vpces", "nlb", E_LEGACY, "", exit_=(0, 0.5), entry=(1, 0.5))
    edge("b4", "nlb", "dx", E_LEGACY, "IP 타깃 ⚠", dashed=1,
         exit_=(0.5, 1), entry=(0.9, 1), points=[(1509, 470), (942, 470)])
    edge("b5", "dx", "sys2", E_LEGACY, "", exit_=(0, 0.75), entry=(1, 0.5),
         points=[(838, 308), (838, 1459)])

    # ── C 조정 루프 ────────────────────────────────────────────────────────
    edge("c1", "wrk_c", "mep", E_PULL, "", dashed=1, exit_=(0.5, 0), entry=(0.5, 1))
    edge("c2", "mep", "fep", E_PULL, "Databricks REST", dashed=1,
         exit_=(1, 0.5), entry=(0, 0.5))
    edge("c3", "wrk_a", "gl", E_PULL, "조회 pull · GitLab · VKS", dashed=1,
         exit_=(0.5, 1), entry=(0.5, 0),
         points=[(1412, 1200), (1015, 1200), (1015, 466), (694, 466)])

    # ── D 배포 ─────────────────────────────────────────────────────────────
    edge("d1", "gl", "harbor", E_DEPLOY, "", exit_=(0.25, 1), entry=(0.5, 0),
         points=[(677, 660), (165, 660)])
    edge("d2", "flux", "harbor", E_DEPLOY, "pull", exit_=(0, 0.5), entry=(1, 0.5))
    edge("d3", "flux", "k8s", E_DEPLOY, "", exit_=(0.5, 1), entry=(0.5, 0),
         points=[(435, 900), (165, 900)])
    edge("d4", "kyverno", "pcapp", E_DEPLOY, "", exit_=(0.5, 1), entry=(0.5, 0))
    edge("d5", "iap", "pcapp", E_DEPLOY, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("d6", "gl", "ws", E_DEPLOY, "bundle deploy · WIF", exit_=(1, 0.5), entry=(0.5, 1),
         points=[(985, 534), (985, 1225), (2144, 1225)])

    # ── E 실행 302 ─────────────────────────────────────────────────────────
    edge("e1", "web_a", "apps", E_REDIR, "302", dashed=1, exit_=(0.5, 0), entry=(0.8, 1),
         points=[(1192, 836), (2914, 836)])
    edge("e2", "web_a", "pcapp", E_REDIR, "302", dashed=1, exit_=(0, 0.5), entry=(1, 0.5),
         points=[(1045, 942), (1045, 1060)])

    # ── F 인증 ─────────────────────────────────────────────────────────────
    edge("f1", "idp", "vdi", E_AUTH, "SSO", dashed=1, exit_=(0.5, 0), entry=(0.5, 1))

    # ── G 소스 · 개발 ──────────────────────────────────────────────────────
    edge("g1", "ws1", "gl", E_SRC, "git push · TGW · DX", exit_=(0.5, 1), entry=(0.75, 1),
         points=[(1652, 1870), (940, 1870), (940, 640), (711, 640)])
    edge("g2", "coder", "ws1", E_SRC, "프로비저닝", exit_=(1, 0.5), entry=(0, 0.5))
    edge("g3", "coder", "ebs", E_SRC, "", exit_=(0, 0.5), entry=(1, 0.5))
    edge("g4", "ws1", "nat", E_SRC, "egress", exit_=(0.5, 0), entry=(0.5, 1),
         points=[(1652, 1565), (1212, 1565)])
    edge("g5", "nat", "igw", E_SRC, "", exit_=(1, 0.5), entry=(0, 0.5))
    edge("g6", "ws2", "bedep", E_SRC, "", exit_=(0.5, 0), entry=(0.5, 1),
         points=[(1892, 1565), (2352, 1565)])
    edge("g7", "bedep", "bedrock", E_SRC, "LLM 호출", exit_=(1, 0.5), entry=(0.5, 0),
         points=[(2619, 1442)])


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
