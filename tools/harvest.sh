#!/usr/bin/env bash
# Fetch the source pages this replica is built from, into reference/ (gitignored).
# The pages are server-rendered, so the visible copy and every asset URL are
# present in the raw HTML without running any JavaScript.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="$ROOT/reference/html"
mkdir -p "$REF"

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

fetch () {
  local path="$1" name="$2"
  if [ -s "$REF/$name.html" ]; then
    echo "have    $name"
    return 0
  fi
  local code
  code=$(curl -sL -A "$UA" -o "$REF/$name.html" -w '%{http_code}' "https://hyundaiksa.com$path")
  echo "$code    $name  ($(du -h "$REF/$name.html" | cut -f1))"
  sleep 1
}

fetch "/ar"                                  "gateway.ar"
fetch "/en"                                  "gateway.en"
for lang in en ar; do
  fetch "/$lang/mynaghi"                     "home.$lang"
  fetch "/$lang/mynaghi/models/tucson"       "tucson.$lang"
  fetch "/$lang/mynaghi/models/santa-fe"     "santafe.$lang"
  fetch "/$lang/mynaghi/offers"              "offers.$lang"
  fetch "/$lang/mynaghi/offers/backtoschool" "campaign.$lang"
  fetch "/$lang/mynaghi/service-booking"     "service.$lang"
  fetch "/$lang/mynaghi/contact-us"          "contact.$lang"
done

echo
echo "Pages in $REF:"
ls -lh "$REF" | tail -n +2 | awk '{print "  " $9 "  " $5}'
