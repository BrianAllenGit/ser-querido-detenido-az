import { chromium } from 'playwright';
import fs from 'fs';
const [,, url, name] = process.argv;
const b = await chromium.launch();
const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36', locale: 'en-US' });
if (/\.pdf($|\?)/i.test(url) || name.startsWith('pdf/')) {
  const r = await ctx.request.get(url, { timeout: 60000 });
  const buf = await r.body();
  fs.mkdirSync('/out/pdf', { recursive: true });
  fs.writeFileSync(`/out/${name}.pdf`, buf);
  console.log(url, r.status(), buf.length);
} else {
  const p = await ctx.newPage();
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForTimeout(5000);
  fs.writeFileSync(`/out/${name}.txt`, await p.innerText('body'));
  fs.writeFileSync(`/out/${name}.html`, await p.content());
  console.log(p.url(), (await p.innerText('body')).length);
}
await b.close();
