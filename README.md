# Hyundai KSA x Dengage demo

A working, bilingual demonstration site themed on publicly available Hyundai
Saudi Arabia content, with the Dengage customer experience data platform
layered in.

Live site, once GitHub Pages is enabled for this repository:

```
https://dengage-presales.github.io/hyundaiKSA/
```

## What is in this repository

| Path | What it is |
|---|---|
| `index.html`, `en/`, `ar/` | The demo site: root gateway plus the Mynaghi journeys in English and Arabic |
| `js/`, `assets/` | The site code, the Dengage engagement layer, fonts, imagery |
| `panel/` | Dengage panel content for the demo campaigns, with channel copy |
| `supabase/` | SQL for the synthetic vehicle dataset used in the remote-data demonstration |

## Run it locally

```bash
python3 -m http.server 8080
# open http://localhost:8080/
```

Serve from the repository root so relative paths resolve the way they do on
Pages. Web push needs the published origin; everything else works locally.

Add `?debug=1` to any page URL for a live readout of every event the page
sends to Dengage, with its payload and destination table.

## Publishing

GitHub Pages publishes the `main` branch directly: Settings, Pages, Source is
"Deploy from a branch" with `main` and the root folder selected. Every push to
`main` goes live by itself. The workflow in `.github/workflows/pages.yml` is a
manual-dispatch fallback that only applies if the source is ever switched back
to "GitHub Actions".

## Notes

- This is a Dengage product demonstration using publicly available content.
  It is not affiliated with or endorsed by Hyundai.
- No form on this site sends data to any backend. Form submissions only mint
  a demo contact key and fire Dengage demo events.
- No credentials live in this repository. The Dengage account and application
  identifiers in the pages are public by design: they ship in the HTML of
  every site that uses the SDK.
- The vehicle dataset under `supabase/` is entirely synthetic and announces
  itself as such (DEMO VINs, a fictional 555 mobile block, demo contact keys).
- Hyundai's own web fonts are committed for visual fidelity. Deleting
  `assets/fonts/*.otf` falls the site back to the metric-matched Arial stack
  that Hyundai's own CSS declares, with no layout shift.
