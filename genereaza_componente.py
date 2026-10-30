#!/usr/bin/env python3
"""Builds the Phase 5 page: for every station AKRO sold, what the client asked for, what AKRO offered and what AKRO
ordered from its supplier ALAMO, and from that, what a station is made of.

Usage:
    python3 genereaza_componente.py [--comenzi "Comanda de achizitie_Q3 2026.xlsx"] [--out output]
    python3 genereaza_componente.py --loturi date/loturi_componente   # only writes the sold stations to read
    python3 genereaza_componente.py --verifica componente/lot_01.json   # only checks these files

Inputs:
  - everything genereaza_statii.py reads (date/mesaje.json, output/produse.csv, the Odoo offer list, analiza/,
    statii/, alamo/): the offers, their stations and the ALAMO conversations are rebuilt the same way;
  - the Odoo list of purchase orders (purchase.order export): for every order to ALAMO, the client offer it was
    made for ("Document sursă");
  - componente/lot_*.json: for the stations analysed, the technical requirement, the configuration offered, the
    components ordered with their role and the remarks, each with the message and the exact quote it comes from;
    componente/raspunsuri.json: the written answers to the three questions of the ticket (componente/INSTRUCTIUNI.md).

Output (in --out): componente.html, the sold stations with the three blocks requirement | solution | supplier order
and the emails in date order, the components found and the answers. It links to emailuri.html, statii.html,
alamo.html and to the attachments in output/atasamente (client data and prices - internal only).

Standard library only.
"""

import argparse
import collections
import datetime
import json
import re
import sys
from pathlib import Path

from genereaza import read_xlsx_rows, summary_text
from genereaza_emailuri import LOCAL_TZ, conversation_text, load_nomenclature
from genereaza_reguli import load_glossary, load_records
from genereaza_statii import (
    EMAIL_OFFER,
    NOT_IN_ODOO,
    ODOO_STATE_HELP,
    TYPES_FILE,
    alamo_conversations,
    all_messages,
    check_alamo,
    check_stations,
    doc_entry,
    is_alamo,
    load_entries,
    load_types,
    message_entry,
    offer_units,
    quote_error,
    record_entry,
    sourced,
    thread,
    unit_text,
    write_page,
)

HERE = Path(__file__).resolve().parent
ANSWERS_FILE = "raspunsuri.json"  # in the analysis folder, but not a station entry
SOLD_STATE = "Comandă de vânzare"
CONFIRMATION = "Confirmare de comandă"
# a supplier order this close to a sale (from 30 days before to 60 days after) is a hint when nothing else explains it
WINDOW_BEFORE, WINDOW_AFTER = 30, 60
# the nomenclature groups a softening or filter station is assembled from, and the station kinds (statii/tipuri.json)
# built that way: a pressure vessel with a filter medium and an automatic valve
STATION_GROUPS = ("14-001", "14-002", "14-003", "14-004", "14-005")
ASSEMBLED = {
    "Stație de dedurizare + Ecomix",
    "Filtru de deferizare și demanganizare",
    "Filtru multistrat sau cu nisip",
    "Filtru cu cărbune activ",
    "Filtru pentru eliminarea arsenului",
    "Stație de eliminare a nitraților",
    "Demineralizator",
}
LINKS = {
    "odoo": "legată în Odoo",
    "pdf": "numită în PDF-ul comenzii",
    "faza4": "legată în Faza 4, de confirmat",
    "perioada": "indiciu din perioadă",
}
SURE = ("odoo", "pdf")  # the links that need no confirmation
QUESTIONS = [
    "Ce componente formează o stație de dedurizare?",
    "De ce parametri ai cerinței depinde configurația?",
    "Ce se comandă de la furnizor pentru fiecare stație?",
]

# --- the purchase orders ----------------------------------------------------------------------------------

PO_NUMBER = re.compile(r"Purchase Order # (P0\d{4})")
PO_BODY = re.compile(r"DESCRIPTION EXPECTED (?:DATE QTY|QTY\s+DATE)\s*(.*?)\s*Page: \d+ / \d+", re.S)
# a line ends at its time, followed by the quantity and the unit (one layout) or by the unit alone (the other one,
# where the quantity comes right after the date and the description wraps around it)
PO_ITEM_END = re.compile(r"\d{2}:\d{2}:\d{2}(?:\s+\d{1,3}(?:,\d{3})*\.\d{2})?\s+[A-Za-z]+")
PO_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")
PO_TIME = re.compile(r"\d{2}:\d{2}:\d{2}")
PO_QTY = re.compile(r"(?<!\S)\d{1,3}(?:,\d{3})*\.\d{2}(?!\S)")
PO_REF = re.compile(r"\[(\d{2})-\s*(\d{6})\]")
PO_CODE = re.compile(r"^\[((?:[^\[\]]|\[[^\]]*\])+)\]\s*")
CONFIRMATION_REF = re.compile(r"Customer reference \.+: #?P ?(0\d{4})")  # "#P01565" or "#P 01565"
CONFIRMATION_NUMBER = re.compile(r"Confirmation\.+: (\S+)")
CONFIRMATION_DATE = re.compile(r"Date\.+: (\d{2})/(\d{2})/(\d{4})")
CONFIRMATION_LINE = re.compile(
    r"^(?P<item>\d{11})\s+(?P<name>.*?)\s*(?P<qty>\d+\.\d{2})\s+(?P<uom>[A-Z]+\+?)\s+(?:to be defined|\d{2}/\d{2}/\d{4})"
    r"\s+€(?P<pu>[\d.]+)\s+€(?P<sum>[\d.]+)\s*$"
)
CONFIRMATION_TOTAL = re.compile(r"Total excl\. VAT \.+ € ([\d.]+)")
# the letterhead and the repeated header of a supplier confirmation: never the rest of a product description
CONFIRMATION_NOISE = re.compile(
    r"^(Pro forma confirmation|Confirmation|Sales order|Date\.|Customer reference|VAT|Terms of|Payment|Item number|"
    r"Delivery address|SC AKRO|Str\.|500407|Romania|SINCE|PLEASE|THE |BDO|Total|Alamo Water|ul\. Gen|05-082|Poland|"
    r"0041090|IBAN|SWIFT|Bank details|Email|Telephone)"
)


def excel_date(value):
    """Excel serial date (46244.40) -> "2026-08-10 09:48", the format of the message dates."""
    if not value:
        return ""
    day = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(value))
    return day.strftime("%Y-%m-%d %H:%M")


def load_order_list(path):
    """{P01380: {...}} from the Odoo purchase.order export: supplier, date, the client offer it was made for, total."""
    rows = read_xlsx_rows(path)
    head = {name: i for i, name in enumerate(rows[0])}

    def cell(row, name):
        i = head.get(name)
        return row[i].strip() if i is not None and i < len(row) else ""

    orders = {}
    for row in rows[1:]:
        number = cell(row, "Referință comandă")
        if not number:
            continue
        total = cell(row, "Total")
        orders[number] = {
            "number": number,
            "supplier": cell(row, "Furnizor"),
            "buyer": cell(row, "Cumpărător"),
            "date": excel_date(cell(row, "Termenul limită al comenzii")),
            "source": cell(row, "Document sursă"),
            "partner": cell(row, "Source Partner"),
            "opportunity": cell(row, "Source Opportunity"),
            "total": round(float(total), 2) if total else None,
            "state": cell(row, "Stare"),
        }
    return orders


def parse_purchase_order(text):
    """Number, product lines and remarks of an AKRO purchase order PDF (pdftotext output). The lines are read from
    the whole body as one text, because in some PDFs the description wraps around the date and the quantity."""
    number = PO_NUMBER.search(text)
    body = PO_BODY.search(text)
    if not number or not body:
        return None
    flat = re.sub(r"\s+", " ", body.group(1))
    lines, start = [], 0
    for end in PO_ITEM_END.finditer(flat):
        chunk = flat[start : end.end()].strip()
        start = end.end()
        date = PO_DATE.search(chunk)
        if not date:
            continue
        qty = PO_QTY.search(chunk, date.end())
        rest = chunk[: date.start()] + " " + chunk[date.end() :]
        if qty:
            at = qty.start() - date.end() + date.start() + 1  # the same match, in rest
            rest = rest[:at] + rest[at + len(qty.group()) :]
        rest = re.sub(r"\s+", " ", PO_TIME.sub(" ", rest)).strip()
        uom = rest.rsplit(" ", 1)[-1]
        rest = rest[: -len(uom)].strip()
        ref = PO_REF.search(rest)
        rest = (rest[: ref.start()] + " " + rest[ref.end() :]).strip() if ref else rest
        code = PO_CODE.match(rest)
        lines.append(
            {
                "code": code.group(1).strip() if code else "",
                "name": re.sub(r"\s+", " ", rest[code.end() :] if code else rest).strip(),
                "ref": f"{ref.group(1)}-{ref.group(2)}" if ref else "",
                "qty": float(qty.group().replace(",", "")) if qty else None,
                "uom": uom,
            }
        )
    note = flat[start:].split("Str. Zizinului Nr. 110;")[0].strip()  # AKRO's footer is not a remark
    return {"number": number.group(1), "lines": lines, "notes": [note] if note else []}


def parse_confirmation(text):
    """Supplier order confirmation (ALAMO "Pro forma confirmation" or "Confirmation"): the AKRO order it answers,
    its number, date, lines with prices in EUR and total."""
    ref = CONFIRMATION_REF.search(text)
    if not ref or "Item number" not in text:
        return None
    raw = [line.strip() for line in text.split("\n")]
    lines = []
    for i, line in enumerate(raw):
        m = CONFIRMATION_LINE.match(line)
        if not m:
            continue
        name = m.group("name")
        code = re.match(r"\(([^)]+)\)\s*", name)
        follow = raw[i + 1] if i + 1 < len(raw) else ""
        # the description of a coded item ("(V3186EU-06)") is on the next line
        if follow and not CONFIRMATION_LINE.match(follow) and not CONFIRMATION_NOISE.match(follow):
            name = f"{name} {follow}"
        lines.append(
            {
                "code": code.group(1) if code else "",
                "item": m.group("item"),
                "name": re.sub(r"\s+", " ", name[code.end() :] if code else name).strip(),
                "qty": float(m.group("qty")),
                "uom": m.group("uom"),
                "price": float(m.group("pu")),
                "amount": float(m.group("sum")),
            }
        )
    number = CONFIRMATION_NUMBER.search(text)
    date = CONFIRMATION_DATE.search(text)
    total = CONFIRMATION_TOTAL.search(text)
    return {
        "order": "P" + ref.group(1),
        "number": number.group(1) if number else "",
        "date": f"{date.group(3)}-{date.group(2)}-{date.group(1)}" if date else "",
        "lines": lines,
        "total": float(total.group(1)) if total else None,
    }


def order_documents(convs, listed, nomenclature):
    """{P01380: [documents]}: the AKRO purchase orders sent to ALAMO and ALAMO's confirmations of them, in date
    order. An order sent twice (Sent Items and a copy) counts once; a changed order is a new version."""
    _, by_ref, _, _ = nomenclature
    docs, seen = collections.defaultdict(list), set()
    for m, conv in sorted(all_messages(convs).values(), key=lambda mc: mc[0]["local_date"]):
        to_alamo = m["is_akro"] and any(is_alamo(r["email"]) for r in m["recipients"])
        for a in m["attachments"]:
            text = a.get("text") or ""
            if m["is_akro"] and "Purchase Order #" in text:
                parsed = parse_purchase_order(text)
                if not parsed or not (to_alamo or parsed["number"] in listed):
                    continue
                kind, order_no, doc_no = "Comandă AKRO", parsed["number"], parsed["number"]
            elif is_alamo(m["from_email"]) and "Customer reference" in text:
                parsed = parse_confirmation(text)
                if not parsed:
                    continue
                kind, order_no, doc_no = "Confirmare ALAMO", parsed["order"], parsed["number"]
            else:
                continue
            key = (kind, doc_no, squash_lines(parsed["lines"]))
            if key in seen:
                continue
            seen.add(key)
            for line in parsed["lines"]:
                product = by_ref.get(line.get("ref") or "")
                line["product"] = product["Nume"] if product else ""
                line["group"] = product["Subcategorie"] if product else ""
            docs[order_no].append(
                {
                    "kind": kind,
                    "number": doc_no,
                    "sent": m["local_date"],
                    "message": m["id"],
                    "conv": conv["id"],
                    "nr": conv["nr"],
                    "file": a["name"],
                    "path": a.get("path") or "",
                    "lines": parsed["lines"],
                    "notes": parsed.get("notes", []),
                    "total": parsed.get("total"),
                }
            )
    return docs


def squash_lines(lines):
    return tuple((line.get("code"), line.get("ref"), line["qty"]) for line in lines)


def supplier_orders(order_list, docs):
    """Every order to ALAMO: the ones in the Odoo list and the ones only found in the emails (after the quarter of
    the list). The lines are those of the last AKRO version sent."""
    orders = {}
    for number in sorted(set(order_list) | set(docs)):
        row = order_list.get(number, {})
        own = docs.get(number, [])
        akro = [d for d in own if d["kind"] == "Comandă AKRO"]
        first = own[0]["sent"] if own else ""
        orders[number] = {
            "number": number,
            "inList": number in order_list,
            "supplier": row.get("supplier") or "ALAMO WATER POLAND",
            "buyer": row.get("buyer", ""),
            "date": row.get("date") or first,
            "source": row.get("source", ""),
            "partner": row.get("partner", ""),
            "opportunity": row.get("opportunity", ""),
            "total": row.get("total"),
            "state": row.get("state", ""),
            "docs": own,
            "lines": akro[-1]["lines"] if akro else [],
            "notes": akro[-1]["notes"] if akro else [],
        }
    return orders


# --- the sold stations ------------------------------------------------------------------------------------


def sold_stations(units, station_entries, orders):
    """The offers with at least one station that the client bought: an order in Odoo, an order confirmation sent,
    or a supplier order made for them."""
    by_key = {e["oferta"]: e for e in station_entries}
    sources = {o["source"] for o in orders.values()}
    out = []
    for unit in units:
        stations = [s for s in by_key.get(unit["key"], {}).get("statii") or [] if not s.get("_error")]
        if not stations:
            continue
        state = unit["odoo"]["state"] if unit["odoo"] else NOT_IN_ODOO
        confirmed = [o for o in unit["docs"] if o["kind"] == CONFIRMATION]
        if state == SOLD_STATE or confirmed or unit["key"] in sources:
            # the day of the sale: the first order confirmation sent, else the first offer
            unit["sold"] = confirmed[0]["sent"] if confirmed else unit["date"]
            out.append((unit, stations))
    return out


def day(text):
    return datetime.date.fromisoformat(text[:10])


def phase4_orders(alamo_entries, alamo_convs, orders):
    """{client offer: ([ALAMO conversations], [orders])} from the Phase 4 links that kept their evidence: the orders
    whose documents are in a linked ALAMO conversation."""
    out = collections.defaultdict(lambda: ([], []))
    for e in alamo_entries:
        conv = alamo_convs.get(e["conv"])
        if not conv:
            continue
        for link in e.get("legaturi") or []:
            if link.get("_error"):
                continue
            convs, numbers = out[link["oferta"]]
            convs.append({"conv": conv["id"], "nr": conv["nr"], "subject": conv["subject"]})
            numbers += [o["number"] for o in orders.values() if any(d["conv"] == conv["id"] for d in o["docs"])]
    return out


def order_links(unit, kinds, orders, phase4):
    """The supplier orders of a sale, from the surest to the weakest: the Odoo source document; the client offer named
    under the lines of the order PDF; the Phase 4 link (an ALAMO conversation with evidence); for a station assembled from parts, the orders of the same period that no
    other sale explains (no Odoo source document of another sale, no Phase 4 link to another sale)."""
    links = [{"order": o["number"], "how": "odoo"} for o in orders.values() if o["source"] == unit["key"]]
    # an order whose PDF names the client offer (the remark under its lines) is as sure as the Odoo link
    links += [
        {"order": o["number"], "how": "pdf"}
        for o in orders.values()
        if o["number"] not in [x["order"] for x in links] and any(unit["key"] in n for n in o["notes"])
    ]
    convs, numbers = phase4.get(unit["key"], ([], []))
    links += [{"order": n, "how": "faza4"} for n in dict.fromkeys(numbers) if n not in [x["order"] for x in links]]
    if not kinds & ASSEMBLED:
        return links, convs
    elsewhere = {n for key, (_, ns) in phase4.items() if key != unit["key"] for n in ns}
    sold = day(unit["sold"])
    for o in sorted(orders.values(), key=lambda o: o["date"]):
        if o["number"] in [x["order"] for x in links] or o["number"] in elsewhere or not o["date"]:
            continue
        distance = (day(o["date"]) - sold).days
        other_sale = o["source"].startswith("S0") and o["source"] != unit["key"]
        station_parts = not o["lines"] or any(line["ref"].startswith(STATION_GROUPS) for line in o["lines"])
        if -WINDOW_BEFORE <= distance <= WINDOW_AFTER and not other_sale and station_parts:
            links.append({"order": o["number"], "how": "perioada", "days": distance})
    return links, convs


def chain_gaps(unit, links, orders, entry):
    """What is missing from the chain requirement -> offer -> supplier order, said, never guessed. The requirement
    comes from the email analysis (Phase 2) or, for a station analysed here, from its checked requirement items."""
    gaps = []
    requirement = [i for i in (entry or {}).get("cerinta") or [] if not i.get("_error")]
    if not any(r["request"] for r in unit["recs"]) and not requirement:
        gaps.append("cerința clientului nu apare în emailuri")
    if not unit["docs"]:
        gaps.append("oferta nu are PDF Odoo în emailuri")
    sure = [x for x in links if x["how"] in SURE]
    if not sure:
        gaps.append(
            "nicio comandă către furnizor nu e legată sigur (în Odoo sau în PDF-ul comenzii) de această vânzare"
        )
    elif not any(orders[x["order"]]["lines"] for x in sure):
        gaps.append("comanda legată sigur nu e în emailuri, deci nu i se cunosc liniile")
    return gaps


def chain_state(links, gaps):
    if not gaps:
        return "complet"
    if any(x["how"] != "perioada" for x in links):
        return "parțial"
    return "fără comandă"


CHAIN_HELP = {
    "complet": "Se văd în emailuri cerința clientului, oferta AKRO și comanda către furnizor legată sigur (în Odoo sau "
    "în PDF-ul comenzii), cu liniile ei.",
    "parțial": "Există o comandă către furnizor legată de vânzare, dar lipsește o parte a lanțului (vezi ce lipsește).",
    "fără comandă": "Nicio comandă către furnizor nu e legată de vânzare; pot exista doar indicii din aceeași perioadă.",
}


# --- analysis checks --------------------------------------------------------------------------------------


def check_entries(entries, sales, orders, convs, nomenclature):
    """Errors in componente/lot_*.json. A requirement or a solution item must quote the client's emails of the sale;
    a component must be on a supplier order linked to the sale and quote its PDF; a remark may quote any email."""
    _, by_ref, _, _ = nomenclature
    everywhere = {mid: m for mid, (m, _) in all_messages(convs).items()}
    by_key = {s["key"]: s for s in sales}
    errors, seen = [], set()
    for e in entries:
        key = e.get("oferta")
        label = f"{e['_file']} {key}"
        sale = by_key.get(key)
        if not sale:
            errors.append(f"{label}: nu e o stație vândută")
            continue
        if key in seen:
            errors.append(f"{label}: oferta apare de două ori")
        seen.add(key)
        if not isinstance(e.get("statii"), int) or e["statii"] < 1:
            errors.append(f"{label}: «statii» trebuie să fie numărul de stații vândute (cel puțin 1)")
        client = {mid: everywhere[mid] for mid in sale["thread"] if mid in everywhere}
        linked = {x["order"] for x in sale["links"]}
        for number in e.get("comenzi") or []:
            if number not in linked:
                errors.append(f"{label}: comanda {number} nu e legată de această vânzare (nici măcar ca indiciu)")
        own = [n for n in e.get("comenzi") or [] if n in linked]
        order_msgs = {d["message"]: everywhere[d["message"]] for n in own for d in orders[n]["docs"]}
        refs = {line["ref"] for n in own for line in orders[n]["lines"] if line["ref"]}
        items = [(f"{k}[{i}]", item, client) for k in ("cerinta", "solutie") for i, item in enumerate(e.get(k) or [])]
        items += [(f"observatii[{i}]", item, everywhere) for i, item in enumerate(e.get("observatii") or [])]
        items += [(f"componente[{i}]", item, order_msgs) for i, item in enumerate(e.get("componente") or [])]
        for name, item, allowed in items:
            item["_error"] = quote_error(item, allowed, f"{label} {name}")
            if name.startswith("componente") and not item["_error"]:
                if item.get("ref") not in by_ref:
                    item["_error"] = f"{label} {name}: codul {item.get('ref')!r} nu e în nomenclator"
                elif item["ref"] not in refs:
                    item["_error"] = f"{label} {name}: codul {item['ref']} nu e pe comenzile din «comenzi»"
                elif not item.get("rol"):
                    item["_error"] = f"{label} {name}: lipsește «rol»"
            if item["_error"]:
                errors.append(item["_error"])
    return errors


def check_answers(answers, convs):
    everywhere = {mid: m for mid, (m, _) in all_messages(convs).items()}
    errors = []
    for i, a in enumerate(answers):
        label = f"{ANSWERS_FILE}[{i}]"
        if a.get("intrebare") not in QUESTIONS:
            errors.append(f"{label}: întrebarea trebuie să fie una din {QUESTIONS}")
        for j, ev in enumerate(a.get("dovezi") or []):
            ev["_error"] = quote_error(ev, everywhere, f"{label} dovezi[{j}]")
            if ev["_error"]:
                errors.append(ev["_error"])
    return errors


# --- batches for the analysis -----------------------------------------------------------------------------


def order_text(order, how):
    head = (
        f"COMANDA {order['number']} ({LINKS[how]}) | {order['supplier']} | {order['date']} | sursa în Odoo: "
        f"{order['source'] or '-'} | stare: {order['state'] or 'nu e în lista Odoo'} | total: {order['total']}"
    )
    parts = [head]
    for d in order["docs"]:
        parts.append(f"  {d['kind']} {d['number']} trimisă {d['sent']} în {d['message']} (conversația {d['nr']}):")
        for line in d["lines"]:
            price = f" | {line['price']} EUR" if line.get("price") is not None else ""
            parts.append(
                f"    [{line.get('ref') or '-'}] [{line.get('code') or '-'}] {line['name']} | {line['qty']} "
                f"{line['uom']}{price} | {line.get('group') or ''}"
            )
        parts += [f"    notă: {n}" for n in d["notes"]]
    if not order["docs"]:
        parts.append("  (nu e în emailuri: doar rândul din lista Odoo)")
    return "\n".join(parts)


def write_batches(sales, orders, convs, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.txt"):
        old.unlink()
    written = []
    for sale in sales:
        unit = sale["unit"]
        text = [unit_text(unit, convs), f"VÂNDUTĂ {unit['sold']} | lanț: {sale['chain']} | lipsește: {sale['gaps']}"]
        text += [order_text(orders[x["order"]], x["how"]) for x in sale["links"]]
        seen = set()
        for cid in sale["convs"]:
            if cid not in seen:
                seen.add(cid)
                text.append(conversation_text(convs[cid]))
        path = folder / f"componente_{unit['key']}.txt"
        path.write_text("\n".join(text), encoding="utf-8")
        written.append((path.name, len(sale["links"])))
    return written


# --- page -------------------------------------------------------------------------------------------------


def order_entry(order):
    return {k: order[k] for k in ("number", "inList", "date", "source", "partner", "total", "state")} | {
        "docs": [
            {
                k: d[k]
                for k in (
                    "kind",
                    "number",
                    "sent",
                    "message",
                    "conv",
                    "nr",
                    "file",
                    "path",
                    "lines",
                    "notes",
                    "total",
                )
            }
            for d in order["docs"]
        ],
        "lines": order["lines"],
        "notes": order["notes"],
    }


def analysed_items(items, msgs, extra=()):
    out = []
    for item in items or []:
        s = sourced(item, msgs)
        if s:
            out.append(s | {k: item.get(k) for k in extra})
    return out


def page_data(sales, orders, entries, answers, convs, nomenclature):
    _, by_ref, _, _ = nomenclature
    everywhere = {mid: m for mid, (m, _) in all_messages(convs).items()}
    by_key = {e["oferta"]: e for e in entries}
    messages, rows = {}, []
    for sale in sales:
        unit = sale["unit"]
        entry = by_key.get(unit["key"], {})
        for mid in sale["thread"]:
            messages[mid] = message_entry(everywhere[mid])
        docs = [o for o in unit["docs"] if not o["resent"]]
        rows.append(
            {
                "key": unit["key"],
                "number": "" if unit["key"].startswith(EMAIL_OFFER) else unit["key"],
                "client": unit["client"],
                "date": unit["date"],
                "sold": unit["sold"],
                "total": unit["total"],
                "currency": unit["currency"],
                "status": unit["odoo"]["state"] if unit["odoo"] else NOT_IN_ODOO,
                "stations": [sourced(s, everywhere) | {"type": s["tip"]} for s in sale["stations"]],
                "records": [record_entry(r) for r in unit["recs"]],
                "docs": [doc_entry(o) for o in docs],
                "convs": [{"id": c, "nr": convs[c]["nr"], "subject": convs[c]["subject"]} for c in unit["convs"]],
                "links": sale["links"],
                "phase4": sale["phase4"],
                "chain": sale["chain"],
                "gaps": sale["gaps"],
                "thread": sale["thread"],
                "analysed": bool(entry),
                "count": entry.get("statii") or 0,
                "requirement": analysed_items(entry.get("cerinta"), everywhere, ("camp",)),
                "solution": analysed_items(entry.get("solutie"), everywhere, ("camp",)),
                "components": analysed_items(
                    entry.get("componente"), everywhere, ("ref", "rol", "cantitate", "unitate")
                ),
                "remarks": analysed_items(entry.get("observatii"), everywhere),
            }
        )
    # the components of every analysed station: in how many stations each code was ordered, with its roles
    table = {}
    for row in rows:
        for c in row["components"]:
            product = by_ref.get(c["ref"], {})
            t = table.setdefault(
                c["ref"],
                {
                    "ref": c["ref"],
                    "name": product.get("Nume", ""),
                    "group": product.get("Subcategorie", ""),
                    "roles": [],
                    "stations": 0,
                    "sales": [],
                    "per": [],
                },
            )
            if c["rol"] not in t["roles"]:
                t["roles"].append(c["rol"])
            if row["key"] not in t["sales"]:
                t["sales"].append(row["key"])
                t["stations"] += row["count"]
            t["per"].append({"key": row["key"], "qty": c.get("cantitate"), "uom": c.get("unitate") or ""})
    components = sorted(table.values(), key=lambda t: (t["group"], -t["stations"], t["ref"]))
    answer_rows = []
    for a in answers:
        evidence = []
        for ev in a.get("dovezi") or []:
            if ev.get("_error"):
                continue
            m = everywhere[ev["src"]]
            messages[ev["src"]] = message_entry(m)
            evidence.append(
                {
                    "src": ev["src"],
                    "quote": ev["citat"],
                    "note": ev.get("nota") or "",
                    "date": m["local_date"],
                }
            )
        answer_rows.append({"question": a["intrebare"], "answer": a.get("raspuns") or [], "evidence": evidence})
    for o in orders.values():
        for d in o["docs"]:
            messages[d["message"]] = message_entry(everywhere[d["message"]])
    return rows, components, answer_rows, messages


def sale_thread(unit, links, phase4, orders, convs):
    """The emails of a sale in date order: the client conversations, then the ALAMO conversations of its surely
    linked orders (Odoo, order PDF or Phase 4), so the whole path from the request to the supplier order reads in one go."""
    ids = list(dict.fromkeys(unit["convs"]))
    for x in links:
        if x["how"] != "perioada":
            ids += [d["conv"] for d in orders[x["order"]]["docs"]]
    ids += [p["conv"] for p in phase4]
    return [m["id"] for m in thread([convs[cid] for cid in dict.fromkeys(ids)])], list(dict.fromkeys(ids))


def build_sales(units, station_entries, orders, alamo_entries, alamo_convs, convs):
    sales = []
    phase4 = phase4_orders(alamo_entries, alamo_convs, orders)
    for unit, stations in sold_stations(units, station_entries, orders):
        links, phase4_convs = order_links(unit, {s["tip"] for s in stations}, orders, phase4)
        gaps = chain_gaps(unit, links, orders, None)
        ids, conv_ids = sale_thread(unit, links, phase4_convs, orders, convs)
        sales.append(
            {
                "unit": unit,
                "key": unit["key"],
                "stations": stations,
                "links": links,
                "phase4": phase4_convs,
                "gaps": gaps,
                "chain": chain_state(links, gaps),
                "thread": ids,
                "convs": conv_ids,
            }
        )
    return sales


def build_outputs(sales, orders, entries, answers, convs, nomenclature, args, problems):
    rows, components, answer_rows, messages = page_data(sales, orders, entries, answers, convs, nomenclature)
    glossary = load_glossary(args.glosar) if Path(args.glosar).exists() else []
    generated = datetime.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")
    chains = collections.Counter(r["chain"] for r in rows)
    listed = [o for o in orders.values() if o["inList"]]
    with_lines = [o for o in orders.values() if o["lines"]]
    reading = {
        "akro": sum(d["kind"] == "Comandă AKRO" for o in orders.values() for d in o["docs"]),
        "alamo": sum(d["kind"] == "Confirmare ALAMO" for o in orders.values() for d in o["docs"]),
        "akroLines": sum(len(o["lines"]) for o in with_lines),
        "akroRefs": sum(bool(line["ref"]) for o in with_lines for line in o["lines"]),
        "listed": len(listed),
        "listedInEmails": sum(bool(o["docs"]) for o in listed),
        "onlyEmails": [o["number"] for o in orders.values() if not o["inList"]],
        "missing": [o["number"] for o in listed if not o["docs"]],
    }
    summary = [
        (
            "Stații vândute",
            [("Vânzări cu cel puțin o stație", len(rows))]
            + [(f"Lanț {c}", chains[c]) for c in CHAIN_HELP if chains[c]]
            + [("Analizate (cu componente)", sum(r["analysed"] for r in rows))],
        ),
        (
            "Comenzi către ALAMO",
            [
                ("În lista Odoo (trimestrul 3)", reading["listed"]),
                ("Din ele, găsite în emailuri", reading["listedInEmails"]),
                ("Doar în emailuri (după trimestru)", len(reading["onlyEmails"])),
                ("Cu liniile citite din PDF", len(with_lines)),
            ],
        ),
        ("Componente", [("Coduri diferite în stațiile analizate", len(components))]),
    ]
    headline = (
        f"{len(rows)} vânzări cu stații · {chains['complet']} cu lanțul complet · "
        f"{sum(r['analysed'] for r in rows)} analizate · {len(components)} componente"
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_page(
        "template_componente.html",
        {
            "generated": generated,
            "sales": rows,
            "orders": [order_entry(o) for o in sorted(orders.values(), key=lambda o: o["date"])],
            "components": components,
            "answers": answer_rows,
            "questions": QUESTIONS,
            "messages": messages,
            "links": LINKS,
            "chainHelp": CHAIN_HELP,
            "stateHelp": ODOO_STATE_HELP,
            "notInOdoo": NOT_IN_ODOO,
            "reading": reading,
            "window": [WINDOW_BEFORE, WINDOW_AFTER],
            "glossary": glossary,
        },
        out / "componente.html",
        summary,
        headline,
    )
    print(summary_text(summary))
    if problems:
        print(f"  ! {len(problems)} probleme (ce nu se verifică nu apare în pagină):")
        for p in problems:
            print(f"    {p}")
    print(f"Gata. Pagina: {out / 'componente.html'}")
    if not (out / "emailuri.html").exists():
        print(f"  ! {out / 'emailuri.html'} lipsește: linkurile spre conversații merg după genereaza_emailuri.py")


# --- main -------------------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description="Generează pagina din Faza 5: stațiile vândute, cu cerința, soluția și comanda către furnizor, "
        "și componentele lor (output/componente.html)."
    )
    ap.add_argument("--mesaje", default=str(HERE / "date" / "mesaje.json"), help="mesajele scrise de extrage_pst.py")
    ap.add_argument("--oferte", default=str(HERE / "Oferte Alex_Q3 2026.xlsx"), help="lista de oferte din Odoo (.xlsx)")
    ap.add_argument(
        "--comenzi",
        default=str(HERE / "Comanda de achizitie_Q3 2026.xlsx"),
        help="lista comenzilor de achiziție din Odoo (.xlsx)",
    )
    ap.add_argument(
        "--nomenclator", default=str(HERE / "output" / "produse.csv"), help="nomenclatorul din genereaza.py"
    )
    ap.add_argument("--analiza", default=str(HERE / "analiza"), help="folderul cu analiza conversațiilor (*.json)")
    ap.add_argument("--statii", default=str(HERE / "statii"), help="folderul cu analiza stațiilor (*.json)")
    ap.add_argument("--alamo", default=str(HERE / "alamo"), help="folderul cu analiza conversațiilor ALAMO (*.json)")
    ap.add_argument("--componente", default=str(HERE / "componente"), help="folderul cu analiza componentelor (*.json)")
    ap.add_argument(
        "--glosar", default=str(HERE / "reguli" / "glosar.json"), help="explicațiile termenilor (glosarul din Faza 3)"
    )
    ap.add_argument("--out", default=str(HERE / "output"), help="unde se scrie pagina (implicit output)")
    ap.add_argument("--loturi", help="doar scrie stațiile vândute de citit, câte una pe fișier, în acest folder")
    ap.add_argument("--verifica", nargs="+", help="doar verifică aceste fișiere de analiză (componente/)")
    args = ap.parse_args()

    # the inputs come from other steps: say which one to run instead of failing with a traceback
    needed = [
        (args.mesaje, "rulează extrage_pst.py (vezi README, «Faza 2»)"),
        (args.nomenclator, 'rulează întâi genereaza.py "Produs (product.template).xlsx" (Task 1)'),
        (args.oferte, "copiază aici lista de oferte din Odoo sau dă calea cu --oferte"),
        (args.comenzi, "copiază aici lista comenzilor de achiziție din Odoo sau dă calea cu --comenzi"),
    ]
    missing_inputs = [(path, fix) for path, fix in needed if not Path(path).exists()]
    for path, fix in missing_inputs:
        print(f"Lipsește {path}: {fix}.", file=sys.stderr)
    if missing_inputs:
        sys.exit(1)

    nomenclature = load_nomenclature(args.nomenclator)
    convs, records = load_records(args, nomenclature)
    units = offer_units(convs, records)
    order_list = load_order_list(args.comenzi)
    orders = supplier_orders(order_list, order_documents(convs, set(order_list), nomenclature))

    station_entries = load_entries(sorted(p for p in Path(args.statii).glob("*.json") if p.name != TYPES_FILE))
    check_stations(station_entries, units, convs, load_types(args.statii))  # drops the stations whose quote fails
    alamo_entries = load_entries(sorted(Path(args.alamo).glob("*.json")))
    alamo_list = alamo_conversations(convs)
    check_alamo(alamo_entries, alamo_list, convs, units)  # drops the links whose evidence fails
    sales = build_sales(units, station_entries, orders, alamo_entries, {c["id"]: c for c in alamo_list}, convs)

    if args.loturi:
        for name, n in write_batches(sales, orders, convs, args.loturi):
            print(f"  {name}: {n} comenzi")
        print(f"{len(sales)} stații vândute, în {args.loturi}")
        return

    folder = Path(args.componente)
    paths = args.verifica or sorted(p for p in folder.glob("*.json") if p.name != ANSWERS_FILE)
    entries = load_entries([p for p in paths if Path(p).name != ANSWERS_FILE])
    errors = check_entries(entries, sales, orders, convs, nomenclature)
    # a station analysed here may have its requirement in its checked items even when Phase 2 found none
    by_key = {e["oferta"]: e for e in entries}
    for sale in sales:
        sale["gaps"] = chain_gaps(sale["unit"], sale["links"], orders, by_key.get(sale["key"]))
        sale["chain"] = chain_state(sale["links"], sale["gaps"])
    answers_path = folder / ANSWERS_FILE
    answers = json.loads(answers_path.read_text(encoding="utf-8")) if answers_path.exists() else []
    if args.verifica:
        if any(Path(p).name == ANSWERS_FILE for p in args.verifica):
            errors += check_answers(answers, convs)
        print(f"{len(entries)} stații verificate")
        print(f"{len(errors)} erori")
        for e in errors:
            print(f"  ! {e}")
        sys.exit(1 if errors else 0)
    errors += check_answers(answers, convs)
    build_outputs(sales, orders, entries, answers, convs, nomenclature, args, errors)


if __name__ == "__main__":
    main()
