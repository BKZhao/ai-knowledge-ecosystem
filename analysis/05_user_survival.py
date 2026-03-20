#!/usr/bin/env python3
"""
analysis/05_user_survival.py
=============================
用户生存分析
- 定义用户"流失"：连续12周无活动
- Kaplan-Meier生存曲线（按用户类型分组）
- Cox比例风险模型（流失风险的影响因素）
- 比较新手 vs 资深用户的流失时序差异
- 检验H3：AI工具后新手用户流失率上升

输出：results/figures/survival/

用法:
    python analysis/05_user_survival.py --features data/features/ --output results/figures/survival/
"""

import argparse
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, CoxPHFitter, WeibullAFTFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test
from lifelines.utils import concordance_index

warnings.filterwarnings("ignore")

PUBLICATION_STYLE = {
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": "--",
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 13,
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
}

# 声誉分层定义
REPUTATION_TIERS = {
    "novice": (0, 100),
    "regular": (100, 1000),
    "experienced": (1000, 10000),
    "expert": (10000, float("inf")),
}

# AI时间节点
CHATGPT_DATE = pd.Timestamp("2022-11-30")
COPILOT_DATE = pd.Timestamp("2022-06-21")

# 流失定义：连续N周无活动
CHURN_WEEKS = 12


def load_user_data(features_dir: Path) -> pd.DataFrame:
    """
    加载用户队列数据
    构建生存分析所需格式
    """
    cohort_path = features_dir / "user_cohorts.parquet"
    if not cohort_path.exists():
        raise FileNotFoundError(f"找不到 {cohort_path}，请先运行 02_build_features.py")
    
    df = pd.read_parquet(cohort_path)
    
    # 转换日期
    for col in ["registration_date", "last_active_week", "first_active_week"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    print(f"  ✓ 加载 {len(df):,} 条用户记录")
    
    # ---- 构建生存分析变量 ----
    
    # 观察截止日期
    OBSERVATION_END = pd.Timestamp("2025-01-01")
    
    # 生存时间（从注册到流失或截止，单位：周）
    if "last_active_week" in df.columns and "first_active_week" in df.columns:
        # 方法1：从第一次活跃到最后一次活跃的持续时间
        df["survival_weeks"] = (
            (df["last_active_week"] - df["first_active_week"]).dt.days / 7
        ).clip(lower=0)
        
        # 流失标记（最后活跃时间 < 截止日期 - 12周 = 视为流失）
        churn_threshold = OBSERVATION_END - pd.Timedelta(weeks=CHURN_WEEKS)
        df["churned"] = (df["last_active_week"] < churn_threshold).astype(int)
    else:
        # 方法2：从注册日期估算
        df["survival_weeks"] = (
            (pd.Timestamp("2025-01-01") - df["registration_date"]).dt.days / 7
        ).clip(lower=1)
        df["churned"] = df.get("churned_2024", 0)
    
    # 确保生存时间为正
    df["survival_weeks"] = df["survival_weeks"].fillna(1).clip(lower=1)
    
    # ---- 协变量 ----
    
    # 声誉分层（注册时的初始信誉）
    df["reputation_tier"] = pd.cut(
        df["reputation"].fillna(0).clip(lower=0),
        bins=[0, 100, 1000, 10000, float("inf")],
        labels=["novice", "regular", "experienced", "expert"],
        right=False
    )
    
    # 注册队列（ChatGPT前vs后）
    df["cohort_post_chatgpt"] = (df["registration_date"] >= CHATGPT_DATE).astype(int)
    df["cohort_post_copilot"] = (df["registration_date"] >= COPILOT_DATE).astype(int)
    
    # 注册年份
    df["registration_year"] = df["registration_date"].dt.year
    
    # 日志声誉
    df["log_reputation"] = np.log1p(df["reputation"].fillna(0))
    
    # 用户类型虚拟变量
    if "user_type" in df.columns:
        df["is_asker_only"] = (df["user_type"] == "asker_only").astype(int)
        df["is_answerer_only"] = (df["user_type"] == "answerer_only").astype(int)
    else:
        df["is_asker_only"] = 0
        df["is_answerer_only"] = 0
    
    # 过滤无效记录
    df = df[
        (df["survival_weeks"] > 0) &
        (df["registration_date"] >= "2018-01-01") &
        (df["registration_date"] < "2025-01-01")
    ].copy()
    
    print(f"  ✓ 过滤后: {len(df):,} 条有效用户记录")
    print(f"  流失率: {df['churned'].mean()*100:.1f}%")
    print(f"  中位生存时间: {df['survival_weeks'].median():.0f} 周")
    
    return df


def plot_km_curves(df: pd.DataFrame, output_dir: Path):
    """
    绘制Kaplan-Meier生存曲线
    分组：声誉分层 + 注册时间队列（ChatGPT前/后）
    """
    print("\n绘制Kaplan-Meier生存曲线...")
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # ---- 左图：按声誉分层的KM曲线 ----
        ax1 = axes[0]
        tier_colors = {
            "novice": "#E74C3C",
            "regular": "#F39C12",
            "experienced": "#27AE60",
            "expert": "#2980B9",
        }
        
        km_results = {}
        
        for tier, color in tier_colors.items():
            df_tier = df[df["reputation_tier"] == tier]
            if len(df_tier) < 30:
                continue
            
            kmf = KaplanMeierFitter()
            kmf.fit(
                df_tier["survival_weeks"],
                event_observed=df_tier["churned"],
                label=f"{tier.capitalize()} (n={len(df_tier):,})"
            )
            kmf.plot_survival_function(ax=ax1, color=color, linewidth=2, ci_show=True, ci_alpha=0.1)
            km_results[tier] = kmf
        
        ax1.set_title("Survival by Reputation Tier\n(Event = Churn after 12-week inactivity)", fontweight="bold")
        ax1.set_xlabel("Weeks Since First Activity", fontsize=12)
        ax1.set_ylabel("Probability of Remaining Active", fontsize=12)
        ax1.set_ylim(0, 1.05)
        ax1.legend(loc="lower left", framealpha=0.9)
        
        # ---- 右图：按注册队列（ChatGPT前vs后）----
        ax2 = axes[1]
        
        cohort_colors = {0: "#3498DB", 1: "#E74C3C"}
        cohort_labels = {0: "Pre-ChatGPT cohort", 1: "Post-ChatGPT cohort"}
        
        for post_chatgpt, color in cohort_colors.items():
            df_cohort = df[df["cohort_post_chatgpt"] == post_chatgpt]
            if len(df_cohort) < 30:
                continue
            
            kmf = KaplanMeierFitter()
            kmf.fit(
                df_cohort["survival_weeks"],
                event_observed=df_cohort["churned"],
                label=f"{cohort_labels[post_chatgpt]} (n={len(df_cohort):,})"
            )
            kmf.plot_survival_function(ax=ax2, color=color, linewidth=2.5, ci_show=True, ci_alpha=0.15)
        
        ax2.set_title("Survival by Registration Cohort\n(Pre vs. Post ChatGPT)", fontweight="bold")
        ax2.set_xlabel("Weeks Since First Activity", fontsize=12)
        ax2.set_ylabel("Probability of Remaining Active", fontsize=12)
        ax2.set_ylim(0, 1.05)
        ax2.legend(loc="lower left", framealpha=0.9)
        
        # 对数秩检验
        try:
            pre = df[df["cohort_post_chatgpt"] == 0]
            post = df[df["cohort_post_chatgpt"] == 1]
            if len(pre) > 30 and len(post) > 30:
                lr = logrank_test(
                    pre["survival_weeks"], post["survival_weeks"],
                    event_observed_A=pre["churned"],
                    event_observed_B=post["churned"]
                )
                ax2.text(
                    0.98, 0.95,
                    f"Log-rank test: p = {lr.p_value:.4f}",
                    transform=ax2.transAxes,
                    ha="right", va="top", fontsize=10,
                    bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8)
                )
        except Exception:
            pass
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"km_curves.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()
    
    return km_results


def plot_km_novice_comparison(df: pd.DataFrame, output_dir: Path):
    """
    专门比较新手用户：
    ChatGPT前注册的新手 vs ChatGPT后注册的新手
    """
    print("\n绘制新手用户对比KM曲线...")
    
    df_novice = df[df["reputation_tier"] == "novice"].copy()
    
    if len(df_novice) < 60:
        print("  ⚠ 新手用户数量不足，跳过")
        return
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 按年份分队列
        years_to_show = [2019, 2020, 2021, 2022, 2023, 2024]
        colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(years_to_show)))
        
        for year, color in zip(years_to_show, colors):
            df_year = df_novice[df_novice["registration_year"] == year]
            if len(df_year) < 20:
                continue
            
            kmf = KaplanMeierFitter()
            kmf.fit(
                df_year["survival_weeks"],
                event_observed=df_year["churned"],
                label=f"{year} cohort (n={len(df_year):,})"
            )
            kmf.plot_survival_function(
                ax=ax, color=color, linewidth=2,
                ci_show=(year in [2021, 2023]),  # 只显示关键年份的CI
                ci_alpha=0.1
            )
        
        # 标注ChatGPT发布年份
        ax.axvline(52, color="red", linestyle="--", linewidth=1.5, alpha=0.7,
                   label="12-month mark")
        
        ax.set_title(
            "Novice User Retention by Registration Year\n"
            "(Color: Green=2019 cohort → Red=2024 cohort)",
            fontweight="bold"
        )
        ax.set_xlabel("Weeks Since Registration", fontsize=12)
        ax.set_ylabel("Proportion Still Active", fontsize=12)
        ax.set_ylim(0, 1.05)
        ax.set_xlim(0, 104)  # 显示前2年
        ax.legend(loc="lower left", fontsize=9, framealpha=0.9)
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"km_novice_cohorts.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()


def run_cox_model(df: pd.DataFrame) -> object:
    """
    Cox比例风险模型
    分析影响用户流失风险的因素
    """
    print("\n运行Cox比例风险模型...")
    
    # 选择协变量
    covariates = [
        "log_reputation",
        "cohort_post_chatgpt",
        "cohort_post_copilot",
        "is_asker_only",
        "is_answerer_only",
    ]
    
    # 添加声誉分层虚拟变量
    df_cox = pd.get_dummies(
        df[["survival_weeks", "churned"] + covariates + ["reputation_tier"]],
        columns=["reputation_tier"],
        drop_first=True  # 参考类：expert
    )
    
    # 移除缺失值
    df_cox = df_cox.dropna()
    
    # 剔除生存时间为0的观测
    df_cox = df_cox[df_cox["survival_weeks"] > 0]
    
    if len(df_cox) < 100:
        print("  ⚠ 样本量不足，跳过Cox模型")
        return None
    
    print(f"  Cox模型样本量: {len(df_cox):,}")
    
    # Cox PH模型
    cph = CoxPHFitter(penalizer=0.1)
    
    # 选择实际存在的列
    feature_cols = [c for c in df_cox.columns if c not in ["survival_weeks", "churned"]]
    
    try:
        cph.fit(
            df_cox[["survival_weeks", "churned"] + feature_cols],
            duration_col="survival_weeks",
            event_col="churned",
            show_progress=False
        )
        
        print("\n  Cox模型结果：")
        print(cph.summary[["coef", "exp(coef)", "se(coef)", "p"]].to_string())
        print(f"\n  Concordance Index: {cph.concordance_index_:.4f}")
        
        return cph
    
    except Exception as e:
        print(f"  ⚠ Cox模型失败: {e}")
        return None


def plot_cox_results(cph: object, output_dir: Path):
    """绘制Cox模型结果森林图"""
    if cph is None:
        return
    
    print("\n绘制Cox森林图...")
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, ax = plt.subplots(figsize=(10, 8))
        cph.plot(ax=ax)
        
        ax.set_title(
            "Cox Proportional Hazards Model\n"
            "(Outcome: User Churn; HR > 1 = Higher Churn Risk)",
            fontweight="bold"
        )
        ax.axvline(0, color="black", linewidth=1)
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"cox_forest_plot.{fmt}"
            plt.savefig(out_path, dpi=300 if fmt == "png" else None)
            print(f"  ✓ {out_path}")
        
        plt.close()


def generate_survival_summary(df: pd.DataFrame, cph: object) -> pd.DataFrame:
    """生成生存分析摘要统计"""
    rows = []
    
    # 按声誉分层
    for tier in ["novice", "regular", "experienced", "expert"]:
        df_tier = df[df["reputation_tier"] == tier]
        if len(df_tier) < 10:
            continue
        
        kmf = KaplanMeierFitter()
        kmf.fit(df_tier["survival_weeks"], event_observed=df_tier["churned"])
        
        # 中位生存时间
        median_survival = kmf.median_survival_time_
        
        # 12周、26周、52周生存率
        survival_12w = kmf.predict(12)
        survival_26w = kmf.predict(26)
        survival_52w = kmf.predict(52)
        
        rows.append({
            "Group": tier.capitalize(),
            "N": len(df_tier),
            "Churn Rate (%)": f"{df_tier['churned'].mean()*100:.1f}%",
            "Median Survival (weeks)": f"{median_survival:.0f}" if not np.isinf(median_survival) else ">200",
            "12-week Retention": f"{float(survival_12w):.1%}",
            "26-week Retention": f"{float(survival_26w):.1%}",
            "52-week Retention": f"{float(survival_52w):.1%}",
        })
    
    df_summary = pd.DataFrame(rows)
    return df_summary


def main():
    parser = argparse.ArgumentParser(description="用户生存分析")
    parser.add_argument("--features", default="data/features/", help="特征数据目录")
    parser.add_argument("--output", default="results/figures/survival/", help="输出目录")
    parser.add_argument("--churn-weeks", type=int, default=12, help="流失判定：连续N周无活动")
    
    args = parser.parse_args()
    
    features_dir = Path(args.features)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("用户生存分析")
    print(f"流失定义：连续 {args.churn_weeks} 周无活动")
    print("=" * 60)
    
    # 加载数据
    print("\n加载用户数据...")
    df = load_user_data(features_dir)
    
    # KM曲线
    km_results = plot_km_curves(df, output_dir)
    
    # 新手用户专项分析
    plot_km_novice_comparison(df, output_dir)
    
    # Cox模型
    cph = run_cox_model(df)
    plot_cox_results(cph, output_dir)
    
    # 生成摘要表
    df_summary = generate_survival_summary(df, cph)
    
    summary_path = Path("results/tables/survival_summary.csv")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(summary_path, index=False)
    
    print("\n" + "=" * 60)
    print("生存分析摘要")
    print("=" * 60)
    print(df_summary.to_string(index=False))
    
    # 保存Cox结果
    if cph is not None:
        cox_path = Path("results/tables/cox_results.csv")
        cph.summary.to_csv(cox_path)
        print(f"\n✓ Cox结果保存到: {cox_path}")
        print(f"  Concordance Index: {cph.concordance_index_:.4f}")
    
    print(f"\n✅ 用户生存分析完成！图表目录: {output_dir}")


if __name__ == "__main__":
    main()
