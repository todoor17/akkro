#!/usr/bin/env python3
"""Builds the Phase 4 pages: the offers AKRO sent, grouped by the kind of station they offer, and the requests
AKRO sent to its supplier ALAMO, each with its whole email thread.

Usage:
    python3 genereaza_statii.py [--statii statii] [--alamo alamo] [--out output]
    python3 genereaza_statii.py --loturi date/loturi_statii   # only writes the offers and ALAMO threads to read
    python3 genereaza_statii.py --verifica statii/lot_01.json alamo/lot_01.json   # only checks these files

Inputs:
  - everything genereaza_emailuri.py reads (date/mesaje.json, output/produse.csv, the Odoo offer list,
    analiza/*.json): the conversations, their requests and offers are rebuilt the same way;
  - statii/*.json: for every offer sent, the stations it offers and their kind, each with the message and the exact
    quote it comes from; statii/tipuri.json: the kinds found, with a plain definition (statii/INSTRUCTIUNI.md);
  - alamo/*.json: for every conversation with ALAMO, what it is (offer request, order, delivery...), what AKRO asks
    for and the client offers it serves, each with an exact quote (alamo/INSTRUCTIUNI.md).

Outputs (in --out):
  - statii.html: offer types, the offers of a type, the open offer with its four blocks and its whole thread;
  - alamo.html: the conversations with ALAMO in date order, each with its thread and the client offers linked to it;
  Both open with a double click and link to each other, to emailuri.html and to the attachments in output/atasamente
  (client data - internal only).

Standard library only.
"""

import argparse
import collections
import datetime
import html
import json
import sys
from pathlib import Path

from genereaza import nav_html, number, summary_html, summary_text
from genereaza_emailuri import (
    LOCAL_TZ,
    ODOO_REF,
    attachment_note,
    company,
    conversation_text,
    domain,
    load_nomenclature,
    squash,
)
from genereaza_reguli import load_glossary, load_records, offer_details, record_text

HERE = Path(__file__).resolve().parent
ALAMO_DOMAINS = {"alamowaterpoland.com"}
TYPES_FILE = "tipuri.json"  # in the stations folder, but not an analysis file
EMAIL_OFFER = "email-"  # key prefix of an offer written in the email body, without an Odoo PDF
NO_STATION = "Fără stație"  # offers of parts, consumables or services only
ODOO_STATES = ["Ofertă trimisă", "Comandă de vânzare", "Anulat", "Ofertă"]
NOT_IN_ODOO = "nu e în lista Odoo"
UNKNOWN_CLIENT = "client neidentificat"
ALAMO_LABELS = ["cerere de ofertă", "comandă", "confirmare de comandă", "livrare", "factură", "altele"]
RFQ = ALAMO_LABELS[0]
LINK_WINDOW_DAYS = 60  # a client offer this close to an ALAMO message is a candidate when they share a product code
BATCH_SIZE = 40
ALAMO_ATTACHMENT_LIMIT = 3000  # characters of each AKRO attachment (purchase orders) given to the analysis


def is_alamo(address):
    return domain(address or "") in ALAMO_DOMAINS


# --- offers sent to clients -------------------------------------------------------------------------------


def offer_units(convs, records):
    """One unit per offer sent to a client: an Odoo document number with all its versions, order confirmations and
    proformas, or, without a PDF, the price written in the email of one request. Each unit keeps the requests and
    conversations it answers."""
    units = {}
    for rec in records:
        conv = convs[rec["conv"]]
        if conv["type"] != "client" or not rec["has_offer"]:
            continue
        keys = list(dict.fromkeys(n.split("-")[0] for n in rec["offers"])) or [EMAIL_OFFER + rec["rid"]]
        for key in keys:
            unit = units.setdefault(key, {"key": key, "recs": [], "convs": []})
            unit["recs"].append(rec)
            if conv["id"] not in unit["convs"]:
                unit["convs"].append(conv["id"])
    for unit in units.values():
        docs = [o for cid in unit["convs"] for o in convs[cid]["offers"] if o["number"].split("-")[0] == unit["key"]]
        unit["docs"] = sorted(docs, key=lambda o: o["sent"])
        first = convs[unit["convs"][0]]
        odoo = next((o["odoo"] for o in unit["docs"] if o["odoo"]), None)
        unit["odoo"] = odoo
        # as in emailuri.html: a conversation whose client the emails do not name stays "client neidentificat"
        unit["client"] = (company(odoo["client"]) if odoo else first["client_name"]) or UNKNOWN_CLIENT
        texts = [t for r in unit["recs"] for t in r["offer_text"]]
        unit["date"] = unit["docs"][0]["sent"] if unit["docs"] else min(t["date"] for t in texts)
        # the value is the last offer sent (a later version replaces the earlier one); a confirmation or a
        # proforma only when no offer PDF is in the emails
        priced = [o for o in unit["docs"] if o["total"] is not None and not o["resent"]]
        last = ([o for o in priced if o["kind"] == "Ofertă"] or priced or [None])[-1]
        unit["total"], unit["currency"] = (last["total"], last["currency"]) if last else (None, "")
    return sorted(units.values(), key=lambda u: u["date"])


def unit_text(unit, convs):
    """What the analysis reads for one offer: the request(s) from the email analysis, the offer lines with prices."""
    odoo = unit["odoo"]["state"] if unit["odoo"] else NOT_IN_ODOO
    nrs = ", ".join(str(convs[cid]["nr"]) for cid in unit["convs"])
    head = (
        f"\n{'#' * 100}\nOFERTA {unit['key']} | client: {unit['client']} | trimisă: {unit['date']} | Odoo: {odoo}"
        f" | conversații: {', '.join(unit['convs'])} (nr. {nrs})"
    )
    parts = [head]
    for rec in unit["recs"]:
        parts.append(record_text(rec))
    for cid in unit["convs"]:
        numbers = [o["number"] for o in convs[cid]["offers"] if o["number"].split("-")[0] == unit["key"]]
        if numbers:
            parts.append(offer_details(convs[cid], numbers))
    return "\n".join(parts)


# --- ALAMO ------------------------------------------------------------------------------------------------


def alamo_conversations(convs):
    """Conversations in which AKRO writes to an ALAMO address (the list of the ALAMO page), in date order."""
    return [
        c
        for c in convs.values()
        if any(m["is_akro"] and any(is_alamo(r["email"]) for r in m["recipients"]) for m in c["messages"])
    ]


def akro_codes(conv):
    """AKRO internal codes ([14-001038]) in the documents AKRO sends in a conversation: its purchase orders."""
    found = collections.defaultdict(set)
    for m in conv["messages"]:
        if m["is_akro"]:
            for a in m["attachments"]:
                for ref in ODOO_REF.findall(a.get("text") or ""):
                    found[ref].add(m["id"])
    return found


def line_ref(line):
    return line["ref"] or (line["product"] or {}).get("ref")


def link_candidates(conv, units):
    """Client offers sharing an AKRO product code with what AKRO orders from ALAMO here, sent within
    LINK_WINDOW_DAYS of it: only hints for the analysis, a link is shown only with its own evidence."""
    codes = akro_codes(conv)
    if not codes:
        return []
    when = datetime.date.fromisoformat(conv["messages"][0]["local_date"][:10])
    out = []
    for unit in units:
        sent = datetime.date.fromisoformat(unit["date"][:10])
        if abs((sent - when).days) > LINK_WINDOW_DAYS:
            continue
        shared = sorted({line_ref(line) for o in unit["docs"] for line in o["lines"]} & set(codes))
        if shared:
            out.append((unit, shared))
    return out


def alamo_text(conv, units):
    """The conversation as in the email analysis batches, plus the text of the documents AKRO attaches (its purchase
    orders and offer requests) and the candidate client offers."""
    out = [conversation_text(conv)]
    for m in conv["messages"]:
        if not m["is_akro"]:
            continue
        for a in m["attachments"]:
            if a.get("text") and not a["inline"]:
                text = a["text"][:ALAMO_ATTACHMENT_LIMIT]
                out.append(f"[TEXTUL ATAȘAMENTULUI TRIMIS DE AKRO în {m['id']}: {a['name']}]\n{text}")
    candidates = link_candidates(conv, units)
    if candidates:
        out.append("CANDIDAȚI (oferte către clienți cu același cod de produs, trimise la cel mult 60 de zile):")
        out += [f"  {u['key']} | {u['client']} | {u['date']} | coduri comune: {', '.join(s)}" for u, s in candidates]
    return "\n".join(out)


def client_offer_index(units, convs):
    """Every offer sent to a client, with its lines: what an ALAMO request is compared with."""
    out = ["OFERTELE TRIMISE CLIENȚILOR (pentru legăturile cu cererile către ALAMO)"]
    for unit in units:
        odoo = unit["odoo"]["state"] if unit["odoo"] else NOT_IN_ODOO
        titles = "; ".join(r["title"] for r in unit["recs"] if r["title"])
        out.append(
            f"\nOFERTA {unit['key']} | {unit['client']} | {unit['date']} | Odoo: {odoo} | cerere: {titles}"
            f" | conversații: {', '.join(unit['convs'])}"
        )
        for o in unit["docs"]:
            if o["resent"]:
                continue
            out.append(f"  {o['kind']} {o['number']} v{o['version']} trimisă în {o['message']}:")
            out += [
                f"    [{line_ref(line) or '-'}] {line['name'][:110]} | {line['qty']} {line['uom']}"
                for line in o["lines"]
            ]
        for t in (t for r in unit["recs"] for t in r["offer_text"]):
            out.append(f"  preț în email [{t['src']}]: {t['text']}")
    return "\n".join(out)


def write_batches(units, alamo, convs, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.txt"):
        old.unlink()
    written = []
    by_conv = collections.defaultdict(list)
    for unit in units:
        by_conv[unit["convs"][0]].append(unit)
    # the offers of one conversation stay in the same batch, followed by the conversation once
    groups = list(by_conv.values())
    batch, size, part = [], 0, 1
    for group in groups + [None]:
        if group is None or (batch and size + len(group) > BATCH_SIZE):
            text = []
            for g in batch:
                text += [unit_text(u, convs) for u in g]
                seen = set()
                for u in g:
                    for cid in u["convs"]:
                        if cid not in seen:
                            seen.add(cid)
                            text.append(conversation_text(convs[cid]))
            path = folder / f"statii_{part:02d}.txt"
            path.write_text("\n".join(text), encoding="utf-8")
            written.append((path.name, size))
            batch, size, part = [], 0, part + 1
        if group is not None:
            batch.append(group)
            size += len(group)
    path = folder / "alamo_01.txt"
    path.write_text("\n".join(alamo_text(c, units) for c in alamo), encoding="utf-8")
    written.append((path.name, len(alamo)))
    path = folder / "oferte_clienti.txt"
    path.write_text(client_offer_index(units, convs), encoding="utf-8")
    written.append((path.name, len(units)))
    return written


# --- analysis checks --------------------------------------------------------------------------------------


def all_messages(convs):
    return {m["id"]: (m, c) for c in convs.values() for m in c["messages"]}


def quote_error(item, allowed, label):
    """Error text for a {src, citat} item, None when the quote is in the message (body or attachment text)."""
    m = allowed.get(item.get("src"))
    quote = squash(item.get("citat") or "")
    if not m:
        return f"{label}: sursa {item.get('src')!r} nu e într-o conversație permisă"
    if len(quote) < 3:
        return f"{label}: citat lipsă"
    texts = [m["body"]] + [a["text"] for a in m["attachments"] if a.get("text")]
    if not any(quote in squash(t) for t in texts):
        return f"{label}: citatul nu apare în {m['id']}: {item.get('citat')[:80]!r}"
    return None


def load_types(folder):
    path = Path(folder) / TYPES_FILE
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_entries(paths):
    entries = []
    for path in map(Path, paths):
        for e in json.loads(path.read_text(encoding="utf-8")):
            e["_file"] = path.name
            entries.append(e)
    return entries


def check_stations(entries, units, convs, types):
    """Errors in statii/*.json. A station whose quote fails is dropped; an offer without an entry is listed."""
    by_key = {u["key"]: u for u in units}
    known = {t["tip"] for t in types}
    errors, seen = [], set()
    for e in entries:
        key = e.get("oferta")
        label = f"{e['_file']} {key}"
        unit = by_key.get(key)
        if not unit:
            errors.append(f"{label}: ofertă necunoscută")
            continue
        if key in seen:
            errors.append(f"{label}: oferta apare de două ori")
        seen.add(key)
        allowed = {m["id"]: m for cid in unit["convs"] for m in convs[cid]["messages"]}
        if not isinstance(e.get("statii"), list):
            errors.append(f"{label}: «statii» trebuie să fie o listă (goală dacă oferta nu are nicio stație)")
            continue
        for i, s in enumerate(e["statii"]):
            s["_error"] = quote_error(s, allowed, f"{label} statii[{i}]")
            if not s.get("tip"):
                s["_error"] = f"{label} statii[{i}]: lipsește «tip»"
            elif known and s["tip"] not in known:
                s["_error"] = f"{label} statii[{i}]: tipul {s['tip']!r} nu e în {TYPES_FILE}"
            if s["_error"]:
                errors.append(s["_error"])
    missing = [u["key"] for u in units if u["key"] not in seen]
    return errors, missing


def check_alamo(entries, alamo, convs, units):
    """Errors in alamo/*.json. A link's evidence may come from any conversation (the ALAMO thread or the client's)."""
    by_id = {c["id"]: c for c in alamo}
    unit_keys = {u["key"] for u in units}
    everywhere = {mid: m for mid, (m, _) in all_messages(convs).items()}
    errors, seen = [], set()
    for e in entries:
        label = f"{e['_file']} {e.get('conv')}"
        conv = by_id.get(e.get("conv"))
        if not conv:
            errors.append(f"{label}: nu e o conversație în care AKRO scrie către ALAMO")
            continue
        seen.add(conv["id"])
        own = {m["id"]: m for m in conv["messages"]}
        labels = e.get("etichete") or []
        if not labels or any(x not in ALAMO_LABELS for x in labels):
            errors.append(f"{label}: «etichete» trebuie să fie din {ALAMO_LABELS}, nu {labels!r}")
        items = [("rezumat", e.get("rezumat"))] + [
            (f"{key}[{i}]", item) for key in ("cereri", "raspunsuri") for i, item in enumerate(e.get(key) or [])
        ]
        for name, item in items:
            if not item:
                continue
            item["_error"] = quote_error(item, own, f"{label} {name}")
            if item["_error"]:
                errors.append(item["_error"])
        for i, link in enumerate(e.get("legaturi") or []):
            link_label = f"{label} legaturi[{i}]"
            link["_error"] = None
            if link.get("oferta") not in unit_keys:
                link["_error"] = f"{link_label}: ofertă necunoscută {link.get('oferta')!r}"
            elif not link.get("dovezi"):
                link["_error"] = f"{link_label}: nicio dovadă"
            if link["_error"]:
                errors.append(link["_error"])
                continue
            for j, ev in enumerate(link["dovezi"]):
                ev["_error"] = quote_error(ev, everywhere, f"{link_label} dovezi[{j}]")
                if ev["_error"]:
                    errors.append(ev["_error"])
            if all(ev["_error"] for ev in link["dovezi"]):
                link["_error"] = f"{link_label}: nicio dovadă verificată"
    missing = [c["id"] for c in alamo if c["id"] not in seen]
    return errors, missing


# --- pages ------------------------------------------------------------------------------------------------


def message_entry(m):
    """One email as the pages show it: the same fields as in emailuri.html."""
    return {
        "date": m["local_date"],
        "akro": m["is_akro"],
        "alamo": is_alamo(m["from_email"]),
        "from": f"{m['from_name']} <{m['from_email']}>" if m["from_email"] else m["from_name"],
        "to": ", ".join(r["name"] or r["email"] for r in m["recipients"] if r["field"] == "to"),
        "cc": ", ".join(r["name"] or r["email"] for r in m["recipients"] if r["field"] == "cc"),
        "subject": m["subject"],
        "folder": m["folder"],
        "body": m["body"],
        "newLen": m["new_len"],
        "att": [
            {"name": a["name"], "path": a["path"], "reason": attachment_note(a["reason"])}
            for a in m["attachments"]
            if not a["inline"]
        ],
    }


def thread(conv_list):
    """The emails of these conversations in date order; a copy of the same email (Sent Items and the Cc in the
    Inbox) appears once."""
    seen, out = set(), []
    for m in sorted((m for c in conv_list for m in c["messages"]), key=lambda m: m["local_date"]):
        key = m["message_id"] or m["id"]
        if key not in seen:
            seen.add(key)
            out.append(m)
    return out


def sourced(item, msgs):
    """{text, src, quote, date} of a checked analysis item; None when its quote failed."""
    if not item or item.get("_error"):
        return None
    m = msgs.get(item.get("src"))
    return {
        "text": item.get("text") or "",
        "src": item["src"],
        "quote": item.get("citat") or "",
        "date": m["local_date"] if m else "",
        "note": item.get("nota") or "",
    }


def record_entry(rec):
    keep = ("rid", "conv", "nr", "title", "category", "state", "request", "final", "clarifications", "phone")
    return {k: rec[k] for k in keep} | {"offerText": rec["offer_text"], "outcome": rec["outcome"]}


def doc_entry(o):
    keep = ("kind", "number", "version", "date", "expires", "sent", "message", "file", "path", "lines", "terms")
    return {k: o[k] for k in keep} | {"total": o["total"], "currency": o["currency"], "resent": o["resent"]}


def stations_page(convs, units, entries, types):
    by_key = {e["oferta"]: e for e in entries}
    type_info = {t["tip"]: t for t in types}
    topics = collections.defaultdict(list)
    for c in convs.values():
        topics[c["topic"]].append(c)
    messages, out = {}, []
    for unit in units:
        entry = by_key.get(unit["key"], {})
        msgs = {m["id"]: m for cid in unit["convs"] for m in convs[cid]["messages"]}
        stations = [
            s
            for s in (
                sourced(s, msgs) | {"type": s["tip"]} if sourced(s, msgs) else None for s in entry.get("statii") or []
            )
            if s
        ]
        kinds = list(dict.fromkeys(s["type"] for s in stations)) or [NO_STATION]
        # the whole deal with the client: every client conversation sharing a document number with this offer
        related = [c for cid in unit["convs"] for c in topics[convs[cid]["topic"]] if c["type"] == "client"]
        emails = thread(list({c["id"]: c for c in [convs[cid] for cid in unit["convs"]] + related}.values()))
        for m in emails:
            messages[m["id"]] = message_entry(m)
        docs = [o for o in unit["docs"] if not o["resent"]]
        pdf = ([o for o in docs if o["kind"] == "Ofertă"] or docs or [None])[-1]
        out.append(
            {
                "key": unit["key"],
                "number": "" if unit["key"].startswith(EMAIL_OFFER) else unit["key"],
                "kinds": list(dict.fromkeys(o["kind"] for o in docs)),
                "client": unit["client"],
                "date": unit["date"],
                "total": unit["total"],
                "currency": unit["currency"],
                "status": unit["odoo"]["state"] if unit["odoo"] else NOT_IN_ODOO,
                "odooTotal": unit["odoo"]["total"] if unit["odoo"] else "",
                "types": kinds,
                "stations": stations,
                "content": entry.get("continut") or "",
                "analysed": bool(entry),
                "records": [record_entry(r) for r in unit["recs"]],
                "convs": [
                    {"id": c["id"], "nr": c["nr"], "subject": c["subject"], "own": c["id"] in unit["convs"]}
                    for c in {c["id"]: c for c in [convs[cid] for cid in unit["convs"]] + related}.values()
                ],
                "docs": [doc_entry(o) for o in docs],
                "pdf": {"path": pdf["path"], "file": pdf["file"]} if pdf and pdf["path"] else None,
                "thread": [m["id"] for m in emails],
            }
        )
    counts = collections.Counter(k for u in out for k in u["types"])
    type_list = [
        {
            "type": name,
            "definition": type_info.get(name, {}).get("definitie", ""),
            "station": type_info.get(name, {}).get("statie", name != NO_STATION),
            "offers": counts[name],
        }
        for name in sorted(counts, key=lambda n: (n == NO_STATION, -counts[n], n))
    ]
    return out, type_list, messages


def alamo_page(convs, alamo, entries, units):
    by_conv = {e["conv"]: e for e in entries}
    by_key = {u["key"]: u for u in units}
    everywhere = all_messages(convs)
    topics = collections.defaultdict(list)
    for c in convs.values():
        topics[c["topic"]].append(c)
    listed = {c["id"] for c in alamo}
    messages, out = {}, []
    for conv in sorted(alamo, key=lambda c: c["messages"][0]["local_date"]):
        entry = by_conv.get(conv["id"], {})
        own = {m["id"]: m for m in conv["messages"]}
        emails = thread([conv])
        for m in emails:
            messages[m["id"]] = message_entry(m)
        # ALAMO's own messages on the same order (confirmations, packing slips) that AKRO did not answer
        others = [
            c
            for c in topics[conv["topic"]]
            if c["id"] != conv["id"]
            and any(
                is_alamo(m["from_email"]) or any(is_alamo(r["email"]) for r in m["recipients"]) for m in c["messages"]
            )
        ]
        for c in others:
            if c["id"] not in listed:
                for m in thread([c]):
                    messages[m["id"]] = message_entry(m)
        links = []
        for link in entry.get("legaturi") or []:
            unit = by_key.get(link.get("oferta"))
            if link.get("_error") or not unit:
                continue
            evidence = []
            for ev in link["dovezi"]:
                if ev.get("_error"):
                    continue
                m, c = everywhere[ev["src"]]
                evidence.append(
                    {
                        "src": ev["src"],
                        "quote": ev["citat"],
                        "note": ev.get("nota") or "",
                        "date": m["local_date"],
                        "conv": c["id"],
                        "nr": c["nr"],
                        "here": c["id"] == conv["id"],
                        "side": "AKRO" if m["is_akro"] else ("ALAMO" if is_alamo(m["from_email"]) else "client"),
                    }
                )
            links.append(
                {
                    "key": unit["key"],
                    "client": unit["client"],
                    "date": unit["date"],
                    "total": unit["total"],
                    "currency": unit["currency"],
                    "status": unit["odoo"]["state"] if unit["odoo"] else NOT_IN_ODOO,
                    "text": link.get("text") or "",
                    "evidence": evidence,
                    "docs": [doc_entry(o) for o in unit["docs"] if not o["resent"]],
                    "offerText": [t for r in unit["recs"] for t in r["offer_text"]],
                }
            )
        out.append(
            {
                "id": conv["id"],
                "nr": conv["nr"],
                "subject": conv["subject"],
                "first": emails[0]["local_date"],
                "last": emails[-1]["local_date"],
                "labels": [x for x in entry.get("etichete") or [] if x in ALAMO_LABELS] or ["altele"],
                "analysed": bool(entry),
                "summary": sourced(entry.get("rezumat"), own),
                "requests": [s for s in (sourced(i, own) for i in entry.get("cereri") or []) if s],
                "answers": [s for s in (sourced(i, own) for i in entry.get("raspunsuri") or []) if s],
                "links": links,
                "keys": conv["topic_keys"],
                "thread": [m["id"] for m in emails],
                "toAlamo": sum(m["is_akro"] and any(is_alamo(r["email"]) for r in m["recipients"]) for m in emails),
                "related": [
                    {
                        "id": c["id"],
                        "nr": c["nr"],
                        "subject": c["subject"],
                        "listed": c["id"] in listed,
                        "thread": [m["id"] for m in thread([c])],
                    }
                    for c in others
                ],
            }
        )
    return out, messages


def alamo_mail_counts(messages, alamo_rows):
    """Emails AKRO sent to ALAMO, over the whole PST (a copy in Sent Items and in the Inbox counts once)."""
    seen, sent, received = set(), [], []
    for m in messages:
        key = m["message_id"] or (m["subject"], m["date"], m["from_email"])
        if key in seen:
            continue
        seen.add(key)
        if m["is_akro"] and any(is_alamo(r["email"]) for r in m["recipients"]):
            sent.append(m)
        elif is_alamo(m["from_email"]):
            received.append(m)
    rfq_ids = {mid for row in alamo_rows if RFQ in row["labels"] for mid in row["thread"]}
    return {
        "sent": len(sent),
        "received": len(received),
        "sentRfq": sum(m["id"] in rfq_ids for m in sent),
        "convs": len(alamo_rows),
        "rfqConvs": sum(RFQ in row["labels"] for row in alamo_rows),
        "first": min(m["local_date"] for m in sent)[:10] if sent else "",
        "last": max(m["local_date"] for m in sent)[:10] if sent else "",
        "byLabel": collections.Counter(row["labels"][0] for row in alamo_rows),
    }


ODOO_STATE_HELP = {
    "Ofertă trimisă": "oferta a fost trimisă clientului, iar în Odoo nu s-a transformat încă în comandă",
    "Comandă de vânzare": "clientul a comandat: oferta a devenit comandă în Odoo",
    "Anulat": "oferta a fost anulată în Odoo",
    "Ofertă": "ciornă în Odoo (documentul există, dar nu e marcat ca trimis)",
    NOT_IN_ODOO: "numărul ofertei nu apare în lista Odoo primită, deci starea nu se cunoaște",
}
ALAMO_LABEL_HELP = {
    "cerere de ofertă": "AKRO cere preț, disponibilitate, termen sau date tehnice, înainte să comande",
    "comandă": "AKRO trimite sau modifică o comandă de achiziție (P0xxxx)",
    "confirmare de comandă": "ALAMO confirmă comanda primită",
    "livrare": "expediere, packing slip, transport sau întrebări despre stadiul comenzii",
    "factură": "facturi trimise sau cerute",
    "altele": "orice altceva",
}


def write_page(template, data, path, summary, headline):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / template).read_text(encoding="utf-8")
    # the data goes in last, so an email text can never be mistaken for one of the other placeholders
    page = (
        page.replace("__SUMMARY_LINE__", html.escape(headline))
        .replace("__SUMMARY__", summary_html(summary))
        .replace("__NAV__", nav_html(path.name))
        .replace("/*__DATA__*/{}", payload)
    )
    path.write_text(page, encoding="utf-8")


def build_outputs(convs, records, units, alamo, types, args):
    station_entries = load_entries(sorted(p for p in Path(args.statii).glob("*.json") if p.name != TYPES_FILE))
    alamo_entries = load_entries(sorted(Path(args.alamo).glob("*.json")))
    s_errors, s_missing = check_stations(station_entries, units, convs, types)
    a_errors, a_missing = check_alamo(alamo_entries, alamo, convs, units)
    offers, type_list, s_messages = stations_page(convs, units, station_entries, types)
    alamo_rows, a_messages = alamo_page(convs, alamo, alamo_entries, units)
    messages = [m for c in convs.values() for m in c["messages"]]
    mails = alamo_mail_counts(messages, alamo_rows)
    # the trade terms are explained with the glossary written for the rules (Phase 3)
    glossary = load_glossary(args.glosar) if Path(args.glosar).exists() else []
    generated = datetime.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")

    status = collections.Counter(o["status"] for o in offers)
    with_station = [o for o in offers if NO_STATION not in o["types"]]
    station_types = [t for t in type_list if t["station"]]
    s_summary = [
        (
            "Oferte",
            [
                ("Oferte trimise clienților", len(offers)),
                ("Cu cel puțin o stație", len(with_station)),
                ("Fără stație (piese, consumabile, servicii)", len(offers) - len(with_station)),
                ("Tipuri de stații găsite", len(station_types)),
            ],
        ),
        ("Stare în Odoo", [(s, status[s]) for s in ODOO_STATES + [NOT_IN_ODOO] if status[s]]),
        ("Tipuri", [(t["type"], t["offers"]) for t in type_list]),
    ]
    s_headline = (
        f"{number(len(offers))} oferte trimise · {number(len(with_station))} cu stații · "
        f"{number(len(station_types))} tipuri de stații"
    )
    a_summary = [
        (
            "Emailuri",
            [
                ("Trimise de AKRO către ALAMO", mails["sent"]),
                ("Din ele, în conversațiile cu cerere de ofertă", mails["sentRfq"]),
                ("Primite de la ALAMO", mails["received"]),
            ],
        ),
        (
            "Conversații în care AKRO scrie către ALAMO",
            [("Toate", mails["convs"])]
            + [(label, mails["byLabel"][label]) for label in ALAMO_LABELS if mails["byLabel"][label]],
        ),
    ]
    a_headline = (
        f"{number(mails['convs'])} conversații · {number(mails['rfqConvs'])} cu cerere de ofertă · "
        f"{number(mails['sent'])} emailuri trimise de AKRO către ALAMO"
    )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_page(
        "template_statii.html",
        {
            "generated": generated,
            "types": type_list,
            "offers": offers,
            "messages": s_messages,
            "noStation": NO_STATION,
            "notInOdoo": NOT_IN_ODOO,
            "states": ODOO_STATES,
            "stateHelp": ODOO_STATE_HELP,
            "glossary": glossary,
        },
        out / "statii.html",
        s_summary,
        s_headline,
    )
    write_page(
        "template_alamo.html",
        {
            "generated": generated,
            "convs": alamo_rows,
            "messages": a_messages,
            "labels": ALAMO_LABELS,
            "labelHelp": ALAMO_LABEL_HELP,
            "rfq": RFQ,
            "stateHelp": ODOO_STATE_HELP,
            "glossary": glossary,
        },
        out / "alamo.html",
        a_summary,
        a_headline,
    )

    print(summary_text(s_summary))
    print(summary_text(a_summary))
    problems = s_errors + a_errors
    if s_missing:
        problems.append(f"{len(s_missing)} oferte fără analiză de stații: {', '.join(s_missing[:10])}")
    if a_missing:
        problems.append(f"{len(a_missing)} conversații ALAMO fără analiză: {', '.join(a_missing)}")
    if problems:
        print(f"  ! {len(problems)} probleme (ce nu se verifică nu apare în pagini):")
        for p in problems:
            print(f"    {p}")
    print(f"Gata. Paginile: {out / 'statii.html'}, {out / 'alamo.html'}")
    if not (out / "emailuri.html").exists():
        print(f"  ! {out / 'emailuri.html'} lipsește: linkurile spre conversații merg după genereaza_emailuri.py")


# --- main -------------------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description="Generează paginile din Faza 4: ofertele pe tipuri de stații (output/statii.html) și cererile "
        "către ALAMO (output/alamo.html)."
    )
    ap.add_argument("--mesaje", default=str(HERE / "date" / "mesaje.json"), help="mesajele scrise de extrage_pst.py")
    ap.add_argument("--oferte", default=str(HERE / "Oferte Alex_Q3 2026.xlsx"), help="lista de oferte din Odoo (.xlsx)")
    ap.add_argument(
        "--nomenclator", default=str(HERE / "output" / "produse.csv"), help="nomenclatorul din genereaza.py"
    )
    ap.add_argument("--analiza", default=str(HERE / "analiza"), help="folderul cu analiza conversațiilor (*.json)")
    ap.add_argument("--statii", default=str(HERE / "statii"), help="folderul cu analiza stațiilor (*.json)")
    ap.add_argument("--alamo", default=str(HERE / "alamo"), help="folderul cu analiza conversațiilor ALAMO (*.json)")
    ap.add_argument(
        "--glosar", default=str(HERE / "reguli" / "glosar.json"), help="explicațiile termenilor (glosarul din Faza 3)"
    )
    ap.add_argument("--out", default=str(HERE / "output"), help="unde se scriu paginile (implicit output)")
    ap.add_argument("--loturi", help="doar scrie ofertele și conversațiile ALAMO de citit, în acest folder")
    ap.add_argument("--verifica", nargs="+", help="doar verifică aceste fișiere de analiză (statii/ sau alamo/)")
    args = ap.parse_args()

    # the inputs come from other steps: say which one to run instead of failing with a traceback
    needed = [
        (args.mesaje, "rulează extrage_pst.py (vezi README, «Faza 2»)"),
        (args.nomenclator, 'rulează întâi genereaza.py "Produs (product.template).xlsx" (Task 1)'),
        (args.oferte, "copiază aici lista de oferte din Odoo sau dă calea cu --oferte"),
    ]
    missing_inputs = [(path, fix) for path, fix in needed if not Path(path).exists()]
    for path, fix in missing_inputs:
        print(f"Lipsește {path}: {fix}.", file=sys.stderr)
    if missing_inputs:
        sys.exit(1)

    nomenclature = load_nomenclature(args.nomenclator)
    convs, records = load_records(args, nomenclature)
    units = offer_units(convs, records)
    alamo = alamo_conversations(convs)

    if args.loturi:
        for name, n in write_batches(units, alamo, convs, args.loturi):
            print(f"  {name}: {n}")
        print(f"{len(units)} oferte trimise clienților, {len(alamo)} conversații cu ALAMO, în {args.loturi}")
        return
    types = load_types(args.statii)
    if args.verifica:
        errors = []
        for path in args.verifica:
            entries = load_entries([path])
            if Path(path).resolve().parent == Path(args.alamo).resolve():
                errors += check_alamo(entries, alamo, convs, units)[0]
            else:
                errors += check_stations(entries, units, convs, types)[0]
            print(f"{path}: {len(entries)} intrări")
        print(f"{len(errors)} erori")
        for e in errors:
            print(f"  ! {e}")
        sys.exit(1 if errors else 0)
    build_outputs(convs, records, units, alamo, types, args)


if __name__ == "__main__":
    main()
