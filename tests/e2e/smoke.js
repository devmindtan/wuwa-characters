#!/usr/bin/env node
// End-to-end smoke test (AGENTS.md §5). Needs the app running (./run.sh) and Chrome.
//   node tests/e2e/smoke.js                 # http://127.0.0.1:8000
//   BASE_URL=https://wuwa-characters.vercel.app node tests/e2e/smoke.js
// playwright-core is resolved from PLAYWRIGHT_CORE (a path) or the normal module path.
const {chromium} = require(process.env.PLAYWRIGHT_CORE || 'playwright-core');

const BASE = (process.env.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const VI_CHARS = /[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]/i;
const issues = [];
const check = (ok, msg) => { if (!ok) issues.push(msg); };

async function open(page, slug) {
  await page.goto(`${BASE}/#/character/${slug}`);
  await page.waitForSelector('#d-crumb span', {state: 'attached'});
  await page.waitForTimeout(250);
}

async function popupLead(page) {
  return page.evaluate(() => ({
    title: document.querySelector('#mech-title').textContent,
    summary: document.querySelector('#mech-summary').textContent,
    source: document.querySelector('#mech-source').textContent,
    occ: document.querySelectorAll('.mech-occ-item').length,
    users: [...document.querySelectorAll('#mech-users-list .mech-user b')].map((b) => b.textContent),
  }));
}

async function clickTerm(page, selector) {
  const el = page.locator(selector).first();
  await el.scrollIntoViewIfNeeded();
  await el.click();
  await page.waitForTimeout(200);
}

async function run(tag, viewport) {
  const page = await (await browser.newContext({viewport})).newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));

  // list + filter
  await page.goto(`${BASE}/#/`);
  await page.waitForSelector('.card');
  const total = await page.locator('.card').count();
  check(total >= 60, `${tag}: only ${total} cards`);
  await page.fill('#q', 'phro');
  await page.waitForTimeout(250);
  check(await page.locator('.card:visible').count() === 1, `${tag}: search filter`);
  // full-text search over skill text (arrives from /api/search in the background)
  await page.waitForFunction(() => document.querySelector('#q') && true);
  await page.waitForTimeout(600);
  await page.fill('#q', 'aftersound');
  await page.waitForTimeout(250);
  check(await page.locator('.card:visible').count() >= 1, `${tag}: full-text search ("aftersound")`);
  await page.fill('#q', '');

  for (const slug of ['phrolova', 'cartethyia', 'jinhsi', 'hsin', 'calcharo']) {
    await open(page, slug);
    for (const tab of ['tree', 'skills', 'chain', 'mats']) {
      await page.click('#tab-btn-' + tab);
      await page.waitForTimeout(80);
    }
    await page.click('#tab-btn-skills');
    check(!(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)), `${tag} ${slug}: horizontal overflow`);
    check(await page.locator('#tab-skills .mech-link').count() > 0, `${tag} ${slug}: no mechanic links`);
    check(await page.locator('.trait').count() >= 3, `${tag} ${slug}: fewer than 3 kit traits`);

    // mechanic popup -> jump to the passage
    await clickTerm(page, '#tab-skills .mech-link:visible');
    const lead = await popupLead(page);
    check(lead.summary.length > 0 && lead.occ > 0, `${tag} ${slug}: empty mechanic popup (${lead.title})`);
    await page.locator('.mech-go').first().click();
    await page.waitForTimeout(450);
    check(await page.locator('.hit').count() > 0, `${tag} ${slug}: "go" did not highlight a passage`);

    // EN must not leave Vietnamese text on screen
    await page.click('.detail-actions [data-lang="en"]');
    await page.waitForTimeout(250);
    const left = await page.evaluate((src) => {
      const re = new RegExp(src, 'i');
      const out = [];
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (w.nextNode()) {
        const el = w.currentNode.parentElement;
        if (!el || el.closest('script,style,[hidden],footer')) continue;
        if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') continue;
        if (re.test(w.currentNode.nodeValue)) out.push(w.currentNode.nodeValue.trim().slice(0, 40));
      }
      return out.slice(0, 3);
    }, VI_CHARS.source);
    check(!left.length, `${tag} ${slug}: Vietnamese left in EN mode: ${left.join(' | ')}`);
    await page.click('.detail-actions [data-lang="vi"]');
    await page.click('#back');
    await page.waitForTimeout(200);
    check(await page.evaluate(() => location.hash) === '#/', `${tag} ${slug}: back did not return to the list`);
  }

  // interactions: element filter dropdown, level slider, Forte tree, material upgrade slider, list language
  await page.goto(`${BASE}/#/`);
  await page.waitForSelector('.card');
  const dd = page.locator('.dd').first();  // element filter (custom dropdown over #f-el)
  await dd.locator('.dd-btn').click();
  await dd.locator('.dd-opt:not(.dd-all)').first().click();
  await page.waitForTimeout(200);
  const filtered = await page.locator('.card:visible').count();
  check(filtered > 0 && filtered < total, `${tag}: element dropdown filter (${filtered}/${total})`);
  await dd.locator('.dd-btn').click();
  await dd.locator('.dd-all').click();
  await page.click('.head-meta .lang-switch [data-lang="en"]').catch(() => {});
  await page.waitForTimeout(150);
  check(await page.evaluate(() => document.documentElement.lang) === 'en', `${tag}: list page language switch`);
  await page.click('.head-meta .lang-switch [data-lang="vi"]').catch(() => {});

  await open(page, 'jinhsi');
  await page.click('#tab-btn-skills');
  const lv = page.locator('#tab-skills .lv-range').first();
  if (await lv.count()) {
    const panel = page.locator('#tab-skills details.mult').first();  // the slider lives in the collapsed multipliers panel
    if (!(await panel.evaluate((d) => d.open))) await panel.locator('summary').click();
    await lv.scrollIntoViewIfNeeded();
    await lv.fill('7');
    await page.waitForTimeout(150);
    check(await page.evaluate(() => [...document.querySelectorAll('.lv-range')].every((r) => r.value === '7')), `${tag}: level slider sync`);
  }
  await page.click('#tab-btn-tree');
  const nodes = page.locator('#d-tree .fn');
  await nodes.nth(1).click();
  await page.waitForTimeout(150);
  check(await page.locator('#d-tree .fn.is-sel').count() === 1 && (await page.locator('#d-tree-detail').innerText()).length > 0,
    `${tag}: Forte tree selection`);
  await page.click('#tab-btn-mats');
  const up = page.locator('.up-range').first();
  if (await up.count()) {
    const before = await page.locator('#tab-mats').innerText();
    await up.scrollIntoViewIfNeeded();
    await up.fill(await up.getAttribute('min'));
    await page.waitForTimeout(150);
    check((await page.locator('#tab-mats').innerText()) !== before, `${tag}: material upgrade slider`);
  }

  // known cases
  await open(page, 'phrolova');
  await page.click('#tab-btn-skills');
  check(await page.locator('#tab-skills .move-link', {hasText: 'Movement of Fate and Finality'}).count() > 0, `${tag}: Movement of Fate and Finality not linked`);
  await clickTerm(page, '#tab-skills .mech-link[data-mech="Hazy Dream"]');
  let lead = await popupLead(page);
  check(/Cantarella/.test(lead.source) && lead.users.includes('Cantarella'), `${tag}: Hazy Dream cross-character quote`);
  await page.keyboard.press('Escape');

  await page.click('.trait-cc');
  await page.waitForTimeout(200);
  lead = await popupLead(page);
  check(lead.occ >= 3 && lead.users.length > 5, `${tag}: crowd-control trait popup`);
  await page.locator('.mech-go').nth(1).click();
  await page.waitForTimeout(450);
  check(await page.locator('[data-line].hit').count() === 1, `${tag}: trait evidence did not highlight exactly one line`);

  // signature weapon tab: R1-R5 values, level slider (data shown in-page, not a wiki link)
  await page.click('#tab-btn-weapon');
  await page.waitForTimeout(200);
  check(await page.evaluate(() => !document.querySelector('#tab-weapon').hidden), `${tag}: weapon tab did not open`);
  const r1 = await page.locator('.wv').first().textContent();
  await page.click('[data-wrank="5"]');
  check(r1 === '12%' && (await page.locator('.wv').first().textContent()) === '24%', `${tag}: weapon rank values (${r1})`);
  const wlv = page.locator('.wp-lv');
  await wlv.scrollIntoViewIfNeeded();
  await wlv.fill('0');
  check((await page.locator('.wp-atk').textContent()) === '47', `${tag}: weapon level slider`);
  await page.click('.detail-actions [data-lang="en"]');
  check(/^ATK is increased by 24%/.test(await page.locator('.wp-eff-text').innerText()), `${tag}: weapon effect in EN`);
  await page.click('.detail-actions [data-lang="vi"]');

  // combo tab: player actions in order, each with short results; assumptions (S0-S6, weapon) filter them
  await page.click('#tab-btn-combo');
  await page.waitForSelector('.cb-act');
  check(await page.locator('[data-cb-rot]').count() >= 2 && await page.locator('.cb-formula .cb-tok').count() > 5,
    `${tag}: combo picker / formula`);
  await page.click('[data-cb-rot="1"]');
  await page.waitForSelector('.cb-act');
  check((await page.locator('.cb-say').allInnerTexts()).some((x) => x.includes('Đánh thường 3 đòn liên tiếp')), `${tag}: Basic 1-3 not merged`);
  const sumText = await page.locator('.cb-sum').innerText();
  check(/Reincarnate → Resolving Chord → Maestro/.test(sumText) && /\+5 Volatile Note - Strings/.test(sumText), `${tag}: combo summary`);
  const results = async (sel) => page.locator(sel).count();
  check(await results('.cb-res.is-weapon') > 0, `${tag}: weapon result missing`);
  const s0 = await results('.cb-res.is-chain');
  await page.click('[data-cb-s="6"]');
  check(await results('.cb-res.is-chain') > s0, `${tag}: chain assumption did not add results`);
  await page.click('[data-cb-weapon]');
  check(await results('.cb-res.is-weapon') === 0, `${tag}: weapon assumption`);
  await page.locator('.cb-res[data-cb-target^="skill-"]').first().click();
  await page.waitForTimeout(450);
  check(await page.evaluate(() => !document.querySelector('#tab-skills').hidden) && (await page.locator('[data-line].hit').count()) === 1,
    `${tag}: combo result did not jump to its kit line`);

  // formula strip: same-name moves in a row collapse, a chip jumps to its step
  await open(page, 'hiyuki');
  await page.click('#tab-btn-combo');
  await page.waitForFunction(() => document.querySelector('#d-combo')?.dataset.slug === 'hiyuki' && document.querySelector('.cb-formula'));
  check((await page.locator('.cb-formula').innerText()).includes('Foreclaimed Self 1–5'), `${tag}: formula did not group Foreclaimed Self 1-5`);
  await page.locator('.cb-tok[data-cb-go]').nth(2).click();
  await page.waitForTimeout(100);
  check(await page.locator('.cb-act.flash').count() === 1, `${tag}: formula chip did not jump to its step`);

  // old Vietnamese route still opens and is rewritten to the English one
  await page.goto(`${BASE}/#/nhan-vat/chisa`);
  await page.waitForSelector('#d-crumb span', {state: 'attached'});
  check(await page.evaluate(() => location.hash) === '#/character/chisa', `${tag}: old #/nhan-vat/ link not redirected`);
  await page.waitForTimeout(250);
  await page.click('.trait-havoc_bane');
  await page.waitForTimeout(200);
  check(await page.locator('.ms-list li').count() >= 3, `${tag}: Havoc Bane summary bullets`);
  await page.keyboard.press('Escape');

  if (viewport.width > 800) {  // tooltips are hover-only
    await page.mouse.move(0, 0);
    const box = await page.locator('.trait').first().boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForTimeout(250);
    check(await page.locator('.tip.show').count() === 1, `${tag}: tooltip did not show within 250ms`);
  }

  check(!errors.length, `${tag}: page errors: ${errors.join('; ')}`);
  console.log(`${tag}: done`);
}

let browser;
(async () => {
  browser = await chromium.launch({channel: process.env.BROWSER_CHANNEL || 'chrome'});
  try {
    await run('desktop', {width: 1366, height: 850});
    await run('mobile', {width: 390, height: 844});
  } finally {
    await browser.close();
  }
  if (issues.length) {
    console.error('FAIL\n- ' + issues.join('\n- '));
    process.exit(1);
  }
  console.log('PASS');
})();
