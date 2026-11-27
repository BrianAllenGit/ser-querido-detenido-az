#!/usr/bin/env python3
"""Builds index.html, docs/SOURCES.md and docs/NEEDS-NATIVE-READ.md from one place.

Run:  python3 tools/build.py     (after tools/extract_quotes.py when the captures change)
No dependencies. The output files are committed, so the site itself has no build step.
Rule: no legal wording on the page is written by us. Quoted text lives in tools/quotes.json (copied from saved source pages),
everything else is a link, a phone number copied from a quote, or a short navigation label (every Spanish one is listed in
docs/NEEDS-NATIVE-READ.md).
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKED = "2026-11-27"
CHECKED_TXT = {"es": "27 de noviembre de 2026", "en": "November 27, 2026"}
SITE_URL = "https://brianallengit.github.io/ser-querido-detenido-az/"
NAME = "Ser querido detenido · Arizona"
E = html.escape
US_GOV = "US government work (17 U.S.C. 105: no copyright in the United States). "

LOCATOR = "https://www.ice.gov/locator"  # the address ICE's own brochure gives; it forwards to locator.ice.gov/odls
ACIS = {"es": "https://acis.eoir.justice.gov/es/", "en": "https://acis.eoir.justice.gov/en/"}
FLORENCE_SITE = "https://firrp.org/"
FLORENCE_FAMILY = "https://firrp.org/resources/prose/parentalrights/"
ACLU_REQUEST = "https://www.acluaz.org/en/resources/requesting-legal-assistance-aclu-arizona"
ACLU_WEHAVE = "https://www.aclu.org/we-have-rights"
EOIR_LIST_PAGE = "https://www.justice.gov/eoir/list-pro-bono-legal-service-providers"
EOIR_LIST_FILE = "https://www.justice.gov/eoir/file/probonofulllist/download"
EOIR_STATUS = "https://www.justice.gov/eoir/check-case-status"
ICE_FIELD = "https://www.ice.gov/contact/ero"
KJZZ = "https://www.kjzz.org/fronteras-desk/2026-10-30/new-lawsuit-alleges-ice-is-hiding-thousands-of-people-in-its-custody"

# id -> (url, Spanish label, English label, what we took from it, terms note)
SOURCES = {
    "ice_brochure_es": (
        "https://www.ice.gov/doclib/news/library/factsheets/pdf/odls-brochure-esp.pdf",
        "ICE: Folleto del Sistema Localizador de Detenidos en Línea (PDF, en español, 12/2021)",
        "ICE: Online Detainee Locator System brochure, Spanish version (PDF, 12/2021)",
        "Six passages word for word (what the ODLS is, the two ways to search, exact spelling, who is not in it, what to do after finding someone, what to do if not found). Dated 12/2021 on the PDF. The Spanish PDF text has no explanation under the second way to search (its first words are missing in the file), so only that heading is quoted; the English version has the full text. The sentence that gives the field-office web address is not copied (the PDF text loses a hyphen in the address).",
        US_GOV + "ICE's own website-policies page returned \"Page Not Found\" when read (tools/captures/terms_ice.txt), so ICE's reuse statement was not read.",
    ),
    "ice_brochure_en": (
        "https://www.ice.gov/doclib/news/library/factsheets/pdf/odls-brochure.pdf",
        "ICE: Folleto del Sistema Localizador de Detenidos en Línea (PDF, en inglés, 12/2021)",
        "ICE: Online Detainee Locator System brochure, English version (PDF, 12/2021)",
        "The same six passages as the Spanish version, word for word.",
        US_GOV + "Same note as the Spanish version.",
    ),
    "ice_factsheet": (
        "https://www.ice.gov/factsheets/locating-individuals-in-detention",
        "ICE: hoja informativa «Locating Individuals in Detention» (en inglés, actualizada el 16 de mayo de 2025)",
        "ICE: fact sheet \"Locating Individuals in Detention\" (Updated 05/16/2025; dated August 8, 2023)",
        "Link only, not quoted. It says use of the ODLS \"requires the individual's full name, alien number (A-number) or date of birth, and country of birth\", which is worded differently from the brochure (A-number and country of birth, or name and country of birth). Both are ICE's own; the page quotes the brochure, which is more specific, and links this fact sheet. The fact sheet lists the brochure in nine languages (Spanish, French, Portuguese, Russian, Somali, Vietnamese, Chinese, Arabic).",
        US_GOV,
    ),
    "ice_locator": (
        LOCATOR,
        "ICE: Sistema Localizador de Detenidos en Línea (ODLS)",
        "ICE: Online Detainee Locator System (ODLS)",
        "Link only. The brochure gives www.ice.gov/locator as the address; it forwards to locator.ice.gov/odls. The tool is not opened or used by this page. It answered \"Access Denied\" to our automated browser (tools/captures/ice_locator.txt), so its screens, fields and Spanish labels were not read. Whether it works in a normal phone browser could not be checked.",
        "Link only.",
    ),
    "ice_ero": (
        ICE_FIELD,
        "ICE: oficinas de campo (Phoenix, ERO) (en inglés)",
        "ICE: Field Offices (Phoenix, ERO)",
        "The Phoenix block (address, phone, area of responsibility, email) word for word. The page is marked \"Updated: 09/02/2026\" and says the field offices listed \"are not check-in locations\".",
        US_GOV,
    ),
    "ice_eloy": (
        "https://www.ice.gov/detain/detention-facilities/eloy-detention-center",
        "ICE: Eloy Detention Center (en inglés)",
        "ICE: Eloy Detention Center",
        "The two paragraphs about calling for information and leaving an urgent message, word for word. Marked \"Updated: 08/06/2026\".",
        US_GOV,
    ),
    "ice_florence": (
        "https://www.ice.gov/detain/detention-facilities/florence-spc",
        "ICE: Florence Service Processing Center (en inglés)",
        "ICE: Florence Service Processing Center",
        "The same two paragraphs for this facility, word for word. Marked \"Updated: 08/06/2026\". A third Arizona facility page (Central Arizona Correctional Center) returned \"Page Not Found\" and is not used.",
        US_GOV,
    ),
    "eoir_status": (
        EOIR_STATUS,
        "EOIR (tribunales de inmigración): Check Case Status (en inglés)",
        "EOIR (immigration courts): Check Case Status",
        "The one paragraph word for word. Marked \"Updated December 14, 2025\". A Spanish page address (check-case-status-espanol) returned \"Page not found\".",
        US_GOV + "justice.gov Legal Policies (read 2026-11-27 at https://www.justice.gov/legalpolicies, saved in tools/captures/misc/terms_doj.txt): \"Unless otherwise indicated, information on Department of Justice websites is in the public domain and may be copied and distributed without permission.\"",
    ),
    "acis_es": (
        ACIS["es"],
        "EOIR: Información automatizada de casos, ACIS (en español)",
        "EOIR: Automated Case Information, Spanish version",
        "The welcome paragraph and the \"for convenience only\" paragraph, word for word, in EOIR's own Spanish. The page shows no date. The tool asks for an A-Number and a nationality, then an hCaptcha check (a third-party service, on EOIR's site, not on this page). The Spanish text has wording problems of its own (\"se provee a penas\", \"número de registro de Extranjero\"); it is copied as it stands.",
        US_GOV + "Same as EOIR status page.",
    ),
    "acis_en": (
        ACIS["en"],
        "EOIR: Información automatizada de casos, ACIS (en inglés)",
        "EOIR: Automated Case Information, English version",
        "The same two paragraphs, word for word. The tool was not used (no A-Number was entered).",
        US_GOV + "Same as EOIR status page.",
    ),
    "eoir_list": (
        EOIR_LIST_FILE,
        "EOIR: Lista de proveedores de servicios legales gratuitos (pro bono), PDF actualizado en octubre de 2026 (en inglés)",
        "EOIR: List of Pro Bono Legal Service Providers, PDF \"Updated October 2026\"",
        "The Eloy Immigration Court page of the Arizona section (two providers: Florence Immigrant and Refugee Rights Project, and the ABA Commission on Immigration Detention Information Hotline), word for word. The Florence court page of the list is identical. The Phoenix and Tucson court pages list the same two providers but the Florence Project there says \"Children's cases only\"; they are not quoted. EOIR's own page (" + EOIR_LIST_PAGE + ", \"Updated November 18, 2026\") says the list is published quarterly and that EOIR \"does not endorse any of these organizations\".",
        US_GOV + "Same as EOIR status page.",
    ),
    "aclu_lawsuit": (
        "https://www.aclu.org/press-releases/immigrants-rights-organizations-file-lawsuit-to-stop-ice-from-hiding-locations-of-detained-people",
        "ACLU: comunicado sobre una demanda por la ubicación de personas detenidas (28 de octubre de 2026, en inglés)",
        "ACLU: press release on a lawsuit about the locations of detained people (October 28, 2026)",
        "Two sentences word for word (what the ODLS has done for 16 years, and what DHS changed in September). They are the organizations' account in a press release about a lawsuit, not a court finding; the page says so. The press release's other sentences (such as its characterisations of the policy, and the statements of the plaintiffs) are not copied. The same lawsuit is described by KJZZ (linked, not copied).",
        "ACLU Site User Agreement (effective July 31, 2025, tools/captures/aclu_useragreement.txt): text may be copied if not for commercial use, without editorial changes, not misleadingly excerpted, with the notice \"Copyright [year] American Civil Liberties Union. Originally posted by the ACLU at [address]\". Shown on the page. Two sentences were picked from a longer paragraph; we do not think that misleads, and the page says what the sentences are. UNVERIFIED and for a human: confirm.",
    ),
    "kjzz": (
        KJZZ,
        "KJZZ (Phoenix): nueva demanda alega que ICE esconde a miles de personas bajo su custodia (30 de octubre de 2026, en inglés)",
        "KJZZ: New lawsuit alleges ICE is hiding thousands of people in its custody (October 30, 2026)",
        "Link only. It reports that the Florence Project is among the groups suing and that the groups say thousands with final orders of removal stopped appearing in the ODLS in mid-September.",
        "Link only. No text copied.",
    ),
    "zine": (
        "https://www.acluaz.org/app/uploads/2025/02/01-2025_aclu-az_immigrants-kyr_zine.pdf",
        "ACLU de Arizona: «Conozca sus derechos con la policía, ICE y la Patrulla Fronteriza» (librito en inglés y español, enero de 2025)",
        "ACLU of Arizona: \"Know Your Rights with Police, ICE, and Border Patrol\" zine (English and Spanish, January 2025)",
        "Two passages in English and the same two in the zine's own Spanish (remember your A-number and give it to family; prepare your family, memorize numbers, name a caregiver), and one English passage on the right to hire a lawyer if detained by ICE. The PDF has no printed date; the year comes from the file name (01-2025) and the upload folder (2025/02), and ACLU of Arizona's page for it (acluaz.org/know-your-rights/immigrants-rights, \"Last updated: August 13, 2025\"). The Spanish version of the lawyer passage is not quoted: the PDF text runs into another section.",
        "ACLU of Arizona User Agreement (effective July 1, 2024, tools/captures/acluaz_useragreement.txt): text may be copied if not for commercial use, without editorial changes, not misleadingly excerpted, with the notice \"Copyright [year] ACLU of Arizona. Originally posted by the ACLU of Arizona at [address]\". Shown on the page. UNVERIFIED and for a human: whether a PDF counts as \"text material\" on the site; the notice names the PDF's address.",
    ),
    "acluaz_contact": (
        "https://www.acluaz.org/contact-us/",
        "ACLU de Arizona: Contacto (en inglés)",
        "ACLU of Arizona: Contact Us",
        "Two paragraphs word for word (it is \"not a general legal service\"; it does not give legal advice about immigration law). The page also says legal assistance requests must go through its form and that it does not review them in person or by phone.",
        "Same ACLU of Arizona User Agreement as above; the notice is shown.",
    ),
    "acluaz_request": (
        ACLU_REQUEST,
        "ACLU de Arizona: Cómo pedir asistencia legal (en inglés)",
        "ACLU of Arizona: Requesting legal assistance",
        "Link only. The page was not opened.",
        "Link only.",
    ),
    "firrp_family": (
        FLORENCE_FAMILY,
        "Florence Project: «What if I’m Picked up by ICE in Arizona?: Making a Family Plan» (en inglés; el sitio ofrece una versión en español)",
        "Florence Project: \"What if I'm Picked up by ICE in Arizona?: Making a Family Plan\"",
        "Link only, not quoted. The page (read with a plain HTTP request) says it is written for immigrant parents in Arizona, \"whether you have papers or not\", to help them plan so they do not lose rights over their children if apprehended by ICE. Its terms were not read.",
        "Link only. The Florence Project's terms were not read, so no text is copied. firrp.org answered ERR_HTTP2_PROTOCOL_ERROR to our headless browser; the page above did load to a plain HTTP request.",
    ),
    "firrp_site": (
        FLORENCE_SITE,
        "Florence Immigrant and Refugee Rights Project (sitio web)",
        "Florence Immigrant and Refugee Rights Project (website)",
        "Link only. The address comes from EOIR's list. The home page itself was not read (our headless browser got an HTTP/2 error).",
        "Link only.",
    ),
    "aclu_wehave": (
        ACLU_WEHAVE,
        "ACLU: «We Have Rights», videos sobre qué hacer si ICE arresta a alguien (en inglés; los videos tienen versión en español)",
        "ACLU: \"We Have Rights\" videos on what to do if ICE arrests someone",
        "Link only. The page says the videos are voiced in several languages including Spanish, and that one explains \"what you and your loved ones should do if one of you is arrested\". The page text is from the 2017 campaign (it cites 2017 arrest numbers), so it is linked, not quoted.",
        "Link only.",
    ),
}

SPANISH_UI = []  # every Spanish string written for this page, for docs/NEEDS-NATIVE-READ.md

TEXT = {
    "title": "Mi familiar fue detenido por ICE en Arizona: primeros pasos",
    "title_en": "A loved one was detained by ICE in Arizona: first steps",
    "desc": "¿No puedes comunicarte con alguien y ICE puede tenerlo? Cómo buscarlo, revisar su caso y hallar ayuda legal gratis en Arizona. Fuentes oficiales, sin rastreo.",
    "desc_en": "Can't reach someone and ICE may have them? How to find them, check their court case and find free legal help in Arizona. Official sources, no tracking.",
    "imgalt": "Ser querido detenido, Arizona: cuatro primeros pasos con fuentes oficiales. A loved one was detained by ICE: four first steps.",
}
SPANISH_UI += [TEXT["title"], TEXT["desc"], TEXT["imgalt"]]

# Phone numbers shown in buttons and on the card. Each must appear word for word in a quote (checked in main).
PHONES = {
    "ero": ("(602) 257-5900", "+16022575900"),
    "eloy_info": ("(520) 464-3000", "+15204643000"),
    "eloy_msg": ("(520) 466-4141", "+15204664141"),
    "flor_info": ("(520) 868-5862", "+15208685862"),
    "flor_msg": ("(520) 868-8388", "+15208688388"),
    "eoir": ("1-800-898-7180", "+18008987180"),
    "firrp": ("(602) 307-1008", "+16023071008"),
}


def ext(url, label, extra=""):
    return '<a href="%s" rel="noopener noreferrer"%s>%s</a>' % (E(url, quote=True), extra, label)


def sources(lang, ids, level=3):
    head = {"es": "De dónde viene esta información", "en": "Where this information comes from"}[lang]
    chk = {"es": "revisado el", "en": "checked on"}[lang]
    li = []
    for i in ids:
        url, es, en, _f, _t = SOURCES[i]
        li.append('<li>%s <span class="chk">(%s <time datetime="%s">%s</time>)</span></li>'
                  % (ext(url, E(es if lang == "es" else en)), chk, CHECKED, CHECKED_TXT[lang]))
    return '<div class="src"><h%d>%s</h%d><ul>%s</ul></div>' % (level, head, level, "".join(li))


with open(os.path.join(ROOT, "tools", "quotes.json"), encoding="utf-8") as _f:
    QUOTES = json.load(_f)

WHO = {
    "ice": ("Servicio de Inmigración y Control de Aduanas de EE. UU. (ICE)", "U.S. Immigration and Customs Enforcement (ICE)"),
    "doj": ("Departamento de Justicia de EE. UU. (EOIR, los tribunales de inmigración)", "U.S. Department of Justice (EOIR, the immigration courts)"),
    "aclu": ("la ACLU", "the ACLU"),
    "az": ("la ACLU de Arizona", "the ACLU of Arizona"),
}


def quote(lang, key, note=None):
    """A passage copied word for word from its source, with the credit its terms require."""
    q = QUOTES[key]
    es = lang == "es"
    link = '<a href="%s" rel="noopener noreferrer">%s</a>' % (E(q["url"], quote=True), E(q["url"]))
    read = ("Leído el %s." if es else "Read on %s.") % CHECKED_TXT[lang]
    en_note = " (en inglés)" if (es and q["lang"] == "en") else ""
    who_es, who_en = WHO[q["kind"]]
    if es:
        label = "Cita %s%s%s, palabra por palabra y sin cambios" % ("de " if q["kind"] in ("aclu", "az") else "del ", who_es, en_note)
    else:
        label = "Quoted from %s, word for word and unchanged" % (who_en if q["kind"] in ("aclu", "az") else "the " + who_en)
    if q["kind"] in ("ice", "doj"):
        notice = ("Fuente: %s, %s. Documento: %s. Información del gobierno de EE. UU., de dominio público. %s" if es else
                  "Source: %s, %s. Document: %s. U.S. government information, in the public domain. %s") % (
            E(who_es if es else who_en), link, E(q["doc_date"]), read)
    else:
        owner = "American Civil Liberties Union" if q["kind"] == "aclu" else "ACLU of Arizona"
        by = "the ACLU" if q["kind"] == "aclu" else "the ACLU of Arizona"
        notice = "Copyright %s %s. Originally posted by %s at %s. %s" % (q["year"], owner, by, link, read)
    if es:
        SPANISH_UI.append(label)
        SPANISH_UI.append("Fuente: ... Documento: ... Información del gobierno de EE. UU., de dominio público. Leído el ... (aviso de crédito)")
    extra = '<p class="qnote">%s</p>' % E(note) if note else ""
    return '<figure class="quote" lang="%s"><p class="qlabel" lang="%s">%s</p>%s<div class="qbody">%s</div><figcaption>%s</figcaption></figure>' % (
        q["lang"], lang, E(label), extra, q["html"], notice)


def btn(url, label, cls="primary", lang_attr=""):
    return '<a class="btn %s" href="%s" rel="noopener noreferrer"%s>%s</a>' % (cls, E(url, quote=True), lang_attr, E(label))


def tel(lang, key, label_es, label_en):
    shown, e164 = PHONES[key]
    lab = label_es if lang == "es" else label_en
    if lang == "es":
        SPANISH_UI.append(label_es + " (número)")
    return '<a class="btn call" href="tel:%s">%s: %s</a>' % (e164, E(lab), shown)


def content(lang):
    es = lang == "es"
    p = lang
    h = []
    A = h.append

    def T(a, b):
        if es:
            SPANISH_UI.append(re.sub(r"<[^>]+>", "", a) if isinstance(a, str) else " | ".join(re.sub(r"<[^>]+>", "", x) for x in a))
        return a if es else b

    def sec(i, title, body, cls=""):
        A('<section class="panel%s" id="%s-%s" tabindex="-1" aria-labelledby="%s-%s-h"><h2 id="%s-%s-h">%s</h2>%s</section>' % (cls, p, i, p, i, p, i, title, body))

    A('<section class="notice" aria-labelledby="%s-imp-h"><h2 id="%s-imp-h">%s</h2><p>%s</p></section>' % (
        p, p, T("Importante", "Important"),
        T("Esta página da <strong>información general</strong> y enlaces a fuentes oficiales. <strong>No es consejo legal</strong> y no puede decirte qué pasará en el caso de tu familiar. "
          "No guarda ni recoge ningún dato tuyo. Los enlaces te llevan a otros sitios.",
          "This page gives <strong>general information</strong> and links to official sources. <strong>It is not legal advice</strong> and it cannot tell you what will happen in your family member's case. "
          "It does not save or collect any information about you. Links take you to other sites.")))

    # jump menu: the four steps
    jump = [("s1", T("Paso 1. Encuéntralo", "Step 1. Find them")), ("s2", T("Paso 2. Su caso en el tribunal", "Step 2. Their court case")),
            ("s3", T("Paso 3. Ayuda legal gratis en Arizona", "Step 3. Free legal help in Arizona")), ("s4", T("Paso 4. Tu familia", "Step 4. Your family"))]
    A('<nav class="jump no-print" aria-labelledby="%s-jump-h"><h2 id="%s-jump-h">%s</h2><ul>%s</ul></nav>' % (
        p, p, T("Cuatro pasos", "Four steps"),
        "".join('<li><a class="btn secondary" href="#%s-%s">%s</a></li>' % (p, i, t) for i, t in jump)))

    # what you need + card (printable)
    need = [T("Nombre completo, tal como aparece en sus documentos", "Full name, as it appears on their papers"),
            T("Número A (A-Number), si lo tienes", "A-Number, if you have it"),
            T("País de nacimiento", "Country of birth"),
            T("Fecha de nacimiento, si la sabes", "Date of birth, if you know it")]
    fields = [T("Nombre completo", "Full name"), T("Número A (A-Number)", "A-Number"), T("País de nacimiento", "Country of birth"),
              T("Fecha de nacimiento", "Date of birth"), T("Centro donde está (dice el localizador)", "Facility where they are (the locator says)"),
              T("Teléfono del centro", "Facility phone"), T("Abogado o grupo de ayuda legal", "Lawyer or legal aid group"),
              T("Quién cuida a los niños", "Who is caring for the children")]
    card = '<p>%s</p><ul class="check">%s</ul><p class="hint">%s</p>' % (
        T("Reúne esto antes de buscar. Lo que ICE pide está citado en el paso 1.", "Gather this before you search. What ICE asks for is quoted in step 1."),
        "".join("<li>%s</li>" % x for x in need),
        T("Para apuntar en papel, imprime la tarjeta. Esta página no guarda nada de lo que escribes en papel.", "To write on paper, print the card. This page does not keep anything you write on paper."))
    card += '<h3>%s</h3><ul class="fields">%s</ul>' % (T("Anota aquí", "Write here"), "".join('<li><span class="fl">%s</span><span class="line" aria-hidden="true"></span></li>' % x for x in fields))
    phones = [
        (T("ICE, oficina de Phoenix", "ICE, Phoenix field office"), "ero"),
        (T("Tribunales de inmigración (EOIR), caso", "Immigration courts (EOIR), case line"), "eoir"),
        (T("Florence Project, ayuda legal", "Florence Project, legal help"), "firrp"),
        (T("Centro Eloy: información", "Eloy Detention Center: information"), "eloy_info"),
        (T("Centro Eloy: dejar un mensaje urgente", "Eloy Detention Center: urgent message"), "eloy_msg"),
        (T("Centro Florence: información", "Florence Service Processing Center: information"), "flor_info"),
        (T("Centro Florence: dejar un mensaje urgente", "Florence Service Processing Center: urgent message"), "flor_msg"),
    ]
    card += '<h3>%s</h3><ul class="phones">%s<li>%s <strong>www.ice.gov/locator</strong></li></ul><p class="hint">%s</p>' % (
        T("Números de esta página", "Numbers on this page"),
        "".join('<li>%s: <a href="tel:%s"><strong>%s</strong></a></li>' % (lab, PHONES[k][1], PHONES[k][0]) for lab, k in phones),
        T("Localizador de ICE:", "ICE locator:"),
        T("Cada número viene de una cita de esta página. Confirma con la fuente antes de llamar.", "Each number comes from a quote on this page. Confirm with the source before you call."))
    card += '<div class="calls no-print"><button type="button" class="btn primary big js-print">%s</button></div>' % T("Imprimir la tarjeta", "Print the card")
    sec("card", T("Antes de empezar", "Before you start"), card, " card")

    # step 1
    s1 = '<p>%s</p><div class="calls">%s</div>' % (
        T("Abre el localizador de ICE. Esto es lo que dice ICE sobre cómo usarlo.", "Open ICE's locator. This is what ICE says about using it."),
        btn(LOCATOR, T("Abrir el localizador de ICE (ice.gov/locator)", "Open the ICE locator (ice.gov/locator)"), "primary"))
    s1 += quote(lang, "odls_what_" + lang) + quote(lang, "odls_search_" + lang) + quote(lang, "odls_exact_" + lang)
    s1 += '<h3>%s</h3>' % T("Si no aparece", "If they do not appear")
    s1 += '<p>%s</p>' % T("ICE dice que no todos aparecen y qué hacer.", "ICE says not everyone appears, and what to do.")
    s1 += quote(lang, "odls_notin_" + lang) + quote(lang, "odls_notfound_" + lang)
    s1 += '<p>%s</p>' % T("Esta es la oficina de ICE para Arizona.", "This is ICE's office for Arizona.")
    s1 += quote(lang, "ero_phoenix_en")
    s1 += '<div class="calls">%s%s</div>' % (tel(lang, "ero", "Llamar a ICE en Phoenix", "Call ICE in Phoenix"),
                                            btn(ICE_FIELD, T("Todas las oficinas de ICE (en inglés)", "All ICE field offices"), "secondary"))
    s1 += '<p>%s</p>' % T("La ACLU informa de un cambio reciente (28 de octubre de 2026). Es lo que dicen las organizaciones en una demanda, no una decisión de un tribunal.",
                          "The ACLU reports a recent change (October 28, 2026). It is what the organizations say in a lawsuit, not a court decision.")
    s1 += quote(lang, "aclu_lawsuit_en", T("Esto es un comunicado de prensa sobre una demanda.", "This is a press release about a lawsuit."))
    s1 += '<div class="calls">%s</div>' % btn(KJZZ, T("KJZZ: reportaje sobre la demanda (en inglés)", "KJZZ: news report on the lawsuit"), "secondary")
    s1 += '<h3>%s</h3><p>%s</p>' % (T("Si lo encontraste", "If you found them"),
                                    T("ICE dice qué hacer. Estos son los centros de Arizona que leímos (en inglés).", "ICE says what to do. These are the Arizona facilities we read."))
    s1 += quote(lang, "odls_found_" + lang) + quote(lang, "eloy_en") + quote(lang, "florence_en")
    s1 += '<div class="calls">%s%s%s%s</div>' % (
        tel(lang, "eloy_info", "Eloy: información", "Eloy: information"), tel(lang, "eloy_msg", "Eloy: mensaje urgente", "Eloy: urgent message"),
        tel(lang, "flor_info", "Florence: información", "Florence: information"), tel(lang, "flor_msg", "Florence: mensaje urgente", "Florence: urgent message"))
    s1 += '<div class="calls">%s</div>' % btn(SOURCES["ice_factsheet"][0], T("ICE: hoja informativa sobre el localizador (en inglés)", "ICE: fact sheet on the locator"), "secondary")
    s1 += sources(lang, ["ice_brochure_" + lang, "ice_locator", "ice_factsheet", "ice_ero", "ice_eloy", "ice_florence", "aclu_lawsuit", "kjzz"])
    sec("s1", T("Paso 1. Encuéntralo", "Step 1. Find them"), s1)

    # step 2
    s2 = '<p>%s</p><div class="calls">%s%s</div>' % (
        T("Si ya hay un caso en el tribunal de inmigración, puedes ver datos básicos en línea o por teléfono. El sitio pide el número A y la nacionalidad.",
          "If there is already a case in immigration court, you can see basic information online or by phone. The site asks for the A-Number and the nationality."),
        btn(ACIS[lang], T("Abrir ACIS en español (tribunales de inmigración)", "Open ACIS in English (immigration courts)"), "primary"),
        tel(lang, "eoir", "Llamar al sistema de casos (EOIR)", "Call the case line (EOIR)"))
    s2 += quote(lang, "acis_intro_" + lang) + quote(lang, "acis_official_" + lang) + quote(lang, "eoir_status_en")
    s2 += '<p class="hint">%s</p>' % T("ACIS usa una verificación de hCaptcha, un servicio de otra empresa, en el sitio de EOIR. Esta página no la usa.",
                                         "ACIS uses an hCaptcha check, a third-party service, on EOIR's site. This page does not use it.")
    s2 += sources(lang, ["acis_" + lang, "eoir_status"])
    sec("s2", T("Paso 2. Su caso en el tribunal", "Step 2. Their court case"), s2)

    # step 3
    s3 = '<p>%s</p>' % T("Esta es la lista de ayuda legal gratuita que publica el Departamento de Justicia para los tribunales de Eloy y Florence. Es la misma en las dos páginas.",
                          "This is the free legal help list the Department of Justice publishes for the Eloy and Florence courts. It is the same on both pages.")
    s3 += quote(lang, "eoir_list_az_en")
    s3 += '<p class="hint">%s</p>' % T("En la misma lista, las páginas de Phoenix y Tucson muestran al Florence Project solo para casos de niños. Abre la lista completa para ver cada tribunal.",
                                        "In the same list, the Phoenix and Tucson pages show the Florence Project for children's cases only. Open the full list to see each court.")
    s3 += '<div class="calls">%s%s%s</div>' % (
        tel(lang, "firrp", "Llamar al Florence Project", "Call the Florence Project"),
        btn(EOIR_LIST_FILE, T("Lista completa de EOIR, todos los tribunales (PDF, en inglés)", "Full EOIR list, all courts (PDF)"), "primary"),
        btn(FLORENCE_SITE, T("Sitio del Florence Project", "Florence Project website"), "secondary"))
    s3 += '<h3>%s</h3><p>%s</p>' % (T("La ACLU de Arizona", "The ACLU of Arizona"), T("La ACLU de Arizona dice qué sí y qué no hace (en inglés).", "The ACLU of Arizona says what it does and does not do."))
    s3 += quote(lang, "acluaz_limits_en") + quote(lang, "zine_lawyer_en")
    s3 += '<div class="calls">%s</div>' % btn(ACLU_REQUEST, T("ACLU de Arizona: pedir asistencia legal (en inglés)", "ACLU of Arizona: request legal assistance"), "secondary")
    s3 += sources(lang, ["eoir_list", "firrp_site", "acluaz_contact", "acluaz_request", "zine"])
    sec("s3", T("Paso 3. Ayuda legal gratis en Arizona", "Step 3. Free legal help in Arizona"), s3)

    # step 4
    s4 = '<p>%s</p>' % T("Esto dice la ACLU de Arizona sobre el número A y un plan para la familia.", "This is what the ACLU of Arizona says about the A-Number and a family plan.")
    s4 += quote(lang, "zine_family_" + lang)
    s4 += '<div class="calls">%s%s</div>' % (
        btn(FLORENCE_FAMILY, T("Florence Project: plan familiar si ICE detiene a un padre o madre (en inglés)", "Florence Project: making a family plan if ICE picks up a parent"), "primary"),
        btn(ACLU_WEHAVE, T("ACLU: videos «We Have Rights» (hay versión en español)", "ACLU: \"We Have Rights\" videos"), "secondary"))
    s4 += '<p class="hint">%s</p>' % T("No encontramos una fuente oficial con permiso de copia sobre dinero, cuentas o facturas, así que esta página no dice nada sobre eso. Pregunta en la ayuda legal del paso 3.",
                                        "We did not find an official source we may copy on money, bank accounts or bills, so this page says nothing about them. Ask the legal help in step 3.")
    s4 += sources(lang, ["zine", "firrp_family", "aclu_wehave"])
    sec("s4", T("Paso 4. Tu familia", "Step 4. Your family"), s4)

    # about
    li = T([
        "<strong>No es consejo legal.</strong> Es una página de enlaces y de citas copiadas de fuentes oficiales y de la ACLU. No dice qué pasará en el caso de tu familiar. Habla con un abogado o con una organización de ayuda legal.",
        "<strong>No recogemos datos.</strong> Esta página no tiene analíticas, anuncios, cookies, formularios ni cuentas, y no guarda nada. No usa ningún servicio de otra empresa.",
        "<strong>Los enlaces salen de este sitio.</strong> Los otros sitios tienen sus propias reglas de privacidad. Esta página no abre ni llena ningún formulario por ti, y no consulta ningún localizador por ti.",
        "Cada enlace se revisó el <time datetime=\"%s\">%s</time>. Las citas son del gobierno de EE. UU. (de dominio público) y de la ACLU y la ACLU de Arizona; se copian <strong>palabra por palabra y sin cambios</strong>, con el crédito que cada fuente pide. Los títulos, botones y avisos fuera de un recuadro de cita son de esta página. Los números de teléfono salen de las citas." % (CHECKED, CHECKED_TXT["es"]),
        "El localizador de ICE no se pudo abrir con nuestra herramienta (dio «acceso denegado»), así que no leímos sus pantallas. Las citas son del folleto de ICE de diciembre de 2021 y de páginas de ICE y EOIR actualizadas en 2025 y 2026. Las reglas y los teléfonos pueden cambiar.",
        "Esta página no está afiliada a ninguna de las organizaciones nombradas ni al gobierno.",
        "En un teléfono o computadora compartidos, el historial del navegador puede mostrar que visitaste esta página. Si es un riesgo, usa una ventana privada.",
        "Es gratis y siempre lo será.",
    ], [
        "<strong>This is not legal advice.</strong> It is a page of links and of quotes copied from official sources and the ACLU. It does not say what will happen in your family member's case. Talk to a lawyer or a legal aid organization.",
        "<strong>We collect no data.</strong> This page has no analytics, ads, cookies, forms or accounts, and it saves nothing. It uses no third-party service.",
        "<strong>Links leave this site.</strong> Other sites have their own privacy rules. This page does not open or fill in any form for you, and does not query any locator for you.",
        "Every link was checked on <time datetime=\"%s\">%s</time>. The quotes are from the U.S. government (public domain) and from the ACLU and the ACLU of Arizona; they are copied <strong>word for word and unchanged</strong>, with the credit each source asks for. Headings, buttons and notices outside a quote box are this page's own. Phone numbers come from the quotes." % (CHECKED, CHECKED_TXT["en"]),
        "ICE's locator could not be opened with our tool (it answered \"access denied\"), so we did not read its screens. The quotes are from ICE's December 2021 brochure and from ICE and EOIR pages updated in 2025 and 2026. Rules and phone numbers can change.",
        "This page is not affiliated with any of the organizations named or with the government.",
        "On a shared phone or computer, the browser history can show that you visited this page. If that is a risk, use a private window.",
        "It is free and always will be.",
    ])
    sec("about", T("Sobre esta página", "About this page"),
        '<ul class="list">%s</ul><div class="calls no-print"><button type="button" class="btn primary big js-print">%s</button></div>' % (
            "".join("<li>%s</li>" % x for x in li), T("Imprimir la tarjeta", "Print the card")))
    return "\n".join(h)


def jsonld_graph():
    steps = [("s1", "Find them", "Look them up in the ICE Online Detainee Locator System with the A-Number and country of birth, or name and country of birth."),
             ("s2", "Check their court case", "Look up the case in EOIR's Automated Case Information system, online or by phone."),
             ("s3", "Get free legal help in Arizona", "Use the EOIR list of free legal service providers for Arizona, the Florence Project and the ACLU of Arizona."),
             ("s4", "Look after your family", "Read the ACLU of Arizona's family plan passage and the Florence Project's family plan guide.")]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": SITE_URL + "#org", "name": NAME, "url": SITE_URL, "logo": SITE_URL + "apple-touch-icon.png",
             "description": "Free, ad-free, zero-tracking page in Spanish and English that quotes official U.S. government and ACLU sources on finding a person detained by ICE in Arizona, checking their court case and finding free legal help."},
            {"@type": "WebSite", "@id": SITE_URL + "#website", "url": SITE_URL, "name": NAME, "description": TEXT["desc"],
             "inLanguage": ["es", "en"], "publisher": {"@id": SITE_URL + "#org"}},
            {"@type": "WebPage", "@id": SITE_URL + "#webpage", "url": SITE_URL, "name": TEXT["title"], "description": TEXT["desc"],
             "inLanguage": ["es", "en"], "isPartOf": {"@id": SITE_URL + "#website"}, "publisher": {"@id": SITE_URL + "#org"},
             "dateModified": CHECKED,
             "primaryImageOfPage": {"@type": "ImageObject", "url": SITE_URL + "og-image.png", "width": 1200, "height": 630},
             "about": {"@type": "Thing", "name": "First steps when a family member is detained by ICE in Arizona"}},
            {"@type": "HowTo", "@id": SITE_URL + "#howto", "name": TEXT["title_en"], "inLanguage": ["es", "en"],
             "description": "Four first steps, each with the official sources quoted word for word on the page.",
             "step": [{"@type": "HowToStep", "position": i, "name": n, "text": t, "url": SITE_URL + "#es-" + k} for i, (k, n, t) in enumerate(steps, 1)]},
        ],
    }


def page():
    foot_es = ("Este sitio no tiene analíticas y no guarda nada. Está alojado en GitHub Pages, que puede guardar registros estándar de visitas "
               "que nosotros no podemos ver ni controlar. Nosotros no agregamos nada.")
    foot_en = ("This site has no analytics and saves nothing. It is hosted on GitHub Pages, which may keep standard visit logs "
               "that we cannot see or control. We add nothing.")
    lead_es = "¿No puedes comunicarte con alguien y ICE puede tenerlo? Cuatro pasos, con las palabras de las fuentes oficiales."
    lead_en = "Can't reach someone and ICE may have them? Four steps, in the words of the official sources."
    SPANISH_UI.extend([foot_es, "Ir al contenido", "Ser querido detenido", "Primeros pasos · Arizona", lead_es])
    jsonld = json.dumps(jsonld_graph(), ensure_ascii=False, indent=1).replace("</", "<\\/")
    es_html, en_html = content("es"), content("en")
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{site}">
<link rel="alternate" hreflang="es" href="{site}">
<link rel="alternate" hreflang="en" href="{site}">
<link rel="alternate" hreflang="x-default" href="{site}">
<meta property="og:site_name" content="{name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}og-image.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{imgalt}">
<meta property="og:url" content="{site}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_US">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}og-image.png">
<meta name="twitter:image:alt" content="{imgalt}">
<meta name="theme-color" content="#0f5e63">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<script type="application/ld+json">{jsonld}</script>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<link rel="stylesheet" href="style.css">
<noscript><link rel="stylesheet" href="noscript.css"></noscript>
</head>
<body>
<a class="skip es" href="#main">Ir al contenido</a>
<a class="skip en" href="#main" lang="en">Skip to content</a>
<header class="top">
  <div class="brand">
    <h1 class="es">Ser querido detenido <span class="where">Primeros pasos · Arizona</span></h1>
    <h1 class="en" lang="en">A loved one was detained <span class="where">First steps · Arizona</span></h1>
  </div>
  <div class="langs no-print" role="group" aria-label="Idioma / Language">
    <button type="button" id="lang-es" data-lang="es" lang="es" aria-label="ES, Español" aria-pressed="true">ES</button>
    <button type="button" id="lang-en" data-lang="en" lang="en" aria-label="EN, English" aria-pressed="false">EN</button>
  </div>
</header>

<main id="main" tabindex="-1">
<div class="es wrap">
<p class="lead">{lead_es}</p>
{es}
</div>
<div class="en wrap" lang="en">
<p class="lead">{lead_en}</p>
{en}
</div>
</main>

<footer>
  <p class="es">{foot_es}</p>
  <p class="en" lang="en">{foot_en}</p>
  <p>{name} · MIT</p>
</footer>
<script src="app.js"></script>
</body>
</html>
""".format(desc=TEXT["desc"], title=TEXT["title"], imgalt=TEXT["imgalt"], jsonld=jsonld, site=SITE_URL, name=NAME,
           es=es_html, en=en_html, foot_es=foot_es, foot_en=foot_en, lead_es=lead_es, lead_en=lead_en)


def sources_md():
    out = ["# Sources", "",
           "Every external fact and quote on the site, with the page it was read on and the terms that allow (or do not allow) using it.",
           "All pages were read on %s. This file is generated by `tools/build.py`; edit the lists there." % CHECKED, "",
           "Rule: no legal wording on the page is written by us. It is either quoted word for word (`tools/quotes.json`, proven by `tools/verify_quotes.py` against `tools/captures/`) or it is a link. Phone numbers in buttons and on the card are copied from quotes (checked by `tools/build.py`).", "",
           "## Source pages", "", "| # | Source | URL | What the page uses | Terms |", "|---|---|---|---|---|"]
    for n, (k, (url, _es, en, facts, terms)) in enumerate(SOURCES.items(), 1):
        out.append("| %d | %s | %s | %s | %s |" % (n, en, url, facts.replace("|", "/"), terms.replace("|", "/")))
    out += ["", "## Quotes (%d records)" % len(QUOTES), "", "| Key | Language | Source | Document date |", "|---|---|---|---|"]
    for k, q in QUOTES.items():
        out.append("| %s | %s | %s | %s |" % (k, q["lang"], q["title"].replace("|", "/"), q["doc_date"]))
    out += ["", "## Looked for and left out", "",
            "- ICE Online Detainee Locator System itself: not readable by our tool (\"Access Denied\"). Its fields and its Spanish screens were not checked. A human should open it on a phone.",
            "- ICE's Spanish page for the fact sheet (`/es/hojas-de-datos/odls`) returned \"Page Not Found\"; the Spanish text comes from ICE's Spanish brochure instead.",
            "- EOIR Spanish page for case status (`/eoir/check-case-status-espanol`) returned \"Page not found\". The English page is quoted (labelled as English in the Spanish view); ACIS has its own Spanish text, which is quoted.",
            "- ICE detention facility page for Central Arizona Correctional Center: \"Page Not Found\". Other Arizona facilities were not looked up; the locator gives the facility's contact information (see the quoted brochure).",
            "- Bond: ACIS says to contact the local court for bond hearing information (quoted). No bond text is copied or written by us.",
            "- Money, bank accounts, bills, children's school or custody, and notarized caregiver letters: no source found that we may copy, other than the ACLU of Arizona and Florence Project passages used or linked. The Florence Project family plan page is linked only (its terms were not read).",
            "- ACLU national \"We Have Rights\" page: linked only (2017 campaign text).",
            "- ACLU of Arizona's full \"Know Your Rights\" web page (acluaz.org/ikyr): its sections are collapsed and their text was not in the saved page, so the PDF zine was quoted.",
            "- AZ courts guide for parents in ICE custody (azcourts.gov PDF): not used; it is for Arizona courts and child-welfare staff, and its terms were not read.",
            "- Florence Project pages: only links. firrp.org answered ERR_HTTP2_PROTOCOL_ERROR to our headless browser.",
            "", "## Notes for the reviewer", "",
            "- Spanish headings, buttons and notices written for this page were produced by an AI and need a native-speaker read: see NEEDS-NATIVE-READ.md. The quoted Spanish (ICE brochure, EOIR ACIS, ACLU of Arizona zine) is the sources' own, including their typos.",
            "- The page never tells anyone what to do about a legal case in our own words. It names the four tools and quotes what each source says.",
            "- Two ICE statements differ in wording (brochure vs fact sheet) on what the locator needs; the page quotes the brochure and links the fact sheet. See the row above.",
            ""]
    return "\n".join(out)


def native_md():
    seen, rows = set(), []
    for s in SPANISH_UI:
        s = html.unescape(re.sub(r"\s+", " ", s)).strip()
        if s and s not in seen:
            seen.add(s)
            rows.append(s)
    out = ["# Spanish text written for this page (needs a native-speaker read)", "",
           "Generated by `tools/build.py`. Every Spanish string below was written by an AI, not copied from a source. The quoted Spanish (ICE brochure, EOIR ACIS, ACLU of Arizona zine) is not listed here because it is copied unchanged.",
           "Questions for the reader: natural for Mexican and Central American Spanish readers in Arizona? Is \"detenido por ICE\" the usual way to say it? Are \"número A\", \"localizador\", \"tribunal de inmigración\" and \"ayuda legal gratis\" understood? Does any phrase sound like legal advice or promise a result? Is the tone calm enough for someone frightened?", "",
           "Also written by us, in `app.js`: the ES page title and description (same strings as the first two items below).", ""]
    out += ["%d. %s" % (i, r) for i, r in enumerate(rows, 1)]
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    # every phone number shown on the page must be in a quote, word for word
    allq = " ".join(q["html"] for q in QUOTES.values())
    for k, (shown, _e) in PHONES.items():
        assert shown in allq, "phone %s (%s) is not in any quote" % (k, shown)
    out = page()
    assert chr(0x2014) not in out, "em dash found"
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
    md = sources_md()
    nm = native_md()
    assert chr(0x2014) not in md + nm
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    open(os.path.join(ROOT, "docs", "SOURCES.md"), "w", encoding="utf-8").write(md)
    open(os.path.join(ROOT, "docs", "NEEDS-NATIVE-READ.md"), "w", encoding="utf-8").write(nm)
    t, d = TEXT["title"], TEXT["desc"]
    print("built index.html (%d bytes); title %d chars, desc %d chars; en title %d, en desc %d" % (len(out), len(t), len(d), len(TEXT["title_en"]), len(TEXT["desc_en"])))
