#!/usr/bin/env bash
# Regression: every example -> HTML/PNG + PPTX on the given template(s). Fails on any [FAIL] / missing text.
# usage: bash tests/run_examples.sh OUT_DIR TEMPLATE.pptx [TEMPLATE2.pptx ...]
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"; OUT="$1"; shift; mkdir -p "$OUT/QA"; rc=0
for spec in "$HERE"/examples/*.py; do
  n=$(basename "$spec" .py)
  python3 "$HERE/scripts/make_html.py" --spec "$spec" --out "$OUT/$n.html" --png "$OUT/$n.png" | grep -q '\[png\] .*png$' \
    && echo "ok   html  $n" || { echo "FAIL html  $n"; rc=1; }
  for t in "$@"; do
    tn=$(basename "$t" .pptx | tr -c 'A-Za-z0-9' '_' | cut -c1-20)
    log=$(python3 "$HERE/scripts/make_pptx.py" --spec "$spec" --template "$t" --out "$OUT/${n}_${tn}.pptx" --qa-dir "$OUT/QA" --ea-font "PingFang SC" 2>&1)
    if echo "$log" | grep -q 'All validations PASSED' && echo "$log" | grep -q '\[lint\] OK' \
       && echo "$log" | grep -q 'missing in PPTX: none' && ! echo "$log" | grep -q '\[FAIL\]'; then
      echo "ok   pptx  $n / $tn"
    else echo "FAIL pptx  $n / $tn"; echo "$log" | tail -5; rc=1; fi
  done
done
exit $rc
