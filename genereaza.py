#!/usr/bin/env python3
"""Regenerates the AKKRO product nomenclature page and the missing-datasheet report.

Usage:
    python3 genereaza.py "Produs (product.template).xlsx" [--drive-folder ID] [--out output]

Inputs:
  - the Odoo product export (one sheet, grey grouping rows included);
  - the public Google Drive folder with the datasheets (listed live, no local copy needed);
  - fise_reguli.json: which products each datasheet belongs to.

Outputs (in --out):
  - produse.html: standalone page, opens with a double click (contains Cost - internal only);
  - produse.csv, produse.xlsx: the same product table (the xlsx also has the report as a second sheet);
  - raport.csv: products without a datasheet, datasheets without a product, matches to confirm,
    duplicate names, uncategorized products, grey headers whose count differs from the rows read.

Standard library only.
"""

import argparse
import collections
import csv
import html
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DRIVE_FOLDER = "1awNY200Ee6N5V21YT50wkgHcwc7k4Oka"
UNCATEGORIZED = "Fără categorie"
STATUS_WITH = "cu fișă"
STATUS_WITHOUT = "fără fișă"
STATUS_TO_CONFIRM = "fișă de confirmat"

XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
# Excel header -> key in the page data
COLUMNS = {
    "Favorite": "favorite",
    "Nume": "name_original",
    "Referință internă": "ref",
    "Responsabil": "responsible",
    "Etichete produs": "tags",
    "Preț vânzare": "price",
    "Cost": "cost",
    "Categorie produs": "category_raw",
    "Tip produs": "type",
    "Cantitate în stoc": "qty_stock",
    "Cantitate prognozată": "qty_forecast",
    "Available to promise": "qty_atp",
    "Unitatea de măsură": "uom",
    "Activitate Excepție Decorare": "activity_exception",
}
NUMERIC = {"price", "cost", "qty_stock", "qty_forecast", "qty_atp"}
HEADER_COUNT = re.compile(r"^(?P<title>.*?)\s*\((?P<count>\d+)\)\s*$")


def read_xlsx_rows(path):
    """Rows of the first sheet as lists of cell strings (stdlib only)."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{XLSX_NS}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{XLSX_NS}t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))

    def col_index(ref):
        letters = re.match(r"[A-Z]+", ref).group()
        n = 0
        for ch in letters:
            n = n * 26 + ord(ch) - 64
        return n - 1

    rows = []
    for row in sheet.iter(f"{XLSX_NS}row"):
        cells = {}
        for c in row.iter(f"{XLSX_NS}c"):
            kind, v = c.get("t"), c.find(f"{XLSX_NS}v")
            if kind == "inlineStr":
                value = "".join(t.text or "" for t in c.iter(f"{XLSX_NS}t"))
            elif v is None:
                continue
            elif kind == "s":
                value = shared[int(v.text)]
            else:
                value = v.text or ""
            cells[col_index(c.get("r"))] = value
        width = max(cells, default=-1) + 1
        rows.append([cells.get(i, "") for i in range(width)])
    return rows


def clean_name(name):
    """Decodes Odoo HTML entities (&quot;) and collapses whitespace."""
    return re.sub(r"\s+", " ", html.unescape(name)).strip()


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def split_category(raw):
    raw = raw.strip()
    if not raw or raw == "All" or raw.startswith("All /"):
        return UNCATEGORIZED, ""
    category, _, subcategory = raw.partition("/")
    return category.strip(), subcategory.strip()


def parse_products(rows):
    """Splits the export into products and grey grouping headers.

    A grey row has no `Nume`; its first cell is `<title> (<expected count>)`. Indented headers are
    categories, non-indented ones are product types. Each header counts the product rows below it
    until the next header of the same or a higher level.
    """
    header = [h.strip() for h in rows[0]]
    missing = [h for h in ("Nume", "Referință internă", "Categorie produs") if h not in header]
    if missing:
        found = ", ".join(h for h in header if h)
        sys.exit(f"Exportul din Odoo nu are coloanele: {', '.join(missing)}.\nColoanele găsite: {found}")
    index = {COLUMNS[h]: i for i, h in enumerate(header) if h in COLUMNS}
    name_col = header.index("Nume")

    products, groups, open_groups, skipped = [], [], {}, []
    for row_number, row in enumerate(rows[1:], start=2):
        row = row + [""] * (len(header) - len(row))
        if not row[name_col].strip():
            label = row[0]
            match = HEADER_COUNT.match(label.strip())
            if not match:  # no name and not a grey row: say so, a product without a name must not vanish quietly
                if any(cell.strip() for cell in row):
                    skipped.append(f"rândul {row_number} din Excel nu are Nume și nu e rând gri, l-am sărit")
                continue
            level = 1 if label.startswith(" ") else 0
            group = {
                "row": row_number,
                "level": level,
                "title": match["title"],
                "expected": int(match["count"]),
                "read": 0,
            }
            groups.append(group)
            open_groups = {lvl: g for lvl, g in open_groups.items() if lvl < level}
            open_groups[level] = group
            continue

        p = {key: row[i].strip() for key, i in index.items()}
        p["row"] = row_number
        p["name_original"] = row[name_col]
        p["name"] = clean_name(row[name_col])
        p["category_original"] = p.pop("category_raw", "")
        p["category"], p["subcategory"] = split_category(p["category_original"])
        for key in NUMERIC:
            p[key] = to_number(p.get(key))
        products.append(p)
        for group in open_groups.values():
            group["read"] += 1
    return products, groups, skipped


def list_drive_folder(folder_id):
    """Files of a public Drive folder: [{name, url}]. Fails loudly - an empty list would mark
    every product as having no datasheet."""
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            page = response.read().decode("utf-8")
    except Exception as e:
        sys.exit(
            f"Nu pot deschide folderul din Drive ({url}): {e}\nVerifică dacă ai internet și dacă folderul e partajat cu link."
        )

    files = []
    for entry in page.split('class="flip-entry"')[1:]:
        link = re.search(r'<a href="([^"]+)"', entry)
        title = re.search(r'flip-entry-title">([^<]+)<', entry)
        if not link or not title:
            continue
        if "/folders/" in link.group(1):
            print(
                f"  ! Am sărit subfolderul «{html.unescape(title.group(1))}» din Drive: se citesc doar fișierele din folderul principal."
            )
            continue
        files.append(
            {
                "name": html.unescape(title.group(1)).strip(),
                "url": html.unescape(link.group(1)).replace("?usp=drive_web", ""),
            }
        )
    if not files:
        sys.exit(f"Folderul din Drive {folder_id} e gol sau nu e partajat cu link.")
    return files


def match_datasheets(products, files, rules):
    """Links each Drive file to products using fise_reguli.json.

    Returns (links per product row, report rows for files without product, warnings).
    """
    by_name = {f["name"]: f for f in files}
    links = collections.defaultdict(list)
    unmatched_files, warnings = [], []

    for file_name in sorted(set(rules) - set(by_name)):
        warnings.append(f"fise_reguli.json are o regulă pentru «{file_name}», dar fișierul nu mai e în Drive.")

    for f in files:
        rule = rules.get(f["name"])
        if not rule:
            unmatched_files.append((f, "nu are încă o regulă în fise_reguli.json"))
            continue
        hits = 0
        for m in rule["potriviri"]:
            name_re = re.compile(m["nume"], re.I)
            sub_re = re.compile(m["subcategorie"], re.I) if m.get("subcategorie") else None
            for p in products:
                if name_re.search(p["name"]) and (not sub_re or sub_re.search(p["subcategory"])):
                    links[p["row"]].append(
                        {
                            "name": f["name"],
                            "url": f["url"],
                            "exact": m["tip"] == "exact",
                            "note": m.get("nota") or rule.get("nota", ""),
                        }
                    )
                    hits += 1
        if not hits:  # a rule with no matches can say why (e.g. the file is not a datasheet)
            unmatched_files.append(
                (f, rule.get("nota") or "regula din fise_reguli.json nu se potrivește cu niciun produs")
            )
    return links, unmatched_files, warnings


def fold(text):
    """Lowercase, no diacritics - same normalization as the page search."""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(c))


def build(products, groups, files, rules):
    links, unmatched_files, warnings = match_datasheets(products, files, rules)
    name_counts = collections.Counter(p["name"] for p in products)

    for p in products:
        sheets = {}
        for link in links.get(p["row"], []):  # one file can match through several rules
            sheet = sheets.setdefault(link["name"], {**link, "exact": False})
            if link["exact"]:  # an exact match wins, and its (empty) note replaces a weaker rule's note
                sheet.update(exact=True, note=link["note"])
        p["sheets"] = list(sheets.values())
        if any(s["exact"] for s in sheets.values()):
            p["status"] = STATUS_WITH
        elif sheets:
            p["status"] = STATUS_TO_CONFIRM
        else:
            p["status"] = STATUS_WITHOUT
        p["alerts"] = []
        if name_counts[p["name"]] > 1:
            p["alerts"].append(f"numele apare de {name_counts[p['name']]} ori")
        if not p["ref"]:
            p["alerts"].append("fără referință internă")
        if p["category"] == UNCATEGORIZED:
            p["alerts"].append("fără categorie")
        p["search"] = fold(f"{p['name']} {p['ref']}")

    report = []

    def add(section, p=None, sheet="", url="", details=""):
        report.append(
            {
                "Secțiune": section,
                "Referință internă": p["ref"] if p else "",
                "Nume": p["name"] if p else "",
                "Categorie": p["category"] if p else "",
                "Subcategorie": p["subcategory"] if p else "",
                "Fișă tehnică": sheet,
                "Link": url,
                "Detalii": details,
            }
        )

    for p in products:
        if p["status"] == STATUS_WITHOUT:
            add("Produse fără fișă tehnică", p)
    for f, reason in unmatched_files:
        add("Fișe tehnice fără produs", sheet=f["name"], url=f["url"], details=reason)
    for p in products:
        if p["status"] == STATUS_TO_CONFIRM:
            for s in p["sheets"]:
                add(
                    "Produse cu fișă de confirmat",
                    p,
                    s["name"],
                    s["url"],
                    s["note"] or "documentul e pentru o familie de produse sau e general, nu e fișa acestui produs",
                )
    for p in sorted((p for p in products if name_counts[p["name"]] > 1), key=lambda p: (p["name"], p["ref"])):
        add("Nume duplicate", p, details=f"apare de {name_counts[p['name']]} ori")
    for p in products:
        if p["category"] == UNCATEGORIZED:
            add("Produse fără categorie", p, details=f"categoria din Odoo: {p['category_original']}")
    for g in groups:
        if g["expected"] != g["read"]:
            kind = "categoria" if g["level"] else "tipul de produs"
            add(
                "Rânduri gri cu alt număr de produse",
                details=f"{kind} «{g['title']}», rândul {g['row']} din Excel: rândul gri spune {g['expected']}, "
                f"sub el sunt {g['read']}",
            )

    return report, warnings


REPORT_FIELDS = [
    "Secțiune",
    "Referință internă",
    "Nume",
    "Categorie",
    "Subcategorie",
    "Fișă tehnică",
    "Link",
    "Detalii",
]


def display_price(p):
    return "–" if p["price"] is None or p["price"] == 1 else p["price"]


# Export columns: same order as the page table, then the optional and the kept-in-data columns
PRODUCT_EXPORT = [
    ("Categorie", lambda p: p["category"]),
    ("Subcategorie", lambda p: p["subcategory"]),
    ("Nume", lambda p: p["name"]),
    ("Referință internă", lambda p: p["ref"]),
    ("Tip produs", lambda p: p["type"]),
    ("Preț vânzare", display_price),
    ("Cost", lambda p: p["cost"]),
    ("Fișă tehnică", lambda p: " | ".join(s["name"] for s in p["sheets"])),
    ("Link fișă", lambda p: " | ".join(s["url"] for s in p["sheets"])),
    ("Status fișă", lambda p: p["status"]),
    ("Alertă", lambda p: ", ".join(p["alerts"])),
    ("Favorite", lambda p: p["favorite"]),
    ("Responsabil", lambda p: p["responsible"]),
    ("Etichete produs", lambda p: p["tags"]),
    ("Cantitate în stoc", lambda p: p["qty_stock"]),
    ("Cantitate prognozată", lambda p: p["qty_forecast"]),
    ("Available to promise", lambda p: p["qty_atp"]),
    ("Activitate Excepție Decorare", lambda p: p["activity_exception"]),
    ("Unitatea de măsură", lambda p: p["uom"]),
    ("Nume original", lambda p: p["name_original"]),
    ("Categorie produs (Odoo)", lambda p: p["category_original"]),
]


def product_table(products):
    return [h for h, _ in PRODUCT_EXPORT], [[get(p) for _, get in PRODUCT_EXPORT] for p in products]


def report_table(report):
    return REPORT_FIELDS, [[r[f] for f in REPORT_FIELDS] for r in report]


def write_csv(path, header, rows):
    # utf-8-sig + ';' so Excel with Romanian regional settings opens it directly
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)
        writer.writerows([csv_value(v) for v in row] for row in rows)


def csv_value(value):
    """Numbers with a decimal comma, as Excel with Romanian settings expects them."""
    if value is None:
        return ""
    if isinstance(value, float):  # .15g keeps every digit (":g" alone rounds 23108.63 to 23108.6)
        return f"{value:.15g}".replace(".", ",") if value != int(value) else str(int(value))
    return value


def col_letter(index):
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def xml_text(value):
    """Escapes for XML and drops control characters Excel rejects."""
    return html.escape(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value)), quote=False)


def sheet_xml(header, rows):
    widths = [min(max(len(str(v or "")) for v in col) + 2, 60) for col in zip(header, *rows)]
    lines = []
    for r, row in enumerate([header, *rows], start=1):
        cells = []
        for c, value in enumerate(row):
            ref = f"{col_letter(c)}{r}"
            style = ' s="1"' if r == 1 else ""
            if value is None or value == "":
                continue
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{ref}"{style}><v>{value}</v></c>')
            else:
                cells.append(
                    f'<c r="{ref}" t="inlineStr"{style}><is><t xml:space="preserve">{xml_text(value)}</t></is></c>'
                )
        lines.append(f'<row r="{r}">{"".join(cells)}</row>')
    last = f"{col_letter(len(header) - 1)}{len(rows) + 1}"
    cols = "".join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, start=1))
    return (
        f"{XML_HEAD}"
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f"<cols>{cols}</cols><sheetData>{''.join(lines)}</sheetData>"
        f'<autoFilter ref="A1:{last}"/></worksheet>'
    )


def write_xlsx(path, sheets):
    """Minimal xlsx (stdlib only): one worksheet per (name, header, rows), bold frozen header, filters."""
    ns = "http://schemas.openxmlformats.org"
    sheet_refs = "".join(
        f'<sheet name="{xml_text(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, _, _) in enumerate(sheets, 1)
    )
    sheet_rels = "".join(
        f'<Relationship Id="rId{i}" Type="{ns}/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, len(sheets) + 1)
    )
    sheet_types = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, len(sheets) + 1)
    )
    parts = {
        "[Content_Types].xml": (
            f'{XML_HEAD}<Types xmlns="{ns}/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f"{sheet_types}</Types>"
        ),
        "_rels/.rels": (
            f'{XML_HEAD}<Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            f'{XML_HEAD}<workbook xmlns="{ns}/spreadsheetml/2006/main" '
            f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets>{sheet_refs}</sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            f'{XML_HEAD}<Relationships xmlns="{ns}/package/2006/relationships">'
            f'{sheet_rels}<Relationship Id="rId{len(sheets) + 1}" '
            f'Type="{ns}/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
        ),
        "xl/styles.xml": (
            f'{XML_HEAD}<styleSheet xmlns="{ns}/spreadsheetml/2006/main">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
            '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
            '<cellXfs count="2"><xf/><xf fontId="1" applyFont="1"/></cellXfs></styleSheet>'
        ),
    }
    for i, (_, header, rows) in enumerate(sheets, 1):
        parts[f"xl/worksheets/sheet{i}.xml"] = sheet_xml(header, rows)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in parts.items():
            z.writestr(name, content)


# every page of the project, in the order a reader goes through them; each page shows them all as its top menu,
# so the pages link to each other as long as they stay in the same folder
PAGES = [
    ("produse.html", "Faza 1", "Nomenclator produse"),
    ("emailuri.html", "Faza 2", "Emailuri: cerere, clarificări, ofertă"),
    ("reguli.html", "Faza 3", "Reguli de ofertare"),
    ("statii.html", "Faza 4", "Oferte pe tipuri de stații"),
    ("alamo.html", "Faza 4", "Cereri către ALAMO"),
    ("componente.html", "Faza 5", "Componentele stațiilor"),
]
# uses the colours of the page it sits in, with fallbacks for a page that defines none
NAV_STYLE = """<style>
  nav.pages { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 6px; margin: 0 0 10px; font-size: 12px; }
  nav.pages .pages-label { color: var(--muted, #5f6b7a); margin-right: 2px; }
  nav.pages a { display: inline-flex; gap: 5px; align-items: baseline; padding: 3px 9px; border: 1px solid var(--border, #dfe3e8);
    border-radius: 999px; color: var(--text, #1d232b); background: var(--surface, #fff); text-decoration: none; white-space: nowrap; }
  nav.pages a span { color: var(--muted, #5f6b7a); }
  nav.pages a:hover { border-color: var(--accent, #1860d6); }
  nav.pages a[aria-current=page] { border-color: var(--accent, #1860d6); color: var(--accent, #1860d6); font-weight: 600; }
</style>"""


def nav_html(current):
    """The menu with every page of the project; current is the file name of the page it goes in."""
    links = []
    for name, phase, title in PAGES:
        here = ' aria-current="page"' if name == current else ""
        links.append(f'<a href="{name}"{here}><span>{phase}</span>{html.escape(title)}</a>')
    label = '<span class="pages-label">Paginile:</span>'
    return f'{NAV_STYLE}<nav class="pages" aria-label="Paginile proiectului">{label}{"".join(links)}</nav>'


def number(n):
    """4696 -> 4.696 (Romanian thousands separator)."""
    return f"{n:,}".replace(",", ".")


def summary_text(summary):
    return "\n".join(f"{title}: " + ", ".join(f"{label} {number(n)}" for label, n in items) for title, items in summary)


def summary_html(summary):
    blocks = []
    for title, items in summary:
        rows = "".join(f"<dt>{html.escape(label)}</dt><dd>{number(n)}</dd>" for label, n in items)
        blocks.append(f"<section><h2>{html.escape(title)}</h2><dl>{rows}</dl></section>")
    return "".join(blocks)


def category_descriptions(products, path):
    """{category or subcategory name: description} from descrieri_categorii.json, keyed there by code
    ("01", "01-008"), so a renamed category keeps its text. Returns (descriptions, warnings)."""
    by_code = json.loads(path.read_text(encoding="utf-8"))
    names = {p["category"] for p in products} | {p["subcategory"] for p in products if p["subcategory"]}
    descriptions, warnings = {}, []
    for name in sorted(names):
        code = re.match(r"\d{2}(?:-\d{3})?", name)
        text = by_code.get(code.group() if code else name)
        if text:
            descriptions[name] = text
        else:
            warnings.append(f"fără descriere în {path.name}: {name}")
    return descriptions, warnings


def write_page(products, path, summary, headline, descriptions):
    data = json.dumps(products, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / "template.html").read_text(encoding="utf-8")
    # the product data goes in last, so a product name can never be mistaken for one of the other placeholders
    page = (
        page.replace("/*__DESCRIPTIONS__*/{}", json.dumps(descriptions, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__SUMMARY_LINE__", html.escape(headline))
        .replace("__SUMMARY__", summary_html(summary))
        .replace("__NAV__", nav_html(path.name))
        .replace("/*__PRODUCTS__*/[]", data)
    )
    path.write_text(page, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(
        description="Generează pagina cu nomenclatorul de produse (output/produse.html) și raportul cu fișele "
        "tehnice lipsă (output/raport.csv)."
    )
    ap.add_argument("excel", help="exportul de produse din Odoo (.xlsx)")
    ap.add_argument("--drive-folder", default=DEFAULT_DRIVE_FOLDER, help="ID-ul folderului din Drive cu fișele tehnice")
    ap.add_argument(
        "--rules", default=str(HERE / "fise_reguli.json"), help="fișierul cu reguli (implicit fise_reguli.json)"
    )
    ap.add_argument("--out", default=str(HERE / "output"), help="unde se scriu pagina și raportul (implicit output)")
    args = ap.parse_args()

    products, groups, skipped = parse_products(read_xlsx_rows(args.excel))
    files = list_drive_folder(args.drive_folder)
    rules = {r["fisier"]: r for r in json.loads(Path(args.rules).read_text(encoding="utf-8"))}
    report, warnings = build(products, groups, files, rules)
    warnings = skipped + warnings
    descriptions, missing = category_descriptions(products, HERE / "descrieri_categorii.json")
    warnings += missing

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sections = collections.Counter(r["Secțiune"] for r in report)
    statuses = collections.Counter(p["status"] for p in products)
    # printed in the terminal and shown, collapsible, at the top of the page
    summary = [
        (
            "Date citite",
            [("Produse din Excel", len(products)), ("Rânduri gri", len(groups)), ("Fișiere în Drive", len(files))],
        ),
        ("Status fișă", [(s, statuses[s]) for s in (STATUS_WITH, STATUS_TO_CONFIRM, STATUS_WITHOUT)]),
        ("În raport", list(sections.items())),
    ]
    headline = " · ".join(
        [f"{number(len(products))} produse"]
        + [f"{number(statuses[s])} {s}" for s in (STATUS_WITH, STATUS_TO_CONFIRM, STATUS_WITHOUT)]
    )

    written = [out / name for name in ("produse.html", "produse.csv", "produse.xlsx", "raport.csv")]
    write_page(products, written[0], summary, headline, descriptions)
    write_csv(written[1], *product_table(products))
    write_xlsx(written[2], [("Produse", *product_table(products)), ("Raport", *report_table(report))])
    write_csv(written[3], *report_table(report))

    print(summary_text(summary))
    for w in warnings:
        print(f"  ! {w}")
    print(f"Gata. Pagina: {out / 'produse.html'}")
    print(f"      Tabelul: {out / 'produse.xlsx'} (cu raportul în foaia a doua), {out / 'produse.csv'}")
    print(f"      Raportul: {out / 'raport.csv'}")


if __name__ == "__main__":
    main()
