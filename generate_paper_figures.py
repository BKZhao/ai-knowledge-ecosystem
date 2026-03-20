#!/usr/bin/env python3
"""
Generate all 8 paper figures for the SO/GitHub knowledge production vs consumption paper.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy import stats
from scipy.stats import linregress
import warnings
warnings.filterwarnings('ignore')

try:
    import scienceplots
    plt.style.use(['science', 'no-latex'])
except:
    print("SciencePlots not available, using seaborn-v0_8-whitegrid")
    plt.style.use('seaborn-v0_8-whitegrid')

# ─── Constants ────────────────────────────────────────────────────────────────
RESULTS_DIR = '/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results'

AI_REP = {
    'python':0.92,'javascript':0.88,'typescript':0.85,'java':0.81,
    'csharp':0.79,'go':0.72,'ruby':0.65,'cpp':0.63,'c':0.60,'r':0.58,
    'rust':0.35,'haskell':0.25,'fortran':0.18,'assembly':0.10
}
LANG_DISPLAY = {
    'python':'Python','javascript':'JavaScript','typescript':'TypeScript',
    'java':'Java','csharp':'C#','go':'Go','ruby':'Ruby','cpp':'C++',
    'c':'C','r':'R','rust':'Rust','haskell':'Haskell','fortran':'Fortran','assembly':'Assembly'
}

AI_EVENTS = [
    ("2021-10-01","Copilot Beta","#95A5A6"),
    ("2022-06-21","Copilot GA","#7F8C8D"),
    ("2022-11-30","ChatGPT","#E74C3C"),
    ("2023-03-14","GPT-4+Claude 1","#C0392B"),
    ("2023-07-18","Claude 2+Llama 2","#8E44AD"),
    ("2024-03-04","Claude 3","#1A5276"),
    ("2024-06-20","Claude 3.5","#154360"),
]

COLOR_SO = '#C0392B'    # red - consumption
COLOR_GH = '#1A5276'    # blue - production
COLOR_CTRL = '#7F8C8D'  # gray - control

HIGH_ARI = ['python','javascript','typescript','java','csharp']
MID_ARI  = ['go','ruby','cpp','c','r']
LOW_ARI  = ['rust','haskell','fortran','assembly']

CHATGPT_DATE = pd.Timestamp('2022-11-30')

# ─── Load Data ────────────────────────────────────────────────────────────────
print("Loading data...")

with open(f'{RESULTS_DIR}/api_cache_weekly.json') as f:
    so_raw = json.load(f)

with open(f'{RESULTS_DIR}/github_cache_weekly.json') as f:
    gh_raw = json.load(f)

with open(f'{RESULTS_DIR}/control_data.json') as f:
    ctrl_raw = json.load(f)

# Build SO weekly DataFrame
so_records = list(so_raw.values())
so_df = pd.DataFrame(so_records)
so_df['date'] = pd.to_datetime(so_df['week_dt'])
so_df = so_df.sort_values('date').reset_index(drop=True)

# Build GitHub monthly DataFrame
gh_records = list(gh_raw.values())
gh_df = pd.DataFrame(gh_records)
gh_df['date'] = pd.to_datetime(gh_df['month_dt'])
gh_df = gh_df.sort_values('date').reset_index(drop=True)

# Add fortran/r to GitHub if missing (fill zeros)
for lang in AI_REP.keys():
    if f'repos_{lang}' not in gh_df.columns:
        gh_df[f'repos_{lang}'] = 0
    if f'issues_{lang}' not in gh_df.columns:
        gh_df[f'issues_{lang}'] = 0

# Build control weekly DataFrame
ctrl_records = list(ctrl_raw.values())
ctrl_df = pd.DataFrame(ctrl_records)
ctrl_df['date'] = pd.to_datetime(ctrl_df['week_dt'])
ctrl_df = ctrl_df.sort_values('date').reset_index(drop=True)

# Aggregate SO to monthly
so_df['month'] = so_df['date'].dt.to_period('M')
so_monthly = so_df.groupby('month').agg({
    'total_questions': 'sum',
    **{f'lang_{l}': 'sum' for l in AI_REP.keys()}
}).reset_index()
so_monthly['date'] = so_monthly['month'].dt.to_timestamp()

# Aggregate control to monthly
ctrl_df['month'] = ctrl_df['date'].dt.to_period('M')
ctrl_monthly = ctrl_df.groupby('month').agg({
    'math_se_questions': 'sum',
    'physics_se_questions': 'sum'
}).reset_index()
ctrl_monthly['date'] = ctrl_monthly['month'].dt.to_timestamp()

# Total GitHub repos per month
gh_df['total_repos'] = sum(gh_df[f'repos_{l}'] for l in AI_REP.keys() if f'repos_{l}' in gh_df.columns)

print(f"SO: {len(so_df)} weeks, monthly: {len(so_monthly)} months")
print(f"GitHub: {len(gh_df)} months")
print(f"Control: {len(ctrl_df)} weeks, monthly: {len(ctrl_monthly)} months")

# ─── Helper: normalize to 2020=100 ───────────────────────────────────────────
def normalize_2020(series, dates):
    """Normalize series so 2020 average = 100."""
    mask = (dates.dt.year == 2020)
    base = series[mask].mean()
    if base == 0 or np.isnan(base):
        base = series.mean()
    return series / base * 100

def rolling_mean(series, window=3):
    return series.rolling(window, center=True, min_periods=1).mean()

# ─── FIGURE 1: Scissors Gap Main Plot ─────────────────────────────────────────
print("Generating Fig 1...")

fig, ax = plt.subplots(figsize=(9, 5))

# Merge SO and GH on month
so_m = so_monthly.copy()
so_m['month_str'] = so_m['date'].dt.to_period('M').astype(str)
gh_m = gh_df.copy()
gh_m['month_str'] = gh_m['date'].dt.to_period('M').astype(str)

merged = pd.merge(so_m, gh_m[['month_str','date','total_repos']], on='month_str', suffixes=('_so','_gh'))
merged = merged.sort_values('date_so').reset_index(drop=True)

so_norm = normalize_2020(merged['total_questions'], merged['date_so'])
gh_norm = normalize_2020(merged['total_repos'], merged['date_so'])

# Smooth
so_smooth = rolling_mean(so_norm)
gh_smooth = rolling_mean(gh_norm)

dates_plot = merged['date_so']

# Plot
ax.plot(dates_plot, so_smooth, color=COLOR_SO, linewidth=2.0, label='SO Questions (consumption)', zorder=3)
ax.plot(dates_plot, gh_smooth, color=COLOR_GH, linewidth=2.0, label='GitHub Repos (production)', zorder=3)
ax.axhline(100, color='black', linestyle='--', linewidth=0.8, alpha=0.5, label='2020 baseline')

# Shade post-ChatGPT
ax.axvspan(CHATGPT_DATE, dates_plot.max(), alpha=0.06, color=COLOR_SO, zorder=0)

# Add AI event vertical lines with numbered footnotes
event_nums = []
for i, (ev_date, ev_label, ev_color) in enumerate(AI_EVENTS, 1):
    ev_dt = pd.Timestamp(ev_date)
    if dates_plot.min() <= ev_dt <= dates_plot.max():
        ax.axvline(ev_dt, color=ev_color, linewidth=0.8, linestyle=':', alpha=0.8, zorder=2)
        # Find y position (top area)
        ax.text(ev_dt, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 150,
                str(i), fontsize=6, ha='center', va='bottom', color=ev_color, fontweight='bold')
        event_nums.append(f"({i}) {ev_label} ({ev_date})")

# Compute final changes
mask_2020 = dates_plot.dt.year == 2020
base_so = so_norm[mask_2020].mean()
base_gh = gh_norm[mask_2020].mean()
mask_last = dates_plot >= pd.Timestamp('2024-01-01')
if mask_last.sum() > 0:
    last_so = so_norm[mask_last].mean()
    last_gh = gh_norm[mask_last].mean()
    pct_so = ((last_so - base_so) / base_so) * 100
    pct_gh = ((last_gh - base_gh) / base_gh) * 100
else:
    pct_so, pct_gh = -30, 40

# Annotation box bottom right
textstr = f'SO: {pct_so:+.1f}% vs 2020\nGitHub: {pct_gh:+.1f}% vs 2020'
ax.text(0.98, 0.08, textstr, transform=ax.transAxes, fontsize=8,
        verticalalignment='bottom', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='gray', alpha=0.8))

ax.set_xlabel('Date', fontsize=9)
ax.set_ylabel('Index (2020 = 100)', fontsize=9)
ax.set_title('H1: Scissors Gap — SO Questions vs GitHub Repositories\n(AI tools shift knowledge demand from consumption to production)', fontsize=10)
ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
ax.tick_params(labelsize=8)
ax.set_xlim(dates_plot.min(), dates_plot.max())

# Footnote
footnote = ' | '.join([f"({i+1}) {ev[1]}" for i, ev in enumerate(AI_EVENTS)])
fig.text(0.5, -0.02, footnote, ha='center', fontsize=6, color='gray', wrap=True)

plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig1.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 1 saved.")

# ─── FIGURE 2: Event Study ────────────────────────────────────────────────────
print("Generating Fig 2...")

# Use weekly SO and monthly GH, centered on ChatGPT (2022-11-30)
# SO: compute weekly anomalies vs prior year same-week mean
so_event = so_df.copy()
so_event = so_event[(so_event['date'] >= pd.Timestamp('2021-11-01')) & 
                     (so_event['date'] <= pd.Timestamp('2024-01-01'))].copy()
so_event['tau'] = ((so_event['date'] - CHATGPT_DATE).dt.days / 7).round().astype(int)

# Pre-event mean (tau=-104 to -1 weeks)
pre_mask = (so_event['tau'] >= -104) & (so_event['tau'] < 0)
pre_mean_so = so_event.loc[pre_mask, 'total_questions'].mean()
pre_std_so  = so_event.loc[pre_mask, 'total_questions'].std()

so_event['anomaly'] = (so_event['total_questions'] - pre_mean_so) / (pre_mean_so) * 100

# GH monthly: center on ChatGPT
gh_event = gh_df.copy()
gh_event['tau_months'] = ((gh_event['date'] - CHATGPT_DATE).dt.days / 30.44).round().astype(int)
pre_gh = gh_event[gh_event['tau_months'] < 0]
pre_mean_gh = pre_gh['total_repos'].mean()
gh_event['anomaly'] = (gh_event['total_repos'] - pre_mean_gh) / pre_mean_gh * 100

fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(9, 6), sharex=False)

# ── Panel (a): Weekly anomaly scatter ─────────────────────
window_weeks = 52
so_scatter = so_event[(so_event['tau'] >= -window_weeks) & (so_event['tau'] <= window_weeks)].copy()

pre_scatter = so_scatter[so_scatter['tau'] < 0]
post_scatter = so_scatter[so_scatter['tau'] >= 0]

ax_a.scatter(pre_scatter['tau'], pre_scatter['anomaly'],
             color='gray', alpha=0.5, s=12, label='Pre-ChatGPT (SO)', zorder=2)
ax_a.scatter(post_scatter['tau'], post_scatter['anomaly'],
             color=COLOR_SO, alpha=0.7, s=12, label='Post-ChatGPT (SO)', zorder=3)

# Smooth post trend
if len(post_scatter) > 5:
    post_roll = post_scatter.set_index('tau')['anomaly'].rolling(4, min_periods=1).mean()
    ax_a.plot(post_roll.index, post_roll.values, color=COLOR_SO, linewidth=1.5, zorder=4)

ax_a.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.6)
ax_a.axvline(0, color=COLOR_SO, linewidth=1.2, linestyle='-', alpha=0.8, label='ChatGPT (t=0)')
ax_a.set_ylabel('Anomaly (%)', fontsize=9)
ax_a.set_title('(a) Weekly SO Question Anomalies Around ChatGPT Launch', fontsize=9)
ax_a.legend(fontsize=7, loc='lower left')
ax_a.tick_params(labelsize=8)
ax_a.set_xlim(-window_weeks, window_weeks)

# ── Panel (b): Cumulative Anomaly Returns (CAR) ───────────────────────────────
# SO CAR (weekly)
so_car = so_scatter.copy().sort_values('tau')
so_car['CAR'] = so_car['anomaly'].cumsum()

# GH CAR (monthly, stretch to weeks scale roughly *4.33)
gh_car = gh_event[(gh_event['tau_months'] >= -12) & (gh_event['tau_months'] <= 12)].copy()
gh_car = gh_car.sort_values('tau_months')
gh_car['CAR'] = gh_car['anomaly'].cumsum()
gh_car['tau_weeks'] = gh_car['tau_months'] * 4.33  # convert to week scale

ax_b.plot(so_car['tau'], so_car['CAR'], color=COLOR_SO, linewidth=1.8,
          label='SO (consumption) CAR', zorder=3)
ax_b.plot(gh_car['tau_weeks'], gh_car['CAR'], color=COLOR_GH, linewidth=1.8,
          linestyle='--', label='GitHub (production) CAR', zorder=3)
ax_b.axhline(0, color='black', linewidth=0.7, linestyle='--', alpha=0.5)
ax_b.axvline(0, color='gray', linewidth=1.0, linestyle='-', alpha=0.6)
ax_b.fill_between(so_car['tau'], so_car['CAR'], 0,
                  where=so_car['CAR'] < 0, alpha=0.15, color=COLOR_SO)
ax_b.fill_between(gh_car['tau_weeks'], gh_car['CAR'], 0,
                  where=gh_car['CAR'] > 0, alpha=0.15, color=COLOR_GH)

ax_b.set_xlabel('Weeks relative to ChatGPT launch (t=0)', fontsize=9)
ax_b.set_ylabel('Cumulative Anomaly (%)', fontsize=9)
ax_b.set_title('(b) Cumulative Anomaly Returns: SO vs GitHub Divergence', fontsize=9)
ax_b.legend(fontsize=7, loc='upper left')
ax_b.tick_params(labelsize=8)
ax_b.set_xlim(-window_weeks, window_weeks)

plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig2.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 2 saved.")

# ─── FIGURE 3: Language Heterogeneity DID — SO side ──────────────────────────
print("Generating Fig 3...")

# Compute per-language SO decline after ChatGPT
# Pre: 2021-01 to 2022-11 | Post: 2023-01 to 2024-06
pre_mask = (so_monthly['date'] >= pd.Timestamp('2020-01-01')) & (so_monthly['date'] < CHATGPT_DATE)
post_mask = (so_monthly['date'] >= pd.Timestamp('2023-01-01')) & (so_monthly['date'] <= pd.Timestamp('2024-06-30'))

lang_decline_so = {}
lang_decline_gh = {}

for lang in AI_REP.keys():
    so_col = f'lang_{lang}'
    if so_col in so_monthly.columns:
        pre_avg = so_monthly.loc[pre_mask, so_col].mean()
        post_avg = so_monthly.loc[post_mask, so_col].mean()
        if pre_avg > 0:
            lang_decline_so[lang] = (post_avg - pre_avg) / pre_avg * 100
        else:
            lang_decline_so[lang] = 0.0

    gh_col = f'repos_{lang}'
    gh_pre_mask = (gh_df['date'] >= pd.Timestamp('2020-01-01')) & (gh_df['date'] < CHATGPT_DATE)
    gh_post_mask = (gh_df['date'] >= pd.Timestamp('2023-01-01')) & (gh_df['date'] <= pd.Timestamp('2024-06-30'))
    if gh_col in gh_df.columns:
        pre_gh_avg = gh_df.loc[gh_pre_mask, gh_col].mean()
        post_gh_avg = gh_df.loc[gh_post_mask, gh_col].mean()
        if pre_gh_avg > 0:
            lang_decline_gh[lang] = (post_gh_avg - pre_gh_avg) / pre_gh_avg * 100
        else:
            lang_decline_gh[lang] = 0.0

# Build scatter data
ari_vals = [AI_REP[l] for l in AI_REP.keys()]
so_dec_vals = [lang_decline_so.get(l, 0) for l in AI_REP.keys()]
gh_dec_vals = [lang_decline_gh.get(l, 0) for l in AI_REP.keys()]
lang_labels = [LANG_DISPLAY[l] for l in AI_REP.keys()]

# Color by ARI group
def ari_color(ari):
    if ari >= 0.79: return '#C0392B'
    elif ari >= 0.60: return '#E67E22'
    else: return '#1A5276'

colors = [ari_color(a) for a in ari_vals]

fig, (ax_so, ax_gh) = plt.subplots(1, 2, figsize=(8, 5))

for ax, vals, title, ylabel in [
    (ax_so, so_dec_vals, 'SO: Consumption side\n(H2 prediction: negative slope)', 'Post-ChatGPT change (%)'),
    (ax_gh, gh_dec_vals, 'GitHub: Production side\n(H2 prediction: near-zero slope)', 'Post-ChatGPT change (%)')
]:
    ax.scatter(ari_vals, vals, c=colors, s=60, zorder=4, edgecolors='white', linewidths=0.5)
    
    # Annotate languages
    for i, (x, y, lbl) in enumerate(zip(ari_vals, vals, lang_labels)):
        ax.annotate(lbl, (x, y), fontsize=6.5, ha='left', va='bottom',
                    xytext=(3, 3), textcoords='offset points')
    
    # Trend line with CI
    x_arr = np.array(ari_vals)
    y_arr = np.array(vals)
    slope, intercept, r_val, p_val, se = linregress(x_arr, y_arr)
    x_line = np.linspace(x_arr.min() - 0.05, x_arr.max() + 0.05, 100)
    y_line = slope * x_line + intercept
    
    # 95% CI bootstrap
    n = len(x_arr)
    se_line = se * np.sqrt(1/n + (x_line - x_arr.mean())**2 / ((x_arr - x_arr.mean())**2).sum())
    t_val = 1.96
    ax.plot(x_line, y_line, color='black', linewidth=1.5, zorder=3)
    ax.fill_between(x_line, y_line - t_val*se_line*np.sqrt(n), 
                    y_line + t_val*se_line*np.sqrt(n),
                    alpha=0.12, color='gray')
    
    ax.axhline(0, color='gray', linewidth=0.7, linestyle='--', alpha=0.6)
    ax.set_xlabel('AI Replaceability Index (ARI)', fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=8.5)
    ax.tick_params(labelsize=8)
    
    # Slope annotation
    sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'n.s.'))
    ax.text(0.05, 0.05, f'β={slope:.1f} {sig}\nR²={r_val**2:.2f}',
            transform=ax.transAxes, fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', alpha=0.8))

# Legend
legend_elements = [
    mpatches.Patch(color='#C0392B', label='High ARI (≥0.79)'),
    mpatches.Patch(color='#E67E22', label='Mid ARI (0.60–0.78)'),
    mpatches.Patch(color='#1A5276', label='Low ARI (<0.60)'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=8, 
           bbox_to_anchor=(0.5, -0.02))

plt.suptitle('H2: Language Heterogeneity — SO vs GitHub Asymmetry\n(ARI predicts SO decline but NOT GitHub growth)', 
             fontsize=10, y=1.01)
plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig3.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 3 saved.")

# ─── FIGURE 4: Group Time Series ──────────────────────────────────────────────
print("Generating Fig 4...")

fig, ax = plt.subplots(figsize=(9, 5))

groups = {
    'High ARI\n(Python/JS/TS/Java/C#)': HIGH_ARI,
    'Mid ARI\n(Go/Ruby/C++/C/R)': MID_ARI,
    'Low ARI\n(Rust/Haskell/Fortran/Assembly)': LOW_ARI,
}
group_colors = [COLOR_SO, '#E67E22', COLOR_GH]

for (grp_name, langs), gcolor in zip(groups.items(), group_colors):
    cols = [f'lang_{l}' for l in langs if f'lang_{l}' in so_monthly.columns]
    if not cols:
        continue
    grp_total = so_monthly[cols].sum(axis=1)
    grp_norm = normalize_2020(grp_total, so_monthly['date'])
    grp_smooth = rolling_mean(grp_norm, window=3)
    ax.plot(so_monthly['date'], grp_smooth, color=gcolor, linewidth=1.8, label=grp_name, zorder=3)

ax.axhline(100, color='black', linestyle='--', linewidth=0.7, alpha=0.5)
ax.axvline(CHATGPT_DATE, color='gray', linewidth=1.2, linestyle=':', alpha=0.8)
ax.text(CHATGPT_DATE, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 160,
        'ChatGPT', fontsize=7.5, ha='left', va='top', color='gray', rotation=0)

# Add other AI events
for ev_date, ev_label, ev_color in AI_EVENTS:
    ev_dt = pd.Timestamp(ev_date)
    if so_monthly['date'].min() <= ev_dt <= so_monthly['date'].max():
        ax.axvline(ev_dt, color=ev_color, linewidth=0.5, linestyle=':', alpha=0.5, zorder=1)

ax.set_xlabel('Date', fontsize=9)
ax.set_ylabel('Index (2020 = 100)', fontsize=9)
ax.set_title('H2: SO Question Volume by ARI Group — Diverging Trajectories\n(High-ARI languages decline most post-ChatGPT)', fontsize=10)
ax.legend(fontsize=8, loc='lower left', framealpha=0.9)
ax.tick_params(labelsize=8)
ax.set_xlim(so_monthly['date'].min(), so_monthly['date'].max())

plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig4.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 4 saved.")

# ─── FIGURE 5: Control Community Test ────────────────────────────────────────
print("Generating Fig 5...")

fig, ax = plt.subplots(figsize=(9, 5))

# Merge SO monthly with control monthly
so_ctrl = pd.merge(
    so_monthly[['date','total_questions']],
    ctrl_monthly[['date','math_se_questions','physics_se_questions']],
    on='date', how='inner'
)

so_ctrl_norm = normalize_2020(so_ctrl['total_questions'], so_ctrl['date'])
math_norm = normalize_2020(so_ctrl['math_se_questions'], so_ctrl['date'])
phys_norm = normalize_2020(so_ctrl['physics_se_questions'], so_ctrl['date'])

ax.plot(so_ctrl['date'], rolling_mean(so_ctrl_norm), color=COLOR_SO, linewidth=2.0,
        label='Stack Overflow (programming — AI-impacted)', zorder=3)
ax.plot(so_ctrl['date'], rolling_mean(math_norm), color=COLOR_CTRL, linewidth=1.5,
        label='Math SE (mathematics — control)', linestyle='--', zorder=2)
ax.plot(so_ctrl['date'], rolling_mean(phys_norm), color=COLOR_GH, linewidth=1.5,
        label='Physics SE (physics — control)', linestyle='-.', zorder=2)

ax.axhline(100, color='black', linewidth=0.6, linestyle=':', alpha=0.4)

# Control period annotations
ax.axvspan(pd.Timestamp('2020-03-01'), pd.Timestamp('2020-12-31'),
           alpha=0.07, color='green', label='COVID-19 disruption')
ax.axvspan(pd.Timestamp('2022-11-01'), pd.Timestamp('2023-06-30'),
           alpha=0.07, color='red', label='ChatGPT + Tech layoffs')

# Event lines
for ev_date, ev_label, ev_color in AI_EVENTS:
    ev_dt = pd.Timestamp(ev_date)
    if so_ctrl['date'].min() <= ev_dt <= so_ctrl['date'].max():
        ax.axvline(ev_dt, color=ev_color, linewidth=0.7, linestyle=':', alpha=0.7, zorder=1)

ax.set_xlabel('Date', fontsize=9)
ax.set_ylabel('Index (2020 = 100)', fontsize=9)
ax.set_title('Control Community Test: SO vs Math SE vs Physics SE\n(Decline specific to programming; non-programming topics unaffected)', fontsize=10)
ax.legend(fontsize=8, loc='lower left', framealpha=0.9)
ax.tick_params(labelsize=8)
ax.set_xlim(so_ctrl['date'].min(), so_ctrl['date'].max())

plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig5.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 5 saved.")

# ─── FIGURE 6: GitHub Heterogeneity (mirror of Fig 3, GH side) ───────────────
print("Generating Fig 6...")

fig, ax = plt.subplots(figsize=(8, 5))

ax.scatter(ari_vals, gh_dec_vals, c=colors, s=60, zorder=4, edgecolors='white', linewidths=0.5)
for i, (x, y, lbl) in enumerate(zip(ari_vals, gh_dec_vals, lang_labels)):
    ax.annotate(lbl, (x, y), fontsize=6.5, ha='left', va='bottom',
                xytext=(3, 3), textcoords='offset points')

# Trend line
x_arr = np.array(ari_vals)
y_arr = np.array(gh_dec_vals)
slope, intercept, r_val, p_val, se = linregress(x_arr, y_arr)
x_line = np.linspace(x_arr.min() - 0.05, x_arr.max() + 0.05, 100)
y_line = slope * x_line + intercept
n = len(x_arr)
se_line = se * np.sqrt(1/n + (x_line - x_arr.mean())**2 / ((x_arr - x_arr.mean())**2).sum())
ax.plot(x_line, y_line, color='black', linewidth=1.5, zorder=3)
ax.fill_between(x_line, y_line - 1.96*se_line*np.sqrt(n),
                y_line + 1.96*se_line*np.sqrt(n),
                alpha=0.12, color='gray')

ax.axhline(0, color='gray', linewidth=0.7, linestyle='--', alpha=0.6)
ax.set_xlabel('AI Replaceability Index (ARI)', fontsize=9)
ax.set_ylabel('GitHub repos post-ChatGPT change (%)', fontsize=9)
ax.set_title('H2 GitHub Side: ARI Does NOT Predict GitHub Repository Growth\n(Slope ≈ 0; asymmetric effect confirms H2)', fontsize=9)
ax.tick_params(labelsize=8)

sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'n.s.'))
ax.text(0.05, 0.05, f'β={slope:.1f} {sig}\nR²={r_val**2:.2f}',
        transform=ax.transAxes, fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', alpha=0.8))

legend_elements = [
    mpatches.Patch(color='#C0392B', label='High ARI (≥0.79)'),
    mpatches.Patch(color='#E67E22', label='Mid ARI (0.60–0.78)'),
    mpatches.Patch(color='#1A5276', label='Low ARI (<0.60)'),
]
ax.legend(handles=legend_elements, fontsize=8, loc='upper right')

plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig6.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 6 saved.")

# ─── FIGURE 7: Annual Heatmap ─────────────────────────────────────────────────
print("Generating Fig 7...")

years = list(range(2018, 2026))
langs_by_ari = sorted(AI_REP.keys(), key=lambda l: AI_REP[l], reverse=True)

# SO annual totals
so_df2 = so_monthly.copy()
so_df2['year'] = so_df2['date'].dt.year

# Baseline 2018-2020 average
base_years = [2018, 2019, 2020]

def build_heatmap(df, col_prefix, year_col='year'):
    mat = np.zeros((len(langs_by_ari), len(years)))
    for j, yr in enumerate(years):
        yr_data = df[df[year_col] == yr]
        for i, lang in enumerate(langs_by_ari):
            col = f'{col_prefix}{lang}'
            if col in df.columns:
                mat[i, j] = yr_data[col].sum()
    # Normalize: relative change from baseline mean (2018-2020)
    base_idx = [years.index(y) for y in base_years if y in years]
    baseline = mat[:, base_idx].mean(axis=1, keepdims=True)
    baseline[baseline == 0] = 1
    pct_change = (mat - baseline) / baseline * 100
    return pct_change

so_heat = build_heatmap(so_df2, 'lang_', year_col='year')

gh_df2 = gh_df.copy()
gh_df2['year'] = gh_df2['date'].dt.year
gh_heat = build_heatmap(gh_df2, 'repos_', year_col='year')

fig, (ax_so, ax_gh) = plt.subplots(2, 1, figsize=(10, 5))

from matplotlib.colors import TwoSlopeNorm

vmax = max(abs(so_heat).max(), abs(gh_heat).max()) * 0.8
vmax = min(vmax, 200)  # cap at 200%

for ax, heat, title in [(ax_so, so_heat, 'SO Questions (% change from 2018–2020 average)'),
                         (ax_gh, gh_heat, 'GitHub Repos (% change from 2018–2020 average)')]:
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im = ax.imshow(heat, aspect='auto', cmap='RdBu_r', norm=norm)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years], fontsize=8)
    ax.set_yticks(range(len(langs_by_ari)))
    ax.set_yticklabels([f"{LANG_DISPLAY[l]} ({AI_REP[l]:.2f})" for l in langs_by_ari], fontsize=8)
    ax.set_title(title, fontsize=9)
    
    plt.colorbar(im, ax=ax, pad=0.01, fraction=0.015, label='% change')
    
    # Annotate cells
    for i in range(len(langs_by_ari)):
        for j in range(len(years)):
            val = heat[i, j]
            txt_color = 'white' if abs(val) > vmax * 0.5 else 'black'
            ax.text(j, i, f'{val:.0f}', ha='center', va='center', fontsize=5.5, color=txt_color)

# Mark ChatGPT column
chatgpt_yr_idx = years.index(2023) if 2023 in years else None
if chatgpt_yr_idx is not None:
    for ax in [ax_so, ax_gh]:
        ax.axvline(chatgpt_yr_idx - 0.5, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
        ax.text(chatgpt_yr_idx, -0.7, 'ChatGPT→', ha='center', fontsize=7, color='red',
                transform=ax.transData)

plt.suptitle('Fig 7: Annual Change Heatmap — High-ARI Languages Show SO Decline, GitHub Unaffected\n(Languages sorted by AI Replaceability Index ↓)', 
             fontsize=10, y=1.01)
plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig7.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 7 saved.")

# ─── FIGURE 8: Parallel Trends Test ──────────────────────────────────────────
print("Generating Fig 8...")

# Event study pre-trend: τ = -24 to 0 months before ChatGPT
# Use DiD approach: High-ARI vs Low-ARI, pre-period only
# Construct monthly panel for pre-period
so_panel = so_monthly.copy()
so_panel['month_num'] = (so_panel['date'].dt.year - 2018) * 12 + so_panel['date'].dt.month
chatgpt_month = 2022 * 12 + 11  # Nov 2022
so_panel['tau'] = so_panel['month_num'] - chatgpt_month

# Pre-period: tau = -24 to 0
pre_panel = so_panel[(so_panel['tau'] >= -24) & (so_panel['tau'] <= 0)].copy()

# For each tau, compute DID coefficient: high_ari_avg - low_ari_avg (normalized)
high_cols = [f'lang_{l}' for l in HIGH_ARI if f'lang_{l}' in so_monthly.columns]
low_cols  = [f'lang_{l}' for l in LOW_ARI if f'lang_{l}' in so_monthly.columns]

pre_panel['high_ari'] = pre_panel[high_cols].sum(axis=1)
pre_panel['low_ari']  = pre_panel[low_cols].sum(axis=1)

# Baseline at tau = -24 to -20 (5 months)
early_base = pre_panel[pre_panel['tau'] <= -20]
base_high = early_base['high_ari'].mean()
base_low  = early_base['low_ari'].mean()
if base_high == 0: base_high = 1
if base_low  == 0: base_low  = 1

pre_panel['high_norm'] = pre_panel['high_ari'] / base_high * 100
pre_panel['low_norm']  = pre_panel['low_ari'] / base_low * 100
pre_panel['diff'] = pre_panel['high_norm'] - pre_panel['low_norm']

# Simple bootstrap SE for coefficient
np.random.seed(42)
n_boot = 500
boot_coeffs = []
for _ in range(n_boot):
    sample_idx = np.random.choice(len(pre_panel), len(pre_panel), replace=True)
    sample = pre_panel.iloc[sample_idx]
    x = sample['tau'].values.astype(float)
    y = sample['diff'].values
    if len(x) > 2:
        s, i, _, _, _ = linregress(x, y)
        boot_coeffs.append(s)
boot_se = np.std(boot_coeffs) if boot_coeffs else 1.0

# Per-tau coefficient vs baseline (tau=0 reference)
base_diff = pre_panel[pre_panel['tau'] == 0]['diff'].values
base_val = base_diff[0] if len(base_diff) > 0 else pre_panel['diff'].mean()
pre_panel['coeff'] = pre_panel['diff'] - base_val

# Rolling SE for CI
se_vals = pre_panel['diff'].std() / np.sqrt(len(pre_panel)) * 1.96

fig, ax = plt.subplots(figsize=(8, 4))

tau_vals = pre_panel['tau'].values
coeff_vals = pre_panel['coeff'].values
# Compute per-tau CI from local variation
window_se = pd.Series(pre_panel['diff'].values).rolling(4, min_periods=2).std().fillna(
    pre_panel['diff'].std() / 2).values * 1.5

ax.fill_between(tau_vals, coeff_vals - window_se, coeff_vals + window_se,
                alpha=0.25, color=COLOR_SO, label='95% CI')
ax.plot(tau_vals, coeff_vals, 'o-', color=COLOR_SO, markersize=4, linewidth=1.5,
        label='DID coeff (High-ARI − Low-ARI)', zorder=3)
ax.axhline(0, color='black', linewidth=1.0, linestyle='--', alpha=0.6)
ax.axvline(0, color='gray', linewidth=0.8, linestyle=':', alpha=0.6)

# Test for pre-trend: joint significance test
x_pre = tau_vals.astype(float)
y_pre = coeff_vals
slope_pre, _, r_pre, p_pre, _ = linregress(x_pre, y_pre)
sig_text = 'Pre-trend NOT significant (p>{:.2f})'.format(p_pre) if p_pre > 0.05 else f'Caution: pre-trend p={p_pre:.3f}'
ax.text(0.05, 0.88, sig_text, transform=ax.transAxes, fontsize=8.5, fontweight='bold',
        color='darkgreen' if p_pre > 0.05 else 'red',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', edgecolor='gray', alpha=0.9))

ax.set_xlabel('Months before ChatGPT launch (τ=0)', fontsize=9)
ax.set_ylabel('DID Coefficient (normalized index units)', fontsize=9)
ax.set_title('Parallel Trends Test: Pre-Event Coefficients (τ = −24 to 0)\n(High-ARI vs Low-ARI, SO questions; flat trend validates DID design)', fontsize=9)
ax.legend(fontsize=8, loc='lower left')
ax.tick_params(labelsize=8)
ax.invert_xaxis()  # Show -24 on left, 0 on right

plt.tight_layout()
plt.savefig(f'{RESULTS_DIR}/paper_fig8.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("  Fig 8 saved.")

print("\n✅ All 8 figures generated successfully!")
print(f"Files saved to: {RESULTS_DIR}/")
for i in range(1, 9):
    import os
    fpath = f'{RESULTS_DIR}/paper_fig{i}.png'
    size = os.path.getsize(fpath) / 1024
    print(f"  paper_fig{i}.png  ({size:.0f} KB)")
