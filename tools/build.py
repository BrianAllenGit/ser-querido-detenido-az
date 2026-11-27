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
FFI_EN = "https://www.freedomforimmigrants.org/resources"
FFI_ES = "https://www.freedomforimmigrants.org/recursos"
WRC_ES = "https://www.womensrefugeecommission.org/wp-content/uploads/2025/02/Me-han-detenido-o-deportado-Que-pasara-con-mis-hijos-o-hijas-2025-1.pdf"
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
    "ffi_resources": (
        FFI_EN,
        "Freedom for Immigrants: «Resources for Individuals Facing Detention or Risk of Deportation, their Families and Loved Ones, and Advocates» (en inglés)",
        "Freedom for Immigrants: \"Resources for Individuals Facing Detention or Risk of Deportation, their Families and Loved Ones, and Advocates\" (English)",
        "GUIDE CARD, link only. Read in full on 2026-11-27 (tools/captures/research/ffi_en.txt). No date on the page. Topics used on the card come from its own headings: finding someone in detention (ICE locator, 1-888-351-4024 line, lost-in-detention toolkit), court date (EOIR 1-800-898-7180 and online form), finding an immigration attorney (directories, AILA referral line, avoiding notarios), immigration bond, sending commissary money. National, no Arizona section. The page does not say attorneys reviewed it.",
        "Link only. Footer: \"Copyright © 2026 Freedom for Immigrants. All Rights Reserved.\" No license or reuse statement. Nothing is copied.",
    ),
    "ffi_recursos": (
        FFI_ES,
        "Freedom for Immigrants: «Recursos para personas que enfrentan detención o riesgo de deportación, sus familias y seres queridos, y defensores» (en español)",
        "Freedom for Immigrants: the same page in Spanish",
        "GUIDE CARD, link only. The Spanish version of the page above, read in full on 2026-11-27 (tools/captures/research/ffi_recursos.txt). Same sections.",
        "Link only. Same copyright line as the English page.",
    ),
    "ffi_lost": (
        "https://www.freedomforimmigrants.org/toolkit-lost-in-detention",
        "Freedom for Immigrants: «Toolkit: Lost in the U.S. immigration detention system» (en inglés; la página enlaza una versión en español)",
        "Freedom for Immigrants: \"Toolkit: Lost in the U.S. immigration detention system\" (English; the page links a Spanish version)",
        "Link only, mentioned on the guide card. Read once (WebFetch). It is for friends, family and advocates looking for someone missing in the system. No date, no Arizona section, says it \"does not account for attorney privileges\" and recommends legal counsel. The Spanish version's address was not opened.",
        "Link only. \"Copyright © 2026 Freedom for Immigrants. All Rights Reserved.\"",
    ),
    "firrp_family_en": (
        FLORENCE_FAMILY,
        "Florence Project: «What if I’m Picked up by ICE in Arizona?: Making a Family Plan» (página en inglés)",
        "Florence Project: \"What if I'm Picked up by ICE in Arizona?: Making a Family Plan\" (English page)",
        "GUIDE CARD, link only. Read in full (tools/captures/research/firrp_family.txt). Marked \"Guide Updated 2017\". Arizona-specific, written for immigrant parents in Arizona. Says it was \"prepared by a small group of volunteer lawyers, advocates, and family law experts\"; credits include Steptoe & Johnson (sponsor), a managing attorney, the Florence Project's executive director, a family services consultant. It says it is not legal advice. It does NOT say an attorney reviewed the final text. Part II has a section \"I am detained in Florence or Eloy, how can I get released?\" (table of contents of the PDF).",
        "Link only. The page shows only \"© 2026 Florence Immigrant & Refugee Rights Project\" and a Privacy Policy link; no reuse or license terms. Nothing is copied.",
    ),
    "firrp_family_es": (
        "https://firrp.org/es/resources/prose/parentalrights/",
        "Florence Project: «¿Y Qué si me Agarra y me Arresta el ICE en Arizona?: Desarrollando un Plan de Familia» (página en español)",
        "Florence Project: the family plan guide, Spanish page",
        "GUIDE CARD, link only. Spanish page (tools/captures/research/firrp_es_page.txt). Its own date line is in English: \"Guide Updated 2017\".",
        "Link only. No reuse terms on the page.",
    ),
    "firrp_manual_es": (
        "https://firrp.org/wp-content/uploads/2024/11/firrp-Spanish-Manual.pdf",
        "Florence Project: guía completa en español, Partes I y II (PDF, 19 páginas)",
        "Florence Project: full guide in Spanish, Parts I and II (PDF, 19 pages)",
        "GUIDE CARD, link only. Downloaded and read (tools/captures/research/firrp_es_manual.txt). File timestamp (HTTP Last-Modified) 2024-11-21; the guide itself is marked 2017.",
        "Link only. No copyright or reuse statement found in the PDF text.",
    ),
    "firrp_manual_en": (
        "https://firrp.org/wp-content/uploads/2022/09/English-Manual-2017.pdf",
        "Florence Project: guía completa en inglés, Partes I y II (PDF, 19 páginas, 2017)",
        "Florence Project: full guide in English, Parts I and II (PDF, 19 pages, 2017)",
        "GUIDE CARD, link only. Downloaded and read (tools/captures/research/firrp_en_manual.txt). The file name says 2017.",
        "Link only. No copyright or reuse statement found in the PDF text.",
    ),
    "firrp_part3": (
        "https://firrp.org/wp-content/uploads/2022/09/FUT-Resource-Guide.pdf",
        "Florence Project: Parte III, recursos y ejemplos de documentos para familias en Arizona (PDF, inglés y español)",
        "Florence Project: Part III, resources and document samples for families in Arizona (PDF, English and Spanish)",
        "GUIDE CARD, link only. The address is the one the Florence Project's own page gives. The PDF itself was not opened; HTTP headers show a PDF of 5.5 MB.",
        "Link only.",
    ),
    "wrc_en": (
        "https://www.womensrefugeecommission.org/research-resources/detained-or-deported-parental-toolkit-english-interactive/",
        "Women's Refugee Commission: «Detained or Deported: What About My Children?» (página en inglés)",
        "Women's Refugee Commission: \"Detained or Deported: What About My Children?\" (English page)",
        "GUIDE CARD, link only. Page read (tools/captures/research/wrc_en_page.txt): \"Published March 31, 2025\", toolkit for detained and deported parents; includes ICE contact information, child welfare agency contacts for all 50 states, how to ask for a family-court lawyer. National with Arizona entries in its state lists; the Spanish credits thank the Florence Project for its Arizona guide.",
        "Link only. Page footer: \"Copyright © Women's Refugee Commission, Inc. 2026\". The PDF credits page says \"© 2014 Women's Refugee Commission, Inc.\" (revised 2025). No reuse terms found. Nothing is copied.",
    ),
    "wrc_pdf_es": (
        WRC_ES,
        "Women's Refugee Commission: «Me han detenido o deportado: ¿Qué pasará con mis hijos o hijas?» (PDF en español, 113 páginas, revisado en 2025)",
        "Women's Refugee Commission: Spanish PDF of the toolkit (113 pages, \"Revisado en 2025\")",
        "GUIDE CARD, link only. Downloaded and read (tools/captures/research/wrc.txt). Credits (Spanish): written by four named authors with research and editing support from named people \"así como de las firmas legales Spears & Imes, LLP y Steptoe & Johnson, LLP\"; 2025 revision by Diane Eikenberry. Thanks the Florence Project for its Arizona guide. It does NOT say an attorney reviewed the text.",
        "Link only. \"© 2014 Women's Refugee Commission, Inc. Revisado en 2025\". No reuse terms found.",
    ),
    "wrc_pdf_en": (
        "https://www.womensrefugeecommission.org/wp-content/uploads/2014/05/Parental-Rights-Toolkit-ENGLISH-2025.pdf",
        "Women's Refugee Commission: PDF en inglés de la misma guía (2025)",
        "Women's Refugee Commission: English PDF of the same toolkit (2025)",
        "GUIDE CARD, link only. The address is the one the WRC page gives. Downloaded and read (tools/captures/research/wrc_en.txt); same credits page: \"© 2014 Women’s Refugee Commission\".",
        "Link only.",
    ),
    "ice_locator": (
        LOCATOR,
        "ICE: Sistema Localizador de Detenidos en Línea (ODLS)",
        "ICE: Online Detainee Locator System (ODLS)",
        "Link only. ICE's own brochure gives www.ice.gov/locator as the address; it forwards to locator.ice.gov/odls. The tool is not opened or used by this page. It answered \"Access Denied\" to our automated browser (tools/captures/ice_locator.txt), so its screens, fields and Spanish labels were not read. Whether it works in a normal phone browser could not be checked.",
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
        "Link only on this version of the page (the two paragraphs quoted before are no longer on the page). The page shows no date. The tool asks for an A-Number and a nationality, then an hCaptcha check (a third-party service, on EOIR's site, not on this page). The Spanish text has wording problems of its own (\"se provee a penas\", \"número de registro de Extranjero\"); it is copied as it stands.",
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
}

SPANISH_UI = []  # every Spanish string written for this page, for docs/NEEDS-NATIVE-READ.md

TEXT = {
    "title": "Mi familiar fue detenido por ICE: las mejores guías",
    "title_en": "A loved one was detained by ICE: the best guides",
    "desc": "Guías ya hechas por organizaciones para familias de personas detenidas por ICE, en español e inglés, a un toque. Con las herramientas oficiales. Sin rastreo.",
    "desc_en": "Guides already made by organizations for families of people detained by ICE, in Spanish and English, one tap away. With the official tools. No tracking.",
    "imgalt": "Ser querido detenido, Arizona: las mejores guías que ya existen, en tu idioma. A loved one was detained by ICE: the best existing guides.",
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


# The guides this page boosts. Everything here is a link or a short factual label; no legal wording is written by us.
# Each tuple: (es, en). Buttons: (source id, label es, label en, class, language of the link or None)
GUIDES = [
    {
        "id": "ffi",
        "title": ("Recursos para personas que enfrentan detención o riesgo de deportación, sus familias y seres queridos, y defensores",
                  "Resources for Individuals Facing Detention or Risk of Deportation, their Families and Loved Ones, and Advocates"),
        "for": ("Para cualquier familia · todo el país", "For any family · nationwide"),
        "pub": ("Freedom for Immigrants (organización sin fines de lucro)", "Freedom for Immigrants (nonprofit)"),
        "langs": ("Español e inglés (la página tiene las dos versiones)", "Spanish and English (the page has both versions)"),
        "date": ("La página no muestra fecha. Leída el 27 de noviembre de 2026.", "The page shows no date. Read on November 27, 2026."),
        "covers": ("Cómo encontrar a alguien en detención, su fecha en el tribunal de inmigración, cómo encontrar un abogado, fianza y cómo enviar dinero.",
                   "How to find someone in detention, their immigration court date, how to find a lawyer, bond, and how to send money."),
        "legal": ("La página no dice que abogados la revisaron.", "The page does not say lawyers reviewed it."),
        "buttons": [("ffi_recursos", "Abrir la guía en español", "Open the guide in Spanish", "primary", "es"),
                    ("ffi_resources", "Abrir la guía en inglés", "Open the guide in English", "secondary", "en"),
                    ("ffi_lost", "Si no aparece: kit «Perdido en detención» (en inglés)", "If they do not appear: \"Lost in detention\" toolkit", "secondary", "en")],
    },
    {
        "id": "firrp",
        "title": ("¿Y Qué si me Agarra y me Arresta el ICE en Arizona?: Desarrollando un Plan de Familia",
                  "What if I'm Picked up by ICE in Arizona?: Making a Family Plan"),
        "for": ("Arizona · para madres y padres", "Arizona · for parents"),
        "pub": ("Florence Immigrant & Refugee Rights Project, Florence Project (Arizona)", "Florence Immigrant & Refugee Rights Project, the Florence Project (Arizona)"),
        "langs": ("Español e inglés (guía en PDF y página)", "Spanish and English (PDF guide and page)"),
        "date": ("Guía actualizada en 2017, según el Florence Project. Las reglas pueden haber cambiado.", "Guide updated in 2017, according to the Florence Project. Rules may have changed."),
        "covers": ("Quién cuida a los niños, poder notarial, tutela temporal, documentos, qué hacer si ICE detiene a un padre o madre, cómo salir de Florence o Eloy, la corte de inmigración y el sistema de bienestar de menores (CPS).",
                   "Who cares for the children, power of attorney, temporary guardianship, documents, what to do if ICE picks up a parent, how to get released from Florence or Eloy, immigration court and the child welfare system (CPS)."),
        "legal": ("El Florence Project dice que la prepararon voluntarios: abogados, defensores y expertos en derecho de familia. No dice que un abogado revisó el texto final.",
                  "The Florence Project says it was prepared by volunteers: lawyers, advocates and family law experts. It does not say a lawyer reviewed the final text."),
        "buttons": [("firrp_manual_es", "Abrir la guía completa (PDF, español)", "Open the full guide (PDF, Spanish)", "primary", "es"),
                    ("firrp_manual_en", "Abrir la guía completa (PDF, inglés)", "Open the full guide (PDF, English)", "secondary", "en"),
                    ("firrp_family_es", "Página de la guía en español", "Guide page in Spanish", "secondary", "es"),
                    ("firrp_family_en", "Página de la guía en inglés", "Guide page in English", "secondary", "en"),
                    ("firrp_part3", "Parte III: recursos y documentos de ejemplo (PDF)", "Part III: resources and document samples (PDF)", "secondary", None)],
    },
    {
        "id": "wrc",
        "title": ("Me han detenido o deportado: ¿Qué pasará con mis hijos o hijas?", "Detained or Deported: What About My Children?"),
        "for": ("Para madres y padres · todo el país, con listas por estado", "For parents · nationwide, with state-by-state lists"),
        "pub": ("Women's Refugee Commission (organización sin fines de lucro, Nueva York)", "Women's Refugee Commission (nonprofit, New York)"),
        "langs": ("Español e inglés (PDF de 113 páginas)", "Spanish and English (113-page PDF)"),
        "date": ("Publicada el 31 de marzo de 2025. El PDF dice «Revisado en 2025».", "Published March 31, 2025. The PDF says \"Revised 2025\"."),
        "covers": ("Cómo proteger sus derechos como madre o padre, quién cuida a los niños, el sistema de bienestar de menores, la corte de familia, cómo conseguir abogado y cómo reunirse con sus hijos. Incluye contactos de ICE y de las agencias de cada estado.",
                   "How to protect your rights as a parent, who cares for the children, the child welfare system, family court, how to get a lawyer and how to reunite with your children. Includes ICE contacts and each state's agencies."),
        "legal": ("Los créditos dan las gracias a los bufetes Spears & Imes y Steptoe & Johnson por apoyar la investigación y el borrador. No dicen que abogados revisaron el texto final.",
                  "The credits thank the law firms Spears & Imes and Steptoe & Johnson for supporting the research and drafting. They do not say lawyers reviewed the final text."),
        "buttons": [("wrc_pdf_es", "Abrir la guía (PDF, español)", "Open the guide (PDF, Spanish)", "primary", "es"),
                    ("wrc_pdf_en", "Abrir la guía (PDF, inglés)", "Open the guide (PDF, English)", "secondary", "en"),
                    ("wrc_en", "Página de la guía (en inglés)", "Guide page (English)", "secondary", "en")],
    },
]


def guide_card(lang, g):
    es = lang == "es"
    i = 0 if es else 1
    labels = (("Publica", "Idiomas", "Fecha", "Qué cubre", "Abogados"), ("Published by", "Languages", "Date", "What it covers", "Lawyers"))[i]
    if es:
        SPANISH_UI.extend(list(labels) + [g["title"][0], g["for"][0], g["pub"][0], g["langs"][0], g["date"][0], g["covers"][0], g["legal"][0]])
    rows = "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (E(l), E(v[i])) for l, v in zip(labels, [g["pub"], g["langs"], g["date"], g["covers"], g["legal"]]))
    # buttons: the one in the reader's language comes first
    btns = []
    for sid, bes, ben, cls, bl in g["buttons"]:
        url = SOURCES[sid][0]
        label = bes if es else ben
        if es:
            SPANISH_UI.append(bes)
        la = "" if bl in (None, lang) else ' lang="%s"' % bl
        btns.append((0 if bl == lang else 1, '<a class="btn %s" href="%s" rel="noopener noreferrer"%s>%s</a>' % (
            "primary" if bl == lang and cls == "primary" else "secondary", E(url, quote=True), la, E(label))))
    first = sorted(btns, key=lambda x: x[0])
    return ('<article class="guide" aria-labelledby="%s-g-%s"><p class="gfor">%s</p><h3 id="%s-g-%s"%s>%s</h3><dl class="meta">%s</dl><div class="calls">%s</div></article>' % (
        lang, g["id"], E(g["for"][i]), lang, g["id"], "" if es else "", E(g["title"][i]), rows, "".join(b for _o, b in first)))


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
        T("Esta página no escribe consejos: <strong>te lleva a guías que ya hicieron organizaciones</strong>. <strong>No es consejo legal.</strong> No guarda ni recoge ningún dato tuyo. Los enlaces te llevan a otros sitios.",
          "This page does not write advice: <strong>it takes you to guides that organizations already made</strong>. <strong>It is not legal advice.</strong> It does not save or collect any information about you. Links take you to other sites.")))

    # 1. the guides
    body = '<p>%s</p>' % T("No escribimos una guía nueva. Estas ya existen. Ábrelas en tu idioma.", "We did not write a new guide. These already exist. Open them in your language.")
    body += "".join(guide_card(lang, g) for g in GUIDES)
    body += '<p class="hint">%s</p>' % T("Dos de las tres hablan de los niños y del papá o la mamá detenidos. Ninguna dice que la revisó un abogado, y ninguna da permiso de copiar su texto: por eso esta página solo las enlaza.",
                                        "Two of the three are about the children and the detained parent. None says a lawyer reviewed it, and none gives permission to copy its text, so this page only links them.")
    body += sources(lang, ["ffi_resources", "ffi_recursos", "ffi_lost", "firrp_family_" + lang, "firrp_manual_" + lang, "firrp_part3", "wrc_en", "wrc_pdf_" + lang])
    sec("guides", T("Las mejores guías que ya existen", "The best guides that already exist"), body)

    # 2. official tools
    t = '<p>%s</p><div class="calls">%s%s%s</div>' % (
        T("Herramientas del gobierno de EE. UU. para buscar a la persona y ver su caso en el tribunal de inmigración.",
          "U.S. government tools to find the person and see their immigration court case."),
        btn(LOCATOR, T("Abrir el localizador de ICE (ice.gov/locator)", "Open the ICE locator (ice.gov/locator)"), "primary"),
        btn(ACIS[lang], T("Abrir ACIS en español (tribunales de inmigración)", "Open ACIS in English (immigration courts)"), "primary"),
        btn(EOIR_STATUS, T("EOIR: cómo ver el estado del caso (en inglés)", "EOIR: how to check case status"), "secondary"))
    t += sources(lang, ["ice_locator", "acis_" + lang, "eoir_status"])
    sec("tools", T("Herramientas oficiales", "Official tools"), t)

    # 3. phone numbers, each copied from a quote
    ph = '<p>%s</p><div class="calls">%s%s%s%s%s%s%s</div>' % (
        T("Cada número viene de una página oficial. Abajo está el texto de donde salen.", "Each number comes from an official page. The text it comes from is below."),
        tel(lang, "ero", "ICE, oficina de Phoenix", "ICE, Phoenix field office"),
        tel(lang, "eloy_info", "Eloy: información", "Eloy: information"), tel(lang, "eloy_msg", "Eloy: mensaje urgente", "Eloy: urgent message"),
        tel(lang, "flor_info", "Florence: información", "Florence: information"), tel(lang, "flor_msg", "Florence: mensaje urgente", "Florence: urgent message"),
        tel(lang, "eoir", "Tribunales de inmigración, línea de casos (EOIR)", "Immigration courts, case line (EOIR)"),
        tel(lang, "firrp", "Florence Project, ayuda legal", "Florence Project, legal help"))
    ph += '<details class="srcq"><summary>%s</summary>' % T("Ver el texto oficial de donde salen los números (en inglés)", "See the official text the numbers come from")
    ph += quote(lang, "ero_phoenix_en") + quote(lang, "eloy_en") + quote(lang, "florence_en") + quote(lang, "eoir_status_en") + quote(lang, "eoir_list_az_en")
    ph += '</details>'
    ph += '<div class="calls">%s</div>' % btn(EOIR_LIST_FILE, T("Lista completa de ayuda legal gratis de EOIR (PDF, en inglés)", "Full EOIR list of free legal help (PDF)"), "secondary")
    ph += sources(lang, ["ice_ero", "ice_eloy", "ice_florence", "eoir_status", "eoir_list"])
    sec("phones", T("Teléfonos oficiales de Arizona", "Official Arizona phone numbers"), ph)

    # about
    li = T([
        "<strong>No es consejo legal.</strong> Es una página de enlaces. No dice qué pasará en el caso de tu familiar. Habla con un abogado o con una organización de ayuda legal.",
        "<strong>No recogemos datos.</strong> Esta página no tiene analíticas, anuncios, cookies, formularios ni cuentas, y no guarda nada. No usa ningún servicio de otra empresa.",
        "<strong>Los enlaces salen de este sitio.</strong> Los otros sitios tienen sus propias reglas de privacidad. Esta página no abre ni llena ningún formulario por ti.",
        "Cada enlace se revisó el <time datetime=\"%s\">%s</time>. Las guías se enlazan, no se copian. Los textos en recuadro son del gobierno de EE. UU. (de dominio público), copiados <strong>palabra por palabra y sin cambios</strong>, con su crédito. Los títulos, botones y avisos fuera de un recuadro son de esta página." % (CHECKED, CHECKED_TXT["es"]),
        "El localizador de ICE no se pudo abrir con nuestra herramienta (dio «acceso denegado»), así que no leímos sus pantallas. Las reglas y los teléfonos pueden cambiar. Esta página no está afiliada a ninguna de las organizaciones nombradas ni al gobierno.",
        "En un teléfono o computadora compartidos, el historial del navegador puede mostrar que visitaste esta página. Si es un riesgo, usa una ventana privada. Es gratis y siempre lo será.",
    ], [
        "<strong>This is not legal advice.</strong> It is a page of links. It does not say what will happen in your family member's case. Talk to a lawyer or a legal aid organization.",
        "<strong>We collect no data.</strong> This page has no analytics, ads, cookies, forms or accounts, and it saves nothing. It uses no third-party service.",
        "<strong>Links leave this site.</strong> Other sites have their own privacy rules. This page does not open or fill in any form for you.",
        "Every link was checked on <time datetime=\"%s\">%s</time>. The guides are linked, not copied. The quote boxes are U.S. government text (public domain), copied <strong>word for word and unchanged</strong>, with credit. Headings, buttons and notices outside a quote box are this page's own." % (CHECKED, CHECKED_TXT["en"]),
        "ICE's locator could not be opened with our tool (it answered \"access denied\"), so we did not read its screens. Rules and phone numbers can change. This page is not affiliated with any of the organizations named or with the government.",
        "On a shared phone or computer, the browser history can show that you visited this page. If that is a risk, use a private window. It is free and always will be.",
    ])
    sec("about", T("Sobre esta página", "About this page"), '<ul class="list">%s</ul>' % "".join("<li>%s</li>" % x for x in li))
    return "\n".join(h)


def jsonld_graph():
    guides = [("Freedom for Immigrants: Resources for people facing detention, their families and loved ones", SOURCES["ffi_resources"][0]),
              ("Florence Project: What if I'm Picked up by ICE in Arizona? Making a Family Plan", SOURCES["firrp_family_en"][0]),
              ("Women's Refugee Commission: Detained or Deported: What About My Children?", SOURCES["wrc_en"][0])]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": SITE_URL + "#org", "name": NAME, "url": SITE_URL, "logo": SITE_URL + "apple-touch-icon.png",
             "description": "Free, ad-free, zero-tracking page in Spanish and English that links the best existing guides for families of people detained by ICE, and the official U.S. government tools and phone numbers for Arizona."},
            {"@type": "WebSite", "@id": SITE_URL + "#website", "url": SITE_URL, "name": NAME, "description": TEXT["desc"],
             "inLanguage": ["es", "en"], "publisher": {"@id": SITE_URL + "#org"}},
            {"@type": "WebPage", "@id": SITE_URL + "#webpage", "url": SITE_URL, "name": TEXT["title"], "description": TEXT["desc"],
             "inLanguage": ["es", "en"], "isPartOf": {"@id": SITE_URL + "#website"}, "publisher": {"@id": SITE_URL + "#org"},
             "dateModified": CHECKED,
             "primaryImageOfPage": {"@type": "ImageObject", "url": SITE_URL + "og-image.png", "width": 1200, "height": 630},
             "about": {"@type": "Thing", "name": "Guides for families when a loved one is detained by ICE"}},
            {"@type": "ItemList", "@id": SITE_URL + "#guides", "name": "Guides for families of people detained by ICE", "inLanguage": ["es", "en"],
             "numberOfItems": len(guides),
             "itemListElement": [{"@type": "ListItem", "position": i, "name": n, "url": u} for i, (n, u) in enumerate(guides, 1)]},
        ],
    }


def page():
    foot_es = ("Este sitio no tiene analíticas y no guarda nada. Está alojado en GitHub Pages, que puede guardar registros estándar de visitas "
               "que nosotros no podemos ver ni controlar. Nosotros no agregamos nada.")
    foot_en = ("This site has no analytics and saves nothing. It is hosted on GitHub Pages, which may keep standard visit logs "
               "that we cannot see or control. We add nothing.")
    lead_es = "Las mejores guías que ya existen, en tu idioma, a un toque."
    lead_en = "The best guides that already exist, in your language, one tap away."
    SPANISH_UI.extend([foot_es, "Ir al contenido", "Ser querido detenido", "Guías · Arizona", lead_es])
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
    <h1 class="es">Ser querido detenido <span class="where">Guías · Arizona</span></h1>
    <h1 class="en" lang="en">A loved one was detained <span class="where">Guides · Arizona</span></h1>
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
           "Rule: no legal wording on the page is written by us. The page boosts existing guides by linking them (no guide text is copied); the only quoted text is ICE and EOIR text for the phone numbers (`tools/quotes.json`, proven by `tools/verify_quotes.py` against `tools/captures/`). Phone numbers in buttons are copied from quotes (checked by `tools/build.py`).", "",
           "## Source pages", "", "| # | Source | URL | What the page uses | Terms |", "|---|---|---|---|---|"]
    for n, (k, (url, _es, en, facts, terms)) in enumerate(SOURCES.items(), 1):
        out.append("| %d | %s | %s | %s | %s |" % (n, en, url, facts.replace("|", "/"), terms.replace("|", "/")))
    out += ["", "## Quotes (%d records)" % len(QUOTES), "", "| Key | Language | Source | Document date |", "|---|---|---|---|"]
    for k, q in QUOTES.items():
        out.append("| %s | %s | %s | %s |" % (k, q["lang"], q["title"].replace("|", "/"), q["doc_date"]))
    out += ["", "## Looked for and left out (this version of the page)", "",
            "Full research with every candidate, terms and dates: the vault note `projects/public-goods/detained-guides-2026-11-27.md` (not in this repository).",
            "- ICE Online Detainee Locator System itself: not readable by our tool (\"Access Denied\"). Its fields and its Spanish screens were not checked. A human should open it on a phone.",
            "- Informed Immigrant (FWD.us) \"Help for People in Detention or Facing Deportation\": English page read, no date, no Arizona content, no attorney-review claim; its Spanish page answered HTTP 500 and could not be read. Not chosen.",
            "- DetentionHelp.org (ASAP, Human Rights First, National Immigration Project): a tool to prepare a federal release petition, EN/ES/ZH. Not a guide, and the detained person must file; not chosen, mentioned in the PR.",
            "- ABA Commission on Immigration \"Guide for Family and Friends of Individuals in ICE Detention\": americanbar.org blocks our tools (Cloudflare 403), the guide could not be read. Not chosen.",
            "- Immigrant Defense Project, CLINIC, NIJC: blocked (Cloudflare / HTTP/2 errors) or not a family guide; not read.",
            "- ILRC Step-by-Step Family Preparedness Plan (2026): read; California-specific forms and a plan to make before detention. Not chosen.",
            "- NYC and Legal Aid NYC guides on what to do after a loved one is detained: New York resources, not Arizona.",
            "- Removed from the page in this version: the ICE locator brochure quotes, the EOIR ACIS quotes, the ACLU lawsuit quote, the ACLU of Arizona zine and contact quotes, and the links to KJZZ, ACLU Request Legal Assistance and ACLU We Have Rights. The ACLU of Arizona terms questions no longer apply.",
            "", "## Notes for the reviewer", "",
            "- Spanish headings, buttons, card labels and notices written for this page were produced by an AI and need a native-speaker read: see NEEDS-NATIVE-READ.md. The quoted ICE and EOIR text is in English only (the sources' own).",
            "- The guide cards describe each guide's contents in short factual labels taken from the guide's own headings. They are our wording and are listed for a native read and a content read.",
            "- Attorney review: none of the three guides says a lawyer reviewed it. The Florence Project guide was written by volunteer lawyers and advocates (their statement). This is stated on the page.",
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
           "Generated by `tools/build.py`. Every Spanish string below was written by an AI, not copied from a source. The titles of the three guides and the publisher names are the sources' own and are listed only where we translated or shortened them. No quoted Spanish remains on the page.",
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
