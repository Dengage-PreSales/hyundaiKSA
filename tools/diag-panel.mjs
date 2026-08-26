// Diagnose the launcher panel's computed styles on the local gateway.
import { createRequire } from 'module';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');

const URL_ = process.argv[2] || 'http://localhost:8123/index.html';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(URL_, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(1500);

await page.click('[data-open="#dengage-panel"]');
await page.waitForTimeout(600);

const report = await page.evaluate(() => {
  const out = {};
  const root = getComputedStyle(document.documentElement);
  out.tokens = {
    surface: root.getPropertyValue('--hy-surface').trim(),
    tint: root.getPropertyValue('--hy-tint').trim(),
    blue: root.getPropertyValue('--hy-blue').trim(),
    line: root.getPropertyValue('--hy-line').trim(),
  };
  const panel = document.getElementById('dengage-panel');
  if (!panel) { out.panel = 'MISSING'; return out; }
  const cs = getComputedStyle(panel);
  out.panel = {
    className: panel.className,
    open: panel.classList.contains('open'),
    background: cs.backgroundColor,
    display: cs.display,
    position: cs.position,
    zIndex: cs.zIndex,
    opacity: cs.opacity,
    visibility: cs.visibility,
    mixBlendMode: cs.mixBlendMode,
    backdropFilter: cs.backdropFilter,
    width: cs.width, height: cs.height,
  };
  // First card inside the launcher grid
  const card = panel.querySelector('#launcher-grid button, #launcher-grid .dps-card, #launcher-grid > *');
  if (card) {
    const cc = getComputedStyle(card);
    out.card = { tag: card.tagName, cls: card.className, background: cc.backgroundColor, color: cc.color, border: cc.borderColor };
  }
  const ref = panel.querySelector('#ref-grid');
  if (ref) {
    const rc = getComputedStyle(ref);
    out.refGrid = { background: rc.backgroundColor, display: rc.display, childCount: ref.children.length, text: ref.textContent.trim().slice(0, 80) };
  }
  // Does the demo-controls stylesheet actually apply? Probe a known rule.
  out.sheets = [...document.styleSheets].map(s => {
    let n = 0; try { n = s.cssRules.length; } catch (e) { n = -1; }
    return { href: (s.href || 'inline').split('/').slice(-2).join('/'), rules: n };
  });
  // Which rule wins background on the panel?
  out.matched = [];
  for (const sheet of document.styleSheets) {
    let rules = []; try { rules = [...sheet.cssRules]; } catch (e) { continue; }
    const walk = rs => { for (const r of rs) {
      if (r.cssRules) { walk([...r.cssRules]); continue; }
      if (!r.selectorText) continue;
      try { if (panel.matches(r.selectorText) && /background/.test(r.style.cssText)) {
        out.matched.push({ sheet: (sheet.href||'inline').split('/').pop(), sel: r.selectorText, css: r.style.cssText.slice(0,140) });
      } } catch (e) {}
    } };
    walk(rules);
  }
  return out;
});

console.log(JSON.stringify(report, null, 2));
await page.screenshot({ path: 'reference/local-shots/diag-gateway-panel.png' });
await browser.close();
