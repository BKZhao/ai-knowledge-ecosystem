#!/bin/bash
set -e
cd /home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research
export PYTHONPATH=/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research:$PYTHONPATH

echo "===== Build Features ====="
python3 pipeline/02_build_features.py --input data/parquet/ --output data/features/ 2>&1 | tail -20

echo "===== 01 Descriptive ====="
python3 src/analysis/01_descriptive.py --features data/features/ --output results/figures/descriptive/ 2>&1 | tail -20

echo "===== 02 Event Study ====="
python3 src/analysis/02_event_study.py --features data/features/ --output results/figures/event_study/ 2>&1 | tail -20

echo "===== 03 DID Analysis ====="
python3 src/analysis/03_did_analysis.py --features data/features/ --output results/figures/did/ 2>&1 | tail -20

echo "===== ALL ANALYSES DONE ====="
