#!/bin/bash
# Publish notes-vs-me to GitHub.
# Prerequisite: a GitHub personal access token with repo scope
#   -> github.com/settings/tokens (classic, "repo" scope is enough)
# Run:  GH_TOKEN=ghp_xxxx bash scripts/publish.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${GH_TOKEN:-}" ]; then
  echo "Usage: GH_TOKEN=ghp_xxxx bash scripts/publish.sh"
  exit 1
fi

USER_NAME=$(curl -s -H "Authorization: token $GH_TOKEN" https://api.github.com/user | python3 -c "import sys,json;print(json.load(sys.stdin)['login'])")
echo "Authenticated as $USER_NAME"

REPO="notes-vs-me"
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $GH_TOKEN" "https://api.github.com/repos/$USER_NAME/$REPO" | grep -q 200 \
  || curl -s -X POST -H "Authorization: token $GH_TOKEN" https://api.github.com/user/repos \
       -d "{\"name\":\"$REPO\",\"description\":\"Local study griller: PDFs in, exam questions out. Open weights, notes never leave the laptop.\",\"private\":false}" > /dev/null
echo "repo ready: github.com/$USER_NAME/$REPO"

git remote add origin "https://$USER_NAME:$GH_TOKEN@github.com/$USER_NAME/$REPO.git" 2>/dev/null \
  || git remote set-url origin "https://$USER_NAME:$GH_TOKEN@github.com/$USER_NAME/$REPO.git"
git push -u origin main
git remote set-url origin "https://github.com/$USER_NAME/$REPO.git"   # strip token from .git/config
echo "Pushed. Public URL: https://github.com/$USER_NAME/$REPO"
