# The Dengage panel pack for the Hyundai KSA demo

Everything in this folder is pasted into the Dengage panel by a person, once,
before the Sunday rehearsal. About 30 to 45 minutes end to end. Nothing here
touches the shared `dengage_demo_` campaigns, tables or contacts, and nothing
in this repository deletes anything in Dengage, ever.

The demo works without this folder: the launcher's platform library fires the
17 shared campaigns as-is. What this folder adds is the Hyundai-specific set
the demo leads with.

## 1. The ten Hyundai campaigns

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
| `hyundai_demo_test-drive-rescue` | `creatives/test-drive-rescue.html` | Popup |
| `hyundai_demo_national-day`      | `creatives/national-day.html`      | Popup |
| `hyundai_demo_finance-teaser`    | `creatives/finance-teaser.html`    | Sticky bar (bottom) |
| `hyundai_demo_service-due`       | `creatives/service-due.html`       | Slide-in |
| `hyundai_demo_launch-bar`        | `creatives/launch-bar.html`        | Sticky bar (top) |
| `hyundai_demo_warranty-expiry`   | `creatives/warranty-expiry.html`   | Slide-in or bar |
| `hyundai_demo_arrival-alert`     | `creatives/arrival-alert.html`     | Popup |
| `hyundai_demo_post-service-nps`  | `creatives/post-service-nps.html`  | Popup |
| `hyundai_demo_ramadan-offer`     | `creatives/ramadan-offer.html`     | Popup |
| `hyundai_demo_newsletter-hy`     | `creatives/newsletter-hy.html`     | Popup |

Three facts about these creatives, learned the hard way on the factory side:

- They render in a cross-origin iframe, so links carry `target="_top"`, there
  are no script tags (the panel strips them on save), and capture goes through
  the engine's own `data-dn-form-id` inputs with `Dn.postSubscription()` and
  `Dn.postQuestion()`.
- The two capture cards (`arrival-alert`, `newsletter-hy`) get a `DPS-` contact
  key minted by the storefront before the popup can appear, so the contact the
  engine creates carries the demo marker rather than an anonymous `sf_` key.
- The imagery is served from this demo's published origin, so the campaigns
  only look right once GitHub Pages is live.

**Verify** after pasting: open the demo, open the launcher, fire each Hyundai
card once. A card that fires with nothing appearing means the campaign is
missing, inactive, or its event name differs from the table. Nothing errors:
a missing campaign is always silent.

## 2. Push on booking, the "seconds later" moment

The run of show books a test drive and a push arrives moments later. That is
one journey:

1. Journeys > new journey, trigger on the **order event**
   (`order_events`, the storefront sends it when the booking form is
   submitted; order ids look like `DPS-hyundaiksa-td-...`).
2. One step: **Web Push**.
   Title: `Booking confirmed`
   Message: `Your TUCSON test drive is set. We will call to agree the time.`
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
`dps_product`) now carries three Hyundai DMS tables, seeded by
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
| Tucson owners, Jeddah | `model_id = tucson` and `city = Jeddah` | 24 |
| High lifetime value | `lifetime_value_sar >= 5000` | 86 |

Eight rows are presenter-typeable contacts, engineered for the demo:

- `DPS-1` Tucson owner in Jeddah whose warranty ends in 45 days
- `DPS-2` Accent owner whose service is 110 days overdue
- `DPS-3` Palisade owner with SAR 18,400 lifetime value
- `DPS-4` Santa Fe owner due for service in 4 weeks

Open the demo with `?ck=DPS-1` and the browser session becomes that
customer: their web behaviour lands on the same contact card the DMS row
joins to. That is the unified-profile moment.

## 5. Message copy for every channel

`messages.html` in this folder renders the push, SMS, WhatsApp and email
copy for the demo scenarios, in English and Arabic, each with a copy button.
Open it straight from disk. Use it during the paste session and on the call
whenever a channel needs prose.

## 6. Verifying without the panel

From any machine, the public campaign surface every visitor's browser reads:

```
curl -s https://pcdn.dengage.com/p/push/28/99d9b8fb-0c62-5a85-3e43-2402554d93a5/dengage_sdk_loader.js | head -c 200
```

answers "is the SDK serving". Whether a specific campaign is live is read in
the panel's campaign list; a fired card that shows nothing is the fastest
honest signal.
