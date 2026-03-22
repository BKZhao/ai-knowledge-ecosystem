"""
完整版研究进度报告 PDF - 2026-03-22（含LLM分类深度分析）
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image, PageBreak,
                                 KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import os, json, pandas as pd, numpy as np
import pyarrow.parquet as pq

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT  = f"{BASE}/results/研究进度完整报告_20260322.pdf"

BLUE   = HexColor('#1565C0')
DBLUE  = HexColor('#0D47A1')
GREEN  = HexColor('#2E7D32')
RED    = HexColor('#C62828')
PURPLE = HexColor('#6A1B9A')
ORANGE = HexColor('#E65100')
LGRAY  = HexColor('#F5F5F5')
MGRAY  = HexColor('#E0E0E0')
DGRAY  = HexColor('#424242')
TEAL   = HexColor('#00695C')

doc = SimpleDocTemplate(OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2.2*cm, bottomMargin=2*cm)

styles = getSampleStyleSheet()
normal = styles['Normal']

def H1(t, c=DBLUE):
    return Paragraph(f'<font color="{c.hexval()}" size="17"><b>{t}</b></font>', normal)
def H2(t, c=BLUE):
    return Paragraph(f'<font color="{c.hexval()}" size="12"><b>{t}</b></font>', normal)
def H3(t, c=DGRAY):
    return Paragraph(f'<font color="{c.hexval()}" size="10.5"><b>{t}</b></font>', normal)
def P(t, s=9.5, bold=False):
    tag = 'b' if bold else 'font'
    return Paragraph(f'<{tag} size="{s}">{t}</{tag}>', normal)
def BL(t, s=9.5):
    return Paragraph(f'<font size="{s}">　• {t}</font>', normal)
def sp(h=0.3): return Spacer(1, h*cm)
def hr(c=MGRAY): return HRFlowable(width="100%", thickness=0.5, color=c, spaceAfter=5, spaceBefore=5)

CENTER = ParagraphStyle('c', parent=normal, alignment=TA_CENTER)
JUSTIFY_S = ParagraphStyle('j', parent=normal, alignment=TA_JUSTIFY, fontSize=9.5, leading=14)

story = []

# ══════════════════════════════════════════
# 封面
# ══════════════════════════════════════════
story += [
    sp(2.5),
    Paragraph('<font size="22" color="#0D47A1"><b>AI Impact on Knowledge Ecosystems</b></font>', CENTER),
    sp(0.4),
    Paragraph('<font size="15" color="#424242"><b>研究完整进度报告</b></font>', CENTER),
    sp(0.2),
    Paragraph('<font size="11" color="#757575">Complete Research Progress Report — 2026-03-22</font>', CENTER),
    sp(0.5),
    HRFlowable(width="55%", thickness=2.5, color=BLUE, hAlign='CENTER'),
    sp(0.5),
    Paragraph('<font size="10.5" color="#424242">赵炳坤（Bingkun Zhao）</font>', CENTER),
    Paragraph('<font size="10" color="#616161">City University of Hong Kong</font>', CENTER),
    sp(3),
]

# 快速摘要box
summary_data = [
    ['📊 数据规模', '💡 核心发现', '⏳ 当前进度'],
    [
        '• SO: 424周×14语言\n• GitHub: 98月×13语言\n• SE: 21社区×2026-02\n• LLM分类: 112,431条\n• 质量指标: 950万帖子',
        '• SO -75.3% vs GitHub +121%\n• DID β₁=-2.26*** β₂=+3.82***\n• Debug: 33%→13% (早于ChatGPT)\n• Conceptual: +7.3pp (ChatGPT后)\n• Philosophy SE唯一上升 +54%',
        '• 数据采集: ✅ 完成\n• DID分析: ✅ 完成\n• LLM分类: 112k完成\n• 200k续跑: ⏳ 暂停(API)\n• 论文写作: 🔄 进行中'
    ]
]
st = Table(summary_data, colWidths=[5.2*cm, 6*cm, 4.3*cm])
st.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DBLUE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,0), 10),
    ('FONTSIZE',   (0,1), (-1,-1), 8.5),
    ('BACKGROUND', (0,1), (-1,-1), LGRAY),
    ('GRID', (0,0), (-1,-1), 0.4, MGRAY),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ('LEFTPADDING', (0,0), (-1,-1), 8),
    ('ALIGN', (0,0), (-1,0), 'CENTER'),
]))
story += [st, PageBreak()]

# ══════════════════════════════════════════
# 第1章：数据集
# ══════════════════════════════════════════
story += [H1("第一章　数据集说明"), sp(0.2), hr(BLUE), sp(0.3)]

story += [
    H2("1.1 Stack Overflow 主数据集"),
    sp(0.15),
    BL("来源：Stack Overflow Data Dump (2024-04) + Stack Exchange API实时补充"),
    BL("原始规模：Posts.xml 97GB → 过滤处理 → posts_2018plus.parquet 497MB"),
    BL("周度时序：<b>424周 × 14编程语言</b>，时间范围 2018-01 ~ 2026-02"),
    BL("14语言：Python, JavaScript, TypeScript, Java, C#, PHP, C++, Swift, Kotlin, Go, Rust, Scala, Haskell, R"),
    BL("质量指标（月度）：avg_score, avg_views, pct_answered, pct_accepted, avg_length, active_users"),
    sp(0.35),
    H2("1.2 GitHub 数据集"),
    sp(0.15),
    BL("来源：GitHub Archive API"),
    BL("<b>13编程语言 × 98个月</b>（2018-01 ~ 2026-02）"),
    BL("指标：新建仓库数、活跃仓库率（有commit的%）、fork率、star率、Issue/仓库比"),
    sp(0.35),
    H2("1.3 Stack Exchange 跨领域社区数据集"),
    sp(0.15),
    BL("来源：SE Data Dump（21个社区）+ SE API（2024-04~2026-02，23个月补充）"),
    BL("覆盖范围：完整覆盖至 <b>2026-02</b>（本轮已补全）"),
    sp(0.15),
]

se_group = [
    ['分组', '社区', '特征'],
    ['技术类', 'Physics, Stats, DataSci, AI.SE', '与编程/AI强相关'],
    ['人文类', 'English, Linguistics, Literature', '语言文学类'],
    ['社会科学', 'Politics, Law, Economics, Academia', '社会人文类'],
    ['自然科学', 'Biology, Chemistry, Astronomy', '传统科学类'],
    ['文化休闲', 'Music, Movies, Travel, Cooking', '娱乐生活类'],
    ['哲学', 'Philosophy', '唯一显著上升社区（+54.6%）'],
]
gt = Table(se_group, colWidths=[2.5*cm, 7*cm, 6*cm])
gt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), TEAL),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (0,-1), 6),
    ('BACKGROUND', (0,6), (-1,6), HexColor('#E8F5E9')),
    ('TEXTCOLOR', (0,6), (-1,6), GREEN),
]))
story += [gt, sp(0.35)]

story += [
    H2("1.4 LLM 问题类型分类数据集"),
    sp(0.15),
    BL("分类工具：<b>DeepSeek-V3</b>（硅基流动API）"),
    BL("总量：<b>112,431条</b>已完成（第1批100k + 第2批14.4k）"),
    BL("类别定义："),
    Paragraph('　　　<font size="9">1 = <b>How-to</b>：如何做某事，有明确步骤答案</font>', normal),
    Paragraph('　　　<font size="9">2 = <b>Debug</b>：调试具体错误，有报错信息</font>', normal),
    Paragraph('　　　<font size="9">3 = <b>Conceptual</b>：概念理解、比较、解释</font>', normal),
    Paragraph('　　　<font size="9">4 = <b>Architecture</b>：架构设计、最佳实践</font>', normal),
]

cls_dist = [
    ['类别', '数量', '比例', '2018年', '2024年', '变化'],
    ['How-to',       '52,206', '46.4%', '39.5%', '40.8%', '-8pp (ChatGPT后)'],
    ['Conceptual',   '41,173', '36.6%', '27.0%', '44.4%', '+7pp (ChatGPT后)'],
    ['Debug',        '17,457', '15.5%', '32.7%', '12.8%', '早期已崩塌'],
    ['Architecture',  '1,595',  '1.4%',  '0.8%',  '2.0%', '缓慢增长'],
]
ct = Table(cls_dist, colWidths=[3*cm, 2.3*cm, 1.8*cm, 1.8*cm, 1.8*cm, 4.8*cm])
ct.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), PURPLE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (0,-1), 6),
    ('BACKGROUND', (0,3), (-1,3), HexColor('#FFF3E0')),
]))
story += [sp(0.2), ct, PageBreak()]

# ══════════════════════════════════════════
# 第2章：核心发现
# ══════════════════════════════════════════
story += [H1("第二章　核心发现"), sp(0.2), hr(BLUE), sp(0.2)]

# 发现1
story += [
    H2("发现1：SO提问行为崩塌，GitHub仓库创建激增", GREEN),
    sp(0.15),
    Paragraph('<font size="9.5">这是研究最核心的"剪刀差"现象，两者在ChatGPT后走向分叉：</font>', normal),
    sp(0.1),
]
f1_data = [
    ['指标', '2018基准', '2026-02', '变化幅度', 'DID系数'],
    ['SO提问量 (14语言合计)', '100', '24.7', '<b>-75.3%</b>', 'β₁ = -2.26***'],
    ['GitHub仓库创建', '100', '221.1', '<b>+121.1%</b>', 'β₂ = +3.82***'],
    ['SO活跃用户数', '—', '—', '-34.7%', '—'],
    ['SO avg_score', '—', '—', '-60.6%', '—'],
    ['GitHub活跃仓库率', '—', '—', '+0.3pp', '—（稳定）'],
]
t1 = Table(f1_data, colWidths=[5.5*cm, 2.3*cm, 2.3*cm, 2.5*cm, 2.9*cm])
t1.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), GREEN),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#E8F5E9')]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (0,-1), 6),
]))
story += [t1, sp(0.2),
    BL("冲击持续加速（无适应期）：2022→2023: -41%, 2023→2024: -49%, 2024→2025: -70%"),
    BL("Ruby异常：SO和GitHub同时下跌（SO -84%, GitHub -60%），语言本身在衰退"),
    sp(0.4),
]

# 发现2
story += [
    H2("发现2：问题类型结构转变——两个独立机制", PURPLE),
    sp(0.1),
    H3("机制A：Debug崩塌（早期，与ChatGPT无关）"),
    sp(0.1),
    BL("Debug占比：<b>2018年32.7% → 2019年13.1%</b>（骤降19.6pp，仅一年！）"),
    BL("2019年后：Debug稳定在12-13%，ChatGPT前后几乎无变化（Δ = +0.1pp）"),
    BL("解读：早期AI辅助工具（IDE智能提示、GitHub Copilot前身等）已大幅吸收Debug需求"),
    BL("含义：Debug崩塌是<b>渐进AI化</b>的结果，不是ChatGPT突变的证据"),
    sp(0.2),
    H3("机制B：How-to→Conceptual转移（ChatGPT后，持续进行）"),
    sp(0.1),
    BL("ChatGPT前(2020-22)：How-to 50.2% vs Conceptual 35.8%，比率1.40"),
    BL("ChatGPT后(2023-24)：How-to 42.4% vs Conceptual 43.1%，比率0.98"),
    BL("<b>How-to首次被Conceptual超越</b>（2024年：40.8% vs 44.4%）"),
    BL("解读：ChatGPT替代了有明确答案的操作类问题，留下了需要人类判断的概念类讨论"),
    sp(0.2),
]

# 语言差异
lang_data = [
    ['语言', '样本量', 'How-to', 'Debug', 'Conceptual', '特征'],
    ['PHP',        '3,995', '65%', '16%', '19%', '操作型为主，较低概念深度'],
    ['Python',    '17,438', '62%', '13%', '25%', '脚本/数据分析，操作导向'],
    ['JavaScript','11,695', '55%', '14%', '30%', '均衡'],
    ['Java',      '18,603', '48%', '18%', '34%', 'Debug比例较高'],
    ['C#',         '5,402', '34%', '21%', '43%', '概念与架构讨论多'],
    ['TypeScript', '2,428', '31%', '16%', '52%', '最高Conceptual比例'],
]
lt = Table(lang_data, colWidths=[2.8*cm, 2*cm, 1.8*cm, 1.8*cm, 2.8*cm, 4.3*cm])
lt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), PURPLE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#F3E5F5')]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ('ALIGN', (5,1), (5,-1), 'LEFT'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('LEFTPADDING', (0,0), (0,-1), 6),
    ('LEFTPADDING', (5,0), (5,-1), 4),
]))
story += [H3("各语言问题类型分布（112k样本）"), sp(0.15), lt, sp(0.3)]

# 发现3
story += [
    H2("发现3：SE跨领域分层效应——选择性冲击", ORANGE),
    sp(0.1),
    BL("冲击强度与<b>AI可替代性正相关</b>，与编程的关联度越高，下降越快"),
    sp(0.1),
]

se_change = [
    ['社区', '下降幅度', '分组', '解读'],
    ['Stack Overflow', '-77.4%', '编程', '最大冲击：编程问答最易被AI替代'],
    ['English SE',     '-68.7%', '人文', '语言类也高度可被AI替代'],
    ['DataSci SE',     '-66.5%', '技术', '数据科学同步崩塌'],
    ['Biology SE',     '-58.9%', '科学', '事实类问题AI可直接回答'],
    ['Physics SE',     '-47.1%', '科学', '物理推导较难被完全替代'],
    ['Law SE',         '-40.1%', '社科', '法律有情境依赖，较抗跌'],
    ['Economics SE',   '-22.6%', '社科', '宏观分析难以直接替代'],
    ['Travel SE',      '-18.0%', '文化', '个人经验/时效性信息抗跌'],
    ['Philosophy SE',  '+54.6%', '哲学', '⚡唯一上升！AI引发哲学大讨论'],
]
set_t = Table(se_change, colWidths=[3.5*cm, 2.5*cm, 2.2*cm, 7.3*cm])
set_t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), ORANGE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#FFF3E0')]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (2,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('LEFTPADDING', (0,0), (0,-1), 6),
    # 最后行高亮
    ('BACKGROUND', (0,-1), (-1,-1), HexColor('#E8F5E9')),
    ('TEXTCOLOR', (0,-1), (-1,-1), GREEN),
    # SO行高亮
    ('BACKGROUND', (0,1), (-1,1), HexColor('#FFEBEE')),
    ('TEXTCOLOR', (1,1), (1,1), RED),
]))
story += [set_t, PageBreak()]

# ══════════════════════════════════════════
# 第3章：理论框架与因果识别
# ══════════════════════════════════════════
story += [H1("第三章　理论框架与方法"), sp(0.2), hr(BLUE), sp(0.2)]

story += [
    H2("3.1 理论框架：DKB vs AKB（V3）"),
    sp(0.1),
    Paragraph('<font size="9.5">本研究提出<b>依赖性知识行为（Dependent Knowledge Behavior, DKB）</b>与<b>自主性知识行为（Autonomous Knowledge Behavior, AKB）</b>的分析框架：</font>', JUSTIFY_S),
    sp(0.15),
]
dkb_data = [
    ['', 'DKB（被AI替代）', 'AKB（被AI激活）'],
    ['定义', '需要他人协助，依赖社区解答', '主动创造，AI降低门槛'],
    ['代表行为', 'SO提问、GitHub Issue', 'GitHub仓库创建、Conceptual讨论'],
    ['实证结果', '-75.3% (SO), Debug -20pp', '+121% (GitHub), Conceptual +7pp'],
    ['机制', '替代效应：AI直接回答', '激活效应：AI赋能创作'],
]
dt = Table(dkb_data, colWidths=[2.5*cm, 6.5*cm, 6.5*cm])
dt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), TEAL),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('BACKGROUND', (0,0), (0,-1), HexColor('#E0F2F1')),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING', (0,0), (-1,-1), 6),
    ('FONTSIZE', (0,0), (0,-1), 9),
    ('TEXTCOLOR', (0,1), (0,-1), TEAL),
]))
story += [dt, sp(0.3),
    H2("3.2 三大机制"),
    sp(0.1),
    BL("<b>替代效应</b>：AI直接回答Debug/How-to类确定性问题，减少SO求助行为"),
    BL("<b>激活效应</b>：AI降低代码创作门槛，激发GitHub仓库数量增长"),
    BL("<b>稀释效应</b>：量增质降——GitHub fork率/star率下降，内容同质化"),
    sp(0.3),
    H2("3.3 DID设计"),
    sp(0.1),
    BL("处理组：Stack Overflow（直接竞争者）"),
    BL("控制组：GitHub（受益者）"),
    BL("时间断点：ChatGPT发布（2022-11-30）"),
    BL("控制变量：20个（Covid期、技术裁员潮、SO AI Ban、语言ARI指数等）"),
    BL("结果：β₁(SO×Post) = <b>-2.26***</b>, β₂(GitHub×Post) = <b>+3.82***</b>，p<0.001"),
    sp(0.3),
    H2("3.4 方法论局限（需在论文中明确讨论）"),
    sp(0.1),
    BL("ARI指数为主观打分（Python=0.92...Rust=0.35），需用HumanEval benchmark替代"),
    BL("GitHub因果识别：平台本身也在增长，β₂识别需加反事实论证"),
    BL("LLM分类误差（~32% F1 on Debug类），结论应作为趋势性而非精确性证据"),
    BL("SE数据2024年后覆盖不完整（仅API公开数据，无Data Dump）"),
    PageBreak(),
]

# ══════════════════════════════════════════
# 第4章：下一步
# ══════════════════════════════════════════
story += [H1("第四章　待完成事项与时间线"), sp(0.2), hr(BLUE), sp(0.2)]

todo_data = [
    ['优先', '任务', '预估时间', '说明'],
    ['🔴', 'API充值，续跑200k分类', '1天', '硅基流动余额充值后自动续跑'],
    ['🔴', '整合分类图表进正式报告', '0.5天', '将C1-C3图嵌入论文章节'],
    ['🔴', 'ARI指数替换为benchmark', '1天', '拉取HumanEval/MBPP各语言成绩'],
    ['🟡', '因果识别强化', '2天', '加合成控制法（Synthetic Control）'],
    ['🟡', '稳健性检验', '1天', '变更窗口期、排除Covid年份'],
    ['🟡', '英文论文初稿', '5天', '按Nature格式，~6000词'],
    ['🟢', 'Math SE单独章节', '0.5天', '纯学术社区对照，已有数据'],
    ['🟢', '投稿材料准备', '2天', 'Nature Human Behaviour / PNAS'],
]
tt = Table(todo_data, colWidths=[1.2*cm, 6.5*cm, 2.3*cm, 5.5*cm])
tt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DGRAY),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ('ALIGN', (2,0), (2,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING', (1,0), (1,-1), 6),
]))
story += [tt, sp(0.5)]

# 图表清单
story += [H2("图表产出清单（已完成）"), sp(0.15)]
fig_data = [
    ['目录', '文件', '内容'],
    ['pub_final/', 'A1_so_collapse.png', 'SO崩塌四联图（量+质+社区+用户）'],
    ['pub_final/', 'A2_github_paradox.png', 'GitHub质量悖论六联图'],
    ['pub_final/', 'A3_five_findings.png', '五个反直觉发现六联图（核心）'],
    ['pub_final/', 'A4_causal.png', '因果识别三联图'],
    ['pub_final/', 'A5_se_compare.png', 'SE社区对照四联图'],
    ['pub_final/', 'A6_classification_baseline.png', '分类基线分析'],
    ['pub_classification/', 'C1_type_distribution.png', '问题类型年度分布（堆积图+趋势）'],
    ['pub_classification/', 'C2_howto_conceptual.png', 'How-to vs Conceptual比率变化'],
    ['pub_classification/', 'C3_annual_grouped.png', '年度分组柱状图'],
    ['pub_se_update/', 'SE1_community_groups.png', 'SE社区分组时序（2018-2026完整版）'],
    ['pub_se_update/', 'SE2_impact_heatmap.png', '22社区ChatGPT影响热图'],
    ['pub_se_update/', 'SE3_so_vs_nontech.png', 'SO vs 非技术SE双轴对比'],
]
figt = Table(fig_data, colWidths=[3.5*cm, 5.5*cm, 6.5*cm])
figt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), BLUE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
]))
story += [figt, sp(0.5)]

# 页脚
story += [
    hr(),
    Paragraph(f'<font size="8" color="#9E9E9E">生成时间：2026-03-22 | '
              'GitHub: BKZhao/ai-knowledge-ecosystem | '
              'Total data points: ~500M+</font>',
              ParagraphStyle('footer', parent=normal, alignment=TA_CENTER))
]

doc.build(story)
print(f"✅ PDF生成：{OUT}")
import os
print(f"文件大小：{os.path.getsize(OUT)/1024:.0f} KB")
