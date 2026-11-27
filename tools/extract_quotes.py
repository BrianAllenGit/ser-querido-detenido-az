#!/usr/bin/env python3
"""Builds tools/quotes.json from the pages and PDFs saved in tools/captures/ (see tools/fetch/).

The quoted text is copied from the captures. Nothing is reworded. Only markup is added: line breaks of the PDF text are
joined, a few lines become <br> or <li>. tools/verify_quotes.py then proves that every block of every quote is a word for
word match of its capture.

Usage: python3 tools/extract_quotes.py   (after tools/fetch/fetchall.sh and tools/fetch/pdftext.sh)
"""
import html as H
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "captures")
OUT = os.path.join(HERE, "quotes.json")
RETRIEVED = "2026-11-27"
E = H.escape


def rd(name):
    with open(os.path.join(CAP, name), encoding="utf-8", errors="replace") as f:
        return f.read()


def flat(s):
    return re.sub(r"\s+", " ", s.replace("​", "")).strip()


def between(text, start, end=None):
    a = text.index(start)
    if end is None:
        return text[a:]
    b = text.index(end, a + len(start))
    return text[a:b]


quotes = {}


def add(key, lang, kind, url, title, body, doc_date, year=None):
    assert "—" not in body, key
    quotes[key] = {"lang": lang, "kind": kind, "url": url, "title": title, "html": body, "doc_date": doc_date,
                   "year": year, "retrieved": RETRIEVED}


def p(s):
    return "<p>%s</p>" % E(flat(s))


def h3(s):
    return "<h3>%s</h3>" % E(flat(s))


# ---- 1. ICE Online Detainee Locator System brochure (12/2021), Spanish and English -------------------------------
BROCHURE = "https://www.ice.gov/doclib/news/library/factsheets/pdf/odls-brochure%s.pdf"
BR = {"en": flat(rd("pdf/odls_brochure_en.txt")), "es": flat(rd("pdf/odls_brochure_es.txt"))}
BR_URL = {"en": BROCHURE % "", "es": BROCHURE % "-esp"}
BR_TITLE = {"en": "How Do I Locate Someone in Immigration Detention? Online Detainee Locator System",
            "es": "¿Cómo localizo a alguien bajo detención inmigratoria? Sistema Localizador de Detenidos en Línea"}


def br(key, lang, blocks):
    add(key + "_" + lang, lang, "ice", BR_URL[lang], BR_TITLE[lang], "\n".join(blocks), "12/2021")


t = BR["en"]
br("odls_what", "en", [
    h3("What is the Online Detainee Locator System?"),
    p(between(t, "The Online Detainee Locator System (ODLS) is a public system", "Previously, the only way")),
    p(between(t, "Previously, the only way", "Do I have to know exactly"))])
br("odls_search", "en", [
    h3(between(t, "How does a family member", "You can search")),
    p("You can search the ODLS in two ways:"),
    p(between(t, "1. By Alien Registration Number", "2. By last name")),
    p(between(t, "2. By last name", "For example, a search for"))])
br("odls_exact", "en", [
    h3(between(t, "Do I have to know exactly", "Yes. The ODLS")),
    p(between(t, "Yes. The ODLS performs", "How does a family member")),
    p(between(t, "For example, a search for", "When you search using")),
    p(between(t, "When you search using an A-Number", "What should I do if I still"))])
br("odls_notin", "en", [
    h3("Who is not in the ODLS?"),
    p(between(t, "The ODLS does not provide location", "I have found who"))])
br("odls_found", "en", [
    h3("I have found who I am looking for. Now what do I do?"),
    p(between(t, "If you have found the individual", "I still have more questions"))])
br("odls_notfound", "en", [
    h3(between(t, "What should I do if I still", "The ODLS only has")),
    # the sentence that gives the field-office web address is not copied: the PDF text loses the hyphen of "field-offices" at a line break
    p(between(t, "The ODLS only has information", " A list of the various ERO"))])

t = BR["es"]
br("odls_what", "es", [
    h3("¿Qué es el Sistema Localizador de Detenidos en Línea?"),
    p(between(t, "El Sistema Localizador de Detenidos en Línea (ODLS", "Anteriormente, la única")),
    p(between(t, "Anteriormente, la única", "¿Debo saber exactamente"))])
br("odls_search", "es", [
    h3(between(t, "¿Cómo puede un familiar", "Usted puede realizar")),
    p("Usted puede realizar una búsqueda en el ODLS mediante dos formas:"),
    p(between(t, "1. Por Número de Registro", "2. Por apellido")),
    # The Spanish PDF has no explanation text for the second way (its first words are missing in the file); only its heading is quoted.
    p("2. Por apellido, nombre de pila y país de nacimiento.")])
br("odls_exact", "es", [
    p(between(t, "Sí. El ODLS realiza", "Por ejemplo, la búsqueda")),
    p(between(t, "Por ejemplo, la búsqueda", "Al realizar una búsqueda")),
    p(between(t, "Al realizar una búsqueda utilizando", "¿Qué debería hacer"))])
br("odls_notin", "es", [
    h3("¿Quiénes no aparecen en el ODLS?"),
    p(between(t, "El ODLS no proporciona información", "He encontrado"))])
br("odls_found", "es", [
    h3("He encontrado a la persona que busco, ¿qué debo hacer ahora?"),
    p(between(t, "Si encontró al individuo", "¿Cómo localizo"))])
br("odls_notfound", "es", [
    h3(between(t, "¿Qué debería hacer si aún", "El ODLS sólo posee")),
    p(between(t, "El ODLS sólo posee", " Puede encontrar una lista"))])

# ---- 2. ICE pages: Phoenix field office and the two Eloy/Florence facility pages ---------------------------------
ero = rd("ice_ero.txt")
blk = between(ero, "Phoenix - ERO", "San Antonio - ERO")
lines = [flat(x) for x in blk.split("\n") if flat(x)]
add("ero_phoenix_en", "en", "ice", "https://www.ice.gov/contact/ero", "ICE Field Offices: Phoenix",
    "<p>%s</p>" % "<br>".join(E(x) for x in lines), "Updated: 09/02/2026")
for key, cap, url, name in [("eloy_en", "ice_eloy.txt", "https://www.ice.gov/detain/detention-facilities/eloy-detention-center", "Eloy Detention Center"),
                            ("florence_en", "ice_florence.txt", "https://www.ice.gov/detain/detention-facilities/florence-spc", "Florence Service Processing Center")]:
    t = rd(cap)
    a = between(t, "If you need information about a detainee", "Detainees cannot receive")
    b = between(t, "Detainees cannot receive incoming calls.", "This facility has tablets") if "This facility has tablets" in t else between(t, "Detainees cannot receive incoming calls.", "Updated:")
    # the fax/tablet paragraph is not copied; take only up to the end of the "message" sentence
    b = b[:b.index("The detainee will be given your message.") + len("The detainee will be given your message.")]
    add(key, "en", "ice", url, name, h3(name) + "\n" + p(a) + "\n" + p(b), "Updated: 08/06/2026")

# ---- 3. EOIR: check case status page, ACIS (English and Spanish), pro bono list for Arizona ----------------------
st = rd("eoir_status_en.txt")
add("eoir_status_en", "en", "doj", "https://www.justice.gov/eoir/check-case-status", "Check Case Status (EOIR)",
    p(between(st, "To obtain case information online", "Updated December 14, 2025")), "Updated December 14, 2025")
for lang, cap, a1, a2, b1, b2, ttl in [
    ("en", "acis_en.txt", "Welcome to the Automated Case Information System", "English\nEspañol", "Case information from this automated resource", "Archive\nAccessibility",
     "Automated Case Information (ACIS)"),
    ("es", "acis_es.txt", "Le damos la bienvenida", "English\nEspañol", "La información sobre el caso que aparece", "Archivo\nAccesibilidad",
     "Información automatizada de casos (ACIS)")]:
    t = rd(cap)
    add("acis_intro_" + lang, lang, "doj", "https://acis.eoir.justice.gov/%s/" % lang, ttl, p(between(t, a1, a2)), "page shows no date")
    add("acis_official_" + lang, lang, "doj", "https://acis.eoir.justice.gov/%s/" % lang, ttl, p(between(t, b1, b2)), "page shows no date")

L = rd("pdf/eoir_az_eloy_left.txt")
R = rd("pdf/eoir_az_eloy_right.txt")
PG = rd("pdf/eoir_az_eloy_page.txt")
assert rd("pdf/eoir_az_florence_left.txt") == L and rd("pdf/eoir_az_florence_right.txt") == R
legend = flat(between(PG, "* Non-Profit Organization", "List of Pro Bono Legal Service Providers"))


def entry(txt, name_end, contact_end):
    name = flat(txt[:name_end])
    contact = [flat(x) for x in txt[name_end:contact_end].split("\n") if flat(x)]
    bullets = [flat(b) for b in re.split(r"\n\s*•\s*", "\n" + txt[contact_end:])[1:]]
    return name, contact, bullets


# Florence Project (right column)
fi = R.index("P.O. Box")
fe = R.index("• Removal defense")
f_name = flat(R[:fi])
f_contact = [flat(x) for x in R[fi:fe].split("\n") if flat(x)]
f_bul = [flat(b) for b in re.split(r"\n\s*•\s*", "\n" + R[fe:])[1:]]
# ABA hotline (left column)
ai = L.index("1050 Connecticut")
ae = L.index("• Pro se case")
a_name = flat(L[:ai])
a_contact = [flat(x) for x in L[ai:ae].split("\n") if flat(x)]
# the contact lines wrap at the url: join "www...public_interest/" and "immigration/" with no space (the PDF broke the address in two)
a_contact = [x for x in a_contact]
a_bul = []
for b in re.split(r"\n\s*•\s*", "\n" + L[ae:])[1:]:
    a_bul.append(flat(b))
body = [h3("Eloy Immigration Court"), p("Eloy, Arizona")]
body.append("<h4>%s</h4>" % E(f_name))
body.append("<p>%s</p>" % "<br>".join(E(x) for x in f_contact))
body.append("<ul>%s</ul>" % "".join("<li>%s</li>" % E(x) for x in f_bul))
body.append("<h4>%s</h4>" % E(a_name))
body.append("<p>%s</p>" % "<br>".join(E(x) for x in a_contact))
body.append("<ul>%s</ul>" % "".join("<li>%s</li>" % E(x) for x in a_bul))
body.append(p(legend))
add("eoir_list_az_en", "en", "doj", "https://www.justice.gov/eoir/list-pro-bono-legal-service-providers",
    "List of Pro Bono Legal Service Providers: Arizona", "\n".join(body), "Updated October 2026")

# ---- 4. ACLU press release (national) and ACLU of Arizona -----------------------------------------------------------
lw = flat(rd("aclu_lawsuit.txt"))
s1 = between(lw, "For over 16 years", "In September,")
s2 = between(lw, "In September,", "This policy of mass disappearance")
add("aclu_lawsuit_en", "en", "aclu",
    "https://www.aclu.org/press-releases/immigrants-rights-organizations-file-lawsuit-to-stop-ice-from-hiding-locations-of-detained-people",
    "Immigrants' Rights Organizations File Lawsuit to Stop ICE from Hiding Locations of Detained People", p(s1.strip() + " " + s2.strip()), "October 28, 2026", "2026")

Z = flat(rd("pdf/z_plain.txt"))
ZURL = "https://www.acluaz.org/app/uploads/2025/02/01-2025_aclu-az_immigrants-kyr_zine.pdf"
add("zine_family_en", "en", "az", ZURL, "Know Your Rights with Police, ICE, and Border Patrol (zine)",
    p(between(Z, "Remember your immigration number", " Do not lie.")) + "\n" +
    p(between(Z, "Prepare yourself and your family in case you are arrested.", " 7 Generally")), "January 2025 (from the file name)", "2025")
add("zine_family_es", "es", "az", ZURL, "Conozca sus derechos con la policía, ICE y la Patrulla Fronteriza (librito)",
    p(between(Z, "Recuerde su número de inmigración", " No mienta.")) + "\n" +
    p(between(Z, "Prepárese usted y a su familia en caso de que sea arrestado.", " Si un oficial le pide firmar")), "January 2025 (from the file name)", "2025")
add("zine_lawyer_en", "en", "az", ZURL, "Know Your Rights with Police, ICE, and Border Patrol (zine)",
    p(between(Z, "If you are detained by ICE or Border Patrol,", " WHAT TO DO IF POLICE OR ICE ARE AT YOUR HOME")), "January 2025 (from the file name)", "2025")

ct = flat(rd("misc/acluaz_contact.txt"))
add("acluaz_limits_en", "en", "az", "https://www.acluaz.org/contact-us/", "Contact Us (ACLU of Arizona)",
    p(between(ct, "The ACLU-AZ is not a general legal service", " Please visit the Request Legal Assistance")) + "\n" +
    p(between(ct, "We do not provide presentations or legal advice about immigration law,", " ALL requests")), "page shows no date; read 2026-11-27", "2026")

# The page boosts existing guides and keeps only the quotes that carry the Arizona phone numbers (see tools/build.py).
KEEP = ["ero_phoenix_en", "eloy_en", "florence_en", "eoir_status_en", "eoir_list_az_en"]
quotes = {k: v for k, v in quotes.items() if k in KEEP}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(quotes, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("wrote", OUT, len(quotes), "quotes")
