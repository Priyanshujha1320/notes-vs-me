#!/bin/bash
# One-shot: push main, deploy landing page to GitHub Pages, publish DEV post.
# Usage: DEV_KEY=xxxx bash scripts/go_live.sh
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="Priyanshujha1320/notes-vs-me"
GH="$HOME/bin/gh"

echo "== 1/3 push main =="
git remote add origin "https://github.com/$REPO.git" 2>/dev/null \
  || git remote set-url origin "https://github.com/$REPO.git"
git push -u origin main

echo "== 2/3 deploy landing page to GitHub Pages =="
PAGES_DIR=$(mktemp -d)
cp static/landing.html "$PAGES_DIR/index.html"
# on Pages there is no /app backend — point the CTAs at the repo instead
sed -i '' 's|href="/app"|href="https://github.com/'"$REPO"'#readme"|g' "$PAGES_DIR/index.html"
cd "$PAGES_DIR"
git init -q -b gh-pages
git add -A
git commit -q -m "Landing page"
git remote add origin "https://github.com/$REPO.git"
git push -f origin gh-pages
cd - > /dev/null
"$GH" api -X POST "repos/$REPO/pages" \
  -f 'source[branch]=gh-pages' -f 'source[path]=/' 2>/dev/null \
  || echo "(Pages already enabled — fine)"
echo "Landing page will be live at https://priyanshujha1320.github.io/notes-vs-me/ (give it 1-2 min)"

echo "== 3/3 publish DEV post =="
python3 - <<'EOF'
import json, os, pathlib
body = pathlib.Path("dev-post-final.md").read_text()
payload = {
    "article": {
        "title": "I built an AI examiner that reads my friend's notes — without the notes ever leaving their laptop",
        "published": True,
        "body_markdown": body,
        "tags": ["devchallenge", "weekendchallenge", "hf26challenge"],
    }
}
pathlib.Path("/tmp/dev-article.json").write_text(json.dumps(payload))
EOF
curl -s -X POST https://dev.to/api/articles \
  -H "api-key: $DEV_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/dev-article.json | python3 -c "import sys,json;d=json.load(sys.stdin);print('PUBLISHED:',d.get('url') or d)"

echo "ALL DONE"
