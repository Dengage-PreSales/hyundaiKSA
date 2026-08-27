# The Dengage panel pack for the D·Auto KSA demo

Everything in this folder is pasted into the Dengage panel by a person, once,
before the Sunday rehearsal. About 30 to 45 minutes end to end. Nothing here
touches the shared `dengage_demo_` campaigns, tables or contacts, and nothing
in this repository deletes anything in Dengage, ever.

The demo works without this folder: the launcher's platform library fires the
17 shared campaigns as-is. What this folder adds is the D·Auto-specific set
the demo leads with.

## 1. The ten D·Auto campaigns

Create each as a new On-Site campaign with a **custom HTML** content, pasting
the matching file from `creatives/`. Settings are identical apart from the
event name and content type:

```
Trigger              Data Layer Event
Event name           exactly as in the table below
Where to display     /hyundaiKSA/
Status               Active
```

The display rule is what guarantees these can never appear on any other demo
sharing this Dengage application.

| Event name | Paste | Content type |
|---|---|---|
| `dauto_demo_test-drive-rescue` | `creatives/test-drive-rescue.html` | Popup |
| `dauto_demo_national-day`      | `creatives/national-day.html`      | Popup |
| `dauto_demo_finance-teaser`    | `creatives/finance-teaser.html`    | Sticky bar (bottom) |
| `dauto_demo_service-due`       | `creatives/service-due.html`       | Slide-in |
| `dauto_demo_launch-bar`        | `creatives/launch-bar.html`        | Sticky bar (top) |
| `dauto_demo_warranty-expiry`   | `creatives/warranty-expiry.html`   | Slide-in or bar |
| `dauto_demo_arrival-alert`     | `creatives/arrival-alert.html`     | Popup |
| `dauto_demo_post-service-nps`  | `creatives/post-service-nps.html`  | Popup |
| `dauto_demo_ramadan-offer`     | `creatives/ramadan-offer.html`     | Popup |
| `dauto_demo_newsletter-capture`     | `creatives/newsletter-capture.html`     | Popup |

Three facts about these creatives, learned the hard way on the factory side:

- They render in a cross-origin iframe, so links carry `target="_top"`, there
  are no script tags (the panel strips them on save), and capture goes through
  the engine's own `data-dn-form-id` inputs with `Dn.postSubscription()` and
  `Dn.postQuestion()`.
- The two capture cards (`arrival-alert`, `newsletter-capture`) get a `DPS-` contact
  key minted by the storefront before the popup can appear, so the contact the
  engine creates carries the demo marker rather than an anonymous `sf_` key.
- The imagery is served from this demo's published origin, so the campaigns
  only look right once GitHub Pages is live.

**Verify** after pasting: open the demo, open the launcher, fire each D·Auto
card once. A card that fires with nothing appearing means the campaign is
missing, inactive, or its event name differs from the table. Nothing errors:
a missing campaign is always silent.

## 2. Push on booking, the "seconds later" moment

The run of show books a test drive and a push arrives moments later. That is
one journey:

1. Journeys > new journey, trigger on the **order event**
   (`order_events`, the storefront sends it when the booking form is
   submitted; order ids look like `DPS-D·Autoksa-td-...`).
2. One step: **Web Push**.
   Title: `Booking confirmed`
   Message: `Your VANTA test drive is set. We will call to agree the time.`
   Arabic variant: `تم تأكيد حجز تجربة القيادة، سنتصل بك لتحديد الموعد.`
3. Audience: everyone (the trigger scopes it); frequency capping off for the
   demo.

The presenting browser must have accepted the push prompt first (the
launcher's Web push card raises it).

## 3. The abandoned booking rescue

The shared abandoned-cart journey may already cover this (the storefront
sends `beginCheckout` when the booking form opens and no order when it is
abandoned). At the Sunday rehearsal, run the flow once and wait for the
rescue message. If nothing arrives, either wire a journey on
`shopping_cart_events` begin-checkout with a 1 minute wait and an
email/push step, or show the journey canvas and send a manual campaign
instead. Do not present an unverified automation.

## 4. Remote data: the DMS tables

The Supabase Postgres this account already reads (the same one behind
`dps_product`) now carries three D·Auto DMS tables, seeded by
`supabase/seed.sql` in this repository:

| Table | What it holds |
|---|---|
| `hy_customer_vehicle` | 300 synthetic ownership records: model, VIN, warranty end, last and next service, odometer, lifetime value |
| `hy_service_history`  | Their workshop visits |
| `hy_branch`           | Branch coordinates for the geofence scene |

Wire them the same way `dps_product` is wired (remote source over the
existing Postgres connection), then build **remote segments** on
`hy_customer_vehicle`:

| Segment to create | Filter | Size in the data |
|---|---|---|
| Warranty expiring 60 days | `warranty_end` within 60 days of today | 10 |
| Service overdue | `next_service_due` before today | 162 |
| Vanta owners, Jeddah | `model_id = vanta` and `city = Jeddah` | 24 |
| High lifetime value | `lifetime_value_sar >= 5000` | 86 |

Eight rows are presenter-typeable contacts, engineered for the demo:

- `DPS-1` Vanta owner in Jeddah whose warranty ends in 45 days
- `DPS-2` Pulse owner whose service is 110 days overdue
- `DPS-3` Summit owner with SAR 18,400 lifetime value
- `DPS-4` Ridge owner due for service in 4 weeks

Open the demo with `?ck=DPS-1` and the browser session becomes that
customer: their web behaviour lands on the same contact card the DMS row
joins to. That is the unified-profile moment.

## 5. Message copy for every channel

`messages.html` in this folder renders the push, SMS, WhatsApp and email
copy for the demo scenarios and the wider ownership lifecycle — saved-car
updates, purchase anniversary, geofence welcome, registration renewal,
service winback, safety recall, test-drive reschedule, delivery day and
accessories — in English and Arabic, each with a copy button. Open it
straight from disk or at the published `/panel/messages.html`. Use it
during the paste session and on the call whenever a channel needs prose.

## 6. Verifying without the panel

From any machine, the public campaign surface every visitor's browser reads:

```
curl -s https://pcdn.dengage.com/p/push/28/99d9b8fb-0c62-5a85-3e43-2402554d93a5/dengage_sdk_loader.js | head -c 200
```

answers "is the SDK serving". And this one answers "did the pastes land" —
it downloads the campaign manifest the SDK actually reads (the filename is
inside the loader; note the `/onsite/` segment in its path) and lists every
D·Auto trigger it carries:

```
BASE=https://pcdn.dengage.com/p/push/28/99d9b8fb-0c62-5a85-3e43-2402554d93a5
curl -s "$BASE/onsite/$(curl -s $BASE/dengage_sdk_loader.js | grep -o 'campaigns\.[a-z0-9]*\.js')" \
  | grep -o 'dauto_demo_[a-z-]*' | sort -u
```

All ten trigger names from the table in section 1 should print. Before the
paste session it prints nothing — that is the "not pasted yet" reading, not
an error. Whether a campaign is also configured correctly is read in the
panel's campaign list; a fired card that shows nothing is the fastest honest
signal.

## 7. The automotive event dictionary

The demo deliberately speaks the panel's standard ecommerce language, so
every existing journey, RFM view and segment works unchanged: a model page
is a product view, a test-drive request is an add-to-cart, a confirmed
booking is an order. That mapping is live on the site today. In production
the same moments graduate to named automotive events — custom big-data
tables joined on the contact key, fed by the web SDK, the mobile SDK, or a
batch from the DMS — and segments mix them freely with web behaviour and
the remote DMS tables from section 4.

| Business moment | Live in this demo today | Production event definition | Fed by |
|---|---|---|---|
| Model page viewed | `page_view_events` (page_type=product, product_id, price) | `vehicle_page_views` + trim, fuel_type | Web SDK |
| Model searched / filtered | `ec:search` | same, plus filter payload | Web SDK |
| Car saved | `wishlist_events` | `saved_vehicles` | Web SDK |
| Test drive requested | `ec:addToCart` (model as line) | `test_drive_requests`: model_id, trim, branch_id, preferred_slot, source | Web SDK / API |
| Booking form opened | `ec:beginCheckout` | funnel step on the same table | Web SDK |
| Test drive booked | `ec:order`, order id `DPS-D·Autoksa-td-*` | `test_drive_bookings`: booking_id, model_id, branch_id, slot | Web SDK / API |
| Test drive completed or no-show | — (post-visit) | `test_drive_outcomes`: booking_id, outcome, advisor | CRM/DMS batch |
| Quote or finance requested | contact created (DPS- key) | `finance_applications`: model_id, amount, status | API |
| Service booked | service form submit (contact story) | `service_bookings`: vin, branch_id, service_type, slot | Web SDK / API |
| Service visit completed | `hy_service_history` remote table, live | `service_visits` batch | DMS |
| Warranty position | `hy_customer_vehicle.warranty_end`, live | same remote read | DMS |
| Delivery scheduled / handed over | — | `vehicle_deliveries`: vin, branch_id, dates | DMS / API |
| Showroom visited | branch geocoords ready in `hy_branch` | geofence enter/exit events | Mobile SDK |
| Recall opened / closed | — | `vehicle_recalls`: vin, campaign_no, status | DMS batch |
| NPS submitted | survey campaign writes tags, live | `nps_responses`: score, visit_id | Web/Mobile SDK |

The left two columns are what Monday shows working; the right two are the
definition conversation with the CRM team, using their own vocabulary.

## 8. Channel coverage in one view

| Channel | State in this demo |
|---|---|
| On-site messages | Live: popups, bars, slide-ins, exit-intent and scroll gestures, A/B, gamified, story |
| Inline on-page | Live: five placement zones across home and model pages |
| App inbox | Live: bell drawer on every page, welcome + National Day copy ready |
| Web push | Live: prompt, origin service worker `/dengage-webpush-sw.js`, booking + rescue + service copy |
| SMS | Copy ready (section 5), CST-conscious with STOP opt-out; sender id needed to send |
| WhatsApp | Copy ready incl. reschedule, delivery day, service confirmation; WABA needed to send |
| Email | Subject and preheader pairs ready; journey nodes shown in the flow canvas |
| Geofence | Branch coordinates seeded (section 4); fires via the mobile SDK narrative |
| RCS | Not offered — say so if asked |
