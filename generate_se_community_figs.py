"""
SE多社区对比分析图 - 完整版（2018-2026）
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import os, warnings
warnings.filterwarnings('ignore')

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT = f"{BASE}/results/pub_se_update"
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(f"{BASE}/results/se_panel_complete_2018_2026.csv")
df['month'] = pd.to_datetime(df['month'])
df = df.set_index('month').sort_index()

CHATGPT = pd.Timestamp('2022-11-01')

# 归一化到2018-01=100
BASE_MONTH = '2018-01-01'
def normalize(s):
    base = s.loc[BASE_MONTH] if BASE_MONTH in s.index else s.dropna().iloc[0]
    if base == 0 or pd.isna(base): return s
    return s / base * 100

# 分组
GROUPS = {
    'Tech (SE)':        ['physics_questions','stats_questions','datascience_questions','ai_questions'],
    'Humanities (SE)':  ['english_questions','linguistics_questions','literature_questions'],
    'Social Science':   ['politics_questions','law_questions','economics_questions','academia_questions'],
    'Natural Science':  ['biology_questions','chemistry_questions','astronomy_questions'],
}
GROUP_COLORS = {
    'Tech (SE)':       ['#1976D2','#0288D1','#00838F','#006064'],
    'Humanities (SE)': ['#7B1FA2','#AD1457','#C62828'],
    'Social Science':  ['#E65100','#F57F17','#558B2F','#1B5E20'],
    'Natural Science': ['#2E7D32','#1565C0','#6A1B9A'],
}
SHORT_NAMES = {
    'physics_questions':'Physics','stats_questions':'Stats',
    'datascience_questions':'DataSci','ai_questions':'AI.SE',
    'english_questions':'English','linguistics_questions':'Linguistics',
    'literature_questions':'Literature','cooking_questions':'Cooking',
    'politics_questions':'Politics','law_questions':'Law',
    'economics_questions':'Economics','academia_questions':'Academia',
    'biology_questions':'Biology','chemistry_questions':'Chemistry',
    'astronomy_questions':'Astronomy','music_questions':'Music',
    'movies_questions':'Movies','travel_questions':'Travel',
    'history_questions':'History','philosophy_questions':'Philosophy',
    'so_questions':'Stack Overflow',
}

# ─────────────────────────────────────────────────────────
# 图1：分组时序图
# ─────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor('white')
gs = GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.32)

so_norm = normalize(df['so_questions'].dropna())

for idx, (grp_name, cols) in enumerate(GROUPS.items()):
    ax = fig.add_subplot(gs[idx//2, idx%2])
    colors = GROUP_COLORS[grp_name]

    for col, color in zip(cols, colors):
        if col not in df.columns: continue
        s = df[col].dropna()
        s_norm = normalize(s)
        ax.plot(s_norm.index, s_norm.values, color=color, lw=1.8,
                label=SHORT_NAMES.get(col, col), alpha=0.85)

    # SO 参照线（粗黑）
    ax.plot(so_norm.index, so_norm.values, color='black', lw=2.5,
            ls='--', label='Stack Overflow', alpha=0.6, zorder=5)

    # ChatGPT线
    ax.axvline(CHATGPT, color='#9C27B0', lw=1.8, ls=':', alpha=0.8)
    ax.text(CHATGPT, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 120,
            'ChatGPT', fontsize=8, color='#9C27B0', rotation=90, va='top', ha='right')

    ax.axhline(100, color='gray', lw=0.8, ls=':', alpha=0.5)
    ax.set_title(grp_name, fontsize=12, fontweight='bold', color=colors[0], pad=7)
    ax.legend(fontsize=8, loc='lower left', framealpha=0.85, ncol=2)
    ax.set_ylabel('Index (2018-01 = 100)', fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # x轴年份
    ax.xaxis.set_major_locator(matplotlib.dates.YearLocator())
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
    ax.tick_params(axis='x', labelsize=8)

fig.suptitle('SE Communities: Question Volume Index (2018–2026)\n(Normalized to Jan 2018 = 100, dashed = Stack Overflow)',
             fontsize=13, fontweight='bold', y=1.01)
plt.savefig(f"{OUT}/SE1_community_groups.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✅ SE1 saved: {OUT}/SE1_community_groups.png")

# ─────────────────────────────────────────────────────────
# 图2：影响热图（变化%）
# ─────────────────────────────────────────────────────────
all_cols = [c for c in df.columns if c != 'so_questions' and not df[c].isna().all()]

pre_mask  = (df.index >= '2020-01-01') & (df.index < '2022-11-01')
post_mask = (df.index >= '2023-01-01') & (df.index <= '2026-02-01')

changes = {}
for col in all_cols:
    s = df[col].dropna()
    pre  = s[(s.index >= '2020-01-01') & (s.index < '2022-11-01')].mean()
    post = s[(s.index >= '2023-01-01') & (s.index <= '2026-02-01')].mean()
    if pre > 0 and not pd.isna(pre) and not pd.isna(post):
        changes[col] = (post - pre) / pre * 100

# SO
so_pre  = df['so_questions'][(df.index >= '2020-01-01') & (df.index < '2022-11-01')].mean()
so_post = df['so_questions'][(df.index >= '2023-01-01') & (df.index <= '2026-02-01')].mean()
so_change = (so_post - so_pre) / so_pre * 100
changes['so_questions'] = so_change

changes_df = pd.Series(changes).sort_values()
names  = [SHORT_NAMES.get(c, c) for c in changes_df.index]
colors_bar = ['#C62828' if v < 0 else '#2E7D32' for v in changes_df.values]

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
bars = ax.barh(names, changes_df.values, color=colors_bar, alpha=0.82, edgecolor='white')

# SO标注
so_idx = list(changes_df.index).index('so_questions')
bars[so_idx].set_edgecolor('black')
bars[so_idx].set_linewidth(2)

ax.axvline(0, color='black', lw=1, ls='-')
ax.axvline(so_change, color='black', lw=2, ls='--', alpha=0.6, label=f'SO baseline ({so_change:.0f}%)')
ax.set_xlabel('Change % (Post-ChatGPT 2023-2026 vs Pre-ChatGPT 2020-2022)', fontsize=10)
ax.set_title('Question Volume Change After ChatGPT — Stack Exchange Communities', fontsize=12, fontweight='bold')
ax.legend(fontsize=9)
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%+.0f%%'))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(labelsize=9)

# 数值标注
for bar, val in zip(bars, changes_df.values):
    ax.text(val + (1 if val >= 0 else -1), bar.get_y() + bar.get_height()/2,
            f'{val:+.0f}%', va='center', ha='left' if val >= 0 else 'right', fontsize=7.5)

plt.tight_layout()
plt.savefig(f"{OUT}/SE2_impact_heatmap.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✅ SE2 saved: {OUT}/SE2_impact_heatmap.png")

# ─────────────────────────────────────────────────────────
# 图3：SO vs Non-tech SE 双轴对比
# ─────────────────────────────────────────────────────────
non_tech_cols = ['english_questions','linguistics_questions','literature_questions',
                 'politics_questions','law_questions','economics_questions',
                 'music_questions','movies_questions','travel_questions']
non_tech_cols = [c for c in non_tech_cols if c in df.columns]

# 月度均值（归一化后）
non_tech_norm = pd.DataFrame({c: normalize(df[c].dropna()) for c in non_tech_cols})
non_tech_avg = non_tech_norm.mean(axis=1).dropna()
so_norm2 = normalize(df['so_questions'].dropna())

fig, ax1 = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor('white')
ax2 = ax1.twinx()

# 填充区
common_idx = so_norm2.index.intersection(non_tech_avg.index)
ax1.fill_between(so_norm2.loc[common_idx].index, so_norm2.loc[common_idx].values,
                 alpha=0.12, color='#1976D2')
ax2.fill_between(non_tech_avg.loc[common_idx].index, non_tech_avg.loc[common_idx].values,
                 alpha=0.12, color='#E65100')

l1, = ax1.plot(so_norm2.index, so_norm2.values, color='#1976D2', lw=2.8, label='Stack Overflow')
l2, = ax2.plot(non_tech_avg.index, non_tech_avg.values, color='#E65100', lw=2.8,
               ls='--', label='Non-Tech SE (avg)')

ax1.axvline(CHATGPT, color='#9C27B0', lw=2, ls='--', alpha=0.7)
ax1.text(CHATGPT, 5, 'ChatGPT\nNov 2022', fontsize=9, color='#9C27B0', va='bottom')
ax1.axhline(100, color='gray', lw=0.8, ls=':', alpha=0.5)

# 最终值标注
so_final = so_norm2.iloc[-1]
nt_final = non_tech_avg.iloc[-1]
ax1.annotate(f'SO: {so_final:.0f}', xy=(so_norm2.index[-1], so_final),
             fontsize=10, fontweight='bold', color='#1976D2',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
ax2.annotate(f'Non-tech: {nt_final:.0f}', xy=(non_tech_avg.index[-1], nt_final),
             fontsize=10, fontweight='bold', color='#E65100',
             xytext=(-100, 15), textcoords='offset points',
             arrowprops=dict(arrowstyle='->', color='#E65100', lw=1.5),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='moccasin', alpha=0.8))

ax1.set_ylabel('Stack Overflow Index (2018-01=100)', fontsize=10, color='#1976D2')
ax2.set_ylabel('Non-Tech SE Index (2018-01=100)', fontsize=10, color='#E65100')
ax1.tick_params(axis='y', labelcolor='#1976D2')
ax2.tick_params(axis='y', labelcolor='#E65100')
ax1.set_title('Stack Overflow vs Non-Technical Stack Exchange\n(Index 2018-01=100)', 
              fontsize=12, fontweight='bold')
ax1.xaxis.set_major_locator(matplotlib.dates.YearLocator())
ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
ax1.spines['top'].set_visible(False)
lines = [l1, l2]
ax1.legend(lines, [l.get_label() for l in lines], fontsize=10, loc='upper right')

plt.tight_layout()
plt.savefig(f"{OUT}/SE3_so_vs_nontech.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✅ SE3 saved: {OUT}/SE3_so_vs_nontech.png")

# ─────────────────────────────────────────────────────────
# 打印关键数字
# ─────────────────────────────────────────────────────────
print("\n=== 关键数字：ChatGPT前后变化 ===")
print(f"{'社区':20s} {'Pre均值':>10} {'Post均值':>10} {'变化%':>8}")
print("-"*52)
for col, chg in sorted(changes.items(), key=lambda x: x[1]):
    name = SHORT_NAMES.get(col, col)
    s = df[col] if col in df.columns else df.get(col, pd.Series())
    pre_v  = s[(s.index >= '2020-01-01') & (s.index < '2022-11-01')].mean() if col in df.columns else 0
    post_v = s[(s.index >= '2023-01-01') & (s.index <= '2026-02-01')].mean() if col in df.columns else 0
    print(f"{name:20s} {pre_v:10.0f} {post_v:10.0f} {chg:+8.1f}%")

print(f"\n✅ 所有图表保存至: {OUT}/")
