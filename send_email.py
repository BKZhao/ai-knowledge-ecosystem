#!/usr/bin/env python3
"""Send email with all 8 paper figures as attachments."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

FROM = "1792721319@qq.com"
AUTH = "jbajwqsinjlvfdai"
TO = ["bingkzhao2-c@my.cityu.edu.hk", "1792721319@qq.com"]
SUBJECT = "【完整图集】论文一全套8张图 - 知识生产vs消费不对称"

RESULTS_DIR = '/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results'

BODY = """各位好，

附件为论文《AI工具对知识生产与消费不对称影响》的完整图集（共8张，Nature/Science风格，300 DPI）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图1（paper_fig1.png）— H1主图：剪刀差
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：ChatGPT发布后，SO问题量（消费端）持续下降，GitHub仓库数（生产端）持续上升，形成明显的"剪刀差"。两者在2020年基准线上方同步增长，之后出现分叉，直观验证了H1假说。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图2（paper_fig2.png）— H1事件研究：累积异常分叉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：以ChatGPT发布为t=0，上图展示SO的周度异常值分布（后52周向下漂移），下图展示SO与GitHub的累积异常收益（CAR）分叉——SO CAR持续为负，GitHub CAR向上反弹，两条曲线的分叉幅度随时间增大。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图3（paper_fig3.png）— H2异质性：SO端斜率显著为负
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：左图（SO端）——AI可替代性指数（ARI）对ChatGPT后SO问题下降幅度有显著负向预测力（β<0），高ARI语言（Python/JavaScript等）下降最大；右图（GitHub端）——斜率接近0，ARI不预测GitHub仓库增长，证实不对称效应。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图4（paper_fig4.png）— H2分组时序：三组分化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：高ARI组（Python/JS/TS/Java/C#）SO问题量跌幅最大；中ARI组（Go/Ruby/C++/C/R）居中；低ARI组（Rust/Haskell/Fortran/Assembly）基本稳定。三组在ChatGPT后轨迹明显分化，支持H2。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图5（paper_fig5.png）— 对照社区检验
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：Stack Overflow（编程）的下降在Math SE和Physics SE中并未出现——两个对照社区问题量保持相对稳定。这证明SO的下降是AI对编程领域的特定冲击，而非平台层面的系统性衰退。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图6（paper_fig6.png）— GitHub端异质性（对照Fig3）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：GitHub仓库数的增长幅度与ARI无显著相关（β≈0，R²≈0），与Fig3的SO端形成鲜明对比。这种"消费端受ARI驱动、生产端不受ARI影响"的不对称性，是论文核心贡献之一。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图7（paper_fig7.png）— 年度热力图（2018–2025）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：SO端（上图）——高ARI语言在2023年后普遍变红（大幅下降），低ARI语言基本不变；GitHub端（下图）——全局普遍变蓝（增长），且增幅与ARI无明显关联。两图的色差对比直观强化了不对称假说。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
图8（paper_fig8.png）— 平行趋势检验
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
核心发现：ChatGPT发布前24个月（τ=-24到0），高ARI组与低ARI组的DID系数围绕零值波动，趋势检验p值不显著，证明平行趋势假定成立，DID设计有效。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

数据来源：Stack Overflow API（424周 × 14语言）、GitHub REST API（98月 × 14语言）、Stack Exchange API（Math SE / Physics SE对照）

如需修改任何图的样式或内容，请回复告知。

此致
AI科研助手 🐂
"""

# Build message
msg = MIMEMultipart()
msg['From'] = FROM
msg['To'] = ', '.join(TO)
msg['Subject'] = SUBJECT
msg.attach(MIMEText(BODY, 'plain', 'utf-8'))

# Attach all 8 figures
for i in range(1, 9):
    fpath = f'{RESULTS_DIR}/paper_fig{i}.png'
    if os.path.exists(fpath):
        with open(fpath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="paper_fig{i}.png"')
        msg.attach(part)
        print(f"  Attached: paper_fig{i}.png")
    else:
        print(f"  WARNING: paper_fig{i}.png not found!")

# Send via QQ SMTP
print("\nConnecting to smtp.qq.com:587...")
try:
    server = smtplib.SMTP('smtp.qq.com', 587, timeout=30)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(FROM, AUTH)
    server.sendmail(FROM, TO, msg.as_string())
    server.quit()
    print("✅ Email sent successfully!")
    print(f"  To: {', '.join(TO)}")
    print(f"  Subject: {SUBJECT}")
    print(f"  Attachments: 8 PNG figures")
except Exception as e:
    print(f"❌ SMTP error: {e}")
    # Try port 465 with SSL
    print("Trying port 465 with SSL...")
    try:
        import ssl
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL('smtp.qq.com', 465, context=context, timeout=30)
        server.login(FROM, AUTH)
        server.sendmail(FROM, TO, msg.as_string())
        server.quit()
        print("✅ Email sent via SSL (port 465)!")
    except Exception as e2:
        print(f"❌ SSL error: {e2}")
        raise
