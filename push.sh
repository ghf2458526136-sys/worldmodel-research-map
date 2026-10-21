#!/usr/bin/env bash
# 一键：建仓库 -> 推送 -> 开 Pages -> 打印地址
set -u
cd "$(dirname "$0")"

TOK=$(printf "protocol=https\nhost=github.com\n\n" | git credential fill 2>/dev/null | sed -n 's/^password=//p')
if [ -z "${TOK:-}" ]; then echo "拿不到 GitHub 凭据（git credential fill 为空）"; exit 1; fi

REPO="awesome-world-model-memory"
OWNER="mngli-ai"

echo "[1/4] 检查仓库是否存在"
code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOK" \
  "https://api.github.com/repos/$OWNER/$REPO")
if [ "$code" = "404" ]; then
  echo "  创建仓库 $OWNER/$REPO"
  curl -s -X POST -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
    https://api.github.com/user/repos \
    -d "{\"name\":\"$REPO\",\"description\":\"世界模型回溯记忆调研图谱\",\"private\":false}" >/dev/null
elif [ "$code" != "200" ]; then
  echo "  GitHub API 返回 $code，先检查代理"; exit 1
fi

echo "[2/4] 推送 main"
git remote remove origin 2>/dev/null
git remote add origin "https://github.com/$OWNER/$REPO.git"
git push -u origin main 2>&1 | tail -3

echo "[3/4] 开启 GitHub Pages"
curl -s -X POST -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/pages" \
  -d '{"source":{"branch":"main","path":"/"}}' >/dev/null
curl -s -X POST -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/pages/builds" >/dev/null

echo "[4/4] 地址（首次要等 1-2 分钟构建）"
echo "  https://$OWNER.github.io/$REPO/"
