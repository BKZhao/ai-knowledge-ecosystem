"""
抓取2024-04之后SO问题的脚本（本地运行）
用法: python fetch_so_2024plus.py
"""
import requests
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

API_KEY = "rl_yXrLKrxSPQzCqJai54e1Y3bHz"  # 用户提供的API Key
LANGUAGES = ['python', 'javascript', 'typescript', 'java', 'c#', 'php', 'c++', 
             'swift', 'kotlin', 'go', 'rust', 'scala', 'haskell', 'r']

def fetch_questions(tag, from_date, to_date, page=1, pagesize=100):
    """获取指定标签、时间范围内的问题"""
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        'order': 'asc',
        'sort': 'creation',
        'tagged': tag,
        'fromdate': int(from_date.timestamp()),
        'todate': int(to_date.timestamp()),
        'page': page,
        'pagesize': pagesize,
        'site': 'stackoverflow',
        'key': API_KEY,
        'filter': 'withbody'  # 包含问题正文，用于LLM分类
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Error: {e}")
        return None

def fetch_question_stats(tag, from_date, to_date):
    """获取问题统计（用于质量指标）"""
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        'order': 'desc',
        'sort': 'creation',
        'tagged': tag,
        'fromdate': int(from_date.timestamp()),
        'todate': int(to_date.timestamp()),
        'page': 1,
        'pagesize': 100,
        'site': 'stackoverflow',
        'key': API_KEY,
        'filter': 'default'  # 不需要body
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("="*60)
    print("SO 2024-04 ~ 2025-12 数据补充脚本")
    print("="*60)
    print("\n⚠️  此脚本需要在本地运行（服务器IP可能被封）")
    print("预计需要: 约21个月 × 14语言 × 若干次API调用")
    print("API限制: 300次/天（无key）/ 10000次/天（有key）")
    print("\n" + "="*60)
    
    # 计算需要抓取的月份
    start = datetime(2024, 4, 1)
    end = datetime(2025, 12, 31)
    
    months = pd.date_range(start, end, freq='MS')
    print(f"\n需要抓取: {len(months)} 个月 × {len(LANGUAGES)} 语言")
    
    # 创建输出目录
    Path("data/fetched_2024plus").mkdir(parents=True, exist_ok=True)
    
    print("\n请确认后按回车继续...")
    input()
    
    all_questions = []
    monthly_stats = []
    
    for lang in LANGUAGES:
        print(f"\n[{lang}] 开始抓取...")
        
        for month in months:
            month_start = month
            month_end = (month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            print(f"  {month.strftime('%Y-%m')}", end=' ', flush=True)
            
            # 获取该月问题
            page = 1
            has_more = True
            month_questions = []
            
            while has_more and page <= 10:  # 限制每月每语言最多1000条
                data = fetch_questions(lang, month_start, month_end, page=page)
                if data and 'items' in data:
                    month_questions.extend(data['items'])
                    has_more = data.get('has_more', False)
                    page += 1
                    time.sleep(0.1)  # 避免触发rate limit
                else:
                    has_more = False
            
            if month_questions:
                # 计算统计
                n = len(month_questions)
                avg_score = sum(q.get('score', 0) for q in month_questions) / n if n > 0 else 0
                avg_views = sum(q.get('view_count', 0) for q in month_questions) / n if n > 0 else 0
                n_answered = sum(1 for q in month_questions if q.get('is_answered', False))
                avg_answers = sum(q.get('answer_count', 0) for q in month_questions) / n if n > 0 else 0
                
                monthly_stats.append({
                    'month': month.strftime('%Y-%m-%d'),
                    'language': lang,
                    'n_questions': n,
                    'avg_score': avg_score,
                    'avg_views': avg_views,
                    'pct_answered': n_answered / n * 100 if n > 0 else 0,
                    'avg_answers': avg_answers
                })
                
                # 保存问题（用于LLM分类）
                for q in month_questions:
                    all_questions.append({
                        'id': q['question_id'],
                        'month': month.strftime('%Y-%m'),
                        'language': lang,
                        'title': q.get('title', ''),
                        'body': q.get('body', ''),
                        'tags': ';'.join(q.get('tags', [])),
                        'score': q.get('score', 0),
                        'view_count': q.get('view_count', 0),
                        'answer_count': q.get('answer_count', 0),
                        'is_answered': q.get('is_answered', False),
                        'creation_date': q.get('creation_date', 0)
                    })
            
            print(f"({len(month_questions)}条)", end='')
        
        print()  # 换行
    
    # 保存结果
    print("\n保存结果...")
    
    df_stats = pd.DataFrame(monthly_stats)
    df_stats.to_csv('data/fetched_2024plus/monthly_stats.csv', index=False)
    print(f"  月度统计: {len(df_stats)} 行")
    
    df_questions = pd.DataFrame(all_questions)
    df_questions.to_csv('data/fetched_2024plus/questions_sample.csv', index=False)
    print(f"  问题样本: {len(df_questions)} 条")
    
    # 分层抽样（用于LLM分类）
    sample = df_questions.groupby(['month', 'language']).apply(
        lambda x: x.sample(min(len(x), 50), random_state=42)
    ).reset_index(drop=True)
    sample.to_csv('data/fetched_2024plus/llm_sample.csv', index=False)
    print(f"  LLM抽样: {len(sample)} 条")
    
    print("\n✅ 抓取完成！")
    print("\n后续步骤:")
    print("1. 上传 data/fetched_2024plus/llm_sample.csv 到服务器")
    print("2. 运行LLM分类")
    print("3. 合并到现有分类结果")

if __name__ == '__main__':
    main()
