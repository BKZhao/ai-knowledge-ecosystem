#!/usr/bin/env python3
"""
pipeline/02_build_features.py
==============================
特征构建模块
从解析后的Parquet数据构建分析所需的特征

输出：
  - data/features/weekly_stats.parquet   周级别聚合统计
  - data/features/posts_features.parquet 帖子级别特征
  - data/features/user_cohorts.parquet   用户队列特征

用法:
    python pipeline/02_build_features.py --input data/parquet/ --output data/features/
    python pipeline/02_build_features.py --feature-type time --output data/features/
"""

import argparse
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm


# ============================================================
# AI相关关键词（用于识别AI相关问题）
# ============================================================
AI_KEYWORDS = [
    # 通用AI/LLM
    "chatgpt", "gpt-4", "gpt4", "gpt-3", "gpt3", "openai", "llm",
    "large language model", "generative ai", "gen ai", "genai",
    # 代码AI工具
    "github copilot", "copilot", "codewhisperer", "tabnine",
    "cursor", "devin", "code llama", "codellama",
    # 模型名
    "claude", "gemini", "llama", "mistral", "falcon",
    "grok", "palm", "bard", "bing chat", "bing ai",
    # 相关概念
    "prompt engineering", "fine-tuning", "rag", "retrieval augmented",
    "vector database", "embeddings", "langchain", "llamaindex",
    "ai assistant", "ai tool", "ai coding",
]

AI_KEYWORDS_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in AI_KEYWORDS) + r")\b",
    re.IGNORECASE
)

# ============================================================
# 编程语言标签列表（按生态分类）
# ============================================================
PROGRAMMING_LANGUAGES = [
    # 高AI可替代性（>0.75）
    "python", "javascript", "java", "c#", "typescript", "php",
    "swift", "kotlin", "go", "ruby", "scala",
    # 中AI可替代性（0.40-0.75）
    "c++", "c", "rust", "haskell", "r", "matlab",
    # 低AI可替代性（<0.40）
    "assembly", "cobol", "fortran", "ada", "prolog",
    # 其他重要语言
    "html", "css", "sql", "bash", "shell", "powershell",
    "dart", "lua", "perl", "groovy", "clojure",
]

# 用于标签匹配的语言集合
LANG_TAG_MAP = {lang: lang for lang in PROGRAMMING_LANGUAGES}
LANG_TAG_MAP.update({
    "c#": "csharp",
    "c++": "c_plus_plus",
})

# 用户声誉分层
REPUTATION_TIERS = {
    "novice": (0, 100),           # 新手
    "regular": (100, 1000),       # 普通用户
    "experienced": (1000, 10000), # 资深用户
    "expert": (10000, float("inf")),  # 专家
}


def get_db_connection(parquet_base: Path) -> duckdb.DuckDBPyConnection:
    """
    创建DuckDB连接并注册Parquet文件视图
    DuckDB可以直接查询Parquet文件，无需加载到内存
    """
    conn = duckdb.connect(":memory:")
    
    # 注册所有可用的Parquet目录
    sources = [
        ("so_posts", "so_posts"),
        ("so_users", "so_users"),
        ("so_votes", "so_votes"),
        ("so_comments", "so_comments"),
        ("mathse_posts", "mathse_posts"),
        ("superuser_posts", "superuser_posts"),
        ("serverfault_posts", "serverfault_posts"),
    ]
    
    for table_name, dir_name in sources:
        dir_path = parquet_base / dir_name
        if dir_path.exists():
            parquet_files = list(dir_path.glob("*.parquet"))
            if parquet_files:
                conn.execute(f"""
                    CREATE VIEW {table_name} AS
                    SELECT * FROM read_parquet('{dir_path}/*.parquet')
                """)
                print(f"  ✓ 注册视图: {table_name} ({len(parquet_files)} 个文件)")
        else:
            print(f"  ⚠ 未找到: {dir_path}")
    
    return conn


def build_weekly_stats(conn: duckdb.DuckDBPyConnection, output_path: Path):
    """
    构建周级别聚合统计
    这是事件研究和DID的核心数据集
    """
    print("\n[1/5] 构建周级别聚合统计...")
    
    query = """
    WITH questions AS (
        -- 仅选择问题帖（PostTypeId=1）
        SELECT
            Id,
            CreationDate,
            Score,
            ViewCount,
            AnswerCount,
            CommentCount,
            AcceptedAnswerId,
            OwnerUserId,
            Tags,
            Body,
            Title,
            community
        FROM so_posts
        WHERE PostTypeId = 1
          AND CreationDate >= '2018-01-01'
          AND CreationDate < '2026-06-01'
    ),
    weekly_base AS (
        SELECT
            date_trunc('week', CreationDate) AS week_start,
            community,
            COUNT(*) AS question_count,
            AVG(Score) AS avg_score,
            MEDIAN(Score) AS median_score,
            AVG(COALESCE(AnswerCount, 0)) AS avg_answer_count,
            SUM(CASE WHEN AcceptedAnswerId IS NOT NULL THEN 1 ELSE 0 END) AS accepted_count,
            AVG(COALESCE(ViewCount, 0)) AS avg_view_count,
            AVG(CommentCount) AS avg_comment_count,
            COUNT(DISTINCT OwnerUserId) AS unique_askers
        FROM questions
        GROUP BY 1, 2
    )
    SELECT * FROM weekly_base
    ORDER BY community, week_start
    """
    
    print("  执行SQL查询（周级别聚合）...")
    df_weekly = conn.execute(query).df()
    print(f"  ✓ 得到 {len(df_weekly):,} 行周级别数据")
    
    # 添加辅助时间特征
    df_weekly["year"] = df_weekly["week_start"].dt.year
    df_weekly["month"] = df_weekly["week_start"].dt.month
    df_weekly["week_of_year"] = df_weekly["week_start"].dt.isocalendar().week.astype(int)
    df_weekly["days_since_start"] = (
        df_weekly["week_start"] - pd.Timestamp("2018-01-01", tz="UTC")
    ).dt.days
    df_weekly["accepted_rate"] = (
        df_weekly["accepted_count"] / df_weekly["question_count"].clip(lower=1)
    )
    
    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_weekly.to_parquet(output_path, index=False, compression="snappy")
    print(f"  ✓ 保存到 {output_path}")
    
    return df_weekly


def build_language_weekly_stats(conn: duckdb.DuckDBPyConnection, output_path: Path):
    """
    按编程语言标签构建周级别统计
    用于DID分析（处理组 vs 对照组）
    """
    print("\n[2/5] 构建语言级别周统计...")
    
    # DuckDB中的标签处理：Tags格式为 <python><numpy><pandas>
    query = """
    WITH questions AS (
        SELECT
            date_trunc('week', CreationDate) AS week_start,
            Tags,
            Score,
            AnswerCount,
            AcceptedAnswerId,
            ViewCount
        FROM so_posts
        WHERE PostTypeId = 1
          AND CreationDate >= '2018-01-01'
          AND Tags IS NOT NULL
    ),
    -- 展开每种语言标签
    lang_questions AS (
        SELECT
            week_start,
            Score,
            AnswerCount,
            AcceptedAnswerId,
            ViewCount,
            unnest(regexp_extract_all(Tags, '<([^>]+)>', 1)) AS tag
        FROM questions
    ),
    -- 只保留编程语言标签
    lang_filter AS (
        SELECT *
        FROM lang_questions
        WHERE tag IN (
            'python', 'javascript', 'java', 'c#', 'typescript', 'php',
            'swift', 'kotlin', 'go', 'ruby', 'scala', 'c++', 'c',
            'rust', 'haskell', 'r', 'matlab', 'assembly', 'cobol',
            'fortran', 'ada', 'prolog', 'html', 'css', 'sql',
            'bash', 'dart', 'lua', 'perl'
        )
    )
    SELECT
        week_start,
        tag AS language,
        COUNT(*) AS question_count,
        AVG(Score) AS avg_score,
        AVG(COALESCE(AnswerCount, 0)) AS avg_answer_count,
        SUM(CASE WHEN AcceptedAnswerId IS NOT NULL THEN 1 ELSE 0 END)::FLOAT /
            NULLIF(COUNT(*), 0) AS accepted_rate,
        AVG(COALESCE(ViewCount, 0)) AS avg_view_count
    FROM lang_filter
    GROUP BY 1, 2
    ORDER BY 2, 1
    """
    
    print("  执行SQL查询（语言级别聚合）...")
    df_lang = conn.execute(query).df()
    print(f"  ✓ 得到 {len(df_lang):,} 行语言-周级别数据")
    
    # 添加AI可替代性指数
    ai_replaceability = {
        "python": 0.92, "javascript": 0.87, "java": 0.81,
        "c#": 0.79, "typescript": 0.85, "php": 0.78,
        "swift": 0.76, "kotlin": 0.77, "go": 0.75,
        "ruby": 0.74, "scala": 0.72, "c++": 0.71,
        "c": 0.68, "rust": 0.63, "haskell": 0.55,
        "r": 0.70, "matlab": 0.65, "assembly": 0.15,
        "cobol": 0.12, "fortran": 0.18, "ada": 0.20,
        "prolog": 0.25, "html": 0.88, "css": 0.85,
        "sql": 0.80, "bash": 0.72, "dart": 0.73,
        "lua": 0.60, "perl": 0.58,
    }
    
    df_lang["ai_replaceability"] = df_lang["language"].map(ai_replaceability)
    df_lang["treatment_group"] = (df_lang["ai_replaceability"] > 0.75).astype(int)
    df_lang["control_group"] = (df_lang["ai_replaceability"] < 0.40).astype(int)
    
    # 保存
    output_path_lang = output_path.parent / "language_weekly_stats.parquet"
    df_lang.to_parquet(output_path_lang, index=False, compression="snappy")
    print(f"  ✓ 保存到 {output_path_lang}")
    
    return df_lang


def extract_post_content_features(body: str) -> dict:
    """
    从帖子HTML内容提取内容特征
    注意：这是逐行处理的，对大数据集使用批量处理
    """
    if not body:
        return {
            "body_length": 0,
            "code_block_count": 0,
            "code_line_count": 0,
            "has_ai_keyword": False,
            "ai_keyword_count": 0,
        }
    
    # 文本长度（原始HTML）
    body_length = len(body)
    
    # 代码块：<code> 和 <pre><code> 标签
    code_blocks = re.findall(r"<code>(.*?)</code>", body, re.DOTALL)
    code_block_count = len(code_blocks)
    code_line_count = sum(block.count("\n") + 1 for block in code_blocks)
    
    # AI关键词检测（在去除HTML标签后的文本中）
    clean_text = re.sub(r"<[^>]+>", " ", body)
    ai_matches = AI_KEYWORDS_PATTERN.findall(clean_text)
    
    return {
        "body_length": body_length,
        "code_block_count": code_block_count,
        "code_line_count": code_line_count,
        "has_ai_keyword": len(ai_matches) > 0,
        "ai_keyword_count": len(ai_matches),
    }


def classify_question_type(title: str, body: str) -> str:
    """
    粗粒度问题类型分类
    how-to / debugging / conceptual / error
    """
    if not title:
        return "unknown"
    
    title_lower = title.lower()
    
    # 错误类问题
    error_patterns = [
        r"\berror\b", r"\bexception\b", r"\bfailed\b", r"\bfailure\b",
        r"\bcrash\b", r"\bbroken\b", r"\bnot working\b", r"\bbug\b",
        r"traceback", r"syntaxerror", r"typeerror", r"valueerror",
    ]
    if any(re.search(p, title_lower) for p in error_patterns):
        return "error"
    
    # 调试类问题
    debug_patterns = [
        r"\bdebug\b", r"\bwhy\s+(?:is|does|doesn't|do|doesn't)\b",
        r"\bnot\s+working\b", r"\bnot\s+(?:running|compiling|executing)\b",
        r"\bwrong\s+output\b", r"\bunexpected\b",
    ]
    if any(re.search(p, title_lower) for p in debug_patterns):
        return "debugging"
    
    # How-to类问题
    howto_patterns = [
        r"\bhow\s+(?:to|do|can|should)\b", r"\bwhat\s+is\s+the\s+(?:best|correct|right)\b",
        r"\bhow\s+(?:can|could)\s+i\b", r"\bwhat\s+(?:is|are)\b.*\bway\b",
    ]
    if any(re.search(p, title_lower) for p in howto_patterns):
        return "how-to"
    
    # 概念/理解类问题
    conceptual_patterns = [
        r"\bwhat\s+is\b", r"\bwhat\s+are\b", r"\bwhat\s+does\b",
        r"\bwhen\s+(?:to|should)\b", r"\bwhy\s+(?:would|should)\b",
        r"\bdifference\s+between\b", r"\bunderstand\b", r"\bexplain\b",
    ]
    if any(re.search(p, title_lower) for p in conceptual_patterns):
        return "conceptual"
    
    return "other"


def build_posts_features(conn: duckdb.DuckDBPyConnection, output_path: Path, sample_size: int = None):
    """
    构建帖子级别特征
    对于大数据集，使用分块处理
    """
    print("\n[3/5] 构建帖子级别特征...")
    
    # 首先只获取元数据（不包含Body，Body很大）
    metadata_query = """
    SELECT
        Id,
        CreationDate,
        PostTypeId,
        Score,
        ViewCount,
        AnswerCount,
        CommentCount,
        AcceptedAnswerId IS NOT NULL AS has_accepted_answer,
        OwnerUserId,
        Tags,
        len(COALESCE(Title, '')) AS title_length,
        len(COALESCE(Tags, '')) AS tags_length,
        -- 标签数量
        CASE 
            WHEN Tags IS NULL THEN 0
            ELSE len(regexp_extract_all(Tags, '<([^>]+)>'))
        END AS tag_count
    FROM so_posts
    WHERE PostTypeId = 1
      AND CreationDate >= '2018-01-01'
    """
    
    if sample_size:
        metadata_query += f"\nUSING SAMPLE {sample_size}"
    
    print(f"  提取帖子元数据...")
    df_meta = conn.execute(metadata_query).df()
    print(f"  ✓ 得到 {len(df_meta):,} 条问题记录")
    
    # 时间特征
    df_meta["week_start"] = df_meta["CreationDate"].dt.to_period("W").dt.start_time
    df_meta["year"] = df_meta["CreationDate"].dt.year
    df_meta["month"] = df_meta["CreationDate"].dt.month
    df_meta["hour_of_day"] = df_meta["CreationDate"].dt.hour
    df_meta["day_of_week"] = df_meta["CreationDate"].dt.dayofweek
    
    # AI时间段标记
    chatgpt_date = pd.Timestamp("2022-11-30", tz="UTC")
    copilot_date = pd.Timestamp("2022-06-21", tz="UTC")
    df_meta["post_chatgpt"] = (df_meta["CreationDate"] >= chatgpt_date).astype(int)
    df_meta["post_copilot"] = (df_meta["CreationDate"] >= copilot_date).astype(int)
    
    # 质量指标
    df_meta["has_accepted_answer"] = df_meta["has_accepted_answer"].astype(int)
    df_meta["answer_count"] = df_meta["AnswerCount"].fillna(0).astype(int)
    df_meta["score_normalized"] = np.log1p(df_meta["Score"].clip(lower=0))
    
    # 现在分批处理Body（提取内容特征）
    print("  分批提取内容特征（Body分析）...")
    
    body_features_list = []
    question_types = []
    
    chunk_size = 100_000
    total_processed = 0
    
    # 获取ID列表并分批查询Body
    id_list = df_meta["Id"].tolist()
    
    for i in tqdm(range(0, len(id_list), chunk_size), desc="  内容特征"):
        chunk_ids = id_list[i:i + chunk_size]
        ids_str = ",".join(map(str, chunk_ids))
        
        body_query = f"""
        SELECT Id, Body, Title
        FROM so_posts
        WHERE Id IN ({ids_str})
          AND PostTypeId = 1
        """
        
        df_body = conn.execute(body_query).df()
        
        for _, row in df_body.iterrows():
            features = extract_post_content_features(row.get("Body", ""))
            body_features_list.append({"Id": row["Id"], **features})
            
            qtype = classify_question_type(row.get("Title", ""), row.get("Body", ""))
            question_types.append({"Id": row["Id"], "question_type": qtype})
        
        total_processed += len(df_body)
    
    # 合并特征
    if body_features_list:
        df_body_features = pd.DataFrame(body_features_list)
        df_qtypes = pd.DataFrame(question_types)
        
        df_meta = df_meta.merge(df_body_features, on="Id", how="left")
        df_meta = df_meta.merge(df_qtypes, on="Id", how="left")
    
    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_meta.to_parquet(output_path, index=False, compression="snappy")
    print(f"  ✓ 保存到 {output_path} ({len(df_meta):,} 行)")
    
    return df_meta


def build_user_cohorts(conn: duckdb.DuckDBPyConnection, output_path: Path):
    """
    构建用户队列特征
    用于生存分析和用户行为分析
    """
    print("\n[4/5] 构建用户队列特征...")
    
    query = """
    WITH user_activity AS (
        -- 用户每周的问答活动
        SELECT
            OwnerUserId AS user_id,
            date_trunc('week', CreationDate) AS week_start,
            PostTypeId,
            Score,
            COUNT(*) AS post_count
        FROM so_posts
        WHERE OwnerUserId IS NOT NULL
          AND CreationDate >= '2018-01-01'
        GROUP BY 1, 2, 3, 4
    ),
    user_stats AS (
        -- 用户总体统计
        SELECT
            u.Id AS user_id,
            u.CreationDate AS registration_date,
            u.Reputation AS reputation,
            u.UpVotes,
            u.DownVotes,
            u.Views AS profile_views,
            u.LastAccessDate,
            -- 活跃年限
            DATEDIFF('day', u.CreationDate, COALESCE(u.LastAccessDate, CURRENT_DATE)) / 365.0 AS active_years,
            -- 声誉分层
            CASE
                WHEN u.Reputation < 100 THEN 'novice'
                WHEN u.Reputation < 1000 THEN 'regular'
                WHEN u.Reputation < 10000 THEN 'experienced'
                ELSE 'expert'
            END AS reputation_tier,
            -- 用户类型（提问者/回答者/混合）
            CASE
                WHEN q_count > 0 AND a_count = 0 THEN 'asker_only'
                WHEN q_count = 0 AND a_count > 0 THEN 'answerer_only'
                WHEN q_count > 0 AND a_count > 0 THEN 'mixed'
                ELSE 'inactive'
            END AS user_type
        FROM so_users u
        LEFT JOIN (
            SELECT OwnerUserId, COUNT(*) AS q_count
            FROM so_posts WHERE PostTypeId = 1
            GROUP BY 1
        ) q ON u.Id = q.OwnerUserId
        LEFT JOIN (
            SELECT OwnerUserId, COUNT(*) AS a_count
            FROM so_posts WHERE PostTypeId = 2
            GROUP BY 1
        ) a ON u.Id = a.OwnerUserId
    ),
    -- 最后活跃周（用于计算流失）
    last_activity AS (
        SELECT
            OwnerUserId AS user_id,
            MAX(date_trunc('week', CreationDate)) AS last_active_week,
            MIN(date_trunc('week', CreationDate)) AS first_active_week
        FROM so_posts
        WHERE OwnerUserId IS NOT NULL
          AND CreationDate >= '2018-01-01'
        GROUP BY 1
    )
    SELECT
        s.*,
        la.last_active_week,
        la.first_active_week,
        -- 流失标记（2024年后12周无活动）
        CASE
            WHEN la.last_active_week < DATE '2024-01-01' THEN 1
            ELSE 0
        END AS churned_2024,
        -- ChatGPT后流失（2023年后无活动）
        CASE
            WHEN la.last_active_week < DATE '2023-01-01' THEN 1
            ELSE 0
        END AS churned_post_chatgpt
    FROM user_stats s
    LEFT JOIN last_activity la ON s.user_id = la.user_id
    WHERE s.reputation > 0  -- 过滤无效用户
    """
    
    print("  执行用户队列查询...")
    df_users = conn.execute(query).df()
    print(f"  ✓ 得到 {len(df_users):,} 条用户记录")
    
    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_users.to_parquet(output_path, index=False, compression="snappy")
    print(f"  ✓ 保存到 {output_path}")
    
    return df_users


def build_response_time_features(conn: duckdb.DuckDBPyConnection, output_path: Path):
    """
    构建回答响应时间特征
    需要join问题和回答数据
    """
    print("\n[5/5] 构建回答响应时间特征...")
    
    query = """
    WITH questions AS (
        SELECT Id, CreationDate, Tags
        FROM so_posts
        WHERE PostTypeId = 1
          AND CreationDate >= '2018-01-01'
    ),
    first_answers AS (
        -- 每个问题的第一个回答
        SELECT
            ParentId AS question_id,
            MIN(CreationDate) AS first_answer_time
        FROM so_posts
        WHERE PostTypeId = 2
          AND ParentId IS NOT NULL
        GROUP BY 1
    )
    SELECT
        q.Id AS question_id,
        date_trunc('week', q.CreationDate) AS week_start,
        q.Tags,
        CASE
            WHEN fa.first_answer_time IS NOT NULL THEN
                DATEDIFF('minute', q.CreationDate, fa.first_answer_time)
            ELSE NULL
        END AS minutes_to_first_answer,
        fa.first_answer_time IS NOT NULL AS has_answer
    FROM questions q
    LEFT JOIN first_answers fa ON q.Id = fa.question_id
    """
    
    print("  计算首次回答时间（大查询，需要几分钟）...")
    df_response = conn.execute(query).df()
    print(f"  ✓ 得到 {len(df_response):,} 条问题响应时间数据")
    
    # 聚合为周统计
    df_response_weekly = df_response.groupby("week_start").agg(
        median_response_time_min=("minutes_to_first_answer", "median"),
        mean_response_time_min=("minutes_to_first_answer", "mean"),
        answer_rate=("has_answer", "mean"),
        question_count=("question_id", "count")
    ).reset_index()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_response_weekly.to_parquet(output_path, index=False, compression="snappy")
    print(f"  ✓ 保存到 {output_path}")
    
    return df_response_weekly


def main():
    parser = argparse.ArgumentParser(
        description="构建Stack Overflow分析特征"
    )
    parser.add_argument(
        "--input",
        default="data/parquet",
        help="Parquet数据目录（默认：data/parquet）"
    )
    parser.add_argument(
        "--output",
        default="data/features",
        help="特征输出目录（默认：data/features）"
    )
    parser.add_argument(
        "--feature-type",
        choices=["all", "time", "content", "user", "response"],
        default="all",
        help="要构建的特征类型"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="内容特征采样大小（不指定则处理全量数据）"
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Stack Overflow 特征构建")
    print(f"输入: {input_dir}")
    print(f"输出: {output_dir}")
    print("=" * 60)
    
    # 连接数据库
    print("\n初始化DuckDB连接...")
    conn = get_db_connection(input_dir)
    
    try:
        feat_type = args.feature_type
        
        # 1. 周级别聚合统计（所有分析的基础）
        if feat_type in ("all", "time"):
            build_weekly_stats(conn, output_dir / "weekly_stats.parquet")
            build_language_weekly_stats(conn, output_dir / "weekly_stats.parquet")
        
        # 2. 帖子级别内容特征
        if feat_type in ("all", "content"):
            build_posts_features(
                conn,
                output_dir / "posts_features.parquet",
                sample_size=args.sample_size
            )
        
        # 3. 用户队列特征
        if feat_type in ("all", "user"):
            build_user_cohorts(conn, output_dir / "user_cohorts.parquet")
        
        # 4. 响应时间特征
        if feat_type in ("all", "response"):
            build_response_time_features(conn, output_dir / "response_time_weekly.parquet")
        
        print("\n" + "=" * 60)
        print("✅ 特征构建完成！")
        print(f"输出文件列表：")
        for f in sorted(output_dir.glob("*.parquet")):
            size_mb = f.stat().st_size / 1024**2
            print(f"  {f.name} ({size_mb:.1f} MB)")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
