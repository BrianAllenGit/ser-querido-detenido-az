// Prints the page height on a phone (375x667, iPhone-like) in both languages, in px and in screens of 667px.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const lang of ['es', 'en']) {
    const p = await b.newPage({ viewport: { width: 375, height: 667 } });
    await p.goto('file:///site/index.html' + (lang === 'en' ? '?lang=en' : ''));
    const h = await p.evaluate(() => document.documentElement.scrollHeight);
    console.log(lang, h + 'px', (h / 667).toFixed(1) + ' screens');
    await p.close();
  }
  await b.close();
})();
