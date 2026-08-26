#!/usr/bin/env python3
"""Delete every file under assets/img/cdn that no built page references.

The harvest deliberately over-collects (every size variant and payload URL in
the captures); the built pages reference the exact files they need. Keeping
only those brings the repository to a committable weight. Reference set =
all page HTML plus the site CSS.
"""
import pathlib
import re
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
CDN = ROOT / "assets" / "img" / "cdn"

referenced = set()
sources = list(ROOT.glob("*.html")) + list(ROOT.glob("en/**/*.html")) + \
          list(ROOT.glob("ar/**/*.html")) + list((ROOT / "assets" / "css").rglob("*.css")) + \
          list((ROOT / "js").glob("*.js"))
for f in sources:
    t = f.read_text(errors="ignore")
    # Parentheses are part of their filenames (image-(8).png); only quotes,
    # whitespace and angle brackets delimit a reference in markup.
    for m in re.finditer(r"assets/img/cdn/([^\s\"'<>]+)", t):
        path = urllib.parse.unquote(m.group(1).split("&quot")[0]).rstrip("),;")
        referenced.add(path)

kept = 0
kept_bytes = 0
dropped = 0
for f in sorted(CDN.rglob("*")):
    if not f.is_file():
        continue
    rel = str(f.relative_to(CDN))
    if rel in referenced:
        kept += 1
        kept_bytes += f.stat().st_size
    else:
        f.unlink()
        dropped += 1

# Empty directories go too.
for d in sorted([p for p in CDN.rglob("*") if p.is_dir()], reverse=True):
    try:
        d.rmdir()
    except OSError:
        pass

print(f"referenced: {len(referenced)}, kept: {kept} ({kept_bytes // (1024*1024)} MB), deleted: {dropped}")
missing = [r for r in sorted(referenced) if not (CDN / r).exists()]
print(f"referenced but missing: {len(missing)}")
for m in missing[:12]:
    print("  MISSING", m)
