#!/usr/bin/env node
// Open the "Find a Car" mega-menu on the tenant home page and save its DOM,
// which only mounts on interaction and therefore is missing from the plain
// hydration dump. Same offline-browser relay as hydrate-dump.mjs.
import { createRequire } from 'module';
import { mkdirSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
const { chromium } = createRequire('/opt/node22/lib/node_modules/')('playwright');

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'reference', 'menu');
mkdirSync(OUT, { recursive: true });

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36';
const cache = new Map();
async function relay(route) {
  const req = route.request();
  const url = req.url();
  if (req.method() !== 'GET') return route.abort();
  if (cache.has(url)) { const h = cache.get(url); return route.fulfill(h); }
  try {
    const res = await fetch(url, { headers: { 'user-agent': UA, accept: req.headers()['accept'] || '*/*' }, redirect: 'follow', signal: AbortSignal.timeout(45000) });
    const body = Buffer.from(await res.arrayBuffer());
    const entry = { status: res.status, headers: { 'content-type': res.headers.get('content-type') || 'application/octet-stream' }, body };
    if (body.length < 8 * 1024 * 1024) cache.set(url, entry);
    return route.fulfill(entry);
  } catch { return route.abort(); }
}

const browser = await chromium.launch();
for (const lang of ['en', 'ar']) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, userAgent: UA, locale: lang === 'ar' ? 'ar-SA' : 'en-SA', serviceWorkers: 'block' });
  await ctx.route('**/*', relay);
  const page = await ctx.newPage();
  try {
    await page.goto(`https://hyundaiksa.com/${lang}/mynaghi`, { waitUntil: 'load', timeout: 120000 });
    await page.waitForTimeout(3000);
    for (const label of ['Reject All', 'رفض الكل']) {
      const btn = page.getByRole('button', { name: label });
      if (await btn.count()) { await btn.first().click().catch(() => {}); break; }
    }
    await page.waitForTimeout(500);
    const trigger = page.locator('header nav button, header nav a').first();
    // "Find a Car" is the first nav item in both languages; hover then click.
    await trigger.hover().catch(() => {});
    await page.waitForTimeout(800);
    await trigger.click().catch(() => {});
    await page.waitForTimeout(2500);
    // Walk every tab inside the opened menu so all categories mount.
    const tabs = page.locator('header [role="tab"], header nav [class*="tab"] button');
    const n = await tabs.count();
    for (let i = 0; i < n && i < 12; i++) {
      await tabs.nth(i).click().catch(() => {});
      await page.waitForTimeout(700);
    }
    const nav = await page.locator('header').first().evaluate(el => el.outerHTML);
    writeFileSync(join(OUT, `menu.${lang}.html`), nav);
    await page.screenshot({ path: join(OUT, `menu.${lang}.png`) });
    console.log(`${lang}: menu DOM ${(nav.length / 1024).toFixed(0)} KB`);
  } catch (e) { console.log(`${lang}: FAILED ${String(e).split('\n')[0]}`); }
  await ctx.close();
}
await browser.close();
console.log('done');
