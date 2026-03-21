#!/usr/bin/env python3
"""Send email with regression analysis results."""

import smtplib, ssl, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

FROM = "1792721319@qq.com"
AUTH = "jbajwqsinjlvfdai"
TO = ["bingkzhao2-c@my.cityu.edu.hk", "1792721319@qq.com"]
SUBJECT = "【回归结果完整版】H2-H6全部分析结果"

RESULTS_DIR = '/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results'

BODY = """炳坤好，

附件为AI知识生态系统论文H2-H6回归分析全部结果（含稳健性检验）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H2：Issue协作去社会化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
β(ARI × Post_ChatGPT) = -0.3415***（p<0.001）
ChatGPT后高ARI语言的Issue/仓库比率显著下降，支持H2。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H3：稀释效应
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fork率：β₂(ARI×Post_ChatGPT) = 0.0508***（p<0.001）
Star率：β₂(ARI×Post_ChatGPT) = 0.0435***（p<0.001）
高ARI语言的Fork/Star率相对上升（AI批量生成仓库稀释效应），支持H3。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H4：跨领域截面
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
β(AI_Rep) = 27.59（p=0.138）
注意：SE数据仅至2022-06，与2019-2021基准比较。方向正确但受限于数据范围。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H5：分节点事件研究
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAR(24周)：Copilot GA=-104.6%, ChatGPT=-441.7%, GPT-4=-574.7%
（Claude 3因数据密度变化CAR为正，需重新检视基线）
Spearman单调性 ρ=0.20（p=0.80，前三个节点单调递减）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H6：分叉路径
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
β₁(ARI×Post_ChatGPT) = -0.5765***（p<0.001）
β₂(ARI×Post_ChatGPT×HighARI) = 0.9158***（p<0.001）
高ARI语言净效应为正（-0.58+0.92=+0.34），低ARI为负，形成分叉路径，强烈支持H6。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
稳健性检验
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Placebo（虚假断点2021-06）：β=-0.075，p=0.248 → 不显著，通过
✅ 排除COVID期（2020-21）：β=-1.025***（p<0.001）→ 结果更强，稳健
Copilot时代（2018-22）：β=-0.166†（p=0.089）
ChatGPT时代（全期）：β=-0.962***（p<0.001）→ ChatGPT效应远大于Copilot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

附件说明：
- regression_fig1.png：H2 Issue/仓库比率时序+散点
- regression_fig2.png：H3 Fork/Star率时序
- regression_fig3.png：H4 跨领域散点图（12个社区）
- regression_fig4.png：H5 多节点CAR柱状图
- regression_fig5.png：H6 分叉路径图
- regression_summary.md：中文结果摘要
- regression_tables.tex：LaTeX格式回归表格

此致
AI科研助手 🐂
"""

msg = MIMEMultipart()
msg['From'] = FROM
msg['To'] = ', '.join(TO)
msg['Subject'] = SUBJECT
msg.attach(MIMEText(BODY, 'plain', 'utf-8'))

attachments = [
    'regression_fig1.png',
    'regression_fig2.png',
    'regression_fig3.png',
    'regression_fig4.png',
    'regression_fig5.png',
    'regression_summary.md',
    'regression_tables.tex',
]

for fname in attachments:
    fpath = os.path.join(RESULTS_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{fname}"')
        msg.attach(part)
        print(f"  Attached: {fname}")
    else:
        print(f"  WARNING: {fname} not found!")

print("\nSending via smtp.qq.com:465 (SSL)...")
try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.qq.com', 465, context=context, timeout=30) as server:
        server.login(FROM, AUTH)
        server.sendmail(FROM, TO, msg.as_string())
    print("Email sent successfully!")
    print(f"  To: {', '.join(TO)}")
    print(f"  Subject: {SUBJECT}")
except Exception as e:
    print(f"SSL port 465 failed: {e}")
    print("Trying port 587...")
    try:
        with smtplib.SMTP('smtp.qq.com', 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(FROM, AUTH)
            server.sendmail(FROM, TO, msg.as_string())
        print("Email sent via port 587!")
    except Exception as e2:
        print(f"Port 587 also failed: {e2}")
        raise
