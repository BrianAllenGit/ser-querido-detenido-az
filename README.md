# Ser querido detenido · Arizona

A free, ad-free, zero-tracking, Spanish-first page (Spanish and English) for one reason to arrive: "I can't reach someone and ICE may have them." It gives four steps, each made of links and passages copied word for word from official sources: 1) find them (ICE Online Detainee Locator System), 2) check their court case (EOIR Automated Case Information), 3) free legal help in Arizona (EOIR list, Florence Project, ACLU of Arizona), 4) your family (ACLU of Arizona family plan passage). It also has a printable card with the phone numbers and blank lines to write on.

Status: private draft. Not published. Planned address once shipped: https://brianallengit.github.io/ser-querido-detenido-az/

## No legal wording is written by us

Quoted text is in `tools/quotes.json`, built from pages and PDFs saved in `tools/captures/`. `python3 tools/verify_quotes.py` proves each block of each quote is a word for word match of its saved source and is on the page (26 quotes). Phone numbers in buttons come from quotes (`tools/build.py` fails if one does not). The Spanish labels we wrote are in [docs/NEEDS-NATIVE-READ.md](docs/NEEDS-NATIVE-READ.md). Sources, terms and what was left out: [docs/SOURCES.md](docs/SOURCES.md).

## Privacy promise

No cookies, no localStorage, no accounts, no forms, no analytics, no ads, no third-party fonts or scripts. A strict Content Security Policy blocks every outside request. The language choice lives only in the page address (`?lang=en`). The page never queries the ICE locator or EOIR for you. GitHub Pages, the planned host, may keep standard visit logs the page cannot see.

## Checks (all in Docker)

```
python3 tools/extract_quotes.py && python3 tools/build.py && python3 tools/verify_quotes.py
./tools/audit.sh    # axe (Chromium 375/1280, WebKit iPhone 15, SE, 16 Pro Max size), overflow 320/375/768, screenshots
./tools/dod.sh      # icons, head and JSON-LD validation, keyboard, text spacing, Lighthouse mobile (run twice the first time: icons are created on the first run)
```

Re-capture with `tools/fetch/fetchall.sh <list> <outdir>` (headless Chromium; ice.gov and others return 403 to plain fetches) and `tools/fetch/pdftext.sh`. Re-read every source and re-run before shipping: the ICE locator situation is changing.

## Deploy to GitHub Pages (only when the owner says so)

1. Make the repository public. 2. Settings, Pages, branch `main`, folder `/ (root)`. 3. If the address changes, update `SITE_URL` in `tools/build.py` and rebuild.

## License

MIT for the code and the page's own wording, see `LICENSE`. Quoted ICE and EOIR text is a US government work (public domain). Quoted ACLU and ACLU of Arizona text is used under their user agreements (noncommercial, unchanged, with their notice). Organizations own their names; this page is not affiliated with them.
