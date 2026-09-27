#!/usr/bin/env python3
"""앱마켓 중심 인프라 아키텍처 도면 `ax-market_infra.drawio`를 생성한다.

반영 결정
- AXM-0007  모듈러 모놀리스 + 레지스트리/프로젝션. 같은 이미지를 web · worker 두 모드로
            (web = catalog · evidence · launch · authz, worker = registry 조정 루프 · ingest)
- AXM-0013  인프라 특성 — 보안성 · 감사 가능성 · 상호운용성 · 가용성 · 운영 용이성
- AXM-0014  SSO 중계는 Cognito
- AXM-0015  Cognito 로그인 경로 = split-horizon DNS + 사내 L4 리버스 프록시
- AXM-0016  ECS Fargate, 클러스터 2개(market · auth-proxy), worker 단일 리더

아이콘
- AWS 서비스·리소스는 **AWS Architecture Icons 2026-07-31 패키지**의 공식 SVG를 내장한다.
  draw.io 내장 `mxgraph.aws4` 스텐실은 패키지보다 늦게 갱신되므로 쓰지 않는다.
  계정 · VPC · 서브넷 경계만 draw.io의 AWS 그룹 도형을 쓴다(편집 편의).
- 출처와 SHA-256은 `assets/icons/sources.json`.

재생성: python3 docs/diagrams/tools/build_market_infra.py
내보내기: drawio -x -f png -e -b 10 -o docs/diagrams/ax-market_infra.drawio.png docs/diagrams/ax-market_infra.drawio
"""
from pathlib import Path
import base64
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent
ICONS = DIAG / "assets" / "icons"
OUT = DIAG / "ax-market_infra.drawio"

W, H = 3200, 2020

INK = "#37474F"
E_USER = "#1A66C9"     # 사용자 진입
E_LOGIN = "#7B1FA2"    # 로그인 (Cognito)
E_RECON = "#546E7A"    # 조정 루프 · 프로바이더 · 데이터
ACCENT = "#C2185B"     # 신규 구축
WARN = "#B7791F"       # 통제 밖 · 퍼블릭 · 미확정
NEUTRAL = "#78909C"
C_COMPUTE = "#ED7100"

cells = None
origins = {}


def st_group(gr_icon, stroke, font, dashed=0, fill="none", sw=1.5, size=20):
    return ("sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
            f"fontSize={size};fontStyle=1;container=1;dropTarget=1;collapsible=0;pointerEvents=0;"
            f"recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.{gr_icon};"
            f"strokeColor={stroke};fillColor={fill};strokeWidth={sw};verticalAlign=top;"
            f"align=left;spacingLeft=34;fontColor={font};dashed={dashed};")


def st_plain(stroke, font, dashed=1, fill="none", sw=1.5, size=15):
    return ("rounded=0;html=1;whiteSpace=wrap;container=1;dropTarget=1;collapsible=0;"
            f"pointerEvents=0;recursiveResize=0;fillColor={fill};strokeColor={stroke};"
            f"strokeWidth={sw};dashed={dashed};verticalAlign=top;align=left;spacingLeft=10;"
            f"spacingTop=4;fontSize={size};fontStyle=1;fontColor={font};")


ST_AZ = st_plain("#147EBA", "#147EBA", dashed=1, sw=1.5, size=16)


def st_edge(color, dashed=0, width=2):
    return ("edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
            f"strokeWidth={width};strokeColor={color};dashed={dashed};endArrow=block;endFill=1;"
            f"endSize=7;fontSize=13;fontStyle=1;fontColor={color};labelBackgroundColor=#FFFFFF;")


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


_img_cache = {}


def icon(cid, label, cx, cy, name, parent="1", size=64, faded=False, lw=220):
    """공식 SVG 아이콘을 중심 좌표에 내장한다. 라벨은 아이콘 아래."""
    if name not in _img_cache:
        raw = (ICONS / name).read_bytes()
        mime = "image/png" if name.endswith(".png") else "image/svg+xml"
        _img_cache[name] = f"data:{mime},{base64.b64encode(raw).decode()}"
    style = ("shape=image;imageAspect=1;aspect=fixed;html=1;verticalLabelPosition=bottom;"
             "verticalAlign=top;align=center;fontSize=14;fontStyle=1;fontColor=#232F3E;"
             f"labelWidth={lw};spacingTop=-2;image={_img_cache[name]};")
    if faded:
        style += "opacity=35;textOpacity=60;"
    return node(cid, label, cx - size / 2, cy - size / 2, size, size, style, parent)


def text(cid, value, x, y, w, h, size=13, color=INK, align="left", parent="1", bold=0):
    return node(cid, value, x, y, w, h,
                f"text;html=1;align={align};verticalAlign=top;whiteSpace=wrap;fontSize={size};"
                f"fontStyle={bold};fontColor={color};spacing=2;", parent)


def badge(cid, value, x, y, w, color):
    return node(cid, value, x, y, w, 26,
                f"rounded=1;arcSize=45;html=1;whiteSpace=wrap;fillColor={color};"
                "strokeColor=none;fontColor=#FFFFFF;fontSize=13;fontStyle=1;"
                "align=center;verticalAlign=middle;")


def edge(cid, src, tgt, color, label="", dashed=0, exit_=None, entry=None, points=None,
         width=2):
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


WARN_G = f"<font color='{WARN}'>⚠</font>"
L, R, T, B = (0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1)


def build(root):
    global cells
    cells = root
    E.SubElement(cells, "mxCell", id="0")
    E.SubElement(cells, "mxCell", id="1", parent="0")

    node("bg", "", 0, 0, W, H,
         "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=none;")
    text("title", "<b>AX App Market · 인프라 아키텍처 v1.0</b>", 40, 26, 1200, 40, 26, "#182C46")
    text("subtitle", "2026-09-27 · 앱마켓 중심 · AXM-0007 · 0013 · 0014 · 0015 · 0016 반영 · "
         "AWS Architecture Icons 2026-07-31", 40, 70, 1500, 24, 14, "#64748B")

    # ── 온프렘 ───────────────────────────────────────────────────────────
    group("g_onp", "온프렘 · 사내망", 40, 140, 560, 1720,
          st_group("group_corporate_data_center", "#5A6C86", "#5A6C86"))
    icon("vdi", "임직원 VDI<br>브라우저", 170, 300, "generic-users.svg", "g_onp")
    icon("dns", "사내 DNS<br><span style='font-weight:normal'>auth.* → 로그인 NLB IP<br>"
         "market.* → ALB IP</span>", 450, 300, "generic-server.svg", "g_onp")
    icon("idp", "원천 IdP<br><span style='font-weight:normal'>타 조직 관리 · SAML 1회 연계</span>",
         450, 560, "generic-office.svg", "g_onp")
    icon("gitlab", "GitLab<br><span style='font-weight:normal'>저장소 · 증적 · 승인</span>",
         170, 1000, "gitlab.svg", "g_onp")
    icon("vks", "VKS 앱<br><span style='font-weight:normal'>Ingress forward-auth</span>",
         450, 1000, "kubernetes.svg", "g_onp")
    text("onp_note", "<b>302 이후</b> 사용자는 런타임에 직통한다.<br>"
         "앱 트래픽은 마켓을 지나지 않는다 (AXM-0009)", 70, 1700, 500, 60, 13, INK, parent="g_onp")

    icon("dx", "Direct Connect<br><span style='font-weight:normal'>+ VPN 백업</span>",
         650, 760, "aws-dx.svg")

    # ── AWS ──────────────────────────────────────────────────────────────
    group("g_aws", "AWS · ap-northeast-2 (서울)", 700, 140, 2460, 1720,
          st_group("group_aws_cloud_alt", "#232F3E", "#232F3E"))
    icon("tgw", "Transit Gateway<br><span style='font-weight:normal'>기구축</span>",
         790, 760, "aws-tgw.svg", "g_aws")

    # 앱마켓 운영 계정
    group("g_mkt", "앱마켓 운영 계정", 880, 190, 1640, 1650,
          st_group("group_account", ACCENT, ACCENT, fill="#FFF7FA", sw=3), "g_aws")
    badge("b_mkt", "신규 구축", 2400, 200, 104, ACCENT)

    group("g_vpc", "앱마켓 VPC · 2 AZ", 910, 250, 1580, 1320,
          st_group("group_vpc2", "#8C4FFF", "#8C4FFF", size=17), "g_mkt")

    group("g_ing", "진입 서브넷 (private)", 940, 305, 1520, 200,
          st_group("group_security_group", "#147EBA", "#147EBA", size=15), "g_vpc")
    icon("alb", "내부 ALB<br><span style='font-weight:normal'>market.&lt;사내도메인&gt; · ACM</span>",
         1250, 400, "aws-alb.svg", "g_ing")
    icon("nlb", "내부 NLB :443<br><span style='font-weight:normal'>auth.&lt;사내도메인&gt; · AZ별 고정 IP</span>",
         1950, 400, "aws-nlb.svg", "g_ing")

    az = {}
    for key, name, x0 in (("a", "가용 영역 a", 940), ("c", "가용 영역 c", 1720)):
        az[key] = x0
        group(f"g_az{key}", name, x0, 545, 740, 995, ST_AZ, "g_vpc")
        group(f"g_app{key}", "앱 서브넷 (private)", x0 + 20, 590, 700, 440,
              st_group("group_security_group", "#147EBA", "#147EBA", size=14), f"g_az{key}")
        group(f"g_cm{key}", "ECS 클러스터 market · Fargate", x0 + 40, 640, 420, 370,
              st_plain(C_COMPUTE, C_COMPUTE, dashed=1, size=14), f"g_app{key}")
        group(f"g_cp{key}", "auth-proxy · Fargate", x0 + 480, 640, 220, 370,
              st_plain(E_LOGIN, E_LOGIN, dashed=1, size=14), f"g_app{key}")
        icon(f"web{key}", "web<br><span style='font-weight:normal'>catalog · evidence<br>"
             "launch · authz</span>", x0 + 140, 770, "aws-ecs-task.svg", f"g_cm{key}", lw=180)
        if key == "a":
            icon("wrk", "worker · 리더 1<br><span style='font-weight:normal'>registry 조정 루프<br>"
                 "ingest · 그룹 동기화</span>", x0 + 350, 770, "aws-ecs-task.svg", "g_cma", lw=190)
        else:
            icon("wrkc", "worker<br><span style='font-weight:normal'>장애 시 재기동</span>",
                 x0 + 350, 770, "aws-ecs-task.svg", "g_cmc", faded=True, lw=190)
        icon(f"px{key}", "proxy<br><span style='font-weight:normal'>nginx stream<br>"
             "TLS 패스스루</span>", x0 + 590, 770, "aws-ecs-task.svg", f"g_cp{key}", lw=180)
        text(f"cm{key}_n", "같은 이미지 · 모드만 분리 (AXM-0007)", x0 + 50, 960, 400, 22, 12,
             C_COMPUTE, parent=f"g_cm{key}")

        group(f"g_dat{key}", "데이터 · 엔드포인트 서브넷 (private)", x0 + 20, 1060, 700, 210,
              st_group("group_security_group", "#147EBA", "#147EBA", size=14), f"g_az{key}")
        group(f"g_egr{key}", "이그레스 서브넷 (public)", x0 + 20, 1300, 700, 220,
              st_group("group_security_group", "#248814", "#248814", size=14), f"g_az{key}")
        icon(f"nat{key}", "NAT GW + EIP<br><span style='font-weight:normal'>auth-proxy 전용</span>",
             x0 + 590, 1400, "aws-nat-gateway.svg", f"g_egr{key}")

    icon("aur_w", "Aurora PostgreSQL<br><span style='font-weight:normal'>writer · advisory lock</span>",
         az["a"] + 170, 1150, "aws-aurora-postgresql.svg", "g_data")
    icon("vpce", "VPC 엔드포인트 <span style='font-weight:normal'>(각 AZ)</span><br>"
         "<span style='font-weight:normal'>ECR · S3 · Logs · Secrets · KMS · STS</span>",
         az["a"] + 500, 1150, "aws-vpc-endpoints.svg", "g_data", lw=260)
    icon("aur_r", "Aurora PostgreSQL<br><span style='font-weight:normal'>reader · 장애 조치</span>",
         az["c"] + 170, 1150, "aws-aurora-postgresql.svg", "g_datc")
    icon("fep", "Databricks front-end<br><span style='font-weight:normal'>PrivateLink EP (각 AZ)</span>",
         az["c"] + 500, 1150, "aws-privatelink.svg", "g_datc")

    icon("igw", "IGW<br><span style='font-weight:normal'>이그레스 전용</span>",
         1700, 1570, "aws-internet-gateway.svg", "g_vpc")

    # 계정 공통 (VPC 밖)
    text("reg_t", "계정 공통", 920, 1600, 200, 24, 15, ACCENT, bold=1, parent="g_mkt")
    reg = [
        ("s3", "S3 증적<br><span style='font-weight:normal'>Object Lock · 삭제 불가</span>",
         "aws-s3-object-lock.svg"),
        ("ecr", "ECR<br><span style='font-weight:normal'>market · proxy 이미지</span>", "aws-ecr.svg"),
        ("cw", "CloudWatch<br><span style='font-weight:normal'>로그 · 플로우 로그</span>",
         "aws-cloudwatch.svg"),
        ("sm", "Secrets Manager<br><span style='font-weight:normal'>OIDC · API 자격증명</span>",
         "aws-secrets-manager.svg"),
        ("kms", "KMS", "aws-kms.svg"),
        ("phz", "Route 53 PHZ<br><span style='font-weight:normal'>auth.* → 로그인 NLB</span>",
         "aws-route53-hosted-zone.svg"),
    ]
    for i, (cid, lab, f) in enumerate(reg):
        icon(cid, lab, 1010 + i * 235, 1690, f, "g_mkt", lw=210)

    # 오른쪽 — 관리형 퍼블릭 · Databricks
    group("g_pub", "AWS 관리형 · 퍼블릭 엔드포인트", 2560, 190, 580, 590,
          st_plain(WARN, WARN, dashed=1, fill="#FFFBF0", sw=2, size=17), "g_aws")
    icon("cf", "CloudFront<br><span style='font-weight:normal'>Cognito 커스텀 도메인<br>"
         "auth.&lt;사내도메인&gt;</span>", 2680, 330, "aws-cloudfront.svg", "g_pub", lw=200)
    icon("cog", "Cognito 사용자 풀<br><span style='font-weight:normal'>SSO 중계 (AXM-0014)</span>",
         2990, 330, "aws-cognito.svg", "g_pub", lw=200)
    icon("waf", "WAF<br><span style='font-weight:normal'>허용: NAT EIP 2 + DBX CP<br>"
         "IP rate 규칙 금지</span>", 2990, 600, "aws-waf.svg", "g_pub", lw=210)

    group("g_dbx", "Databricks 전용 계정", 2560, 840, 580, 400,
          st_group("group_account", "#CD2264", "#CD2264", size=17), "g_aws")
    badge("b_dbx", "기존", 3060, 850, 64, NEUTRAL)
    icon("ws", "워크스페이스 · Apps API<br><span style='font-weight:normal'>상태 조회 · SCIM · CAN_USE</span>",
         2850, 1010, "databricks.png", "g_dbx", lw=260)

    group("g_cp", "Databricks 컨트롤 플레인 · 통제 밖", 2560, 1300, 580, 300,
          st_plain(WARN, WARN, dashed=1, fill="#FFFBF0", sw=2, size=17), "g_aws")
    icon("dcp", "계정 SSO 토큰 교환<br><span style='font-weight:normal'>퍼블릭 DNS → CloudFront</span>",
         2850, 1430, "databricks.png", "g_cp", lw=260)

    # ── 범례 ─────────────────────────────────────────────────────────────
    text("legend", (
        f"<b>선</b>&nbsp;&nbsp; <font color='{E_USER}'><b>━━</b></font> 사용자 진입 (DX · 사설)"
        f"&nbsp;&nbsp;&nbsp; <font color='{E_LOGIN}'><b>━━</b></font> 로그인 — split-horizon DNS → "
        "L4 프록시 → NAT → Cognito (AXM-0015)"
        f"&nbsp;&nbsp;&nbsp; <font color='{E_RECON}'><b>┅┅</b></font> 조정 루프 pull · 프로바이더 · 데이터<br>"
        f"<b>경계</b>&nbsp;&nbsp; <font color='{ACCENT}'><b>굵은 테두리</b></font> 신규 구축"
        f"&nbsp;&nbsp;&nbsp; <font color='{WARN}'><b>점선 · 옅은 배경</b></font> 퍼블릭 또는 우리 통제 밖"
        f"&nbsp;&nbsp;&nbsp; <font color='{C_COMPUTE}'><b>주황 점선</b></font> ECS 클러스터 market"
        f"&nbsp;&nbsp;&nbsp; <font color='{E_LOGIN}'><b>보라 점선</b></font> ECS 클러스터 auth-proxy<br>"
        f"<b>미확정</b>&nbsp;&nbsp; {WARN_G} 로그인 프록시 PoC · Databricks CP 출구 IP 확인 · "
        "원천 IdP 종류 · 목표 수량(SLA)에 따른 사양"),
        40, 1890, 3100, 90, 14, INK)

    # ── 사용자 진입 ──────────────────────────────────────────────────────
    edge("u0", "vdi", "dns", E_USER, "이름 해석", dashed=1, exit_=R, entry=L)
    edge("u1", "vdi", "dx", E_USER, "HTTPS", exit_=B, entry=L, points=[(170, 760)])
    edge("u2", "dx", "tgw", E_USER, "", exit_=R, entry=L)
    edge("u3", "tgw", "alb", E_USER, "카탈로그 · /launch", exit_=T, entry=L,
         points=[(790, 400)])
    edge("u4", "alb", "weba", E_USER, "", exit_=B, entry=T, points=[(1250, 515), (1080, 515)])
    edge("u5", "alb", "webc", E_USER, "", exit_=B, entry=T, points=[(1250, 515), (1860, 515)])

    # ── 로그인 ───────────────────────────────────────────────────────────
    edge("l0", "tgw", "nlb", E_LOGIN, "로그인 auth.*", exit_=(0.75, 0), entry=T,
         points=[(806, 278), (1950, 278)])
    edge("l1", "nlb", "pxa", E_LOGIN, "", exit_=B, entry=T, points=[(1950, 530), (1530, 530)])
    edge("l2", "nlb", "pxc", E_LOGIN, "", exit_=B, entry=T, points=[(1950, 530), (2310, 530)])
    edge("l3", "pxa", "nata", E_LOGIN, "", exit_=B, entry=T)
    edge("l4", "pxc", "natc", E_LOGIN, "", exit_=B, entry=T)
    edge("l5", "nata", "igw", E_LOGIN, "", exit_=B, entry=T, points=[(1530, 1492), (1700, 1492)])
    edge("l6", "natc", "igw", E_LOGIN, "", exit_=B, entry=T, points=[(2310, 1492), (1700, 1492)])
    text("l7_t", "인터넷 HTTPS · SNI 유지 → CloudFront", 1760, 1578, 420, 22, 13, E_LOGIN, bold=1)
    edge("l7", "igw", "cf", E_LOGIN, "", exit_=R, entry=L,
         points=[(2545, 1570), (2545, 330)])
    edge("l8", "cf", "cog", E_LOGIN, "", exit_=R, entry=L)
    edge("l9", "waf", "cog", WARN, "연결", dashed=1, exit_=T, entry=B)
    edge("l10", "idp", "cog", E_LOGIN, "SAML (브라우저 경유)", dashed=1, exit_=R, entry=T,
         points=[(565, 560), (565, 118), (2990, 118)])
    edge("l11", "dcp", "cf", WARN, "토큰 교환 · 퍼블릭", dashed=1, exit_=R, entry=T,
         points=[(3110, 1430), (3110, 225), (2680, 225)])

    # ── 조정 루프 · 프로바이더 · 데이터 ──────────────────────────────────
    edge("r1", "wrk", "tgw", E_RECON, "provider: GitLab · VKS", dashed=1, exit_=R, entry=B,
         points=[(1392, 770), (1392, 1045), (790, 1045)])
    edge("r2", "dx", "gitlab", E_RECON, "", dashed=1, exit_=B, entry=T,
         points=[(650, 890), (170, 890)])
    edge("r3", "dx", "vks", E_RECON, "", dashed=1, exit_=B, entry=T,
         points=[(650, 890), (450, 890)])
    edge("r4", "wrk", "fep", E_RECON, "provider: Databricks", dashed=1, exit_=R, entry=T,
         points=[(1392, 770), (1392, 1045), (2220, 1045)])
    edge("r5", "fep", "ws", E_RECON, "PrivateLink", dashed=1, exit_=R, entry=L,
         points=[(2525, 1150), (2525, 1010)])
    edge("r6", "g_cma", "aur_w", E_RECON, "", dashed=1, exit_=(0.3, 1), entry=T)
    edge("r7", "g_cma", "s3", E_RECON, "증적 · Gateway EP", dashed=1, exit_=L, entry=T,
         points=[(925, 825), (925, 1620), (1010, 1620)])


def main():
    mf = E.Element("mxfile", host="app.diagrams.net", pages="1")
    page = E.SubElement(mf, "diagram", id="market-infra", name="앱마켓 인프라 v1.0")
    model = E.SubElement(page, "mxGraphModel", dx="3200", dy="2020", grid="1",
                         gridSize="10", guides="1", tooltips="1", connect="1",
                         arrows="1", fold="1", page="1", pageScale="1",
                         pageWidth=str(W), pageHeight=str(H), math="0", shadow="0",
                         background="#FFFFFF")
    build(E.SubElement(model, "root"))
    tree = E.ElementTree(mf)
    E.indent(tree, space="  ")
    tree.write(OUT, encoding="UTF-8", xml_declaration=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
