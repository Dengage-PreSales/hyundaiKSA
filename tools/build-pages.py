#!/usr/bin/env python3
"""Build the static demo pages from the hydrated captures.

Each page in reference/hydrated/ is transformed into a self-contained static
page for D·Auto, a fictitious automotive brand: scripts and trackers removed,
every photograph and logo replaced by the committed brand-asset system under
assets/brand/, every name, model, trademark and phone number swapped for the
fictitious equivalents, links mapped to the pages this demo carries, and the
Dengage layer injected with the load-bearing head order (identity first, SDK
second, stylesheets after).

The page LAYOUT is the only thing the captures still provide; no proprietary
name, image, font or mark survives into the built tree.
"""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
HYD = ROOT / "reference" / "hydrated"
CDN_PREFIX = r"https://assets\.hyundai-me\.com/client-mynaghi-production/"

CSS_CHUNKS = [
    "1ro47j0m9_bpw", "1xd0wv4t3_w6f", "3ioh63cvv2q2g", "2me9zktabzrcz",
    "31qivdt-iwa4m", "1aoqx93wdvmqk", "1z_mbvpkjhpd5",
]

LANGDIR = {"en": "", "ar": "ar/"}

# Non-model pages: capture stem -> (site-relative output, spec).
BASE_PAGES = {
    "home":     ("index.html",                     {"type": "home"}),
    "offers":   ("offers/index.html",              {"type": "promotion"}),
    "campaign": ("offers/back-to-school/index.html", {"type": "promotion", "promotion": "back-to-school"}),
    "service":  ("service-booking/index.html",     {"type": "other"}),
    "contact":  ("contact-us/index.html",          {"type": "other"}),
}

# Model pages: capture stem -> (fictitious slug, path on the captured property
# as it appears inside hrefs, list price in SAR, category). The price NUMBERS
# are kept from the captures so the funnel maths stays realistic; attached to
# invented models they are openly fictional. One model publishes no price on
# purpose: the omit-a-key-you-cannot-source rule needs a living example.
MODEL_SRC = {
    "tucson":         ("vanta",           "tucson",         "101258", "SUV"),
    "santafe":        ("ridge",           "santa-fe",       "138429", "SUV"),
    "accent":         ("pulse",           "accent",         "71484",  "Sedan"),
    "azera":          ("sovereign",       "azera",          "158436", "Sedan"),
    "elantra":        ("vector",          "Elantra",        "86694",  "Sedan"),
    "grandi10":       ("neo",             "grandi10",       "56239",  "Sedan"),
    "sonata":         ("serene",          "sonata",         "107904", "Sedan"),
    "creta":          ("terra",           "creta",          "86200",  "SUV"),
    "creta-grand":    ("terra-max",       "creta-grand",    "102054", "SUV"),
    "kona":           ("apex",            "kona",           "92544",  "SUV"),
    "palisade":       ("summit",          "palisade",       "177039", "SUV"),
    "venue":          ("urban",           "venue",          "77334",  "SUV"),
    "stargazer":      ("nova",            "stargazer",      "79147",  "MPV"),
    "staria-premium": ("voyager-premium", "staria-premium", "180294", "MPV"),
    "staria-van":     ("voyager-van",     "staria-van",     None,     "MPV"),
    "staria-wagon":   ("voyager",         "staria-wagon",   "136224", "MPV"),
}

PAGES = {}
for _stem, (_out, _spec) in BASE_PAGES.items():
    for _lang in ("en", "ar"):
        PAGES[f"{_stem}.{_lang}"] = dict(_spec, out=LANGDIR[_lang] + _out)
for _stem, (_slug, _live, _price, _cat) in MODEL_SRC.items():
    for _lang in ("en", "ar"):
        _spec = {"out": f"{LANGDIR[_lang]}models/{_slug}/index.html",
                 "type": "product", "product": _slug, "cat": _cat}
        if _price:
            _spec["price"] = _price
        PAGES[f"{_stem}.{_lang}"] = _spec

# Captured-property routes -> site-relative output templates. Every href the
# captures carry resolves inside this demo; a fictitious brand has no live
# site to fall back to, so nothing may leave it.
ROUTES = {
    "": "{langdir}index.html",
    "/mynaghi": "{langdir}index.html",
    "/mynaghi/models": "{langdir}index.html",
    "/mynaghi/offers": "{langdir}offers/index.html",
    "/mynaghi/offers/backtoschool": "{langdir}offers/back-to-school/index.html",
    "/mynaghi/service-booking": "{langdir}service-booking/index.html",
    "/mynaghi/contact-us": "{langdir}contact-us/index.html",
}
for _stem, (_slug, _live, _price, _cat) in MODEL_SRC.items():
    for _key in {_live, _live.lower()}:
        ROUTES[f"/mynaghi/models/{_key}"] = "{langdir}models/" + _slug + "/index.html"

# Pages the property has and this demo deliberately does not: each maps to
# the demo page that carries the same intent.
ALIAS = {
    "about-mynaghi": "index.html",
    "innovation": "index.html",
    "yourperfectpartner": "index.html",
    "after-sales-network": "service-booking/index.html",
    "maintenance": "service-booking/index.html",
    "parts-and-accessories": "service-booking/index.html",
    "warranty": "service-booking/index.html",
    "bluelink": "service-booking/index.html",
    "hyundai-service": "service-booking/index.html",
    "aftersales-offers": "offers/index.html",
    "career": "contact-us/index.html",
    "cookies": "contact-us/index.html",
    "find-us": "contact-us/index.html",
    "fleet": "contact-us/index.html",
    "legal-terms": "contact-us/index.html",
    "login": "contact-us/index.html",
    "privacy-policy": "contact-us/index.html",
    "terms-conditions": "contact-us/index.html",
    "terms-of-use": "contact-us/index.html",
}

# ---------------------------------------------------------------------------
# The D·Auto brand-asset system

SCENES = [f"scene-{b}-{i}.svg" for b in ("sedan", "suv", "van") for i in (1, 2, 3, 4)]
PANELS = [f"panel-{i}.svg" for i in (1, 2, 3, 4)]
BODY_OF = {"Sedan": "sedan", "SUV": "suv", "MPV": "van"}

# Mirrors the ART map in js/vehicles.js: each model's signature scene.
ART = {
    "pulse": "scene-sedan-1.svg", "sovereign": "scene-sedan-2.svg",
    "vector": "scene-sedan-3.svg", "neo": "scene-sedan-4.svg",
    "serene": "scene-sedan-1.svg", "terra": "scene-suv-1.svg",
    "terra-max": "scene-suv-2.svg", "apex": "scene-suv-3.svg",
    "summit": "scene-suv-4.svg", "ridge": "scene-suv-1.svg",
    "vanta": "scene-suv-2.svg", "urban": "scene-suv-3.svg",
    "nova": "scene-van-1.svg", "voyager-premium": "scene-van-2.svg",
    "voyager-van": "scene-van-3.svg", "voyager": "scene-van-4.svg",
}

HEADER_LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="125" height="16" '
                   'viewBox="0 0 125 16" fill="none" aria-label="D&#183;AUTO">'
                   '<text x="0" y="13.2" font-family="Arial, sans-serif" font-size="14.5" '
                   'font-weight="800" letter-spacing="3" class="color-fill">D&#183;AUTO</text></svg>')
FOOTER_LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="140" height="18" '
                   'viewBox="0 0 140 18" fill="none" aria-label="D&#183;AUTO">'
                   '<text x="0" y="14.6" font-family="Arial, sans-serif" font-size="16" '
                   'font-weight="800" letter-spacing="3.4" fill="#ffffff">D&#183;AUTO</text></svg>')


def brand_asset(path: str, spec: dict) -> str:
    """A deterministic brand tile for any captured photograph: product pages
    draw from their own body style's scene set so a model's gallery reads as
    one family; everything else cycles the whole system."""
    h = int(hashlib.md5(path.encode("utf-8")).hexdigest(), 16)
    if spec.get("product"):
        body = BODY_OF.get(spec.get("cat", "SUV"), "suv")
        pool = [f"scene-{body}-{i}.svg" for i in (1, 2, 3, 4)] + PANELS
    else:
        pool = SCENES + PANELS
    return "assets/brand/" + pool[h % len(pool)]


# ---------------------------------------------------------------------------
# The rebrand dictionaries. Ordered: longer phrases first so a long match is
# never half-eaten by a short one, compound lockups before their parts so
# nothing doubles.

REBRAND = [
    # Company lockups before their component words.
    ("Mohamed Yousuf Naghi Motors Co.", "D·Auto Motors Co."),
    ("MOHAMED YOUSUF NAGHI MOTORS", "D·AUTO MOTORS"),
    ("Mohamed Yousuf Naghi Motors", "D·Auto Motors"),
    ("Mohamed Yousuf Naghi", "D·Auto Motors"),
    ("شركة محمد يوسف ناغي للسيارات", "شركة دي أوتو للسيارات"),
    ("محمد يوسف ناغي للسيارات", "دي أوتو للسيارات"),
    ("محمد يوسف ناغي", "دي أوتو"),
    ("MYNaghi Hyundai", "D·Auto"),
    ("Mynaghi Hyundai", "D·Auto"),
    ("Naghi Hyundai", "D·Auto"),
    ("MYNAGHI", "D·AUTO"),
    ("MYNaghi", "D·Auto"),
    ("MyNaghi", "D·Auto"),
    ("Mynaghi", "D·Auto"),
    ("mynaghi", "D·Auto"),
    ("NAGHI", "D·AUTO"),
    ("Naghi", "D·Auto"),
    ("ناغي", "دي أوتو"),
    # The brand itself.
    ("HYUNDAI", "D·AUTO"),
    ("Hyundai", "D·Auto"),
    ("hyundai", "D·Auto"),
    ("هيونداي", "دي أوتو"),
    # Model names, longest first. English.
    ("STARIA PREMIUM", "VOYAGER PREMIUM"),
    ("STARIA Premium", "VOYAGER Premium"),
    ("Staria Premium", "Voyager Premium"),
    ("STARIA VAN", "VOYAGER VAN"),
    ("STARIA Van", "VOYAGER Van"),
    ("Staria Van", "Voyager Van"),
    ("STARIA WAGON", "VOYAGER WAGON"),
    ("STARIA Wagon", "VOYAGER Wagon"),
    ("Staria Wagon", "Voyager Wagon"),
    ("CRETA GRAND", "TERRA MAX"),
    ("Creta Grand", "Terra Max"),
    ("GRAND I10", "NEO"),
    ("GRAND i10", "NEO"),
    ("Grand i10", "Neo"),
    ("SANTA FE", "RIDGE"),
    ("Santa Fe", "Ridge"),
    ("SANTA-FE", "RIDGE"),
    ("Santa-Fe", "Ridge"),
    ("TUCSON", "VANTA"),
    ("Tucson", "Vanta"),
    # The captured property misspells its own model in several headings.
    ("TUSCON", "VANTA"),
    ("Tuscon", "Vanta"),
    ("tuscon", "Vanta"),
    ("ACCENT", "PULSE"),
    ("Accent", "Pulse"),
    ("AZERA", "SOVEREIGN"),
    ("Azera", "Sovereign"),
    ("ELANTRA", "VECTOR"),
    ("Elantra", "Vector"),
    ("SONATA", "SERENE"),
    ("Sonata", "Serene"),
    ("CRETA", "TERRA"),
    ("Creta", "Terra"),
    ("KONA", "APEX"),
    ("Kona", "Apex"),
    ("PALISADE", "SUMMIT"),
    ("Palisade", "Summit"),
    ("VENUE", "URBAN"),
    ("Venue", "Urban"),
    ("STARGAZER", "NOVA"),
    ("Stargazer", "Nova"),
    ("STARIA", "VOYAGER"),
    ("Staria", "Voyager"),
    # Model names, Arabic (both attested spellings where the captures vary).
    ("ستاريا بريميوم", "فوياجر بريميوم"),
    ("ستاريا فان", "فوياجر فان"),
    ("كريتا جراند", "تيرا ماكس"),
    ("جراند i10", "نيو"),
    ("سانتافي", "ريدج"),
    ("سانتا في", "ريدج"),
    ("سنتافي", "ريدج"),
    ("توسان", "فانتا"),
    ("أكسنت", "بولس"),
    ("اكسنت", "بولس"),
    ("أزيرا", "سوفرين"),
    ("ازيرا", "سوفرين"),
    ("إلنترا", "فكتور"),
    ("النترا", "فكتور"),
    ("سوناتا", "سيرين"),
    ("كريتا", "تيرا"),
    ("كونا", "أبكس"),
    ("باليسيد", "سوميت"),
    ("فينيو", "أوربان"),
    ("ستارجايزر", "نوفا"),
    ("ستارجازر", "نوفا"),
    ("ستاريا", "فوياجر"),
    # Technology marks.
    ("Sensuous Sportiness", "Sculpted Motion"),
    ("Sensuous", "Sculpted"),
    ("SMARTSENSE", "SENSESHIELD"),
    ("SmartSense", "SenseShield"),
    ("Smartsense", "SenseShield"),
    ("smartSense", "SenseShield"),
    ("smartsense", "SenseShield"),
    ("Smart Sense", "SenseShield"),
    ("سمارت سينس", "سينس شيلد"),
    ("BLUELINK", "D·CONNECT"),
    ("BlueLink", "D·Connect"),
    ("Bluelink", "D·Connect"),
    ("blueLink", "D·Connect"),
    ("bluelink", "D·Connect"),
    ("Blue Link", "D·Connect"),
    ("بلولينك", "دي كونكت"),
    ("بلو لينك", "دي كونكت"),
    ("N LINE", "R-SPEC"),
    ("N Line", "R-Spec"),
    ("N-Line", "R-Spec"),
    ("N-line", "R-Spec"),
    ("n line", "R-Spec"),
    ("N branding", "R-Spec branding"),
    ("N badge", "R-Spec badge"),
    ("N logo", "R-Spec logo"),
    ("N Performance", "R-Spec Performance"),
    ("HTRAC", "AWD"),
    ("Smartstream", "EcoStream"),
    ("SmartStream", "EcoStream"),
    ("IONIQ", "E-SERIES"),
    ("CALLIGRAPHY", "SIGNATURE"),
    ("Calligraphy", "Signature"),
    ("بشعار N", "بشعار R-Spec"),
    ("شعار N", "شعار R-Spec"),
    ("hyundaiksa.com", "d-auto.example"),
]

# A lockup like "MYNaghi Hyundai TUCSON" can leave a doubled brand after two
# passes; collapse it.
CLEANUP = [
    ("D·AUTO D·AUTO", "D·AUTO"),
    ("D·Auto D·Auto", "D·Auto"),
    ("دي أوتو دي أوتو", "دي أوتو"),
]

# Applied to the whole document, references included: the property's real
# numbers become the fictitious brand's, and the marque-named font tokens in
# class and style space are renamed EXACTLY as build_css renames them inside
# the compiled chunks — the two must stay in lockstep or those selectors stop
# matching. None of these tokens collides with the load-bearing demo slug
# (data-demo-slug="hyundaiksa"), which is an internal namespace, not content.
LITERAL_SWAPS = [
    ("+9668001240191", "+9668001002000"),
    ("9668001240191", "9668001002000"),
    ("8001240191", "8001002000"),
    ("800 124 0191", "800 100 2000"),
    ("800-124-0191", "800-100-2000"),
    ("font-hyundai-arabic-medium", "font-dauto-arabic-medium"),
    ("font-hyundai-medium", "font-dauto-medium"),
    ("font-hyundai-regular", "font-dauto-regular"),
    ("font-hyundai-bold", "font-dauto-bold"),
    ("font-bold-hyundai", "font-bold-dauto"),
    ("hyundaiArabicMedium", "dautoArabicMedium"),
    ("hyundaiMedium", "dautoMedium"),
    ("hyundaiRegular", "dautoRegular"),
    ("hyundaiBold", "dautoBold"),
    ("hyundaiLight", "dautoLight"),
    ("hyundaiarabicmedium_", "dautoarabicmedium_"),
    ("hyundaimedium_", "dautomedium_"),
    ("hyundairegular_", "dautoregular_"),
    ("hyundaibold_", "dautobold_"),
    ("hyundailight_", "dautolight_"),
    # Class/data tokens the templates name after models and marks (the
    # tucson-title heading class is reused on every model page). build_css
    # applies the same renames so the selectors keep matching.
    ("tucson", "vanta"),
    ("tuscon", "vanta"),
    ("smartsense", "senseshield"),
]

TEXT_ATTRS = r"(alt|aria-label|aria-description|placeholder|title|content|models_name|models_code)"


def _apply_words(text: str) -> str:
    for old, new in REBRAND:
        if old in text:
            text = text.replace(old, new)
    for old, new in CLEANUP:
        if old in text:
            text = text.replace(old, new)
    return text


def rebrand(html: str) -> str:
    """Nothing proprietary survives: model names, marks and company names go
    from every text node and every human-readable attribute; phone numbers go
    from the whole document. Class names, ids and asset paths are structure,
    not content, and stay exactly as captured."""
    for old, new in LITERAL_SWAPS:
        html = html.replace(old, new)
    html = re.sub(r">([^<]*)<", lambda m: ">" + _apply_words(m.group(1)) + "<", html)
    html = re.sub(TEXT_ATTRS + r'="([^"]*)"',
                  lambda m: m.group(1) + '="' + _apply_words(m.group(2)) + '"', html)
    return html


def swap_logos(t: str) -> str:
    """The captured wordmark svgs (125x16 in the header, 140x18 in the footer)
    become the D·AUTO wordmark. The header variant keeps class="color-fill" so
    the site's own hover/scroll recolouring keeps driving it; the footer sits
    on the dark band and is simply white. The footer's bitmap logo (an <img>
    hotlinked from the build agency's CDN) becomes the white brand logo."""
    t = re.sub(r'<svg[^>]*viewBox="0 0 125 16".*?</svg>', HEADER_LOGO_SVG, t, flags=re.S)
    t = re.sub(r'<svg[^>]*viewBox="0 0 140 18".*?</svg>', FOOTER_LOGO_SVG, t, flags=re.S)
    return t


def strip_profile_button(t: str) -> str:
    """A fictitious brand has no account backend to sign in to, and the
    demonstration-site contract forbids a control that cannot act. The whole
    Login affordance leaves the header."""
    return re.sub(r'<button[^>]*class="[^"]*profile_button[^"]*"[^>]*>.*?</button>',
                  "", t, flags=re.S)


def rel_to_root(out_path: str) -> str:
    depth = out_path.count("/")
    return "../" * depth


def map_route(href: str, rel: str):
    """Return the local href for a captured-property path, or None for a href
    that is not site-internal. Every internal path resolves: built page,
    intent alias, or home."""
    clean = href.split("?")[0].split("#")[0].rstrip("/")
    m = re.match(r"^/(en|ar)(/.*)?$", clean)
    if not m:
        return None
    lang, rest = m.group(1), m.group(2) or ""
    langdir = LANGDIR[lang]
    target = ROUTES.get(rest)
    if not target and rest.startswith("/mynaghi/"):
        seg = rest[len("/mynaghi/"):].split("/")[0]
        alias = ALIAS.get(seg)
        if alias:
            target = "{langdir}" + alias
    if not target:
        target = "{langdir}index.html"
    return rel + target.format(langdir=langdir)


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


def rewrite_assets(t: str, rel: str, spec: dict) -> str:
    """Every captured photograph becomes a committed D·Auto brand tile; the
    handful of generic site-root icons keep their committed copies."""
    t = t.replace("&amp;", "&")
    # The build agency's CDN serves exactly one thing the pages show: the
    # footer's white wordmark bitmap.
    t = re.sub(r"https://assets\.tech\.beyond-creation\.net/[^\s\"'<>]+",
               rel + "assets/brand/logo-white.svg", t)
    # Parentheses are legal and PRESENT in their filenames (image-(8).png), so
    # the path class must allow them; quotes, whitespace and angle brackets
    # still terminate, which is what actually delimits a URL in markup.
    # A bare & is ALSO legal in their filenames (exterior&interior.webp) and
    # stays in the path — but &quot;/&amp; entities terminate it, so an
    # inline-style url(&quot;...&quot;) still ends before the entity. Query
    # strings are the second group and are dropped.
    t = re.sub(CDN_PREFIX + r"((?:[^\s\"'<>?&]|&(?!quot;|amp;))+)(\?[^\s\"'<>]*)?",
               lambda m: rel + brand_asset(m.group(1), spec), t)
    # Whatever still points at their _next tree cannot resolve here.
    t = re.sub(r"/_next/image\?url=([^\s\"'&]+)[^\s\"']*", r"\1", t)
    # The handful of images served from the site root rather than the CDN,
    # in every spelling they appear in: absolute to the live host, or
    # root-relative inside src AND srcset candidate lists. Anything carrying
    # the old marque in its name becomes the brand logo instead.
    t = t.replace("https://hyundaiksa.com/images/", "/images/")
    def site_img(m):
        name = m.group(1)
        if "hyundai" in name.lower():
            return rel + "assets/brand/logo-white.svg"
        return rel + "assets/img/site/" + name
    t = re.sub(r"/images/([^\s\"'<>,?\\]+)(\?[^\s\"'<>,]*)?", site_img, t)
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
    """A committed demo carries no multi-megabyte films. Each video element
    becomes its own declared thumbnail (from the page's JSON-LD), or its
    poster; one with neither disappears. The thumbnail URL is a CDN path, so
    the asset pass then turns it into a brand tile like any other image."""
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


def force_hero_scene(t: str, rel: str, slug: str) -> str:
    """A model page's first hero slide shows that model's own signature scene,
    whatever photograph the capture happened to freeze there."""
    art = ART.get(slug)
    if not art:
        return t
    at = t.find("banner-slide")
    if at == -1:
        return t
    m = re.search(r'(<img[^>]*?src=")[^"]*(")', t[at:at + 8000])
    if not m:
        return t
    s, e = at + m.start(), at + m.end()
    return t[:s] + m.group(1) + rel + "assets/brand/" + art + m.group(2) + t[e:]


HOME_HERO = ["scene-suv-2.svg", "scene-sedan-1.svg", "scene-van-2.svg",
             "scene-suv-4.svg", "scene-sedan-3.svg"]


def force_home_heroes(t: str) -> str:
    """The home hero carousel is the first thing anyone sees: every slide gets
    a car scene, in a fixed rotation, instead of whatever the hash draw would
    give it. Runs after rewrite_assets, so it retargets committed paths."""
    slide_at = [m.start() for m in re.finditer("banner-slide", t)]
    if not slide_at:
        return t
    out, last, idx = [], 0, 0
    for at in slide_at:
        window = t[at:at + 8000]
        m = re.search(r'(src=")[^"]*assets/brand/[^"]*(")', window)
        if not m:
            continue
        s, e = at + m.start(), at + m.end()
        if s < last:
            continue
        rel_m = re.search(r'src="((?:\.\./)*)assets/brand/', window)
        rel = rel_m.group(1) if rel_m else ""
        out.append(t[last:s])
        out.append('src="' + rel + "assets/brand/" + HOME_HERO[idx % len(HOME_HERO)] + '"')
        last = e
        idx += 1
    out.append(t[last:])
    return "".join(out)


def rewrite_links(t: str, rel: str) -> str:
    """Every link resolves inside the demo. Captured-property hrefs — relative
    or absolute — map to the built page with the same intent; there is no
    live property behind a fictitious brand to fall back to."""
    def fix(match):
        href = match.group(1)
        if href.startswith("https://hyundaiksa.com/"):
            href = href[len("https://hyundaiksa.com"):]
        if href.startswith(("http", "tel:", "mailto:", "#", "javascript:")):
            return match.group(0)
        mapped = map_route(href, rel)
        if mapped is None:
            return match.group(0)
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
<link rel="icon" type="image/svg+xml" href="{rel}assets/brand/favicon.svg">
<link rel="icon" href="{rel}assets/favicon.ico" sizes="32x32">
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
    inbox_label = "تحديثات دي أوتو" if ar else "D·Auto updates"
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
    site_path = out_path[3:] if out_path.startswith("ar/") else out_path

    title = re.search(r"<title>(.*?)</title>", src, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', src)
    body_m = re.search(r"<body([^>]*)>(.*)</body>", src, re.S)
    if not body_m:
        raise SystemExit(f"{name}: no body found")

    body_attrs, body = body_m.group(1), body_m.group(2)

    video_thumbs, hero_list = ld_media(src)
    body = strip_scripts(body)
    body = settle_inline_styles(body)
    body = strip_lazy_reservations(body)
    body = replace_videos(body, video_thumbs)
    body = backfill_hero_images(body, hero_list)
    body = rewrite_assets(body, rel, spec)
    if spec.get("product"):
        body = force_hero_scene(body, rel, spec["product"])
    if spec["type"] == "home":
        body = force_home_heroes(body)
    body = rewrite_links(body, rel)
    body = swap_logos(body)
    body = strip_profile_button(body)
    body = wire_test_drive(body, spec.get("product", "vanta"))

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
    page_title = title.group(1).strip() if title else "D·Auto Saudi Arabia"
    page_desc = (desc.group(1) if desc else "").replace('"', "&quot;")

    head = head_block(name, spec, page_title, page_desc, rel, lang, body_attrs)
    mounts = mounts_block(rel, lang)

    page = f"""<!DOCTYPE html>
<html lang="{lang}" dir="{dirattr}" class="preloader-mounted" data-demo-slug="hyundaiksa" data-rel-root="{rel}" data-site-path="{site_path}">
<head>
{head}
</head>
<body{body_attrs}{extra_attrs}>
{body}
{mounts}
</body>
</html>
"""
    return rebrand(page)


def build_css():
    """Copy the site's compiled CSS with the proprietary typography removed:
    the @font-face blocks that loaded licensed .otf files are dropped (the
    demo's fonts.css supplies the open replacements), the metric-adjusted
    local-Arial fallback faces stay, and every family/token name loses the
    old marque."""
    outdir = ROOT / "assets" / "css" / "site"
    outdir.mkdir(parents=True, exist_ok=True)
    for chunk in CSS_CHUNKS:
        src = ROOT / "reference" / "css" / f"{chunk}.css"
        if not src.exists():
            print(f"  missing css chunk {chunk}")
            continue
        css = src.read_text(errors="ignore")
        css = re.sub(r"@font-face\s*\{[^}]*/_next/static/media/[^}]*\}", "", css)
        css = css.replace("hyundai", "dauto").replace("Hyundai", "DAuto").replace("HYUNDAI", "DAUTO")
        css = css.replace("GESSTwoMedium_ENNumbers", "DAutoArabic")
        css = css.replace("tucson", "vanta").replace("tuscon", "vanta").replace("smartsense", "senseshield")
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
