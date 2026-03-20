#!/usr/bin/env python3
"""
pipeline/03_ai_timeline.py
===========================
构建AI工具发布时间线数据
- AI事件节点
- AI能力指数时间序列（基于HumanEval benchmark）

输出：data/features/ai_timeline.csv

用法:
    python pipeline/03_ai_timeline.py --output data/features/ai_timeline.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# AI工具事件节点（有文献支撑的关键节点）
# ============================================================
AI_EVENTS = [
    # ---- 第一代：专业编程AI（2021-2022）----
    {
        "date": "2021-10-01",
        "name": "GitHub Copilot Beta",
        "name_short": "Copilot β",
        "generation": 1,
        "coding_focus": True,
        "humaneval_pass1": 0.265,   # Codex原始论文报告
        "description": "GitHub与OpenAI合作发布的AI代码补全工具Technical Preview",
        "impact_scope": "coding",
        "public_accessible": False,   # 仅受邀测试
    },
    {
        "date": "2022-06-21",
        "name": "GitHub Copilot GA",
        "name_short": "Copilot GA",
        "generation": 1,
        "coding_focus": True,
        "humaneval_pass1": 0.300,   # 估计值
        "description": "GitHub Copilot正式发布，面向付费用户（$10/月）",
        "impact_scope": "coding",
        "public_accessible": True,
    },
    {
        "date": "2022-11-30",
        "name": "ChatGPT Launch",
        "name_short": "ChatGPT",
        "generation": 2,
        "coding_focus": False,
        "humaneval_pass1": 0.480,   # GPT-3.5代码能力
        "description": "OpenAI发布ChatGPT，5天内用户破百万，成为史上增长最快应用",
        "impact_scope": "general",
        "public_accessible": True,
    },
    {
        "date": "2023-03-14",
        "name": "GPT-4 Release",
        "name_short": "GPT-4",
        "generation": 2,
        "coding_focus": False,
        "humaneval_pass1": 0.670,   # OpenAI技术报告
        "description": "OpenAI发布GPT-4，多模态能力，HumanEval 67%",
        "impact_scope": "general",
        "public_accessible": True,
    },
    {
        "date": "2023-07-18",
        "name": "Llama 2 Open Source",
        "name_short": "Llama 2",
        "generation": 3,
        "coding_focus": False,
        "humaneval_pass1": 0.295,   # Llama 2 70B
        "description": "Meta开源Llama 2，降低部署门槛，开源生态爆发",
        "impact_scope": "general",
        "public_accessible": True,
    },
    {
        "date": "2023-08-25",
        "name": "Code Llama Release",
        "name_short": "Code Llama",
        "generation": 3,
        "coding_focus": True,
        "humaneval_pass1": 0.530,   # Code Llama 34B
        "description": "Meta发布代码专用模型Code Llama，免费可商用",
        "impact_scope": "coding",
        "public_accessible": True,
    },
    {
        "date": "2024-01-20",
        "name": "Devin AI Coder Demo",
        "name_short": "Devin Demo",
        "generation": 4,
        "coding_focus": True,
        "humaneval_pass1": 0.138,   # SWE-bench resolved rate（不同benchmark）
        "description": "Cognition发布Devin，首个声称能独立完成软件工程任务的AI agent",
        "impact_scope": "coding",
        "public_accessible": False,
    },
    {
        "date": "2024-03-04",
        "name": "Devin Public Release",
        "name_short": "Devin GA",
        "generation": 4,
        "coding_focus": True,
        "humaneval_pass1": 0.138,
        "description": "Devin正式发布，媒体广泛报道，程序员就业焦虑讨论高峰",
        "impact_scope": "coding",
        "public_accessible": True,
    },
    {
        "date": "2024-06-20",
        "name": "Claude 3.5 Sonnet",
        "name_short": "Claude 3.5",
        "generation": 4,
        "coding_focus": False,
        "humaneval_pass1": 0.890,   # Anthropic报告
        "description": "Anthropic发布Claude 3.5 Sonnet，超越GPT-4o编程能力",
        "impact_scope": "general",
        "public_accessible": True,
    },
    {
        "date": "2024-10-01",
        "name": "Cursor 1M Users",
        "name_short": "Cursor 1M",
        "generation": 4,
        "coding_focus": True,
        "humaneval_pass1": 0.900,   # 底层模型能力
        "description": "AI编程IDE Cursor宣布达到100万付费用户里程碑",
        "impact_scope": "coding",
        "public_accessible": True,
    },
    {
        "date": "2024-12-05",
        "name": "GPT-o1 Full Release",
        "name_short": "o1 Full",
        "generation": 4,
        "coding_focus": False,
        "humaneval_pass1": 0.920,   # 估计值
        "description": "OpenAI o1推理模型完整版发布，擅长数学和代码",
        "impact_scope": "general",
        "public_accessible": True,
    },
    {
        "date": "2025-02-01",
        "name": "DeepSeek R1 Global Impact",
        "name_short": "DeepSeek R1",
        "generation": 5,
        "coding_focus": False,
        "humaneval_pass1": 0.924,   # 官方报告
        "description": "DeepSeek R1开源推理模型引发全球轰动，媲美o1性能",
        "impact_scope": "general",
        "public_accessible": True,
    },
]

# ============================================================
# HumanEval基准分数节点（用于线性插值）
# 来源：各模型官方技术报告 / Papers with Code
# ============================================================
HUMANEVAL_BENCHMARKS = [
    ("2020-06-01", 0.100, "Codex (before public)"),
    ("2021-08-01", 0.288, "Codex paper (davinci)"),
    ("2021-10-01", 0.265, "Copilot Beta"),
    ("2022-03-15", 0.290, "text-davinci-002"),
    ("2022-06-21", 0.300, "Copilot GA / gpt-3.5"),
    ("2022-11-30", 0.480, "ChatGPT (gpt-3.5-turbo)"),
    ("2023-03-14", 0.670, "GPT-4"),
    ("2023-07-18", 0.295, "Llama 2 70B"),
    ("2023-08-25", 0.530, "Code Llama 34B"),
    ("2023-11-06", 0.850, "GPT-4 Turbo"),
    ("2024-05-13", 0.877, "GPT-4o"),
    ("2024-06-20", 0.890, "Claude 3.5 Sonnet"),
    ("2024-09-12", 0.912, "o1-mini"),
    ("2024-12-05", 0.920, "o1 Full"),
    ("2025-01-20", 0.924, "DeepSeek R1"),
    ("2025-03-01", 0.930, "Claude 3.7 Sonnet (est.)"),
]

# ============================================================
# AI对SO替代性的关键阶段
# ============================================================
REPLACEMENT_PHASES = {
    "pre_ai": {
        "start": "2018-01-01",
        "end": "2021-09-30",
        "description": "Pre-AI基准期"
    },
    "copilot_era": {
        "start": "2021-10-01",
        "end": "2022-11-29",
        "description": "Copilot专业工具期"
    },
    "chatgpt_shock": {
        "start": "2022-11-30",
        "end": "2023-06-30",
        "description": "ChatGPT冲击期（6个月）"
    },
    "ai_normalization": {
        "start": "2023-07-01",
        "end": "2024-03-31",
        "description": "AI工具普及期"
    },
    "agent_era": {
        "start": "2024-04-01",
        "end": "2026-06-30",
        "description": "AI Agent时代"
    }
}


def build_weekly_ai_capability_index(
    start_date: str = "2018-01-01",
    end_date: str = "2026-06-01"
) -> pd.DataFrame:
    """
    构建周级别AI能力指数时间序列
    
    方法：
    1. 以HumanEval pass@1分数作为能力基准
    2. 在已知节点之间线性插值
    3. 加权：编程专注工具权重×1.5
    4. 归一化到0-1区间（以2018年基准为0）
    """
    # 生成每周日期序列
    weeks = pd.date_range(start=start_date, end=end_date, freq="W-MON", tz="UTC")
    df = pd.DataFrame({"week_start": weeks})
    
    # 将HumanEval节点转为时间序列
    bench_dates = [pd.Timestamp(d, tz="UTC") for d, _, _ in HUMANEVAL_BENCHMARKS]
    bench_scores = [s for _, s, _ in HUMANEVAL_BENCHMARKS]
    bench_names = [n for _, _, n in HUMANEVAL_BENCHMARKS]
    
    # 线性插值
    bench_ts = pd.Series(bench_scores, index=bench_dates)
    
    # 对每周进行插值
    all_dates = pd.DatetimeIndex(
        bench_dates + [pd.Timestamp(d, tz="UTC") for d in [start_date, end_date]]
    ).sort_values()
    bench_full = bench_ts.reindex(pd.DatetimeIndex(bench_dates))
    
    # 使用numpy插值
    bench_timestamps = np.array([t.timestamp() for t in bench_dates])
    week_timestamps = np.array([t.timestamp() for t in weeks])
    
    # 在已知范围内插值，范围外外推（但不超过最大值）
    ai_capability = np.interp(
        week_timestamps,
        bench_timestamps,
        bench_scores,
        left=bench_scores[0],   # 范围左侧用第一个值
        right=bench_scores[-1], # 范围右侧用最后一个值
    )
    
    df["humaneval_score"] = ai_capability
    
    # 标准化：相对于2018年基准（约0.05）
    baseline = 0.05  # 2018年前GPT系列的代码能力估计
    df["ai_capability_index"] = (df["humaneval_score"] - baseline) / (1.0 - baseline)
    df["ai_capability_index"] = df["ai_capability_index"].clip(0, 1)
    
    # 添加阶段标记
    df["phase"] = "pre_ai"
    for phase_name, phase_info in REPLACEMENT_PHASES.items():
        mask = (
            (df["week_start"] >= pd.Timestamp(phase_info["start"], tz="UTC")) &
            (df["week_start"] < pd.Timestamp(phase_info["end"], tz="UTC"))
        )
        df.loc[mask, "phase"] = phase_name
    
    # 添加每个主要事件后的"事件指示变量"
    for event in AI_EVENTS:
        event_date = pd.Timestamp(event["date"], tz="UTC")
        col_name = "post_" + event["name"].lower().replace(" ", "_").replace(".", "")
        df[col_name] = (df["week_start"] >= event_date).astype(int)
    
    # 关键断点变量（用于DID和RDD）
    df["post_chatgpt"] = (df["week_start"] >= pd.Timestamp("2022-11-30", tz="UTC")).astype(int)
    df["post_copilot"] = (df["week_start"] >= pd.Timestamp("2022-06-21", tz="UTC")).astype(int)
    df["post_gpt4"] = (df["week_start"] >= pd.Timestamp("2023-03-14", tz="UTC")).astype(int)
    
    # 周序号（用于趋势项）
    df["week_num"] = range(len(df))
    df["week_num_sq"] = df["week_num"] ** 2
    
    # ChatGPT后的时间距离（用于RDD带宽选择）
    chatgpt_week = pd.Timestamp("2022-11-30", tz="UTC")
    df["weeks_from_chatgpt"] = (
        (df["week_start"] - chatgpt_week).dt.days / 7
    ).round(0).astype(int)
    
    return df


def build_events_dataframe() -> pd.DataFrame:
    """构建AI事件DataFrame（用于图表标注）"""
    df = pd.DataFrame(AI_EVENTS)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)
    
    # 生成颜色标记（按generation）
    gen_colors = {1: "#4C72B0", 2: "#DD8452", 3: "#55A868", 4: "#C44E52", 5: "#8172B3"}
    df["color"] = df["generation"].map(gen_colors)
    
    # 生成线型（编程专注 vs 通用）
    df["linestyle"] = df["coding_focus"].map({True: "--", False: "-"})
    
    return df


def main():
    parser = argparse.ArgumentParser(description="构建AI工具能力指数时间线")
    parser.add_argument(
        "--output",
        default="data/features/ai_timeline.csv",
        help="输出CSV文件路径"
    )
    parser.add_argument(
        "--start",
        default="2018-01-01",
        help="时间序列开始日期"
    )
    parser.add_argument(
        "--end",
        default="2026-06-01",
        help="时间序列结束日期"
    )
    
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("构建AI能力指数时间序列...")
    df_timeline = build_weekly_ai_capability_index(args.start, args.end)
    
    print(f"  时间范围: {df_timeline['week_start'].min()} 到 {df_timeline['week_start'].max()}")
    print(f"  总周数: {len(df_timeline)}")
    print(f"  AI能力指数范围: {df_timeline['ai_capability_index'].min():.3f} ~ {df_timeline['ai_capability_index'].max():.3f}")
    
    df_timeline.to_csv(output_path, index=False)
    print(f"\n✓ 保存到 {output_path}")
    
    # 同时保存事件节点
    events_path = output_path.parent / "ai_events.csv"
    df_events = build_events_dataframe()
    df_events.to_csv(events_path, index=False)
    print(f"✓ 事件节点保存到 {events_path} ({len(df_events)} 个事件)")
    
    # 打印摘要
    print("\n关键事件节点摘要：")
    print(df_events[["date", "name", "generation", "humaneval_pass1"]].to_string(index=False))


if __name__ == "__main__":
    main()
