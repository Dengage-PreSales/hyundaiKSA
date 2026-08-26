#!/usr/bin/env node
// Render each source page in Chromium and save the HYDRATED DOM plus a
// full-page screenshot. The environment's egress proxy resets Chromium's own
// CONNECTs, so the browser runs fully offline: every request is intercepted
// and fetched by Node instead (Node's fetch honours HTTPS_PROXY via
// NODE_USE_ENV_PROXY and trusts the proxy CA via NODE_EXTRA_CA_CERTS), then
// fulfilled into the page. No TLS verification is disabled anywhere.
//
// Usage: NODE_USE_ENV_PROXY=1 NODE_PATH=/opt/node22/lib/node_modules \
//        node tools/hydrate-dump.mjs [pageName ...]
import { createRequire } from 'module';
import { mkdirSync, writeFileSync } from 'fs';
const { chromium } = createRequire('/opt/node22/lib/node_modules/')('playwright');
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT_DOM = join(ROOT, 'reference', 'hydrated');
const OUT_SHOT = join(ROOT, 'reference', 'shots');
mkdirSync(OUT_DOM, { recursive: true });
mkdirSync(OUT_SHOT, { recursive: true });

const PAGES = {
  'gateway.ar': 'https://hyundaiksa.com/ar',
  'gateway.en': 'https://hyundaiksa.com/en',
  'home.en': 'https://hyundaiksa.com/en/mynaghi',
  'home.ar': 'https://hyundaiksa.com/ar/mynaghi',
  'tucson.en': 'https://hyundaiksa.com/en/mynaghi/models/tucson',
  'tucson.ar': 'https://hyundaiksa.com/ar/mynaghi/models/tucson',
  'santafe.en': 'https://hyundaiksa.com/en/mynaghi/models/santa-fe',
  'santafe.ar': 'https://hyundaiksa.com/ar/mynaghi/models/santa-fe',
  'offers.en': 'https://hyundaiksa.com/en/mynaghi/offers',
  'offers.ar': 'https://hyundaiksa.com/ar/mynaghi/offers',
  'campaign.en': 'https://hyundaiksa.com/en/mynaghi/offers/backtoschool',
  'campaign.ar': 'https://hyundaiksa.com/ar/mynaghi/offers/backtoschool',
  'service.en': 'https://hyundaiksa.com/en/mynaghi/service-booking',
  'service.ar': 'https://hyundaiksa.com/ar/mynaghi/service-booking',
  'contact.en': 'https://hyundaiksa.com/en/mynaghi/contact-us',
  'contact.ar': 'https://hyundaiksa.com/ar/mynaghi/contact-us',
};

// The rest of the model range. Paths come from the home-page grid links —
// note Elantra's capitalised path, which is how the live site spells it.
for (const slug of ['accent', 'azera', 'Elantra', 'grandi10', 'kona', 'palisade',
                    'sonata', 'stargazer', 'staria-premium', 'staria-van',
                    'staria-wagon', 'venue', 'creta', 'creta-grand']) {
  const key = slug.toLowerCase();
  PAGES[`${key}.en`] = `https://hyundaiksa.com/en/mynaghi/models/${slug}`;
  PAGES[`${key}.ar`] = `https://hyundaiksa.com/ar/mynaghi/models/${slug}`;
}

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36';
const cache = new Map();

async function relay(route) {
  const req = route.request();
  const url = req.url();
  if (req.method() !== 'GET') return route.abort();
  if (cache.has(url)) {
    const hit = cache.get(url);
    return route.fulfill({ status: hit.status, headers: hit.headers, body: hit.body });
  }
  try {
    const res = await fetch(url, {
      headers: { 'user-agent': UA, 'accept': req.headers()['accept'] || '*/*', 'accept-language': req.headers()['accept-language'] || 'en' },
      redirect: 'follow',
      signal: AbortSignal.timeout(45000),
    });
    const body = Buffer.from(await res.arrayBuffer());
    const headers = { 'content-type': res.headers.get('content-type') || 'application/octet-stream' };
    const entry = { status: res.status, headers, body };
    if (body.length < 8 * 1024 * 1024) cache.set(url, entry);
    return route.fulfill(entry);
  } catch (e) {
    return route.abort();
  }
}

const wanted = process.argv.slice(2);
const names = wanted.length ? wanted : Object.keys(PAGES);

const browser = await chromium.launch();
for (const name of names) {
  const url = PAGES[name];
  if (!url) { console.log('unknown page', name); continue; }
  const lang = name.endsWith('.ar') ? 'ar' : 'en';
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: UA,
    locale: lang === 'ar' ? 'ar-SA' : 'en-SA',
    permissions: [],           // geolocation prompts get denied, like a fresh visitor
    serviceWorkers: 'block',
  });
  await ctx.route('**/*', relay);
  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: 'load', timeout: 120000 });
    await page.waitForTimeout(3500);
    // Dismiss the cookie banner. "Reject All" on purpose: this crawl must not
    // land as consented traffic in Hyundai's production analytics.
    for (const label of ['Reject All', 'رفض الكل']) {
      const btn = page.getByRole('button', { name: label });
      if (await btn.count()) { await btn.first().click().catch(() => {}); break; }
    }
    await page.waitForTimeout(800);
    // Scroll through the page so lazy sections mount and reveal.
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.7;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 220));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(2500);
    const html = await page.content();
    writeFileSync(join(OUT_DOM, `${name}.html`), html);
    // Reveal-on-scroll sections screenshot at opacity 0 unless animations are
    // neutralised first. This is a screenshot aid only; the saved DOM above is
    // untouched.
    await page.addStyleTag({ content: '*{transition:none!important;animation:none!important} .opacity-0{opacity:1!important} .move-x-o,.move-y-o{transform:none!important;opacity:1!important}' });
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(OUT_SHOT, `${name}.png`), fullPage: true });
    console.log(`${name}: ${(html.length / 1024).toFixed(0)} KB DOM, screenshot saved`);
  } catch (e) {
    console.log(`${name}: FAILED ${String(e).split('\n')[0]}`);
  }
  await ctx.close();
}
await browser.close();
console.log('done');
