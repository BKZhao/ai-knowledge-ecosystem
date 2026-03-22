"""
问题类型分类时序分析图
基于97,947条LLM标注数据
"""
import pandas as pd
import json
import numpy as np
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT_DIR = f"{BASE}/results/pub_classification"
import os; os.makedirs(OUT_DIR, exist_ok=True)

LABEL_MAP = {1: 'How-to', 2: 'Debug', 3: 'Conceptual', 4: 'Architecture'}
COLORS = {
    'How-to':      '#2196F3',
    'Debug':       '#F44336',
    'Conceptual':  '#4CAF50',
    'Architecture':'#FF9800'
}
CHATGPT_DATE = '2022-11-30'

# ── 加载数据 ──────────────────────────────────────────────
print("Loading data...")
with open(f"{BASE}/results/classification_100k_progress.json") as f:
    labels = json.load(f)

df_parquet = pq.read_table(
    f"{BASE}/data/parquet/posts_2018plus.parquet",
    columns=['Id','PostTypeId','CreationDate','Tags']
).to_pandas()
df_parquet['Id'] = df_parquet['Id'].astype(str)
df_q = df_parquet[df_parquet['PostTypeId'] == 1].copy()

label_df = pd.DataFrame(list(labels.items()), columns=['Id','label_id'])
label_df['label'] = label_df['label_id'].map(LABEL_MAP)
merged = df_q.merge(label_df, on='Id')
merged['date'] = pd.to_datetime(merged['CreationDate'])
merged['year'] = merged['date'].dt.year
merged['quarter'] = merged['date'].dt.to_period('Q').astype(str)
merged['yearmonth'] = merged['date'].dt.to_period('M').astype(str)

print(f"Loaded {len(merged)} labeled questions")

# ── 按年统计 ──────────────────────────────────────────────
yearly = merged.groupby(['year','label']).size().unstack(fill_value=0)
yearly_pct = yearly.div(yearly.sum(axis=1), axis=0) * 100

# ── 按季度统计 ──────────────────────────────────────────────
quarterly = merged.groupby(['quarter','label']).size().unstack(fill_value=0)
quarterly_pct = quarterly.div(quarterly.sum(axis=1), axis=0) * 100

# ── 绝对数（季度，归一化到每年14000条基准） ──────────────────
# 每季度样本量不等，用比例×总SO实际量更准；这里用比例图为主

# ═══════════════════════════════════════════════════════════
# 图1：年度比例堆积面积图 + 各类型趋势线（2×2）
# ═══════════════════════════════════════════════════════════
fig = plt.figure(figsize=(14, 10))
fig.patch.set_facecolor('white')
gs = GridSpec(3, 2, figure=fig, hspace=0.48, wspace=0.32)

years = sorted(yearly_pct.index)

# 左上：堆积面积图
ax1 = fig.add_subplot(gs[0, :])
bottom = np.zeros(len(years))
for lbl in ['How-to', 'Debug', 'Conceptual', 'Architecture']:
    if lbl in yearly_pct.columns:
        vals = yearly_pct[lbl].reindex(years, fill_value=0).values
        ax1.bar(years, vals, bottom=bottom, color=COLORS[lbl], label=lbl, alpha=0.85, width=0.65)
        # 标注百分比
        for i, (y, v, b) in enumerate(zip(years, vals, bottom)):
            if v > 3:
                ax1.text(y, b + v/2, f'{v:.0f}%', ha='center', va='center',
                         fontsize=8.5, fontweight='bold', color='white')
        bottom += vals

ax1.axvline(x=2022.83, color='#9C27B0', lw=2, ls='--', alpha=0.8)
ax1.text(2022.85, 97, 'ChatGPT\n(Nov 2022)', fontsize=8, color='#9C27B0', va='top')
ax1.set_xlim(2017.4, 2024.6)
ax1.set_ylim(0, 105)
ax1.set_ylabel('Proportion (%)', fontsize=11)
ax1.set_title('Stack Overflow Question Type Distribution by Year (N=97,947)', fontsize=13, fontweight='bold', pad=10)
ax1.set_xticks(years)
ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d%%'))

# 右下2×2：各类型单独趋势
for idx, lbl in enumerate(['How-to', 'Debug', 'Conceptual', 'Architecture']):
    row, col = (idx // 2) + 1, idx % 2
    ax = fig.add_subplot(gs[row, col])
    if lbl in quarterly_pct.columns:
        q_vals = quarterly_pct[lbl]
        q_x = range(len(q_vals))
        ax.fill_between(q_x, q_vals.values, alpha=0.25, color=COLORS[lbl])
        ax.plot(q_x, q_vals.values, color=COLORS[lbl], lw=2.2, marker='o', ms=3)
        
        # ChatGPT线（季度Q4 2022 = 2022Q4）
        quarters = list(q_vals.index)
        chatgpt_q = '2022Q4'
        if chatgpt_q in quarters:
            cidx = quarters.index(chatgpt_q)
            ax.axvline(x=cidx, color='#9C27B0', lw=1.5, ls='--', alpha=0.7)
        
        # 趋势：ChatGPT前后均值
        pre_mask  = [q < '2022Q4' for q in quarters]
        post_mask = [q >= '2022Q4' for q in quarters]
        pre_mean  = q_vals.values[pre_mask].mean()
        post_mean = q_vals.values[post_mask].mean()
        change = post_mean - pre_mean
        sign = '+' if change > 0 else ''
        
        ax.set_title(f'{lbl}  ({sign}{change:.1f}pp post-ChatGPT)', fontsize=10,
                     fontweight='bold', color=COLORS[lbl], pad=6)
        
        # x轴：只显示年份标签
        year_ticks = [i for i, q in enumerate(quarters) if q.endswith('Q1')]
        year_labels = [q[:4] for q in quarters if q.endswith('Q1')]
        ax.set_xticks(year_ticks)
        ax.set_xticklabels(year_labels, fontsize=8)
        ax.set_ylabel('Share (%)', fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(labelsize=8)

plt.suptitle('Question Type Shifts After ChatGPT Launch', fontsize=14, fontweight='bold', y=1.01)
plt.savefig(f"{OUT_DIR}/C1_type_distribution.png", dpi=150, bbox_inches='tight',
            facecolor='white')
plt.close()
print("✅ C1 saved")

# ═══════════════════════════════════════════════════════════
# 图2：How-to vs Conceptual 比率变化（核心发现）
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor('white')

ax = axes[0]
# How-to / Conceptual 比率
ratio = quarterly_pct['How-to'] / quarterly_pct['Conceptual'].replace(0, np.nan)
q_x = range(len(ratio))
quarters = list(ratio.index)

ax.plot(q_x, ratio.values, color='#673AB7', lw=2.5)
ax.fill_between(q_x, ratio.values, 1, alpha=0.15, color='#673AB7')
ax.axhline(y=1, color='gray', lw=1, ls=':')

chatgpt_q = '2022Q4'
if chatgpt_q in quarters:
    cidx = quarters.index(chatgpt_q)
    ax.axvline(x=cidx, color='#9C27B0', lw=2, ls='--', alpha=0.8)
    ax.text(cidx+0.2, ratio.max()*0.95, 'ChatGPT', fontsize=9, color='#9C27B0')

year_ticks = [i for i, q in enumerate(quarters) if q.endswith('Q1')]
year_labels = [q[:4] for q in quarters if q.endswith('Q1')]
ax.set_xticks(year_ticks)
ax.set_xticklabels(year_labels)
ax.set_ylabel('How-to / Conceptual ratio', fontsize=11)
ax.set_title('How-to vs Conceptual Ratio\n(>1 = How-to dominates)', fontsize=11, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Pre/Post annotation
pre_ratio  = ratio.values[:cidx].mean()
post_ratio = ratio.values[cidx:].mean()
ax.annotate(f'Pre: {pre_ratio:.2f}', xy=(cidx//2, pre_ratio),
            fontsize=10, color='#2196F3', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
ax.annotate(f'Post: {post_ratio:.2f}', xy=(cidx + (len(ratio)-cidx)//2, post_ratio),
            fontsize=10, color='#F44336', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.7))

# 右图：Debug绝对份额下降
ax2 = axes[1]
for lbl in ['How-to', 'Debug', 'Conceptual']:
    vals = quarterly_pct[lbl].values if lbl in quarterly_pct.columns else np.zeros(len(quarters))
    ax2.plot(q_x, vals, color=COLORS[lbl], lw=2, label=lbl, marker='o', ms=2.5)

if chatgpt_q in quarters:
    ax2.axvline(x=quarters.index(chatgpt_q), color='#9C27B0', lw=2, ls='--', alpha=0.7, label='ChatGPT')

ax2.set_xticks(year_ticks)
ax2.set_xticklabels(year_labels)
ax2.set_ylabel('Share (%)', fontsize=11)
ax2.set_title('Question Type Proportions Over Time\n(Quarterly)', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9, loc='upper left')
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/C2_howto_conceptual_shift.png", dpi=150, bbox_inches='tight',
            facecolor='white')
plt.close()
print("✅ C2 saved")

# ═══════════════════════════════════════════════════════════
# 图3：核心数字表 + 年度变化
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor('white')

x = np.arange(len(years))
width = 0.2
lbls = ['How-to', 'Debug', 'Conceptual', 'Architecture']
offsets = [-1.5, -0.5, 0.5, 1.5]

for lbl, offset in zip(lbls, offsets):
    if lbl in yearly_pct.columns:
        vals = yearly_pct[lbl].reindex(years, fill_value=0).values
        bars = ax.bar(x + offset*width, vals, width, label=lbl,
                      color=COLORS[lbl], alpha=0.85)

ax.axvline(x=4.5 + 0.33, color='#9C27B0', lw=2.5, ls='--', alpha=0.8)
ax.text(4.5 + 0.35, ax.get_ylim()[1]*0.92 if ax.get_ylim()[1] > 0 else 55,
        'ChatGPT', fontsize=10, color='#9C27B0')

ax.set_xticks(x)
ax.set_xticklabels(years, fontsize=11)
ax.set_ylabel('Share (%)', fontsize=11)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
ax.set_title('Annual Question Type Proportions — Stack Overflow (2018–2024)', 
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 打印关键数字
print("\n=== 关键发现 ===")
print(yearly_pct.round(1).to_string())

# 2018 vs 2024 变化
print("\n2018→2024 变化:")
for lbl in lbls:
    if lbl in yearly_pct.columns:
        delta = yearly_pct.loc[2024, lbl] - yearly_pct.loc[2018, lbl]
        print(f"  {lbl}: {yearly_pct.loc[2018,lbl]:.1f}% → {yearly_pct.loc[2024,lbl]:.1f}% ({delta:+.1f}pp)")

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/C3_annual_grouped.png", dpi=150, bbox_inches='tight',
            facecolor='white')
plt.close()
print("\n✅ C3 saved")
print(f"\nAll figures saved to {OUT_DIR}/")
