"""
研究进度报告 PDF - 2026-03-22
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, json, pandas as pd
from datetime import datetime

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT  = f"{BASE}/results/研究进度报告_20260322.pdf"

# ── 颜色 ──
BLUE   = HexColor('#1565C0')
DBLUE  = HexColor('#0D47A1')
GREEN  = HexColor('#2E7D32')
RED    = HexColor('#C62828')
PURPLE = HexColor('#6A1B9A')
ORANGE = HexColor('#E65100')
LGRAY  = HexColor('#F5F5F5')
MGRAY  = HexColor('#E0E0E0')
DGRAY  = HexColor('#424242')

doc = SimpleDocTemplate(OUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm)

styles = getSampleStyleSheet()
story  = []

def H1(text, color=DBLUE):
    return Paragraph(f'<font color="{color.hexval()}" size="18"><b>{text}</b></font>', styles['Normal'])

def H2(text, color=BLUE):
    return Paragraph(f'<font color="{color.hexval()}" size="13"><b>{text}</b></font>', styles['Normal'])

def H3(text, color=DGRAY):
    return Paragraph(f'<font color="{color.hexval()}" size="11"><b>{text}</b></font>', styles['Normal'])

def P(text, size=10):
    return Paragraph(f'<font size="{size}">{text}</font>', styles['Normal'])

def bullet(text, size=9.5):
    return Paragraph(f'<font size="{size}">• {text}</font>', styles['Normal'])

def sp(h=0.3): return Spacer(1, h*cm)
def hr(): return HRFlowable(width="100%", thickness=0.5, color=MGRAY, spaceAfter=6)

# ══════════════════════════════════════════════════
# 封面
# ══════════════════════════════════════════════════
story += [
    sp(3),
    Paragraph('<font size="24" color="#0D47A1"><b>AI Impact on Knowledge Ecosystems</b></font>',
              ParagraphStyle('c', alignment=TA_CENTER)),
    sp(0.5),
    Paragraph('<font size="16" color="#424242">研究进度报告</font>',
              ParagraphStyle('c', alignment=TA_CENTER)),
    sp(0.3),
    Paragraph('<font size="12" color="#757575">Research Progress Report — 2026-03-22</font>',
              ParagraphStyle('c', alignment=TA_CENTER)),
    sp(0.5),
    HRFlowable(width="60%", thickness=2, color=BLUE, hAlign='CENTER'),
    sp(0.5),
    Paragraph('<font size="11" color="#424242">赵炳坤 | City University of Hong Kong</font>',
              ParagraphStyle('c', alignment=TA_CENTER)),
    sp(4),
]

# 进度总览表
overview_data = [
    ['模块', '状态', '完成度'],
    ['数据采集：SO周度数据 (14语言×424周)', '✅ 完成', '100%'],
    ['数据采集：GitHub月度数据 (13语言×98月)', '✅ 完成', '100%'],
    ['数据采集：SE社区数据 (21社区×2018-2026)', '✅ 完成', '100%'],
    ['数据采集：SO质量指标 (950万帖子)', '✅ 完成', '100%'],
    ['LLM问题分类 (DeepSeek-V3)', '✅ 完成', '112k/~200k'],
    ['DID主回归分析', '✅ 完成', '100%'],
    ['SE跨领域对比分析', '✅ 完成', '100%'],
    ['问题类型时序分析', '✅ 完成', '100%'],
    ['论文图表生成', '✅ 完成', '15+张'],
    ['研究框架/理论', '✅ 完成', 'V3版'],
    ['API密钥续费 (硅基流动)', '⚠️ 待办', '余额耗尽'],
    ['200k分类续跑', '⏳ 进行中', '14k/200k (暂停)'],
]
ot = Table(overview_data, colWidths=[9.5*cm, 3.5*cm, 2.5*cm])
ot.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DBLUE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,0), 10),
    ('FONTSIZE',   (0,1), (-1,-1), 9),
    ('BACKGROUND', (0,1), (-1,-1), LGRAY),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING', (0,0), (0,-1), 8),
    # 状态颜色
    ('TEXTCOLOR', (1,6), (1,6), RED),   # 待办
    ('TEXTCOLOR', (1,7), (1,7), ORANGE), # 进行中
]))
story += [H2("📊 总体进度概览"), sp(0.3), ot, PageBreak()]

# ══════════════════════════════════════════════════
# 第1页：数据集说明
# ══════════════════════════════════════════════════
story += [H1("1. 数据集"), sp(0.4), hr()]

story += [
    H2("1.1 Stack Overflow 主数据集"),
    sp(0.2),
    bullet("来源：Stack Overflow Data Dump (2024年4月) + API实时补充"),
    bullet("原始规模：950万帖子（Posts.xml 97GB）"),
    bullet("处理后：posts_2018plus.parquet（497MB，仅保留2018-2024问题）"),
    bullet("周度时序：424周 × 14编程语言，2018-01 ~ 2026-02"),
    bullet("质量指标：avg_score, avg_views, pct_answered, pct_accepted, avg_length, active_users"),
    sp(0.4),
    H2("1.2 GitHub 数据集"),
    sp(0.2),
    bullet("来源：GitHub API (gh archive)"),
    bullet("覆盖：13编程语言 × 98个月（2018-01 ~ 2026-02）"),
    bullet("指标：新建仓库数、活跃仓库率、fork率、star率、Issue/仓库比"),
    sp(0.4),
    H2("1.3 Stack Exchange 社区数据集"),
    sp(0.2),
    bullet("来源：SE Data Dump（21个社区）+ SE API补充（2024-2026）"),
    bullet("覆盖：2018-01 ~ 2026-02（23个月补充数据已完成）"),
    bullet("社区分组：技术类(4) / 人文类(3) / 社会科学(4) / 自然科学(3)"),
    sp(0.4),
    H2("1.4 LLM问题分类数据集"),
    sp(0.2),
    bullet("工具：DeepSeek-V3 via 硅基流动API"),
    bullet("规模：112,431条已分类（100k批次 + 额外14k批次）"),
    bullet("类别：How-to / Debug / Conceptual / Architecture"),
    bullet("分布：How-to 46.4% | Conceptual 36.6% | Debug 15.5% | Arch 1.4%"),
    sp(0.4),
]

# 数据集文件表
data_files = [
    ['文件名', '大小', '说明'],
    ['posts_2018plus.parquet', '497 MB', 'SO问题元数据（2018-2024，950万行）'],
    ['post_titles.csv', '2.1 GB', 'SO问题标题+标签（全量）'],
    ['stacked_panel.csv', '252 KB', 'DID面板数据（2390行×8列）'],
    ['se_panel_complete_2018_2026.csv', '11 KB', 'SE多社区月度面板'],
    ['weekly_api_stats.csv', '26 KB', 'SO周度API统计'],
    ['github_monthly_stats.csv', '18 KB', 'GitHub月度仓库统计'],
    ['github_quality_metrics.csv', '23 KB', 'GitHub质量指标'],
    ['so_quality_monthly.csv', '15 KB', 'SO月度质量指标'],
    ['classification_results_combined.csv', '~3 MB', 'LLM分类结果（112k条）'],
    ['control_variables.csv', '25 KB', '控制变量（20个）'],
    ['*_monthly.csv (17个)', '~2 KB各', 'SE各社区月度数据'],
]
dt = Table(data_files, colWidths=[6*cm, 2*cm, 7.5*cm])
dt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), BLUE),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (0,-1), 6),
]))
story += [H3("数据文件清单"), sp(0.2), dt, PageBreak()]

# ══════════════════════════════════════════════════
# 第2页：核心发现
# ══════════════════════════════════════════════════
story += [H1("2. 核心发现"), sp(0.3), hr()]

findings = [
    ('H1：SO提问量崩塌 + GitHub仓库激增', GREEN, [
        'SO消费行为 -75.3%（2018→2026），加速度持续增大',
        'GitHub仓库创建 +121.1%（同期）',
        'DID主回归：β₁=-2.26*** (SO), β₂=+3.82*** (GitHub), p<0.001',
        '冲击持续加速：2022→23: -41%, 2023→24: -49%, 2024→25: -70%',
    ]),
    ('H2：质量稀释效应', ORANGE, [
        'GitHub活跃率稳定(+0.3pp)，但fork率-7.9pp，star率-7.8pp',
        'Issue/仓库比率 TypeScript -54.4%, Python -37.3%',
        'SO：avg_score -60.6%, avg_views -77.2%，avg_length +16%（反直觉）',
        '解读：简单问题消失，剩下都是难题',
    ]),
    ('H3：问题类型结构性转变', PURPLE, [
        'Debug类：2018年30.1% → 2024年7.8%（-22.4pp）',
        'Conceptual类：28.6% → 47.4%（+18.7pp）',
        'Debug崩塌早在ChatGPT之前（2018→2019骤降），说明是长期趋势',
        'ChatGPT后：Conceptual加速上升（AI引发更多概念性讨论）',
    ]),
    ('H4：SE跨领域分层效应', BLUE, [
        'SO（编程）-77.4% > English（语言）-68.7% > DataSci -66.5%',
        'Travel -18%, Economics -22.6%（最抗跌）',
        'Philosophy +54.6%（唯一上升！AI引发哲学讨论激增）',
        'ARI与SO下降相关性弱（r=0.23，不显著）→ 行为替代而非内容替代',
    ]),
]

for title, color, bullets_list in findings:
    story.append(H2(f"🔍 {title}", color))
    story.append(sp(0.15))
    for b in bullets_list:
        story.append(bullet(b))
    story.append(sp(0.35))

story += [hr(), PageBreak()]

# ══════════════════════════════════════════════════
# 第3页：理论框架 + 待办事项
# ══════════════════════════════════════════════════
story += [H1("3. 理论框架（V3）"), sp(0.3), hr()]

story += [
    H2("依赖性知识行为（DKB）vs 自主性知识行为（AKB）"),
    sp(0.2),
    P("• <b>DKB（被AI替代）</b>：SO提问、GitHub Issue → 需要他人协助的依赖行为", 10),
    P("• <b>AKB（被AI激活）</b>：GitHub仓库创建、Conceptual讨论 → 主动的自主行为", 10),
    sp(0.3),
    P("三大机制：", 10),
    bullet("<b>替代效应</b>：AI直接回答技术问题，减少SO依赖行为"),
    bullet("<b>激活效应</b>：AI降低创作门槛，激发GitHub代码生产"),
    bullet("<b>稀释效应</b>：量增但质降（fork率/star率下降），内容同质化"),
    sp(0.5),
]

story += [H1("4. 待完成工作"), sp(0.3), hr()]

todo_data = [
    ['优先级', '任务', '备注'],
    ['🔴 高', 'API充值续跑200k分类', '硅基流动余额耗尽，需充值'],
    ['🔴 高', '整合完整分类图表进论文', '需加分类时序图到PDF报告'],
    ['🟡 中', '稳健性检验：更换ARI指标', '用HumanEval benchmark替代主观打分'],
    ['🟡 中', '因果识别强化', '加强β₂的识别逻辑，反驳GitHub自然增长'],
    ['🟢 低', '数学SE对照完整版', 'Math SE数据已有，待加入对比'],
    ['🟢 低', '投稿准备', 'Nature/PNAS格式调整'],
]
tt = Table(todo_data, colWidths=[2*cm, 9*cm, 4.5*cm])
tt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DGRAY),
    ('TEXTCOLOR',  (0,0), (-1,0), white),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
    ('GRID', (0,0), (-1,-1), 0.3, MGRAY),
    ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING', (0,1), (1,-1), 6),
]))
story += [tt, sp(0.5)]

story += [
    H1("5. 已产出图表清单", DGRAY), sp(0.3), hr(),
    P("pub_final/：A1-A6（6张多联图）", 9.5),
    P("pub_v3/：P1-P11（11张单图）", 9.5),
    P("pub_classification/：C1-C3（3张分类时序图）", 9.5),
    P("pub_se_update/：SE1-SE3（3张SE社区更新图）", 9.5),
    sp(0.3),
    H2("本次新增（2026-03-22）", GREEN),
    bullet("SE1：SE社区分组时序图（2018-2026完整版）"),
    bullet("SE2：ChatGPT影响热图（22个社区对比，Philosophy +54%!!）"),
    bullet("SE3：SO vs 非技术SE双轴对比"),
    bullet("C1-C3：问题类型分布时序分析（Debug -22pp, Conceptual +19pp）"),
    sp(0.5),
    Paragraph('<font size="8" color="#9E9E9E">生成时间：2026-03-22 | '
              'GitHub: BKZhao/ai-knowledge-ecosystem</font>',
              ParagraphStyle('footer', alignment=TA_CENTER)),
]

doc.build(story)
print(f"✅ PDF生成：{OUT}")
