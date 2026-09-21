#!/usr/bin/env bash
# Apply Frappe-first nginx routing for erpgenex.local.site / 192.168.1.2
# so every app www/ works without frontend/erpgenex-web.
set -euo pipefail
NGINX_CONF="${1:-/home/frappeuser/frappe-bench/config/nginx.conf}"
BACKUP="${NGINX_CONF}.bak.frappe-first.$(date +%Y%m%d%H%M%S)"

if [[ ! -f "$NGINX_CONF" ]]; then
  echo "nginx.conf not found: $NGINX_CONF" >&2
  exit 1
fi

cp -a "$NGINX_CONF" "$BACKUP"
python3 - <<'PY' "$NGINX_CONF"
import re, sys
from pathlib import Path
path = Path(sys.argv[1])
text = path.read_text()

# Replace Next-backed location / inside the erpgenex.local.site / 192.168.1.2 server only.
# Match the first occurrence after server_name ... 192.168.1.2
marker = "192.168.1.2"
idx = text.find(marker)
if idx < 0:
    raise SystemExit("server block for 192.168.1.2 not found")

# Find location / { proxy_pass http://erpgenex-web; ... } after this server_name
rest = text[idx:]
pat = re.compile(
    r"location /\s*\{\s*\n\s*proxy_pass http://erpgenex-web;.*?^\t\}",
    re.M | re.S,
)
m = pat.search(rest)
if not m:
    # already frappe?
    if "Frappe-first public site" in rest[:8000] or "proxy_pass  http://frappe-bench-frappe" in rest[:4000]:
        print("OK: already Frappe-first or no Next location / found after 192.168.1.2")
        raise SystemExit(0)
    raise SystemExit("Could not find Next location / block after 192.168.1.2")

replacement = """# ── ERPGenex Frappe-first public site (app-owned www/) ── AUTO
\tlocation / {
\t\tproxy_http_version 1.1;
\t\tproxy_set_header X-Forwarded-For $remote_addr;
\t\tproxy_set_header X-Forwarded-Proto $scheme;
\t\tproxy_set_header X-Frappe-Site-Name erpgenex.local.site;
\t\tproxy_set_header Host $host;
\t\tproxy_set_header X-Use-X-Accel-Redirect True;
\t\tproxy_read_timeout 120;
\t\tproxy_redirect off;
\t\tproxy_pass http://frappe-bench-frappe;
\t}"""

new_rest = pat.sub(replacement, rest, count=1)
new_text = text[:idx] + new_rest
path.write_text(new_text)
print(f"Patched {path}")
PY

echo "Backup: $BACKUP"
nginx -t
sudo systemctl reload nginx || sudo service nginx reload
echo "Done — public / now serves Frappe app www/"
