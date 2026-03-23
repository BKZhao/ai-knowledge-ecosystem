"""
研究进度完整报告 - 中文修复版（使用WQY字体）
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

pdfmetrics.registerFont(TTFont('WQY', '/home/node/.fonts/wqy-microhei.ttc', subfontIndex=0))

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT  = f"{BASE}/results/研究进度完整报告_20260322_v2.pdf"

DBLUE  = HexColor('#0D47A1'); BLUE = HexColor('#1565C0')
GREEN  = HexColor('#2E7D32');  RED  = HexColor('#C62828')
PURPLE = HexColor('#6A1B9A'); ORANGE= HexColor('#E65100')
LGRAY  = HexColor('#F5F5F5'); MGRAY = HexColor('#E0E0E0')
DGRAY  = HexColor('#424242'); TEAL  = HexColor('#00695C')

doc = SimpleDocTemplate(OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm, topMargin=2.2*cm, bottomMargin=2*cm)

def st(size=10, color=black, bold=False, align=TA_LEFT):
    return ParagraphStyle('x', fontName='WQY', fontSize=size,
        textColor=color, alignment=align, leading=size*1.5)

def H1(t, c=DBLUE):  return Paragraph(t, st(17, c, True))
def H2(t, c=BLUE):   return Paragraph(t, st(12, c, True))
def H3(t, c=DGRAY):  return Paragraph(t, st(10.5, c, True))
def P(t, s=9.5, c=black): return Paragraph(t, st(s, c))
def BL(t):           return Paragraph(f'　• {t}', st(9.5))
def sp(h=0.3):       return Spacer(1, h*cm)
def hr(c=MGRAY):     return HRFlowable(width="100%", thickness=0.5, color=c, spaceAfter=4, spaceBefore=4)

def tbl(data, cw, hc=DBLUE):
    t = Table(data, colWidths=cw)
    cmds = [
        ('BACKGROUND', (0,0), (-1,0), hc),
        ('TEXTCOLOR',  (0,0), (-1,0), white),
        ('FONTNAME',   (0,0), (-1,-1), 'WQY'),
        ('FONTSIZE',   (0,0), (-1,0), 9.5),
        ('FONTSIZE',   (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (0,-1), 7),
    ]
    t.setStyle(TableStyle(cmds))
    return t

story = []

# ══ 封面 ══
story += [
    sp(2.5),
    Paragraph('AI Impact on Knowledge Ecosystems', st(22, DBLUE, True, TA_CENTER)),
    sp(0.4),
    Paragraph('研究完整进度报告', st(15, DGRAY, True, TA_CENTER)),
    sp(0.2),
    Paragraph('Complete Research Progress Report — 2026-03-22', st(11, HexColor('#757575'), align=TA_CENTER)),
    sp(0.5),
    HRFlowable(width="55%", thickness=2.5, color=BLUE, hAlign='CENTER'),
    sp(0.5),
    Paragraph('赵炳坤（Bingkun Zhao）', st(10.5, DGRAY, align=TA_CENTER)),
    Paragraph('City University of Hong Kong', st(10, HexColor('#616161'), align=TA_CENTER)),
    sp(2),
]

ov = [
    ['模块', '状态', '完成度'],
    ['SO周度数据 (14语言×424周)', '✅ 完成', '100%'],
    ['GitHub月度数据 (13语言×98月)', '✅ 完成', '100%'],
    ['SE社区数据 (21社区×至2026-02)', '✅ 完成', '100%'],
    ['SO质量指标 (950万帖子)', '✅ 完成', '100%'],
    ['LLM问题分类 (DeepSeek-V3)', '✅ 完成', '112,431条'],
    ['DID主回归分析', '✅ 完成', 'β₁=-2.26*** β₂=+3.82***'],
    ['SE跨领域对比分析', '✅ 完成', '22个社区'],
    ['问题类型时序分析', '✅ 完成', '4类×7年'],
    ['论文图表生成', '✅ 完成', '15+张'],
    ['200k续跑分类', '⏳ 暂停', 'API余额不足（需充值）'],
]
story += [tbl(ov, [9.5*cm, 3*cm, 3.5*cm]), PageBreak()]

# ══ 第一章 ══
story += [H1('第一章　数据集说明'), sp(0.2), hr(BLUE), sp(0.2)]
story += [
    H2('1.1 Stack Overflow 主数据集'), sp(0.15),
    BL('来源：SO Data Dump (2024-04) + SE API补充'),
    BL('原始规模：Posts.xml 97GB → posts_2018plus.parquet 497MB'),
    BL('周度时序：424周 × 14编程语言，2018-01 ~ 2026-02'),
    BL('14语言：Python, JavaScript, TypeScript, Java, C#, PHP, C++, Swift, Kotlin, Go, Rust, Scala, Haskell, R'),
    BL('质量指标（月度）：avg_score, avg_views, pct_answered, pct_accepted, avg_length, active_users'),
    sp(0.25),
    H2('1.2 GitHub 数据集'), sp(0.15),
    BL('13编程语言 × 98个月（2018-01 ~ 2026-02）'),
    BL('指标：新建仓库数、活跃仓库率、fork率、star率、Issue/仓库比'),
    sp(0.25),
    H2('1.3 Stack Exchange 跨领域社区数据集'), sp(0.15),
    BL('21个社区，完整覆盖至 2026-02（本轮已补全23个月）'),
]

seg = [
    ['分组', '社区', 'ChatGPT后均值变化'],
    ['技术类', 'Physics, Stats, DataSci, AI.SE', '-47% ~ -67%'],
    ['人文类', 'English, Linguistics, Literature', '-31% ~ -69%'],
    ['社会科学', 'Politics, Law, Economics, Academia', '-22% ~ -43%'],
    ['自然科学', 'Biology, Chemistry, Astronomy', '-52% ~ -59%'],
    ['文化休闲', 'Music, Movies, Travel, Cooking', '-18% ~ -56%'],
    ['哲学（特殊）', 'Philosophy', '⚡ +54.6%（唯一上升）'],
]
sgt = tbl(seg, [2.8*cm, 6.8*cm, 4*cm], TEAL)
sgt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), TEAL),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTNAME',   (0,0), (-1,-1), 'WQY'),
    ('FONTSIZE',   (0,0), (-1,0), 9.5),
    ('FONTSIZE',   (0,1), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (0,-1), 7),
    ('BACKGROUND', (0,6), (-1,6), HexColor('#E8F5E9')),
    ('TEXTCOLOR', (0,6), (-1,6), GREEN),
]))
story += [sp(0.15), sgt, sp(0.25)]

story += [
    H2('1.4 LLM 问题类型分类数据集'), sp(0.15),
    BL('分类工具：DeepSeek-V3（硅基流动API），约$0.001/条'),
    BL('总量：112,431条已完成（第1批100k + 第2批14k，余额耗尽暂停）'),
    BL('分类定义：1=How-to / 2=Debug / 3=Conceptual / 4=Architecture'),
]
cls = [
    ['类别', '数量', '比例', '2018年', '2024年', '变化说明'],
    ['How-to',       '52,206', '46.4%', '39.5%', '40.8%', 'ChatGPT后 -7.9pp'],
    ['Conceptual',   '41,173', '36.6%', '27.0%', '44.4%', 'ChatGPT后 +7.3pp ↑'],
    ['Debug',        '17,457', '15.5%', '32.7%', '12.8%', '2019年已崩塌 (-20pp)'],
    ['Architecture',  '1,595',  '1.4%',  '0.8%',  '2.0%', '缓慢增长'],
]
story += [sp(0.15), tbl(cls, [2.8*cm, 2*cm, 1.7*cm, 1.7*cm, 1.7*cm, 4.6*cm], PURPLE), PageBreak()]

# ══ 第二章 ══
story += [H1('第二章　核心发现'), sp(0.2), hr(BLUE), sp(0.2)]

story += [H2('发现1：SO崩塌 + GitHub激增（剪刀差效应）', GREEN), sp(0.15)]
f1 = [
    ['指标', '2018基准', '2026-02', '变化幅度', 'DID系数'],
    ['SO提问量 (14语言合计)', '100', '24.7', '-75.3%', 'β₁ = -2.26***'],
    ['GitHub仓库创建', '100', '221.1', '+121.1%', 'β₂ = +3.82***'],
    ['SO活跃用户数', '—', '—', '-34.7%', '—'],
    ['GitHub fork率', '—', '—', '-7.9pp', '稀释效应'],
]
story += [tbl(f1, [5.5*cm, 2.2*cm, 2.2*cm, 2.2*cm, 3.4*cm], GREEN),
    sp(0.15),
    BL('冲击持续加速：2022→23: -41%, 2023→24: -49%, 2024→25: -70%（无适应期）'),
    sp(0.3),
    H2('发现2：问题类型结构转变——两个独立机制', PURPLE), sp(0.15),
    H3('机制A：Debug崩塌（早于ChatGPT，2018→2019年）'), sp(0.1),
    BL('Debug占比：2018年32.7% → 2019年13.1%（一年骤降19.6pp！）'),
    BL('ChatGPT前后变化：仅 +0.1pp → 与ChatGPT无关'),
    BL('解读：早期IDE/AI工具已吸收Debug需求，这是渐进AI化的结果'),
    sp(0.15),
    H3('机制B：How-to→Conceptual转移（ChatGPT后）'), sp(0.1),
    BL('ChatGPT前：How-to 50.2% vs Conceptual 35.8%，比率1.40'),
    BL('ChatGPT后：How-to 42.4% vs Conceptual 43.1%，比率0.98'),
    BL('2024年：Conceptual首次超过How-to（44.4% vs 40.8%）'),
    BL('解读：ChatGPT替代确定性操作问题，留下需要人类判断的概念讨论'),
    sp(0.25),
]

lang_d = [
    ['语言', '样本量', 'How-to', 'Debug', 'Conceptual', '特征'],
    ['PHP',         '3,995', '65%', '16%', '19%', '操作型，低概念深度'],
    ['Python',     '17,438', '62%', '13%', '25%', '脚本/数据分析导向'],
    ['JavaScript', '11,695', '55%', '14%', '30%', '均衡'],
    ['Java',       '18,603', '48%', '18%', '34%', 'Debug比例偏高'],
    ['C#',          '5,402', '34%', '21%', '43%', '概念/架构讨论多'],
    ['TypeScript',  '2,428', '31%', '16%', '52%', '最高Conceptual比例'],
]
story += [H3('各语言问题类型分布（112k样本）'), sp(0.15),
    tbl(lang_d, [2.8*cm, 2*cm, 1.8*cm, 1.8*cm, 2.8*cm, 4.3*cm], PURPLE), sp(0.3)]

story += [
    H2('发现3：SE跨领域分层冲击', ORANGE), sp(0.15),
    BL('冲击强度与AI可替代性正相关'),
    BL('Philosophy SE唯一逆势上升（+54.6%）——AI引发了哲学大讨论'),
    BL('Travel SE最抗跌（-18%）——个人经验/时效信息难被替代'),
    sp(0.2),
    H2('发现4：质量稀释效应', ORANGE), sp(0.15),
    BL('GitHub量增质降：fork率-7.9pp，star率-7.8pp，Issue/仓库比-35%'),
    BL('SO：avg_score -60.6%，avg_length +16%（反直觉——简单问题消失）'),
    PageBreak()
]

# ══ 第三章 ══
story += [H1('第三章　理论框架与方法'), sp(0.2), hr(BLUE), sp(0.2)]
dkb = [
    ['', 'DKB（依赖性知识行为，被AI替代）', 'AKB（自主性知识行为，被AI激活）'],
    ['定义', '需要他人协助，依赖社区解答', '主动创造，AI降低门槛'],
    ['代表行为', 'SO提问、GitHub Issue', 'GitHub仓库创建、Conceptual讨论'],
    ['实证结果', '-75.3% (SO), Debug -20pp', '+121% (GitHub), Conceptual +7pp'],
    ['机制', '替代效应', '激活效应'],
]
story += [
    H2('3.1 核心理论：DKB vs AKB 框架（V3）'), sp(0.15),
    tbl(dkb, [2.3*cm, 7.2*cm, 6*cm], TEAL), sp(0.25),
    H2('3.2 DID设计'), sp(0.1),
    BL('处理组：Stack Overflow | 控制组：GitHub | 断点：ChatGPT发布（2022-11-30）'),
    BL('控制变量：20个（Covid、技术裁员、SO AI Ban、语言ARI等）'),
    BL('结果：β₁(SO×Post) = -2.26***，β₂(GitHub×Post) = +3.82***，p<0.001'),
    sp(0.25),
    H2('3.3 方法论局限'), sp(0.1),
    BL('ARI指数主观打分 → 待用HumanEval/MBPP benchmark替代'),
    BL('GitHub因果：需加合成控制法反事实论证'),
    BL('LLM分类误差（Debug类F1约32%），结论为趋势性证据'),
    PageBreak()
]

# ══ 第四章 ══
story += [H1('第四章　待完成事项'), sp(0.2), hr(BLUE), sp(0.2)]
todo = [
    ['优先级', '任务', '预估', '说明'],
    ['🔴 高', '硅基流动API充值，续跑200k分类', '1天', '充值后后台自动恢复'],
    ['🔴 高', '整合分类图表C1-C3进论文', '0.5天', '已生成，待嵌入'],
    ['🔴 高', 'ARI替换为HumanEval benchmark', '1天', '方法论强化'],
    ['🟡 中', '因果识别强化（合成控制法）', '2天', '应对审稿人质疑'],
    ['🟡 中', '稳健性检验（变更窗口期）', '1天', ''],
    ['🟡 中', '英文论文初稿', '5天', 'Nature Human Behaviour / PNAS'],
    ['🟢 低', 'Math SE单独章节', '0.5天', '已有数据'],
    ['🟢 低', '投稿材料准备', '2天', ''],
]
story += [tbl(todo, [1.5*cm, 6.3*cm, 1.8*cm, 5.9*cm]), sp(0.4)]

figs = [
    ['目录', '图表', '内容'],
    ['pub_final/', 'A1-A6', 'SO崩塌/GitHub悖论/5大发现/因果识别/SE对比/分类基线'],
    ['pub_v3/', 'P1-P11', '11张单图'],
    ['pub_classification/', 'C1-C3', '问题类型时序/How-to比率/年度分组'],
    ['pub_se_update/', 'SE1-SE3', 'SE社区分组/22社区热图/SO vs 非技术SE'],
]
story += [H2('已产出图表（15张+）'), sp(0.15),
    tbl(figs, [3.5*cm, 3*cm, 9*cm]), sp(0.4),
    hr(),
    Paragraph('生成时间：2026-03-22　|　GitHub: BKZhao/ai-knowledge-ecosystem',
              st(8, HexColor('#9E9E9E'), align=TA_CENTER))
]

doc.build(story)
print(f'✅ PDF生成：{OUT}')
print(f'大小：{os.path.getsize(OUT)/1024:.0f} KB')
