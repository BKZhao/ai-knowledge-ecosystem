"""
扩充图表集 - 新增10+张分析图
"""
import pandas as pd, numpy as np, json
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import warnings; warnings.filterwarnings('ignore')

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT  = f"{BASE}/results/pub_extra"
import os; os.makedirs(OUT, exist_ok=True)

# ── 颜色 ──
BLUE   = '#1565C0'; DBLUE = '#0D47A1'; GREEN = '#2E7D32'
RED    = '#C62828'; PURPLE= '#6A1B9A'; ORANGE= '#E65100'
TEAL   = '#00695C'; GRAY  = '#616161'; GOLD  = '#F57F17'
COLORS_14 = ['#1976D2','#388E3C','#D32F2F','#7B1FA2','#F57C00',
             '#0097A7','#5D4037','#455A64','#C2185B','#512DA8',
             '#00796B','#AFB42B','#0288D1','#E64A19']

CHATGPT = pd.Timestamp('2022-11-01')

def setup_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.tick_params(labelsize=9)

def add_chatgpt(ax, label=True):
    ax.axvline(CHATGPT, color='#9C27B0', lw=2, ls='--', alpha=0.75, zorder=5)
    if label:
        ax.text(CHATGPT, ax.get_ylim()[1]*0.95, 'ChatGPT', fontsize=8,
                color='#9C27B0', ha='right', va='top', rotation=90)

# ── 加载数据 ──
sp = pd.read_csv(f"{BASE}/results/stacked_panel.csv")
sp['month'] = pd.to_datetime(sp['month'])

sq = pd.read_csv(f"{BASE}/results/so_quality_monthly.csv")
sq['month'] = pd.to_datetime(sq['month'])

gq = pd.read_csv(f"{BASE}/results/github_quality_metrics.csv")
gq['month'] = pd.to_datetime(gq['month'])

se = pd.read_csv(f"{BASE}/results/se_panel_complete_2018_2026.csv")
se['month'] = pd.to_datetime(se['month'])
se = se[se['month'] >= '2018-01-01']

with open(f"{BASE}/results/classification_100k_progress.json") as f: d1 = json.load(f)
with open(f"{BASE}/results/classification_200k_extra_progress.json") as f: d2 = json.load(f)
all_labels = {**d1, **d2}

df_pq = pq.read_table(f"{BASE}/data/parquet/posts_2018plus.parquet",
    columns=['Id','PostTypeId','CreationDate','Tags']).to_pandas()
df_pq['Id'] = df_pq['Id'].astype(str)
df_q = df_pq[df_pq['PostTypeId']==1].copy()
ldf = pd.DataFrame(list(all_labels.items()), columns=['Id','label_id'])
ldf['label'] = ldf['label_id'].map({1:'How-to',2:'Debug',3:'Conceptual',4:'Architecture'})
merged = df_q.merge(ldf, on='Id')
merged['date'] = pd.to_datetime(merged['CreationDate'])
merged['year'] = merged['date'].dt.year
merged['quarter'] = merged['date'].dt.to_period('Q').astype(str)

print("数据加载完成")

# ════════════════════════════════════════════════════════
# 图E1：14语言各自趋势热图
# ════════════════════════════════════════════════════════
so_data = sp[sp['platform']=='SO'].copy()
lang_pivot = so_data.groupby(['month','language'])['activity'].sum().unstack()
lang_pivot = lang_pivot.fillna(0)
lang_pivot_norm = lang_pivot.div(lang_pivot.iloc[0], axis=1) * 100

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor('white')
im = ax.imshow(lang_pivot_norm.T.values, aspect='auto', cmap='RdYlGn_r',
               vmin=0, vmax=120, interpolation='nearest')
ax.set_yticks(range(len(lang_pivot_norm.columns)))
ax.set_yticklabels([l.upper()[:3] if l != 'csharp' else 'C#' 
                    for l in lang_pivot_norm.columns], fontsize=9)
year_ticks = [i for i, m in enumerate(lang_pivot_norm.index) if m.month == 1]
ax.set_xticks(year_ticks)
ax.set_xticklabels([lang_pivot_norm.index[i].year for i in year_ticks], fontsize=9)
chatgpt_x = list(lang_pivot_norm.index).index(pd.Timestamp('2022-11-01'))
ax.axvline(chatgpt_x, color='purple', lw=2.5, ls='--', alpha=0.8)
ax.text(chatgpt_x+0.5, -0.7, 'ChatGPT', color='purple', fontsize=9, va='top')
plt.colorbar(im, ax=ax, label='Index (Jan 2018 = 100)', shrink=0.8)
ax.set_title('Stack Overflow Activity Heatmap by Programming Language (2018–2026)\n(Normalized to Jan 2018 = 100, red = decline, green = growth)',
             fontsize=12, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig(f"{OUT}/E1_language_heatmap.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E1 saved")

# ════════════════════════════════════════════════════════
# 图E2：各语言标准化趋势（4×4 grid）
# ════════════════════════════════════════════════════════
langs_plot = ['python','javascript','typescript','java',
              'csharp','php','cpp','go',
              'rust','swift','kotlin','r',
              'scala','haskell']
so_monthly = so_data.groupby(['month','language'])['activity'].sum().reset_index()

fig, axes = plt.subplots(4, 4, figsize=(16, 12), sharey=False)
fig.patch.set_facecolor('white')
fig.suptitle('Stack Overflow Question Volume by Language (2018–2026, Normalized to Jan 2018)',
             fontsize=13, fontweight='bold', y=1.01)

for idx, lang in enumerate(langs_plot):
    row, col = idx//4, idx%4
    ax = axes[row][col]
    s = so_monthly[so_monthly['language']==lang].set_index('month')['activity']
    if len(s) == 0:
        ax.set_visible(False); continue
    base = s.iloc[0] if s.iloc[0] > 0 else 1
    s_norm = s / base * 100
    ax.fill_between(s_norm.index, s_norm.values, alpha=0.2, color=COLORS_14[idx])
    ax.plot(s_norm.index, s_norm.values, color=COLORS_14[idx], lw=1.8)
    ax.axvline(CHATGPT, color='purple', lw=1.5, ls='--', alpha=0.7)
    ax.axhline(100, color='gray', lw=0.8, ls=':', alpha=0.5)
    ax.set_title(lang.upper()[:3] if lang != 'csharp' else 'C#', fontsize=10, fontweight='bold',
                 color=COLORS_14[idx])
    final_val = s_norm.iloc[-1]
    ax.text(0.98, 0.05, f'{final_val:.0f}', transform=ax.transAxes,
            fontsize=9, color=RED if final_val < 50 else GREEN, ha='right', va='bottom', fontweight='bold')
    setup_ax(ax)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))

# 隐藏最后一格
axes[3][3].set_visible(False)
plt.tight_layout()
plt.savefig(f"{OUT}/E2_language_grid_normalized.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E2 saved")

# ════════════════════════════════════════════════════════
# 图E3：SO质量指标全面对比（雷达图 + 时序）
# ════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
fig.patch.set_facecolor('white')
fig.suptitle('Stack Overflow Quality Metrics Time Series (2018–2024)', fontsize=13, fontweight='bold')

metrics = [
    ('avg_score',    'Average Vote Score',    BLUE,   False),
    ('avg_views',    'Avg Page Views',        TEAL,   False),
    ('pct_answered', '% Answered',            GREEN,  True),
    ('pct_accepted', '% Accepted',            ORANGE, True),
    ('avg_length',   'Avg Question Length',   PURPLE, False),
    ('qa_ratio',     'Q/A Ratio',             RED,    False),
]

for idx, (col, title, color, is_pct) in enumerate(metrics):
    row, c = idx//3, idx%3
    ax = axes[row][c]
    if col not in sq.columns: ax.set_visible(False); continue

    s = sq.set_index('month')[col].dropna()
    ax.fill_between(s.index, s.values, alpha=0.15, color=color)
    ax.plot(s.index, s.values, color=color, lw=2.2, zorder=3)

    # ChatGPT线
    ax.axvline(CHATGPT, color='#9C27B0', lw=2, ls='--', alpha=0.7, zorder=5)

    # Pre/Post均值
    pre  = s[s.index < CHATGPT].mean()
    post = s[s.index >= CHATGPT].mean()
    ax.axhline(pre,  color=color, lw=1.2, ls=':', alpha=0.6)
    ax.axhline(post, color=color, lw=1.2, ls='-.', alpha=0.6)
    chg = (post-pre)/pre*100 if pre != 0 else 0
    ax.text(0.03, 0.08, f'Δ = {chg:+.1f}%', transform=ax.transAxes,
            fontsize=9, fontweight='bold',
            color=GREEN if chg > 0 else RED,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    ax.set_title(title, fontsize=10, fontweight='bold', color=color)
    setup_ax(ax)
    if is_pct:
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT}/E3_so_quality_full.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E3 saved")

# ════════════════════════════════════════════════════════
# 图E4：GitHub质量指标——Fork率/Star率语言对比
# ════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor('white')
fig.suptitle('GitHub Repository Quality Metrics by Language (2018–2026)', fontsize=13, fontweight='bold')

langs_gh = ['python','javascript','typescript','java','go','rust']
colors_gh = [COLORS_14[0],COLORS_14[1],COLORS_14[2],COLORS_14[3],COLORS_14[4],COLORS_14[7]]
metric_pairs = [
    (0, 0, 'total',  'Total New Repositories', False),
    (0, 1, 'active', 'Active Repository Rate', True),
    (1, 0, 'forked', 'Fork Rate (%)', True),
    (1, 1, 'starred','Star Rate (%)', True),
]

for r, c, metric_suffix, title, is_rate in metric_pairs:
    ax = axes[r][c]
    for lang, color in zip(langs_gh, colors_gh):
        col = f'{metric_suffix}_{lang}'
        if col not in gq.columns: continue
        s = gq.set_index('month')[col].dropna()
        if is_rate:
            # 计算率
            total_col = f'total_{lang}'
            if total_col not in gq.columns: continue
            total = gq.set_index('month')[total_col].reindex(s.index)
            if metric_suffix in ['forked','starred'] and total.mean() > 0:
                s = s / total * 100
            base = s.iloc[0] if not is_rate or metric_suffix == 'active' else None
            if metric_suffix == 'active':
                s = s * 100
        else:
            base = s.iloc[0] if s.iloc[0] > 0 else 1
            s = s / base * 100

        ax.plot(s.index, s.values, color=color, lw=1.8, label=lang, alpha=0.85)

    ax.axvline(CHATGPT, color='#9C27B0', lw=2, ls='--', alpha=0.7)
    if not is_rate:
        ax.axhline(100, color='gray', lw=0.8, ls=':')
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.legend(fontsize=8, ncol=2, loc='upper left')
    setup_ax(ax)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT}/E4_github_quality_by_lang.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E4 saved")

# ════════════════════════════════════════════════════════
# 图E5：问题类型×语言热图
# ════════════════════════════════════════════════════════
lang_labels = ['python','javascript','typescript','java','csharp','php','cpp','go','rust','r','swift','kotlin','scala','haskell']
label_names = ['How-to','Debug','Conceptual','Architecture']

# 构建矩阵
matrix = np.zeros((len(lang_labels), len(label_names)))
for li, lang in enumerate(lang_labels):
    tag = 'c#' if lang == 'csharp' else lang
    mask = merged['Tags'].str.contains(tag, case=False, na=False)
    sub = merged[mask]
    if len(sub) > 50:
        dist = sub['label'].value_counts()
        for lj, lname in enumerate(label_names):
            matrix[li, lj] = dist.get(lname, 0) / len(sub) * 100

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor('white')
im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd', vmin=0, vmax=70)
ax.set_xticks(range(4))
ax.set_xticklabels(label_names, fontsize=11)
ax.set_yticks(range(len(lang_labels)))
ax.set_yticklabels([l.upper()[:3] if l not in ['csharp','haskell'] else ('C#' if l=='csharp' else 'HKL')
                    for l in lang_labels], fontsize=10)
for i in range(len(lang_labels)):
    for j in range(len(label_names)):
        ax.text(j, i, f'{matrix[i,j]:.0f}%', ha='center', va='center',
                fontsize=9, fontweight='bold',
                color='white' if matrix[i,j] > 40 else 'black')
plt.colorbar(im, ax=ax, label='Proportion (%)', shrink=0.8)
ax.set_title('Question Type Distribution by Programming Language\n(N = 112,723 classified questions)',
             fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Question Type', fontsize=11)
ax.set_ylabel('Programming Language', fontsize=11)
plt.tight_layout()
plt.savefig(f"{OUT}/E5_type_by_language_heatmap.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E5 saved")

# ════════════════════════════════════════════════════════
# 图E6：Debug崩塌详细分析（2018-2020聚焦）
# ════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('white')
fig.suptitle('The Debug Collapse: Pre-ChatGPT Structural Shift (2018–2022)', fontsize=13, fontweight='bold')

quarterly = merged.groupby(['quarter','label']).size().unstack(fill_value=0)
quarterly_pct = quarterly.div(quarterly.sum(axis=1), axis=0) * 100

ax = axes[0]
for lbl, color in zip(['How-to','Debug','Conceptual','Architecture'],
                       [BLUE, RED, GREEN, ORANGE]):
    if lbl in quarterly_pct.columns:
        vals = quarterly_pct[lbl].values
        qx = range(len(vals))
        ax.plot(qx, vals, color=color, lw=2.5, label=lbl, marker='o', ms=3.5)

quarters_list = list(quarterly_pct.index)
# 2019Q1
q2019 = quarters_list.index('2019Q1') if '2019Q1' in quarters_list else 4
ax.axvline(q2019, color='gray', lw=2, ls=':', alpha=0.7, label='2019 Start')
ax.text(q2019+0.2, 30, 'Debug\ncollapse\n(2019)', fontsize=8.5, color=RED, va='top')
# ChatGPT
chatgpt_q = '2022Q4'
if chatgpt_q in quarters_list:
    qcgpt = quarters_list.index(chatgpt_q)
    ax.axvline(qcgpt, color='#9C27B0', lw=2, ls='--', alpha=0.75)
    ax.text(qcgpt+0.2, 52, 'ChatGPT', fontsize=8.5, color='#9C27B0', va='top')

year_ticks = [i for i, q in enumerate(quarters_list) if q.endswith('Q1')]
ax.set_xticks(year_ticks)
ax.set_xticklabels([q[:4] for q in quarters_list if q.endswith('Q1')], fontsize=9)
ax.set_ylabel('Share (%)', fontsize=10)
ax.set_title('Quarterly Question Type Proportions', fontsize=11, fontweight='bold')
ax.legend(fontsize=9, loc='center right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))

# 右图：Debug按语言分析
ax2 = axes[1]
debug_by_year_lang = {}
for lang in ['python','javascript','java','php','typescript']:
    tag = lang
    mask = merged['Tags'].str.contains(tag, case=False, na=False)
    sub = merged[mask]
    by_year = sub.groupby('year')['label'].apply(lambda x: (x=='Debug').sum()/len(x)*100)
    debug_by_year_lang[lang] = by_year

years = list(range(2018, 2025))
for (lang, series), color in zip(debug_by_year_lang.items(), COLORS_14[:5]):
    vals = [series.get(y, np.nan) for y in years]
    ax2.plot(years, vals, color=color, lw=2.2, marker='o', ms=5, label=lang)

ax2.axvline(2019.5, color='gray', lw=2, ls=':', alpha=0.7)
ax2.axvline(2022.9, color='#9C27B0', lw=2, ls='--', alpha=0.75)
ax2.set_xticks(years)
ax2.set_xticklabels(years, fontsize=9)
ax2.set_ylabel('Debug Question Share (%)', fontsize=10)
ax2.set_title('Debug Share by Language (2018–2024)', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))

plt.tight_layout()
plt.savefig(f"{OUT}/E6_debug_collapse_detail.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E6 saved")

# ════════════════════════════════════════════════════════
# 图E7：SO vs GitHub 绝对数量双轴（完整版）
# ════════════════════════════════════════════════════════
so_total = sp[sp['platform']=='SO'].groupby('month')['activity'].sum()
gh_total = sp[sp['platform']=='GitHub'].groupby('month')['activity'].sum()

fig, ax1 = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
ax2 = ax1.twinx()

ax1.fill_between(so_total.index, so_total.values/1000, alpha=0.15, color=RED)
ax1.plot(so_total.index, so_total.values/1000, color=RED, lw=2.5, label='Stack Overflow (left)')
ax2.fill_between(gh_total.index, gh_total.values/1e6, alpha=0.12, color=BLUE)
ax2.plot(gh_total.index, gh_total.values/1e6, color=BLUE, lw=2.5, ls='--', label='GitHub (right)')

ax1.axvline(CHATGPT, color='#9C27B0', lw=2.5, ls='--', alpha=0.8)
ax1.text(CHATGPT, ax1.get_ylim()[1]*0.95 if ax1.get_ylim()[1]>0 else 800,
         'ChatGPT', fontsize=10, color='#9C27B0', va='top', ha='right', rotation=90)

ax1.set_ylabel('SO Weekly Questions (thousands)', fontsize=11, color=RED)
ax2.set_ylabel('GitHub Monthly Repos (millions)', fontsize=11, color=BLUE)
ax1.tick_params(axis='y', labelcolor=RED)
ax2.tick_params(axis='y', labelcolor=BLUE)
ax1.set_title('Stack Overflow vs GitHub: Absolute Volume Divergence (2018–2026)\n'
              'SO: −98.5% | GitHub: +536.2%', fontsize=13, fontweight='bold')
ax1.xaxis.set_major_locator(mdates.YearLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labels1+labels2, fontsize=10, loc='upper left')
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)

# 标注关键节点
so_2018 = so_total.loc['2018-01-01']/1000 if pd.Timestamp('2018-01-01') in so_total.index else 0
so_2026 = so_total.iloc[-1]/1000
ax1.annotate(f'Peak: {so_2018:.0f}k', xy=(so_total.index[0], so_2018),
             fontsize=9, color=RED, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
ax1.annotate(f'Now: {so_2026:.1f}k', xy=(so_total.index[-1], so_2026),
             xytext=(-100, 20), textcoords='offset points',
             fontsize=9, color=RED,
             arrowprops=dict(arrowstyle='->', color=RED),
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(f"{OUT}/E7_so_github_absolute.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E7 saved")

# ════════════════════════════════════════════════════════
# 图E8：加速效应——年同比下降率
# ════════════════════════════════════════════════════════
so_monthly_total = sp[sp['platform']=='SO'].groupby('month')['activity'].sum()
so_yoy = so_monthly_total.pct_change(12) * 100  # 年同比

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('white')

ax = axes[0]
colors_bar = [RED if v < 0 else GREEN for v in so_yoy.dropna().values]
ax.bar(so_yoy.dropna().index, so_yoy.dropna().values, width=25, color=colors_bar, alpha=0.8)
ax.axvline(CHATGPT, color='#9C27B0', lw=2.5, ls='--', alpha=0.8)
ax.axhline(0, color='black', lw=1)
ax.set_title('SO Year-over-Year Change Rate\n(Monthly, 2019–2026)', fontsize=11, fontweight='bold')
ax.set_ylabel('YoY Change (%)', fontsize=10)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 标注加速
for year, rate in [(2022, -41), (2023, -49), (2024, -70)]:
    ax.annotate(f'{year}→{year+1}\n{rate}%',
                xy=(pd.Timestamp(f'{year}-11-01'), rate-3),
                fontsize=8, color=RED, ha='center',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# 右图：各语言YoY热图
ax2 = axes[1]
yoy_by_lang = {}
for lang in sp['language'].unique():
    s = sp[sp['platform']=='SO'][sp['language']==lang].groupby('month')['activity'].sum()
    yoy_by_lang[lang] = s.pct_change(12) * 100

yoy_df = pd.DataFrame(yoy_by_lang).dropna()
# 只保留2019-2026
yoy_df = yoy_df[(yoy_df.index >= '2019-01-01')]

im = ax2.imshow(yoy_df.T.values, aspect='auto', cmap='RdYlGn',
                vmin=-100, vmax=50, interpolation='nearest')
ax2.set_yticks(range(len(yoy_df.columns)))
ax2.set_yticklabels([l[:4].upper() if l != 'csharp' else 'C#' for l in yoy_df.columns], fontsize=8)
year_ticks2 = [i for i, m in enumerate(yoy_df.index) if m.month == 1]
ax2.set_xticks(year_ticks2)
ax2.set_xticklabels([yoy_df.index[i].year for i in year_ticks2], fontsize=9)
cgpt_candidates = [i for i, m in enumerate(yoy_df.index) if m.year==2022 and m.month>=11]
if cgpt_candidates:
    ax2.axvline(cgpt_candidates[0], color='purple', lw=2.5, ls='--')
plt.colorbar(im, ax=ax2, label='YoY Change (%)', shrink=0.8)
ax2.set_title('YoY Change Heatmap by Language\n(Red = decline, Green = growth)',
              fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(f"{OUT}/E8_acceleration_analysis.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E8 saved")

# ════════════════════════════════════════════════════════
# 图E9：Conceptual问题上升的语言差异
# ════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.patch.set_facecolor('white')
fig.suptitle('How-to vs Conceptual Inversion by Programming Language', fontsize=13, fontweight='bold')

focus_langs = [('python','Python'),('javascript','JavaScript'),('typescript','TypeScript'),
               ('java','Java'),('csharp','C#'),('rust','Rust')]

for idx, (lang, lang_name) in enumerate(focus_langs):
    row, col = idx//3, idx%3
    ax = axes[row][col]
    tag = 'c#' if lang == 'csharp' else lang
    mask = merged['Tags'].str.contains(tag, case=False, na=False)
    sub = merged[mask]
    by_q = sub.groupby('quarter')['label'].value_counts(normalize=True).unstack(fill_value=0) * 100
    by_q.index = [str(q) for q in by_q.index]
    qs = list(by_q.index)
    qx = range(len(qs))

    for lbl, color in [('How-to', BLUE), ('Conceptual', GREEN)]:
        if lbl in by_q.columns:
            ax.plot(qx, by_q[lbl].values, color=color, lw=2.2, label=lbl, marker='o', ms=2.5)
    ax.fill_between(qx, by_q.get('How-to', pd.Series(0, index=range(len(qs)))).values,
                    by_q.get('Conceptual', pd.Series(0, index=range(len(qs)))).values,
                    alpha=0.15, color='gray')

    chatgpt_q = '2022Q4'
    if chatgpt_q in qs:
        ax.axvline(qs.index(chatgpt_q), color='#9C27B0', lw=1.8, ls='--', alpha=0.7)

    year_ticks_q = [i for i, q in enumerate(qs) if q.endswith('Q1')]
    ax.set_xticks(year_ticks_q)
    ax.set_xticklabels([q[:4] for q in qs if q.endswith('Q1')], fontsize=8)
    ax.set_title(lang_name, fontsize=11, fontweight='bold', color=COLORS_14[idx])
    ax.set_ylabel('%', fontsize=9)
    ax.legend(fontsize=8, loc='lower right' if lang in ['typescript','rust'] else 'upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))

plt.tight_layout()
plt.savefig(f"{OUT}/E9_howto_conceptual_by_lang.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E9 saved")

# ════════════════════════════════════════════════════════
# 图E10：GitHub vs SO散点图（各语言，两期对比）
# ════════════════════════════════════════════════════════
pre_mask  = (sp['month'] >= '2020-01-01') & (sp['month'] < '2022-11-01')
post_mask = (sp['month'] >= '2023-01-01') & (sp['month'] <= '2026-02-01')

pre_so  = sp[sp['platform']=='SO' & pre_mask].groupby('language')['activity'].mean()
post_so = sp[sp['platform']=='SO' & post_mask].groupby('language')['activity'].mean()
pre_gh  = sp[sp['platform']=='GitHub' & pre_mask].groupby('language')['activity'].mean()
post_gh = sp[sp['platform']=='GitHub' & post_mask].groupby('language')['activity'].mean()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('white')
fig.suptitle('SO Decline vs GitHub Growth by Language: Before vs After ChatGPT', fontsize=12, fontweight='bold')

for ax, (so_data_p, gh_data_p, period, color) in zip(axes, [
    (pre_so, pre_gh, 'Pre-ChatGPT (2020-2022)', BLUE),
    (post_so, post_gh, 'Post-ChatGPT (2023-2026)', RED),
]):
    langs_common = so_data_p.index.intersection(gh_data_p.index)
    so_vals = so_data_p.loc[langs_common]
    gh_vals = gh_data_p.loc[langs_common]
    ax.scatter(so_vals.values/1000, gh_vals.values/1000, s=80, color=color, alpha=0.8, zorder=5)
    for lang in langs_common:
        short = lang[:4].upper() if lang != 'csharp' else 'C#'
        ax.annotate(short, (so_vals[lang]/1000, gh_vals[lang]/1000),
                    textcoords='offset points', xytext=(4,2), fontsize=7, alpha=0.8)
    ax.set_xlabel('SO Questions (thousands/month)', fontsize=10)
    ax.set_ylabel('GitHub Repos (thousands/month)', fontsize=10)
    ax.set_title(period, fontsize=11, fontweight='bold', color=color)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT}/E10_so_github_scatter.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E10 saved")

# ════════════════════════════════════════════════════════
# 图E11：SE哲学社区深度分析
# ════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('white')
fig.suptitle('Philosophy SE: The Only Growing Community in the AI Era', fontsize=12, fontweight='bold')

ax = axes[0]
# 哲学 vs SO vs Travel（三线对比，归一化）
groups = {
    'Philosophy SE (+54.6%)': (se['philosophy_questions'].dropna(), '#E91E63'),
    'Stack Overflow (−77.4%)': (sp[sp['platform']=='SO'].groupby('month')['activity'].sum(), RED),
    'Travel SE (−18%)':        (se['travel_questions'].dropna(), BLUE),
    'Physics SE (−47.1%)':     (se['physics_questions'].dropna(), TEAL),
}
for label, (series, color) in groups.items():
    if len(series) == 0: continue
    base = series.iloc[0] if series.iloc[0] > 0 else 1
    s_norm = series / base * 100
    ax.plot(s_norm.index, s_norm.values, color=color, lw=2.5 if 'Philosophy' in label else 2,
            label=label, zorder=5 if 'Philosophy' in label else 3,
            ls='-' if 'Philosophy' in label else '--')

ax.axvline(CHATGPT, color='#9C27B0', lw=2, ls='--', alpha=0.7)
ax.axhline(100, color='gray', lw=0.8, ls=':', alpha=0.5)
ax.text(CHATGPT, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 200,
        'ChatGPT', fontsize=9, color='#9C27B0', va='top', ha='right', rotation=90)
ax.set_title('Philosophy vs Other Communities\n(Normalized to Jan 2018 = 100)', fontsize=10, fontweight='bold')
ax.legend(fontsize=8.5, loc='upper left')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_ylabel('Index (2018-01 = 100)', fontsize=10)

# 右图：所有社区按变化排序的水平条
ax2 = axes[1]
changes = {
    'SO (Programming)': -77.4, 'English': -68.7, 'DataSci': -66.5,
    'Biology': -58.9, 'CogSci': -55.8, 'Music': -56.3,
    'Chemistry': -52.8, 'Statistics': -52.0, 'Astronomy': -51.8,
    'Physics': -47.1, 'AI.SE': -43.9, 'Academia': -43.4,
    'Linguistics': -42.5, 'Politics': -42.4, 'Law': -40.1,
    'Cooking': -36.7, 'History': -36.2, 'Literature': -30.0,
    'Movies': -29.0, 'Economics': -22.6, 'Travel': -18.0,
    'Philosophy': +54.6,
}
sorted_changes = sorted(changes.items(), key=lambda x: x[1])
names_s = [x[0] for x in sorted_changes]
vals_s  = [x[1] for x in sorted_changes]
colors_s = [GREEN if v > 0 else RED for v in vals_s]
bars = ax2.barh(names_s, vals_s, color=colors_s, alpha=0.85, edgecolor='white')
ax2.axvline(0, color='black', lw=1)
ax2.set_xlabel('Change % (Post vs Pre ChatGPT)', fontsize=10)
ax2.set_title('All 22 Communities: Post-ChatGPT Change', fontsize=10, fontweight='bold')
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
ax2.tick_params(axis='y', labelsize=8)
for bar, val in zip(bars, vals_s):
    ax2.text(val + (1 if val >= 0 else -1), bar.get_y() + bar.get_height()/2,
             f'{val:+.0f}%', va='center', ha='left' if val >= 0 else 'right', fontsize=7.5)

plt.tight_layout()
plt.savefig(f"{OUT}/E11_philosophy_analysis.png", dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ E11 saved")

print(f"\n✅ 所有图表生成完毕！保存于 {OUT}/")
print("生成了 E1-E11，共11张新图")
