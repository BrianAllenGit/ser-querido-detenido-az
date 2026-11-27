// Runs inside the official Playwright Docker image. See tools/audit.sh.
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const axeSrc = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const SITE = '/site', OUT = '/out';
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(SITE, path.normalize(p));
  if (!f.startsWith(SITE) || !fs.existsSync(f)) { res.writeHead(404); return res.end('nf'); }
  res.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
(async () => {
  await new Promise(r => server.listen(8080, r));
  const browser = await chromium.launch();
  const base = 'http://127.0.0.1:8080/';
  let fail = 0; const report = [];
  const log = s => { console.log(s); report.push(s); };
  for (const lang of ['es', 'en']) {
    const url = base + (lang === 'en' ? '?lang=en' : '');
    for (const [w, h] of [[375, 812], [1280, 800]]) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, bypassCSP: false });
      const page = await ctx.newPage(); const errs = [];
      page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      page.on('pageerror', e => errs.push(String(e)));
      page.on('request', r => { if (!r.url().startsWith(base)) errs.push('EXTERNAL REQUEST ' + r.url()); });
      await page.goto(url, { waitUntil: 'load' });
      const htmlLang = await page.evaluate(() => document.documentElement.lang);
      // axe is injected through CDP so the page's strict CSP stays on
      await page.evaluate(axeSrc).catch(async () => { await page.addScriptTag({ content: axeSrc }); });
      const res = await page.evaluate(async () => await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] } }));
      log(`axe ${lang} ${w}px lang=${htmlLang}: ${res.violations.length} violations, ${res.passes.length} rules passed, ${res.incomplete.length} incomplete, console errors: ${errs.length}`);
      for (const v of res.violations) { fail++; log(`  VIOLATION ${v.id}: ${v.help} (${v.nodes.length}) ${v.nodes[0].html.slice(0, 160)}`); }
      for (const v of res.incomplete) log(`  incomplete ${v.id}: ${v.nodes.length} node(s) ${v.nodes[0].html.slice(0,100)} ${(v.nodes[0].any[0]||{}).message||''}`);
      for (const e of errs) { fail++; log('  ERROR ' + e); }
      if (htmlLang !== lang) { fail++; log('  wrong lang'); }
      await page.screenshot({ path: `${OUT}/${lang}-${w}.png` });
      await page.screenshot({ path: `${OUT}/${lang}-${w}-full.png`, fullPage: true });
      await ctx.close();
    }
    for (const w of [320, 375, 768]) {
      const ctx = await browser.newContext({ viewport: { width: w, height: 800 } });
      const page = await ctx.newPage(); await page.goto(url, { waitUntil: 'load' });
      const r = await page.evaluate(() => {
        const vw = document.documentElement.clientWidth; const bad = [];
        for (const el of document.querySelectorAll('body *')) {
          const b = el.getBoundingClientRect();
          if (b.width && (b.right > vw + 0.5 || b.left < -0.5) && !el.closest('.skip')) bad.push(el.tagName + '.' + el.className + ' right=' + Math.round(b.right));
        }
        // tap targets: buttons and button-like links at least 44px tall
        const small = [...document.querySelectorAll('button,.btn')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).length;
        return { vw, sw: document.documentElement.scrollWidth, bad: bad.slice(0, 5), nbad: bad.length, small };
      });
      const ok = r.sw <= r.vw && r.nbad === 0 && r.small === 0; if (!ok) fail++;
      log(`overflow ${lang} ${w}px: scrollWidth ${r.sw} vs ${r.vw}, elements past the edge: ${r.nbad}, small tap targets: ${r.small} ${ok ? 'OK' : 'FAIL ' + r.bad.join(' | ')}`);
      if (w === 320) await page.screenshot({ path: `${OUT}/${lang}-320.png` });
      await ctx.close();
    }
  }
  // language toggle and keyboard check
  {
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } }); const page = await ctx.newPage();
    await page.goto(base); await page.click('#lang-en');
    const a = await page.evaluate(() => [document.documentElement.lang, location.search, document.title, document.getElementById('lang-en').getAttribute('aria-pressed'), getComputedStyle(document.querySelector('.wrap.es')).display]);
    await page.click('#lang-es');
    const b = await page.evaluate(() => [document.documentElement.lang, location.search]);
    const ok = a.join('|') === 'en|?lang=en|A loved one was detained by ICE in Arizona: first steps|true|none' && b.join('|') === 'es|'; if (!ok) fail++;
    log(`language toggle: ${ok ? 'OK' : 'FAIL'} ${JSON.stringify(a)} ${JSON.stringify(b)}`);
    await page.emulateMedia({ media: 'print' }); await page.screenshot({ path: `${OUT}/es-print-preview.png` });
    await ctx.close();
  }
  // no-JS: both languages visible
  {
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 }, javaScriptEnabled: false }); const page = await ctx.newPage();
    await page.goto(base);
    const vis = await page.locator('.wrap.en').isVisible(); if (!vis) fail++;
    log(`no JavaScript: English block visible = ${vis}`);
    await ctx.close();
  }

  // WebKit (Safari engine) at iPhone 15, iPhone SE and iPhone 16 Pro Max sizes: axe, overflow, tap targets, screenshots. The page has no text field,
  // so there is no on-screen keyboard to open; the check is recorded as "no text inputs" below.
  {
    const { webkit, devices } = require('playwright');
    const wk = await webkit.launch();
    const phones = [['iphone15', devices['iPhone 15']], ['iphoneSE', devices['iPhone SE']], ['iphone16pm', { ...devices['iPhone 15 Pro Max'], viewport: { width: 440, height: 956 } }]];
    for (const [name, dev] of phones) {
      for (const lang of ['es', 'en']) {
        const ctx = await wk.newContext({ ...dev }); const page = await ctx.newPage(); const errs = [];
        page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); }); page.on('pageerror', e => errs.push(String(e)));
        page.on('request', r => { if (!r.url().startsWith(base)) errs.push('EXTERNAL REQUEST ' + r.url()); });
        await page.goto(base + (lang === 'en' ? '?lang=en' : ''), { waitUntil: 'load' });
        await page.evaluate(axeSrc);
        const res = await page.evaluate(async () => await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] } }));
        const m = await page.evaluate(() => {
          const vw = document.documentElement.clientWidth; let bad = 0;
          for (const el of document.querySelectorAll('body *')) { const b = el.getBoundingClientRect(); if (b.width && (b.right > vw + 0.5 || b.left < -0.5) && !el.closest('.skip')) bad++; }
          const small = [...document.querySelectorAll('button,.btn')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).length;
          return { vw, sw: document.documentElement.scrollWidth, bad, small, inputs: document.querySelectorAll('input,textarea,select').length };
        });
        const ok = res.violations.length === 0 && errs.length === 0 && m.sw <= m.vw && m.bad === 0 && m.small === 0;
        if (!ok) fail++;
        log(`webkit ${name} ${lang} ${m.vw}px: axe ${res.violations.length} violations (${res.passes.length} passed), overflow ${m.sw} vs ${m.vw}, past edge ${m.bad}, small targets ${m.small}, text inputs ${m.inputs}, errors ${errs.length} ${ok ? 'OK' : 'FAIL'}`);
        for (const v of res.violations) log(`  VIOLATION ${v.id}: ${v.help} (${v.nodes.length}) ${v.nodes[0].html.slice(0, 120)}`);
        if (lang === 'es') await page.screenshot({ path: `${OUT}/webkit-${name}-es.png` });
        await ctx.close();
      }
    }
    await wk.close();
  }
  // og image
  {
    const ctx = await browser.newContext({ viewport: { width: 1200, height: 630 } }); const page = await ctx.newPage();
    await page.goto(base + 'tools/og.html'); await page.screenshot({ path: `${OUT}/og-image.png` }); await ctx.close();
  }
  log(fail ? `RESULT: FAIL (${fail})` : 'RESULT: PASS');
  fs.writeFileSync(`${OUT}/audit-report.txt`, report.join('\n') + '\n');
  await browser.close(); server.close(); process.exit(fail ? 1 : 0);
})();
