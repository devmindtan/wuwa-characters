// Render public/assets/og-image.jpg (1200x630 link-preview thumbnail) from og.html.
// Usage: node scripts/og/render.js   (needs playwright-core and Google Chrome;
//   e.g. `npx -p @playwright/cli node scripts/og/render.js` or set PLAYWRIGHT_CORE=/path/to/playwright-core)
// Update the patch number / Resonator count in og.html and in the og:* tags of
// public/index.html together when the game version changes.
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_CORE || 'playwright-core');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  await page.goto('file://' + path.join(__dirname, 'og.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const broken = await page.evaluate(() => [...document.images].filter((i) => !i.naturalWidth).map((i) => i.src));
  if (broken.length) throw new Error('images failed to load: ' + broken.join(', '));
  const out = path.join(__dirname, '..', '..', 'public', 'assets', 'og-image.jpg');
  await page.screenshot({ path: out, type: 'jpeg', quality: 88 });
  console.log('wrote', out);
  await browser.close();
})();
