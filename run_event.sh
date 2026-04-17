#!/bin/bash
cd /home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research
export PYTHONPATH=.:$PYTHONPATH

echo "===== 02 Event Study ====="
python3 src/analysis/02_event_study.py --features data/features/ --output results/figures/event_study/ 2>&1 | tail -40

echo "===== DONE ====="
