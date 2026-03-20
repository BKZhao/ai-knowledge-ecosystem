#!/usr/bin/env python3
"""
Generate 5 GitHub analysis figures (Nature/Science style, 300 DPI)
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
import warnings
warnings.filterwarnings('ignore')

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"
OUT  = "/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results"

# ── Load data ────────────────────────────────────────────────────────────────
with open(f"{BASE}/github_cache_weekly.json") as f:
    gh_raw = json.load(f)

with open(f"{BASE}/api_cache_weekly.json") as f:
    so_raw = json.load(f)

# ── GitHub monthly DataFrame ─────────────────────────────────────────────────
gh_rows = list(gh_raw.values())
gh = pd.DataFrame(gh_rows)
gh['date'] = pd.to_datetime(gh['month_dt'])
gh = gh.sort_values('date').reset_index(drop=True)

LANGS = ['python','javascript','typescript','java','csharp','go','rust','cpp','c','ruby','assembly','haskell']
# R not in github data, skip

# Total repos / issues per month
gh['total_repos']  = gh[[f'repos_{l}'  for l in LANGS]].sum(axis=1)
gh['total_issues'] = gh[[f'issues_{l}' for l in LANGS]].sum(axis=1)

# ── SO weekly → monthly ──────────────────────────────────────────────────────
so_rows = list(so_raw.values())
so = pd.DataFrame(so_rows)
so['date'] = pd.to_datetime(so['week_dt'])
so = so.sort_values('date').reset_index(drop=True)
so['month'] = so['date'].dt.to_period('M')
so_monthly = so.groupby('month').agg({
    'total_questions': 'sum',
    **{f'lang_{l}': 'sum' for l in ['python','javascript','java','csharp','typescript','cpp','c','go','rust','assembly','ruby','r','haskell']}
}).reset_index()
so_monthly['date'] = so_monthly['month'].dt.to_timestamp()

# ── Constants ────────────────────────────────────────────────────────────────
AI_EVENTS = [
    ("2021-10-01","Copilot Beta","#95A5A6"),
    ("2022-06-21","Copilot GA","#7F8C8D"),
    ("2022-11-30","ChatGPT","#E74C3C"),
    ("2023-03-14","GPT-4","#C0392B"),
    ("2023-07-18","Claude 2+Llama 2","#8E44AD"),
    ("2024-03-04","Claude 3","#1A5276"),
    ("2024-06-20","Claude 3.5","#154360"),
]

AI_REP = {
    'python':0.92,'javascript':0.88,'typescript':0.85,'java':0.81,
    'csharp':0.79,'go':0.72,'ruby':0.65,'cpp':0.63,'c':0.60,'r':0.58,
    'rust':0.35,'haskell':0.25,'assembly':0.10
}

LANG_LABELS = {
    'python':'Python','javascript':'JavaScript','typescript':'TypeScript',
    'java':'Java','csharp':'C#','go':'Go','rust':'Rust','cpp':'C++',
    'c':'C','ruby':'Ruby','assembly':'Assembly','haskell':'Haskell','r':'R'
}

# Nature style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
})

def add_ai_events(ax, ymin, ymax, alpha=0.85):
    """Add vertical lines for AI events."""
    for date_str, label, color in AI_EVENTS:
        dt = pd.Timestamp(date_str)
        ax.axvline(dt, color=color, linewidth=0.9, linestyle='--', alpha=0.75, zorder=2)
        # Stagger labels to avoid overlap
        y_pos = ymax * 0.97 if AI_EVENTS.index((date_str,label,color)) % 2 == 0 else ymax * 0.90
        ax.text(dt, y_pos, label, rotation=90, fontsize=6.5, color=color,
                ha='right', va='top', alpha=0.9)

def normalize_to_2020(series, dates):
    """Normalize series to 2020 average = 100."""
    mask = (dates >= '2020-01-01') & (dates <= '2020-12-31')
    base = series[mask].mean()
    if base == 0:
        return series * 0
    return series / base * 100


# ══════════════════════════════════════════════════════════════════════════════
# FIG 1 — GitHub总量趋势 vs SO总量
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Fig 1...")
fig, ax1 = plt.subplots(figsize=(9, 4))

# GitHub normalized
gh_norm = normalize_to_2020(gh['total_repos'], gh['date'])
ax1.plot(gh['date'], gh_norm, color='#2166AC', linewidth=1.8, label='GitHub Repos (normalized)', zorder=4)
ax1.fill_between(gh['date'], gh_norm, alpha=0.12, color='#2166AC')

# SO normalized on same axis (secondary)
ax2 = ax1.twinx()
so_norm = normalize_to_2020(so_monthly['total_questions'], so_monthly['date'])
ax2.plot(so_monthly['date'], so_norm, color='#D6604D', linewidth=1.5,
         linestyle='-', label='SO Questions (normalized)', zorder=3)
ax2.fill_between(so_monthly['date'], so_norm, alpha=0.08, color='#D6604D')
ax2.set_ylabel('SO Questions (2020=100)', color='#D6604D', fontsize=10)
ax2.tick_params(axis='y', labelcolor='#D6604D')
ax2.spines['right'].set_visible(True)
ax2.spines['top'].set_visible(False)

# AI events
for date_str, label, color in AI_EVENTS:
    dt = pd.Timestamp(date_str)
    ax1.axvline(dt, color=color, linewidth=1.0, linestyle='--', alpha=0.8, zorder=2)

# Label key events
event_labels = [
    ("2022-11-30", "ChatGPT", "#E74C3C", 0.92),
    ("2023-03-14", "GPT-4",   "#C0392B", 0.82),
    ("2022-06-21", "Copilot GA", "#7F8C8D", 0.72),
    ("2024-03-04", "Claude 3", "#1A5276", 0.62),
]
ymax_ax1 = gh_norm.max() * 1.05
for date_str, label, color, yfrac in event_labels:
    dt = pd.Timestamp(date_str)
    ax1.text(dt + pd.Timedelta(days=20), ymax_ax1 * yfrac, label,
             fontsize=7, color=color, ha='left', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor='none'))

ax1.set_xlabel('Date', fontsize=10)
ax1.set_ylabel('GitHub Repos (2020=100)', color='#2166AC', fontsize=10)
ax1.tick_params(axis='y', labelcolor='#2166AC')
ax1.set_xlim(gh['date'].min(), gh['date'].max())
ax1.set_ylim(0, ymax_ax1 * 1.05)

# Shade ChatGPT era
chatgpt_dt = pd.Timestamp("2022-11-30")
ax1.axvspan(chatgpt_dt, gh['date'].max(), alpha=0.06, color='#E74C3C', zorder=1)
ax1.text(chatgpt_dt + pd.DateOffset(months=1), ymax_ax1 * 0.25,
         'Post-ChatGPT Era', fontsize=8, color='#E74C3C', alpha=0.7)

# Combined legend
lines1 = [Line2D([0],[0], color='#2166AC', linewidth=1.8, label='GitHub Repos'),
          Line2D([0],[0], color='#D6604D', linewidth=1.5, label='SO Questions')]
ax1.legend(handles=lines1, loc='upper left', framealpha=0.9)

ax1.set_title('Figure 1: GitHub Repository Activity vs. Stack Overflow Questions\n'
              'Both normalized to 2020=100; GitHub surges post-ChatGPT while SO declines',
              fontsize=10, pad=8)

# Grid
ax1.yaxis.grid(True, alpha=0.3, linewidth=0.5)
ax1.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"{OUT}/github_fig1.png", dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("  ✓ github_fig1.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIG 2 — 各语言变化幅度排序（水平条形图）
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Fig 2...")

# Compute pre/post ChatGPT change for repos and issues
pre_mask  = (gh['date'] >= '2021-12-01') & (gh['date'] <= '2022-11-30')
post_mask = (gh['date'] >= '2023-01-01') & (gh['date'] <= '2024-01-31')

change_repos  = {}
change_issues = {}
for lang in LANGS:
    pre_r  = gh.loc[pre_mask,  f'repos_{lang}'].mean()
    post_r = gh.loc[post_mask, f'repos_{lang}'].mean()
    pre_i  = gh.loc[pre_mask,  f'issues_{lang}'].mean()
    post_i = gh.loc[post_mask, f'issues_{lang}'].mean()
    change_repos[lang]  = (post_r - pre_r) / pre_r * 100 if pre_r > 0 else 0
    change_issues[lang] = (post_i - pre_i) / pre_i * 100 if pre_i > 0 else 0

# Sort by repos change
sorted_langs = sorted(LANGS, key=lambda l: change_repos[l])

fig, ax = plt.subplots(figsize=(8, 6))

y_pos = np.arange(len(sorted_langs))
bar_height = 0.35

repos_vals  = [change_repos[l]  for l in sorted_langs]
issues_vals = [change_issues[l] for l in sorted_langs]

bars1 = ax.barh(y_pos + bar_height/2, repos_vals,  bar_height, color='#2166AC', alpha=0.85, label='Repos change %')
bars2 = ax.barh(y_pos - bar_height/2, issues_vals, bar_height, color='#F4A582', alpha=0.85, label='Issues change %')

# Y-tick labels
ax.set_yticks(y_pos)
ax.set_yticklabels([LANG_LABELS[l] for l in sorted_langs], fontsize=9)

# Annotate ARI
for i, lang in enumerate(sorted_langs):
    ari = AI_REP.get(lang, 0)
    ax.text(max(repos_vals[i], issues_vals[i]) + 3, y_pos[i],
            f'ARI={ari}', fontsize=7, va='center', color='#555555')

# Zero line
ax.axvline(0, color='black', linewidth=0.8)

# Highlight negative bars
for bar in bars1:
    if bar.get_width() < 0:
        bar.set_color('#D6604D')
for bar in bars2:
    if bar.get_width() < 0:
        bar.set_color('#D6604D')

ax.set_xlabel('Change (%) vs. Pre-ChatGPT Baseline', fontsize=10)
ax.set_title('Figure 2: Language-Level GitHub Activity Change (Pre vs. Post-ChatGPT)\n'
             'Ruby & Haskell decline; TypeScript, Rust, Python surge', fontsize=10, pad=8)

handles = [mpatches.Patch(color='#2166AC', label='Repos change (%)'),
           mpatches.Patch(color='#F4A582', label='Issues change (%)'),
           mpatches.Patch(color='#D6604D', label='Negative change')]
ax.legend(handles=handles, loc='lower right', framealpha=0.9)
ax.xaxis.grid(True, alpha=0.3, linewidth=0.5)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"{OUT}/github_fig2.png", dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("  ✓ github_fig2.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIG 3 — GitHub vs SO 不对称散点（双面板）
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Fig 3...")

# SO change per language (pre/post ChatGPT)
so_pre_mask  = (so_monthly['date'] >= '2021-12-01') & (so_monthly['date'] <= '2022-11-30')
so_post_mask = (so_monthly['date'] >= '2023-01-01') & (so_monthly['date'] <= '2024-01-31')

so_change = {}
for lang in ['python','javascript','java','csharp','typescript','cpp','c','go','rust','assembly','ruby','r','haskell']:
    col = f'lang_{lang}'
    pre_s  = so_monthly.loc[so_pre_mask,  col].mean()
    post_s = so_monthly.loc[so_post_mask, col].mean()
    so_change[lang] = (post_s - pre_s) / pre_s * 100 if pre_s > 0 else None

# Common languages with both SO and GitHub data
common_langs = [l for l in LANGS if l in so_change and so_change[l] is not None]

ari_vals   = [AI_REP[l] for l in common_langs]
so_vals    = [so_change[l]      for l in common_langs]
gh_vals    = [change_repos[l]   for l in common_langs]
labels_c   = [LANG_LABELS[l]   for l in common_langs]

# Color by language category
cat_colors = []
rising  = ['typescript','python','rust','go','javascript']
stable  = ['c','cpp','java','csharp']
decline = ['ruby','haskell']
for l in common_langs:
    if l in rising:  cat_colors.append('#2166AC')
    elif l in stable: cat_colors.append('#4DAC26')
    else:            cat_colors.append('#D6604D')

fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(8, 5))

# ── Panel (a): ARI vs SO change ──
r_so, p_so = stats.pearsonr(ari_vals, so_vals)
ax_a.scatter(ari_vals, so_vals, c=cat_colors, s=70, edgecolors='white', linewidths=0.8, zorder=4)
for i, lab in enumerate(labels_c):
    ax_a.annotate(lab, (ari_vals[i], so_vals[i]),
                  textcoords='offset points', xytext=(4, 2), fontsize=7.5, color='#333333')

m_so, b_so, _, _, _ = stats.linregress(ari_vals, so_vals)
x_line = np.linspace(min(ari_vals), max(ari_vals), 100)
ax_a.plot(x_line, m_so*x_line + b_so, '--', color='gray', linewidth=1.2, alpha=0.7)
ax_a.axhline(0, color='black', linewidth=0.7, alpha=0.5)

ax_a.set_xlabel('AI Replaceability Index (ARI)', fontsize=10)
ax_a.set_ylabel('SO Questions Change (%) Post-ChatGPT', fontsize=9)
ax_a.set_title(f'(a) ARI vs. SO Decline\nr = {r_so:.2f}, p = {p_so:.3f}', fontsize=9)
ax_a.text(0.05, 0.05, f'r = {r_so:.2f}\np = {p_so:.3f}',
          transform=ax_a.transAxes, fontsize=9,
          bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

# ── Panel (b): ARI vs GitHub change ──
r_gh, p_gh = stats.pearsonr(ari_vals, gh_vals)
ax_b.scatter(ari_vals, gh_vals, c=cat_colors, s=70, edgecolors='white', linewidths=0.8, zorder=4)
for i, lab in enumerate(labels_c):
    ax_b.annotate(lab, (ari_vals[i], gh_vals[i]),
                  textcoords='offset points', xytext=(4, 2), fontsize=7.5, color='#333333')

m_gh, b_gh, _, _, _ = stats.linregress(ari_vals, gh_vals)
ax_b.plot(x_line, m_gh*x_line + b_gh, '--', color='gray', linewidth=1.2, alpha=0.7)
ax_b.axhline(0, color='black', linewidth=0.7, alpha=0.5)

ax_b.set_xlabel('AI Replaceability Index (ARI)', fontsize=10)
ax_b.set_ylabel('GitHub Repos Change (%) Post-ChatGPT', fontsize=9)
ax_b.set_title(f'(b) ARI vs. GitHub Growth\nr = {r_gh:.2f}, p = {p_gh:.3f}', fontsize=9)
ax_b.text(0.05, 0.05, f'r = {r_gh:.2f}\np = {p_gh:.3f}',
          transform=ax_b.transAxes, fontsize=9,
          bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

# Shared legend
handles_leg = [mpatches.Patch(color='#2166AC', label='Rising (TS/Py/Rust/Go/JS)'),
               mpatches.Patch(color='#4DAC26', label='Stable (C/C++/Java/C#)'),
               mpatches.Patch(color='#D6604D', label='Declining (Ruby/Haskell)')]
fig.legend(handles=handles_leg, loc='lower center', ncol=3, fontsize=8,
           bbox_to_anchor=(0.5, -0.02), framealpha=0.9)

fig.suptitle('Figure 3: Asymmetry — ARI Predicts SO Decline but NOT GitHub Growth\n'
             'Knowledge consumption collapses; production activity is indifferent to AI replaceability',
             fontsize=9.5, y=1.02)

plt.tight_layout()
plt.savefig(f"{OUT}/github_fig3.png", dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("  ✓ github_fig3.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIG 4 — GitHub语言时序（3类分组）
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Fig 4...")

rising_langs  = ['typescript','python','rust','go','javascript']
stable_langs  = ['c','cpp','java','csharp']
decline_langs = ['ruby','haskell']

lang_groups = [
    ("Rising Languages (TypeScript / Python / Rust / Go / JavaScript)", rising_langs,
     ['#1F78B4','#33A02C','#FF7F00','#6A3D9A','#E31A1C']),
    ("Stable Languages (C / C++ / Java / C#)", stable_langs,
     ['#A6761D','#D95F02','#7570B3','#1B9E77']),
    ("Declining Languages (Ruby / Haskell)", decline_langs,
     ['#CC4C02','#8B0000']),
]

chatgpt_dt = pd.Timestamp("2022-11-30")

fig, axes = plt.subplots(3, 1, figsize=(9, 6), sharex=True)

for ax, (title, langs, colors) in zip(axes, lang_groups):
    for lang, color in zip(langs, colors):
        col = f'repos_{lang}'
        raw = gh[col].rolling(3, center=True, min_periods=1).mean()
        norm = normalize_to_2020(raw, gh['date'])
        ax.plot(gh['date'], norm, color=color, linewidth=1.5,
                label=LANG_LABELS[lang], zorder=4)

    ax.axvline(chatgpt_dt, color='#E74C3C', linewidth=1.2, linestyle='--', alpha=0.8, zorder=5)
    ax.axhline(100, color='gray', linewidth=0.6, linestyle=':', alpha=0.6)
    ax.text(chatgpt_dt + pd.Timedelta(days=15), ax.get_ylim()[1]*0.9 if ax.get_ylim()[1] > 0 else 150,
            'ChatGPT', fontsize=7.5, color='#E74C3C', ha='left')
    ax.set_ylabel('Activity (2020=100)', fontsize=9)
    ax.set_title(title, fontsize=9, pad=3)
    ax.legend(loc='upper left', fontsize=7.5, ncol=len(langs), framealpha=0.85)
    ax.yaxis.grid(True, alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)

axes[-1].set_xlabel('Date', fontsize=10)

# Add ChatGPT annotation on all panels after rendering
for ax in axes:
    ylim = ax.get_ylim()
    ax.axvline(chatgpt_dt, color='#E74C3C', linewidth=1.2, linestyle='--', alpha=0.8)

fig.suptitle('Figure 4: GitHub Repository Activity by Language Group (2020=100, 3-month MA)\n'
             'All rising languages accelerate post-ChatGPT; Ruby & Haskell decline steadily',
             fontsize=10, y=1.01)

plt.tight_layout()
plt.savefig(f"{OUT}/github_fig4.png", dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("  ✓ github_fig4.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIG 5 — Issue数变化：GitHub协作 vs SO问答消费
# ══════════════════════════════════════════════════════════════════════════════
print("Generating Fig 5...")

# Pick 6 focal languages for clear storytelling
focal_langs = ['python','typescript','rust','javascript','ruby','go']
focal_colors = ['#1F78B4','#FF7F00','#E31A1C','#33A02C','#8B0000','#6A3D9A']

fig, (ax_gh, ax_so) = plt.subplots(1, 2, figsize=(9, 5))

# ── GitHub Issues ──
for lang, color in zip(focal_langs, focal_colors):
    col = f'issues_{lang}'
    raw = gh[col].rolling(3, center=True, min_periods=1).mean()
    norm = normalize_to_2020(raw, gh['date'])
    ax_gh.plot(gh['date'], norm, color=color, linewidth=1.5,
               label=LANG_LABELS[lang], zorder=4)

ax_gh.axvline(chatgpt_dt, color='#E74C3C', linewidth=1.2, linestyle='--', alpha=0.85, zorder=5)
ax_gh.axhline(100, color='gray', linewidth=0.6, linestyle=':', alpha=0.6)
ax_gh.text(chatgpt_dt + pd.Timedelta(days=20), ax_gh.get_ylim()[1]*0.9 if ax_gh.get_ylim()[1] > 100 else 180,
           'ChatGPT', fontsize=7.5, color='#E74C3C', ha='left')
ax_gh.set_ylabel('GitHub Issues (2020=100)', fontsize=10)
ax_gh.set_xlabel('Date', fontsize=10)
ax_gh.set_title('(a) GitHub Issues\n(Project Collaboration)', fontsize=9)
ax_gh.legend(loc='upper left', fontsize=7.5, framealpha=0.85)
ax_gh.yaxis.grid(True, alpha=0.3, linewidth=0.5)
ax_gh.set_axisbelow(True)

# ── SO Questions ──
so_focal = ['python','javascript','typescript','go','ruby','rust']
for lang, color in zip(so_focal, focal_colors):
    col = f'lang_{lang}'
    if col not in so_monthly.columns:
        continue
    so_m = so_monthly.set_index('date')[col].reset_index()
    so_m.columns = ['date', 'val']
    raw = so_m['val'].rolling(3, center=True, min_periods=1).mean()
    norm = normalize_to_2020(raw, so_m['date'])
    ax_so.plot(so_m['date'], norm, color=color, linewidth=1.5,
               label=LANG_LABELS[lang], zorder=4)

ax_so.axvline(chatgpt_dt, color='#E74C3C', linewidth=1.2, linestyle='--', alpha=0.85, zorder=5)
ax_so.axhline(100, color='gray', linewidth=0.6, linestyle=':', alpha=0.6)
ax_so.set_ylabel('SO Questions (2020=100)', fontsize=10)
ax_so.set_xlabel('Date', fontsize=10)
ax_so.set_title('(b) Stack Overflow Questions\n(Knowledge Consumption)', fontsize=9)
ax_so.legend(loc='upper left', fontsize=7.5, framealpha=0.85)
ax_so.yaxis.grid(True, alpha=0.3, linewidth=0.5)
ax_so.set_axisbelow(True)

fig.suptitle('Figure 5: GitHub Issues (Collaboration) vs. Stack Overflow (Consumption)\n'
             'GitHub Issues ↑ = more active projects; SO ↓ = AI replaces Q&A lookup',
             fontsize=9.5, y=1.02)

# Add annotation arrow/box
ax_gh.annotate('GitHub Issues rising\n→ more projects, more\ncollaboration',
               xy=(pd.Timestamp('2023-06-01'), 130), fontsize=7.5,
               color='#1F78B4', ha='center',
               bbox=dict(boxstyle='round', facecolor='#EBF5FB', alpha=0.8, edgecolor='#1F78B4'))
ax_so.annotate('SO Questions falling\n→ AI replaces\nknowledge lookup',
               xy=(pd.Timestamp('2023-06-01'), 70), fontsize=7.5,
               color='#E74C3C', ha='center',
               bbox=dict(boxstyle='round', facecolor='#FDEDEC', alpha=0.8, edgecolor='#E74C3C'))

plt.tight_layout()
plt.savefig(f"{OUT}/github_fig5.png", dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("  ✓ github_fig5.png")

print("\n✅ All 5 figures saved to:", OUT)
