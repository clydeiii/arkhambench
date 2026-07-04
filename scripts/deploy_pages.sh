#!/usr/bin/env bash
# Redeploy the viewer (with current exports AND the local card-image cache) to
# GitHub Pages. The image cache stays out of main (gitignored) but ships with
# the site so first loads don't depend on arkhamdb hotlink throttling.
# Card images (c) FFG, served the same way community sites like arkhamdb do.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 scripts/fetch_card_images.py >/dev/null || echo "warning: image cache refresh failed" >&2

REMOTE_URL="$(git remote get-url origin)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp -R viewer/. "$TMP/"

git -C "$TMP" init -q -b gh-pages
git -C "$TMP" -c user.name="Clyde" -c user.email="clydeiii@gmail.com" add -A
git -C "$TMP" -c user.name="Clyde" -c user.email="clydeiii@gmail.com" commit -q -m "Deploy viewer $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git -C "$TMP" push -q -f "$REMOTE_URL" gh-pages:gh-pages

echo "Deployed. Site: https://clydeiii.github.io/arkhambench/ (Pages rebuild takes ~1 min)"
