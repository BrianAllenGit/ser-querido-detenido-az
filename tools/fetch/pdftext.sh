#!/bin/bash
# Turns the saved PDFs into text (poppler pdftotext). The EOIR list is two columns per page, so page 4 (Eloy) and 5 (Florence) are cut in half.
set -euo pipefail
cd "$(dirname "$0")/../captures/pdf"
pdftotext odls_brochure_en.pdf odls_brochure_en.txt
pdftotext odls_brochure_es.pdf odls_brochure_es.txt
pdftotext -raw acluaz_zine_2025.pdf acluaz_zine_raw.txt
for pg in 4 5; do
  name=$([ $pg = 4 ] && echo eloy || echo florence)
  pdftotext -f $pg -l $pg -x 0 -y 90 -W 295 -H 702 probono_full.pdf eoir_az_${name}_left.txt
  pdftotext -f $pg -l $pg -x 295 -y 90 -W 317 -H 702 probono_full.pdf eoir_az_${name}_right.txt
done
pdftotext -f 4 -l 4 probono_full.pdf eoir_az_eloy_page.txt
