#!/usr/bin/env python3
"""Build weekly_stats.parquet and language_weekly_stats.parquet from existing data."""
import pandas as pd
import numpy as np
import re
import sys
from pathlib import Path

BASE = Path('/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research')

print("Loading posts parquet...")
df = pd.read_parquet(BASE / 'data/parquet/posts_2018plus.parquet')
df['CreationDate'] = pd.to_datetime(df['CreationDate'])
df['week'] = df['CreationDate'].dt.to_period('W').apply(lambda r: r.start_time)

# === 1. weekly_stats.parquet (overall SO weekly stats) ===
print("Building weekly_stats.parquet...")
questions = df[df['PostTypeId'] == 1].copy()
answers = df[df['PostTypeId'] == 2].copy()

weekly_q = questions.groupby('week').agg(
    question_count=('Id', 'count'),
    avg_score=('Score', 'mean'),
    avg_views=('ViewCount', 'mean'),
    avg_answers=('AnswerCount', 'mean'),
    avg_body_length=('BodyLength', 'mean'),
    avg_code_blocks=('CodeBlockCount', 'mean'),
    pct_accepted=('HasAccepted', 'mean'),
).reset_index()

weekly_a = answers.groupby('week').agg(
    answer_count=('Id', 'count'),
    avg_answer_score=('Score', 'mean'),
).reset_index()

weekly = weekly_q.merge(weekly_a, on='week', how='outer').fillna(0)
weekly['total_activity'] = weekly['question_count'] + weekly['answer_count']
weekly = weekly.rename(columns={'week': 'date'})
weekly.to_parquet(BASE / 'data/features/weekly_stats.parquet', index=False)
print(f"  weekly_stats: {len(weekly)} rows, {weekly['date'].min()} to {weekly['date'].max()}")

# === 2. language_weekly_stats.parquet ===
print("Building language_weekly_stats.parquet...")

LANGUAGES = {
    'python': 'python', 'javascript': 'javascript', 'java': 'java',
    'typescript': 'typescript', 'c#': 'csharp', 'c++': 'cpp', 'c': 'c',
    'go': 'go', 'ruby': 'ruby', 'rust': 'rust', 'r': 'r',
    'haskell': 'haskell', 'php': 'php', 'swift': 'swift',
    'kotlin': 'kotlin', 'scala': 'scala', 'assembly': 'assembly',
}

def get_language(tags_str):
    if not isinstance(tags_str, str):
        return None
    for tag in LANGUAGES:
        if re.search(rf'<{tag}>', tags_str, re.IGNORECASE):
            return LANGUAGES[tag]
    return None

q = questions.copy()
q['language'] = q['Tags'].apply(get_language)
q_lang = q[q['language'].notna()]

lang_weekly = q_lang.groupby(['week', 'language']).agg(
    question_count=('Id', 'count'),
    avg_score=('Score', 'mean'),
    avg_views=('ViewCount', 'mean'),
    avg_answers=('AnswerCount', 'mean'),
    pct_accepted=('HasAccepted', 'mean'),
).reset_index()
lang_weekly = lang_weekly.rename(columns={'week': 'date'})
lang_weekly['log_question_count'] = np.log1p(lang_weekly['question_count'])
lang_weekly.to_parquet(BASE / 'data/features/language_weekly_stats.parquet', index=False)
print(f"  language_weekly_stats: {len(lang_weekly)} rows, {lang_weekly['language'].nunique()} languages")
print(f"  Date range: {lang_weekly['date'].min()} to {lang_weekly['date'].max()}")

print("Done!")
