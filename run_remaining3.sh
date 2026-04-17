#!/bin/bash
set -e
cd /home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research
export PYTHONPATH=.:$PYTHONPATH

echo "===== Build Features (duckdb) ====="
python3 build_features_duckdb.py

echo "===== 02 Event Study ====="
python3 src/analysis/02_event_study.py --features data/features/ --output results/figures/event_study/ 2>&1 | tail -30

echo "===== 03 DID Analysis ====="
python3 src/analysis/03_did_analysis.py --features data/features/ --output results/figures/did/ 2>&1 | tail -30

echo "===== 01 Descriptive ====="
python3 src/analysis/01_descriptive.py --features data/features/ --output results/figures/descriptive/ 2>&1 | tail -30

echo "===== ALL DONE ====="
