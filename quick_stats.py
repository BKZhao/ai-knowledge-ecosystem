"""
SO快速描述统计 - 流式解析，不需要全量解压
目标：按周统计2018-2026年的提问量、回答量、用户活跃度
"""
import py7zr
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from datetime import datetime
import os, json

DATA_DIR = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/data/raw"
OUT_DIR  = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"
os.makedirs(OUT_DIR, exist_ok=True)

# AI工具关键事件
AI_EVENTS = [
    ("2021-10-01", "Copilot Beta"),
    ("2022-06-21", "Copilot GA"),
    ("2022-11-30", "ChatGPT"),
    ("2023-03-14", "GPT-4"),
    ("2023-07-18", "Llama 2"),
    ("2024-03-04", "Claude 3"),
]

print("开始流式解析 Posts.7z ...")
weekly_q  = defaultdict(int)  # 问题数
weekly_a  = defaultdict(int)  # 回答数
weekly_accepted = defaultdict(int)  # 有采纳答案的问题
weekly_score_sum = defaultdict(float)
weekly_score_cnt = defaultdict(int)

# 编程语言标签统计
lang_tags = ["python","javascript","java","c#","php","typescript",
             "c++","c","ruby","go","rust","swift","kotlin","r","matlab",
             "assembly","cobol","fortran","haskell","erlang"]
weekly_lang = {lang: defaultdict(int) for lang in lang_tags}

count = 0
skipped = 0

EXTRACT_DIR = f"{DATA_DIR}/extracted"
os.makedirs(EXTRACT_DIR, exist_ok=True)

# 检查是否已经解压
xml_path = f"{EXTRACT_DIR}/Posts.xml"
if not os.path.exists(xml_path):
    print("解压 Posts.7z 到临时目录...")
    with py7zr.SevenZipFile(f"{DATA_DIR}/stackoverflow.com-Posts.7z", mode='r') as z:
        z.extractall(path=EXTRACT_DIR)
    print("解压完成！")
else:
    print(f"已有解压文件：{xml_path}")

with open(xml_path, 'rb') as bio:
    fname = "Posts.xml"
    if True:
        print(f"开始解析 {fname} ...")
        for event, elem in ET.iterparse(bio, events=("end",)):
            if elem.tag != "row":
                continue
            count += 1
            if count % 500000 == 0:
                print(f"  已处理 {count:,} 条，问题数: {sum(weekly_q.values()):,}")

            try:
                date_str = elem.get("CreationDate", "")[:10]
                if not date_str or date_str < "2018-01-01":
                    elem.clear()
                    continue
                
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                week = dt.strftime("%Y-W%V")  # ISO周
                post_type = elem.get("PostTypeId", "")
                score = float(elem.get("Score", 0))
                
                if post_type == "1":  # 问题
                    weekly_q[week] += 1
                    weekly_score_sum[week] += score
                    weekly_score_cnt[week] += 1
                    if elem.get("AcceptedAnswerId"):
                        weekly_accepted[week] += 1
                    # 语言标签
                    tags = elem.get("Tags", "").lower()
                    for lang in lang_tags:
                        if f"<{lang}>" in tags:
                            weekly_lang[lang][week] += 1

                elif post_type == "2":  # 回答
                    weekly_a[week] += 1

            except Exception:
                skipped += 1
            finally:
                elem.clear()

print(f"\n解析完成！总计 {count:,} 条，跳过 {skipped} 条")

# 整理数据
weeks = sorted(set(list(weekly_q.keys()) + list(weekly_a.keys())))
df = pd.DataFrame({
    "week": weeks,
    "questions": [weekly_q[w] for w in weeks],
    "answers":   [weekly_a[w] for w in weeks],
    "accepted":  [weekly_accepted[w] for w in weeks],
    "avg_score": [weekly_score_sum[w]/weekly_score_cnt[w] if weekly_score_cnt[w]>0 else 0 for w in weeks],
})
df["week_dt"] = pd.to_datetime(df["week"] + "-1", format="%Y-W%V-%u")
df["acceptance_rate"] = df["accepted"] / df["questions"].replace(0,1)
df.to_csv(f"{OUT_DIR}/weekly_stats.csv", index=False)

# 语言数据
lang_df = pd.DataFrame({"week": weeks})
for lang in lang_tags:
    lang_df[lang] = [weekly_lang[lang][w] for w in weeks]
lang_df["week_dt"] = pd.to_datetime(lang_df["week"] + "-1", format="%Y-W%V-%u")
lang_df.to_csv(f"{OUT_DIR}/weekly_lang_stats.csv", index=False)

print(f"数据已保存到 {OUT_DIR}")
print(f"\n基本统计：")
print(f"  时间范围: {df['week_dt'].min()} ~ {df['week_dt'].max()}")
print(f"  总提问数: {df['questions'].sum():,}")
print(f"  总回答数: {df['answers'].sum():,}")
print(f"  周均提问: {df['questions'].mean():.0f}")

# 画图
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle("Stack Overflow Activity (2018-2026) - AI Impact Analysis", fontsize=14, fontweight='bold')

ai_colors = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD']

# 图1：提问量趋势
ax1 = axes[0]
ax1.plot(df["week_dt"], df["questions"], color='steelblue', linewidth=1, alpha=0.8)
# 30周移动平均
df["q_ma"] = df["questions"].rolling(8).mean()
ax1.plot(df["week_dt"], df["q_ma"], color='navy', linewidth=2, label='8-week MA')
for (date, label), color in zip(AI_EVENTS, ai_colors):
    ax1.axvline(pd.Timestamp(date), color=color, linestyle='--', alpha=0.8, linewidth=1.5)
    ax1.text(pd.Timestamp(date), ax1.get_ylim()[1]*0.9 if ax1.get_ylim()[1]>0 else 1, 
             label, rotation=90, fontsize=7, color=color)
ax1.set_ylabel("Weekly Questions")
ax1.set_title("Question Volume")
ax1.legend()

# 图2：回答量趋势
ax2 = axes[1]
ax2.plot(df["week_dt"], df["answers"], color='coral', linewidth=1, alpha=0.8)
df["a_ma"] = df["answers"].rolling(8).mean()
ax2.plot(df["week_dt"], df["a_ma"], color='darkred', linewidth=2, label='8-week MA')
for (date, label), color in zip(AI_EVENTS, ai_colors):
    ax2.axvline(pd.Timestamp(date), color=color, linestyle='--', alpha=0.8, linewidth=1.5)
ax2.set_ylabel("Weekly Answers")
ax2.set_title("Answer Volume")
ax2.legend()

# 图3：采纳率
ax3 = axes[2]
ax3.plot(df["week_dt"], df["acceptance_rate"]*100, color='green', linewidth=1, alpha=0.8)
df["acc_ma"] = df["acceptance_rate"].rolling(8).mean()
ax3.plot(df["week_dt"], df["acc_ma"]*100, color='darkgreen', linewidth=2, label='8-week MA')
for (date, label), color in zip(AI_EVENTS, ai_colors):
    ax3.axvline(pd.Timestamp(date), color=color, linestyle='--', alpha=0.8, linewidth=1.5)
ax3.set_ylabel("Acceptance Rate (%)")
ax3.set_title("Question Acceptance Rate")
ax3.legend()

for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/so_trends.png", dpi=150, bbox_inches='tight')
print(f"图表已保存: {OUT_DIR}/so_trends.png")

# 打印ChatGPT前后对比
pre  = df[df["week_dt"] < "2022-11-30"]["questions"].mean()
post = df[df["week_dt"] >= "2022-11-30"]["questions"].mean()
print(f"\nChatGPT前后对比：")
print(f"  ChatGPT前周均提问: {pre:.0f}")
print(f"  ChatGPT后周均提问: {post:.0f}")
print(f"  变化幅度: {(post-pre)/pre*100:.1f}%")
