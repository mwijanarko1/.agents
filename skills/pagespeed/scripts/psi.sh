#!/usr/bin/env bash
# PageSpeed Insights runner — never prints the API key.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: psi.sh <url> [mobile|desktop|both] [categories]
  categories: comma list performance,accessibility,best-practices,seo
  default categories: all four
EOF
  exit 1
}

[[ $# -lt 1 ]] && usage

URL="$1"
STRATEGY="${2:-both}"
CATEGORIES="${3:-performance,accessibility,best-practices,seo}"

KEY_FILE="${PAGESPEED_API_KEY_FILE:-$HOME/.config/pagespeed/api_key}"
KEY="${PAGESPEED_API_KEY:-${GOOGLE_API_KEY:-}}"

if [[ -z "$KEY" && -f "$KEY_FILE" ]]; then
  KEY="$(tr -d '[:space:]' <"$KEY_FILE")"
fi

if [[ -z "$KEY" ]]; then
  echo "error: no API key. Put it in $KEY_FILE (chmod 600) or set PAGESPEED_API_KEY" >&2
  exit 2
fi

# Refuse to run if caller is trying to dump the key via xtrace
if [[ -n "${SHELLOPTS:-}" && "$SHELLOPTS" == *xtrace* ]]; then
  echo "error: refuse to run under set -x (would leak key)" >&2
  exit 3
fi

API="https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

run_one() {
  local strat="$1"
  local qs="url=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$URL")"
  qs+="&strategy=${strat}"
  IFS=',' read -ra cats <<<"$CATEGORIES"
  for c in "${cats[@]}"; do
    c="$(echo "$c" | tr -d '[:space:]')"
    [[ -n "$c" ]] && qs+="&category=${c}"
  done

  # key only on curl argv to Google — never echo
  local tmp
  tmp="$(mktemp)"
  local code
  code="$(curl -sS -o "$tmp" -w '%{http_code}' "${API}?${qs}&key=${KEY}")" || true

  if [[ "$code" != "200" ]]; then
    # strip any accidental key from error bodies
    python3 - "$tmp" "$code" "$strat" <<'PY'
import json,sys,re
path,code,strat=sys.argv[1:4]
raw=open(path).read()
raw=re.sub(r'key=[^&\s"]+','key=REDACTED',raw)
try:
    err=json.loads(raw)
    msg=err.get("error",{}).get("message", raw[:300])
except Exception:
    msg=raw[:300]
print(json.dumps({"strategy":strat,"ok":False,"http":int(code),"error":msg}))
PY
    rm -f "$tmp"
    return 1
  fi

  python3 - "$tmp" "$strat" <<'PY'
import json,sys
path,strat=sys.argv[1:3]
j=json.load(open(path))
lr=j.get("lighthouseResult") or {}
aud=lr.get("audits") or {}
cats=lr.get("categories") or {}

def audit(aid):
    a=aud.get(aid) or {}
    if not a: return None
    return {"display": a.get("displayValue"), "score": a.get("score")}

def cat_score(name):
    c=cats.get(name) or {}
    s=c.get("score")
    return None if s is None else round(s*100)

def field(block):
    if not block: return None
    metrics=block.get("metrics") or {}
    out={"overall": block.get("overall_category")}
    for k,v in metrics.items():
        out[k]={"percentile": v.get("percentile"), "category": v.get("category")}
    return out

out={
  "strategy": strat,
  "ok": True,
  "finalUrl": lr.get("finalDisplayedUrl") or lr.get("finalUrl"),
  "fetchTime": lr.get("fetchTime"),
  "scores": {k: cat_score(k) for k in cats.keys()},
  "metrics": {
    "FCP": audit("first-contentful-paint"),
    "LCP": audit("largest-contentful-paint"),
    "TBT": audit("total-blocking-time"),
    "CLS": audit("cumulative-layout-shift"),
    "SI": audit("speed-index"),
    "TTI": audit("interactive"),
    "INP": audit("interaction-to-next-paint"),
  },
  "field": field(j.get("loadingExperience")),
  "originField": field(j.get("originLoadingExperience")),
}
print(json.dumps(out, indent=2))
PY
  rm -f "$tmp"
}

case "$STRATEGY" in
  mobile|MOBILE) run_one mobile ;;
  desktop|DESKTOP) run_one desktop ;;
  both|BOTH)
    run_one mobile || true
    run_one desktop || true
    ;;
  *) usage ;;
esac
