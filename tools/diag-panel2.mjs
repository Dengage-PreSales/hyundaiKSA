import { createRequire } from 'module';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(process.argv[2] || 'http://localhost:8123/index.html', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(1200);
await page.click('[data-open="#dengage-panel"]');
await page.waitForTimeout(400);

const out = await page.evaluate(() => {
  const r = {};
  const panel = document.getElementById('dengage-panel');
  const cs = getComputedStyle(panel);
  r.varAtPanel = cs.getPropertyValue('--hy-surface');
  r.bgBefore = cs.backgroundColor;

  // What did the parser keep of the .dps-modal rule?
  const sheet = [...document.styleSheets].find(s => s.href && s.href.includes('demo-controls'));
  r.demoRules = [];
  for (const rule of sheet.cssRules) {
    if (rule.selectorText && /dps-modal|dps-drawer/.test(rule.selectorText)) {
      r.demoRules.push({ sel: rule.selectorText, bg: rule.style.background, bgColor: rule.style.backgroundColor, len: rule.style.length });
    }
  }

  // Probe 1: inline literal
  panel.style.background = '#ff00aa';
  r.inlineLiteral = getComputedStyle(panel).backgroundColor;
  // Probe 2: inline var
  panel.style.background = 'var(--hy-surface)';
  r.inlineVar = getComputedStyle(panel).backgroundColor;
  panel.style.background = '';

  // Probe 3: registered property? (a @property with initial transparent could do this)
  r.propertyRules = [];
  for (const s of document.styleSheets) {
    try { for (const rule of s.cssRules) {
      if (rule.constructor.name === 'CSSPropertyRule') r.propertyRules.push({ sheet: (s.href||'inline').split('/').pop(), name: rule.name, initial: rule.initialValue, inherits: rule.inherits, syntax: rule.syntax });
    } } catch (e) {}
  }
  return r;
});
console.log(JSON.stringify(out, null, 2));
await browser.close();
