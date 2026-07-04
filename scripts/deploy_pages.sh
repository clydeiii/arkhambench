#!/usr/bin/env bash
# Redeploy the viewer (with current viewer/data exports) to GitHub Pages.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

git branch -D gh-pages-src 2>/dev/null || true
git subtree split -P viewer -b gh-pages-src
git push -f origin gh-pages-src:gh-pages
git branch -D gh-pages-src
echo "Deployed. Site: https://clydeiii.github.io/arkhambench/ (Pages rebuild takes ~1 min)"
