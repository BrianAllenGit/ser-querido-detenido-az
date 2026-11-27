# Website definition of done: evidence

Mirrors Brian's website definition of done (vault: `me/working-together/web-definition-of-done.md`). Run 2026-11-27 inside Docker only (Playwright 1.49.1 image, axe-core 4.10.2, Lighthouse 12.2.1). Re-run with `./tools/audit.sh` and `./tools/dod.sh`. Planned address (not live): https://brianallengit.github.io/ser-querido-detenido-az/

## 1. Accessibility
- [x] axe-core 0 violations, ES and EN at 375 and 1280 in Chromium (41 rules passed each), and in WebKit at iPhone 15 (393), iPhone SE (320) and an iPhone 16 Pro Max size (440), both languages: 0 violations (`docs/screenshots/audit-report.txt`).
- [x] Keyboard: 68 tab stops per language, 0 without a visible focus indicator, no trap, skip link first (`docs/lighthouse/extra.txt`).
- [x] One H1 per language, headings in order, landmarks (header, nav, main, sections with labels, footer). The page has no text field, so there is no on-screen keyboard case to test (WebKit run reports 0 text inputs).
- [x] 0 tap targets under 44px at 320, 375, 768 and in WebKit; contrast checked by axe.
- [x] reduced-motion and forced-colors screenshots in `docs/lighthouse/`. JavaScript off: both languages in the static HTML (12 panels).
- [ ] Not machine-verifiable: real screen reader pass, native Spanish read, real-device phone test.

## 2. Phone first
- [x] No horizontal scroll and nothing past the edge at 320, 375, 768 (ES and EN) and at the WebKit iPhone sizes. Text-spacing overrides at 320 and 375 and a 640px (200% zoom) width: no overflow.

## 3. Languages
- [x] ES default, visible ES/EN switch, `lang` on `<html>` updates, hreflang es/en/x-default. Quoted Spanish is ICE's, EOIR's and the ACLU of Arizona's own.

## 4. Search
- [x] Title 59 characters, description 158, canonical, robots meta, `robots.txt`, `sitemap.xml` with alternates (`docs/lighthouse/validate.txt`, 56 checks, 0 fail).
- [x] JSON-LD `@graph`: Organization, WebSite, WebPage, HowTo (four steps, matching the four visible steps). No FAQPage. Run Google's Rich Results Test by hand at ship time.
- [x] All content is in the static HTML.

## 5. Link previews
- [x] Open Graph and Twitter tags complete; `og-image.png` 1200x630, 77 KB. [ ] Platform debuggers by hand at ship time.

## 6. AI answers
- [x] Plain lead and `llms.txt` with summary, sources and limits.

## 7. App polish
- [x] Favicon set, apple-touch-icon, theme-color, manifest, print styles (the card prints the numbers and blank lines).
- [x] Lighthouse mobile (Docker, local server): ES 100/100/100/100, EN 100/100/100/100 (performance, accessibility, best practices, SEO).

## 8. Trust and safety
- [x] Zero tracking, storage, ads, third-party requests: the audit fails on any external request or console error (0 seen). Strict CSP.
- [x] 26 quotes verified word for word against saved sources (`python3 tools/verify_quotes.py`). Every phone number is inside a quote.
- [x] No person named in the HTML or JSON-LD apart from the planned host.

## Needs a human (before shipping)
- [ ] Native Spanish read of `docs/NEEDS-NATIVE-READ.md`.
- [ ] Open the ICE locator on a phone: our tool got "Access Denied", so its screens, fields and Spanish labels are unread. Check that `www.ice.gov/locator` works.
- [ ] A lawyer or accredited representative should read the whole page once (highest-care topic), especially the ACLU lawsuit sentences (an allegation, labelled as a press release) and whether to keep them.
- [ ] Confirm the licence reading: ICE's own reuse terms page was "Not Found" (public domain by 17 U.S.C. 105); ACLU and ACLU of Arizona notices are shown; a PDF zine counts as "text material" (unverified).
- [ ] The page is very long (about 28,000 px on a phone) because the sources are quoted in full; decide whether to collapse the secondary quotes.
- [ ] Re-read every source the day you ship (ICE brochure is dated 12/2021; locator policy is in flux as of the October 2026 lawsuit).
- [ ] Rich Results Test, link debuggers, live-URL checks.
