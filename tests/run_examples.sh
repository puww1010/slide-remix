#!/usr/bin/env bash
# Regression: doctor, then every example -> HTML/PNG + PPTX on the given template(s). Fails on any [FAIL] / missing text.
# usage: bash tests/run_examples.sh OUT_DIR [TEMPLATE.pptx ...]     (no template -> bundled demo template)
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-/tmp/slide-remix-reg}"; shift || true; mkdir -p "$OUT/QA"; rc=0
TEMPLATES=("$@"); [ ${#TEMPLATES[@]} -eq 0 ] && TEMPLATES=("demo")
python3 "$HERE/scripts/doctor.py" --need html,pptx || { echo "FAIL doctor: required tools missing (see above)"; exit 1; }
for spec in "$HERE"/examples/*.py; do
  n=$(basename "$spec" .py)
  src=(); [ -f "$HERE/examples/$n.source.txt" ] && src=(--source "$HERE/examples/$n.source.txt")
  hlog=$(python3 "$HERE/scripts/make_html.py" --spec "$spec" --out "$OUT/$n.html" --png "$OUT/$n.png" "${src[@]}" 2>&1); hc=$?
  if [ $hc -eq 0 ] && ! echo "$hlog" | grep -q "missing from page: \["; then echo "ok   html  $n"
  elif [ $hc -eq 2 ]; then echo "warn html  $n (HTML ok, PNG failed: $(echo "$hlog" | grep '\[png\]' | cut -c1-120))"
  else echo "FAIL html  $n"; echo "$hlog" | tail -3; rc=1; fi
  for t in "${TEMPLATES[@]}"; do
    tn=$(basename "$t" .pptx | tr -c 'A-Za-z0-9' '_' | cut -c1-20)
    log=$(python3 "$HERE/scripts/make_pptx.py" --spec "$spec" --template "$t" --out "$OUT/${n}_${tn}.pptx" --qa-dir "$OUT/QA" --ea-font "PingFang SC" 2>&1); pc=$?
    if [ $pc -eq 0 ] && echo "$log" | grep -q '\[validate[^]]*\] .*PASSED' && echo "$log" | grep -q '\[lint\] OK' \
       && echo "$log" | grep -q 'missing in PPTX: none'; then
      echo "ok   pptx  $n / $tn$(echo "$log" | grep -q 'no preview render' && echo '  (no preview: LibreOffice/pdftoppm missing)')"
    else echo "FAIL pptx  $n / $tn"; echo "$log" | grep -E '^\[(FAIL|WARN)' | head -5; rc=1; fi
  done
done
exit $rc
