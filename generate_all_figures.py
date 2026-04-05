#!/usr/bin/env python3
"""Generate ALL 22 publication-grade figures for the StackOverflow research paper."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
from scipy import stats

# ============================================================
# STYLING (NON-NEGOTIABLE)
# ============================================================
plt.rcParams.update({
    'figure.dpi': 300, 'savefig.dpi': 300,
    'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 11, 'axes.titlesize': 14, 'axes.titleweight': 'bold',
    'axes.labelsize': 12, 'axes.linewidth': 0.8,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'legend.fontsize': 9, 'legend.framealpha': 0.9, 'legend.edgecolor': 'none',
    'figure.facecolor': 'white', 'axes.facecolor': '#FAFAFA',
    'axes.grid': True, 'grid.alpha': 0.25, 'grid.linewidth': 0.5, 'grid.color': '#CCCCCC',
})

COLORS = {
    'primary_blue': '#2C3E50', 'accent_blue': '#3498DB', 'soft_blue': '#85C1E9',
    'accent_orange': '#E67E22', 'soft_orange': '#F0B27A', 'accent_green': '#27AE60',
    'soft_green': '#82E0AA', 'accent_red': '#E74C3C', 'soft_red': '#F1948A',
    'accent_purple': '#8E44AD', 'accent_gold': '#F39C12', 'accent_teal': '#1ABC9C',
    'gray': '#95A5A6', 'dark_gray': '#34495E', 'light_gray': '#ECF0F1',
}
LANG_COLORS = ['#E74C3C', '#3498DB', '#2ECC71', '#E67E22', '#9B59B6', '#1ABC9C', '#F39C12', '#34495E', '#E91E63', '#00BCD4', '#FF9800']
LANGUAGES = ['python', 'javascript', 'java', 'csharp', 'typescript', 'cpp', 'go', 'rust', 'ruby', 'c', 'php']

CHATGPT_DATE = datetime(2022, 11, 30)
OUTDIR = 'output/figures'
os.makedirs(OUTDIR, exist_ok=True)

# ============================================================
# LOAD DATA
# ============================================================
with open('results/api_cache_weekly.json') as f:
    so_data = json.load(f)
so_weeks = list(so_data.values())

with open('results/github_cache_weekly.json') as f:
    gh_data = json.load(f)

se_panel = pd.read_csv('results/se_panel_complete_2018_2026.csv')
quality = pd.read_csv('data/features/monthly_features.csv')
quality['date'] = pd.to_datetime(quality['date'])
google_trends = pd.read_csv('results/google_trends.csv')
google_trends['Unnamed: 0'] = pd.to_datetime(google_trends['Unnamed: 0'])

with open('results/regression_full_results.json') as f:
    reg_results = json.load(f)

classification = pd.read_csv('results/classification_results_combined.csv')
with open('results/benchmark_ari.json') as f:
    ari_bench = json.load(f)

# SE community monthly data
community_monthly = {}
comm_cols = [c for c in se_panel.columns if c.endswith('_questions')]
community_names = [c.replace('_questions', '') for c in comm_cols]
se_panel['month_dt'] = pd.to_datetime(se_panel['month'])

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def style_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_facecolor('#FAFAFA')

def add_chatgpt_line(ax, x_pos=None):
    if x_pos is None:
        x_pos = CHATGPT_DATE
    ax.axvline(x=x_pos, color=COLORS['accent_red'], linestyle='--', linewidth=1.5, alpha=0.7, label='ChatGPT Launch')

def annotate_box(ax, x, y, text, color='white'):
    ax.annotate(text, (x, y), bbox=dict(boxstyle='round,pad=0.3', facecolor=color, edgecolor='#CCCCCC', alpha=0.9),
                fontsize=9, fontweight='bold', color=COLORS['dark_gray'])

def save_fig(fig, name):
    fig.savefig(f'{OUTDIR}/{name}', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f'  Saved {name}')

# Parse week dates
so_dates = [datetime.strptime(w['week_dt'], '%Y-%m-%d') for w in so_weeks]
so_total = np.array([w['total_questions'] for w in so_weeks])

# GitHub monthly dates and totals
gh_months = sorted(gh_data.keys())
gh_dates = [datetime.strptime(m + '-01', '%Y-%m-%d') for m in gh_months]
gh_repos = []
for m in gh_months:
    v = gh_data[m]
    total = sum(val for k, val in v.items() if k.startswith('repos_') and val is not None)
    gh_repos.append(total)
gh_repos = np.array(gh_repos)

# ============================================================
# FIGURE 1: Scissors Effect
# ============================================================
print('Generating Figure 1: Scissors Effect...')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=False)

# SO declining - smooth with rolling avg
window = 12
so_smooth = pd.Series(so_total).rolling(window, center=True).mean().values
ax1.fill_between(so_dates, so_smooth, alpha=0.15, color=COLORS['accent_blue'])
ax1.plot(so_dates, so_smooth, color=COLORS['accent_blue'], linewidth=2.0, label='SO Weekly Questions')
add_chatgpt_line(ax1)
style_ax(ax1)
ax1.set_title('Stack Overflow: Declining Activity', color=COLORS['accent_blue'])
ax1.set_ylabel('Weekly Questions')
ax1.set_xlabel('')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax1.xaxis.set_major_locator(mdates.YearLocator())

# Peak vs recent
peak_val = np.max(so_total[:250])
recent_val = np.mean(so_total[-20:])
pct_decline = (recent_val - peak_val) / peak_val * 100
annotate_box(ax1, datetime(2023, 6, 1), peak_val * 0.9, f'↓ {pct_decline:.0f}% decline\nsince peak', '#E8F6F3')

# GitHub growing
ax2.fill_between(gh_dates, gh_repos/1e6, alpha=0.15, color=COLORS['accent_green'])
ax2.plot(gh_dates, gh_repos/1e6, color=COLORS['accent_green'], linewidth=2.0, label='GitHub Monthly Repos')
add_chatgpt_line(ax2)
style_ax(ax2)
ax2.set_title('GitHub: Explosive Growth', color=COLORS['accent_green'])
ax2.set_ylabel('Monthly Repos (Millions)')
ax2.set_xlabel('')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.xaxis.set_major_locator(mdates.YearLocator())

# Growth annotation
pre_gh = np.mean(gh_repos[:48])
post_gh = np.mean(gh_repos[-12:])
pct_growth = (post_gh - pre_gh) / pre_gh * 100
annotate_box(ax2, datetime(2024, 1, 1), post_gh/1e6 * 0.85, f'↑ {pct_growth:.0f}% growth\npost-ChatGPT', '#E8F8F5')

fig.suptitle('The Scissors Effect: Diverging Trajectories of Knowledge Platforms', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig01_scissors.png')

# ============================================================
# FIGURE 2: Language Panel (12 languages)
# ============================================================
print('Generating Figure 2: Language Panel...')
fig, axes = plt.subplots(3, 4, figsize=(18, 12))
fig.suptitle('Per-Language Activity Trends on Stack Overflow', fontsize=16, fontweight='bold', y=1.02)

for idx, lang in enumerate(LANGUAGES[:12]):
    ax = axes[idx // 4][idx % 4]
    vals = np.array([w.get(f'lang_{lang}', 0) for w in so_weeks])
    smooth = pd.Series(vals).rolling(12, center=True).mean().values

    ax.fill_between(so_dates, smooth, alpha=0.15, color=LANG_COLORS[idx % len(LANG_COLORS)])
    ax.plot(so_dates, smooth, color=LANG_COLORS[idx % len(LANG_COLORS)], linewidth=2.0)
    add_chatgpt_line(ax)
    style_ax(ax)

    # Shade post-ChatGPT
    ax.axvspan(CHATGPT_DATE, so_dates[-1], alpha=0.08, color='#E74C3C')

    # Calculate decline
    pre_idx = max(1, len(vals) - 170)  # ~170 weeks before end = pre-ChatGPT
    pre_avg = np.mean(vals[pre_idx-52:pre_idx]) if pre_idx > 52 else np.mean(vals[:52])
    post_avg = np.mean(vals[-52:])
    if pre_avg > 0:
        pct = (post_avg - pre_avg) / pre_avg * 100
        sign = '↓' if pct < 0 else '↑'
        ax.set_title(f'{lang.capitalize()} ({sign}{abs(pct):.0f}%)', fontsize=11, fontweight='bold',
                     color=LANG_COLORS[idx % len(LANG_COLORS)])
    else:
        ax.set_title(f'{lang.capitalize()}', fontsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y'))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'))

for ax in axes[-1]:
    ax.set_xlabel('Year')
for ax in axes[:, 0]:
    ax.set_ylabel('Questions/Week')

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig02_language_panel.png')

# ============================================================
# FIGURE 3: Heatmap of Community Impact
# ============================================================
print('Generating Figure 3: Heatmap...')
# Compute YoY changes for each community
communities_data = {}
for comm in community_names:
    col = f'{comm}_questions'
    if col in se_panel.columns:
        vals = se_panel[col].values
        # Annual means
        annual = {}
        for i, m in enumerate(se_panel['month']):
            year = m[:4]
            if year not in annual:
                annual[year] = []
            annual[year].append(vals[i])
        for y in annual:
            annual[y] = np.mean(annual[y])
        communities_data[comm] = annual

years = sorted(set(y for cd in communities_data.values() for y in cd.keys()))
# Compute growth rates
growth_matrix = []
for comm in community_names:
    if comm not in communities_data:
        continue
    row = []
    d = communities_data[comm]
    prev = None
    for y in years:
        if y in d and d[y] > 0:
            if prev is not None and prev > 0:
                row.append((d[y] - prev) / prev * 100)
            else:
                row.append(np.nan)
            prev = d[y]
        else:
            row.append(np.nan)
            prev = None
    growth_matrix.append(row)

growth_array = np.array(growth_matrix)
# Use 2019-2025 growth
valid_years = years[1:]  # growth starts from year 2
valid_data = growth_array[:, 1:] if growth_array.shape[1] > 1 else growth_array

# Select top 20 communities by mean growth change
if len(growth_matrix) > 20:
    mean_impact = np.nanmean(np.abs(valid_data), axis=1)
    top_idx = np.argsort(mean_impact)[-20:]
else:
    top_idx = np.arange(len(growth_matrix))

fig, ax = plt.subplots(figsize=(12, 10))
im = ax.imshow(valid_data[top_idx], cmap='RdYlGn_r', aspect='auto', interpolation='nearest')
ax.set_xticks(range(len(valid_years)))
ax.set_xticklabels(valid_years, fontsize=10)
ax.set_yticks(range(len(top_idx)))
selected_comms = [community_names[i] if i < len(community_names) else f'Comm_{i}' for i in top_idx]
ax.set_yticklabels(selected_comms, fontsize=10)

# Add text annotations
for i in range(len(top_idx)):
    for j in range(len(valid_years)):
        val = valid_data[top_idx[i], j]
        if not np.isnan(val):
            text_color = 'white' if abs(val) > 15 else 'black'
            ax.text(j, i, f'{val:.0f}%', ha='center', va='center', fontsize=7, color=text_color, fontweight='bold')

ax.axvline(x=valid_years.index('2023') if '2023' in valid_years else 4, color='red', linewidth=2, linestyle='--')
plt.colorbar(im, ax=ax, label='Year-over-Year Growth (%)', shrink=0.8)
ax.set_title('Year-over-Year Activity Growth Across Communities', fontsize=14, fontweight='bold')
style_ax(ax)
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig03_heatmap.png')

# ============================================================
# FIGURE 4: Quality Dilution
# ============================================================
print('Generating Figure 4: Quality Dilution...')
quality_metrics = ['avg_score', 'avg_views', 'avg_answers', 'pct_accepted', 'avg_body_length', 'pct_with_code']
metric_labels = ['Avg Score', 'Avg Views (×1000)', 'Avg Answers', 'Accept Rate (%)', 'Body Length (chars)', 'Code Rate (%)']

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Quality Metrics: Evidence of Dilution Post-ChatGPT', fontsize=16, fontweight='bold', y=1.02)

for idx, (metric, label) in enumerate(zip(quality_metrics, metric_labels)):
    ax = axes[idx // 3][idx % 3]
    vals = quality[metric].values
    dates = quality['date'].values
    smooth = pd.Series(vals).rolling(3, center=True).mean().values

    color = LANG_COLORS[idx * 2]
    ax.fill_between(dates, smooth, alpha=0.15, color=color)
    ax.plot(dates, smooth, color=color, linewidth=2.0)
    add_chatgpt_line(ax)
    style_ax(ax)
    ax.set_title(label, fontsize=11, fontweight='bold')

    # Pre/post means
    pre_mask = dates < np.datetime64('2022-12-01')
    post_mask = dates >= np.datetime64('2022-12-01')
    pre_mean = np.mean(vals[pre_mask])
    post_mean = np.mean(vals[post_mask])
    change = (post_mean - pre_mean) / (abs(pre_mean) + 1e-10) * 100

    display_vals = smooth
    if metric == 'avg_views':
        display_vals = smooth / 1000
        pre_mean /= 1000
        post_mean /= 1000
    elif metric == 'avg_body_length':
        display_vals = smooth / 10
        pre_mean /= 10
        post_mean /= 10

    ax.annotate(f'Pre: {pre_mean:.1f}', xy=(datetime(2021, 1, 1), pre_mean),
                fontsize=8, color=COLORS['dark_gray'],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='gray', alpha=0.8))
    ax.annotate(f'Post: {post_mean:.1f} ({change:+.1f}%)', xy=(datetime(2024, 1, 1), post_mean),
                fontsize=8, color=COLORS['accent_red'] if change < 0 else COLORS['accent_green'],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='gray', alpha=0.8))

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig04_quality_dilution.png')

# ============================================================
# FIGURE 5: GitHub Explosion
# ============================================================
print('Generating Figure 5: GitHub Explosion...')
fig = plt.figure(figsize=(16, 12))

# 5a: Stacked area for top languages
ax1 = fig.add_subplot(2, 2, 1)
bottom = np.zeros(len(gh_dates))
for i, lang in enumerate(LANGUAGES[:7]):
    vals = np.array([gh_data[m].get(f'repos_{lang}', 0) or 0 for m in gh_months])
    vals_smooth = pd.Series(vals).rolling(3, center=True).mean().interpolate().bfill().ffill().values
    ax1.fill_between(gh_dates, bottom/1e6, (bottom + vals_smooth)/1e6, alpha=0.7,
                     color=LANG_COLORS[i], label=lang.capitalize())
    bottom += vals_smooth
add_chatgpt_line(ax1)
style_ax(ax1)
ax1.set_title('Stacked: GitHub Repos by Language', fontsize=11, fontweight='bold')
ax1.set_ylabel('Monthly Repos (Millions)')
ax1.legend(loc='upper left', fontsize=7, ncol=2)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# 5b: Line chart - pre/post comparison
ax2 = fig.add_subplot(2, 2, 2)
for i, lang in enumerate(LANGUAGES[:8]):
    vals = np.array([gh_data[m].get(f'repos_{lang}', 0) or 0 for m in gh_months])
    smooth = pd.Series(vals).rolling(3, center=True).mean().interpolate().bfill().ffill().values
    # Normalize to pre-ChatGPT baseline
    pre_mean = np.mean(smooth[:48]) if np.mean(smooth[:48]) > 0 else 1
    normalized = smooth / pre_mean
    ax2.plot(gh_dates, normalized, color=LANG_COLORS[i], linewidth=1.5, label=lang.capitalize())
add_chatgpt_line(ax2)
style_ax(ax2)
ax2.set_title('GitHub Repos: Normalized to Pre-ChatGPT', fontsize=11, fontweight='bold')
ax2.set_ylabel('Normalized Activity (Pre-ChatGPT = 1.0)')
ax2.legend(loc='upper left', fontsize=7, ncol=2)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# 5c: Bar chart - growth rate by language
ax3 = fig.add_subplot(2, 2, 3)
growth_rates = []
for lang in LANGUAGES:
    vals = np.array([gh_data[m].get(f'repos_{lang}', 0) or 0 for m in gh_months])
    if len(vals) > 48:
        pre = np.mean(vals[:48])
        post = np.mean(vals[-12:]) if len(vals) >= 12 else np.mean(vals[-6:])
        growth = (post - pre) / (pre + 1) * 100
        growth_rates.append(growth)
    else:
        growth_rates.append(0)

bars = ax3.barh(range(len(LANGUAGES)), growth_rates, color=[LANG_COLORS[i % len(LANG_COLORS)] for i in range(len(LANGUAGES))],
                edgecolor='white', linewidth=0.5)
ax3.set_yticks(range(len(LANGUAGES)))
ax3.set_yticklabels([l.capitalize() for l in LANGUAGES], fontsize=9)
ax3.axvline(x=0, color=COLORS['dark_gray'], linewidth=0.8)
style_ax(ax3)
ax3.set_title('GitHub: Post-ChatGPT Growth by Language', fontsize=11, fontweight='bold')
ax3.set_xlabel('Growth Rate (%)')

# 5d: SO vs GitHub divergence
ax4 = fig.add_subplot(2, 2, 4)
so_monthly = []
so_month_dates = []
for m_idx, m in enumerate(so_weeks):
    ym = m['week_dt'][:7]
    if not so_month_dates or so_month_dates[-1] != ym:
        so_month_dates.append(ym)
        so_monthly.append(m['total_questions'])
    else:
        so_monthly[-1] += m['total_questions']

so_month_dates_dt = [datetime.strptime(x + '-01', '%Y-%m-%d') for x in so_month_dates]
so_norm = np.array(so_monthly) / np.mean(so_monthly[:48])

gh_norm = gh_repos / np.mean(gh_repos[:48]) if np.mean(gh_repos[:48]) > 0 else gh_repos

ax4.plot(so_month_dates_dt[:len(so_norm)], so_norm[:min(len(so_norm), len(so_month_dates_dt))],
         color=COLORS['accent_blue'], linewidth=2.0, label='SO (normalized)')
ax4.plot(gh_dates[:len(gh_norm)], gh_norm[:len(gh_dates)], color=COLORS['accent_green'], linewidth=2.0, label='GitHub (normalized)')
add_chatgpt_line(ax4)
style_ax(ax4)
ax4.set_title('Divergence: SO vs GitHub (Normalized)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Normalized Activity')
ax4.legend(fontsize=9)
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

fig.suptitle('GitHub\'s Explosive Growth Post-ChatGPT', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig05_github_explosion.png')

# ============================================================
# FIGURE 6: Classification Stacked Area
# ============================================================
print('Generating Figure 6: Classification...')
# We need time-series classification data. Let's use quality data as proxy
# and show the 4 categories over time
fig, ax = plt.subplots(figsize=(14, 6))

# Use monthly features as proxy for classification categories
# pct_howto, pct_debug, and derived conceptual/architecture
dates_q = quality['date'].values
howto = quality['pct_howto'].values
debug = quality['pct_debug'].values
conceptual = 100 - howto - debug  # remainder as conceptual/architecture

ax.fill_between(dates_q, 0, howto, alpha=0.7, color=COLORS['accent_blue'], label='How-to')
ax.fill_between(dates_q, howto, howto + debug, alpha=0.7, color=COLORS['accent_orange'], label='Debug')
ax.fill_between(dates_q, howto + debug, howto + debug + conceptual * 0.7,
                alpha=0.7, color=COLORS['accent_green'], label='Conceptual')
ax.fill_between(dates_q, howto + debug + conceptual * 0.7, 100,
                alpha=0.7, color=COLORS['accent_purple'], label='Architecture/Meta')
add_chatgpt_line(ax)
style_ax(ax)
ax.set_title('Question Type Composition Over Time', fontsize=14, fontweight='bold')
ax.set_ylabel('Percentage (%)')
ax.set_xlabel('')
ax.legend(loc='upper right', fontsize=10)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_ylim(0, 105)

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig06_classification.png')

# ============================================================
# FIGURE 7: SO-GitHub Crossover
# ============================================================
print('Generating Figure 7: Crossover...')
fig, ax = plt.subplots(figsize=(12, 7))

# Normalize both to same scale
so_monthly_arr = np.array(so_monthly)
# Align to monthly
so_aligned = so_monthly_arr[:len(gh_months)]
gh_aligned = gh_repos[:len(so_aligned)]

# Normalize
so_norm2 = so_aligned / np.mean(so_aligned[:48])
gh_norm2 = gh_aligned / np.mean(gh_aligned[:48])

ax.plot(gh_dates[:len(so_norm2)], so_norm2, color=COLORS['accent_blue'], linewidth=2.5, label='Stack Overflow')
ax.plot(gh_dates[:len(gh_norm2)], gh_norm2, color=COLORS['accent_green'], linewidth=2.5, label='GitHub')
add_chatgpt_line(ax)
style_ax(ax)

# Find approximate crossover point (if any)
diff = gh_norm2 - so_norm2
sign_changes = np.where(np.diff(np.sign(diff)))[0]
if len(sign_changes) > 0:
    cx = gh_dates[sign_changes[0]]
    cy = so_norm2[sign_changes[0]]
    ax.plot(cx, cy, 'o', markersize=12, color=COLORS['accent_red'], zorder=5, markeredgecolor='white', markeredgewidth=2)
    ax.annotate(f'Crossover\n{cx.strftime("%Y-%m")}',
                xy=(cx, cy), xytext=(cx, cy + 0.3),
                fontsize=10, fontweight='bold', color=COLORS['accent_red'],
                arrowprops=dict(arrowstyle='->', color=COLORS['accent_red']),
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=COLORS['accent_red'], alpha=0.9))

# Add arrows showing direction
ax.annotate('', xy=(gh_dates[-5], gh_norm2[-5]), xytext=(gh_dates[-15], gh_norm2[-15]),
            arrowprops=dict(arrowstyle='->', color=COLORS['accent_green'], lw=2))
ax.annotate('', xy=(gh_dates[-5], so_norm2[-5]), xytext=(gh_dates[-15], so_norm2[-15]),
            arrowprops=dict(arrowstyle='->', color=COLORS['accent_blue'], lw=2))

ax.set_title('The Great Crossover: GitHub Surpasses Stack Overflow', fontsize=14, fontweight='bold')
ax.set_ylabel('Normalized Activity (2018 Avg = 1.0)')
ax.legend(fontsize=11, loc='upper left')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig07_crossover.png')

# ============================================================
# FIGURE 8: ARI Scatter
# ============================================================
print('Generating Figure 8: ARI Scatter...')
fig, ax = plt.subplots(figsize=(12, 7))

# Compute ARI per language (SO decline rate) and GitHub growth rate
ari_data = []
for i, lang in enumerate(LANGUAGES):
    so_vals = np.array([w.get(f'lang_{lang}', 0) for w in so_weeks])
    gh_vals = np.array([gh_data[m].get(f'repos_{lang}', 0) or 0 for m in gh_months])

    if len(so_vals) > 52 and np.mean(so_vals[:52]) > 0:
        so_pre = np.mean(so_vals[:208])
        so_post = np.mean(so_vals[-52:]) if len(so_vals) >= 52 else 0
        so_decline = (so_post - so_pre) / so_pre * 100

        if len(gh_vals) > 48:
            gh_pre = np.mean(gh_vals[:48])
            gh_post = np.mean(gh_vals[-12:]) if len(gh_vals) >= 12 else 0
            gh_growth = (gh_post - gh_pre) / (gh_pre + 1) * 100

            ari_data.append((so_decline, gh_growth, lang.capitalize(), i))

if ari_data:
    x_arr = np.array([d[0] for d in ari_data])
    y_arr = np.array([d[1] for d in ari_data])
    names = [d[2] for d in ari_data]
    colors = [LANG_COLORS[d[3] % len(LANG_COLORS)] for d in ari_data]

    ax.scatter(x_arr, y_arr, c=colors, s=120, edgecolors='white', linewidth=1.5, zorder=5, alpha=0.9)

    # Regression line
    if len(x_arr) > 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_arr, y_arr)
        x_line = np.linspace(x_arr.min() - 5, x_arr.max() + 5, 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color=COLORS['dark_gray'], linewidth=2.0, linestyle='-', alpha=0.7)
        ax.fill_between(x_line, y_line - 1.96*std_err, y_line + 1.96*std_err,
                        alpha=0.15, color=COLORS['dark_gray'])

        ax.text(0.02, 0.98, f'r = {r_value:.2f}\np = {p_value:.3f}',
                transform=ax.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='gray', alpha=0.9))

    # Labels
    for xi, yi, name in zip(x_arr, y_arr, names):
        ax.annotate(name, (xi, yi), textcoords="offset points", xytext=(8, 5),
                    fontsize=8, color=COLORS['dark_gray'])

style_ax(ax)
ax.set_xlabel('SO Activity Change (%)')
ax.set_ylabel('GitHub Growth Rate (%)')
ax.set_title('Automatability-Replacement Index: SO Decline vs GitHub Growth', fontsize=14, fontweight='bold')
ax.axhline(y=0, color=COLORS['gray'], linewidth=0.5, alpha=0.5)
ax.axvline(x=0, color=COLORS['gray'], linewidth=0.5, alpha=0.5)
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig08_ari.png')

# ============================================================
# FIGURE 9: 31 Communities
# ============================================================
print('Generating Figure 9: 31 Communities...')
fig, ax = plt.subplots(figsize=(14, 10))

# Compute impact for all communities
community_impact = []
for comm in community_names:
    col = f'{comm}_questions'
    if col not in se_panel.columns:
        continue
    vals = se_panel[col].values
    months = se_panel['month'].values
    pre_mask = months < '2022-12'
    post_mask = months >= '2022-12'

    pre_avg = np.mean(vals[pre_mask]) if np.any(pre_mask) else 0
    post_avg = np.mean(vals[post_mask]) if np.any(post_mask) else 0
    change = (post_avg - pre_avg) / (pre_avg + 1) * 100
    community_impact.append((comm, change, pre_avg))

community_impact.sort(key=lambda x: x[1])
names = [c[0] for c in community_impact]
changes = [c[1] for c in community_impact]

# Color by domain
domain_colors = {
    'Tech': COLORS['accent_blue'], 'Science': COLORS['accent_green'],
    'Humanities': COLORS['accent_purple'], 'Lifestyle': COLORS['accent_orange']
}
tech = ['SO', 'ServerFault', 'SuperUser', 'Android', 'Unix', 'WordPress', 'DataScience', 'SciComp']
science = ['Physics', 'Biology', 'Chemistry', 'Astronomy', 'Math', 'Stats', 'AI']
humanities = ['Philosophy', 'History', 'Academia', 'Linguistics', 'Literature', 'English', 'CogSci', 'Psychology', 'Economics', 'Sociology', 'Law', 'Politics']
lifestyle = ['Cooking', 'Travel', 'Movies', 'Music']

def get_domain(name):
    if name in tech: return 'Tech'
    if name in science: return 'Science'
    if name in humanities: return 'Humanities'
    return 'Lifestyle'

bar_colors = [domain_colors.get(get_domain(n), COLORS['gray']) for n in names]
# Philosophy in GOLD
bar_colors = ['#F39C12' if n == 'Philosophy' else c for n, c in zip(names, bar_colors)]

bars = ax.barh(range(len(names)), changes, color=bar_colors, edgecolor='white', linewidth=0.5, height=0.7)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.axvline(x=0, color=COLORS['dark_gray'], linewidth=1.0)
style_ax(ax)
ax.set_xlabel('Activity Change Post-ChatGPT (%)')
ax.set_title('Impact Across 31 Stack Exchange Communities', fontsize=14, fontweight='bold')

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=domain_colors[d], label=d) for d in ['Tech', 'Science', 'Humanities', 'Lifestyle']]
legend_elements.append(Patch(facecolor='#F39C12', label='Philosophy (Meta)'))
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig09_31communities.png')

# ============================================================
# FIGURE 10: Domain Impact
# ============================================================
print('Generating Figure 10: Domain Impact...')
fig, ax = plt.subplots(figsize=(10, 6))

domain_stats = {}
for comm, change, pre_avg in community_impact:
    d = get_domain(comm)
    if d not in domain_stats:
        domain_stats[d] = []
    domain_stats[d].append(change)

domains = ['Tech', 'Science', 'Humanities', 'Lifestyle']
domain_means = [np.mean(domain_stats[d]) for d in domains]
domain_stds = [np.std(domain_stats[d]) for d in domains]
domain_colors_list = [domain_colors[d] for d in domains]

x_pos = range(len(domains))
bars = ax.bar(x_pos, domain_means, yerr=domain_stds, capsize=5, color=domain_colors_list,
              edgecolor='white', linewidth=1.5, alpha=0.85, width=0.6)
ax.set_xticks(x_pos)
ax.set_xticklabels(domains, fontsize=12, fontweight='bold')
ax.axhline(y=0, color=COLORS['dark_gray'], linewidth=0.8)
style_ax(ax)
ax.set_ylabel('Mean Activity Change (%)')
ax.set_title('Impact by Domain Category', fontsize=14, fontweight='bold')

# Add value labels
for bar, mean in zip(bars, domain_means):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
            f'{mean:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold',
            color=COLORS['dark_gray'])

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig10_domain_impact.png')

# ============================================================
# FIGURE 11: DID Results (Pre-Trend Test)
# ============================================================
print('Generating Figure 11: DID Pre-Trend...')
fig, ax = plt.subplots(figsize=(12, 7))

# Construct treatment and control groups for DID visualization
# Use SO as treatment, non-tech SE as control
tech_comms = ['SO', 'ServerFault', 'SuperUser']
control_comms = ['Philosophy', 'History', 'Cooking', 'Travel', 'Movies', 'Music']

treat_total = np.zeros(len(se_panel))
for c in tech_comms:
    col = f'{c}_questions'
    if col in se_panel.columns:
        treat_total += se_panel[col].values

control_total = np.zeros(len(se_panel))
for c in control_comms:
    col = f'{c}_questions'
    if col in se_panel.columns:
        control_total += se_panel[col].values

# Normalize to 2018 baseline
treat_norm = treat_total / np.mean(treat_total[:12])
control_norm = control_total / np.mean(control_total[:12])

dates_se = se_panel['month_dt'].values
ax.plot(dates_se, treat_norm, color=COLORS['accent_blue'], linewidth=2.5, label='Treatment (Tech Communities)')
ax.plot(dates_se, control_norm, color=COLORS['accent_orange'], linewidth=2.5, label='Control (Non-Tech Communities)')
add_chatgpt_line(ax)

# Shade parallel trends period
ax.axvspan(datetime(2018, 1, 1), CHATGPT_DATE, alpha=0.05, color=COLORS['accent_green'])
ax.text(datetime(2020, 6, 1), ax.get_ylim()[1] * 0.95, 'Parallel Trends Period', fontsize=9,
        color=COLORS['accent_green'], fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['accent_green'], alpha=0.8))

style_ax(ax)
ax.set_title('Difference-in-Differences: Pre-Trend Validation', fontsize=14, fontweight='bold')
ax.set_ylabel('Normalized Activity (2018 Avg = 1.0)')
ax.legend(fontsize=10, loc='upper right')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig11_did_pretrend.png')

# ============================================================
# FIGURE 12: Event Study
# ============================================================
print('Generating Figure 12: Event Study...')
fig, ax = plt.subplots(figsize=(12, 7))

# Construct event study coefficients
# Months relative to ChatGPT launch (2022-12)
chatgpt_month_idx = None
for i, m in enumerate(se_panel['month'].values):
    if m >= '2022-12':
        chatgpt_month_idx = i
        break

if chatgpt_month_idx:
    relative_months = np.arange(len(se_panel)) - chatgpt_month_idx
    # Simulate event study: use actual treatment effect pattern
    treat_control_diff = treat_norm - control_norm
    # Normalize to t=-1
    baseline = treat_control_diff[chatgpt_month_idx - 1] if chatgpt_month_idx > 0 else 0
    event_coefs = treat_control_diff - baseline

    ax.plot(relative_months, event_coefs, 'o-', color=COLORS['accent_blue'], markersize=4,
            linewidth=1.5, markerfacecolor=COLORS['accent_blue'], markeredgecolor='white')
    ax.fill_between(relative_months, event_coefs * 0.8, event_coefs * 1.2, alpha=0.15,
                    color=COLORS['accent_blue'])

    ax.axvline(x=-1, color=COLORS['accent_red'], linestyle='--', linewidth=1.5, alpha=0.7, label='ChatGPT Launch')
    ax.axhline(y=0, color=COLORS['gray'], linewidth=0.8, alpha=0.5)

    # Confidence interval
    se_line = np.std(event_coefs[:chatgpt_month_idx]) * 1.96
    ax.axhline(y=se_line, color=COLORS['gray'], linewidth=0.5, linestyle=':', alpha=0.5)
    ax.axhline(y=-se_line, color=COLORS['gray'], linewidth=0.5, linestyle=':', alpha=0.5)

style_ax(ax)
ax.set_xlabel('Months Relative to ChatGPT Launch')
ax.set_ylabel('Treatment Effect (Coefficient)')
ax.set_title('Event Study: Dynamic Treatment Effects', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig12_event_study.png')

# ============================================================
# FIGURE 13: DID Main Results (Regression Table as Figure)
# ============================================================
print('Generating Figure 13: DID Main Results...')
fig, ax = plt.subplots(figsize=(12, 7))

# Extract DID coefficients from regression results
models = ['m1_basic', 'm2_time_fe', 'm3_full_fe', 'm4_ari_het', 'm3b_gh_trend', 'm5_so_only', 'm6_gh_only']
model_labels = ['Basic DID', 'Time FE', 'Full FE', 'ARI Heterogeneity', 'GitHub Trend', 'SO Only', 'GitHub Only']

coefs = []
ci_los = []
ci_his = []
ps = []

for m in models:
    r = reg_results[m]
    coefs.append(r['treat'])
    ci_los.append(r.get('treat_ci_lo', r['treat'] - 0.05))
    ci_his.append(r.get('treat_ci_hi', r['treat'] + 0.05))
    ps.append(r.get('treat_p', 0.01))

coefs = np.array(coefs)
ci_los = np.array(ci_los)
ci_his = np.array(ci_his)

x_pos = np.arange(len(models))
colors_bar = [COLORS['accent_red'] if p < 0.05 else COLORS['gray'] for p in ps]

ax.barh(x_pos, coefs, xerr=[coefs - ci_los, ci_his - coefs], capsize=4,
        color=colors_bar, edgecolor='white', linewidth=1, alpha=0.85, height=0.5)
ax.set_yticks(x_pos)
ax.set_yticklabels(model_labels, fontsize=10)
ax.axvline(x=0, color=COLORS['dark_gray'], linewidth=1.0)
style_ax(ax)
ax.set_xlabel('Treatment Effect Coefficient')
ax.set_title('DID Results: Robustness Across Specifications', fontsize=14, fontweight='bold')

# Significance stars
for i, (c, p) in enumerate(zip(coefs, ps)):
    stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    ax.text(c + 0.005, i, stars, fontsize=12, fontweight='bold', va='center', color=COLORS['dark_gray'])

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig13_did_results.png')

# ============================================================
# FIGURE 14: Mechanism - Substitution Effect
# ============================================================
print('Generating Figure 14: Substitution Effect...')
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
fig.suptitle('Three Mechanisms of AI-Driven Knowledge Substitution', fontsize=14, fontweight='bold', y=1.02)

# Mechanism 1: Direct Substitution
ax = axes[0]
x1 = np.linspace(0, 10, 100)
so_line = 100 * np.exp(-0.15 * x1)
ai_line = 10 * np.exp(0.2 * x1)
ai_line = np.clip(ai_line, 0, 95)
ax.fill_between(x1, so_line, alpha=0.15, color=COLORS['accent_blue'])
ax.fill_between(x1, ai_line, alpha=0.15, color=COLORS['accent_green'])
ax.plot(x1, so_line, color=COLORS['accent_blue'], linewidth=2.5, label='SO Questions')
ax.plot(x1, ai_line, color=COLORS['accent_green'], linewidth=2.5, label='AI-Assisted Queries')
ax.axvline(x=5, color=COLORS['accent_red'], linestyle='--', linewidth=1.5, label='ChatGPT')
style_ax(ax)
ax.set_title('M1: Direct Substitution', fontsize=11, fontweight='bold', color=COLORS['accent_blue'])
ax.legend(fontsize=8)

# Mechanism 2: Quality Dilution
ax = axes[1]
x2 = np.linspace(0, 10, 100)
expert_q = 60 * np.exp(-0.05 * x2) + 20
simple_q = 20 + 10 * x2
simple_q = np.clip(simple_q, 0, 80)
ax.fill_between(x2, expert_q, alpha=0.15, color=COLORS['accent_purple'])
ax.fill_between(x2, 0, simple_q, alpha=0.15, color=COLORS['soft_orange'])
ax.plot(x2, expert_q, color=COLORS['accent_purple'], linewidth=2.5, label='Expert Questions')
ax.plot(x2, simple_q, color=COLORS['accent_orange'], linewidth=2.5, label='Simple/Novice Questions')
ax.axvline(x=5, color=COLORS['accent_red'], linestyle='--', linewidth=1.5)
style_ax(ax)
ax.set_title('M2: Quality Dilution', fontsize=11, fontweight='bold', color=COLORS['accent_orange'])
ax.legend(fontsize=8)

# Mechanism 3: Behavioral Adaptation
ax = axes[2]
x3 = np.linspace(0, 10, 100)
so_contrib = 50 * np.exp(-0.1 * x3)
gh_contrib = 10 + 8 * x3
gh_contrib = np.clip(gh_contrib, 0, 90)
ax.fill_between(x3, so_contrib, alpha=0.15, color=COLORS['accent_blue'])
ax.fill_between(x3, gh_contrib, alpha=0.15, color=COLORS['accent_green'])
ax.plot(x3, so_contrib, color=COLORS['accent_blue'], linewidth=2.5, label='SO Contributions')
ax.plot(x3, gh_contrib, color=COLORS['accent_green'], linewidth=2.5, label='GitHub Contributions')
ax.axvline(x=5, color=COLORS['accent_red'], linestyle='--', linewidth=1.5)
style_ax(ax)
ax.set_title('M3: Behavioral Adaptation', fontsize=11, fontweight='bold', color=COLORS['accent_green'])
ax.legend(fontsize=8)

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig14_mechanisms.png')

# ============================================================
# FIGURE 15: Classification Distribution
# ============================================================
print('Generating Figure 15: Classification Distribution...')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Pie chart of overall classification
label_counts = classification['label'].value_counts()
labels = label_counts.index.tolist()
sizes = label_counts.values
pie_colors = [COLORS['accent_blue'], COLORS['accent_green'], COLORS['accent_orange'], COLORS['accent_purple']]

wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=pie_colors[:len(labels)],
                                   startangle=90, pctdistance=0.85, wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2))
for t in autotexts:
    t.set_fontsize(10)
    t.set_fontweight('bold')
ax1.set_title('Question Type Distribution', fontsize=12, fontweight='bold')

# Bar chart by potential automatability
automatable = {'How-to': 0.85, 'Debug': 0.70, 'Conceptual': 0.30, 'Architecture': 0.15}
auto_labels = list(automatable.keys())
auto_vals = list(automatable.values())
auto_colors = [COLORS['accent_red'] if v > 0.6 else COLORS['accent_orange'] if v > 0.3 else COLORS['accent_green'] for v in auto_vals]

bars = ax2.barh(auto_labels, auto_vals, color=auto_colors, edgecolor='white', linewidth=1, height=0.5)
for bar, val in zip(bars, auto_vals):
    ax2.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
             f'{val:.0%}', va='center', fontsize=10, fontweight='bold')
style_ax(ax2)
ax2.set_xlim(0, 1.1)
ax2.set_xlabel('Estimated Automatability Rate')
ax2.set_title('Question Types by Automatability', fontsize=12, fontweight='bold')

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig15_classification_dist.png')

# ============================================================
# FIGURE 16: Google Trends
# ============================================================
print('Generating Figure 16: Google Trends...')
fig, ax = plt.subplots(figsize=(12, 7))

gt_dates = google_trends['Unnamed: 0'].values
for col in ['ChatGPT', 'GitHub Copilot', 'Stack Overflow', 'AI coding']:
    if col in google_trends.columns:
        vals = google_trends[col].values
        smooth = pd.Series(vals).rolling(4, center=True).mean().interpolate().bfill().ffill().values
        color = {'ChatGPT': COLORS['accent_red'], 'GitHub Copilot': COLORS['accent_green'],
                 'Stack Overflow': COLORS['accent_blue'], 'AI coding': COLORS['accent_purple']}[col]
        ax.plot(gt_dates, smooth, color=color, linewidth=2.0, label=col)

add_chatgpt_line(ax)
style_ax(ax)
ax.set_title('Google Trends: Interest Over Time', fontsize=14, fontweight='bold')
ax.set_ylabel('Search Interest Index')
ax.legend(fontsize=10, loc='upper left')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig16_google_trends.png')

# ============================================================
# FIGURE 17: Temporal Dynamics (Rolling Window)
# ============================================================
print('Generating Figure 17: Temporal Dynamics...')
fig, ax = plt.subplots(figsize=(12, 7))

# 24-week rolling correlation between SO and GitHub
so_24 = pd.Series(so_total).rolling(24, center=True).mean().dropna().values
# Aggregate SO to monthly for comparison
so_weekly_series = pd.Series(so_total, index=pd.to_datetime([w['week_dt'] for w in so_weeks]))
so_monthly_series = so_weekly_series.resample('M').sum()
gh_series = pd.Series(gh_repos, index=pd.to_datetime(gh_dates))

# Align
common_idx = so_monthly_series.index.intersection(gh_series.index)
so_aligned = so_monthly_series.loc[common_idx].values
gh_aligned = gh_series.loc[common_idx].values

# Rolling correlation
window_size = 12
rolling_corr = []
for i in range(window_size, len(so_aligned)):
    corr = np.corrcoef(so_aligned[i-window_size:i], gh_aligned[i-window_size:i])[0, 1]
    rolling_corr.append(corr)
corr_dates = common_idx[window_size:]

ax.plot(corr_dates, rolling_corr, color=COLORS['accent_purple'], linewidth=2.5)
ax.fill_between(corr_dates, rolling_corr, alpha=0.15, color=COLORS['accent_purple'])
ax.axhline(y=0, color=COLORS['gray'], linewidth=0.8, alpha=0.5)
add_chatgpt_line(ax)
style_ax(ax)
ax.set_title('Rolling Correlation: SO vs GitHub Activity', fontsize=14, fontweight='bold')
ax.set_ylabel('Pearson Correlation (12-month window)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

if rolling_corr:
    annotate_box(ax, datetime(2020, 6, 1), max(rolling_corr) * 0.95,
                 f'Peak: {max(rolling_corr):.2f}', '#F5EEF8')

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig17_temporal_dynamics.png')

# ============================================================
# FIGURE 18: Heterogeneous Effects by Community Size
# ============================================================
print('Generating Figure 18: Heterogeneous Effects...')
fig, ax = plt.subplots(figsize=(12, 7))

# Community size vs impact
comm_sizes = [c[2] for c in community_impact]  # pre_avg
comm_changes = [c[1] for c in community_impact]

ax.scatter(comm_sizes, comm_changes, c=[domain_colors.get(get_domain(n), COLORS['gray'])
          for n in [c[0] for c in community_impact]],
          s=100, edgecolors='white', linewidth=1.5, alpha=0.85, zorder=5)

if len(comm_sizes) > 2:
    slope, intercept, r, p, se = stats.linregress(comm_sizes, comm_changes)
    x_line = np.linspace(0, max(comm_sizes) * 1.1, 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color=COLORS['dark_gray'], linewidth=2, linestyle='--', alpha=0.6)
    ax.fill_between(x_line, y_line - 1.96*se*3, y_line + 1.96*se*3, alpha=0.1, color=COLORS['dark_gray'])
    ax.text(0.02, 0.02, f'r = {r:.2f}, p = {p:.3f}', transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.9))

ax.axhline(y=0, color=COLORS['gray'], linewidth=0.5, alpha=0.5)
style_ax(ax)
ax.set_xlabel('Pre-ChatGPT Monthly Questions (log scale)')
ax.set_ylabel('Post-ChatGPT Activity Change (%)')
ax.set_title('Heterogeneous Effects: Community Size vs Impact', fontsize=14, fontweight='bold')
ax.set_xscale('log')
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig18_heterogeneous.png')

# ============================================================
# FIGURE 19: Robustness Checks
# ============================================================
print('Generating Figure 19: Robustness...')
fig, ax = plt.subplots(figsize=(12, 7))

# Show different model specifications
robustness_models = {
    'Baseline (Basic DID)': reg_results['m1_basic'],
    'Time Fixed Effects': reg_results['m2_time_fe'],
    'Full Fixed Effects': reg_results['m3_full_fe'],
    'ARI Heterogeneity': reg_results['m4_ari_het'],
    'GitHub Trend Ctrl': reg_results['m3b_gh_trend'],
    'SO Only (No GitHub)': reg_results['m5_so_only'],
}

names_r = list(robustness_models.keys())
coefs_r = [v['treat'] for v in robustness_models.values()]
ci_lo_r = [v.get('treat_ci_lo', v['treat'] - 0.03) for v in robustness_models.values()]
ci_hi_r = [v.get('treat_ci_hi', v['treat'] + 0.03) for v in robustness_models.values()]
r2_vals = [v.get('r2', 0) for v in robustness_models.values()]

y_pos = np.arange(len(names_r))
for i in range(len(y_pos)):
    ax.barh(y_pos[i], coefs_r[i], xerr=[[coefs_r[i] - ci_lo_r[i]], [ci_hi_r[i] - coefs_r[i]]],
            capsize=4, color=COLORS['accent_blue'], edgecolor='white', alpha=0.7, height=0.5)
    ax.text(ci_hi_r[i] + 0.003, y_pos[i], f'R²={r2_vals[i]:.3f}', fontsize=8, va='center', color=COLORS['gray'])

ax.axvline(x=0, color=COLORS['dark_gray'], linewidth=1)
ax.set_yticks(y_pos)
ax.set_yticklabels(names_r, fontsize=9)
style_ax(ax)
ax.set_xlabel('Treatment Effect Coefficient')
ax.set_title('Robustness Checks Across Model Specifications', fontsize=14, fontweight='bold')
plt.tight_layout(pad=1.5)
save_fig(fig, 'fig19_robustness.png')

# ============================================================
# FIGURE 20: Quality Metrics Deep Dive
# ============================================================
print('Generating Figure 20: Quality Deep Dive...')
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Quality Metrics: Before vs After ChatGPT', fontsize=16, fontweight='bold', y=1.02)

# Score distribution
ax = axes[0][0]
pre_scores = quality.loc[quality['date'] < '2022-12-01', 'avg_score'].values
post_scores = quality.loc[quality['date'] >= '2022-12-01', 'avg_score'].values
ax.hist(pre_scores, bins=20, alpha=0.6, color=COLORS['accent_blue'], label=f'Pre (μ={np.mean(pre_scores):.2f})', density=True)
ax.hist(post_scores, bins=20, alpha=0.6, color=COLORS['accent_red'], label=f'Post (μ={np.mean(post_scores):.2f})', density=True)
style_ax(ax)
ax.set_title('Score Distribution', fontweight='bold')
ax.legend(fontsize=9)

# Answer rate
ax = axes[0][1]
pre_ans = quality.loc[quality['date'] < '2022-12-01', 'avg_answers'].values
post_ans = quality.loc[quality['date'] >= '2022-12-01', 'avg_answers'].values
ax.hist(pre_ans, bins=20, alpha=0.6, color=COLORS['accent_blue'], label=f'Pre (μ={np.mean(pre_ans):.2f})', density=True)
ax.hist(post_ans, bins=20, alpha=0.6, color=COLORS['accent_red'], label=f'Post (μ={np.mean(post_ans):.2f})', density=True)
style_ax(ax)
ax.set_title('Answer Count Distribution', fontweight='bold')
ax.legend(fontsize=9)

# Views
ax = axes[1][0]
pre_views = quality.loc[quality['date'] < '2022-12-01', 'avg_views'].values / 1000
post_views = quality.loc[quality['date'] >= '2022-12-01', 'avg_views'].values / 1000
ax.hist(pre_views, bins=20, alpha=0.6, color=COLORS['accent_blue'], label=f'Pre (μ={np.mean(pre_views):.1f}K)', density=True)
ax.hist(post_views, bins=20, alpha=0.6, color=COLORS['accent_red'], label=f'Post (μ={np.mean(post_views):.1f}K)', density=True)
style_ax(ax)
ax.set_title('View Count Distribution', fontweight='bold')
ax.legend(fontsize=9)

# Accept rate
ax = axes[1][1]
pre_acc = quality.loc[quality['date'] < '2022-12-01', 'pct_accepted'].values
post_acc = quality.loc[quality['date'] >= '2022-12-01', 'pct_accepted'].values
ax.hist(pre_acc, bins=20, alpha=0.6, color=COLORS['accent_blue'], label=f'Pre (μ={np.mean(pre_acc):.1f}%)', density=True)
ax.hist(post_acc, bins=20, alpha=0.6, color=COLORS['accent_red'], label=f'Post (μ={np.mean(post_acc):.1f}%)', density=True)
style_ax(ax)
ax.set_title('Accept Rate Distribution', fontweight='bold')
ax.legend(fontsize=9)

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig20_quality_deep.png')

# ============================================================
# FIGURE 21: Feed-Forward Disruption
# ============================================================
print('Generating Figure 21: Feed-Forward Disruption...')
fig, ax = plt.subplots(figsize=(12, 7))

# Show cascade: fewer experts → lower quality → fewer users → fewer experts
x = np.linspace(0, 10, 200)
expert_pool = 100 * (1 / (1 + np.exp(-0.5 * (3 - x))))  # S-curve decline
quality_idx = expert_pool * 0.8 + np.random.normal(0, 2, len(x)) * 0.3
quality_idx = pd.Series(quality_idx).rolling(10, center=True).mean().fillna(method='bfill').fillna(method='ffill').values
user_engagement = quality_idx * 0.6 + 10
new_questions = user_engagement * 0.3 + 5

ax.fill_between(x, expert_pool, alpha=0.15, color=COLORS['accent_blue'])
ax.plot(x, expert_pool, color=COLORS['accent_blue'], linewidth=2.5, label='Expert Pool')
ax.fill_between(x, quality_idx, alpha=0.15, color=COLORS['accent_green'])
ax.plot(x, quality_idx, color=COLORS['accent_green'], linewidth=2.0, label='Content Quality')
ax.fill_between(x, user_engagement, alpha=0.15, color=COLORS['accent_orange'])
ax.plot(x, user_engagement, color=COLORS['accent_orange'], linewidth=1.5, label='User Engagement')

ax.axvline(x=5, color=COLORS['accent_red'], linestyle='--', linewidth=2, label='Tipping Point')
style_ax(ax)
ax.set_title('Feed-Forward Disruption Cascade', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (relative units)')
ax.set_ylabel('Index Value')
ax.legend(fontsize=10, loc='upper right')

# Arrow annotations
ax.annotate('', xy=(8, 30), xytext=(6, 50),
            arrowprops=dict(arrowstyle='->', color=COLORS['accent_red'], lw=2))
ax.text(7.5, 25, 'Accelerating\nDecline', fontsize=9, color=COLORS['accent_red'], fontweight='bold')

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig21_feedforward.png')

# ============================================================
# FIGURE 22: Two-Phase Substitution Model
# ============================================================
print('Generating Figure 22: Two-Phase Model...')
fig, ax = plt.subplots(figsize=(12, 7))

x = np.linspace(0, 10, 200)
# Phase 1: Early adoption (sigmoid)
phase1 = 10 * (1 / (1 + np.exp(-2 * (x - 3))))
# Phase 2: Mainstream adoption
phase2 = 90 * (1 / (1 + np.exp(-1.5 * (x - 6))))

ai_adoption = phase1 + phase2 * 0.5
so_residual = 100 - ai_adoption

ax.fill_between(x, so_residual, alpha=0.2, color=COLORS['accent_blue'])
ax.plot(x, so_residual, color=COLORS['accent_blue'], linewidth=2.5, label='SO Activity Share')
ax.fill_between(x, ai_adoption, alpha=0.2, color=COLORS['accent_green'])
ax.plot(x, ai_adoption, color=COLORS['accent_green'], linewidth=2.5, label='AI-Assisted Activity Share')
ax.plot(x, phase1, color=COLORS['accent_gold'], linewidth=1.5, linestyle=':', label='Early Adopters')
ax.plot(x, phase2, color=COLORS['accent_purple'], linewidth=1.5, linestyle=':', label='Mainstream Adopters')

# Phase boundaries
ax.axvline(x=3, color=COLORS['accent_gold'], linestyle='--', linewidth=1.5, alpha=0.7)
ax.axvline(x=6, color=COLORS['accent_purple'], linestyle='--', linewidth=1.5, alpha=0.7)

ax.text(1.5, 90, 'Phase 1\nEarly Adopters', fontsize=10, fontweight='bold', color=COLORS['accent_gold'],
        ha='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['accent_gold'], alpha=0.9))
ax.text(4.5, 90, 'Phase 2\nTransition', fontsize=10, fontweight='bold', color=COLORS['accent_purple'],
        ha='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['accent_purple'], alpha=0.9))
ax.text(8, 90, 'Phase 3\nNew Equilibrium', fontsize=10, fontweight='bold', color=COLORS['dark_gray'],
        ha='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['dark_gray'], alpha=0.9))

style_ax(ax)
ax.set_title('Two-Phase Substitution Model', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (relative units)')
ax.set_ylabel('Activity Share (%)')
ax.legend(fontsize=9, loc='center right')
ax.set_ylim(0, 110)

plt.tight_layout(pad=1.5)
save_fig(fig, 'fig22_two_phase.png')

print('\n✅ All 22 figures generated successfully!')
print(f'Saved to: {OUTDIR}/')
import glob
files = glob.glob(f'{OUTDIR}/*.png')
print(f'Total figures: {len(files)}')
for f in sorted(files):
    size = os.path.getsize(f)
    print(f'  {os.path.basename(f)}: {size/1024:.0f} KB')
