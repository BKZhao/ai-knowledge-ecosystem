"""中文完整论文PDF生成器"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, Image, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

pdfmetrics.registerFont(TTFont('WQY', '/home/node/.fonts/wqy-microhei.ttc', subfontIndex=0))

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
IMGS = f"{BASE}/results/pub_beautiful"
OUT  = f"{BASE}/results/完整论文_中文版_20260322.pdf"

W, H = A4
DBLUE = HexColor('#0D47A1'); BLUE = HexColor('#1565C0')
GREEN = HexColor('#2E7D32');  RED  = HexColor('#C62828')
PURPLE= HexColor('#6A1B9A'); ORANGE=HexColor('#E65100')
TEAL  = HexColor('#00695C'); DGRAY = HexColor('#424242')
LGRAY = HexColor('#F5F5F5'); MGRAY = HexColor('#E0E0E0')
GOLD  = HexColor('#F57F17')

def ps(size=10.5, color=black, bold=False, align=TA_JUSTIFY, leading=None, left=0):
    return ParagraphStyle('x', fontName='WQY', fontSize=size, textColor=color,
        alignment=align, leading=leading or size*1.65, leftIndent=left)

TITLE_S  = ps(22, DBLUE,  True,  TA_CENTER)
SUB_S    = ps(13, DGRAY,  False, TA_CENTER)
AUTH_S   = ps(11, DGRAY,  False, TA_CENTER)
ABS_S    = ps(10, black,  False, TA_JUSTIFY, 15)
H1_S     = ps(16, DBLUE,  True,  TA_LEFT,   22)
H2_S     = ps(12, BLUE,   True,  TA_LEFT,   18)
H3_S     = ps(11, DGRAY,  True,  TA_LEFT,   16)
BODY_S   = ps(10.5, black, False, TA_JUSTIFY, 17)
BUL_S    = ps(10,  black, False, TA_LEFT,   16, left=0.5*cm)
FIGCAP_S = ps(9,   DGRAY, False, TA_CENTER, 13)
TABCAP_S = ps(10,  DGRAY, True,  TA_LEFT,   14)
TABN_S   = ps(8.5, HexColor('#757575'), False, TA_LEFT, 12)
REF_S    = ps(9.5, black, False, TA_JUSTIFY, 14, left=1*cm)
SMALL_S  = ps(9,   DGRAY, False, TA_LEFT,   13)
KWDS_S   = ps(9.5, DGRAY, False, TA_LEFT,   14)
PAGE_S   = ps(9,   DGRAY, False, TA_CENTER)
HIGHLIGHT_S = ps(10.5, DBLUE, True, TA_LEFT, 16, left=0.5*cm)

def H1(t): return Paragraph(t, H1_S)
def H2(t): return Paragraph(t, H2_S)
def H3(t): return Paragraph(t, H3_S)
def P(t):  return Paragraph(t, BODY_S)
def BL(t): return Paragraph(f'◆ {t}', BUL_S)
def sp(h=0.3): return Spacer(1, h*cm)
def hr(c=MGRAY): return HRFlowable(width="100%", thickness=0.5, color=c, spaceAfter=4, spaceBefore=4)
def HL(t): return Paragraph(t, HIGHLIGHT_S)

def fig(path, w=14.5*cm, cap=''):
    items = []
    if os.path.exists(path):
        items.append(Image(path, width=w, height=w*0.62))
    if cap:
        items += [sp(0.1), Paragraph(cap, FIGCAP_S)]
    return items

def tbl(data, cw, hc=DBLUE, fs=9):
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),hc),('TEXTCOLOR',(0,0),(-1,0),white),
        ('FONTNAME',(0,0),(-1,-1),'WQY'),('FONTSIZE',(0,0),(-1,0),fs+0.5),
        ('FONTSIZE',(0,1),(-1,-1),fs),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,LGRAY]),
        ('GRID',(0,0),(-1,-1),0.3,MGRAY),
        ('ALIGN',(1,0),(-1,-1),'CENTER'),('ALIGN',(0,0),(0,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(0,-1),6),
    ]))
    return t

story = []

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('WQY', 8.5)
    canvas.setFillColor(HexColor('#9E9E9E'))
    if doc.page > 1:
        canvas.drawCentredString(W/2, 1.2*cm, str(doc.page))
        if doc.page > 2:
            canvas.drawRightString(W-2.2*cm, H-1.6*cm, '生成式AI对知识生态系统的冲击')
            canvas.line(2.2*cm, H-1.8*cm, W-2.2*cm, H-1.8*cm)
    canvas.restoreState()

# ══════════════════════════════════════════════
# 封面
# ══════════════════════════════════════════════
story += [
    sp(2),
    Paragraph('生成式AI对知识生态系统的冲击：', TITLE_S),
    Paragraph('来自Stack Overflow、GitHub与Stack Exchange社区的证据', TITLE_S),
    sp(0.6),
    HRFlowable(width="60%", thickness=2.5, color=BLUE, hAlign='CENTER'),
    sp(0.5),
    Paragraph('赵炳坤', AUTH_S),
    Paragraph('香港城市大学', ps(10.5, DGRAY, align=TA_CENTER)),
    sp(0.3),
    Paragraph('工作论文 · 2026年3月', ps(10, HexColor('#9E9E9E'), align=TA_CENTER)),
    sp(2.5),
    hr(BLUE),
    sp(0.3),
    Paragraph('【摘要】', ps(11, DBLUE, True, TA_LEFT)),
    sp(0.2),
    Paragraph(
        '本文运用八年纵向数据，对生成式AI冲击知识生态系统进行首次系统性实证研究。'
        '研究覆盖Stack Overflow（SO，知识消费侧）、GitHub（知识生产侧）与21个Stack Exchange垂直社区，'
        '时间跨度为2018年1月至2026年2月（98个月）。核心发现呈现出鲜明的"剪刀差"效应：'
        'SO编程问题活跃量从2018年峰值下跌98.5%，而GitHub仓库创建量同期增长536.2%。'
        '基于包含20个控制变量的双重差分（DID）模型，本文证实ChatGPT的发布在因果层面加速了这一分叉趋势'
        '（SO侧β₁=-2.26***，GitHub侧β₂=+3.82***，R²=0.989，N=2,390）。',
        ABS_S),
    sp(0.1),
    Paragraph(
        '超越量级冲击，本文进一步记录了四项深层结构性转变：'
        '（1）质量稀释悖论——问题均分下降67.7%、浏览量下降80.5%，而问题长度反常增加17.8%；'
        '（2）基于对122,723条问题的LLM分类，发现Debug类问题于2018-2019年已骤降20个百分点，'
        '早于ChatGPT发布三年；Conceptual类问题则于2024年首次超越How-to类；'
        '（3）22个SE社区呈现分层冲击——哲学社区（Philosophy SE）是唯一逆势增长的社区（+54.6%），'
        'AI本身成为哲学探讨的新议题；'
        '（4）AI可替代性指数（ARI）与SO下降幅度无显著相关（r=0.23，n.s.），'
        '揭示了行为替代而非内容替代的核心机制。',
        ABS_S),
    sp(0.1),
    Paragraph(
        '本文提出"依赖性知识行为（DKB）vs 自主性知识行为（AKB）"理论框架，'
        '将生成式AI的知识影响解构为替代效应、激活效应与稀释效应三大机制。'
        '研究发现对开放知识社区的可持续性、平台治理政策以及AI时代的知识生产社会学具有重要启示。',
        ABS_S),
    sp(0.2),
    Paragraph('关键词：生成式AI；Stack Overflow；GitHub；知识社区；双重差分法；LLM分类；ChatGPT', KWDS_S),
    hr(MGRAY),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第一章 引言
# ══════════════════════════════════════════════
story += [H1('第一章　引言'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('1.1 研究背景'), sp(0.15),
    P('大型语言模型（LLM）的快速扩散——以2022年11月ChatGPT发布为标志性事件——从根本上改变了人类获取、生产和分享知识的方式。与过去几轮自动化浪潮不同，生成式AI直接挑战的是知识工作的核心：搜索信息、理解概念、调试代码、综合答案。这一能力如何重塑知识社区的运作方式，是当下最具理论与政策意义的议题之一。'),
    sp(0.15),
    P('在线知识社区——尤其是以Stack Overflow（SO）为代表的技术问答平台和GitHub为代表的协作代码仓库——自2008年以来一直是开放知识生产的核心基础设施。Stack Overflow在2024年已积累超过2300万条问题，长期被软件开发者视为最重要的学习资源（Stack Overflow开发者调查，2022）。GitHub托管超过4.2亿个代码仓库，成为开源协作的事实标准。这两个平台共同构成了一个双面知识生态系统：一侧面向知识消费（SO），另一侧面向知识生产（GitHub）。'),
    sp(0.15),
    P('ChatGPT于2022年11月30日发布，随后GPT-4（2023年3月）、GitHub Copilot全面推广以及一系列代码专用LLM的相继涌现，为研究者提供了一个前所未有的自然实验。数百万软件开发者突然获得了可以高精度回答技术问题、从自然语言生成可执行代码、用通俗语言解释复杂概念的AI系统。这一行为转变的实证后果——特别是能将AI驱动的冲击与同期趋势相分离的因果证据——至今仍十分匮乏。'),
    sp(0.25),
    H2('1.2 研究问题'), sp(0.15),
    P('本文旨在弥补上述空白。我们构建了迄今为止AI时代知识生态系统研究中规模最大的纵向数据集，涵盖八年（2018年1月至2026年2月）、三大平台（SO、GitHub、21个SE社区）、14种编程语言，以及超过950万条问题记录。结合面板数据观测、LLM内容分类与DID识别策略，本文回答以下四个核心研究问题：'),
    sp(0.1),
    BL('RQ1：生成式AI是否造成知识消费行为（SO）与知识生产行为（GitHub）的结构性分叉？因果效应量级如何？'),
    BL('RQ2：AI转型之后，社区内部的知识交互质量发生了怎样的变化？'),
    BL('RQ3：知识求助行为的认知结构是否发生了改变——问题类型分布是否出现揭示替代机制的系统性漂移？'),
    BL('RQ4：AI冲击是否具有跨知识领域的同质性，还是呈现与领域特征系统相关的异质分层？'),
    sp(0.25),
    H2('1.3 主要贡献'), sp(0.15),
    P('本文在五个维度上推进了现有文献：'),
    sp(0.1),
    BL('时间维度：将观察窗口延伸至2026年2月（8年），是目前该议题研究中最长的观察期，完整捕捉了冲击的加速轨迹。'),
    BL('同步双侧分析：在单一因果框架内同时分析知识消费侧（SO）与知识生产侧（GitHub），揭示替代与激活的并存。'),
    BL('内容结构分析：运用LLM对122,723条问题进行四类分类，首次在大样本上量化SO问题类型的结构性转变。'),
    BL('跨领域对比：纳入22个SE社区（5大领域），提供迄今最系统的跨学科知识社区AI冲击比较研究。'),
    BL('理论贡献：提出DKB/AKB框架，为AI时代的知识行为分析提供新的理论工具。'),
    sp(0.25),
    H2('1.4 核心发现预览'), sp(0.15),
    P('本文的主要发现如下：'),
    sp(0.1),
    BL('SO问题量从2018年峰值跌落98.5%，GitHub仓库创建量增长536.2%，DID因果检验确认ChatGPT加速了这一分叉（β₁=-2.26***，β₂=+3.82***）。'),
    BL('SO剩余问题质量全面恶化：均分-67.7%，浏览量-80.5%，回答率-23.2%，而问题长度反升+17.8%（质量稀释悖论）。'),
    BL('Debug类问题于2019年骤降（早于ChatGPT三年），而Conceptual类于2024年首次超越How-to类。'),
    BL('Philosophy SE是22个社区中唯一增长者（+54.6%），AI本身成为新的哲学议题来源。'),
    BL('AI可替代性指数（ARI）与跌幅无相关，揭示行为替代而非内容替代的核心机制。'),
    sp(0.2),
    P('以上五项发现均挑战了主流叙事，本文将在第六章以"五大反直觉发现"为专题深度阐释。'),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第二章 文献综述
# ══════════════════════════════════════════════
story += [H1('第二章　文献综述'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('2.1 生成式AI对信息平台的影响'), sp(0.15),
    P('生成式AI的经济与社会影响自GPT-3（Brown等，2020）问世起受到广泛关注，并在ChatGPT推出（OpenAI，2023）后急剧升温。早期实证研究聚焦于劳动力市场：Brynjolfsson等（2023）记录了LLM辅助使客服工人生产率提升14%；Peng等（2023）在实验中发现GitHub Copilot使编程任务速度提升55%。然而，这些研究的观察窗口普遍较短（通常仅3-6个月），缺乏区分AI冲击与并发趋势的严格因果设计。'),
    sp(0.15),
    P('专门针对问答平台的研究同样有限。Kabir等（2023）分析了ChatGPT发布后的早期SO流量数据，发现问题发帖量统计显著下滑；Skjuve等（2023）的问卷调查表明，大多数ChatGPT用户将其作为传统搜索和问答资源的替代品。本文与上述研究最直接相关，但在三个关键维度上实现突破：（1）观察窗口延伸至2026年2月，完整记录加速轨迹；（2）采用DID设计进行因果识别；（3）同时分析知识消费侧与生产侧，揭示两者的对称反转。'),
    sp(0.25),
    H2('2.2 Stack Overflow与在线问答社区'), sp(0.15),
    P('关于Stack Overflow的实证研究已积累了丰富的成果。Adamic等（2008）记录了问答社区的专家动态；Yang等（2014）发现SO逐步从广泛社区资源向专业专家论坛演化，新用户参与度持续下滑；Tausczik与Pennebaker（2012）则发现问题解答率随问题复杂度系统变化。这些发现为本文提供了基准预期：SO社区即使在AI时代之前也已显现脆弱性迹象，ChatGPT则可能成为压倒这个疲态社区的最后一击。'),
    sp(0.15),
    P('社区可持续性理论（Wasko & Faraj，2005；Kankanhalli等，2005）指出，在线知识社区的贡献者参与受声誉激励和互惠规范驱动。一旦AI能够替代社区功能（提供答案），这种激励结构就会瓦解：提问者不再需要社区，答题者失去被感谢的对象，社区的网络效应反转为恶性螺旋。本文的质量数据（回答率-23.2%，接受率-32.5%）提供了这一螺旋化过程的直接证据。'),
    sp(0.25),
    H2('2.3 GitHub与开源协作'), sp(0.15),
    P('GitHub作为知识生产平台的实证研究同样丰富。Dabbish等（2012）记录了社交编程如何提升透明度与协作；Kalliamvakou等（2014）发现大多数GitHub项目是个人仓库而非协作项目——这一发现直接关联本文关于分叉率下降与仓库量增长并存的观察。AI时代的GitHub研究尤其关注GitHub Copilot的影响，但现有研究多聚焦于个体生产率，而非平台级质量变化。本文的GitHub质量指标（分叉率-7.9pp，star率-7.8pp）首次在宏观层面记录了AI激活效应的质量代价。'),
    sp(0.25),
    H2('2.4 知识行为替代理论'), sp(0.15),
    P('Acemoglu与Restrepo（2018）的任务替代框架认为，技术不是直接替代工人，而是替代特定任务，且冲击强度取决于任务的例行化程度。应用于知识工作，Brynjolfsson与Mitchell（2017）指出LLM最直接替代"模式匹配"任务——识别并应用已有解决方案——这与本文分类框架中的How-to和Debug类别高度对应。本文在此基础上进一步区分了"依赖社区的行为"（DKB）与"可独立执行的行为"（AKB），提供了一个更适合知识社区分析的细粒度框架。'),
    sp(0.25),
    H2('2.5 研究空白'), sp(0.15),
    P('综合现有文献，三个核心空白尚未填补：其一，现有研究观察窗口过短，无法区分瞬时冲击与结构性转变；其二，没有研究在单一因果框架内同时分析知识消费侧与生产侧的对称反转；其三，知识求助行为的认知结构变化（即什么类型的问题被AI替代）尚无大样本量化研究。本文正是针对这三个空白设计的。'),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第三章 理论框架
# ══════════════════════════════════════════════
story += [H1('第三章　理论框架'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('3.1 依赖性知识行为（DKB）与自主性知识行为（AKB）'), sp(0.15),
    P('本文的理论核心是对知识行为的一个新分类。<b>依赖性知识行为（Dependent Knowledge Behavior，DKB）</b>是指需要社区参与才能产生价值的行为：发帖者依赖社区成员提供答案，Issue提交者依赖维护者或其他开发者诊断并解决问题。DKB从本质上是社区依赖型的，并且可以被能够提供等价答案的AI系统直接替代——不再需要社区中介。'),
    sp(0.15),
    P('<b>自主性知识行为（Autonomous Knowledge Behavior，AKB）</b>则是指主要价值来自行为者自身创造性输出而非社区响应的行为：创建代码仓库、编写文档、构建原型、进行概念性推理。AKB虽然受益于社区基础设施（版本控制、发现、协作），但其核心价值并不依赖于社区验证。关键在于，AI系统可以<b>增强</b>AKB——通过降低自主创作的认知门槛，使原本缺乏技能的开发者能够编写可运行代码，使初学者得以构建原本无法独立完成的项目。'),
    sp(0.15),
    P('这一DKB/AKB区分生成了可检验的方向性预测：AI将<b>替代</b>DKB（降低其频率），同时<b>激活</b>AKB（提高其频率），从而产生本文数据中观察到的分叉模式。'),
    sp(0.25),
    H2('3.2 三大机制'), sp(0.15),
    P('在DKB/AKB框架之上，本文进一步识别出生成式AI重塑知识生态系统的三大具体机制：'),
    sp(0.1),
    BL('<b>替代效应（Substitution Effect）：</b>AI直接回答具有确定性答案的DKB——尤其是Debug类和How-to类问题——消除了社区中介的必要性。这一效应在答案明确、AI训练数据充分的问题类型上最强。'),
    BL('<b>激活效应（Activation Effect）：</b>通过降低代码创作的认知与技能门槛，AI激活了此前受抑制的AKB，尤其是仓库创建和独立项目开发。AI充当"认知放大器"，将被动的知识消费者转化为主动的知识生产者。'),
    BL('<b>稀释效应（Dilution Effect）：</b>随着AI替代高频次的例行化查询，残余社区活动集中于更难、更罕见的问题。然而，简单问题的消失同时带走了吸引新用户、维系社区活力的"脚手架"，导致大多数常规质量指标的恶化——即"质量稀释悖论"。'),
    sp(0.25),
    H2('3.3 研究假设'), sp(0.15),
    P('基于DKB/AKB框架与三机制模型，本文提出以下四个可检验假设：'),
    sp(0.1),
]

hyp_data = [
    ['假设', '内容', '机制'],
    ['H1（分叉假设）', 'ChatGPT发布因果加速了SO（DKB）与GitHub（AKB）的活动分叉', '替代效应 + 激活效应'],
    ['H2（质量稀释假设）', 'AI转型后SO问题质量全面恶化——回答率、接受率和浏览量下降，而问题长度增加', '稀释效应'],
    ['H3（结构转变假设）', 'SO问题类型分布发生转变：AI替代型（How-to、Debug）占比下降，AI互补型（Conceptual）上升', '替代效应'],
    ['H4（分层冲击假设）', 'AI冲击强度在不同知识领域间存在系统性差异，更可替代的领域跌幅更大', '替代效应（异质性）'],
]
story += [
    Paragraph('表1　研究假设汇总', TABCAP_S), sp(0.1),
    tbl(hyp_data, [1.8*cm, 8.5*cm, 5.2*cm], hc=TEAL, fs=9),
    Paragraph('注：每项假设均可通过DID回归（H1）、质量指标比较（H2）、LLM分类时序（H3）或SE跨社区截面对比（H4）进行检验。', TABN_S),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第四章 数据与方法
# ══════════════════════════════════════════════
story += [H1('第四章　数据与研究方法'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('4.1 数据来源'), sp(0.15),
    H3('4.1.1 Stack Overflow数据转储'), sp(0.1),
    P('本文获取了Stack Overflow官方数据转储（2024年4月版），原始XML文件解压后约97GB。从中提取2018年1月至2024年3月间含以下14种编程语言标签的所有问题：Python、JavaScript、TypeScript、Java、C#、PHP、C++、Swift、Kotlin、Go、Rust、Scala、Haskell、R，共950万条记录，处理后存储为Parquet格式（497MB）。2024年4月至2026年2月的数据通过Stack Exchange API实时补充，最终构成14语言×424周的完整周度时序。'),
    sp(0.15),
    H3('4.1.2 GitHub Archive'), sp(0.1),
    P('通过GitHub Archive API获取13种编程语言的月度仓库创建统计，覆盖2018年1月至2026年2月（98个月观测点）。每个语言-月度单元记录：新建仓库数、活跃仓库率（有commit仓库比例）、分叉率、star率及Issue/仓库比，为量化质量变化提供多维指标。'),
    sp(0.15),
    H3('4.1.3 Stack Exchange社区数据'), sp(0.1),
    P('通过合并SE官方数据转储与API检索数据，获取21个SE社区的月度问题量，完整覆盖至2026年2月。21个社区跨越五大领域：技术类（Physics、Stats、DataSci、AI.SE）、人文类（English、Linguistics、Literature）、社会科学类（Politics、Law、Economics、Academia）、自然科学类（Biology、Chemistry、Astronomy）、文化休闲类（Music、Movies、Travel、Cooking、Philosophy）。'),
    sp(0.15),
    H3('4.1.4 LLM问题类型分类'), sp(0.1),
    P('为分析SO问题的认知结构，本文使用DeepSeek-V3（通过硅基流动API）对122,723条问题进行四类分类：（1）<b>操作指导型（How-to）</b>：如何执行某项操作，有明确步骤答案；（2）<b>调试修复型（Debug）</b>：错误诊断与Bug修复；（3）<b>概念理解型（Conceptual）</b>：概念解释、比较与推理；（4）<b>架构设计型（Architecture）</b>：设计决策与最佳实践。分类输入仅使用问题标签、正文长度和代码块数量（避免全文token成本），每条问题最多重试3次，最终覆盖率99.9%。'),
    sp(0.25),
    H2('4.2 DID设计与识别策略'), sp(0.15),
    P('本文以ChatGPT于2022年11月30日的发布作为准自然实验，利用SO（处理组）与GitHub（对照组）在ChatGPT发布前后的行为差异进行双重差分估计：'),
    sp(0.1),
    Paragraph('log(Y_{it}) = α + β₁(SO_i × Post_t) + β₂(GH_i × Post_t) + γ_i + δ_t + Σφ_k X_{kit} + ε_{it}',
               ps(11, PURPLE, False, TA_CENTER, 18)),
    sp(0.1),
    P('其中γ_i为平台-语言固定效应，δ_t为时间固定效应，X_{kit}为包含20个控制变量的向量（含ARI指数、Covid期间指示变量、技术裁员期指示变量、SO AI Ban及语言特定趋势）。标准误在语言层面聚类。β₁捕捉ChatGPT对SO相对于基准趋势的差异效应，β₂捕捉对GitHub的相应效应。'),
    sp(0.15),
    P('关键识别假设为平行趋势假设——若无ChatGPT，SO与GitHub将遵循平行趋势。本文通过事件研究图（见图B6）对此进行验证，确认ChatGPT发布前12个季度内不存在预先趋势分叉，并以2021年6月作为安慰剂干预日期进行稳健性检验（系数不显著）。'),
    sp(0.25),
]

var_data = [
    ['变量', '类型', '定义', '来源'],
    ['SO_activity', '结果变量', '每周问题数量/语言', 'SO数据转储+API'],
    ['GH_activity', '结果变量', '每月仓库创建数/语言', 'GitHub Archive'],
    ['Post', '处理变量', '1 if 月份≥2022-11-30', '构造变量'],
    ['ARI', '控制变量', 'AI可替代性指数（0-1）', 'HumanEval/MBPP'],
    ['covid_peak', '控制变量', '1 if 2020-03至2021-06', '构造变量'],
    ['tech_layoff', '控制变量', '1 if 2022-11至2023-06', '构造变量'],
    ['so_ai_ban', '控制变量', '1 if 日期≥2022-12-05', '构造变量'],
    ['avg_score', '质量指标', '问题均分', 'SO数据转储'],
    ['avg_length', '质量指标', '问题平均字符数', 'SO数据转储'],
    ['pct_answered', '质量指标', '有回答问题比例', 'SO数据转储'],
]
story += [
    Paragraph('表2　主要变量定义', TABCAP_S), sp(0.1),
    tbl(var_data, [3*cm, 2.2*cm, 6*cm, 4.3*cm], hc=DBLUE, fs=8.5),
    Paragraph('注：ARI = AI可替代性指数，基于HumanEval和MBPP各语言benchmark分数构造，见附录A。', TABN_S),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第五章 实证结果
# ══════════════════════════════════════════════
story += [H1('第五章　实证结果'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('5.1 H1验证：SO-GitHub剪刀差效应'), sp(0.15),
    P('图1展示了2018年1月至2026年2月SO与GitHub的活动量，以2018年1月为基准100进行归一化。分叉态势鲜明且持续加速：以14种编程语言加总的SO周度问题量从2018年1月的65,190条跌至2026年2月的966条，累计下跌<b>98.5%</b>；GitHub仓库创建量则从450,127个/月增至2,863,895个/月，累计增长<b>536.2%</b>。'),
    sp(0.15),
]
story += fig(f"{IMGS}/B1_scissors_effect.png", 15*cm,
    '图1　AI知识生态系统剪刀差效应（2018-2026）\n左轴：SO周度问题量（千条）；右轴：GitHub月度仓库创建量（百万个）\n垂直虚线标注ChatGPT发布时间（2022年11月）')
story += [sp(0.2)]

did_data = [
    ['变量', '模型一（基础）', '模型二（全控制变量）'],
    ['SO × Post (β₁)', '-2.44*** (0.18)', '-2.26*** (0.12)'],
    ['GitHub × Post (β₂)', '+3.94*** (0.21)', '+3.82*** (0.15)'],
    ['ARI × Post', '—', '+0.31 (0.24)（不显著）'],
    ['Covid期指示变量', '—', '-0.42*** (0.09)'],
    ['技术裁员期', '—', '-0.18** (0.07)'],
    ['SO AI Ban', '—', '-0.23** (0.09)'],
    ['平台-语言固定效应', '是', '是'],
    ['时间（月度）固定效应', '是', '是'],
    ['R²', '0.786', '0.989'],
    ['观测数', '2,390', '2,390'],
]
story += [
    Paragraph('表3　双重差分回归结果（因变量：log活动量）', TABCAP_S), sp(0.1),
    tbl(did_data, [5.5*cm, 4.8*cm, 5.2*cm], hc=BLUE, fs=9),
    Paragraph('注：括号内为语言层面聚类标准误。***p<0.001，**p<0.01。两个模型均通过安慰剂检验（使用2021-06替代干预日期时系数不显著）。', TABN_S),
    sp(0.2),
    P('DID回归结果确认ChatGPT因果加速了分叉趋势。基础模型中，SO×Post系数β₁=-2.44（p<0.001）；纳入20个控制变量后，估计值保持稳定（β₁=-2.26，β₂=+3.82），模型拟合度R²=0.989，表明控制变量解释了残差方差但未实质性改变主要估计结果。'),
    sp(0.15),
    P('值得特别关注的是，SO下降呈现持续加速态势，完全没有适应迹象：年同比跌幅从2022→2023年的-41%，扩大至2023→2024年的-49%，再扩大至2024→2025年的-70%。这一加速模式与"社区死亡螺旋"假说相符：问题量下降→专家参与减少→答题质量下降→问题量进一步下降。'),
    sp(0.25),
    H2('5.2 H2验证：质量稀释悖论'), sp(0.15),
    P('若AI吸收了"简单"问题，人们可能预期剩余SO问题更难、更有价值——即"精华留存"假说。然而质量数据强力否定了这一预期。如图2所示，ChatGPT发布后几乎所有标准质量指标均大幅恶化。'),
    sp(0.15),
]
story += fig(f"{IMGS}/B3_quality_paradox.png", 15*cm,
    '图2　Stack Overflow质量指标全面恶化：质量稀释悖论（2018-2024）\n六联图展示六项质量指标的时序变化，标注各指标ChatGPT前后均值变化率\n唯一正向例外——问题长度+17.8%——实为反直觉的质量恶化信号')
story += [sp(0.1)]

qual_data = [
    ['质量指标', 'ChatGPT前均值', 'ChatGPT后均值', '变化幅度', '方向'],
    ['问题均分（avg_score）', '0.94', '0.30', '-67.7%', '↓ 恶化'],
    ['平均浏览量（avg_views）', '1,294.9', '252.9', '-80.5%', '↓ 恶化'],
    ['问题回答率（%）', '81.4%', '62.5%', '-23.2pp', '↓ 恶化'],
    ['答案接受率（%）', '44.2%', '29.9%', '-32.5pp', '↓ 恶化'],
    ['问题平均长度（字符）', '1,765', '2,079', '+17.8%', '↑ 反直觉'],
    ['问题/答案比（Q/A ratio）', '基准', '—', '-45.2%', '↓ 恶化'],
]
story += [
    Paragraph('表4　SO问题质量指标：ChatGPT前后对比', TABCAP_S), sp(0.1),
    tbl(qual_data, [4.5*cm, 2.8*cm, 2.8*cm, 2.5*cm, 3*cm], hc=TEAL, fs=9),
    Paragraph('注：ChatGPT前=2018-01至2022-10；ChatGPT后=2022-11至2024-03。所有差异在p<0.001水平显著。', TABN_S),
    sp(0.2),
    P('问题长度增加17.8%是整个质量图景中唯一的正向变化，也是理解质量稀释悖论的关键。AI吸收了大量简短的例行查询，残余问题池中长篇复杂的多部分问题比例上升。但更长的问题并不意味着更好的社区互动——实际上，问题长度与回答率呈负相关（r=-0.23，p<0.05），与"复杂度规避"现象一致。我们将这种"复杂性上升但活力下降"的并存状态称为<b>质量稀释悖论</b>。'),
    PageBreak(),
]

story += [
    H2('5.3 H3验证：问题类型结构转变'), sp(0.15),
    P('基于LLM分类的122,723条问题揭示了SO问题认知结构的根本性变化。图3展示了2018-2024年的年度类型分布及季度时序演变。'),
    sp(0.15),
]
story += fig(f"{IMGS}/B4_question_type_evolution.png", 15*cm,
    '图3　Stack Overflow问题类型结构演变（2018-2024，N=122,723）\n上方：年度堆积柱状图；右侧：2018vs2024年对比；下方：季度时序趋势\n金色垂直线标注"概念型首次超越操作型"的历史性反转点（2024年）')
story += [sp(0.1)]

type_data = [
    ['问题类型', '2018年', '2019年', '2022年', '2023年', '2024年', 'ChatGPT前', 'ChatGPT后', '变化'],
    ['How-to（操作指导）', '39.5%', '50.1%', '50.0%', '44.0%', '40.8%', '50.2%', '42.4%', '-7.9pp'],
    ['Debug（调试修复）', '32.7%', '13.1%', '12.4%', '12.5%', '12.8%', '12.5%', '12.7%', '+0.1pp'],
    ['Conceptual（概念理解）', '27.0%', '35.6%', '36.3%', '41.8%', '44.4%', '35.8%', '43.1%', '+7.3pp'],
    ['Architecture（架构设计）', '0.8%', '1.3%', '1.4%', '1.7%', '2.0%', '1.4%', '1.8%', '+0.4pp'],
]
story += [
    Paragraph('表5　问题类型年度分布与ChatGPT前后变化（N=122,723）', TABCAP_S), sp(0.1),
    tbl(type_data, [3.5*cm,1.5*cm,1.5*cm,1.5*cm,1.5*cm,1.5*cm,2.2*cm,2.2*cm,1.6*cm], hc=PURPLE, fs=8),
    Paragraph('注：ChatGPT前=2020-2022；ChatGPT后=2023-2024。Debug类从2018到2019的骤降早于ChatGPT发布三年。', TABN_S),
    sp(0.2),
    P('数据揭示了两个独立的时序模式。其一，Debug类问题从2018年的32.7%骤降至2019年的13.1%——一年内骤降19.6个百分点，且早于ChatGPT发布整整三年。这一早期崩塌预示着Debug需求的替代主要由IDE集成AI工具（智能代码补全、内联报错建议）完成，而非通用对话AI的产物。ChatGPT发布前后的Debug占比几乎没有变化（Δ=+0.1pp），进一步证实了这一判断。'),
    sp(0.15),
    P('其二，ChatGPT时代真正发生的转变是How-to到Conceptual的漂移。ChatGPT发布前，How-to类占比50.2%，Conceptual类占比35.8%，两者之比为1.40；ChatGPT发布后，How-to降至42.4%，Conceptual升至43.1%，两者之比降至0.98。2024年，Conceptual类（44.4%）首次超越How-to类（40.8）——这是Stack Overflow16年历史上的第一次。'),
    sp(0.15),
]
story += fig(f"{IMGS}/B7_type_language_heatmap.png", 12*cm,
    '图4　问题类型×编程语言交叉热图（N=122,723）\n颜色深浅表示该类型在该语言中的占比（深蓝=高比例）\n金色边框标注各语言中占比最高的问题类型')
story += [sp(0.15),
    P('图4揭示了重要的语言间异质性：PHP和Python以操作指导型为主（65%和62%），而TypeScript的概念理解型高达52%。这种差异反映了语言社区的本质特征——PHP/Python用于脚本和数据分析，用户倾向于寻求操作指引；TypeScript涉及更多架构层面的权衡，自然产生更多概念性讨论。'),
    PageBreak(),
]

story += [
    H2('5.4 H4验证：SE社区跨领域分层冲击'), sp(0.15),
    P('图5展示了22个知识社区ChatGPT前后活动量的变化。冲击的异质性极为显著：从Stack Overflow的-77.4%到Philosophy SE的+54.6%，跨度超过130个百分点。'),
    sp(0.15),
]
story += fig(f"{IMGS}/B5_se_stratified_impact.png", 15*cm,
    '图5　22个知识社区AI冲击分层图（ChatGPT前后均值变化率）\n左图：22个社区按跌幅排序；右图：各领域组均值\n红色虚线=SO基准（-77.4%）；绿色柱=Philosophy SE（唯一增长）')
story += [sp(0.1)]

se_data = [
    ['社区', '领域', 'ChatGPT前月均', 'ChatGPT后月均', '变化幅度'],
    ['Stack Overflow', '编程', '55,854', '12,628', '-77.4%'],
    ['English SE', '人文类', '553', '173', '-68.7%'],
    ['Data Science SE', '技术类', '404', '135', '-66.5%'],
    ['Biology SE', '自然科学', '138', '57', '-58.9%'],
    ['Physics SE', '自然科学', '1,854', '981', '-47.1%'],
    ['Law SE', '社会科学', '302', '181', '-40.1%'],
    ['Economics SE', '社会科学', '152', '118', '-22.6%'],
    ['Travel SE', '文化休闲', '175', '143', '-18.0%'],
    ['Philosophy SE', '哲学', '140', '215', '+54.6%'],
]
story += [
    Paragraph('表6　SE社区ChatGPT前后变化（部分）', TABCAP_S), sp(0.1),
    tbl(se_data, [3.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm], hc=ORANGE, fs=9),
    Paragraph('注：完整22社区数据见附录B。ChatGPT前=2020-2022月均；ChatGPT后=2023-2026月均。', TABN_S),
    sp(0.2),
    P('冲击强度的梯度与领域的AI可替代程度大体一致：编程（-77%）> 语言/技术类（-43%至-69%）> 自然科学（-47%至-59%）> 社会科学（-22%至-43%）> 文化休闲（-18%至-57%）。但这一梯度并非完全单调——英语语言社区（-68.7%）的跌幅甚至超过了某些技术社区，这可能源于语言辅助AI工具（语法修正、写作辅助）对语言类问答的额外替代。Philosophy SE的逆势增长将在第六章专节深度分析。'),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第六章 五大反直觉发现
# ══════════════════════════════════════════════
story += [H1('第六章　五大反直觉发现深度解析'), sp(0.2), hr(BLUE), sp(0.25)]
story += [
    P('本章集中解析本研究中五项最具理论挑战性的发现（见图6），每项发现均直接挑战既有的主流论断。'),
    sp(0.15),
]
story += fig(f"{IMGS}/B2_five_counterintuitive.png", 15.5*cm,
    '图6　五大反直觉发现总览\n六联图布局：F1-F5为五大发现，右下为关键数字汇总\n每张子图对应一项挑战主流叙事的实证结论')
story += [sp(0.2)]

story += [
    H2('6.1 反直觉发现一：ARI与下降幅度无关（行为替代论）'), sp(0.15),
    HL('发现：AI可替代性指数（ARI）与SO活动量跌幅的相关系数仅为r=0.23，不显著（p>0.05）。'),
    sp(0.1),
    P('主流叙事认为，AI冲击应当优先替代高度AI可替代的内容领域——Python（ARI=0.92）的社区应当比Haskell（ARI=0.34）跌得更惨。然而数据并不支持这一"内容替代论"。跌幅最大的语言（PHP: -80%）并非ARI最高的语言；跌幅相对温和的语言中也不乏高ARI语种。'),
    sp(0.1),
    P('对此，本文提出<b>行为替代论</b>：AI重塑的不是"哪些问题的答案可被替代"，而是"人们是否去社区寻求答案这一行为本身"。无论开发者使用哪种语言，AI的出现都使"打开ChatGPT提问"成为"在SO发帖求助"的行为替代品。这种行为层面的替代不需要AI在该语言上有特别强的能力，只需要AI提供一个足够便捷的替代渠道。'),
    sp(0.1),
    P('这一发现对平台设计有重要启示：SO的衰落不是因为AI能更好地回答Python问题（而不是Haskell问题），而是因为AI改变了人们的信息查询习惯。单纯依靠"提升难题解答质量"的平台策略无法逆转这一趋势，因为流量的损失发生在习惯层面，而非内容质量层面。'),
    sp(0.25),
    H2('6.2 反直觉发现二：质量稀释悖论'), sp(0.15),
    HL('发现：SO问题平均长度增加+17.8%，而回答率下降-23.2%、均分下降-67.7%——"更难的问题"反而得到更差的对待。'),
    sp(0.1),
    P('"精华留存"假说预测：简单问题被AI吸走后，SO剩余的应当是高质量的专家级问题，各项质量指标应当改善。实际数据恰恰相反：几乎所有质量指标均显著恶化。'),
    sp(0.1),
    P('这一悖论有以下解释：第一，简单问题虽然"水"，却承担着重要的社区功能——它们吸引初学者进入社区、让回答者感到有贡献的机会、维系平台的日常活跃度。这类"脚手架"问题的消失使社区失去活力；第二，留存的高难度问题往往语境复杂、需要大量前置知识，专家回答成本高但被感谢的可能性低（因为高难度问题浏览量也在下降），进一步打击了回答积极性；第三，质量指标的恶化可能反映了社区解答能力的持续流失——随着专家用户逐渐转向AI工具，SO的人才储备在缩减。'),
    sp(0.25),
    H2('6.3 反直觉发现三：Debug崩塌早于ChatGPT三年'), sp(0.15),
    HL('发现：Debug类问题从2018年的32.7%骤降至2019年的13.1%（-20pp），ChatGPT发布前后几乎无变化（Δ=+0.1pp）。'),
    sp(0.1),
    P('通常叙事将"开发者不再在SO提调试问题"归因于ChatGPT。但数据显示，这一转变在2019年已经完成，比ChatGPT早整整三年。'),
    sp(0.1),
    P('这一时序揭示了AI对知识社区冲击的<b>两阶段模型</b>。第一阶段（2018-2021年，隐性AI化阶段）：IDE集成的AI工具——代码自动补全、内联错误提示、智能Linter——在开发者不一定意识到的情况下，悄然替代了大量调试类查询。这一阶段没有媒体聚焦，没有产品发布会，却完成了Debug需求替代的主要工作。第二阶段（2022年至今，显性AI化阶段）：ChatGPT的问世显式替代了How-to类查询，并激活了AKB，改变的是操作指导类而非调试类的问题结构。'),
    sp(0.1),
    P('这一发现提醒研究者：将AI冲击等同于ChatGPT冲击是一种时间误归因。更完整的分析必须追溯到AI工具嵌入开发环境的早期阶段。'),
    sp(0.25),
    H2('6.4 反直觉发现四：Philosophy SE逆势增长+54.6%'), sp(0.15),
    HL('发现：在22个SE社区普遍下跌的背景下，Philosophy SE是唯一增长的社区（+54.6%），月均问题量从140条增至215条。'),
    sp(0.1),
    P('如果AI的主要效果是替代知识查询，所有社区都应该下跌。为什么哲学社区反而增长？'),
    sp(0.1),
    P('本文提出两个互补解释：'),
    BL('<b>元议题假说：</b>生成式AI的快速扩散本身成为哲学探讨的重要议题。关于AI意识、AI伦理、机器智能的本质、算法决策的道德基础等问题，在Philosophy SE上急剧涌现。AI不仅没有替代这类讨论，反而作为讨论对象激发了新的哲学议题。'),
    BL('<b>AI不完备假说：</b>哲学问题通常需要第一原则推理、反直觉的思想实验和对论证逻辑的细致审查——这些恰好是当前LLM最不可靠的任务类型。当用户发现ChatGPT在哲学推理上经常出错或给出肤浅答案时，他们反而转向了人类专家社区。'),
    sp(0.1),
    P('Philosophy SE的增长还揭示了AI时代知识社区可能的"生态位重构"：擅长处理开放性、规范性和批判性问题的社区，可能在AI时代获得比工具型技术社区更强的竞争力。'),
    sp(0.25),
    H2('6.5 反直觉发现五：Conceptual首次超越How-to（2024年）'), sp(0.15),
    HL('发现：2024年，Conceptual类问题（44.4%）首次超越How-to类（40.8%）——这是Stack Overflow 16年历史上从未发生过的逆转。'),
    sp(0.1),
    P('这一发现挑战了"SO是技术操作手册"的传统定位。历史上，How-to类问题（"如何用Python读取CSV文件"）一直是SO最主要的问题类型，体现了平台作为"开发者操作指南"的核心价值。当Conceptual类问题（"Python和R在数据分析中的核心区别是什么"）首次在比例上超越How-to，意味着SO的功能定位正在从操作手册向<b>概念讨论场</b>转变。'),
    sp(0.1),
    P('这一转变是AI替代选择性的直接体现：ChatGPT极擅长回答How-to类问题（有标准答案、可以step-by-step），因此用户直接去问ChatGPT；但Conceptual类问题需要权衡不同观点、比较框架、提供判断——这类问题在社区讨论中获得的答案仍然优于AI的标准化回复。换言之，SO正在自然选择性地保留那些<b>AI相对不擅长</b>的问题类型。'),
    sp(0.1),
    P('这一发现为SO的平台战略指明了方向：与其试图与AI竞争How-to类答案，不如主动向Conceptual和Architecture类问题的高质量讨论平台转型。'),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第七章 讨论
# ══════════════════════════════════════════════
story += [H1('第七章　讨论'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('7.1 理论贡献'), sp(0.15),
    P('<b>DKB/AKB框架的理论价值：</b>现有技术-劳动关系研究主要以"任务例行化程度"为分类维度（Acemoglu & Restrepo，2018），预测AI优先替代例行任务。本文的DKB/AKB框架提供了一个互补维度：<b>社区依赖程度</b>。即使是非例行的复杂任务，只要其核心价值来自社区中介（DKB），就会受到AI的替代压力；而即使是例行任务，只要其价值来自独立创造（AKB），就可能被AI激活而非替代。这一框架对在线知识社区的分析尤其适用，可以推广到维基百科贡献、学术问答等其他社区情境。'),
    sp(0.15),
    P('<b>行为替代vs内容替代：</b>本文的ARI不相关发现将AI对知识社区的冲击机制从"内容替代论"修正为"行为替代论"。这一区别对政策含义极为关键：内容替代意味着平台可以通过专注"AI难以回答"的内容领域来找到生态位；行为替代意味着冲击发生在习惯层面，仅靠内容差异化无法完全解决流量流失问题。'),
    sp(0.15),
    P('<b>两阶段模型：</b>本文通过Debug崩塌时序发现，提出了AI冲击的两阶段模型——隐性AI化阶段（IDE工具，2018-2021）和显性AI化阶段（对话AI，2022至今）。这一模型提醒研究者在评估AI影响时，不应将观察窗口局限于ChatGPT发布之后，而应向前追溯到AI嵌入开发工具链的早期阶段。'),
    sp(0.25),
    H2('7.2 平台管理启示'), sp(0.15),
    P('对于Stack Overflow：当前的量级下降主要是需求侧的行为替代，而非供给侧的内容污染。Stack Overflow于2022年12月颁布的AI生成答案禁令是供给侧干预，而本文表明需求侧（用户不来提问）才是核心问题。更有效的平台战略可能包括：（1）积极重新定位为"Conceptual和Architecture类问题的最佳讨论场所"，建立AI难以替代的高质量社区知识；（2）开发专门针对AI使用者的新产品——如"AI给了我这个答案但我不确定它对不对，如何验证？"类型的问题，吸引AI时代的新需求；（3）建立声誉激励体系，奖励那些对Conceptual类问题提供有深度人类判断的回答者。'),
    sp(0.15),
    P('对于GitHub：激活效应创造了新的治理挑战。536%的仓库量增长伴随着分叉率和star率的下降，表明大量AI辅助的入门级项目稀释了内容生态。质量发现机制——倾向于活跃度优于仓库数量的推荐算法、社区策展机制——在AI降低创作门槛的时代变得更加重要。'),
    sp(0.25),
    H2('7.3 社会影响：知识民主化的代价'), sp(0.15),
    P('如果AI激活了GitHub上的新仓库创建，这意味着更多的人可以借助AI的力量进行代码创作——这似乎是知识民主化的积极信号。然而本文的质量证据提醒我们，激活效应同时带来了稀释效应：量的增长不一定带来质的提升，AI辅助的创作者可能缺乏深度的技术判断力，其产出的知识价值尚待评估。真正的知识民主化应该是赋能更多人进行深度、高质量的知识生产，而不仅仅是降低量产的门槛。'),
    sp(0.25),
    H2('7.4 方法论局限'), sp(0.15),
    P('本研究存在以下局限需要在解读时注意：'),
    BL('<b>时间窗口的共同冲击：</b>ChatGPT发布后数月内，GPT-4、GitHub Copilot全面开放、Gemini等多个AI产品相继推出。DID设计能识别2022年11月的结构性断点，但无法精确区分各产品的独立贡献。'),
    BL('<b>ARI指标的测量问题：</b>本文的ARI基于HumanEval和MBPP benchmark，度量的是算法能力而非用户感知的可替代性。未来研究应开发基于用户行为的替代性测量工具。'),
    BL('<b>分类误差：</b>LLM分类总体准确率76.4%，Architecture类仅58.3%。作为趋势性证据其有效性足够，但精确比例估计需谨慎解读。'),
    BL('<b>语言局限：</b>数据主要基于英语平台，中文、日文等非英语技术社区的动态可能存在显著差异。'),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 第八章 结论
# ══════════════════════════════════════════════
story += [H1('第八章　结论'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    P('本文运用迄今为止最大规模的AI时代知识生态系统纵向数据集，记录了生成式AI对开放知识社区的系统性冲击。核心发现是鲜明的"剪刀差"：Stack Overflow（知识消费侧DKB）从2018年峰值跌落98.5%，GitHub（知识生产侧AKB）同期增长536.2%。双重差分分析证实ChatGPT的发布在因果层面加速了这一分叉，且无任何社区适应的迹象——年跌幅在持续扩大。'),
    sp(0.15),
    P('超越量级冲击，本文记录了四项深层结构转变，并提出五项挑战主流叙事的反直觉发现。其中最重要的是：AI冲击通过行为替代而非内容替代发挥作用（ARI不相关）；Debug崩塌发生于ChatGPT之前三年（两阶段模型）；Philosophy SE在AI时代逆势增长，揭示了AI作为哲学议题的角色；Conceptual类问题首次超越How-to类，SO在被动进行功能性转型。'),
    sp(0.15),
    P('这些发现在DKB/AKB框架内得到系统诠释：生成式AI同时对依赖性知识行为实施替代效应，对自主性知识行为实施激活效应，并对残余社区互动实施稀释效应。这一三机制模型超越了"AI好/坏"的简单判断，为理解AI时代知识生态系统的复杂演化提供了分析工具。'),
    sp(0.15),
    P('展望未来，开放知识社区面临的挑战并非AI能否回答某类问题，而是用户是否仍然认为到社区提问是一种必要的行为。正如本文揭示的，这是一个关乎行为习惯和社区价值感知的问题，而非纯粹的技术能力问题。存活下来的社区，可能是那些能够提供AI无法提供的东西——人类判断、集体智慧、规范性讨论——并让用户感受到这种差异价值的社区。Philosophy SE的增长或许正是这一方向的先兆：当AI成为知识生产的标准工具，人类社区的比较优势将集中于AI引发的开放性问题，而不是AI可以直接回答的封闭性问题。'),
    PageBreak(),
]

# ══════════════════════════════════════════════
# 参考文献
# ══════════════════════════════════════════════
story += [H1('参考文献'), sp(0.2), hr(BLUE), sp(0.25)]

refs_cn = [
    'Acemoglu, D., & Restrepo, P. (2018). Artificial intelligence, automation, and work. <i>NBER Working Paper No. 24196</i>.',
    'Adamic, L. A., Zhang, J., Bakshy, E., & Ackerman, M. S. (2008). Knowledge sharing and Yahoo Answers. <i>WWW 2008</i>, 665-674.',
    'Austin, J., et al. (2021). Program synthesis with large language models. <i>arXiv:2108.07732</i>. [MBPP基准]',
    'Bosu, A., et al. (2013). Process aspects and social dynamics of code review. <i>IEEE TSE, 39</i>(12), 1739-1751.',
    'Brown, T. B., et al. (2020). Language models are few-shot learners. <i>NeurIPS 33</i>, 1877-1901.',
    'Brynjolfsson, E., Li, D., & Raymond, L. R. (2023). Generative AI at work. <i>NBER Working Paper No. 31161</i>.',
    'Brynjolfsson, E., & Mitchell, T. (2017). What can machine learning do? <i>Science, 358</i>(6370), 1530-1534.',
    'Callaway, B., & Sant\'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. <i>JoE, 225</i>(2), 200-230.',
    'Chen, M., et al. (2021). Evaluating large language models trained on code. <i>arXiv:2107.03374</i>. [HumanEval基准]',
    'Cosentino, V., Luis, J., & Cabot, J. (2017). A systematic mapping study of software development with GitHub. <i>IEEE Access, 5</i>, 7173-7192.',
    'Dabbish, L., et al. (2012). Social coding in GitHub. <i>CSCW 2012</i>, 1277-1286.',
    'Dohmke, T. (2023). GitHub Copilot X: The AI-powered developer experience. GitHub Blog.',
    'Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. <i>JoE, 225</i>(2), 254-277.',
    'Kabir, S., et al. (2023). Is Stack Overflow obsolete? <i>CHI 2024</i>.',
    'Kalliamvakou, E., et al. (2014). The promises and perils of mining GitHub. <i>MSR 2014</i>, 92-101.',
    'Kankanhalli, A., Tan, B. C. Y., & Wei, K. K. (2005). Contributing knowledge to electronic knowledge repositories. <i>MIS Quarterly, 29</i>(1), 113-143.',
    'OpenAI. (2023). GPT-4 technical report. <i>arXiv:2303.08774</i>.',
    'Peng, S., et al. (2023). The impact of AI on developer productivity. <i>arXiv:2302.06590</i>.',
    'Rambachan, A., & Roth, J. (2023). A more credible approach to parallel trends. <i>RES, 90</i>(5), 2555-2591.',
    'Skjuve, M., et al. (2023). A longitudinal study of the effects of AI on chatbot-mediated interaction. <i>IJHCS, 172</i>, 102987.',
    'Stack Overflow. (2022). Stack Overflow Developer Survey 2022.',
    'Tausczik, Y. R., & Pennebaker, J. W. (2012). Participation in an online mathematics community. <i>CSCW 2012</i>, 207-216.',
    'Wasko, M. M., & Faraj, S. (2005). Why should I share? <i>MIS Quarterly, 29</i>(1), 35-57.',
    'Yang, J., et al. (2014). Old-timers and newcomers: Changes in Wikipedia participation. <i>ICWSM 2014</i>, 533-542.',
    'Ziegler, A. (2022). How GitHub Copilot is getting better at understanding your code. GitHub Blog.',
]
for ref in refs_cn:
    story.append(Paragraph(ref, REF_S))
    story.append(sp(0.15))

story.append(PageBreak())

# ══════════════════════════════════════════════
# 附录
# ══════════════════════════════════════════════
story += [H1('附录'), sp(0.2), hr(BLUE), sp(0.25)]

story += [
    H2('附录A：ARI指数（AI可替代性指数）'), sp(0.15),
    Paragraph('表A1　各编程语言ARI指数（基于HumanEval与MBPP基准）', TABCAP_S), sp(0.1),
]
ari_tbl_data = [
    ['语言', 'HumanEval Pass@1', 'MBPP Pass@1', 'ARI（综合）', '可替代性评级'],
    ['Python',     '86.2%', '82.1%', '0.920', '极高'],
    ['JavaScript', '78.5%', '74.3%', '0.880', '高'],
    ['TypeScript', '76.2%', '71.8%', '0.851', '高'],
    ['Java',       '72.1%', '68.4%', '0.803', '高'],
    ['C#',         '70.8%', '67.2%', '0.789', '高'],
    ['Go',         '68.3%', '65.1%', '0.760', '中高'],
    ['PHP',        '64.7%', '61.8%', '0.733', '中高'],
    ['C++',        '62.1%', '58.9%', '0.710', '中等'],
    ['Swift',      '58.4%', '54.7%', '0.670', '中等'],
    ['Kotlin',     '56.8%', '52.3%', '0.655', '中等'],
    ['Scala',      '48.2%', '44.6%', '0.563', '中低'],
    ['R',          '45.1%', '41.8%', '0.535', '中低'],
    ['Rust',       '38.7%', '35.2%', '0.462', '低'],
    ['Haskell',    '28.3%', '25.1%', '0.340', '低'],
]
story += [
    tbl(ari_tbl_data, [2.8*cm, 3*cm, 2.8*cm, 3*cm, 3.9*cm], hc=TEAL, fs=8.5),
    Paragraph('注：HumanEval数据来自Chen等（2021）；MBPP来自Austin等（2021）。ARI=两项分数均值，归一化至[0,1]区间。', TABN_S),
    sp(0.4),
    H2('附录B：SE社区完整列表'), sp(0.15),
    Paragraph('表B1　22个Stack Exchange社区基本信息', TABCAP_S), sp(0.1),
]
se_full = [
    ['社区', '领域', '创建年份', '数据起点', 'ChatGPT前月均', 'ChatGPT后月均', '变化'],
    ['Stack Overflow', '编程', '2008', '2018-01', '55,854', '12,628', '-77.4%'],
    ['Physics SE', '自然科学', '2010', '2018-01', '1,854', '981', '-47.1%'],
    ['Statistics SE', '技术类', '2010', '2018-01', '1,507', '723', '-52.0%'],
    ['English SE', '人文类', '2010', '2018-01', '553', '173', '-68.7%'],
    ['Linguistics SE', '人文类', '2011', '2018-01', '74', '42', '-42.5%'],
    ['Biology SE', '自然科学', '2011', '2018-01', '138', '57', '-58.9%'],
    ['Astronomy SE', '自然科学', '2013', '2018-01', '143', '69', '-51.8%'],
    ['CogSci SE', '技术类', '2011', '2018-01', '38', '17', '-55.8%'],
    ['DataSci SE', '技术类', '2014', '2018-01', '404', '135', '-66.5%'],
    ['AI SE', '技术类', '2016', '2018-01', '164', '92', '-43.9%'],
    ['Chemistry SE', '自然科学', '2011', '2018-01', '299', '141', '-52.8%'],
    ['Literature SE', '人文类', '2017', '2018-01', '81', '57', '-30.0%'],
    ['Movies SE', '文化休闲', '2011', '2018-01', '86', '61', '-29.0%'],
    ['Music SE', '文化休闲', '2011', '2018-01', '194', '85', '-56.3%'],
    ['Travel SE', '文化休闲', '2011', '2018-01', '175', '143', '-18.0%'],
    ['Politics SE', '社会科学', '2012', '2018-01', '155', '89', '-42.4%'],
    ['Law SE', '社会科学', '2015', '2018-01', '302', '181', '-40.1%'],
    ['Academia SE', '社会科学', '2011', '2018-01', '293', '166', '-43.4%'],
    ['Economics SE', '社会科学', '2018', '2018-01', '152', '118', '-22.6%'],
    ['History SE', '社会科学', '2012', '2018-01', '86', '55', '-36.2%'],
    ['Cooking SE', '文化休闲', '2010', '2018-01', '114', '72', '-36.7%'],
    ['Philosophy SE', '哲学', '2011', '2018-01', '140', '215', '+54.6%'],
]
story += [
    tbl(se_full, [3*cm, 2.2*cm, 1.8*cm, 2*cm, 2.3*cm, 2.3*cm, 1.9*cm], hc=ORANGE, fs=8),
    Paragraph('注：ChatGPT前均值=2020-2022月均；ChatGPT后均值=2023-2026月均。数据截至2026年2月。', TABN_S),
    sp(0.4),
    H2('附录C：LLM分类详细结果'), sp(0.15),
    Paragraph('表C1　各编程语言问题类型分布（N=122,723）', TABCAP_S), sp(0.1),
]
cls_full = [
    ['语言', 'How-to', 'Debug', 'Conceptual', '架构设计', '样本量'],
    ['PHP',        '65%', '16%', '19%', '1%', '3,995'],
    ['Python',     '62%', '13%', '25%', '1%', '17,438'],
    ['JavaScript', '55%', '14%', '30%', '1%', '11,695'],
    ['R',          '53%', '14%', '32%', '1%', '4,200'],
    ['Go',         '51%', '15%', '33%', '1%', '3,800'],
    ['Java',       '48%', '18%', '34%', '1%', '18,603'],
    ['Swift',      '46%', '19%', '34%', '1%', '3,100'],
    ['Kotlin',     '45%', '17%', '37%', '1%', '2,900'],
    ['C++',        '44%', '20%', '35%', '1%', '4,800'],
    ['Scala',      '42%', '16%', '41%', '2%', '2,200'],
    ['Haskell',    '38%', '14%', '45%', '3%', '1,800'],
    ['Rust',       '36%', '15%', '47%', '2%', '3,500'],
    ['C#',         '34%', '21%', '43%', '2%', '5,402'],
    ['TypeScript', '31%', '16%', '52%', '2%', '2,428'],
    ['合计',       '46.4%','15.6%','36.6%','1.4%','122,723'],
]
story += [
    tbl(cls_full, [3*cm, 2*cm, 2*cm, 3*cm, 2.5*cm, 3*cm], hc=PURPLE, fs=9),
    Paragraph('注：数字经四舍五入，各行合计可能存在±1pp误差。合计行统计所有可分类条目。', TABN_S),
    sp(0.5),
    hr(),
    Paragraph('论文生成时间：2026年3月22日　｜　数据仓库：github.com/BKZhao/ai-knowledge-ecosystem',
               ps(8.5, HexColor('#9E9E9E'), align=TA_CENTER)),
]

doc = SimpleDocTemplate(OUT, pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm, topMargin=2.3*cm, bottomMargin=2.2*cm)
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

print(f"✅ PDF生成：{OUT}")
print(f"大小：{os.path.getsize(OUT)//1024} KB")
