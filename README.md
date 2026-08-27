# D·Auto x Dengage demo

A working, bilingual demonstration site for **D·Auto**, a fictitious
automotive brand, with the Dengage customer experience data platform layered
in. Every model name, price, showroom, phone number and image on the site is
invented or generated for this demonstration; the brand exists only here, so
the same demo can be shown to any automotive prospect. It is not affiliated
with, and does not represent, any real car maker or distributor.

Live site:

```
https://dengage-presales.github.io/hyundaiKSA/
```

(The repository name predates the fictitious brand; renaming the repository —
for example to `d-auto-demo` — changes the URL and nothing else.)

## What is in this repository

| Path | What it is |
|---|---|
| `index.html`, `models/`, `offers/`, `service-booking/`, `contact-us/` | The English site at the root |
| `ar/` | The full Arabic (RTL) mirror |
| `js/`, `assets/` | The site code, the Dengage engagement layer, the D·Auto brand asset system |
| `panel/` | Dengage panel content for the demo campaigns, with channel copy |
| `supabase/` | SQL for the synthetic vehicle dataset used in the remote-data demonstration |
| `docs/` | Presales research and the demo runbook |

Typography is Outfit and Cairo from Google Fonts; all vehicle imagery is the
committed SVG brand-scene system under `assets/brand/`. Nothing on the site
is loaded from, or points at, any car maker's property.

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
to GitHub Actions.

## What the forms do

There is no backend. Submitting any form on the site does exactly one thing:
it identifies the visitor as a demo contact (a `DPS-` key) in the shared
Dengage presales application and fires the corresponding demo events. No form
data goes anywhere else. The SDK identifiers in the pages are public-by-design
values, not credentials.
