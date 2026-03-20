#!/usr/bin/env python3
"""
Generate 7 high-quality Nature/Science style figures for SO research.
All overlap issues resolved. 300 DPI. White background.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib import rcParams
import warnings
warnings.filterwarnings('ignore')

try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False
    print("adjustText not available, using manual offsets")

# ─── Global Style ────────────────────────────────────────────────────────────
rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 9,
    'axes.titlesize': 11,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'figure.dpi': 100,
    'savefig.dpi': 300,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'legend.fontsize': 8,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '0.8',
})

# ─── Constants ────────────────────────────────────────────────────────────────
AI_REP = {
    'python': 0.92, 'javascript': 0.88, 'typescript': 0.85,
    'java': 0.81, 'csharp': 0.79, 'go': 0.72,
    'ruby': 0.65, 'cpp': 0.63, 'c': 0.60, 'r': 0.58,
    'rust': 0.35, 'haskell': 0.25, 'fortran': 0.18, 'assembly': 0.10
}

LANG_DISPLAY = {
    'python': 'Python', 'javascript': 'JavaScript', 'typescript': 'TypeScript',
    'java': 'Java', 'csharp': 'C#', 'go': 'Go', 'ruby': 'Ruby',
    'cpp': 'C++', 'c': 'C', 'r': 'R', 'rust': 'Rust',
    'haskell': 'Haskell', 'fortran': 'Fortran', 'assembly': 'Assembly'
}

AI_EVENTS = [
    ("2021-10-01", "Copilot Beta",       "GitHub",    "#95A5A6"),
    ("2022-06-21", "Copilot GA",          "GitHub",    "#7F8C8D"),
    ("2022-11-30", "ChatGPT",             "OpenAI",    "#E74C3C"),
    ("2023-03-14", "GPT-4 + Claude 1",   "Multi",     "#C0392B"),
    ("2023-07-18", "Claude 2 + Llama 2", "Multi",     "#8E44AD"),
    ("2023-08-24", "Code Llama",          "Meta",      "#6C3483"),
    ("2024-03-04", "Claude 3",            "Anthropic", "#1A5276"),
    ("2024-05-13", "GPT-4o",              "OpenAI",    "#D35400"),
    ("2024-06-20", "Claude 3.5 Sonnet",  "Anthropic", "#154360"),
    ("2024-10-01", "Cursor 1M",           "Other",     "#1E8449"),
    ("2025-02-19", "Claude 3.7",          "Anthropic", "#0B5345"),
]

# Consistent language color palette (ColorBrewer Set1 + extra)
LANG_COLORS = {
    'python': '#E41A1C',
    'javascript': '#FF7F00',
    'typescript': '#FFCC00',
    'java': '#4DAF4A',
    'csharp': '#984EA3',
    'go': '#377EB8',
    'ruby': '#A65628',
    'cpp': '#F781BF',
    'c': '#999999',
    'r': '#66C2A5',
    'rust': '#FC8D62',
    'haskell': '#8DA0CB',
    'fortran': '#E78AC3',
    'assembly': '#A6D854',
}

OUTDIR = '/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/results'

# ─── Load Data ────────────────────────────────────────────────────────────────
def load_data():
    with open(f'{OUTDIR}/api_cache_weekly.json') as f:
        raw = json.load(f)
    
    rows = []
    for k, v in raw.items():
        rows.append(v)
    
    df = pd.DataFrame(rows)
    df['week_dt'] = pd.to_datetime(df['week_dt'])
    df = df.sort_values('week_dt').reset_index(drop=True)
    
    # Fill zeros (missing data) with NaN for interpolation
    lang_cols = [f'lang_{l}' for l in AI_REP.keys()]
    for col in lang_cols:
        if col in df.columns:
            df[col] = df[col].replace(0, np.nan)
    
    return df

def ma(series, window=8):
    return series.rolling(window, center=True, min_periods=1).mean()

def to_dt(s):
    return pd.Timestamp(s)

# ─── Fig 1: SO Total Volume Trend ─────────────────────────────────────────────
def fig1(df):
    fig, ax = plt.subplots(figsize=(9, 4))
    
    # Era backgrounds
    eras = [
        ('2018-01-01', '2020-03-01', '#AED6F1', 'Pre-COVID'),
        ('2020-03-01', '2021-10-01', '#A9DFBF', 'COVID Era'),
        ('2021-10-01', '2022-11-30', '#F9E79F', 'Early AI'),
        ('2022-11-30', '2026-12-31', '#F5CBA7', 'GenAI Era'),
    ]
    for s, e, c, label in eras:
        ax.axvspan(to_dt(s), to_dt(e), alpha=0.08, color=c, zorder=0)
    
    dates = df['week_dt']
    total = df['total_questions'] / 1000  # k units
    total_ma = ma(total)
    
    # Raw data
    ax.plot(dates, total, color='#999999', lw=0.4, alpha=0.3, zorder=1)
    # MA line
    ax.fill_between(dates, total_ma, alpha=0.1, color='#2C3E50', zorder=2)
    ax.plot(dates, total_ma, color='#2C3E50', lw=2, zorder=3, label='8-week MA')
    
    # ChatGPT before/after mean lines
    chatgpt_date = to_dt("2022-11-30")
    pre_mask = (dates < chatgpt_date) & (dates >= to_dt('2021-01-01'))
    post_mask = (dates >= chatgpt_date) & (dates <= to_dt('2024-06-30'))
    
    pre_mean = total_ma[pre_mask].mean()
    post_mean = total_ma[post_mask].mean()
    drop_pct = (post_mean - pre_mean) / pre_mean * 100
    
    ax.axhline(pre_mean, xmin=0.3, xmax=0.52, color='#2471A3', lw=1.2, ls='--', zorder=4, alpha=0.8)
    ax.axhline(post_mean, xmin=0.52, xmax=0.85, color='#E74C3C', lw=1.2, ls='--', zorder=4, alpha=0.8)
    
    # Annotate drop
    mid_post_date = to_dt('2023-09-01')
    ax.annotate(f'{drop_pct:.1f}% decline', 
                xy=(mid_post_date, (pre_mean + post_mean) / 2),
                xytext=(mid_post_date, post_mean - 3),
                fontsize=7.5, color='#E74C3C',
                ha='center',
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=0.8))
    
    # AI event vertical lines (no text labels, use footnote numbers)
    footnote_syms = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪']
    for i, (dt_str, name, org, color) in enumerate(AI_EVENTS):
        vline_date = to_dt(dt_str)
        ax.axvline(vline_date, color=color, lw=0.8, alpha=0.7, ls=':', zorder=3)
        # Place number at top of plot
        ypos = ax.get_ylim()[1] if ax.get_ylim()[1] > 1 else total_ma.max() * 0.97
        ax.text(vline_date, total_ma.max() * 0.97, footnote_syms[i],
                fontsize=6, ha='center', va='top', color=color, fontweight='bold')
    
    ax.set_xlim(to_dt('2018-01-01'), to_dt('2026-03-31'))
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel('Weekly Questions (k)', fontsize=9)
    ax.set_title('Stack Overflow Weekly Question Volume (2018–2026)', fontsize=11, pad=8)
    ax.tick_params(labelsize=8)
    
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    ax.legend(loc='lower left', fontsize=8)
    
    # Era labels (subtle, at bottom of era band)
    era_label_y = total_ma.min() * 0.97
    era_mids = [
        (to_dt('2019-01-01'), 'Pre-COVID'),
        (to_dt('2020-09-01'), 'COVID'),
        (to_dt('2021-11-15'), 'Early AI'),
        (to_dt('2023-09-01'), 'GenAI Era'),
    ]
    for xpos, label in era_mids:
        ax.text(xpos, era_label_y, label, fontsize=6.5, color='#666666',
                ha='center', va='bottom', style='italic', alpha=0.7)
    
    # Footnote box below figure
    footnote_lines = []
    for i, (dt_str, name, org, color) in enumerate(AI_EVENTS):
        footnote_lines.append(f'{footnote_syms[i]} {dt_str[:7]} {name} ({org})')
    
    # Two columns
    n = len(footnote_lines)
    col1 = '  '.join(footnote_lines[:6])
    col2 = '  '.join(footnote_lines[6:])
    footnote_text = col1 + '\n' + col2
    
    fig.text(0.01, -0.06, footnote_text, fontsize=6.5, color='#555555',
             va='top', ha='left', wrap=True,
             transform=ax.transAxes)
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig1.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Fig 2: Language Decline Bar Chart ────────────────────────────────────────
def fig2(df):
    # Compute decline: pre-ChatGPT (2021-2022) vs post (2023-2024)
    chatgpt_date = to_dt("2022-11-30")
    pre = df[(df['week_dt'] >= '2021-01-01') & (df['week_dt'] < chatgpt_date)]
    post = df[(df['week_dt'] >= '2023-01-01') & (df['week_dt'] <= '2024-12-31')]
    
    langs = list(AI_REP.keys())
    declines = {}
    for lang in langs:
        col = f'lang_{lang}'
        if col in df.columns:
            pre_mean = pre[col].mean()
            post_mean = post[col].mean()
            if pre_mean and pre_mean > 0:
                declines[lang] = (post_mean - pre_mean) / pre_mean * 100
            else:
                declines[lang] = 0
    
    # Sort by ARI (low to high) for display
    langs_sorted = sorted(langs, key=lambda l: AI_REP[l])
    
    # 4-group colors (ColorBrewer RdYlBu_r)
    def get_group_color(ari):
        if ari > 0.80: return '#D73027'    # high: red
        elif ari > 0.60: return '#FC8D59'   # med-high: orange  
        elif ari > 0.40: return '#91BFDB'   # med-low: light blue
        else: return '#4575B4'              # low: blue
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    y_pos = np.arange(len(langs_sorted))
    bar_vals = [declines.get(l, 0) for l in langs_sorted]
    bar_colors = [get_group_color(AI_REP[l]) for l in langs_sorted]
    
    bars = ax.barh(y_pos, bar_vals, color=bar_colors, height=0.65, zorder=2)
    
    # Y labels: "Language (ARI)"
    y_labels = [f'{LANG_DISPLAY[l]} ({AI_REP[l]:.2f})' for l in langs_sorted]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=8)
    
    # Value labels OUTSIDE bar (right of bar end)
    for i, (bar, val) in enumerate(zip(bars, bar_vals)):
        xpos = val - 1.0 if val < 0 else val + 0.5
        ha = 'right' if val < 0 else 'left'
        ax.text(xpos, bar.get_y() + bar.get_height() / 2,
                f'{val:.1f}%', va='center', ha=ha, fontsize=7.5, color='#333333')
    
    ax.axvline(0, color='black', lw=0.8)
    ax.set_xlabel('Change in Weekly Questions (%)', fontsize=9)
    ax.set_title('Programming Language Question Volume Change\n(Pre-ChatGPT 2021–2022 vs. Post 2023–2024)',
                 fontsize=11, pad=8)
    ax.tick_params(labelsize=8)
    ax.set_xlim(min(bar_vals) * 1.25, max(max(bar_vals) * 1.2, 5))
    
    # Grid lines
    ax.grid(axis='x', alpha=0.3, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    
    # Legend
    legend_patches = [
        mpatches.Patch(color='#D73027', label='High AI replaceability (ARI > 0.80)'),
        mpatches.Patch(color='#FC8D59', label='Med-high (0.60–0.80)'),
        mpatches.Patch(color='#91BFDB', label='Med-low (0.40–0.60)'),
        mpatches.Patch(color='#4575B4', label='Low ARI (< 0.40)'),
    ]
    ax.legend(handles=legend_patches, loc='lower right', fontsize=7.5, 
              framealpha=0.9, edgecolor='0.8')
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig2.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Fig 3: H2 Scatter ─────────────────────────────────────────────────────────
def fig3(df):
    from scipy import stats
    
    # Compute decline per language
    chatgpt_date = to_dt("2022-11-30")
    pre = df[(df['week_dt'] >= '2021-01-01') & (df['week_dt'] < chatgpt_date)]
    post = df[(df['week_dt'] >= '2023-01-01') & (df['week_dt'] <= '2024-12-31')]
    
    langs = list(AI_REP.keys())
    x_vals = []
    y_vals = []
    valid_langs = []
    
    for lang in langs:
        col = f'lang_{lang}'
        if col in df.columns:
            pre_mean = pre[col].mean()
            post_mean = post[col].mean()
            if pre_mean and pre_mean > 5:
                pct = (post_mean - pre_mean) / pre_mean * 100
                x_vals.append(AI_REP[lang])
                y_vals.append(pct)
                valid_langs.append(lang)
    
    x = np.array(x_vals)
    y = np.array(y_vals)
    
    fig, ax = plt.subplots(figsize=(6, 5.5))
    
    # Background vertical bands
    band_colors = [
        (0.0, 0.40, '#4575B4', 'Low'),
        (0.40, 0.60, '#91BFDB', 'Med-low'),
        (0.60, 0.80, '#FC8D59', 'Med-high'),
        (0.80, 1.00, '#D73027', 'High'),
    ]
    ymin, ymax = min(y) * 1.2, max(y) * 1.1
    for x0, x1, c, label in band_colors:
        ax.axvspan(x0, x1, alpha=0.06, color=c, zorder=0)
    
    # Scatter
    for i, (lang, xi, yi) in enumerate(zip(valid_langs, x, y)):
        ax.scatter(xi, yi, color=LANG_COLORS[lang], s=60, zorder=4,
                   edgecolors='white', linewidths=0.5)
    
    # Trend line + CI
    slope, intercept, r, p, se = stats.linregress(x, y)
    x_line = np.linspace(0.05, 0.98, 200)
    y_line = slope * x_line + intercept
    
    # 95% CI
    n = len(x)
    x_mean = x.mean()
    s_err = np.sqrt(np.sum((y - (slope * x + intercept))**2) / (n - 2))
    ci = 1.96 * s_err * np.sqrt(1/n + (x_line - x_mean)**2 / np.sum((x - x_mean)**2))
    
    ax.plot(x_line, y_line, color='#2C3E50', lw=1.5, zorder=3)
    ax.fill_between(x_line, y_line - ci, y_line + ci, alpha=0.15, color='#2C3E50', zorder=2)
    
    # Language labels - use adjustText or manual offsets
    texts = []
    for lang, xi, yi in zip(valid_langs, x, y):
        t = ax.text(xi, yi, LANG_DISPLAY[lang], fontsize=7.5, ha='center', va='bottom',
                    color='#333333')
        texts.append(t)
    
    if HAS_ADJUST_TEXT:
        adjust_text(texts, ax=ax,
                    arrowprops=dict(arrowstyle='-', color='#999999', lw=0.5),
                    expand_points=(1.5, 1.8),
                    force_text=(0.5, 0.8),
                    only_move={'text': 'xy', 'points': 'y'})
    else:
        # Manual precise offsets per language
        offsets = {
            'python': (0.02, -2.5), 'javascript': (-0.04, 1.5), 
            'typescript': (0.03, 1.5), 'java': (0.02, 1.5),
            'csharp': (-0.04, -2.5), 'go': (0.02, 1.5),
            'ruby': (-0.04, 1.5), 'cpp': (0.03, -2.5),
            'c': (0.02, 1.5), 'r': (0.02, 1.5),
            'rust': (0.0, 1.5), 'haskell': (-0.01, -2.5),
            'fortran': (0.01, 1.5), 'assembly': (0.0, 1.5),
        }
        for t, lang in zip(texts, valid_langs):
            if lang in offsets:
                dx, dy = offsets[lang]
                t.set_position((t.get_position()[0] + dx, t.get_position()[1] + dy))
    
    # Stats box
    r2 = r**2
    p_str = f'{p:.3f}' if p >= 0.001 else f'{p:.2e}'
    stats_text = f'$R^2$ = {r2:.3f}\n$n$ = {n}\n$p$ = {p_str}'
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes,
            fontsize=8, va='top', ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='0.8', alpha=0.9))
    
    ax.set_xlabel('AI Replaceability Index (ARI)', fontsize=9)
    ax.set_ylabel('Change in Weekly Questions (%)', fontsize=9)
    ax.set_title('H2: Higher AI Replaceability → Greater Question Volume Decline', fontsize=11, pad=8)
    ax.axhline(0, color='0.7', lw=0.8, ls='--', zorder=1)
    ax.tick_params(labelsize=8)
    ax.set_xlim(-0.02, 1.02)
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig3.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Fig 4: Event Study ────────────────────────────────────────────────────────
def fig4(df):
    import matplotlib.dates as mdates
    
    total_ma = ma(df['total_questions'] / 1000)
    dates = df['week_dt']
    
    # Compute residuals for anomaly detection
    trend = total_ma.rolling(52, min_periods=4, center=True).mean()
    residuals = total_ma - trend
    
    chatgpt_date = to_dt("2022-11-30")
    
    # CAR: cumulative abnormal returns from ChatGPT
    post_mask = dates >= chatgpt_date
    car = residuals[post_mask].cumsum()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                                    gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.08})
    
    # ── Upper panel: weekly anomalies (scatter) ──
    pre_mask = dates < chatgpt_date
    ax1.scatter(dates[pre_mask], residuals[pre_mask], 
                color='#AAAAAA', s=8, alpha=0.6, zorder=2, label='Pre-ChatGPT')
    ax1.scatter(dates[post_mask], residuals[post_mask], 
                color='#E74C3C', s=8, alpha=0.6, zorder=2, label='Post-ChatGPT')
    ax1.axhline(0, color='0.5', lw=0.8, ls='-')
    ax1.set_ylabel('Weekly Abnormal Volume (k)', fontsize=9)
    ax1.set_title('(a) Weekly Abnormal Question Volume Around AI Events', fontsize=11, pad=6)
    ax1.legend(loc='upper left', fontsize=8, markerscale=1.5)
    ax1.tick_params(labelsize=8)
    
    # ── Lower panel: CAR ──
    car_dates = dates[post_mask]
    car_vals = car.values
    ax2.fill_between(car_dates, 0, car_vals, alpha=0.15, color='#2C3E50')
    ax2.plot(car_dates, car_vals, color='#2C3E50', lw=1.5)
    ax2.axhline(0, color='0.5', lw=0.8, ls='-')
    ax2.set_ylabel('Cumulative Abnormal Volume (k)', fontsize=9)
    ax2.set_title('(b) Cumulative Abnormal Return (CAR) — Post-ChatGPT', fontsize=11, pad=6)
    ax2.tick_params(labelsize=8)
    
    # AI event lines on both panels with alternating up/down labels
    footnote_syms = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪']
    
    for i, (dt_str, name, org, color) in enumerate(AI_EVENTS):
        vline_date = to_dt(dt_str)
        for ax in [ax1, ax2]:
            ax.axvline(vline_date, color=color, lw=0.8, alpha=0.7, ls=':', zorder=3)
        
        # Alternating up/down on upper panel
        yrange1 = ax1.get_ylim()
        if abs(yrange1[1]) < 1: 
            yr = residuals.abs().max()
            yrange1 = (-yr*1.2, yr*1.2)
            ax1.set_ylim(yrange1)
        
        y_label = yrange1[1] * (0.92 if i % 2 == 0 else 0.78)
        ax1.text(vline_date, y_label, footnote_syms[i],
                 fontsize=6.5, ha='center', color=color, fontweight='bold', zorder=5,
                 bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Footnotes
    footnote_lines = [f'{footnote_syms[i]} {dt_str[:7]} {name}' 
                      for i, (dt_str, name, org, color) in enumerate(AI_EVENTS)]
    col1 = '  '.join(footnote_lines[:6])
    col2 = '  '.join(footnote_lines[6:])
    
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.set_xlabel('Year', fontsize=9)
    ax2.set_xlim(to_dt('2021-01-01'), to_dt('2026-03-31'))
    
    # Vendor legend at bottom
    vendors = {}
    for dt_str, name, org, color in AI_EVENTS:
        if org not in vendors:
            vendors[org] = color
    vendor_patches = [mpatches.Patch(color=c, label=org) for org, c in vendors.items()]
    fig.legend(handles=vendor_patches, loc='lower center', ncol=5, fontsize=7.5,
               bbox_to_anchor=(0.5, -0.02), framealpha=0.9, edgecolor='0.8',
               title='Organization', title_fontsize=8)
    
    fig.text(0.01, -0.06, col1 + '\n' + col2, fontsize=6.5, color='#555555',
             va='top', ha='left', transform=ax2.transAxes)
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig4.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Fig 5: Language Group Time Series ────────────────────────────────────────
def fig5(df):
    import matplotlib.dates as mdates
    
    # 3 groups (as specified)
    groups = {
        'High ARI (>0.80)\nPython+JS+TS+Java+C#': 
            ['python', 'javascript', 'typescript', 'java', 'csharp'],
        'Med-high ARI (0.60–0.80)\nGo+Ruby+C+++C+R':
            ['go', 'ruby', 'cpp', 'c', 'r'],
        'Low ARI (<0.40)\nRust+Haskell+Fortran+Assembly':
            ['rust', 'haskell', 'fortran', 'assembly'],
    }
    group_colors = ['#D73027', '#FC8D59', '#4575B4']
    group_labels = list(groups.keys())
    
    fig, ax = plt.subplots(figsize=(9, 5))
    
    dates = df['week_dt']
    
    # Normalize to 2018 average
    ref_mask = df['week_dt'].dt.year == 2018
    
    lines = []
    for (label, langs), color in zip(groups.items(), group_colors):
        cols = [f'lang_{l}' for l in langs if f'lang_{l}' in df.columns]
        group_sum = df[cols].sum(axis=1).replace(0, np.nan)
        group_sum_ma = ma(group_sum)
        
        ref_val = group_sum_ma[ref_mask].mean()
        if ref_val and ref_val > 0:
            normalized = group_sum_ma / ref_val * 100
        else:
            normalized = group_sum_ma
        
        ax.fill_between(dates, normalized, 100, alpha=0.07, color=color)
        line, = ax.plot(dates, normalized, color=color, lw=2, label=label)
        lines.append(line)
    
    ax.axhline(100, color='0.6', lw=0.8, ls='--', alpha=0.7)
    ax.axvline(to_dt('2022-11-30'), color='#E74C3C', lw=1.2, ls='--', alpha=0.8)
    ax.text(to_dt('2022-11-30'), ax.get_ylim()[1] if ax.get_ylim()[1] > 1 else 105,
            'ChatGPT', fontsize=7.5, color='#E74C3C', ha='left', va='top',
            rotation=90, style='italic')
    
    ax.set_xlim(to_dt('2018-01-01'), to_dt('2026-03-31'))
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel('Normalized Volume (2018 = 100)', fontsize=9)
    ax.set_title('Programming Language Groups: Normalized Question Volume by AI Replaceability',
                 fontsize=11, pad=8)
    ax.tick_params(labelsize=8)
    
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y', alpha=0.3, lw=0.5)
    ax.set_axisbelow(True)
    
    ax.legend(loc='lower left', fontsize=8, framealpha=0.9)
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig5.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Fig 6: Annual Heatmap ─────────────────────────────────────────────────────
def fig6(df):
    import seaborn as sns
    
    langs_by_ari = sorted(AI_REP.keys(), key=lambda l: AI_REP[l], reverse=True)
    
    df['year'] = df['week_dt'].dt.year
    years = sorted(df['year'].unique())
    years = [y for y in years if 2018 <= y <= 2025]
    
    # Annual totals per language
    heatmap_data = {}
    for lang in langs_by_ari:
        col = f'lang_{lang}'
        if col in df.columns:
            annual = df.groupby('year')[col].mean()
            heatmap_data[lang] = annual
    
    heat_df = pd.DataFrame(heatmap_data, index=years).T
    heat_df = heat_df[years]
    
    # Normalize: each language to 2018 = 100
    ref_year = 2018
    for lang in heat_df.index:
        ref_val = heat_df.loc[lang, ref_year]
        if ref_val and ref_val > 0:
            heat_df.loc[lang] = heat_df.loc[lang] / ref_val * 100
        else:
            heat_df.loc[lang] = np.nan
    
    # Rename for display
    heat_df.index = [LANG_DISPLAY[l] for l in heat_df.index]
    heat_df.columns = [str(y) for y in heat_df.columns]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Diverging colormap centered at 100
    vmin = heat_df.values[~np.isnan(heat_df.values)].min()
    vmax = heat_df.values[~np.isnan(heat_df.values)].max()
    center = 100
    
    sns.heatmap(heat_df, ax=ax, cmap='RdBu_r', center=center,
                vmin=min(vmin, 80), vmax=max(vmax, 120),
                annot=True, fmt='.0f', annot_kws={'size': 7.5},
                linewidths=0.3, linecolor='0.9',
                cbar_kws={'label': 'Normalized Volume (2018=100)', 'shrink': 0.8})
    
    ax.set_title('Annual Programming Language Question Volume\n(Normalized to 2018 = 100)',
                 fontsize=11, pad=8)
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel('Language (sorted by ARI ↓)', fontsize=9)
    ax.tick_params(labelsize=8)
    
    # Y-axis: add ARI values
    y_labels = [f'{l} ({AI_REP[[k for k,v in LANG_DISPLAY.items() if v==l][0]]:.2f})'
                for l in heat_df.index]
    ax.set_yticklabels(y_labels, rotation=0, fontsize=7.5)
    ax.set_xticklabels(heat_df.columns, rotation=0, fontsize=8)
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig6.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Fig 7: Normalized Index Trends ────────────────────────────────────────────
def fig7(df):
    import matplotlib.dates as mdates
    import matplotlib.cm as cm
    
    langs_by_ari = sorted(AI_REP.keys(), key=lambda l: AI_REP[l])
    
    # Normalize to 2020 Q1
    q1_2020_mask = (df['week_dt'] >= '2020-01-01') & (df['week_dt'] < '2020-04-01')
    
    fig, ax = plt.subplots(figsize=(9, 5))
    
    dates = df['week_dt']
    
    # Highlight languages
    highlight = {'python', 'javascript', 'assembly', 'rust', 'typescript'}
    
    # Color gradient: warm for high ARI, cool for low ARI
    n = len(langs_by_ari)
    
    for i, lang in enumerate(langs_by_ari):
        ari = AI_REP[lang]
        col = f'lang_{lang}'
        if col not in df.columns:
            continue
        
        series = df[col].replace(0, np.nan)
        series_ma = ma(series)
        
        ref_val = series_ma[q1_2020_mask].mean()
        if not ref_val or ref_val == 0:
            continue
        normalized = series_ma / ref_val * 100
        
        # Color: warm (high ARI) → cool (low ARI)
        if ari >= 0.80:
            color = plt.cm.YlOrRd(0.6 + ari * 0.4)
        elif ari >= 0.60:
            color = plt.cm.YlOrRd(0.3 + ari * 0.3)
        else:
            color = plt.cm.YlGnBu(0.3 + (1 - ari) * 0.55)
        
        alpha = 0.9 if lang in highlight else 0.35
        lw = 1.8 if lang in highlight else 0.8
        zorder = 5 if lang in highlight else 2
        
        line, = ax.plot(dates, normalized, color=color, lw=lw, alpha=alpha, zorder=zorder)
        
        # Label at end for highlighted languages
        if lang in highlight:
            last_valid = normalized.dropna()
            if len(last_valid) > 0:
                last_date = dates.iloc[last_valid.index[-1]]
                last_val = last_valid.iloc[-1]
                ax.text(last_date + pd.Timedelta(weeks=2), last_val,
                        LANG_DISPLAY[lang], fontsize=7.5, va='center',
                        color=color, fontweight='bold')
    
    ax.axhline(100, color='0.6', lw=0.8, ls='--', alpha=0.7)
    ax.axvline(to_dt('2022-11-30'), color='#E74C3C', lw=1.2, ls='--', alpha=0.8)
    ax.text(to_dt('2022-11-30'), ax.get_ylim()[0] if ax.get_ylim()[0] < 100 else 95,
            'ChatGPT', fontsize=7.5, color='#E74C3C', ha='right', va='bottom',
            rotation=90, style='italic')
    
    ax.set_xlim(to_dt('2018-01-01'), to_dt('2026-06-30'))
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel('Normalized Volume (2020-Q1 = 100)', fontsize=9)
    ax.set_title('Programming Language Question Trends\n(Normalized to 2020 Q1, colored by AI Replaceability)',
                 fontsize=11, pad=8)
    ax.tick_params(labelsize=8)
    
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y', alpha=0.3, lw=0.5)
    ax.set_axisbelow(True)
    
    # Colorbar-style legend
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize
    
    # Simple legend
    warm_patch = mpatches.Patch(color=plt.cm.YlOrRd(0.85), label='High ARI (warm colors)')
    cool_patch = mpatches.Patch(color=plt.cm.YlGnBu(0.8), label='Low ARI (cool colors)')
    hi_line = Line2D([0], [0], color='gray', lw=1.8, alpha=0.9, label='Highlighted languages')
    lo_line = Line2D([0], [0], color='gray', lw=0.8, alpha=0.35, label='Other languages')
    ax.legend(handles=[warm_patch, cool_patch, hi_line, lo_line],
              loc='upper right', fontsize=7.5, framealpha=0.9)
    
    plt.tight_layout()
    path = f'{OUTDIR}/final_fig7.png'
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved {path}')
    import os
    print(f'  Size: {os.path.getsize(path)/1024:.1f} KB')


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Loading data...')
    df = load_data()
    print(f'Data loaded: {len(df)} weeks, {df.week_dt.min()} to {df.week_dt.max()}')
    
    print('\nGenerating figures...')
    print('─' * 50)
    
    print('Fig 1: SO Total Volume Trend')
    fig1(df)
    
    print('Fig 2: Language Decline Bar Chart')
    fig2(df)
    
    print('Fig 3: H2 Scatter')
    fig3(df)
    
    print('Fig 4: Event Study')
    fig4(df)
    
    print('Fig 5: Language Group Time Series')
    fig5(df)
    
    print('Fig 6: Annual Heatmap')
    fig6(df)
    
    print('Fig 7: Normalized Index Trends')
    fig7(df)
    
    print('\n' + '─' * 50)
    print('All figures generated successfully!')
