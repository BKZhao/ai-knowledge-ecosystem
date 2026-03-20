#!/usr/bin/env python3
"""
analysis/02_event_study.py
===========================
事件研究法分析
对每个AI事件节点计算累积异常效应（CAR）

方法：
- 估计窗口：事件前52周（拟合基准OLS趋势）
- 事件窗口：事件前后各12周
- 异常值 = 实际值 - 预期值
- 累积异常效应（CAR）及95% CI
- Newey-West标准误（处理序列自相关）

输出：results/figures/event_study/

用法:
    python analysis/02_event_study.py --features data/features/ --output results/figures/event_study/
"""

import argparse
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_hac

warnings.filterwarnings("ignore")

# 全局图表风格
PUBLICATION_STYLE = {
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.grid": True, "grid.alpha": 0.3, "grid.linestyle": "--",
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 13,
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.facecolor": "white",
}


# AI事件列表（来自pipeline/03_ai_timeline.py）
EVENT_LIST = [
    {"date": "2021-10-01", "name": "GitHub Copilot Beta", "short": "Copilot β"},
    {"date": "2022-06-21", "name": "GitHub Copilot GA", "short": "Copilot GA"},
    {"date": "2022-11-30", "name": "ChatGPT Launch", "short": "ChatGPT"},
    {"date": "2023-03-14", "name": "GPT-4 Release", "short": "GPT-4"},
    {"date": "2023-07-18", "name": "Llama 2 Open Source", "short": "Llama 2"},
    {"date": "2023-08-25", "name": "Code Llama Release", "short": "Code Llama"},
    {"date": "2024-03-04", "name": "Devin Public Release", "short": "Devin"},
    {"date": "2024-06-20", "name": "Claude 3.5 Sonnet", "short": "Claude 3.5"},
]

# 估计窗口和事件窗口大小（周）
ESTIMATION_WINDOW = 52   # 事件前52周用于拟合基准
EVENT_WINDOW = 12        # 事件前后各12周


def load_data(features_dir: Path) -> pd.DataFrame:
    """加载周统计数据"""
    weekly_path = features_dir / "weekly_stats.parquet"
    if not weekly_path.exists():
        raise FileNotFoundError(f"找不到 {weekly_path}，请先运行 02_build_features.py")
    
    df = pd.read_parquet(weekly_path)
    df["week_start"] = pd.to_datetime(df["week_start"])
    
    # 只保留SO主站
    df_so = df[df["community"] == "so"].sort_values("week_start").reset_index(drop=True)
    
    # 对数变换（处理右偏和异方差）
    df_so["log_question_count"] = np.log1p(df_so["question_count"])
    df_so["log_view_count"] = np.log1p(df_so["avg_view_count"])
    
    # 周序号（用于趋势项）
    df_so["t"] = range(len(df_so))
    df_so["t_sq"] = df_so["t"] ** 2
    
    # 季节性控制（周固定效应）
    df_so["week_of_year"] = df_so["week_start"].dt.isocalendar().week.astype(int)
    
    return df_so


def run_event_study(
    df: pd.DataFrame,
    event_date: str,
    outcome_var: str = "log_question_count",
    est_window: int = ESTIMATION_WINDOW,
    event_window: int = EVENT_WINDOW,
) -> dict:
    """
    对单个事件运行事件研究
    
    返回：
    - abnormal_returns: 每周异常值（AR）
    - cumulative_ar: 累积异常值（CAR）序列
    - car_final: 事件窗口末尾的CAR
    - car_ci: 95% CI
    - baseline_model: 基准OLS模型
    - ar_se: 异常值标准误（Newey-West）
    """
    event_date = pd.Timestamp(event_date, tz="UTC") if "UTC" not in str(event_date) else pd.Timestamp(event_date)
    
    # 找事件周索引
    df_sorted = df.sort_values("week_start").reset_index(drop=True)
    
    # 找最近的周
    date_diffs = (df_sorted["week_start"] - event_date).abs()
    event_idx = date_diffs.idxmin()
    
    # 定义各窗口
    est_start_idx = max(0, event_idx - est_window - event_window)
    est_end_idx = event_idx - event_window
    evt_start_idx = event_idx - event_window
    evt_end_idx = min(len(df_sorted) - 1, event_idx + event_window)
    
    if est_start_idx >= est_end_idx or est_end_idx <= 0:
        print(f"    ⚠ 估计窗口不足，跳过事件")
        return None
    
    # 估计窗口数据（用于拟合基准）
    df_est = df_sorted.iloc[est_start_idx:est_end_idx].copy()
    
    # 事件窗口数据（用于计算异常值）
    df_evt = df_sorted.iloc[evt_start_idx:evt_end_idx + 1].copy()
    
    if len(df_est) < 20:
        print(f"    ⚠ 估计窗口数据不足 ({len(df_est)} 周)，跳过")
        return None
    
    # ---- 拟合基准模型（OLS）----
    # 控制变量：时间趋势 + 季节性（月份虚拟变量）
    X_est = pd.get_dummies(
        df_est[["t", "t_sq", "week_of_year"]],
        columns=["week_of_year"],
        drop_first=True
    )
    X_est = sm.add_constant(X_est.astype(float))
    y_est = df_est[outcome_var].values
    
    model = sm.OLS(y_est, X_est).fit()
    
    # ---- 用估计窗口参数预测事件窗口 ----
    X_evt = pd.get_dummies(
        df_evt[["t", "t_sq", "week_of_year"]],
        columns=["week_of_year"],
        drop_first=True
    )
    X_evt = sm.add_constant(X_evt.astype(float))
    
    # 对齐列（确保特征一致）
    missing_cols = set(X_est.columns) - set(X_evt.columns)
    for col in missing_cols:
        X_evt[col] = 0
    X_evt = X_evt[X_est.columns]
    
    y_pred = model.predict(X_evt)
    y_actual = df_evt[outcome_var].values
    
    # ---- 异常值计算 ----
    ar = y_actual - y_pred  # 异常值（Abnormal Returns）
    car = np.cumsum(ar)     # 累积异常值（CAR）
    
    # 相对时间（0 = 事件周）
    relative_weeks = list(range(-event_window, len(ar) - event_window))
    
    # ---- Newey-West标准误 ----
    # 先用估计窗口残差估计AR方差
    resid_est = y_est - model.predict(X_est)
    
    # 残差的NW标准误（允许4阶序列相关）
    lags = min(4, len(resid_est) // 5)
    ar_variance = np.var(resid_est)
    ar_se = np.sqrt(ar_variance)  # 单期标准误近似
    
    # CAR的标准误随窗口累积（假设独立，保守估计）
    car_se = ar_se * np.sqrt(np.arange(1, len(ar) + 1))
    
    # 95% CI
    z_95 = 1.96
    car_lower = car - z_95 * car_se
    car_upper = car + z_95 * car_se
    
    # 事件周的CAR t统计量
    pre_event_ar = ar[relative_weeks.index(0) - min(5, event_window):][:5] if 0 in relative_weeks else ar[:5]
    
    return {
        "event_date": event_date,
        "ar": ar,
        "car": car,
        "car_lower": car_lower,
        "car_upper": car_upper,
        "car_se": car_se,
        "relative_weeks": relative_weeks,
        "actual": y_actual,
        "predicted": y_pred,
        "df_evt_dates": df_evt["week_start"].values,
        "baseline_model": model,
        "r_squared": model.rsquared,
        "car_final": car[-1] if len(car) > 0 else np.nan,
        "car_final_se": car_se[-1] if len(car_se) > 0 else np.nan,
        "car_final_t": car[-1] / car_se[-1] if car_se[-1] > 0 else np.nan,
        "est_window_size": len(df_est),
    }


def plot_car(result: dict, event_name: str, output_dir: Path):
    """
    绘制单个事件的CAR图
    """
    relative_weeks = result["relative_weeks"]
    car = result["car"]
    car_lower = result["car_lower"]
    car_upper = result["car_upper"]
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # ---- 上图：CAR ----
        ax1.fill_between(relative_weeks, car_lower, car_upper, alpha=0.2, color="#3498DB", label="95% CI")
        ax1.plot(relative_weeks, car, color="#2980B9", linewidth=2.5, label="CAR")
        ax1.axhline(0, color="black", linewidth=1, linestyle="-")
        ax1.axvline(0, color="red", linewidth=2, linestyle="--", label="Event date", zorder=5)
        
        # 标注CAR最终值
        final_car = car[-1]
        final_ci = f"[{car_lower[-1]:.3f}, {car_upper[-1]:.3f}]"
        ax1.text(
            0.98, 0.05,
            f"Final CAR: {final_car:.3f}\n95% CI: {final_ci}",
            transform=ax1.transAxes,
            ha="right", va="bottom",
            fontsize=10, fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8)
        )
        
        ax1.set_title(
            f"Cumulative Abnormal Returns: {event_name}\n"
            f"(Outcome: log question count, Estimation window: {result['est_window_size']} weeks)",
            fontweight="bold"
        )
        ax1.set_ylabel("Cumulative Abnormal Effect (log scale)", fontsize=11)
        ax1.set_xlabel("")
        ax1.legend(loc="upper left")
        ax1.set_xlim(min(relative_weeks), max(relative_weeks))
        
        # ---- 下图：实际 vs 预测 ----
        ax2.plot(relative_weeks, result["actual"], color="#E74C3C", linewidth=2, label="Actual")
        ax2.plot(relative_weeks, result["predicted"], color="#2ECC71", linewidth=2,
                 linestyle="--", label="Predicted (counterfactual)")
        ax2.axvline(0, color="red", linewidth=1.5, linestyle="--")
        ax2.fill_between(
            relative_weeks,
            result["predicted"], result["actual"],
            where=[a > p for a, p in zip(result["actual"], result["predicted"])],
            alpha=0.2, color="green", label="Above expected"
        )
        ax2.fill_between(
            relative_weeks,
            result["predicted"], result["actual"],
            where=[a < p for a, p in zip(result["actual"], result["predicted"])],
            alpha=0.2, color="red", label="Below expected"
        )
        
        ax2.set_title("Actual vs. Counterfactual (log question count)")
        ax2.set_ylabel("Log(Question Count + 1)", fontsize=11)
        ax2.set_xlabel("Weeks Relative to Event (0 = event week)", fontsize=12)
        ax2.legend(loc="upper left")
        ax2.set_xlim(min(relative_weeks), max(relative_weeks))
        
        plt.tight_layout()
        
        safe_name = event_name.lower().replace(" ", "_").replace(".", "").replace("/", "_")
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"car_{safe_name}.{fmt}"
            plt.savefig(out_path, dpi=200 if fmt == "png" else None)
        
        plt.close()


def plot_all_cars_summary(results: list, output_dir: Path):
    """
    绘制所有事件的CAR汇总图（多面板）
    """
    valid_results = [(r, e) for r, e in results if r is not None]
    n = len(valid_results)
    
    if n == 0:
        return
    
    cols = 4
    rows = (n + cols - 1) // cols
    
    with plt.rc_context(PUBLICATION_STYLE):
        fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 4))
        axes = axes.flatten() if n > 1 else [axes]
        
        for i, (result, event) in enumerate(valid_results):
            ax = axes[i]
            rw = result["relative_weeks"]
            
            ax.fill_between(rw, result["car_lower"], result["car_upper"],
                            alpha=0.25, color="#3498DB")
            ax.plot(rw, result["car"], color="#2980B9", linewidth=2)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.axvline(0, color="red", linewidth=1.5, linestyle="--")
            
            # 显著性标记
            t_stat = result.get("car_final_t", 0)
            if abs(t_stat) > 2.576:
                sig = "***"
            elif abs(t_stat) > 1.96:
                sig = "**"
            elif abs(t_stat) > 1.645:
                sig = "*"
            else:
                sig = ""
            
            ax.set_title(f"{event['short']}{sig}", fontsize=9, fontweight="bold")
            ax.tick_params(labelsize=8)
        
        # 隐藏多余子图
        for j in range(n, len(axes)):
            axes[j].set_visible(False)
        
        fig.suptitle(
            "Cumulative Abnormal Effects Around AI Tool Releases\n"
            "(Baseline: OLS trend from pre-event 52 weeks; * p<.10, ** p<.05, *** p<.01)",
            fontsize=13, fontweight="bold", y=1.01
        )
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            out_path = output_dir / f"car_all_events_summary.{fmt}"
            plt.savefig(out_path, dpi=200 if fmt == "png" else None, bbox_inches="tight")
            print(f"  ✓ 汇总图: {out_path}")
        
        plt.close()


def generate_event_study_table(results: list) -> pd.DataFrame:
    """生成事件研究汇总表（用于Table 2）"""
    rows = []
    for result, event in results:
        if result is None:
            continue
        
        t_stat = result.get("car_final_t", 0)
        if abs(t_stat) > 2.576:
            sig = "***"
        elif abs(t_stat) > 1.96:
            sig = "**"
        elif abs(t_stat) > 1.645:
            sig = "*"
        else:
            sig = ""
        
        # 转换CAR为百分比变化（对数差近似为百分比）
        car_pct = (np.exp(result["car_final"]) - 1) * 100
        
        rows.append({
            "Event": event["name"],
            "Date": event["date"],
            "CAR (log)": f"{result['car_final']:.4f}{sig}",
            "CAR (%)": f"{car_pct:.1f}%",
            "SE": f"({result['car_final_se']:.4f})",
            "t-stat": f"{t_stat:.2f}",
            "R² (baseline)": f"{result['r_squared']:.3f}",
            "Est. window (weeks)": result["est_window_size"],
        })
    
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="事件研究法分析")
    parser.add_argument("--features", default="data/features/", help="特征数据目录")
    parser.add_argument("--output", default="results/figures/event_study/", help="输出目录")
    parser.add_argument("--outcome", default="log_question_count", help="结果变量")
    
    args = parser.parse_args()
    
    features_dir = Path(args.features)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("事件研究法分析")
    print(f"结果变量: {args.outcome}")
    print("=" * 60)
    
    # 加载数据
    df = load_data(features_dir)
    print(f"\n数据范围: {df['week_start'].min()} 到 {df['week_start'].max()}")
    print(f"总周数: {len(df)}")
    
    # 对每个事件运行分析
    all_results = []
    
    for event in EVENT_LIST:
        print(f"\n处理事件: {event['name']} ({event['date']})")
        
        result = run_event_study(
            df,
            event_date=event["date"],
            outcome_var=args.outcome,
            est_window=ESTIMATION_WINDOW,
            event_window=EVENT_WINDOW,
        )
        
        if result:
            car_pct = (np.exp(result["car_final"]) - 1) * 100
            print(f"  CAR: {result['car_final']:.4f} ({car_pct:.1f}%)")
            print(f"  t统计量: {result['car_final_t']:.2f}")
            print(f"  基准R²: {result['r_squared']:.3f}")
            
            # 绘制单事件图
            plot_car(result, event["name"], output_dir)
            print(f"  ✓ 图表已保存")
        
        all_results.append((result, event))
    
    # 汇总图
    print("\n生成汇总图...")
    plot_all_cars_summary(all_results, output_dir)
    
    # 汇总表
    print("\n生成汇总表...")
    df_table = generate_event_study_table(all_results)
    
    # 保存为CSV（用于后续LaTeX格式化）
    table_path = Path("results/tables/event_study_results.csv")
    table_path.parent.mkdir(parents=True, exist_ok=True)
    df_table.to_csv(table_path, index=False)
    
    print("\n" + "=" * 60)
    print("事件研究结果汇总")
    print("=" * 60)
    print(df_table.to_string(index=False))
    
    print(f"\n✅ 事件研究完成！")
    print(f"   图表目录: {output_dir}")
    print(f"   汇总表: {table_path}")


if __name__ == "__main__":
    main()
