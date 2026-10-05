#!/bin/bash
# Update the published DEV post (article id 4799035) with the current dev-post-final.md.
# Usage: DEV_KEY=xxxx bash scripts/update_post.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'EOF'
import json, os, pathlib
body = pathlib.Path("dev-post-final.md").read_text()
payload = {"article": {"body_markdown": body}}
pathlib.Path("/tmp/dev-article-update.json").write_text(json.dumps(payload))
EOF
curl -s -X PUT https://dev.to/api/articles/4799035 \
  -H "api-key: $DEV_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/dev-article-update.json | python3 -c "import sys,json;d=json.load(sys.stdin);print('UPDATED:',d.get('url') or d)"
