#!/usr/bin/env python3
"""
analysis/01_descriptive.py
===========================
描述统计分析与可视化
- SO整体活跃度趋势图（2018-2026，按周）
- 标注所有AI事件节点
- 与对照社区（Math SE / Super User）对比图
- 各编程语言问题量趋势（Top 20语言）
- 用户构成变化（新手/资深比例）

输出：results/figures/descriptive/ 目录下6-8张出版级图表

用法:
    python analysis/01_descriptive.py --features data/features/ --output results/figures/descriptive/
"""

import argparse
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

# 设置matplotlib中文支持（需要SimHei或Noto Sans CJK字体）
matplotlib.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

# ============================================================
# 全局图表风格设置（出版级别）
# ============================================================
PUBLICATION_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "lines.linewidth": 1.5,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
}

# 调色板（出版友好，对色盲友好）
COLORS = {
    "so": "#F48024",          # Stack Overflow橙色
    "mathse": "#2E86AB",      # Math SE蓝色
    "superuser": "#3DAA35",   # Super User绿色
    "serverfault": "#C0392B", # Server Fault红色
    "ai_event": "#8B4513",    # AI事件标注棕色
    "trend": "#2C3E50",       # 趋势线深色
    "treatment": "#E74C3C",   # 处理组红色
    "control": "#3498DB",     # 对照组蓝色
}

# AI事件代际颜色
GEN_COLORS = {1: "#4C72B0", 2: "#DD8452", 3: "#55A868", 4: "#C44E52", 5: "#8172B3"}


def load_data(features_dir: Path) -> dict:
    """加载分析所需的特征数据"""
    data = {}
    
    print("加载特征数据...")
    
    # 周级别统计
    weekly_path = features_dir / "weekly_stats.parquet"
    if weekly_path.exists():
        data["weekly"] = pd.read_parquet(weekly_path)
        data["weekly"]["week_start"] = pd.to_datetime(data["weekly"]["week_start"])
        print(f"  ✓ weekly_stats: {len(data['weekly']):,} 行")
    else:
        print(f"  ⚠ 未找到 {weekly_path}")
        data["weekly"] = None
    
    # 语言周统计
    lang_path = features_dir / "language_weekly_stats.parquet"
    if lang_path.exists():
        data["lang_weekly"] = pd.read_parquet(lang_path)
        data["lang_weekly"]["week_start"] = pd.to_datetime(data["lang_weekly"]["week_start"])
        print(f"  ✓ language_weekly_stats: {len(data['lang_weekly']):,} 行")
    else:
        data["lang_weekly"] = None
    
    # AI时间线
    timeline_path = features_dir / "ai_timeline.csv"
    if timeline_path.exists():
        data["ai_timeline"] = pd.read_csv(timeline_path)
        data["ai_timeline"]["week_start"] = pd.to_datetime(data["ai_timeline"]["week_start"])
        print(f"  ✓ ai_timeline: {len(data['ai_timeline']):,} 行")
    else:
        data["ai_timeline"] = None
    
    # AI事件节点
    events_path = features_dir / "ai_events.csv"
    if events_path.exists():
        data["ai_events"] = pd.read_csv(events_path)
        data["ai_events"]["date"] = pd.to_datetime(data["ai_events"]["date"])
        print(f"  ✓ ai_events: {len(data['ai_events'])} 个事件")
    else:
        # 使用内置事件数据
        from pipeline.ai_timeline import build_events_dataframe
        data["ai_events"] = build_events_dataframe()
    
    # 用户队列
    cohort_path = features_dir / "user_cohorts.parquet"
    if cohort_path.exists():
        data["user_cohorts"] = pd.read_parquet(cohort_path)
        print(f"  ✓ user_cohorts: {len(data['user_cohorts']):,} 行")
    else:
        data["user_cohorts"] = None
    
    return data


def add_ai_event_annotations(ax, events_df: pd.DataFrame, ymin_frac=0.0, ymax_frac=1.0, 
                               fontsize=8, show_labels=True):
    """
    在图表上添加AI事件垂直线标注
    按generation用不同颜色区分
    """
    ylim = ax.get_ylim()
    yrange = ylim[1] - ylim[0]
    
    # 交替显示标签位置（避免重叠）
    label_y_positions = [ylim[0] + yrange * 0.75, ylim[0] + yrange * 0.65]
    
    for i, (_, event) in enumerate(events_df.iterrows()):
        event_date = pd.Timestamp(event["date"])
        gen = event.get("generation", 2)
        color = GEN_COLORS.get(gen, "#666666")
        
        ax.axvline(
            x=event_date,
            color=color,
            linestyle="--",
            linewidth=0.8,
            alpha=0.7
        )
        
        if show_labels:
            label = event.get("name_short", event.get("name", ""))
            y_pos = label_y_positions[i % len(label_y_positions)]
            ax.text(
                event_date,
                y_pos,
                label,
                rotation=90,
                fontsize=fontsize,
                color=color,
                verticalalignment="bottom",
                horizontalalignment="right",
                alpha=0.8
            )


def fig01_so_weekly_trend(data: dict, output_dir: Path):
    """
    图1：Stack Overflow每周问题提交量趋势（2018-2026）
    标注所有AI事件节点
    """
    print("\n绘制 图1: SO周趋势...")
    
    if data["weekly"] is None:
        print("  ⚠ 数据不足，跳过")
        return
    
    df = data["weekly"].copy()
    df_so = df[df["community"] == "so"].sort_values("week_start")
    
    # 平滑：4周移动平均
    df_so["q_count_ma4"] = df_so["question_count"].rolling(4, center=True).mean()
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
        
        ax1 = axes[0]
        ax2 = axes[1]
        
        # 原始数据（浅色）
        ax1.fill_between(
            df_so["week_start"], df_so["question_count"],
            alpha=0.2, color=COLORS["so"], label="Weekly questions (raw)"
        )
        # 4周移动平均
        ax1.plot(
            df_so["week_start"], df_so["q_count_ma4"],
            color=COLORS["so"], linewidth=2, label="4-week moving average"
        )
        
        # 标注AI事件
        if data["ai_events"] is not None:
            add_ai_event_annotations(ax1, data["ai_events"], fontsize=7)
        
        ax1.set_title(
            "Stack Overflow Weekly Question Volume (2018–2026)",
            fontweight="bold", pad=12
        )
        ax1.set_ylabel("Questions per Week", fontsize=12)
        ax1.legend(loc="upper left", framealpha=0.9)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        
        # 添加重要时间轴阴影区域
        chatgpt_date = pd.Timestamp("2022-11-30")
        ax1.axvspan(
            pd.Timestamp("2020-03-01"), pd.Timestamp("2021-06-01"),
            alpha=0.05, color="gray", label="COVID period"
        )
        ax1.axvspan(
            chatgpt_date, pd.Timestamp("2023-03-14"),
            alpha=0.08, color="orange", label="ChatGPT shock"
        )
        
        # 下图：AI能力指数
        if data["ai_timeline"] is not None:
            df_timeline = data["ai_timeline"].copy()
            df_timeline["week_start"] = pd.to_datetime(df_timeline["week_start"])
            ax2.fill_between(
                df_timeline["week_start"],
                df_timeline["ai_capability_index"],
                color="#8172B3", alpha=0.6, label="AI Capability Index"
            )
            ax2.set_ylabel("AI Cap. Index", fontsize=10)
            ax2.set_ylim(0, 1.1)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax2.xaxis.set_major_locator(mdates.YearLocator())
            ax2.legend(loc="upper left", fontsize=9)
        
        ax2.set_xlabel("Year", fontsize=12)
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"fig01_so_weekly_trend.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ 保存: {out_path}")
        
        plt.close()


def fig02_community_comparison(data: dict, output_dir: Path):
    """
    图2：四社区问题量对比（归一化）
    验证H4：SO冲击大于其他社区
    """
    print("\n绘制 图2: 社区对比...")
    
    if data["weekly"] is None:
        print("  ⚠ 数据不足，跳过")
        return
    
    df = data["weekly"].copy()
    
    # 计算每个社区的归一化问题量（相对于2021年均值）
    communities = [
        ("so", "Stack Overflow", COLORS["so"]),
        ("mathse", "Math Stack Exchange", COLORS["mathse"]),
        ("superuser", "Super User", COLORS["superuser"]),
        ("serverfault", "Server Fault", COLORS["serverfault"]),
    ]
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for comm_id, comm_name, color in communities:
            df_comm = df[df["community"] == comm_id].sort_values("week_start").copy()
            if df_comm.empty:
                continue
            
            # 归一化：2021年全年均值为基准
            baseline_mask = (
                (df_comm["week_start"] >= "2021-01-01") &
                (df_comm["week_start"] < "2022-01-01")
            )
            baseline = df_comm.loc[baseline_mask, "question_count"].mean()
            if baseline > 0:
                df_comm["q_normalized"] = df_comm["question_count"] / baseline
            else:
                continue
            
            # 8周移动平均
            df_comm["q_norm_ma8"] = df_comm["q_normalized"].rolling(8, center=True).mean()
            
            ax.plot(
                df_comm["week_start"],
                df_comm["q_norm_ma8"],
                label=comm_name,
                color=color,
                linewidth=2
            )
        
        # 标注ChatGPT事件
        ax.axvline(
            pd.Timestamp("2022-11-30"),
            color="red", linestyle="-", linewidth=2, alpha=0.8
        )
        ax.text(
            pd.Timestamp("2022-11-30"), ax.get_ylim()[1] * 0.95,
            "ChatGPT\nLaunch",
            ha="center", va="top", fontsize=9,
            color="red", fontweight="bold"
        )
        ax.axhline(1.0, color="gray", linestyle=":", linewidth=1, alpha=0.5)
        
        ax.set_title(
            "Normalized Question Volume: Four Communities (2018–2026)\n"
            "(Baseline = 2021 annual average)",
            fontweight="bold"
        )
        ax.set_ylabel("Normalized Question Count\n(2021 avg = 1.0)", fontsize=12)
        ax.set_xlabel("Year", fontsize=12)
        ax.legend(loc="lower left", framealpha=0.9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"fig02_community_comparison.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ 保存: {out_path}")
        
        plt.close()


def fig03_language_trends(data: dict, output_dir: Path):
    """
    图3：Top 20编程语言问题量趋势
    """
    print("\n绘制 图3: 语言趋势...")
    
    if data["lang_weekly"] is None:
        print("  ⚠ 数据不足，跳过")
        return
    
    df = data["lang_weekly"].copy()
    
    # 找Top 20语言（按总问题量）
    top_langs = (
        df.groupby("language")["question_count"].sum()
        .nlargest(20).index.tolist()
    )
    
    df_top = df[df["language"].isin(top_langs)].copy()
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, axes = plt.subplots(4, 5, figsize=(20, 16))
        axes = axes.flatten()
        
        # 调色板
        palette = sns.color_palette("tab20", n_colors=20)
        
        for i, lang in enumerate(top_langs):
            ax = axes[i]
            df_lang = df_top[df_top["language"] == lang].sort_values("week_start")
            
            # 4周移动平均
            df_lang["q_ma4"] = df_lang["question_count"].rolling(4).mean()
            
            ax.fill_between(
                df_lang["week_start"], df_lang["question_count"],
                alpha=0.3, color=palette[i]
            )
            ax.plot(
                df_lang["week_start"], df_lang["q_ma4"],
                color=palette[i], linewidth=1.5
            )
            
            # ChatGPT垂直线
            ax.axvline(
                pd.Timestamp("2022-11-30"),
                color="red", linestyle="--", linewidth=1, alpha=0.7
            )
            
            ax.set_title(lang.capitalize(), fontsize=10, fontweight="bold")
            ax.set_xlabel("")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
            ax.tick_params(labelsize=8)
            
            # y轴格式
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, p: f"{x/1000:.0f}K" if x >= 1000 else f"{x:.0f}")
            )
        
        # 隐藏多余的子图
        for j in range(len(top_langs), len(axes)):
            axes[j].set_visible(False)
        
        fig.suptitle(
            "Weekly Question Volume by Programming Language (2018–2026)\n"
            "Red dashed line: ChatGPT launch (Nov 2022)",
            fontsize=14, fontweight="bold", y=1.01
        )
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"fig03_language_trends.{fmt}"
            plt.savefig(out_path, dpi=200 if fmt == "png" else None, bbox_inches="tight")
            print(f"  ✓ 保存: {out_path}")
        
        plt.close()


def fig04_user_composition(data: dict, output_dir: Path):
    """
    图4：用户构成变化（新手/资深/专家比例）
    """
    print("\n绘制 图4: 用户构成变化...")
    
    if data["user_cohorts"] is None:
        print("  ⚠ 数据不足，跳过")
        return
    
    df = data["user_cohorts"].copy()
    df["registration_date"] = pd.to_datetime(df["registration_date"])
    df["reg_quarter"] = df["registration_date"].dt.to_period("Q").dt.start_time
    
    # 按注册季度统计用户分层
    tier_by_quarter = df.groupby(["reg_quarter", "reputation_tier"]).size().unstack(fill_value=0)
    tier_by_quarter = tier_by_quarter.div(tier_by_quarter.sum(axis=1), axis=0)  # 归一化为比例
    
    # 只看2018年后
    tier_by_quarter = tier_by_quarter[tier_by_quarter.index >= pd.Timestamp("2018-01-01")]
    
    tier_colors = {
        "novice": "#E74C3C",
        "regular": "#F39C12",
        "experienced": "#27AE60",
        "expert": "#2980B9",
    }
    tier_order = ["novice", "regular", "experienced", "expert"]
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 左图：堆叠面积图（用户构成比例）
        available_tiers = [t for t in tier_order if t in tier_by_quarter.columns]
        colors_list = [tier_colors[t] for t in available_tiers]
        
        tier_by_quarter[available_tiers].plot.area(
            ax=ax1,
            color=colors_list,
            alpha=0.8,
            stacked=True
        )
        
        ax1.axvline(
            pd.Timestamp("2022-11-30"),
            color="black", linestyle="--", linewidth=2
        )
        ax1.text(
            pd.Timestamp("2022-11-30"), 0.95, "ChatGPT",
            ha="right", va="top", fontsize=9, fontweight="bold"
        )
        ax1.set_title("User Composition by Reputation Tier\n(New Users per Quarter)", fontweight="bold")
        ax1.set_ylabel("Proportion", fontsize=12)
        ax1.set_xlabel("Registration Quarter", fontsize=12)
        ax1.legend(loc="upper left", framealpha=0.9)
        ax1.set_ylim(0, 1)
        
        # 右图：新手用户绝对数量趋势
        if "novice" in tier_by_quarter.columns:
            novice_count = df[df["reputation_tier"] == "novice"].groupby("reg_quarter").size()
            novice_count = novice_count[novice_count.index >= pd.Timestamp("2018-01-01")]
            novice_ma = novice_count.rolling(4, center=True).mean()
            
            ax2.fill_between(
                novice_count.index, novice_count.values,
                alpha=0.3, color="#E74C3C", label="Novice registrations (raw)"
            )
            ax2.plot(
                novice_ma.index, novice_ma.values,
                color="#E74C3C", linewidth=2, label="4-quarter MA"
            )
            ax2.axvline(
                pd.Timestamp("2022-11-30"),
                color="black", linestyle="--", linewidth=2
            )
        
        ax2.set_title("Novice User Registrations Over Time", fontweight="bold")
        ax2.set_ylabel("New Novice Users per Quarter", fontsize=12)
        ax2.set_xlabel("Registration Quarter", fontsize=12)
        ax2.legend(loc="upper left")
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"fig04_user_composition.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ 保存: {out_path}")
        
        plt.close()


def fig05_summary_stats_heatmap(data: dict, output_dir: Path):
    """
    图5：关键指标热力图（年×指标）
    """
    print("\n绘制 图5: 摘要统计热力图...")
    
    if data["weekly"] is None:
        print("  ⚠ 数据不足，跳过")
        return
    
    df = data["weekly"].copy()
    df_so = df[df["community"] == "so"].copy()
    df_so["year"] = df_so["week_start"].dt.year
    
    # 按年聚合关键指标
    yearly = df_so.groupby("year").agg(
        total_questions=("question_count", "sum"),
        avg_score=("avg_score", "mean"),
        accepted_rate=("accepted_rate", "mean"),
        avg_answers=("avg_answer_count", "mean"),
        unique_askers=("unique_askers", "sum"),
    )
    
    # 归一化到0-1（每列）
    yearly_norm = (yearly - yearly.min()) / (yearly.max() - yearly.min())
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, ax = plt.subplots(figsize=(10, 5))
        
        sns.heatmap(
            yearly_norm.T,
            ax=ax,
            cmap="RdYlGn",
            annot=False,
            linewidths=0.5,
            vmin=0, vmax=1,
            cbar_kws={"label": "Normalized Value (0=min, 1=max)"}
        )
        
        # 标注ChatGPT列
        years = yearly_norm.index.tolist()
        if 2022 in years:
            chatgpt_col = years.index(2022)
            ax.axvline(chatgpt_col + 1, color="red", linewidth=3)
        
        ax.set_title(
            "Stack Overflow Key Metrics by Year (Normalized)",
            fontweight="bold"
        )
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Metric", fontsize=12)
        
        metric_labels = {
            "total_questions": "Total Questions",
            "avg_score": "Avg Question Score",
            "accepted_rate": "Acceptance Rate",
            "avg_answers": "Avg Answers/Question",
            "unique_askers": "Unique Askers",
        }
        ax.set_yticklabels(
            [metric_labels.get(m, m) for m in yearly_norm.columns],
            rotation=0
        )
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"fig05_summary_heatmap.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ 保存: {out_path}")
        
        plt.close()


def fig06_acceptance_response_trends(data: dict, output_dir: Path):
    """
    图6：回答质量趋势（采纳率 + 回答数量）
    """
    print("\n绘制 图6: 回答质量趋势...")
    
    if data["weekly"] is None:
        print("  ⚠ 数据不足，跳过")
        return
    
    df = data["weekly"].copy()
    df_so = df[df["community"] == "so"].sort_values("week_start")
    df_so["accepted_rate_ma8"] = df_so["accepted_rate"].rolling(8, center=True).mean()
    df_so["avg_answers_ma8"] = df_so["avg_answer_count"].rolling(8, center=True).mean()
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # 上图：采纳率
        ax1.fill_between(
            df_so["week_start"], df_so["accepted_rate"] * 100,
            alpha=0.2, color="#2ECC71"
        )
        ax1.plot(
            df_so["week_start"], df_so["accepted_rate_ma8"] * 100,
            color="#27AE60", linewidth=2, label="Acceptance Rate (8-week MA)"
        )
        ax1.axvline(pd.Timestamp("2022-11-30"), color="red", linestyle="--", linewidth=1.5)
        ax1.text(pd.Timestamp("2022-11-30"), ax1.get_ylim()[1] * 0.9, "ChatGPT",
                 fontsize=9, color="red", ha="right")
        ax1.set_ylabel("Acceptance Rate (%)", fontsize=12)
        ax1.set_title("Answer Quality Metrics Over Time", fontweight="bold")
        ax1.legend(loc="upper right")
        
        # 下图：平均回答数
        ax2.fill_between(
            df_so["week_start"], df_so["avg_answer_count"],
            alpha=0.2, color="#3498DB"
        )
        ax2.plot(
            df_so["week_start"], df_so["avg_answers_ma8"],
            color="#2980B9", linewidth=2, label="Avg Answers per Question (8-week MA)"
        )
        ax2.axvline(pd.Timestamp("2022-11-30"), color="red", linestyle="--", linewidth=1.5)
        ax2.set_ylabel("Avg Answers per Question", fontsize=12)
        ax2.set_xlabel("Year", fontsize=12)
        ax2.legend(loc="upper right")
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax2.xaxis.set_major_locator(mdates.YearLocator())
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"fig06_answer_quality_trends.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ 保存: {out_path}")
        
        plt.close()


def print_summary_stats(data: dict):
    """打印关键描述统计数据（用于Table 1）"""
    if data["weekly"] is None:
        return
    
    df = data["weekly"].copy()
    df_so = df[df["community"] == "so"]
    
    print("\n" + "=" * 60)
    print("关键描述统计（Stack Overflow）")
    print("=" * 60)
    
    # 按阶段统计
    phases = {
        "Pre-AI (2018-2021)": ("2018-01-01", "2021-09-30"),
        "Copilot Era (2021-2022)": ("2021-10-01", "2022-11-29"),
        "Post-ChatGPT (2022-2023)": ("2022-11-30", "2023-12-31"),
        "AI Agent Era (2024+)": ("2024-01-01", "2026-06-01"),
    }
    
    for phase_name, (start, end) in phases.items():
        mask = (
            (df_so["week_start"] >= start) &
            (df_so["week_start"] < end)
        )
        df_phase = df_so[mask]
        
        if df_phase.empty:
            continue
        
        print(f"\n{phase_name}:")
        print(f"  周均问题数: {df_phase['question_count'].mean():.0f}")
        print(f"  平均得分:   {df_phase['avg_score'].mean():.2f}")
        print(f"  采纳率:     {df_phase['accepted_rate'].mean()*100:.1f}%")
        print(f"  平均回答数: {df_phase['avg_answer_count'].mean():.2f}")


def main():
    parser = argparse.ArgumentParser(description="描述统计分析")
    parser.add_argument("--features", default="data/features/", help="特征数据目录")
    parser.add_argument("--output", default="results/figures/descriptive/", help="图表输出目录")
    parser.add_argument("--figs", default="all", help="要生成的图表（all/1/2/3/4/5/6）")
    
    args = parser.parse_args()
    
    features_dir = Path(args.features)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("描述统计分析")
    print(f"特征目录: {features_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 加载数据
    data = load_data(features_dir)
    
    # 生成图表
    fig_funcs = [
        fig01_so_weekly_trend,
        fig02_community_comparison,
        fig03_language_trends,
        fig04_user_composition,
        fig05_summary_stats_heatmap,
        fig06_acceptance_response_trends,
    ]
    
    if args.figs == "all":
        for fn in fig_funcs:
            fn(data, output_dir)
    else:
        figs_to_run = [int(x) for x in args.figs.split(",")]
        for n in figs_to_run:
            if 1 <= n <= len(fig_funcs):
                fig_funcs[n-1](data, output_dir)
    
    # 打印描述统计
    print_summary_stats(data)
    
    print(f"\n✅ 描述统计完成！图表保存在: {output_dir}")


if __name__ == "__main__":
    main()
