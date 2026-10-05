#!/bin/bash
# Redeploy the landing page to GitHub Pages (after changes to static/landing.html).
# Usage: bash scripts/deploy_pages.sh
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="Priyanshujha1320/notes-vs-me"
PAGES_DIR=$(mktemp -d)
cp static/landing.html "$PAGES_DIR/index.html"
# on Pages there is no /app backend — point the CTAs at the repo instead
sed -i '' 's|href="https://github.com/Priyanshujha1320/notes-vs-me"|href="https://github.com/Priyanshujha1320/notes-vs-me"|g' "$PAGES_DIR/index.html"
cd "$PAGES_DIR"
git init -q -b gh-pages
git add -A
git commit -q -m "Landing page"
git remote add origin "https://github.com/$REPO.git"
git push -f origin gh-pages
echo "Pushed. Live in ~1 min at https://priyanshujha1320.github.io/notes-vs-me/"
