#!/usr/bin/env python3
"""Build the static replica pages from the hydrated captures.

Each page in reference/hydrated/ is transformed into a self-contained static
page: scripts and trackers removed, every asset rewritten to the committed
copy under assets/img/cdn/, links mapped to the pages this replica carries,
and the Dengage layer injected with the load-bearing head order (identity
first, SDK second, stylesheets after).
"""
import re
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parent.parent
HYD = ROOT / "reference" / "hydrated"
CDN_PREFIX = r"https://assets\.hyundai-me\.com/client-mynaghi-production/"

CSS_CHUNKS = [
    "1ro47j0m9_bpw", "1xd0wv4t3_w6f", "3ioh63cvv2q2g", "2me9zktabzrcz",
    "31qivdt-iwa4m", "1aoqx93wdvmqk", "1z_mbvpkjhpd5",
]

PAGES = {
    "gateway.ar": {"out": "index.html",                                "type": "other"},
    "gateway.en": {"out": "en/index.html",                             "type": "other"},
    "home.en":    {"out": "en/mynaghi/index.html",                     "type": "home"},
    "home.ar":    {"out": "ar/mynaghi/index.html",                     "type": "home"},
    "tucson.en":  {"out": "en/mynaghi/models/tucson/index.html",       "type": "product", "product": "tucson", "price": "101258", "cat": "SUV"},
    "tucson.ar":  {"out": "ar/mynaghi/models/tucson/index.html",       "type": "product", "product": "tucson", "price": "101258", "cat": "SUV"},
    "santafe.en": {"out": "en/mynaghi/models/santa-fe/index.html",     "type": "product", "product": "santa-fe", "price": "138429", "cat": "SUV"},
    "santafe.ar": {"out": "ar/mynaghi/models/santa-fe/index.html",     "type": "product", "product": "santa-fe", "price": "138429", "cat": "SUV"},
    "offers.en":  {"out": "en/mynaghi/offers/index.html",              "type": "promotion"},
    "offers.ar":  {"out": "ar/mynaghi/offers/index.html",              "type": "promotion"},
    "campaign.en": {"out": "en/mynaghi/offers/back-to-school/index.html", "type": "promotion", "promotion": "back-to-school"},
    "campaign.ar": {"out": "ar/mynaghi/offers/back-to-school/index.html", "type": "promotion", "promotion": "back-to-school"},
    "service.en": {"out": "en/mynaghi/service-booking/index.html",     "type": "other"},
    "service.ar": {"out": "ar/mynaghi/service-booking/index.html",     "type": "other"},
    "contact.en": {"out": "en/mynaghi/contact-us/index.html",          "type": "other"},
    "contact.ar": {"out": "ar/mynaghi/contact-us/index.html",          "type": "other"},
}

# Site routes that exist in the replica, per language, mapped to output paths.
ROUTES = {
    "": "index.html",
    "/mynaghi": "{lang}/mynaghi/index.html",
    "/mynaghi/models/tucson": "{lang}/mynaghi/models/tucson/index.html",
    "/mynaghi/models/santa-fe": "{lang}/mynaghi/models/santa-fe/index.html",
    "/mynaghi/offers": "{lang}/mynaghi/offers/index.html",
    "/mynaghi/offers/backtoschool": "{lang}/mynaghi/offers/back-to-school/index.html",
    "/mynaghi/service-booking": "{lang}/mynaghi/service-booking/index.html",
    "/mynaghi/contact-us": "{lang}/mynaghi/contact-us/index.html",
}

# The rest of the model range, generated: slug -> (live URL path, price in SAR
# from the model grid, category). Elantra's path is capitalised on the live
# site; staria-van's price is not published, so its page carries no price.
MODEL_PAGES = {
    "accent":         ("accent",         "71484",  "Sedan"),
    "azera":          ("azera",          "158436", "Sedan"),
    "elantra":        ("Elantra",        "86694",  "Sedan"),
    "grandi10":       ("grandi10",       "56239",  "Sedan"),
    "sonata":         ("sonata",         "107904", "Sedan"),
    "creta":          ("creta",          "86200",  "SUV"),
    "creta-grand":    ("creta-grand",    "102054", "SUV"),
    "kona":           ("kona",           "92544",  "SUV"),
    "palisade":       ("palisade",       "177039", "SUV"),
    "venue":          ("venue",          "77334",  "SUV"),
    "stargazer":      ("stargazer",      "79147",  "MPV"),
    "staria-premium": ("staria-premium", "180294", "MPV"),
    "staria-van":     ("staria-van",     None,     "MPV"),
    "staria-wagon":   ("staria-wagon",   "136224", "MPV"),
}
for _slug, (_path, _price, _cat) in MODEL_PAGES.items():
    for _lang in ("en", "ar"):
        _spec = {"out": f"{_lang}/mynaghi/models/{_path}/index.html",
                 "type": "product", "product": _slug, "cat": _cat}
        if _price:
            _spec["price"] = _price
        PAGES[f"{_slug}.{_lang}"] = _spec
    ROUTES[f"/mynaghi/models/{_path}"] = "{lang}/mynaghi/models/" + _path + "/index.html"


def rel_to_root(out_path: str) -> str:
    depth = out_path.count("/")
    return "../" * depth


def map_route(href: str, rel: str):
    """Return the local href for a site-internal path, or None if unbuilt."""
    clean = href.split("?")[0].split("#")[0].rstrip("/")
    m = re.match(r"^/(en|ar)(/.*)?$", clean)
    if not m:
        return None
    lang, rest = m.group(1), m.group(2) or ""
    if rest == "" and lang == "ar":
        return rel + "index.html"
    if rest == "" and lang == "en":
        return rel + "en/index.html"
    target = ROUTES.get(rest)
    if not target:
        return "DEAD"
    return rel + target.format(lang=lang)


def strip_scripts(t: str) -> str:
    t = re.sub(r"<script\b[^>]*>.*?</script>", "", t, flags=re.S)
    t = re.sub(r"<noscript\b[^>]*>.*?</noscript>", "", t, flags=re.S)
    t = re.sub(r"<next-route-announcer\b.*?</next-route-announcer>", "", t, flags=re.S)
    t = re.sub(r"<link[^>]+rel=\"(?:preload|modulepreload|prefetch|preconnect|dns-prefetch)\"[^>]*>", "", t)
    return t


def settle_inline_styles(t: str) -> str:
    """The capture freezes the scroll-reveal animation's inline styles. Settle
    ONLY elements the reveal system owns (their class carries move-*): the
    swiper carousels also drive opacity inline, and settling those stacks
    every slide of a fade carousel on top of each other."""
    def fix(match):
        tag = match.group(0)
        if "move-" not in tag and "data-animate" not in tag:
            return tag
        # The scroll-blur layers also ride the move- system; forcing those
        # visible blurs whole sections. They stay exactly as captured.
        if "blur" in tag:
            return tag
        def styles(m2):
            style = m2.group(1)
            style = re.sub(r"opacity:\s*0(?!\.)[^;\"]*;?", "opacity: 1;", style)
            style = re.sub(r"visibility:\s*hidden;?", "", style)
            style = re.sub(r"transform:\s*translate[^;\"]*;?", "", style)
            return 'style="' + style + '"'
        return re.sub(r'style="([^"]*)"', styles, tag)
    return re.sub(r"<[a-zA-Z][^>]*>", fix, t)


def strip_lazy_reservations(t: str) -> str:
    """Lazily-mounted sections reserve their live heights through inline
    content-visibility placeholders. With no script to mount the content the
    reservation is just a band of blank page, so both declarations go. Only
    style attributes are touched; the site CSS text stays as shipped."""
    def fix(m):
        style = m.group(1)
        if "content-visibility" not in style and "contain-intrinsic-size" not in style:
            return m.group(0)
        style = re.sub(r"content-visibility:\s*[^;\"]+;?", "", style)
        style = re.sub(r"contain-intrinsic-size:\s*[^;\"]+;?", "", style)
        return 'style="' + style + '"'
    return re.sub(r'style="([^"]*)"', fix, t)


def rewrite_assets(t: str, rel: str) -> str:
    t = t.replace("&amp;", "&")
    # Parentheses are legal and PRESENT in their filenames (image-(8).png), so
    # the path class must allow them; quotes, whitespace and angle brackets
    # still terminate, which is what actually delimits a URL in markup.
    # A bare & is ALSO legal in their filenames (exterior&interior.webp) and
    # stays in the path — but &quot;/&amp; entities terminate it, so an
    # inline-style url(&quot;...&quot;) still ends before the entity. Query
    # strings are the second group and are dropped.
    t = re.sub(CDN_PREFIX + r"((?:[^\s\"'<>?&]|&(?!quot;|amp;))+)(\?[^\s\"'<>]*)?",
               lambda m: rel + "assets/img/cdn/" + m.group(1), t)
    # Whatever still points at their _next tree cannot resolve here.
    t = re.sub(r"/_next/image\?url=([^\s\"'&]+)[^\s\"']*", r"\1", t)
    # The handful of images served from the site root rather than the CDN,
    # in every spelling they appear in: absolute to the live host, or
    # root-relative inside src AND srcset candidate lists.
    t = t.replace("https://hyundaiksa.com/images/", "/images/")
    t = re.sub(r"/images/([^\s\"'<>,?\\]+)(\?[^\s\"'<>,]*)?",
               lambda m: rel + "assets/img/site/" + m.group(1), t)
    return t


def ld_media(src: str):
    """Read the page's own JSON-LD: a map from every video URL to its declared
    thumbnail, and the ordered media list of the hero ItemList."""
    video_thumbs = {}
    hero_list = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            data = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        items = data.get("itemListElement") if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        ordered = []
        for entry in items:
            item = entry.get("item", {}) if isinstance(entry, dict) else {}
            content = item.get("contentUrl") or item.get("url")
            thumb = item.get("thumbnailUrl")
            if item.get("@type") == "VideoObject" and content and thumb:
                video_thumbs[content] = thumb
                ordered.append(thumb)
            elif content:
                ordered.append(content)
        if ordered and not hero_list:
            hero_list = ordered
    return video_thumbs, hero_list


def replace_videos(t: str, video_thumbs: dict) -> str:
    """A committed replica carries no multi-megabyte films. Each video element
    becomes its own declared thumbnail (from the page's JSON-LD), or its
    poster; one with neither disappears."""
    def swap(match):
        block = match.group(0)
        image = None
        for src_m in re.finditer(r'(?:src)="([^"]+\.mp4[^"]*)"', block):
            url = src_m.group(1).split("?")[0]
            if url in video_thumbs:
                image = video_thumbs[url]
                break
        if not image:
            poster = re.search(r'poster="([^"]+)"', block)
            image = poster.group(1) if poster else None
        if image:
            return ('<img src="' + image + '" alt="" '
                    'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:2">')
        return ""
    return re.sub(r"<video\b.*?</video>", swap, t, flags=re.S)


def backfill_hero_images(t: str, hero_list) -> str:
    """The hero carousel's second slide mounts its image lazily, so the capture
    can carry a slide with text and no media at all. Give every imageless
    banner-slide its JSON-LD medium, in position order."""
    if not hero_list:
        return t
    wrapper_at = t.find("banner-wrapper")
    if wrapper_at == -1:
        return t
    out = []
    last = 0
    index = 0
    for m in re.finditer(r'<div class="banner-slide[^"]*"[^>]*>', t):
        if m.start() < wrapper_at:
            continue
        if index >= len(hero_list):
            break
        # Look ahead inside this slide for an existing img.
        window = t[m.end():m.end() + 4000]
        slide_end = window.find("banner-slide")
        probe = window if slide_end == -1 else window[:slide_end]
        medium = hero_list[index]
        index += 1
        out.append(t[last:m.end()])
        if "<img" not in probe:
            out.append('<img src="' + medium + '" alt="" '
                       'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:2">')
        last = m.end()
    out.append(t[last:])
    return "".join(out)


def rewrite_links(t: str, rel: str) -> str:
    def fix(match):
        href = match.group(1)
        if href.startswith(("http", "tel:", "mailto:", "#", "javascript:")):
            return match.group(0)
        mapped = map_route(href, rel)
        if mapped is None:
            return match.group(0)
        if mapped == "DEAD":
            return 'href="#" data-demo-dead="1"'
        return 'href="' + mapped + '"'
    return re.sub(r'href="([^"]*)"', fix, t)


def wire_test_drive(t: str, product: str) -> str:
    """Every 'Book a Test Drive' affordance opens the funnel modal. The label
    is either the element's own text or, on the model pages, an aria-label
    with the visible text nested inside a span; both shapes get the hook."""
    def fix(match):
        tag = match.group(0)
        if "data-book-test-drive" in tag:
            return tag
        return tag[:-1] + ' data-book-test-drive="' + product + '">'
    for label in ("Book a Test Drive", "Book A Test Drive", "احجز تجربة قيادة",
                  "Schedule your Test Drive", "احجز تجربة القيادة",
                  "قم بحجز تجربة قيادة"):
        esc = re.escape(label)
        t = re.sub(r'<(?:a|button)\b[^>]*aria-label="' + esc + r'"[^>]*>', fix, t)
        t = re.sub(r"<(?:a|button)\b[^>]*>(?=[^<]*" + esc + ")", fix, t)
    return t


def head_block(name: str, spec: dict, title: str, description: str, rel: str,
               lang: str, body_attrs: str) -> str:
    css_links = "\n".join(
        f'<link rel="stylesheet" href="{rel}assets/css/site/{c}.css">' for c in CSS_CHUNKS
    )
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="noindex">
<link rel="icon" href="{rel}assets/favicon.ico">
<link rel="manifest" href="{rel}manifest.webmanifest">
<meta name="theme-color" content="#002c5f">

<!-- ORDER IN THE HEAD IS LOAD BEARING. identity.js resolves the contact key
     synchronously and must run before the SDK snippet initializes; both must
     run before any stylesheet, because a pending stylesheet blocks every
     script after it and a blocked corporate network must never be able to
     stop the SDK from starting. -->
<script src="{rel}js/identity.js"></script>
<!-- DENGAGE SDK START -->
<script>
  (function (window, document) {{
    window.dengage = window.dengage || function () {{
      (window.dengage.q = window.dengage.q || []).push(arguments);
    }};
    var accountId = '28';
    var appGuid = '99d9b8fb-0c62-5a85-3e43-2402554d93a5';
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://pcdn.dengage.com/p/push/' + accountId + '/' + appGuid + '/dengage_sdk_loader.js';
    document.getElementsByTagName('head')[0].appendChild(script);
    window.__dnInit ? window.dengage('initialize', window.__dnInit) : window.dengage('initialize');
  }})(window, document);
</script>
<!-- DENGAGE SDK END -->

{css_links}
<link rel="stylesheet" href="{rel}assets/css/fonts.css">
<link rel="stylesheet" href="{rel}assets/css/override.css">
<link rel="stylesheet" href="{rel}assets/css/demo-controls.css">"""


def mounts_block(rel: str, lang: str) -> str:
    ar = lang == "ar"
    launcher_label = "عرض دنقيج" if ar else "Dengage demo"
    inbox_label = "تحديثات هيونداي" if ar else "Hyundai updates"
    intro = ("شغّل أي تجربة على هذه الصفحة مباشرة. كل شيء يصل إلى لوحة دنقيج لحظة حدوثه."
             if ar else
             "Fire any experience on this page, live. Everything lands in the Dengage panel as it happens.")
    refresh = "تحديث" if ar else "Refresh"
    quickref = "مرجع سريع" if ar else "Quick reference"
    events_h = "أحداث المتجر" if ar else "Storefront events"
    events_p = ("أرسل حدث تجارة إلكترونية حقيقياً إلى دنقيج، تماماً كما يفعل الموقع نفسه."
                if ar else
                "Send a real ecommerce event to Dengage, exactly as the site itself does.")
    send = "إرسال الحدث" if ar else "Send event"
    reset = "إعادة تعيين حالة الودجات" if ar else "Reset widget display state"
    close = "إغلاق" if ar else "Close"
    scripts = "\n".join(
        f'<script src="{rel}js/{f}.js"></script>'
        for f in ["config", "copy", "vehicles", "dengageEvents", "site",
                  "panels", "slots", "inbox", "debug"]
    )
    return f"""
<!-- ==================== Dengage demo layer ==================== -->
<div class="scrim" id="scrim"></div>

<aside class="dps-drawer" id="inbox" aria-label="{inbox_label}">
  <div class="dps-drawer-head dps-modal-head">
    <h2>{inbox_label}</h2>
    <span id="inbox-count" hidden></span>
    <button type="button" id="inbox-refresh">{refresh}</button>
    <button type="button" class="dps-x" data-close="1" aria-label="{close}">&times;</button>
  </div>
  <div class="dps-drawer-body" id="inbox-body"></div>
</aside>

<div class="dps-modal" id="test-drive" role="dialog" aria-modal="true"></div>

<div class="dps-modal" id="dengage-panel" role="dialog" aria-label="Dengage">
  <div class="dps-modal-head">
    <h2>Dengage</h2>
    <button type="button" class="dps-x" data-close="1" aria-label="{close}">&times;</button>
  </div>
  <div class="dps-modal-body">
    <p class="dps-note">{intro}</p>
    <details class="ref-details">
      <summary>{quickref}</summary>
      <div id="ref-grid"></div>
    </details>
    <div class="launcher-grid" id="launcher-grid"></div>
    <h2 class="dps-h">{events_h}</h2>
    <p class="dps-note">{events_p}</p>
    <div class="dps-field">
      <select id="event-select"></select>
    </div>
    <p id="event-note"></p>
    <button type="button" class="btn-dps" id="event-send">{send}</button>
    <button type="button" class="btn btn-quiet btn-block" id="reset-display">{reset}</button>
    <div class="log" id="panel-log"></div>
  </div>
</div>

<div class="dps-controls">
  <button type="button" class="dps-bell" data-open="#inbox" aria-label="{inbox_label}">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 4a5 5 0 0 1 5 5v4l1.7 2.6H5.3L7 13V9a5 5 0 0 1 5-5z"/><path d="M10 19a2 2 0 0 0 4 0"/></svg>
    <span class="dps-badge" id="inbox-badge" hidden>0</span>
  </button>
  <button type="button" class="dps-launch" data-open="#dengage-panel" aria-label="{launcher_label}">
    <svg viewBox="0 0 38 38"><path d="M11.3821 34.8307H6.61521V28.0187H11.3821C16.4408 27.824 20.4293 23.6395 20.2348 18.5791C20.1375 13.7133 16.1489 9.82066 11.3821 9.72334H6.61521V15.5623H12.3549V22.3744H0V2.91125H11.3821C20.2348 3.2032 27.1418 10.5019 26.85 19.3576C26.6554 27.824 19.8456 34.6361 11.3821 34.8307Z"/><path d="M36.9964 15.9687C38.288 17.303 38.3802 19.5905 36.9964 20.9248C35.6126 22.2591 33.3986 22.2591 32.0148 20.9248C31.369 20.2576 31 19.3045 31 18.4468C31 16.5406 32.476 14.9203 34.4134 14.9203C34.4134 14.9203 34.4134 14.9203 34.5056 14.9203C35.4281 14.9203 36.3507 15.3015 36.9964 15.9687Z"/></svg>
  </button>
</div>

{scripts}
"""


def build(name: str, spec: dict) -> str:
    src = (HYD / f"{name}.html").read_text(errors="ignore")
    out_path = spec["out"]
    rel = rel_to_root(out_path)
    lang = "ar" if name.endswith(".ar") else "en"

    html_tag = re.search(r"<html([^>]*)>", src)
    title = re.search(r"<title>(.*?)</title>", src, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', src)
    body_m = re.search(r"<body([^>]*)>(.*)</body>", src, re.S)
    if not body_m:
        raise SystemExit(f"{name}: no body found")

    body_attrs, body = body_m.group(1), body_m.group(2)

    video_thumbs, hero_list = ld_media(src)
    # The live gateway is chromeless: its only navigation is the scripted
    # geolocation popup, which a static page cannot run. The tenant home's
    # header takes its place, injected raw so every later pass (scripts,
    # assets, links) treats it like the rest of the page.
    if name.startswith("gateway"):
        home_src = (HYD / f"home.{lang}.html").read_text(errors="ignore")
        hm = re.search(r"<header\b.*?</header>", home_src, re.S)
        if hm:
            body = hm.group(0) + body
        fm = re.search(r"<footer\b.*?</footer>", home_src, re.S)
        if fm:
            body = body + fm.group(0)
    body = strip_scripts(body)
    # The gateway heroes' Explore buttons had script-driven navigation; they
    # become plain links into the Mynaghi tenant of the page's language.
    if name.startswith("gateway"):
        target = rel + lang + "/mynaghi/index.html"
        body = re.sub(r'<button\b(?=[^>]*aria-label="(?:اكتشف|Explore|استكشف)")',
                      '<button onclick="location.href=\'' + target + '\'" ', body)
    body = settle_inline_styles(body)
    body = strip_lazy_reservations(body)
    body = replace_videos(body, video_thumbs)
    body = backfill_hero_images(body, hero_list)
    body = rewrite_assets(body, rel)
    body = rewrite_links(body, rel)
    body = wire_test_drive(body, spec.get("product", "tucson"))

    # The header needs the class js/slots.js measures.
    body = re.sub(r"<header\b([^>]*)class=\"", r'<header\1class="site-header ', body, count=1)

    # Inline slots: below the header, above the end of the body content.
    body = re.sub(r"(</header>)", r'\1\n<div id="dn_inline_target_below_header"></div>', body, count=1)
    if spec["type"] == "home":
        # Below the hero carousel: after the first section-sized block in main.
        body = re.sub(r"(</section>)", r'\1\n<div class="dps-slot-wrap"><div id="dn_inline_target_below_hero"></div></div>', body, count=1)
        anchor = body.find("Explore Featured Models") if lang == "en" else body.find("استكشف")
        if anchor != -1:
            close_at = body.find("</h2>", anchor)
            if close_at != -1:
                body = body[:close_at + 5] + '\n<div id="dn_inline_target_in_grid"></div>' + body[close_at + 5:]
    if spec["type"] == "product":
        anchor = body.find("Starting")
        if anchor == -1:
            anchor = body.find("يبدأ")
        if anchor != -1:
            close_at = body.find("</div>", anchor)
            if close_at != -1:
                body = body[:close_at + 6] + '\n<div id="dn_inline_target_pdp_below_price"></div>' + body[close_at + 6:]
    body = re.sub(r"(<footer)", r'<div class="dps-slot-wrap"><div id="dn_inline_target_above_footer"></div></div>\n\1', body, count=1)

    # Page identity for the event layer.
    extra_attrs = f' data-page-type="{spec["type"]}"'
    if name.startswith("gateway"):
        extra_attrs += ' data-gateway="1"'
    if spec.get("product"):
        extra_attrs += f' data-product-id="{spec["product"]}"'
        if spec.get("price"):
            extra_attrs += f' data-price="{spec["price"]}"'
        extra_attrs += f' data-category-path="Vehicles>{spec.get("cat", "SUV")}"'
    if spec.get("promotion"):
        extra_attrs += f' data-promotion-id="{spec["promotion"]}"'
    # The frozen body height and pointer state go; the font variable classes stay.
    body_attrs = re.sub(r'style="[^"]*"', "", body_attrs)

    dirattr = "rtl" if lang == "ar" else "ltr"
    page_title = title.group(1).strip() if title else "Hyundai Saudi Arabia"
    page_desc = (desc.group(1) if desc else "").replace('"', "&quot;")

    head = head_block(name, spec, page_title, page_desc, rel, lang, body_attrs)
    mounts = mounts_block(rel, lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{dirattr}" class="preloader-mounted" data-demo-slug="hyundaiksa">
<head>
{head}
</head>
<body{body_attrs}{extra_attrs}>
{body}
{mounts}
</body>
</html>
"""


def build_css():
    """Copy the site's compiled CSS, pointing its font URLs at the committed
    files. Only fonts live under /_next/static/media in these chunks."""
    outdir = ROOT / "assets" / "css" / "site"
    outdir.mkdir(parents=True, exist_ok=True)
    renames = {
        "GESSTwoMedium_ENNumbers-s.0uin9duiiya9_.otf": "GESSTwoMedium_ENNumbers.otf",
        "GESSTwoMedium_ENNumbers-s.p.0uin9duiiya9_.otf": "GESSTwoMedium_ENNumbers.otf",
        "HyundaiSansHead_Bold-s.p.05uap75rtvbhd.otf": "HyundaiSansHead_Bold.otf",
        "HyundaiSansHead_Light-s.p.3qmu59-gs-29n.otf": "HyundaiSansHead_Light.otf",
        "HyundaiSansHead_Light.3qmu59-gs-29n.otf": "HyundaiSansHead_Light.otf",
        "HyundaiSansHead_Medium-s.p.43swq4rlfs0yk.otf": "HyundaiSansHead_Medium.otf",
        "HyundaiSansHead_Regular-s.p.1wz0ync88eat7.otf": "HyundaiSansHead_Regular.otf",
        "HyundaiSansHead_Regular.1wz0ync88eat7.otf": "HyundaiSansHead_Regular.otf",
    }
    for chunk in CSS_CHUNKS:
        src = ROOT / "reference" / "css" / f"{chunk}.css"
        if not src.exists():
            print(f"  missing css chunk {chunk}")
            continue
        css = src.read_text(errors="ignore")
        for old, new in renames.items():
            css = css.replace(f"/_next/static/media/{old}", f"../../fonts/{new}")
        css = re.sub(r"/\*# sourceMappingURL=[^*]+\*/", "", css)
        (outdir / f"{chunk}.css").write_text(css)
    print(f"css: {len(CSS_CHUNKS)} chunks written to assets/css/site/")


def main(names):
    build_css()
    for name in (names or PAGES.keys()):
        spec = PAGES[name]
        out = ROOT / spec["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        html = build(name, spec)
        out.write_text(html)
        print(f"{name} -> {spec['out']} ({len(html)//1024} KB)")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
