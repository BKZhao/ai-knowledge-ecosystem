#!/usr/bin/env python3
"""Build weekly/language weekly parquets with correct schema for analysis scripts."""
import duckdb, math
from pathlib import Path
BASE = Path('/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research')

conn = duckdb.connect()
conn.execute("CREATE VIEW posts AS SELECT * FROM read_parquet('data/parquet/posts_2018plus.parquet')")

print("Building weekly_stats.parquet...")
weekly = conn.execute("""
    WITH q AS (
        SELECT date_trunc('week', CAST(CreationDate AS TIMESTAMP)) as week_start,
               'so' as community,
               count(*) as question_count, avg(Score) as avg_score,
               avg(ViewCount) as avg_view_count, avg(AnswerCount) as avg_answers,
               avg(BodyLength) as avg_body_length, avg(CodeBlockCount) as avg_code_blocks,
               avg(HasAccepted) as pct_accepted
        FROM posts WHERE PostTypeId = 1 GROUP BY 1, 2
    ),
    a AS (
        SELECT date_trunc('week', CAST(CreationDate AS TIMESTAMP)) as week_start,
               count(*) as answer_count, avg(Score) as avg_answer_score
        FROM posts WHERE PostTypeId = 2 GROUP BY 1
    )
    SELECT q.*, COALESCE(a.answer_count,0) as answer_count,
           COALESCE(a.avg_answer_score,0) as avg_answer_score,
           q.question_count + COALESCE(a.answer_count,0) as total_activity
    FROM q LEFT JOIN a ON q.week_start = a.week_start ORDER BY q.week_start
""").df()
weekly.to_parquet(BASE / 'data/features/weekly_stats.parquet', index=False)
print(f"  weekly_stats: {len(weekly)} rows, cols: {weekly.columns.tolist()}")

print("Building language_weekly_stats.parquet...")
conn.execute("""
    CREATE TABLE tagged AS
    SELECT
        date_trunc('week', CAST(CreationDate AS TIMESTAMP)) as week_start,
        CAST(Score AS DOUBLE) as score,
        CAST(ViewCount AS DOUBLE) as views,
        CAST(AnswerCount AS DOUBLE) as answers,
        CAST(HasAccepted AS DOUBLE) as accepted,
        (CASE
            WHEN Tags LIKE '%|python|%' THEN 'python'
            WHEN Tags LIKE '%|javascript|%' THEN 'javascript'
            WHEN Tags LIKE '%|typescript|%' THEN 'typescript'
            WHEN Tags LIKE '%|c#|%' THEN 'csharp'
            WHEN Tags LIKE '%|c++|%' THEN 'cpp'
            WHEN Tags LIKE '%|java|%' AND Tags NOT LIKE '%|javascript|%' THEN 'java'
            WHEN Tags LIKE '%|go|%' THEN 'go'
            WHEN Tags LIKE '%|ruby|%' THEN 'ruby'
            WHEN Tags LIKE '%|rust|%' THEN 'rust'
            WHEN Tags LIKE '%|r|%' AND Tags NOT LIKE '%|ruby|%' AND Tags NOT LIKE '%|rust|%' THEN 'r'
            WHEN Tags LIKE '%|haskell|%' THEN 'haskell'
            WHEN Tags LIKE '%|php|%' THEN 'php'
            WHEN Tags LIKE '%|swift|%' THEN 'swift'
            WHEN Tags LIKE '%|kotlin|%' THEN 'kotlin'
            WHEN Tags LIKE '%|scala|%' THEN 'scala'
            WHEN Tags LIKE '%|assembly|%' THEN 'assembly'
            ELSE NULL
        END) as language
    FROM posts WHERE PostTypeId = 1
""")

lang_weekly = conn.execute("""
    SELECT week_start, language, count(*) as question_count,
           avg(score) as avg_score, avg(views) as avg_view_count,
           avg(answers) as avg_answers, avg(accepted) as pct_accepted
    FROM tagged WHERE language IS NOT NULL
    GROUP BY week_start, language ORDER BY week_start, language
""").df()
conn.execute("DROP TABLE tagged")

lang_weekly['log_question_count'] = lang_weekly['question_count'].apply(math.log1p)
lang_weekly.to_parquet(BASE / 'data/features/language_weekly_stats.parquet', index=False)
print(f"  language_weekly: {len(lang_weekly)} rows, {lang_weekly['language'].nunique()} langs")
conn.close()
print("Done!")
