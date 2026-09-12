#!/usr/bin/env python3
"""Regenerate the accepted architecture with embedded product icons. No network required."""
from pathlib import Path
import base64
import html
import math
import xml.etree.ElementTree as E

OUT = Path(__file__).resolve().parents[1]
W,H=1920,1280
NAVY='#182C46'; INK='#23364D'; MUTED='#64748B'; BORDER='#CBD5E1'
BLUE='#2563B9'; TEAL='#087E83'; ORANGE='#DA623C'; GOLD='#B7791F'
svg=[]
root=E.Element('mxfile',host='app.diagrams.net')
page=E.SubElement(root,'diagram',id='ax-component-architecture',name='AX 앱 운영 체계 · 구성요소 뷰')
m=E.SubElement(page,'mxGraphModel',dx=str(W),dy=str(H),grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(W),pageHeight=str(H))
cells=E.SubElement(m,'root')
E.SubElement(cells,'mxCell',id='0');E.SubElement(cells,'mxCell',id='1',parent='0')
seq=1

def vertex(value,x,y,w,h,style):
    global seq
    seq+=1
    c=E.SubElement(cells,'mxCell',id=str(seq),value=value,style=style,vertex='1',parent='1')
    E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})

def rect(x,y,w,h,fill='white',stroke='none',radius=12,sw=1.4,dash=False):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')
    vertex('',x,y,w,h,f'rounded={int(radius>0)};arcSize=8;fillColor={fill};strokeColor={stroke};strokeWidth={sw};dashed={int(dash)};')

def txt(x,y,s,size=20,color=INK,bold=False,align='left',width=600):
    anchor='middle' if align=='center' else 'start'
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{html.escape(s)}</text>')
    vertex(s,x-width/2 if align=='center' else x,y-size,width,size+8,f'text;html=0;fillColor=none;strokeColor=none;align={align};verticalAlign=middle;spacing=0;fontFamily=Apple SD Gothic Neo;fontSize={size};fontColor={color};fontStyle={int(bold)};')

def edge(points,color=MUTED,dash=False,arrow=True,width=2):
    svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="6 5"' if dash else '')+(f' marker-end="url(#{color[1:]})"' if arrow else '')+'/>')
    global seq
    seq+=1
    c=E.SubElement(cells,'mxCell',id=str(seq),edge='1',parent='1',style=f'endArrow={"block" if arrow else "none"};strokeColor={color};strokeWidth={width};dashed={int(dash)};rounded=0;')
    g=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
    for name,p in [('sourcePoint',points[0]),('targetPoint',points[-1])]:
        E.SubElement(g,'mxPoint',x=str(p[0]),y=str(p[1]),**{'as':name})
    a=E.SubElement(g,'Array',**{'as':'points'})
    for x,y in points[1:-1]:E.SubElement(a,'mxPoint',x=str(x),y=str(y))

def badge(x,y,w,s,color=BLUE,fill='#EBF2FD'):
    rect(x,y,w,26,fill,radius=5)
    txt(x+w/2,y+18,s,14,color,True,'center',w)

def icon(kind,x,y,size=48,color=BLUE):
    a=[]
    if kind=='code':
        a=['<rect x="7" y="9" width="50" height="44" rx="6"/>','<path d="M7 21h50M14 15h1m5 0h1M25 30l-8 7 8 7m14-14 8 7-8 7m-4-18-6 26"/>']
    elif kind=='gitlab':
        a=[f'<path d="M32 55 7 35 12 9 23 28h18L52 9l5 26Z" fill="{color}" stroke="none"/>','<path d="M7 35h50L32 55 23 28m9 27 9-27" stroke="white" stroke-width="1.7"/>']
    elif kind=='dbx':
        a=['<path d="m7 18 25-12 25 12-25 12ZM7 29l25 12 25-12M7 40l25 12 25-12"/>']
    elif kind=='k8s':
        a=[f'<path d="m32 3 23 12 6 26-17 20H20L3 41l6-26Z" fill="{color}" stroke="none"/>','<circle cx="32" cy="32" r="14" stroke="white"/>','<circle cx="32" cy="32" r="4" stroke="white"/>']
        for n in range(7):
            ang=2*math.pi*n/7
            a.append(f'<path d="M{32+5*math.sin(ang):.2f} {32+5*math.cos(ang):.2f}L{32+21*math.sin(ang):.2f} {32+21*math.cos(ang):.2f}" stroke="white"/>')
    elif kind=='app':
        a=['<rect x="5" y="7" width="44" height="38" rx="5" opacity=".35"/>','<rect x="11" y="13" width="44" height="38" rx="5" fill="white"/>','<rect x="17" y="19" width="42" height="38" rx="5" fill="white"/>','<path d="M17 30h42M24 25h1m5 0h1"/>','<rect x="25" y="37" width="10" height="10" rx="1"/>','<path d="M41 38h10m-10 7h10"/>']
    elif kind=='bot':
        a=['<rect x="9" y="19" width="46" height="34" rx="9"/>','<path d="M32 19V9m-5 0h10M3 30v12m58-12v12M23 44h18"/>','<circle cx="23" cy="32" r="3"/>','<circle cx="41" cy="32" r="3"/>']
    elif kind=='db':
        a=['<path d="M10 16v32c0 12 44 12 44 0V16"/>','<ellipse cx="32" cy="16" rx="22" ry="9"/>','<path d="M10 31c0 12 44 12 44 0M10 44c0 12 44 12 44 0"/>']
    elif kind=='shield':
        a=['<path d="m32 5 23 9v18c0 12-12 22-23 27C21 54 9 44 9 32V14Z"/>','<path d="m21 31 8 8 16-18"/>']
    elif kind=='user':
        a=['<circle cx="32" cy="18" r="10"/>','<path d="M12 56V46c0-18 40-18 40 0v10Z"/>']
    elif kind=='key':
        a=['<circle cx="22" cy="23" r="14"/>','<path d="m32 34 22 22m-9-9 8-8m-16 0 8-8"/>']
    elif kind=='market':
        a=['<path d="M9 26v30h46V26M6 25l6-17h40l6 17M6 25c0 10 13 10 13 0 0 10 13 10 13 0 0 10 13 10 13 0 0 10 13 10 13 0"/>','<path d="M26 56V40h14v16"/>']
    elif kind=='chart':
        a=['<path d="M8 9v47h49M18 43V32m12 11V22m12 21V12"/>','<path d="m14 26 14-13 13 4L55 5"/>']
    elif kind=='logs':
        a=['<rect x="12" y="6" width="40" height="52" rx="5"/>','<path d="M22 18h21M22 28h21M22 38h21M22 48h13"/>']
    elif kind=='server':
        a=['<path d="m7 20 7-12h36l7 12v35H7Z"/>','<path d="M7 20h50M7 38h50M16 28h20m-20 18h20"/>','<circle cx="48" cy="29" r="1.5"/>','<circle cx="48" cy="47" r="1.5"/>']
    elif kind=='cloud':
        a=['<path d="M17 49h32c16 0 16-24 1-25C45 4 20 6 17 24 0 25 1 49 17 49Z"/>','<path d="M23 35h18m-9-8v16"/>']
    elif kind=='network':
        a=['<rect x="21" y="5" width="22" height="15" rx="3"/>','<rect x="4" y="43" width="22" height="15" rx="3"/>','<rect x="38" y="43" width="22" height="15" rx="3"/>','<path d="M32 20v12H15v11m17-11h17v11"/>']
    elif kind=='package':
        a=['<path d="m7 18 25-12 25 12v29L32 59 7 47ZM7 18l25 12 25-12M32 30v29M20 12l25 12v13"/>']
    elif kind=='sync':
        a=['<path d="M10 26a23 23 0 0 1 42-10l5 8M57 7v17H40M54 38a23 23 0 0 1-42 10l-5-8M7 57V40h17"/>']
    elif kind=='spark':
        a=['<path d="m32 5 7 19 20 8-20 8-7 19-7-19-20-8 20-8ZM52 3v12m-6-6h12"/>']
    body=f'<g fill="none" stroke="{color}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round">'+''.join(a)+'</g>'
    svg.append(f'<g transform="translate({x},{y}) scale({size/64})">{body}</g>')
    data=base64.b64encode(f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{body}</svg>'.encode()).decode()
    vertex('',x,y,size,size,f'shape=image;imageAspect=0;aspect=fixed;image=data:image/svg+xml,{data};')

def tile(cx,y,kind,label,sub='',color=BLUE,size=51,width=130):
    icon(kind,cx-size/2,y,size,color)
    txt(cx,y+size+26,label,18,INK,True,'center',width)
    if sub:txt(cx,y+size+49,sub,15,MUTED,False,'center',width)

def domain(x,y,w,h,n,title,eng,color,fill):
    rect(x,y,w,h,fill,BORDER,16,1.7)
    rect(x,y,w,70,color,radius=12)
    rect(x+18,y+17,36,36,'white',radius=18)
    txt(x+36,y+43,str(n),24,color,True,'center',36)
    txt(x+69,y+34,title,25,'white',True,width=w-85)
    txt(x+69,y+56,eng,12,'#E4EBF5',width=w-85)

def panel(x,y,w,h,title,color=INK,icon_name=None):
    rect(x,y,w,h,'white',BORDER,12)
    if icon_name:
        icon(icon_name,x+18,y+16,32,color)
        txt(x+61,y+42,title,23,color,True,width=w-80)
    else:txt(x+20,y+37,title,23,color,True,width=w-40)


W,H=2200,1400
for k,v in [('dx',W),('dy',H),('pageWidth',W),('pageHeight',H)]:m.set(k,str(v))
page.set('id','ax-devsecops-architecture');page.set('name','AX 앱 운영 체계 · 배치·DevSecOps')
INK='#263442';NAVY='#263442';BORDER='#88939E';BLUE='#3B617E';TEAL='#366C6A';ORANGE='#A56A34';MUTED='#64717D'

def box(x,y,w,h,title,kind=None,c=INK):
    rect(x,y,w,h,'white',BORDER,8,1.5)
    if kind:
        icon(kind,x+16,y+14,30,c)
        txt(x+59,y+39,title,23,c,True,width=w-75)
    else:txt(x+18,y+38,title,23,c,True,width=w-36)

def node(x,y,w,h,title,sub='',c=INK):
    rect(x,y,w,h,'#F7F8FA','#BAC1C8',5,1)
    assets={'Flux · agentk':'flux.svg','Kyverno':'kyverno.svg',
            '워크스페이스 EC2':'aws-ec2.svg','Bedrock':'aws-bedrock.svg',
            '내부 ALB':'aws-alb.svg','관리형 DB':'generic-database.svg','S3 증적':'aws-s3.svg',
            'Front-end PrivateLink':'aws-privatelink.svg',
            'Endpoint Service · 내부 NLB':'aws-nlb.svg'}
    filename=assets.get(title)
    cx=x+w/2
    fontsize=20
    if filename:
        brand(filename,x+12,y+13,30,30)
        cx+=19
        fontsize=18 if w<275 else 20
    txt(cx,y+29,title,fontsize,c,True,'center',w-(66 if filename else 20))
    if sub:txt(cx,y+54,sub,15,MUTED,False,'center',w-(66 if filename else 20))

def integration(x,y,n,label,c=TEAL):
    rect(x-15,y-15,30,30,c,radius=15)
    txt(x,y+8,str(n),16,'white',True,'center',30)
    if label:
        txt(x+24,y+5,label,13,c,True,width=240)


def group(x,w,n,title):
    rect(x,140,w,1160,'white',BORDER,0,2.2)
    rect(x,140,w,56,'#F2F4F6',radius=0)
    rect(x+16,151,33,33,BLUE,radius=17)
    txt(x+32.5,175,n,21,'white',True,'center',33)
    txt(x+63,177,title,27,INK,True,width=w-79)
    edge([(x,1010),(x+w,1010)],MUTED,arrow=False,width=1.6)

ICONS = OUT / 'assets' / 'icons'
_generic_icon = icon
USED_ICONS = set()

def brand(name, x, y, w=32, h=None):
    """Embed original assets; preserve aspect ratio and colors in both formats."""
    if h is None: h=w
    file=ICONS/name
    raw=file.read_bytes()
    mime='image/png' if file.suffix=='.png' else 'image/svg+xml'
    # The press-kit canvas has large transparent margins. Trim only that canvas,
    # retaining the entire mark, its proportions, and clear space.
    if name=='gitlab.svg':
        asset=E.fromstring(raw)
        asset.set('viewBox','100 105 180 170')
        raw=E.tostring(asset,encoding='utf-8')
    data=base64.b64encode(raw).decode()
    svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:{mime};base64,{data}"/>')
    vertex('',x,y,w,h,f'shape=image;imageAspect=1;aspect=fixed;image=data:{mime},{data};')
    USED_ICONS.add(name)

def icon(kind,x,y,size=48,color=BLUE):
    mapped={'gitlab':'gitlab.svg','k8s':'kubernetes.svg','key':'keycloak.svg',
            'dbx':'databricks.png','app':'generic-app.svg','db':'generic-database.svg',
            'server':'generic-server.svg'}
    if kind=='chart' and y==769:
        return brand('grafana.svg' if x==135 else 'prometheus.svg',x,y,size,size)
    if kind=='logs' and y==769:
        return brand('loki.svg',x,y,size,size)
    if kind=='server' and x==1093 and y==1171:
        return brand('aws-ec2.svg',x,y,size,size)
    if kind in mapped:
        return brand(mapped[kind],x,y,size,size)
    return _generic_icon(kind,x,y,size,color)

svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">')
svg.append('<title id="title">AX 앱 운영 체계 — 배치와 DevSecOps</title><desc id="desc">온프렘 GitLab 검증·승인·배포 파이프라인, AWS 개발환경·앱마켓, VKS 및 Databricks 실행 환경을 실제 배치 경계와 인프라 계층으로 표현한 목표 구성.</desc><defs>')
for c in [NAVY,BLUE,TEAL,ORANGE,GOLD,MUTED]:
    svg.append(f'<marker id="{c[1:]}" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0L8 4.5L0 9Z" fill="{c}"/></marker>')
svg.append('</defs><g font-family="Apple SD Gothic Neo, Noto Sans CJK KR, sans-serif">')
rect(0,0,W,H,'white',radius=0)
txt(40,67,'AX 앱 운영 체계',38,INK,True,width=1100)
txt(40,106,'온프렘에서 검증·승인하고, 승인된 앱을 두 런타임에 배포',22,MUTED,width=1530)
txt(1840,66,'목표 구성 · 설계 단계',18,MUTED,width=320)
txt(1840,102,'2026.09.12',15,MUTED,width=320)
group(40,920,'1','온프렘')
group(1000,720,'2','AWS · 우리 계정')
group(1760,400,'3','Databricks 운영 영역')

# The delivery pipeline is physically inside the on-premises management area.
box(64,225,530,440,'DevSecOps · GitLab / Runner','gitlab',BLUE)
for y,n,title,sub in [
    (294,'01','소스 · 빌드','Git 저장소 · 이미지 빌드'),
    (381,'02','보안 · AI 검증','SAST · SCA · Secret · SBOM / AI-BOM · 평가'),
    (468,'03','운영 승인','MR 승인 · 보호된 환경'),
    (555,'04','승인된 변경 배포','GitOps 저장소 갱신 / Databricks Bundles'),
]:
    node(85,y,488,69,title,sub,BLUE)
    txt(102,y+29,n,16,BLUE,True,width=33)
    if n=='01': brand('generic-git.svg',152,y+16,26)
    if n=='02': brand('generic-shield.svg',152,y+16,26)
    if y<555:edge([(329,y+69),(329,y+87)],BLUE,width=1.8)
brand('harbor.svg',85,633,24)
txt(117,650,'Harbor',16,INK,True,width=80)
brand('cosign.svg',200,630,94,30)
txt(308,650,'이미지 검사 · 서명 · provenance',15,INK,width=270)

box(624,225,312,290,'Private Cloud · VKS','k8s',BLUE)
node(642,284,276,60,'Flux · agentk','GitOps 동기화',BLUE)
edge([(780,344),(780,362)],INK,width=1.7)
node(642,362,276,60,'Kyverno','서명·provenance 검증',BLUE)
edge([(780,422),(780,440)],INK,width=1.7)
node(642,440,276,57,'업무 Web App','컨테이너 실행',INK)

box(624,547,312,126,'AD · Keycloak','key',INK)
txt(642,625,'SSO · Ingress 연계¹',18,INK,width=276)
txt(642,650,'데이터 권한: 앱에서 집행',15,MUTED,width=276)
edge([(780,547),(780,515)],INK,width=1.7)

box(64,703,530,247,'운영 · 감사','chart',INK)
for cx,kind,label in [(155,'chart','Grafana'),(329,'chart','Prometheus'),(503,'logs','Loki')]:
    icon(kind,cx-20,769,40,BLUE)
    txt(cx,842,label,20,INK,True,'center',150)
txt(85,889,'GitLab 감사 · 런타임 로그 · 상태·사용량',18,INK,width=490)
txt(85,925,'운영 결과 → 수정·재평가',17,MUTED,width=490)
edge([(329,703),(329,665)],MUTED,True,width=1.7)

box(624,707,312,243,'사내 시스템 연계 대상','app',INK)
for x,y,label in [(671,777,'MES'),(805,777,'SRM'),(671,845,'ERP'),(805,845,'CRM')]:
    icon('app',x,y,28,BLUE);txt(x+38,y+22,label,19,INK,True,width=88)
txt(780,930,'Wehub',18,INK,True,'center',270)
brand('generic-app.svg',720,908,25)
edge([(936,468),(948,468),(948,803),(936,803)],INK,width=1.7)

# Customer AWS accounts host development and the marketplace, not the CI engine.
box(1024,225,260,510,'Playground 계정',None,TEAL)
icon('code',1128,292,51,TEAL)
txt(1154,388,'AX Playground',25,TEAL,True,'center',235)
txt(1154,422,'AX Playground Server',20,INK,True,'center',235)
edge([(1154,439),(1154,470)],INK,width=1.7)
node(1042,470,224,86,'워크스페이스 EC2','VS Code · Claude Code',TEAL)
txt(1154,591,'표준 템플릿 · Dev Container',15,MUTED,False,'center',235)
node(1042,624,224,59,'Bedrock','개발 AI 연계',TEAL)
txt(1154,714,'PoC → 운영 전환',15,MUTED,False,'center',235)

box(1310,225,386,510,'앱마켓 운영 계정',None,TEAL)
icon('market',1329,291,34,TEAL)
txt(1377,318,'AX App Market',27,TEAL,True,width=300)
txt(1328,355,'검색 · 권한 신청 · 실행',20,INK,width=350)
node(1362,386,282,56,'내부 ALB','사설 진입',TEAL)
edge([(1503,442),(1503,465),(1409,465),(1409,487)],INK,width=1.7)
edge([(1503,465),(1597,465),(1597,487)],INK,width=1.7)
for x,az in [(1328,'AZ-a'),(1513,'AZ-c')]:
    rect(x,487,165,98,'#F6F8F9','#BAC1C8',5,1)
    txt(x+82.5,512,az,14,MUTED,False,'center',155)
    icon('server',x+18,531,30,TEAL)
    txt(x+60,552,'마켓 서비스',17,INK,True,width=100)
    txt(x+60,574,'web · 조회',13,MUTED,width=100)
edge([(1410,585),(1410,602),(1595,602),(1595,619)],INK,width=1.4)
edge([(1595,585),(1595,602),(1410,602),(1410,619)],INK,width=1.4)
node(1328,619,165,61,'관리형 DB','Multi-AZ',TEAL)
node(1513,619,165,61,'S3 증적','승인·SBOM',TEAL)
txt(1328,711,'운영 콘솔 · 상태·비용·증적 조회¹',16,MUTED,width=350)

box(1024,771,672,179,'사설 연결',None,TEAL)
node(1042,829,266,97,'Front-end PrivateLink','Databricks 전용 계정',TEAL)
txt(1175,911,'사용자·API 진입',15,MUTED,False,'center',250)
node(1326,829,352,97,'Endpoint Service · 내부 NLB','NCC 연계 / 배치 계정 미정',ORANGE)
txt(1502,911,'온프렘 IP 타깃 검증 필요',15,ORANGE,False,'center',336)

# Provider-managed runtime stays outside the customer account boundary.
box(1784,225,352,230,'Databricks Apps','dbx',BLUE)
icon('app',1850,298,43,BLUE);icon('bot',2000,298,43,BLUE)
txt(1871,379,'Web App',19,INK,True,'center',150)
txt(2021,379,'Agent App',19,INK,True,'center',150)
txt(1802,419,'배포 → 헬스·서빙 버전 확인',18,INK,width=320)
box(1784,495,352,217,'데이터 · AI',None,INK)
brand('unity-catalog.svg',1802,546,25)
txt(1840,568,'OBO → Unity Catalog',19,INK,True,width=278)
brand('genie.svg',1802,582,25)
txt(1840,604,'Agent · Genie · Model Serving',16,INK,width=278)
brand('databricks-sql.svg',1802,618,25)
txt(1840,640,'공용 SQL Warehouse',18,INK,width=278)
txt(1802,688,'논리 서비스 관계',14,MUTED,width=315)
edge([(1960,455),(1960,495)],INK,width=1.7)
box(1784,786,352,113,'NCC 사설 엔드포인트','network',ORANGE)
txt(1802,872,'승인된 사내 자원 연계',18,INK,width=315)
edge([(2136,411),(2148,411),(2148,759),(1960,759),(1960,786)],INK,width=1.7)

# Development and approved delivery: logical artifact flow, not packet routing.
edge([(1024,391),(980,391),(980,214),(329,214),(329,225)],BLUE,width=1.8)
rect(680,203,214,22,'white',radius=2);txt(787,220,'코드 제출 · Git push',15,BLUE,True,'center',214)
edge([(573,594),(608,594),(608,314),(642,314)],BLUE,width=1.8)
txt(650,278,'GitOps 변경 반영 · Flux pull',13,BLUE,width=265)
edge([(573,615),(601,615),(601,202),(1960,202),(1960,225)],BLUE,width=1.8)
rect(1210,192,318,22,'white',radius=2);txt(1369,209,'승인 후 Bundle 배포²',16,BLUE,True,'center',318)
edge([(1308,861),(1317,861),(1317,759),(1742,759),(1742,364),(1784,364)],TEAL,width=1.8)
edge([(1784,864),(1750,864),(1750,968),(1502,968),(1502,926)],ORANGE,True,width=1.8)

# Integration points are numbered so the important interfaces can be discussed
# without tracing every line in the drawing.
integration(980,214,1,'개발 산출물',BLUE)
integration(608,314,2,'GitOps / Flux',BLUE)
integration(1210,202,3,'Bundle 배포',BLUE)
integration(1422,596,4,'사설 진입',TEAL)
integration(1750,864,5,'',ORANGE)
txt(1640,859,'NCC 연계',13,ORANGE,True,width=100)

# A distinct infrastructure layer mirrors the reference without inventing hardware.
for x,title,w in [(62,'인프라 기반',880),(1024,'AWS · 서울',670),(1784,'관리형 기반',350)]:
    txt(x,1050,title,23,INK,True,width=w)
icon('network',406,1072,44,BLUE)
txt(470,1102,'사내 네트워크',20,INK,True,width=290)
edge([(428,1116),(428,1143),(196,1143),(196,1167)],INK,width=1.6)
edge([(428,1143),(710,1143),(710,1167)],INK,width=1.6)
for x in [115,177,239]:icon('server',x,1167,47,BLUE)
icon('db',686,1167,47,BLUE)
txt(200,1242,'VKS 컴퓨트',20,INK,True,'center',280)
txt(710,1242,'스토리지',20,INK,True,'center',280)
txt(62,1280,'기구축 자원 · 아이콘 수는 실제 수량과 무관',15,MUTED,width=875)

node(1110,1083,468,58,'TGW · Route53 Resolver','VPC 라우팅 · 사내 DNS 연계',TEAL)
brand('aws-tgw.svg',1125,1095,30)
brand('aws-resolver.svg',1533,1095,30)
edge([(428,1116),(428,1128),(980,1128),(980,1100),(1110,1100)],TEAL,width=2)
rect(930,1071,162,22,'white',radius=2);brand('aws-dx.svg',936,1072,20)
brand('aws-vpn.svg',961,1072,20)
txt(1039,1088,'DX · VPN',16,TEAL,True,'center',106)
edge([(1175,829),(1175,753),(1707,753),(1707,1065),(1344,1065),(1344,1083)],TEAL,arrow=False,width=1.5)
edge([(1707,753),(1707,415),(1644,415)],TEAL,width=1.5)
for x,kind,label in [(1062,'server','개발 EC2'),(1279,'server','마켓 2 AZ'),(1496,'db','DB · S3')]:
    icon(kind,x+31,1171,42,TEAL)
    txt(x+52,1242,label,19,INK,True,'center',180)
edge([(1344,1141),(1344,1156),(1114,1156),(1114,1171)],INK,width=1.4)
edge([(1344,1156),(1331,1156),(1331,1171)],INK,width=1.4)
edge([(1344,1156),(1548,1156),(1548,1171)],INK,width=1.4)
txt(1024,1280,'컴퓨트 선택·CIDR 미정 / 공통 네트워크 계정 확인 필요',14,MUTED,width=672)
edge([(1678,908),(1690,908),(1690,1117),(1578,1117)],ORANGE,True,width=1.6)
icon('cloud',1930,1100,62,BLUE)
txt(1960,1195,'서버리스 컴퓨트',23,INK,True,'center',330)
txt(1960,1237,'Databricks 소유 계정',18,MUTED,False,'center',330)
txt(1960,1280,'Apps · Agent 실행',17,MUTED,False,'center',330)

txt(40,1337,'사용자: VDI → DX·TGW → 마켓 → 앱 이동. 이후 사용자 ↔ 런타임 직통',18,INK,width=1510)
txt(40,1372,'파랑: 코드·배포 흐름  |  초록: 사설 진입  |  주황 점선: 사내 연동 검증·승인 대기',15,MUTED,width=1370)
txt(1490,1337,'¹ 세부 방식 제안   ² WIF 검증 대기',15,MUTED,width=670)
txt(1490,1372,'GitLab 등급 · 서명 키 · 데이터 등급 확인 필요',15,MUTED,width=670)
svg.append('</g></svg>')
(OUT/'ax-app-operating-devsecops.svg').write_text('\n'.join(svg))
E.indent(root)
E.ElementTree(root).write(OUT/'ax-app-operating-devsecops.drawio.xml',encoding='utf-8',xml_declaration=True)
print('Embedded original icons:', len(USED_ICONS))
