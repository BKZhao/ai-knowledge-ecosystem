#!/bin/bash
# Stack Overflow 研究数据下载队列
# 在 Posts 下完后运行此脚本

BASE_URL="https://archive.org/download/stackexchange"
DATA_DIR="/home/node/.openclaw/workspaces/ou_061694b4b8257fa782c21a959956256d/stackoverflow_research/data/raw"

mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

files=(
    "stackoverflow.com-Votes.7z"
    "stackoverflow.com-Comments.7z"
    "math.stackexchange.com.7z"
    "superuser.com.7z"
    "serverfault.com.7z"
)

for f in "${files[@]}"; do
    if [ -f "$f" ]; then
        echo "⏭️  已存在，跳过：$f"
    else
        echo "⬇️  开始下载：$f"
        wget -q --show-progress "$BASE_URL/$f" -O "$f"
        echo "✅ 完成：$f"
    fi
done

echo ""
echo "🎉 所有文件下载完毕！"
ls -lh *.7z
