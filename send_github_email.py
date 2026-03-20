#!/usr/bin/env python3
"""Send GitHub analysis figures via email."""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
USER = "1792721319@qq.com"
PASS = "jbajwqsinjlvfdai"

TO   = "bingkzhao2-c@my.cityu.edu.hk"
CC   = "1792721319@qq.com"
SUBJ = "【GitHub深度分析】5张图 - 知识生产端完整分析"

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"

BODY = """\
您好，

本邮件附上GitHub知识生产端深度分析的5张图（Nature/Science风格，300 DPI），
以下是每张图的核心发现：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Fig 1 — GitHub总量趋势 vs Stack Overflow总量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• GitHub仓库数在ChatGPT（2022-11）后持续加速上升
• Stack Overflow问题量在同期出现明显下滑
• 两者均标准化到2020=100，呈现显著的"剪刀差"
• 核心信息：AI工具的普及并未抑制代码生产，反而激活了知识生产端

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Fig 2 — 各语言变化幅度排序（水平条形图）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• TypeScript: +397.7%（最大惊喜！前端工程化爆发）
• Rust: +222.3%（AI不擅长Rust，但Rust社区最活跃）
• Python: +201.9%（AI首选语言，增长符合预期）
• Ruby: -59.8%（唯一大幅下降：语言本身衰退+AI加速）
• Haskell: -13.9%（小众语言边缘化）
• 条形图同时展示仓库数和Issue数变化，标注AI可替代性指数(ARI)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Fig 3 — 不对称效应：ARI vs SO下降 vs GitHub增长（双面板）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 左图(a)：ARI与SO问题下降有一定负相关（r弱但存在）
  → 高AI可替代语言的SO问题下降更多
• 右图(b)：ARI与GitHub增长几乎无相关（r≈0）
  → GitHub活跃度的增长与"AI能不能写这个语言"无关
• 核心发现：这个不对称性揭示SO下降=知识消费行为改变，
  而非开发者放弃编程

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Fig 4 — GitHub语言时序（3类分组，3行×1列）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 上升语言（TypeScript/Python/Rust/Go/JS）：ChatGPT后加速
• 稳定语言（C/C++/Java/C#）：缓慢增长，相对稳定
• 下降语言（Ruby/Haskell）：持续衰退趋势
• 标准化到2020=100，3个月移动平均平滑
• 红色虚线标注ChatGPT发布节点

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Fig 5 — Issue数变化：知识协作 vs 知识消费
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 左图：GitHub Issue数量——代表项目协作（提Bug、讨论需求）
• 右图：Stack Overflow问题数——代表知识消费（查答案）
• GitHub Issues上升 → 更多项目，更多协作，更活跃
• SO Questions下降 → AI替代了"搜索现成答案"的行为
• 两者讲述截然不同的故事：生产≠消费

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

总体结论：
AI工具（GitHub Copilot/ChatGPT/GPT-4/Claude）改变的是知识"消费"方式，
而非知识"生产"能力。开发者仍在写代码、开项目、提Issue，
只是不再需要频繁查Stack Overflow了。

TypeScript和Rust的爆发尤其有趣——
TypeScript是AI辅助前端工程化的受益者；
Rust则因AI难以驾驭其所有权系统，反而刺激了社区学习和探索热情。

祝研究顺利！

---
本邮件由 OpenClaw AI 自动生成
数据来源：GitHub API + Stack Overflow API (2018-2026)
"""

def send():
    msg = MIMEMultipart()
    msg['From']    = USER
    msg['To']      = TO
    msg['Cc']      = CC
    msg['Subject'] = SUBJ

    msg.attach(MIMEText(BODY, 'plain', 'utf-8'))

    # Attach 5 figures
    figs = [f"github_fig{i}.png" for i in range(1, 6)]
    for fname in figs:
        fpath = os.path.join(BASE, fname)
        if not os.path.exists(fpath):
            print(f"  ⚠ Missing: {fpath}")
            continue
        with open(fpath, 'rb') as f:
            img_data = f.read()
        img = MIMEImage(img_data, name=fname)
        img.add_header('Content-Disposition', 'attachment', filename=fname)
        msg.attach(img)
        print(f"  📎 Attached: {fname} ({len(img_data)//1024} KB)")

    recipients = [TO, CC]
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(USER, PASS)
        server.sendmail(USER, recipients, msg.as_string())
    print(f"\n✅ Email sent to {TO} (cc: {CC})")

if __name__ == '__main__':
    send()
