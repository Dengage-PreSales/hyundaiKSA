#!/usr/bin/env node
// Screenshot locally served replica pages, for the side-by-side check against
// reference/shots/. Serves nothing itself: run `python3 -m http.server 8123`
// from the repository root first (or pass a different port as PORT=).
// External hosts are unreachable from this sandbox's browser, which doubles
// as the factory's own hygiene rule: layout must stand with no SDK loaded.
import { createRequire } from 'module';
import { mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
const { chromium } = createRequire('/opt/node22/lib/node_modules/')('playwright');

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'reference', 'local-shots');
mkdirSync(OUT, { recursive: true });
const PORT = process.env.PORT || '8123';

const pages = process.argv.slice(2);
if (!pages.length) {
  console.log('usage: node tools/shot-local.mjs <path> [...]  e.g. en/mynaghi/');
  process.exit(1);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
for (const p of pages) {
  const page = await ctx.newPage();
  const name = p.replace(/[^a-z0-9]+/gi, '_').replace(/^_+|_+$/g, '') || 'root';
  try {
    // domcontentloaded, not load: with no network the SDK loader's failure
    // stalls the load event for many seconds while autoplay cycles on.
    await page.goto(`http://127.0.0.1:${PORT}/${p}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(900);
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.8;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 80));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(OUT, `${name}.png`), fullPage: true });
    const errors = await page.evaluate(() => window.__dpsErrors || []);
    console.log(`${p} -> ${name}.png`, errors.length ? `JS errors: ${errors.join(' | ')}` : '');
  } catch (e) {
    console.log(`${p}: FAILED ${String(e).split('\n')[0]}`);
  }
  await page.close();
}
await browser.close();
