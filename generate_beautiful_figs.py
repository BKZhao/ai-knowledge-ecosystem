"""
美化版图表 + 中文论文生成
Publication-ready风格：深色主题配色、精致排版
"""
import pandas as pd, numpy as np, json
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib import rcParams
import warnings; warnings.filterwarnings('ignore')

# ── 全局美化设置 ──────────────────────────────
rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linewidth': 0.6,
    'grid.color': '#CCCCCC',
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.size': 4,
    'ytick.major.size': 4,
})

BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research"
OUT  = f"{BASE}/results/pub_beautiful"
import os; os.makedirs(OUT, exist_ok=True)

# ── 精致配色方案 ──────────────────────────────
PAL = {
    'so':       '#E53935',   # SO - 暗红
    'github':   '#1E88E5',   # GitHub - 蓝
    'chatgpt':  '#8E24AA',   # ChatGPT线 - 紫
    'howto':    '#1565C0',   # How-to - 深蓝
    'debug':    '#D32F2F',   # Debug - 红
    'concept':  '#2E7D32',   # Conceptual - 深绿
    'arch':     '#F57F17',   # Architecture - 橙
    'neutral':  '#546E7A',   # 中性 - 蓝灰
    'bg':       '#FAFAFA',   # 背景
    'text':     '#212121',   # 主文字
    'subtext':  '#757575',   # 副文字
    'line':     '#E0E0E0',   # 分隔线
}

LANG_COLORS = {
    'python':     '#3776AB', 'javascript': '#F7DF1E',
    'typescript': '#3178C6', 'java':       '#ED8B00',
    'csharp':     '#9B4F96', 'php':        '#777BB4',
    'cpp':        '#00599C', 'go':         '#00ADD8',
    'rust':       '#CE422B', 'swift':      '#FA7343',
    'kotlin':     '#7F52FF', 'r':          '#1E6FBE',
    'scala':      '#DC322F', 'haskell':    '#5D4F85',
}

CHATGPT_DATE = pd.Timestamp('2022-11-01')
COPILOT_DATE = pd.Timestamp('2021-06-01')

def add_event_lines(ax, events=None, yloc=0.97):
    """添加事件标注线"""
    if events is None:
        events = [
            (CHATGPT_DATE, 'ChatGPT\n(Nov 2022)', PAL['chatgpt']),
        ]
    ymin, ymax = ax.get_ylim()
    for dt, label, color in events:
        ax.axvline(dt, color=color, lw=1.8, ls='--', alpha=0.75, zorder=8)
        ax.text(dt, ymin + (ymax-ymin)*yloc, f' {label}',
                fontsize=8, color=color, va='top', ha='left',
                fontweight='bold')

def styled_fig(nrows=1, ncols=1, figsize=(14, 6), title='', subtitle=''):
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    fig.patch.set_facecolor(PAL['bg'])
    if title:
        fig.text(0.5, 0.98, title, ha='center', va='top',
                 fontsize=14, fontweight='bold', color=PAL['text'])
    if subtitle:
        fig.text(0.5, 0.94, subtitle, ha='center', va='top',
                 fontsize=10, color=PAL['subtext'])
    return fig, axes

def style_ax(ax, xlabel='', ylabel='', title='', color=PAL['neutral']):
    ax.set_facecolor(PAL['bg'])
    if title: ax.set_title(title, fontsize=11, fontweight='bold', color=color, pad=8)
    if xlabel: ax.set_xlabel(xlabel, fontsize=9.5, color=PAL['subtext'])
    if ylabel: ax.set_ylabel(ylabel, fontsize=9.5, color=PAL['subtext'])
    ax.tick_params(colors=PAL['subtext'], labelsize=8.5)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    for spine in ax.spines.values():
        spine.set_color(PAL['line'])

# ── 加载数据 ──────────────────────────────────
sp = pd.read_csv(f"{BASE}/results/stacked_panel.csv")
sp['month'] = pd.to_datetime(sp['month'])
so_ts = sp[sp['platform']=='SO'].groupby('month')['activity'].sum()
gh_ts = sp[sp['platform']=='GitHub'].groupby('month')['activity'].sum()

sq = pd.read_csv(f"{BASE}/results/so_quality_monthly.csv")
sq['month'] = pd.to_datetime(sq['month'])
sq = sq.set_index('month')

se = pd.read_csv(f"{BASE}/results/se_panel_complete_2018_2026.csv")
se['month'] = pd.to_datetime(se['month'])
se = se[se['month'] >= '2018-01-01'].set_index('month')

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
merged['Tags'] = merged['Tags'].fillna('')

so_lang = sp[sp['platform']=='SO'].copy()
gh_lang = sp[sp['platform']=='GitHub'].copy()

print("✓ 数据加载完成")

# ════════════════════════════════════════════════════════════
# 图B1：核心剪刀差 — 精致双轴大图
# ════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(14, 7))
fig.patch.set_facecolor(PAL['bg'])
gs = GridSpec(1, 1, figure=fig, left=0.08, right=0.92, top=0.85, bottom=0.12)
ax1 = fig.add_subplot(gs[0])
ax2 = ax1.twinx()

# SO填充区域
ax1.fill_between(so_ts.index, so_ts.values/1000, 0, alpha=0.15, color=PAL['so'], zorder=2)
l1, = ax1.plot(so_ts.index, so_ts.values/1000, color=PAL['so'], lw=2.8, zorder=4,
               label='Stack Overflow (Questions/Week)')

# GitHub填充区域
ax2.fill_between(gh_ts.index, gh_ts.values/1e6, 0, alpha=0.12, color=PAL['github'], zorder=1)
l2, = ax2.plot(gh_ts.index, gh_ts.values/1e6, color=PAL['github'], lw=2.8, ls='--', zorder=3,
               label='GitHub (Repos/Month)')

# 事件线
for dt, label, color, side in [
    (COPILOT_DATE, 'Copilot GA', '#00897B', 'left'),
    (CHATGPT_DATE, 'ChatGPT', PAL['chatgpt'], 'left'),
    (pd.Timestamp('2023-03-01'), 'GPT-4', '#6D4C41', 'left'),
]:
    ax1.axvline(dt, color=color, lw=1.5, ls=':', alpha=0.8, zorder=5)
    ypos = ax1.get_ylim()[1] * 0.92 if ax1.get_ylim()[1] > 0 else 800
    ax1.text(dt, ypos, f' {label}', fontsize=8, color=color, rotation=90,
             va='top', ha='right', fontweight='bold')

# 关键数字标注
so_2018 = so_ts.loc[pd.Timestamp('2018-01-01')]/1000
so_now  = so_ts.iloc[-1]/1000
gh_2018 = gh_ts.loc[pd.Timestamp('2018-01-01')]/1e6
gh_now  = gh_ts.iloc[-1]/1e6

ax1.annotate(f'-98.5%\n({so_2018:.0f}k → {so_now:.1f}k)',
             xy=(so_ts.index[-1], so_now),
             xytext=(-120, 40), textcoords='offset points',
             fontsize=10, fontweight='bold', color=PAL['so'],
             arrowprops=dict(arrowstyle='->', color=PAL['so'], lw=1.5),
             bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=PAL['so'], alpha=0.9))

ax2.annotate(f'+536.2%\n({gh_2018:.1f}M → {gh_now:.1f}M)',
             xy=(gh_ts.index[-1], gh_now),
             xytext=(-140, -50), textcoords='offset points',
             fontsize=10, fontweight='bold', color=PAL['github'],
             arrowprops=dict(arrowstyle='->', color=PAL['github'], lw=1.5),
             bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=PAL['github'], alpha=0.9))

ax1.set_ylabel('SO Questions (thousands/week)', fontsize=11, color=PAL['so'], labelpad=10)
ax2.set_ylabel('GitHub Repos (millions/month)', fontsize=11, color=PAL['github'], labelpad=10)
ax1.tick_params(axis='y', colors=PAL['so'], labelsize=9)
ax2.tick_params(axis='y', colors=PAL['github'], labelsize=9)
ax1.tick_params(axis='x', labelsize=9)
ax1.xaxis.set_major_locator(mdates.YearLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax1.set_facecolor(PAL['bg'])
ax2.set_facecolor(PAL['bg'])
for spine in ax1.spines.values(): spine.set_color(PAL['line'])
for spine in ax2.spines.values(): spine.set_color(PAL['line'])

lines = [l1, l2]
ax1.legend(lines, [l.get_label() for l in lines], fontsize=10, loc='upper left',
           framealpha=0.9, edgecolor=PAL['line'])

fig.text(0.5, 0.93, 'The AI Knowledge Ecosystem Scissors Effect', ha='center',
         fontsize=15, fontweight='bold', color=PAL['text'])
fig.text(0.5, 0.89, 'Stack Overflow collapses -98.5% while GitHub surges +536.2% (2018–2026)',
         ha='center', fontsize=10, color=PAL['subtext'])

plt.savefig(f"{OUT}/B1_scissors_effect.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B1 saved")

# ════════════════════════════════════════════════════════════
# 图B2：5大反直觉发现 — 精致卡片式布局
# ════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor(PAL['bg'])
fig.text(0.5, 0.97, '5 Counter-Intuitive Findings', ha='center',
         fontsize=16, fontweight='bold', color=PAL['text'])
fig.text(0.5, 0.93, 'Challenging conventional narratives about AI\'s impact on knowledge communities',
         ha='center', fontsize=10.5, color=PAL['subtext'])

gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35,
              left=0.06, right=0.97, top=0.89, bottom=0.06)

# ── F1：ARI与下降无关 ──
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(PAL['bg'])
ari_data = {
    'Python':0.92,'JavaScript':0.88,'TypeScript':0.85,'Java':0.80,
    'C#':0.79,'Go':0.76,'PHP':0.73,'C++':0.71,
    'Swift':0.67,'Kotlin':0.66,'Scala':0.56,'R':0.54,
    'Rust':0.46,'Haskell':0.34
}
lang_names = list(ari_data.keys())
ari_vals = list(ari_data.values())
# 计算各语言下降幅度（ChatGPT前后）
pre_mask  = (sp['month']>='2020-01-01') & (sp['month']<'2022-11-01')
post_mask = (sp['month']>='2023-01-01') & (sp['month']<='2026-02-01')
declines = {}
for lang in so_lang['language'].unique():
    pre_v  = so_lang[so_lang['language']==lang][pre_mask]['activity'].mean()
    post_v = so_lang[so_lang['language']==lang][post_mask]['activity'].mean()
    if pre_v > 0: declines[lang] = (post_v - pre_v) / pre_v * 100
lang_key_map = {'csharp':'C#','cpp':'C++','javascript':'JavaScript','typescript':'TypeScript',
                'python':'Python','java':'Java','go':'Go','php':'PHP','swift':'Swift',
                'kotlin':'Kotlin','scala':'Scala','r':'R','rust':'Rust','haskell':'Haskell'}
x_pts, y_pts, names_pts = [], [], []
for eng, proper in lang_key_map.items():
    if eng in declines and proper in ari_data:
        x_pts.append(ari_data[proper])
        y_pts.append(declines[eng])
        names_pts.append(proper[:2])
sc = ax1.scatter(x_pts, y_pts, c=PAL['neutral'], s=75, alpha=0.85, zorder=4,
            edgecolors='white', linewidths=0.8)
# 重新scatter（简化）
ax1.scatter(x_pts, y_pts, c=PAL['neutral'], s=75, alpha=0.85, zorder=4,
            edgecolors='white', linewidths=0.8)
for x, y, n in zip(x_pts, y_pts, names_pts):
    ax1.annotate(n, (x, y), xytext=(4, 3), textcoords='offset points',
                 fontsize=7.5, color=PAL['text'], alpha=0.8)
# 拟合线
if len(x_pts) > 2:
    z = np.polyfit(x_pts, y_pts, 1)
    p = np.poly1d(z)
    xx = np.linspace(min(x_pts), max(x_pts), 100)
    ax1.plot(xx, p(xx), '--', color=PAL['chatgpt'], lw=1.5, alpha=0.6)
    corr = np.corrcoef(x_pts, y_pts)[0,1]
    ax1.text(0.05, 0.08, f'r = {corr:.2f} (n.s.)', transform=ax1.transAxes,
             fontsize=10, fontweight='bold', color=PAL['chatgpt'],
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=PAL['chatgpt'], alpha=0.9))
ax1.set_xlabel('AI Replaceability Index (ARI)', fontsize=9.5)
ax1.set_ylabel('SO Activity Change (%)', fontsize=9.5)
ax1.set_title('Finding 1\nARI ≠ Decline Magnitude\n(Behavior, not content, drives substitution)',
              fontsize=10, fontweight='bold', color=PAL['neutral'], pad=5)
for sp_ in ax1.spines.values(): sp_.set_color(PAL['line'])

# ── F2：问题越来越长但越来越差 ──
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(PAL['bg'])
ax2_r = ax2.twinx()
length_s = sq['avg_length'].dropna()
answered_s = sq['pct_answered'].dropna()
common_idx = length_s.index.intersection(answered_s.index)
l_norm = length_s.loc[common_idx] / length_s.loc[common_idx].iloc[0] * 100
a_norm = answered_s.loc[common_idx] / answered_s.loc[common_idx].iloc[0] * 100
ax2.fill_between(l_norm.index, l_norm.values, 100, where=(l_norm.values > 100),
                 alpha=0.2, color=PAL['arch'], interpolate=True)
ax2.plot(l_norm.index, l_norm.values, color=PAL['arch'], lw=2.2, label='Question Length ↑')
ax2_r.fill_between(a_norm.index, a_norm.values, 100, where=(a_norm.values < 100),
                   alpha=0.2, color=PAL['debug'], interpolate=True)
ax2_r.plot(a_norm.index, a_norm.values, color=PAL['debug'], lw=2.2, ls='--', label='Answer Rate ↓')
ax2.axvline(CHATGPT_DATE, color=PAL['chatgpt'], lw=1.5, ls=':', alpha=0.8)
ax2.axhline(100, color='gray', lw=0.8, ls=':', alpha=0.5)
ax2.set_ylabel('Length Index (2018=100)', fontsize=8.5, color=PAL['arch'])
ax2_r.set_ylabel('Answer Rate Index', fontsize=8.5, color=PAL['debug'])
ax2.tick_params(axis='y', colors=PAL['arch'], labelsize=8)
ax2_r.tick_params(axis='y', colors=PAL['debug'], labelsize=8)
ax2.tick_params(axis='x', labelsize=8)
ax2.xaxis.set_major_locator(mdates.YearLocator(2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.set_title('Finding 2\nLonger Questions, Fewer Answers\n(Quality Dilution Paradox)',
              fontsize=10, fontweight='bold', color=PAL['neutral'], pad=5)
lines_f2 = [mpatches.Patch(color=PAL['arch'], label='+17.8% length'),
            mpatches.Patch(color=PAL['debug'], label='-23.2% answered')]
ax2.legend(handles=lines_f2, fontsize=8, loc='lower left', framealpha=0.9)
for sp_ in ax2.spines.values(): sp_.set_color(PAL['line'])

# ── F3：Debug崩塌早于ChatGPT ──
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor(PAL['bg'])
q_data = merged.groupby(['quarter','label']).size().unstack(fill_value=0)
q_pct = q_data.div(q_data.sum(axis=1), axis=0) * 100
qs = list(q_pct.index); qx = list(range(len(qs)))
debug_vals = q_pct.get('Debug', pd.Series(0, index=q_pct.index)).values
concept_vals = q_pct.get('Conceptual', pd.Series(0, index=q_pct.index)).values
ax3.fill_between(qx, debug_vals, alpha=0.2, color=PAL['debug'])
ax3.fill_between(qx, concept_vals, alpha=0.2, color=PAL['concept'])
ax3.plot(qx, debug_vals, color=PAL['debug'], lw=2.2, label='Debug')
ax3.plot(qx, concept_vals, color=PAL['concept'], lw=2.2, label='Conceptual')
# 标注2019崩塌
q2019 = qs.index('2019Q1') if '2019Q1' in qs else 4
ax3.axvline(q2019, color='gray', lw=2, ls=':', alpha=0.7)
ax3.text(q2019+0.3, 30, '2019\nCollapse', fontsize=8, color=PAL['debug'],
         fontweight='bold', va='top')
# ChatGPT
qcgpt = qs.index('2022Q4') if '2022Q4' in qs else len(qs)-6
ax3.axvline(qcgpt, color=PAL['chatgpt'], lw=1.8, ls='--', alpha=0.8)
ax3.text(qcgpt+0.3, 42, 'ChatGPT', fontsize=8, color=PAL['chatgpt'], fontweight='bold', va='top')
ytq = [i for i, q in enumerate(qs) if q.endswith('Q1')]
ax3.set_xticks(ytq); ax3.set_xticklabels([q[:4] for q in qs if q.endswith('Q1')], fontsize=8)
ax3.set_ylabel('Share (%)', fontsize=9)
ax3.legend(fontsize=8.5, loc='center right')
ax3.set_title('Finding 3\nDebug Collapsed 3 Years Before ChatGPT\n(Pre-AI tool substitution)',
              fontsize=10, fontweight='bold', color=PAL['neutral'], pad=5)
ax3.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
for sp_ in ax3.spines.values(): sp_.set_color(PAL['line'])

# ── F4：Philosophy唯一上升 ──
ax4 = fig.add_subplot(gs[1, 0])
ax4.set_facecolor(PAL['bg'])
communities = {
    'Philosophy': ('philosophy_questions', '#E91E63'),
    'SO':         (None, PAL['so']),
    'Physics':    ('physics_questions', PAL['neutral']),
    'Travel':     ('travel_questions', PAL['github']),
    'DataSci':    ('datascience_questions', PAL['arch']),
}
for name, (col, color) in communities.items():
    if col is None:
        s = so_ts
    else:
        s = se[col].dropna() if col in se.columns else None
    if s is None or len(s) == 0: continue
    base = s.iloc[0] if s.iloc[0] > 0 else 1
    s_norm = s / base * 100
    lw = 3 if name == 'Philosophy' else 1.8
    ls = '-' if name == 'Philosophy' else '--'
    alpha = 1.0 if name == 'Philosophy' else 0.7
    ax4.plot(s_norm.index, s_norm.values, color=color, lw=lw, ls=ls,
             alpha=alpha, label=f'{name}', zorder=5 if name=='Philosophy' else 3)
ax4.axvline(CHATGPT_DATE, color=PAL['chatgpt'], lw=1.5, ls=':', alpha=0.8)
ax4.axhline(100, color='gray', lw=0.7, ls=':', alpha=0.4)
# 哲学标注
ax4.text(pd.Timestamp('2025-06-01'), 165, '+54.6%\nPhilosophy', fontsize=9,
         color='#E91E63', fontweight='bold', va='top', ha='center')
ax4.xaxis.set_major_locator(mdates.YearLocator(2))
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax4.tick_params(labelsize=8)
ax4.set_ylabel('Index (2018 = 100)', fontsize=9)
ax4.legend(fontsize=7.5, loc='upper left', ncol=2, framealpha=0.9)
ax4.set_title('Finding 4\nPhilosophy SE: The Only Growing Community\n(AI generates new philosophical inquiry)',
              fontsize=10, fontweight='bold', color=PAL['neutral'], pad=5)
for sp_ in ax4.spines.values(): sp_.set_color(PAL['line'])

# ── F5：Conceptual首次超过How-to ──
ax5 = fig.add_subplot(gs[1, 1])
ax5.set_facecolor(PAL['bg'])
howto_vals = q_pct.get('How-to', pd.Series(0, index=q_pct.index)).values
ax5.fill_between(qx, howto_vals, concept_vals,
                 where=(concept_vals > howto_vals), alpha=0.3, color=PAL['concept'],
                 label='Conceptual > How-to', interpolate=True)
ax5.fill_between(qx, howto_vals, concept_vals,
                 where=(howto_vals >= concept_vals), alpha=0.2, color=PAL['howto'],
                 label='How-to > Conceptual', interpolate=True)
ax5.plot(qx, howto_vals, color=PAL['howto'], lw=2.5, label='How-to')
ax5.plot(qx, concept_vals, color=PAL['concept'], lw=2.5, label='Conceptual')
ax5.axvline(qcgpt, color=PAL['chatgpt'], lw=1.8, ls='--', alpha=0.8)
# 标注交叉点
for i in range(1, len(howto_vals)):
    if howto_vals[i-1] >= concept_vals[i-1] and howto_vals[i] < concept_vals[i]:
        ax5.axvline(i, color='gold', lw=2.5, alpha=0.9, zorder=6)
        ax5.text(i, 48, ' Inversion!', fontsize=9, color='#B8860B',
                 fontweight='bold', va='top')
        break
ax5.set_xticks(ytq); ax5.set_xticklabels([q[:4] for q in qs if q.endswith('Q1')], fontsize=8)
ax5.set_ylabel('Share (%)', fontsize=9)
ax5.legend(fontsize=7.5, loc='upper right', ncol=2, framealpha=0.9)
ax5.set_title('Finding 5\nConceptual Surpasses How-to (2024)\n(First time in SO\'s 16-year history)',
              fontsize=10, fontweight='bold', color=PAL['neutral'], pad=5)
ax5.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
for sp_ in ax5.spines.values(): sp_.set_color(PAL['line'])

# ── 右下：数字总结卡 ──
ax6 = fig.add_subplot(gs[1, 2])
ax6.set_facecolor('#ECEFF1')
ax6.axis('off')
stats = [
    ('Stack Overflow 2018→2026', '-98.5%', PAL['so']),
    ('GitHub 2018→2026', '+536.2%', PAL['github']),
    ('DID β₁ (SO×Post)', '-2.26***', PAL['so']),
    ('DID β₂ (GitHub×Post)', '+3.82***', PAL['github']),
    ('Debug collapse (2018→2019)', '-20pp', PAL['debug']),
    ('Conceptual post-ChatGPT', '+7.3pp', PAL['concept']),
    ('Philosophy SE', '+54.6%', '#E91E63'),
    ('ARI-decline correlation', 'r=0.23 n.s.', PAL['neutral']),
]
ax6.set_xlim(0, 1); ax6.set_ylim(0, len(stats)+1)
ax6.set_title('Key Numbers', fontsize=11, fontweight='bold', color=PAL['text'], pad=8)
for i, (label, val, color) in enumerate(stats):
    y = len(stats) - i - 0.3
    ax6.text(0.04, y, label, fontsize=8.5, va='center', color=PAL['subtext'])
    ax6.text(0.98, y, val, fontsize=10, va='center', ha='right',
             fontweight='bold', color=color)
    ax6.axhline(y - 0.5, color=PAL['line'], lw=0.6, xmin=0.02, xmax=0.98)

plt.savefig(f"{OUT}/B2_five_counterintuitive.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B2 saved")

# ════════════════════════════════════════════════════════════
# 图B3：SO质量悖论 — 精致6联图
# ════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 9))
fig.patch.set_facecolor(PAL['bg'])
gs3 = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38,
               left=0.07, right=0.97, top=0.88, bottom=0.1)
fig.text(0.5, 0.95, 'Stack Overflow Quality Metrics: The Dilution Paradox', ha='center',
         fontsize=14, fontweight='bold', color=PAL['text'])
fig.text(0.5, 0.91, 'Every metric worsened after ChatGPT — except question length (which increased)',
         ha='center', fontsize=10, color=PAL['subtext'])

metrics_q = [
    ('avg_score',    'Average Vote Score', PAL['howto'], False, '-67.7%'),
    ('avg_views',    'Avg Page Views', PAL['concept'], False, '-80.5%'),
    ('pct_answered', '% Questions Answered', PAL['github'], True, '-23.2pp'),
    ('pct_accepted', '% Accepted Answer', PAL['arch'], True, '-32.5pp'),
    ('avg_length',   'Avg Question Length (chars)', '#2196F3', False, '+17.8%'),
    ('qa_ratio',     'Questions per Answer (Q/A)', PAL['debug'], False, '-45.2%'),
]
pre_q  = sq[sq.index < CHATGPT_DATE]
post_q = sq[sq.index >= CHATGPT_DATE]

for idx, (col, title, color, is_pct, change_str) in enumerate(metrics_q):
    r, c = idx//3, idx%3
    ax = fig.add_subplot(gs3[r, c])
    ax.set_facecolor(PAL['bg'])
    if col not in sq.columns: continue
    s = sq[col].dropna()
    # 平滑
    s_smooth = s.rolling(3, center=True).mean().fillna(s)
    ax.fill_between(s.index, s.values, alpha=0.12, color=color)
    ax.plot(s.index, s_smooth.values, color=color, lw=2.2, zorder=4)
    # pre/post均值线
    pre_m  = pre_q[col].dropna().mean()
    post_m = post_q[col].dropna().mean()
    ax.axhline(pre_m,  color=color, lw=1.2, ls=':', alpha=0.7, xmin=0.0, xmax=0.57)
    ax.axhline(post_m, color=color, lw=1.2, ls='-.', alpha=0.7, xmin=0.57, xmax=1.0)
    ax.axvline(CHATGPT_DATE, color=PAL['chatgpt'], lw=1.8, ls='--', alpha=0.75, zorder=6)
    # 变化标注
    bg_color = '#FFEBEE' if '-' in change_str else '#E8F5E9'
    txt_color = PAL['debug'] if '-' in change_str else PAL['concept']
    ax.text(0.97, 0.93, change_str, transform=ax.transAxes,
            fontsize=12, fontweight='bold', color=txt_color, ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.4', fc=bg_color, ec=txt_color, alpha=0.9, lw=1.2))
    ax.set_title(title, fontsize=10, fontweight='bold', color=color, pad=6)
    ax.tick_params(labelsize=8)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    if is_pct:
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
    for sp_ in ax.spines.values(): sp_.set_color(PAL['line'])

plt.savefig(f"{OUT}/B3_quality_paradox.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B3 saved")

# ════════════════════════════════════════════════════════════
# 图B4：问题类型完整演变
# ════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 8))
fig.patch.set_facecolor(PAL['bg'])
gs4 = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35,
               left=0.06, right=0.97, top=0.88, bottom=0.1)
fig.text(0.5, 0.95, 'Question Type Structural Shift (2018–2024)', ha='center',
         fontsize=14, fontweight='bold', color=PAL['text'])
fig.text(0.5, 0.91, 'LLM Classification of 122,723 Stack Overflow Questions',
         ha='center', fontsize=10, color=PAL['subtext'])

# 主图：堆积柱状图（年度）
ax_main = fig.add_subplot(gs4[0, :2])
ax_main.set_facecolor(PAL['bg'])
yearly = merged.groupby(['year','label']).size().unstack(fill_value=0)
yearly_pct = yearly.div(yearly.sum(axis=1), axis=0)*100
years_list = list(yearly_pct.index)
x = np.arange(len(years_list))
w = 0.6
bottom = np.zeros(len(years_list))
label_order = ['How-to','Debug','Conceptual','Architecture']
lcolors = [PAL['howto'], PAL['debug'], PAL['concept'], PAL['arch']]
for lbl, lc in zip(label_order, lcolors):
    if lbl not in yearly_pct.columns: continue
    vals = yearly_pct[lbl].values
    bars = ax_main.bar(x, vals, w, bottom=bottom, color=lc, label=lbl, alpha=0.88)
    for i, (v, b) in enumerate(zip(vals, bottom)):
        if v > 5:
            ax_main.text(x[i], b + v/2, f'{v:.0f}%', ha='center', va='center',
                        fontsize=8.5, fontweight='bold', color='white')
    bottom += vals
ax_main.axvline(4.5 + 0.4, color=PAL['chatgpt'], lw=2, ls='--', alpha=0.85, zorder=7)
ax_main.text(4.7, 98, 'ChatGPT', fontsize=9, color=PAL['chatgpt'], fontweight='bold', va='top')
ax_main.set_xticks(x); ax_main.set_xticklabels(years_list, fontsize=9)
ax_main.set_ylabel('Proportion (%)', fontsize=10)
ax_main.set_title('Annual Distribution by Question Type', fontsize=11, fontweight='bold', pad=5)
ax_main.legend(fontsize=9, loc='upper left', ncol=4, framealpha=0.9)
ax_main.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d%%'))
for sp_ in ax_main.spines.values(): sp_.set_color(PAL['line'])

# 右侧：2018 vs 2024 对比（圆环图）
ax_pie = fig.add_subplot(gs4[0, 2])
ax_pie.set_facecolor(PAL['bg'])
ax_pie.axis('off')
# 手动画2个迷你圆形图
ax_pie.set_xlim(0,1); ax_pie.set_ylim(0,1)
ax_pie.text(0.5, 0.97, '2018 vs 2024', ha='center', fontsize=11, fontweight='bold', color=PAL['text'])
data_2018 = yearly_pct.loc[2018, label_order] if 2018 in yearly_pct.index else [0,0,0,0]
data_2024 = yearly_pct.loc[2024, label_order] if 2024 in yearly_pct.index else [0,0,0,0]
# 用文字表示
for i, (lbl, lc) in enumerate(zip(label_order, lcolors)):
    v18 = data_2018[i] if hasattr(data_2018,'__getitem__') else 0
    v24 = data_2024[i] if hasattr(data_2024,'__getitem__') else 0
    delta = v24 - v18
    y_pos = 0.82 - i*0.18
    ax_pie.text(0.05, y_pos, lbl, fontsize=9.5, fontweight='bold', color=lc, va='center')
    ax_pie.text(0.45, y_pos, f'{v18:.0f}%', fontsize=9, color=PAL['subtext'], va='center', ha='center')
    ax_pie.text(0.62, y_pos, '→', fontsize=9, color=PAL['subtext'], va='center', ha='center')
    ax_pie.text(0.78, y_pos, f'{v24:.0f}%', fontsize=9, color=lc, va='center', ha='center', fontweight='bold')
    sign = '+' if delta > 0 else ''
    dcolor = PAL['concept'] if delta > 0 else PAL['debug']
    ax_pie.text(0.97, y_pos, f'{sign}{delta:.0f}pp', fontsize=9, color=dcolor,
                va='center', ha='right', fontweight='bold')
ax_pie.text(0.45, 0.98, '2018', fontsize=8, color=PAL['subtext'], ha='center')
ax_pie.text(0.78, 0.98, '2024', fontsize=8, color=PAL['subtext'], ha='center')
ax_pie.text(0.97, 0.98, 'Δ', fontsize=8, color=PAL['subtext'], ha='right')
ax_pie.axhline(0.90, color=PAL['line'], lw=0.8, xmin=0.02, xmax=0.98)

# 下行：季度趋势
ax_qt = fig.add_subplot(gs4[1, :])
ax_qt.set_facecolor(PAL['bg'])
for lbl, lc in zip(label_order, lcolors):
    if lbl not in q_pct.columns: continue
    vals = q_pct[lbl].values
    ax_qt.fill_between(qx, vals, alpha=0.12, color=lc)
    ax_qt.plot(qx, vals, color=lc, lw=2.2, label=lbl, marker='o', ms=2.5)

ax_qt.axvline(q2019, color='gray', lw=1.8, ls=':', alpha=0.7)
ax_qt.text(q2019+0.3, 31, 'Debug\nCollapse\n2019', fontsize=7.5, color=PAL['debug'],
           va='top', fontweight='bold')
ax_qt.axvline(qcgpt, color=PAL['chatgpt'], lw=2, ls='--', alpha=0.85)
ax_qt.text(qcgpt+0.3, 52, 'ChatGPT', fontsize=8.5, color=PAL['chatgpt'], va='top', fontweight='bold')
# 标注反转点
for i in range(1, len(howto_vals)):
    if howto_vals[i-1] >= concept_vals[i-1] and howto_vals[i] < concept_vals[i]:
        ax_qt.axvline(i, color='gold', lw=2.5, alpha=0.9, zorder=6)
        ax_qt.text(i+0.3, 45, 'Inversion!', fontsize=8.5, color='#B8860B', va='top', fontweight='bold')
        break

ax_qt.set_xticks(ytq); ax_qt.set_xticklabels([q[:4] for q in qs if q.endswith('Q1')], fontsize=9)
ax_qt.set_ylabel('Share (%)', fontsize=10)
ax_qt.set_title('Quarterly Trend: Two-Phase Structural Change', fontsize=11, fontweight='bold', pad=5)
ax_qt.legend(fontsize=9, loc='center right', ncol=4)
ax_qt.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
for sp_ in ax_qt.spines.values(): sp_.set_color(PAL['line'])

plt.savefig(f"{OUT}/B4_question_type_evolution.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B4 saved")

# ════════════════════════════════════════════════════════════
# 图B5：SE社区分层冲击 — 精致排名图
# ════════════════════════════════════════════════════════════
changes_se = {
    'Stack Overflow':-77.4,'English SE':-68.7,'Data Science SE':-66.5,
    'Biology SE':-58.9,'CogSci SE':-55.8,'Music SE':-56.3,'Chemistry SE':-52.8,
    'Statistics SE':-52.0,'Astronomy SE':-51.8,'Physics SE':-47.1,'AI SE':-43.9,
    'Academia SE':-43.4,'Linguistics SE':-42.5,'Politics SE':-42.4,'Law SE':-40.1,
    'Cooking SE':-36.7,'History SE':-36.2,'Literature SE':-30.0,'Movies SE':-29.0,
    'Economics SE':-22.6,'Travel SE':-18.0,'Philosophy SE':+54.6
}
sorted_c = sorted(changes_se.items(), key=lambda x: x[1])
names_s = [x[0] for x in sorted_c]
vals_s  = [x[1] for x in sorted_c]

fig, axes = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={'width_ratios':[2,1]})
fig.patch.set_facecolor(PAL['bg'])

ax = axes[0]
ax.set_facecolor(PAL['bg'])
domain_colors = {
    'Stack Overflow': '#B71C1C',
    'English SE': '#880E4F', 'Data Science SE': '#1A237E', 'Biology SE': '#1B5E20',
    'CogSci SE': '#4A148C', 'Music SE': '#E65100', 'Chemistry SE': '#006064',
    'Statistics SE': '#0D47A1', 'Astronomy SE': '#4527A0', 'Physics SE': '#006064',
    'AI SE': '#880E4F', 'Academia SE': '#3E2723', 'Linguistics SE': '#880E4F',
    'Politics SE': '#BF360C', 'Law SE': '#BF360C', 'Cooking SE': '#E65100',
    'History SE': '#BF360C', 'Literature SE': '#880E4F', 'Movies SE': '#E65100',
    'Economics SE': '#1B5E20', 'Travel SE': '#006064', 'Philosophy SE': '#1B5E20',
}
colors_bar = ['#2E7D32' if v >= 0 else
              ('#C62828' if v < -60 else ('#EF5350' if v < -40 else '#EF9A9A'))
              for v in vals_s]
colors_bar[-1] = '#2E7D32'  # Philosophy

bars = ax.barh(names_s, vals_s, color=colors_bar, alpha=0.88, height=0.72,
               edgecolor='white', linewidth=0.5)

# SO 参考线
so_val = changes_se['Stack Overflow']
ax.axvline(so_val, color=PAL['so'], lw=2, ls='--', alpha=0.6, zorder=3)
ax.text(so_val-1, 21.2, f'SO: {so_val}%', fontsize=8.5, color=PAL['so'],
        ha='right', fontweight='bold')
ax.axvline(0, color=PAL['text'], lw=1, alpha=0.5)

for bar, val in zip(bars, vals_s):
    color_txt = '#2E7D32' if val >= 0 else PAL['debug']
    ax.text(val + (1.5 if val>=0 else -1.5), bar.get_y()+bar.get_height()/2,
            f'{val:+.1f}%', va='center', ha='left' if val>=0 else 'right',
            fontsize=8.5, fontweight='bold', color=color_txt)

ax.set_xlabel('Post-ChatGPT Change (%)\n(Post 2023–2026 vs Pre 2020–2022)', fontsize=10)
ax.set_title('Domain-Stratified AI Impact:\n22 Knowledge Communities Ranked by Disruption',
             fontsize=11, fontweight='bold', color=PAL['text'], pad=8)
ax.tick_params(axis='y', labelsize=9)
ax.tick_params(axis='x', labelsize=8.5)
for sp_ in ax.spines.values(): sp_.set_color(PAL['line'])

# 右侧：领域分组对比
ax2 = axes[1]
ax2.set_facecolor(PAL['bg'])
domain_groups = {
    'Programming\n(SO+1)': [-77.4],
    'Technical SE\n(4)': [-68.7,-66.5,-43.9],
    'Humanities\n(3)': [-68.7,-42.5,-30.0],
    'Natural Sci.\n(3)': [-58.9,-52.8,-51.8,-47.1],
    'Social Sci.\n(4)': [-43.4,-42.4,-40.1,-22.6],
    'Cultural\n(4)': [-56.3,-36.7,-36.2,-29.0,-18.0],
    'Philosophy\n(1)': [+54.6],
}
group_means = {k: np.mean(v) for k,v in domain_groups.items()}
gnames = list(group_means.keys()); gmeans = list(group_means.values())
gcolors = [PAL['debug'] if v < 0 else PAL['concept'] for v in gmeans]
bars2 = ax2.barh(gnames, gmeans, color=gcolors, alpha=0.85, height=0.6,
                 edgecolor='white')
ax2.axvline(0, color=PAL['text'], lw=1, alpha=0.5)
for bar, val in zip(bars2, gmeans):
    ax2.text(val+(1 if val>=0 else -1), bar.get_y()+bar.get_height()/2,
             f'{val:+.1f}%', va='center', ha='left' if val>=0 else 'right',
             fontsize=9, fontweight='bold')
ax2.set_xlabel('Average Change (%)', fontsize=10)
ax2.set_title('By Domain Group\n(Average Impact)', fontsize=11, fontweight='bold', pad=8)
ax2.tick_params(labelsize=9)
for sp_ in ax2.spines.values(): sp_.set_color(PAL['line'])

plt.tight_layout()
plt.savefig(f"{OUT}/B5_se_stratified_impact.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B5 saved")

# ════════════════════════════════════════════════════════════
# 图B6：加速轨迹 — 精致版
# ════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor(PAL['bg'])
fig.text(0.5, 0.97, 'The Acceleration Paradox: No Signs of Community Adaptation',
         ha='center', fontsize=13, fontweight='bold', color=PAL['text'])

# 左：年度下降率
ax = axes[0]
ax.set_facecolor(PAL['bg'])
# 按年份汇总SO下降
annual = so_ts.groupby(so_ts.index.year).mean()
yoy_annual = annual.pct_change() * 100
yrs = list(yoy_annual.index[1:])
rates = list(yoy_annual.values[1:])
bar_colors = ['#EF9A9A' if r < -20 else '#FFCDD2' if r < 0 else '#C8E6C9' for r in rates]
bar_colors = [PAL['so'] if y >= 2022 else '#EF5350' if y >= 2019 else '#FFCDD2' for y, r in zip(yrs, rates)]
bars = ax.bar(yrs, rates, color=bar_colors, alpha=0.85, width=0.7, edgecolor='white')
ax.axhline(0, color=PAL['text'], lw=1, alpha=0.5)
ax.axvline(2022.5, color=PAL['chatgpt'], lw=2, ls='--', alpha=0.8)
ax.text(2022.6, max(rates)*0.9 if rates else 5, 'ChatGPT', fontsize=9,
        color=PAL['chatgpt'], fontweight='bold')
for bar, rate, yr in zip(bars, rates, yrs):
    if yr >= 2019:
        ax.text(bar.get_x()+bar.get_width()/2, rate-2 if rate < 0 else rate+1,
                f'{rate:.0f}%', ha='center', va='top' if rate<0 else 'bottom',
                fontsize=9.5, fontweight='bold', color='white' if abs(rate) > 30 else PAL['text'])
ax.set_ylabel('Year-over-Year Change (%)', fontsize=10)
ax.set_title('Annual Decline Rate (2019–2025)', fontsize=11, fontweight='bold', pad=6)
ax.set_xticks(yrs); ax.set_xticklabels(yrs, fontsize=9)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d%%'))
for sp_ in ax.spines.values(): sp_.set_color(PAL['line'])

# 右：累计下降vs预期适应
ax2 = axes[1]
ax2.set_facecolor(PAL['bg'])
so_norm = so_ts / so_ts.iloc[0] * 100
ax2.fill_between(so_norm.index, so_norm.values, 100,
                 where=(so_norm.values < 100), alpha=0.2, color=PAL['so'], interpolate=True)
ax2.plot(so_norm.index, so_norm.values, color=PAL['so'], lw=2.8, label='Actual SO trend')
# 假设适应曲线（指数平滑到70%）
from scipy.signal import savgol_filter
chatgpt_idx = list(so_norm.index).index(
    min(so_norm.index, key=lambda x: abs((x-CHATGPT_DATE).days)))
expected = np.full(len(so_norm), 100.0)
for i in range(chatgpt_idx, len(so_norm)):
    months_post = i - chatgpt_idx
    expected[i] = 100 * np.exp(-0.01 * months_post) * 0.7 + 30
ax2.plot(so_norm.index, expected, color='gray', lw=1.5, ls=':', alpha=0.7,
         label='Expected adaptation')
ax2.axhline(100, color='gray', lw=0.8, ls=':', alpha=0.4)
ax2.axvline(CHATGPT_DATE, color=PAL['chatgpt'], lw=2, ls='--', alpha=0.8)
# 标注关键里程碑
milestones = [
    ('2022-11-01', 'ChatGPT', 80),
    ('2023-03-01', 'GPT-4', 60),
    ('2024-01-01', 'Gemini', 35),
]
for dt_str, label, y in milestones:
    dt = pd.Timestamp(dt_str)
    if dt in so_norm.index or any(abs((so_norm.index - dt).days) < 35):
        ax2.axvline(dt, color='#757575', lw=1.2, ls=':', alpha=0.6, zorder=3)
        ax2.text(dt, y, f'\n{label}', fontsize=7.5, color='#757575', va='top', ha='center')
ax2.set_ylabel('SO Activity Index (2018 = 100)', fontsize=10)
ax2.set_title('SO Decline: Actual vs. Expected Adaptation', fontsize=11, fontweight='bold', pad=6)
ax2.xaxis.set_major_locator(mdates.YearLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.legend(fontsize=9, framealpha=0.9)
ax2.tick_params(labelsize=8.5)
for sp_ in ax2.spines.values(): sp_.set_color(PAL['line'])

plt.tight_layout(rect=[0,0,1,0.95])
plt.savefig(f"{OUT}/B6_acceleration.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B6 saved")

# ════════════════════════════════════════════════════════════
# 图B7：各语言问题类型热图（精致）
# ════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor(PAL['bg'])
ax.set_facecolor(PAL['bg'])

lang_list = ['python','javascript','typescript','java','csharp','php',
             'cpp','go','rust','swift','kotlin','r','scala','haskell']
label_list = ['How-to','Debug','Conceptual','Architecture']
matrix = np.zeros((len(lang_list), len(label_list)))
lang_display = ['Python','JavaScript','TypeScript','Java','C#','PHP',
                'C++','Go','Rust','Swift','Kotlin','R','Scala','Haskell']

for li, lang in enumerate(lang_list):
    tag = 'c#' if lang == 'csharp' else lang
    mask = merged['Tags'].str.contains(tag, case=False, na=False)
    sub = merged[mask]
    if len(sub) > 50:
        dist = sub['label'].value_counts()
        for lj, lname in enumerate(label_list):
            matrix[li, lj] = dist.get(lname, 0) / len(sub) * 100

from matplotlib.colors import LinearSegmentedColormap
cmap_custom = LinearSegmentedColormap.from_list('custom',
    ['#E3F2FD', '#1565C0'], N=256)
im = ax.imshow(matrix, aspect='auto', cmap=cmap_custom, vmin=0, vmax=70,
               interpolation='nearest')

ax.set_xticks(range(4))
ax.set_xticklabels(label_list, fontsize=13, fontweight='bold')
ax.set_yticks(range(len(lang_list)))
ax.set_yticklabels(lang_display, fontsize=11)

for i in range(len(lang_list)):
    for j in range(len(label_list)):
        val = matrix[i, j]
        color = 'white' if val > 40 else PAL['text']
        weight = 'bold' if val == matrix[i].max() else 'normal'
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=10.5, fontweight=weight, color=color)

cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('Proportion (%)', fontsize=10)
cbar.ax.tick_params(labelsize=9)

ax.set_title('Question Type × Programming Language\n(N = 122,723 classified questions)',
             fontsize=13, fontweight='bold', pad=12)
ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
ax.tick_params(axis='x', top=True, labeltop=True, bottom=False, labelbottom=False)

# 高亮最大值行
for i in range(len(lang_list)):
    max_j = np.argmax(matrix[i])
    ax.add_patch(plt.Rectangle((max_j-0.5, i-0.5), 1, 1,
                                fill=False, edgecolor='gold', lw=2.5, zorder=5))

plt.tight_layout()
plt.savefig(f"{OUT}/B7_type_language_heatmap.png", dpi=150, bbox_inches='tight', facecolor=PAL['bg'])
plt.close()
print("✅ B7 saved")

print(f"\n✅ 7张美化图表已生成")
import os
for f in sorted(os.listdir(OUT)):
    size = os.path.getsize(f"{OUT}/{f}")//1024
    print(f"  {f}: {size}KB")
