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
for _lang in ("en", "ar"):
    PAGES[f"company.{_lang}"] = {"out": LANGDIR[_lang] + "company/index.html",
                                 "type": "other", "synthetic": "company"}

# Captured-property routes -> site-relative output templates. Every href the
# captures carry resolves inside this demo; a fictitious brand has no live
# site to fall back to, so nothing may leave it.
ROUTES = {
    "": "{langdir}index.html",
    "/mynaghi": "{langdir}index.html",
    "/mynaghi/models": "{langdir}index.html#models",
    "/mynaghi/offers": "{langdir}offers/index.html",
    "/mynaghi/offers/backtoschool": "{langdir}offers/back-to-school/index.html",
    "/mynaghi/service-booking": "{langdir}service-booking/index.html",
    "/mynaghi/contact-us": "{langdir}contact-us/index.html",
}
for _stem, (_slug, _live, _price, _cat) in MODEL_SRC.items():
    for _key in {_live, _live.lower()}:
        ROUTES[f"/mynaghi/models/{_key}"] = "{langdir}models/" + _slug + "/index.html"

# Pages the property has and this demo deliberately does not: each maps to
# the demo destination that carries the same intent — its own page, or its
# own anchored section of one. No two different intents share a bare page.
ALIAS = {
    "about-mynaghi": "company/index.html#about",
    "innovation": "company/index.html#innovation",
    "career": "company/index.html#careers",
    "fleet": "company/index.html#fleet",
    "privacy-policy": "company/index.html#privacy",
    "legal-terms": "company/index.html#terms",
    "terms-conditions": "company/index.html#terms",
    "terms-of-use": "company/index.html#terms",
    "cookies": "company/index.html#cookies",
    "yourperfectpartner": "service-booking/index.html#aftercare",
    "hyundai-service": "service-booking/index.html#promise",
    "after-sales-network": "service-booking/index.html#network",
    "maintenance": "service-booking/index.html#maintenance",
    "parts-and-accessories": "service-booking/index.html#parts",
    "warranty": "service-booking/index.html#warranty",
    "bluelink": "service-booking/index.html#connect",
    "aftersales-offers": "offers/index.html#aftersales",
    "find-us": "index.html#dealers",
    "login": "contact-us/index.html",
}

# ---------------------------------------------------------------------------
# The D·Auto imagery system: real photography, committed under assets/photo/.
# Every file is an Unsplash photograph (Unsplash License: free to download,
# copy, modify and distribute), fetched at build-prep time and verified by
# eye; filenames keep the Unsplash photo id for provenance. The README
# carries the credit list.

PHOTO = {
    # heroes and general scenery
    "hero-desert-road": "1653491493226.jpg",   # white SUV on a desert highway
    "hero-sunset-road": "1568605117036.jpg",   # car on a winding road at sunset
    "hero-dunes-aerial": "1763535834153.jpg",  # carving down a dune, aerial
    "hero-night-motion": "1503376780353.jpg",  # dark coupe in motion at night
    "hero-dusk-desert": "1552519507.jpg",      # teal coupe in the desert at dusk
    # per-model signatures
    "pulse": "1502877338535.jpg",              # blue coupe on a city street
    "sovereign": "1616422285623.jpg",          # white grand tourer in the mountains
    "vector": "1555215695.jpg",                # white sports sedan under palms
    "neo": "1739738709610.jpg",                # red city hatch, motion pan
    "serene": "1493238792000.jpg",             # sedan rear in golden city light
    "terra": "1637189300412.jpg",              # off-roader on a red dune
    "terra-max": "1519641471654.jpg",          # family crossover, icy fjord
    "apex": "1600661653561.jpg",               # white crossover in the desert
    "summit": "1533473359331.jpg",             # full-size SUV in red-rock country
    "ridge": "1523996183508.jpg",              # SUV on the dunes at dusk
    "vanta": "1653491493226.jpg",              # the flagship shares the hero shot
    "urban": "1549399542.jpg",                 # compact sport model under palms
    "nova": "1568605117036.jpg",               # family roadtrip at sunset
    "voyager-premium": "1623371857133.jpg",    # silver MPV at dusk
    "voyager-van": "1548379269.jpg",           # utility van on the dunes
    "voyager": "1623371857133.jpg",
    # roles
    "service": "1487754180451.jpg",            # technician topping up an engine
    "fleet": "1543465077.jpg",                 # aerial car park
    "interior": "1449965408869.jpg",           # hands on the wheel, city bokeh
    "night-tech": "1533106418989.jpg",         # glowing headlights in the dark
    "showroom-light": "1518987048.jpg",        # showroom in magenta light
    "city-rain": "1471479917193.jpg",          # rainy city street, car rear
    "performance": "1494976388531.jpg",        # dark muscle car, storm sky
    "interchange": "1465447142348.jpg",        # aerial highway interchange
}


def photo(role: str) -> str:
    return "assets/photo/" + PHOTO[role]


POOLS = {
    "sedan": ["pulse", "sovereign", "vector", "serene", "performance", "interior"],
    "suv": ["terra", "ridge", "vanta", "summit", "apex", "hero-dunes-aerial", "interior"],
    "van": ["voyager-premium", "voyager-van", "terra-max", "interior"],
    "generic": ["hero-desert-road", "hero-sunset-road", "hero-dusk-desert",
                "city-rain", "showroom-light", "interior", "hero-night-motion"],
}
BODY_OF = {"Sedan": "sedan", "SUV": "suv", "MPV": "van"}

# Mirrors the ART map in js/vehicles.js: each model's signature photograph.
ART = {m: PHOTO[m] for m in (
    "pulse", "sovereign", "vector", "neo", "serene", "terra", "terra-max",
    "apex", "summit", "ridge", "vanta", "urban", "nova", "voyager-premium",
    "voyager-van", "voyager")}

HEADER_LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="125" height="16" '
                   'viewBox="0 0 125 16" fill="none" aria-label="D&#183;AUTO">'
                   '<text x="0" y="13.2" font-family="Arial, sans-serif" font-size="14.5" '
                   'font-weight="800" letter-spacing="3" class="color-fill">D&#183;AUTO</text></svg>')
FOOTER_LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="140" height="18" '
                   'viewBox="0 0 140 18" fill="none" aria-label="D&#183;AUTO">'
                   '<text x="0" y="14.6" font-family="Arial, sans-serif" font-size="16" '
                   'font-weight="800" letter-spacing="3.4" fill="#ffffff">D&#183;AUTO</text></svg>')


def brand_asset(path: str, spec: dict, state: dict) -> str:
    """A deterministic replacement photograph for any captured image. A model
    page draws from its own body style's photo pool (its signature shot
    first), hashed by the original path so a repeated source image maps to a
    repeated photo. Everywhere else the scenery set is dealt out in order,
    one per distinct source image, so neighbouring sections never show the
    same photograph twice."""
    if spec.get("product"):
        h = int(hashlib.md5(path.encode("utf-8")).hexdigest(), 16)
        body = BODY_OF.get(spec.get("cat", "SUV"), "suv")
        pool = [spec["product"]] + POOLS[body]
        return photo(pool[h % len(pool)])
    pool = POOLS["generic"]
    if path not in state:
        state[path] = state.get("__next", 0)
        state["__next"] = state[path] + 1
    return photo(pool[state[path] % len(pool)])


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
    ("customer.care@hyundai.mynaghi.com", "care@d-auto.example"),
    ("@hyundai.mynaghi.com", "@d-auto.example"),
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
    state = {}
    t = re.sub(CDN_PREFIX + r"((?:[^\s\"'<>?&]|&(?!quot;|amp;))+)(\?[^\s\"'<>]*)?",
               lambda m: rel + brand_asset(m.group(1), spec, state), t)
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
    """A model page's first hero slide shows that model's own signature
    photograph, whatever image the capture happened to freeze there."""
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
    return t[:s] + m.group(1) + rel + "assets/photo/" + art + m.group(2) + t[e:]


HOME_HERO = ["hero-desert-road", "hero-sunset-road", "hero-dunes-aerial",
             "hero-night-motion", "hero-dusk-desert"]


def force_home_heroes(t: str) -> str:
    """The home hero carousel is the first thing anyone sees: every slide gets
    a hero photograph, in a fixed rotation, instead of whatever the hash draw
    would give it. Runs after rewrite_assets, so it retargets committed
    paths."""
    slide_at = [m.start() for m in re.finditer("banner-slide", t)]
    if not slide_at:
        return t
    out, last, idx = [], 0, 0
    for at in slide_at:
        window = t[at:at + 8000]
        m = re.search(r'(src=")[^"]*assets/photo/[^"]*(")', window)
        if not m:
            continue
        s, e = at + m.start(), at + m.end()
        if s < last:
            continue
        rel_m = re.search(r'src="((?:\.\./)*)assets/photo/', window)
        rel = rel_m.group(1) if rel_m else ""
        out.append(t[last:s])
        out.append('src="' + rel + photo(HOME_HERO[idx % len(HOME_HERO)]) + '"')
        last = e
        idx += 1
    out.append(t[last:])
    return "".join(out)


def fix_asset_anchors(t: str, rel: str, langdir: str) -> str:
    """A captured menu link to a CDN document (the maintenance price list PDF)
    would otherwise be swept into a photograph by the asset pass. A link must
    land on content, so it goes to the maintenance section instead."""
    return re.sub(r'href="[^"]*assets/(?:photo|brand)/[^"]*"',
                  'href="' + rel + langdir + 'service-booking/index.html#maintenance"', t)


def inject_home_anchors(t: str) -> str:
    """Stable ids on the home page's own sections, so menu items can land on
    the exact block they promise: #models (the finder grid), #dealers (the
    showroom directory), #about (the Who We Are strip)."""
    at = t.find("tab_switcher")
    if at != -1:
        s = t.rfind("<section", 0, at)
        if s != -1 and 'id="' not in t[s:t.find(">", s)]:
            t = t[:s + len("<section")] + ' id="models"' + t[s + len("<section"):]
    for marker, anchor in (("showroom", "dealers"), ("Who We Are", "about"), ("من نحن", "about")):
        at = t.find(marker)
        if at == -1:
            continue
        if 'id="%s"' % anchor in t:
            continue
        s = t.rfind("<section", 0, at)
        if s == -1:
            continue
        gt = t.find(">", s)
        if 'id="' in t[s:gt]:
            continue
        t = t[:s + len("<section")] + f' id="{anchor}"' + t[s + len("<section"):]
    return t


def aftercare_band(rel: str, lang: str, langdir: str) -> str:
    """The ownership and aftercare band on the service page: one anchored card
    per aftersales promise the menus point at, with the synthetic maintenance
    price list the old PDF link now lands on."""
    ar = lang == "ar"
    def T(en, arb):
        return arb if ar else en
    book = rel + langdir + "service-booking/index.html"
    contact = rel + langdir + "contact-us/index.html"
    cards = [
        ("promise", T("Customer Promise", "وعد العملاء"), photo("interior"),
         T("Transparent pricing, genuine parts and a courtesy status update at every step. If a repair takes longer than promised, your next periodic service is on us.",
           "أسعار شفافة وقطع أصلية وتحديث لحالة السيارة في كل خطوة. إذا تأخر الإصلاح عن الموعد الموعود، فالصيانة الدورية التالية على حسابنا."),
         T("Book with the promise", "احجز الآن"), book),
        ("network", T("Aftersales Network", "شبكة ما بعد البيع"), photo("hero-desert-road"),
         T("Nine service centers across the Kingdom — Jeddah, Makkah, Madinah, Taif, Tabuk, Abha, Khamis Mushait and Yanbu — plus quick-service lanes for while-you-wait jobs.",
           "تسعة مراكز خدمة في أنحاء المملكة — جدة ومكة والمدينة والطائف وتبوك وأبها وخميس مشيط وينبع — مع مسارات خدمة سريعة للأعمال الفورية."),
         T("Find your center", "اعثر على مركزك"), rel + langdir + "index.html#dealers"),
        ("maintenance", T("Periodic Maintenance", "الصيانة الدورية"), photo("service"),
         T("Fixed-price scheduled services, booked online in under a minute.",
           "خدمات مجدولة بأسعار ثابتة، تُحجز عبر الإنترنت في أقل من دقيقة."),
         T("Book maintenance", "احجز الصيانة"), book),
        ("parts", T("Parts &amp; Accessories", "قطع الغيار والإكسسوارات"), photo("night-tech"),
         T("Genuine D·Auto parts with a 12-month warranty, and an accessory range fitted while you wait at any service center.",
           "قطع غيار دي أوتو الأصلية بضمان 12 شهراً، ومجموعة إكسسوارات تُركب أثناء انتظارك في أي مركز خدمة."),
         T("Ask about parts", "استفسر عن القطع"), contact),
        ("warranty", T("Warranty", "الضمان"), photo("hero-sunset-road"),
         T("Every new D·Auto carries a 5-year / 100,000 km vehicle warranty and 8 years on the powertrain. Check your cover from any service center.",
           "كل سيارة دي أوتو جديدة تأتي بضمان 5 سنوات أو 100,000 كم وضمان 8 سنوات على مجموعة الدفع. تحقق من تغطيتك في أي مركز خدمة."),
         T("Warranty questions", "أسئلة الضمان"), contact),
        ("connect", T("D·Connect", "دي كونكت"), photo("interior"),
         T("The connected-car service: remote lock, climate pre-start, live vehicle health and service alerts in one app, free for 5 years.",
           "خدمة السيارة المتصلة: قفل عن بُعد وتشغيل مسبق للتكييف وحالة السيارة المباشرة وتنبيهات الصيانة في تطبيق واحد، مجاناً لمدة 5 سنوات."),
         T("See it in service", "اطلبها مع الصيانة"), book),
    ]
    prices = [("10,000 km", "399"), ("20,000 km", "549"), ("40,000 km", "899"), ("60,000 km", "1,190")]
    price_rows = "".join(
        f'<tr><td>{k}</td><td>{T("SAR", "ر.س")} {v}</td></tr>' for k, v in prices)
    card_html = "".join(
        f'<article class="dps-care-card" id="{cid}">'
        f'<img src="{rel}{img}" alt="" loading="lazy">'
        f'<div class="dps-care-body"><h3>{title}</h3><p>{text}</p>'
        + (f'<table class="dps-price-table"><tbody>{price_rows}</tbody></table>' if cid == "maintenance" else "")
        + f'<a class="dps-care-cta" href="{href}">{cta}</a></div></article>'
        for cid, title, img, text, cta, href in cards)
    return (f'<section class="dps-band" id="aftercare" dir="{"rtl" if ar else "ltr"}">'
            f'<div class="dps-band-head"><h2>{T("Ownership &amp; Aftercare", "الملكية وخدمات ما بعد البيع")}</h2>'
            f'<p>{T("Everything that happens after the keys: one promise, one network, one app.", "كل ما يأتي بعد استلام المفاتيح: وعد واحد وشبكة واحدة وتطبيق واحد.")}</p></div>'
            f'<div class="dps-band-grid">{card_html}</div></section>')


def offers_grid(rel: str, lang: str, langdir: str) -> str:
    """The offers landing page's actual content: the running national offers,
    each one a door to the page where it is redeemed. The aftersales half
    carries its own anchor because the menus link straight to it."""
    ar = lang == "ar"
    def T(en, arb):
        return arb if ar else en
    def card(img, kicker, title, text, cta, href):
        return (f'<article class="dps-offer-card"><img src="{rel}{img}" alt="" loading="lazy">'
                f'<div class="dps-care-body"><span class="dps-kicker">{kicker}</span>'
                f'<h3>{title}</h3><p>{text}</p><a class="dps-care-cta" href="{href}">{cta}</a></div></article>')
    sales = (
        card(photo("terra-max"), T("Family offer", "عرض العائلة"),
             T("Back to School, sorted", "العودة للمدارس بلا عناء"),
             T("Own the family SUV from SAR 929 a month, with the first scheduled service free.",
               "امتلك سيارة العائلة بدءاً من 929 ر.س شهرياً، مع أول صيانة مجدولة مجاناً."),
             T("See the campaign", "شاهد الحملة"), rel + langdir + "offers/back-to-school/index.html") +
        card(photo("vanta"), T("Finance offer", "عرض التمويل"),
             T("VANTA from SAR 929 / month", "فانتا من 929 ر.س شهرياً"),
             T("The flagship SUV with 0% down payment for salary-transfer customers this quarter.",
               "السيارة الرائدة بدفعة أولى 0% لعملاء تحويل الراتب هذا الربع."),
             T("Explore the VANTA", "اكتشف فانتا"), rel + langdir + "models/vanta/index.html") +
        card(photo("showroom-light"), T("Season event", "فعالية الموسم"),
             T("National Day showcase", "معرض اليوم الوطني"),
             T("Special editions and same-day test drives at every showroom on September 23.",
               "إصدارات خاصة وتجارب قيادة في نفس اليوم في جميع المعارض يوم 23 سبتمبر."),
             T("Register interest", "سجل اهتمامك"), rel + langdir + "contact-us/index.html"))
    after = (
        card(photo("service"), T("Aftersales offer", "عرض ما بعد البيع"),
             T("Service Season: 20% off", "موسم الصيانة: خصم 20%"),
             T("Twenty percent off every scheduled maintenance booked online this month.",
               "خصم عشرون بالمئة على كل صيانة مجدولة تُحجز عبر الإنترنت هذا الشهر."),
             T("Book a service", "احجز صيانة"), rel + langdir + "service-booking/index.html#maintenance") +
        card(photo("city-rain"), T("Trade-in", "استبدال"),
             T("Upgrade with trade-in boost", "ارتقِ بسيارتك مع مكافأة الاستبدال"),
             T("Bring any car for a same-day valuation and an extra SAR 3,000 toward a new D·Auto.",
               "أحضر أي سيارة لتقييم فوري واحصل على 3,000 ر.س إضافية عند شراء دي أوتو جديدة."),
             T("Get a valuation", "احصل على تقييم"), rel + langdir + "contact-us/index.html"))
    return (f'<section class="dps-band" id="offers-grid" dir="{"rtl" if ar else "ltr"}">'
            f'<div class="dps-band-head"><h2>{T("Current offers", "العروض الحالية")}</h2>'
            f'<p>{T("Every offer below is live on this demonstration site; each card opens the page where it happens.", "كل عرض أدناه فعّال في هذا الموقع التجريبي؛ وكل بطاقة تفتح الصفحة التي يتحقق فيها.")}</p></div>'
            f'<div class="dps-band-grid">{sales}</div>'
            f'<div class="dps-band-head" id="aftersales"><h2>{T("Aftersales offers", "عروض ما بعد البيع")}</h2></div>'
            f'<div class="dps-band-grid">{after}</div></section>')


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


def company_main(rel: str, lang: str, langdir: str) -> str:
    """The company page: the corporate and legal destinations the menus
    promise, each as its own anchored section. All copy is authored for the
    fictitious brand."""
    ar = lang == "ar"
    def T(en, arb):
        return arb if ar else en
    contact = rel + langdir + "contact-us/index.html"
    roles = [
        (T("Service Advisor — Jeddah", "مستشار خدمة — جدة"),
         T("Front-of-house at our busiest service center.", "واجهة الاستقبال في أكثر مراكزنا نشاطاً.")),
        (T("EV Technician — Riyadh", "فني مركبات كهربائية — الرياض"),
         T("Certified high-voltage work on the coming E-Series.", "أعمال الجهد العالي المعتمدة لسلسلة E-Series القادمة.")),
        (T("CRM Specialist — Jeddah", "أخصائي إدارة علاقات العملاء — جدة"),
         T("Own the customer journeys this very site demonstrates.", "تولَّ رحلات العملاء التي يعرضها هذا الموقع.")),
    ]
    roles_html = "".join(
        f'<article class="dps-care-card"><div class="dps-care-body"><h3>{r}</h3><p>{d}</p>'
        f'<a class="dps-care-cta" href="{contact}">{T("Apply via contact desk", "قدّم عبر مكتب التواصل")}</a></div></article>'
        for r, d in roles)
    legal = [
        ("privacy", T("Privacy Policy", "سياسة الخصوصية"),
         T("This is a product demonstration. The only personal data this site touches is the demo contact identity a visitor explicitly creates, which exists solely inside the connected engagement-platform demo account and can be reset from the demo panel at any time. Nothing is sold, shared or used for advertising.",
           "هذا موقع عرض توضيحي. البيانات الشخصية الوحيدة التي يتعامل معها الموقع هي هوية جهة الاتصال التجريبية التي ينشئها الزائر بنفسه، وتوجد فقط داخل حساب العرض الخاص بمنصة التفاعل ويمكن إعادة تعيينها من لوحة العرض في أي وقت. لا يُباع أي شيء ولا يُشارك ولا يُستخدم للإعلان."),),
        ("terms", T("Terms &amp; Legal", "الشروط والأحكام"),
         T("D·Auto is a fictitious brand created for demonstrations. Vehicles, prices, offers and showrooms on this site are invented; nothing here is an offer to sell a real vehicle, and no real manufacturer or distributor is represented.",
           "دي أوتو علامة تجارية خيالية أُنشئت لأغراض العرض. السيارات والأسعار والعروض والمعارض في هذا الموقع مبتكرة؛ ولا يشكّل أي محتوى هنا عرضاً لبيع سيارة حقيقية، ولا يمثّل أي مصنّع أو موزّع حقيقي."),),
        ("cookies", T("Cookies", "ملفات تعريف الارتباط"),
         T("The site stores only what the demonstration needs in your browser: the demo session, the saved-cars list and widget display state, all namespaced to this demo and cleared by the panel's reset control. There are no advertising or analytics trackers.",
           "يخزّن الموقع في متصفحك ما يحتاجه العرض فقط: جلسة العرض وقائمة السيارات المحفوظة وحالة عرض الودجات، وكلها ضمن نطاق هذا العرض وتُمسح بزر إعادة التعيين في اللوحة. لا توجد متتبعات إعلانات أو تحليلات."),),
    ]
    legal_html = "".join(
        f'<section class="dps-page-section" id="{lid}"><h2>{title}</h2><p>{text}</p></section>'
        for lid, title, text in legal)
    return f"""<main class="dps-page" dir="{'rtl' if ar else 'ltr'}">
<div class="dps-page-hero"><img src="{rel}{photo('interchange')}" alt="">
<div class="dps-page-hero-text"><h1>{T('D·Auto Motors Co.', 'شركة دي أوتو للسيارات')}</h1>
<p>{T('The national distributor of a car brand that exists to demonstrate what great customer engagement looks like.', 'الموزّع الوطني لعلامة سيارات وُجدت لتعرض كيف يبدو التفاعل المتميز مع العملاء.')}</p></div></div>
<section class="dps-page-section" id="about"><h2>{T('Who we are', 'من نحن')}</h2>
<p>{T('D·Auto Motors Co. distributes the sixteen-model D·Auto range across the Kingdom: fifteen showrooms, nine service centers and one promise — that every owner is known, remembered and looked after on every channel they use.',
      'توزّع شركة دي أوتو للسيارات تشكيلة دي أوتو المكوّنة من ستة عشر طرازاً في أنحاء المملكة: خمسة عشر معرضاً وتسعة مراكز خدمة ووعد واحد — أن يكون كل مالك معروفاً ومُتذكَّراً ومُعتنى به في كل قناة يستخدمها.')}</p></section>
<section class="dps-page-section" id="innovation"><h2>{T('Innovation', 'الابتكار')}</h2>
<p>{T('From the SenseShield driver-assistance suite to the D·Connect connected-car app and the coming all-electric E-Series line, the range is built digital-first — which is exactly why this demonstration site can show a live event for everything a visitor does.',
      'من حزمة مساعدة السائق سينس شيلد إلى تطبيق السيارة المتصلة دي كونكت وسلسلة E-Series الكهربائية القادمة، بُنيت التشكيلة رقمياً أولاً — ولهذا يستطيع موقع العرض هذا إظهار حدث مباشر لكل ما يفعله الزائر.')}</p>
<img class="dps-page-img" src="{rel}{photo('night-tech')}" alt=""></section>
<section class="dps-page-section" id="careers"><h2>{T('Careers', 'الوظائف')}</h2>
<p>{T('Three roles are open this quarter.', 'ثلاث وظائف متاحة هذا الربع.')}</p>
<div class="dps-band-grid">{roles_html}</div></section>
<section class="dps-page-section" id="fleet"><h2>{T('Fleet &amp; business', 'الأساطيل والأعمال')}</h2>
<p>{T('From five cars to five hundred: fleet pricing, scheduled-maintenance contracts and a dedicated account manager for every business customer.',
      'من خمس سيارات إلى خمسمئة: أسعار أساطيل وعقود صيانة مجدولة ومدير حساب مخصص لكل عميل أعمال.')}</p>
<img class="dps-page-img" src="{rel}{photo('fleet')}" alt="">
<p><a class="dps-care-cta" href="{contact}">{T('Request a fleet quote', 'اطلب عرض أسطول')}</a></p></section>
{legal_html}
</main>"""


def build(name: str, spec: dict) -> str:
    out_path = spec["out"]
    rel = rel_to_root(out_path)
    lang = "ar" if name.endswith(".ar") else "en"
    langdir = LANGDIR[lang]
    site_path = out_path[3:] if out_path.startswith("ar/") else out_path

    if spec.get("synthetic") == "company":
        home_src = (HYD / f"home.{lang}.html").read_text(errors="ignore")
        hm = re.search(r"<header\b.*?</header>", home_src, re.S)
        fm = re.search(r"<footer\b.*?</footer>", home_src, re.S)
        src = ""
        body_attrs = ""
        body = (hm.group(0) if hm else "") + company_main(rel, lang, langdir) + (fm.group(0) if fm else "")
        title = None
        desc = None
        video_thumbs, hero_list = {}, []
    else:
        src = (HYD / f"{name}.html").read_text(errors="ignore")
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
        body = inject_home_anchors(body)
    body = rewrite_links(body, rel)
    body = fix_asset_anchors(body, rel, langdir)
    body = swap_logos(body)
    body = strip_profile_button(body)
    body = wire_test_drive(body, spec.get("product", "vanta"))

    # The authored bands ride just above the footer: the aftercare cards on
    # the service page, the offers grid on the offers landing page.
    if name.startswith("service."):
        body = re.sub(r"(<footer)", aftercare_band(rel, lang, langdir).replace("\\", "\\\\") + r"\n\1", body, count=1)
    if name.startswith("offers."):
        body = re.sub(r"(<footer)", offers_grid(rel, lang, langdir).replace("\\", "\\\\") + r"\n\1", body, count=1)

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
    if spec.get("synthetic") == "company":
        page_title = ("شركة دي أوتو للسيارات | دي أوتو" if lang == "ar"
                      else "D·Auto Motors Co. | D·Auto")
        page_desc = ("عن شركة دي أوتو: من نحن، الابتكار، الوظائف، الأساطيل والسياسات."
                     if lang == "ar" else
                     "About D·Auto Motors Co.: who we are, innovation, careers, fleet and policies.")
    else:
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
