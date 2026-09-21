#!/usr/bin/env bash
# Pull ErpGenEx apps from GitHub (PAT) and update all bench sites.
# Usage on external server:
#   export GITHUB_TOKEN='ghp_...'
#   bash apps/erpgenex_saas/deploy/update_erpgenex_bench.sh
set -euo pipefail

BENCH="${BENCH:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$BENCH"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
	echo "Set GITHUB_TOKEN (GitHub PAT with repo scope)." >&2
	exit 1
fi

AUTH="https://x-access-token:${GITHUB_TOKEN}@github.com/ErpGenex"

pull_app() {
	local app="$1"
	local dir="apps/$app"
	[[ -d "$dir/.git" ]] || return 0
	local url
	url="$(git -C "$dir" remote get-url origin 2>/dev/null || true)"
	if [[ "$url" != *"github.com/ErpGenex/"* ]]; then
		return 0
	fi
	local repo="${url##*/}"
	repo="${repo%.git}"
	echo "==> pull $app ($repo)"
	git -C "$dir" fetch "$AUTH/${repo}.git" main
	git -C "$dir" checkout main 2>/dev/null || git -C "$dir" checkout -B main FETCH_HEAD
	git -C "$dir" merge --ff-only FETCH_HEAD
}

echo "Bench: $BENCH"

if [[ -f sites/apps.txt ]]; then
	while IFS= read -r app || [[ -n "$app" ]]; do
		app="${app// /}"
		[[ -n "$app" ]] || continue
		pull_app "$app" || echo "WARN: pull failed for $app" >&2
	done < sites/apps.txt
else
	for dir in apps/omnexa_* apps/erpgenex_*; do
		[[ -d "$dir/.git" ]] || continue
		pull_app "$(basename "$dir")" || true
	done
fi

echo "==> bench migrate (all sites)"
bench migrate

echo "==> bench build"
bench build --app omnexa_core || true
bench build --app erpgenex_saas || true

echo "==> clear-cache (all sites)"
bench --site all clear-cache

echo "==> restart"
bench restart || sudo supervisorctl restart all || true

echo "Done. Sites:"
ls -1 sites 2>/dev/null | grep -vE '^(assets|apps\.txt|apps\.json|common_site_config\.json)$' || true
