#!/usr/bin/env python3
"""Builds the AKKRO offering-rules catalogue: how a client request becomes the offer AKRO sends.

Usage:
    python3 genereaza_reguli.py [--reguli reguli] [--out output]
    python3 genereaza_reguli.py --loturi date/loturi_reguli   # only writes the conversations to read, per category
    python3 genereaza_reguli.py --verifica reguli/13.json     # only checks the evidence of these rule files

Inputs:
  - everything genereaza_emailuri.py reads (date/mesaje.json, output/produse.csv, the Odoo offer list,
    analiza/*.json): the conversations, their states and offers are rebuilt the same way;
  - reguli/*.json: the rules, each with the conversations it comes from and an exact quote per conversation
    (written by reading the conversations from --loturi, see reguli/INSTRUCTIUNI.md);
  - reguli/glosar.json: plain explanations of the trade terms and abbreviations, shown on the page next to them.

Outputs (in --out):
  - reguli.html: standalone page, opens with a double click; links to emailuri.html in the same folder
    (client data - internal only).

Standard library only.
"""

import argparse
import collections
import datetime
import html
import json
import re
import sys
from pathlib import Path

from genereaza import nav_html, number, summary_html, summary_text
from genereaza_emailuri import (
    LOCAL_TZ,
    STATE_AFTER_SALE,
    STATE_COMPLETE,
    STATE_NO_OFFER,
    build_conversations,
    build_records,
    check_analysis,
    conversation_text,
    link_topics,
    load_analysis,
    load_messages,
    load_nomenclature,
    load_odoo_offers,
    message_texts,
    squash,
)

HERE = Path(__file__).resolve().parent
GENERAL = "Toate categoriile"
CATEGORIES = [
    "01-Filtre impuritati",
    "08-Osmoza si filtrare pe membrane",
    "10-Ozonatoare",
    "11-Pompe de dozare",
    "12-Chimicale pentru conditionare si intretinere",
    "13-Filtre multistrat diferite medii",
    "14-Componente pentru filtre multistrat",
    "16-Prestari servicii",
    "21-Aparatura de analiza si control",
    "23-Diverse materiale, consumabile",
    "25-Produse ocazionale unicate",
    "27-Uv",
    "Altele / neclar",
    GENERAL,
]
# the main source; the other two states only for the clarifications AKRO asks (ticket: "doar pentru clarificări")
CLARIFICATION_ONLY = {STATE_NO_OFFER, STATE_AFTER_SALE}
USED_STATES = [STATE_COMPLETE, STATE_NO_OFFER, STATE_AFTER_SALE]
EVIDENCE_FOR = ["cerere", "clarificare", "ofertă"]
CONFIDENCE_SURE = "sigură"
CONFIDENCE_HINT = "indiciu"
CONFIDENCE_CONTRADICTORY = "contradictorie"
CONFIDENCES = [CONFIDENCE_SURE, CONFIDENCE_HINT, CONFIDENCE_CONTRADICTORY]
SURE_MIN_CONVERSATIONS = 3
GLOSSARY_FILE = "glosar.json"  # in the rules folder, but not a rules file
BATCH_SIZE = 40


# --- conversations ----------------------------------------------------------------------------------------


def load_records(args, nomenclature):
    """Conversations (by id) and request records, built exactly as in emailuri.html; conv["topic"] groups the
    conversations about the same deal (shared AKRO document number), as the topics of emailuri.html."""
    _, messages = load_messages(args.mesaje)
    odoo = load_odoo_offers(args.oferte)
    conversations, _ = build_conversations(messages, odoo, nomenclature)
    analysis = load_analysis(args.analiza)
    check_analysis(analysis, conversations)  # marks the items without a verified source, as on the page
    records = build_records(conversations, analysis)
    link_topics(conversations, odoo)
    return {c["id"]: c for c in conversations}, records


def record_text(rec):
    """What the email analysis found for one request: the start of its block in the rules batches."""

    def item(i):
        return f"{i['text']} [{i['src']}] «{i['quote']}»" if i else "-"

    out = [
        f"\n{'#' * 100}\nRÂND {rec['rid']} (nr. {rec['nr']}) | stare: {rec['state']} | categorie: {rec['category']}"
        f" | cerere: {rec['title'] or '-'}",
        f"CERINȚA: {item(rec['request'])}",
    ]
    out += [f"CERINȚĂ FINALĂ ({f['extra'].get('camp', '-')}): {item(f)}" for f in rec["final"]]
    for c in rec["clarifications"]:
        out.append(
            f"CLARIFICARE: întrebare {item(c['question'])} → răspuns {item(c['answer'])} | schimbare: {c['change']}"
        )
    out += [f"TELEFON: {item(p)}" for p in rec["phone"]]
    out += [f"FIȘĂ DE SECURITATE ({s['extra'].get('moment', '-')}): {item(s)}" for s in rec["sds"]]
    out += [f"OFERTĂ ÎN TEXT: {item(o)}" for o in rec["offer_text"]]
    outcome = rec["outcome"] or {}
    out.append(f"REZULTAT: {outcome.get('value', '-')}" + (f" — {item(outcome)}" if outcome.get("src") else ""))
    return "\n".join(out)


def offer_details(conv, numbers):
    """The offers of a request with prices, currency and terms - conversation_text lists only names and quantities."""
    out = []
    for o in conv["offers"]:
        if o["number"] not in numbers or o["resent"]:
            continue
        out.append(
            f"PREȚURI {o['kind']} {o['number']} v{o['version']} ({o['sent'][:10]}), total {o['total']} {o['currency']}:"
        )
        for line in o["lines"]:
            ref = line["ref"] or (line["product"] or {}).get("ref") or "-"
            out.append(
                f"  [{ref}] {line['name'][:120]} | {line['qty']} {line['uom']} × {line['price']} {line['currency']}"
                + (f" (reducere {line['discount']}%)" if line["discount"] else "")
                + f" | {line['match']}"
            )
        out += [f"  termen: {k}: {v}" for k, v in o["terms"]]
    return "\n".join(out)


def write_batches(convs, records, folder):
    """Per category, the requests the rules come from: the email analysis, the offers with prices and the
    whole conversation. Complete requests first; the other two states only for clarifications."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("reguli_*.txt"):
        old.unlink()
    by_category = collections.defaultdict(list)
    for rec in records:
        if rec["state"] in USED_STATES:
            by_category[rec["category"]].append(rec)
    written = []
    for category, recs in sorted(by_category.items()):
        recs.sort(key=lambda r: (USED_STATES.index(r["state"]), float(str(r["nr"]).split(".")[0])))
        slug = re.match(r"\d{2}", category).group() if re.match(r"\d{2}", category) else "altele"
        for part, start in enumerate(range(0, len(recs), BATCH_SIZE), start=1):
            text = "\n".join(
                f"{record_text(rec)}\n{offer_details(convs[rec['conv']], rec['offers'])}\n"
                f"{conversation_text(convs[rec['conv']])}"
                for rec in recs[start : start + BATCH_SIZE]
            )
            path = folder / f"reguli_{slug}_{part}.txt"
            path.write_text(f"CATEGORIA {category}\n{text}", encoding="utf-8")
            written.append((path.name, len(recs[start : start + BATCH_SIZE])))
    return written


# --- rules (reguli/*.json) --------------------------------------------------------------------------------


def load_glossary(path):
    """[{termen, forme, exact, explicatie}]: each form is a regular expression the page looks for in the rules
    (case-sensitive when "exact"). A form that does not compile stops the run instead of breaking the page."""
    glossary = json.loads(Path(path).read_text(encoding="utf-8"))
    for entry in glossary:
        for form in entry["forme"]:
            try:
                re.compile(form)
            except re.error as e:
                sys.exit(f"{path}: forma {form!r} de la «{entry['termen']}» nu e o expresie validă: {e}")
    return [
        {"term": e["termen"], "forms": e["forme"], "exact": bool(e.get("exact")), "text": e["explicatie"]}
        for e in glossary
    ]


def load_rules(paths):
    rules = []
    for path in map(Path, paths):
        for rule in json.loads(path.read_text(encoding="utf-8")):
            rule["_file"] = path.name
            rules.append(rule)
    return rules


def check_evidence(ev, convs, states, label):
    """Error text for one piece of evidence, None when its quote is found in the message it names."""
    conv = convs.get(ev.get("conv"))
    if not conv:
        return f"{label}: conversație necunoscută {ev.get('conv')!r}"
    used = states.get(conv["id"], set()) & set(USED_STATES)
    if not used:
        return f"{label}: {conv['id']} nu e o cerere folosită (stare {', '.join(sorted(states.get(conv['id'], [])))})"
    if ev.get("pentru") not in EVIDENCE_FOR:
        return f"{label}: «pentru» trebuie să fie una din {EVIDENCE_FOR}, nu {ev.get('pentru')!r}"
    if STATE_COMPLETE not in used and ev["pentru"] != "clarificare":
        return f"{label}: {conv['id']} ({', '.join(sorted(used))}) poate fi doar dovadă de clarificare"
    m = next((m for m in conv["messages"] if m["id"] == ev.get("src")), None)
    quote = squash(ev.get("citat") or "")
    if not m:
        return f"{label}: sursa {ev.get('src')} nu e în {conv['id']}"
    if len(quote) < 3:
        return f"{label}: citat lipsă"
    if not any(quote in t for t in message_texts(m)):
        return f"{label}: citatul nu apare în {m['id']}: {ev.get('citat')[:80]!r}"
    return None


def check_rules(rules, convs, records, nomenclature):
    """Errors per rule. Evidence that fails is dropped (marked _error); a rule left without evidence is not shown."""
    states = collections.defaultdict(set)
    for rec in records:
        states[rec["conv"]].add(rec["state"])
    by_ref = nomenclature[1]
    errors, seen = [], set()
    for rule in rules:
        label = f"{rule['_file']} {rule.get('cod') or '?'}"
        if rule.get("cod") in seen:
            errors.append(f"{label}: cod folosit deja de altă regulă")
        seen.add(rule.get("cod"))
        for key in ("cod", "titlu", "cand"):
            if not rule.get(key):
                errors.append(f"{label}: lipsește «{key}»")
        if rule.get("categorie") not in CATEGORIES:
            errors.append(f"{label}: categorie necunoscută {rule.get('categorie')!r}")
        for p in (rule.get("oferta") or {}).get("produse") or []:
            if p.get("ref") and p["ref"] not in by_ref:
                errors.append(f"{label}: codul {p['ref']} nu e în nomenclator")
            elif not p.get("ref") and not p.get("nume"):
                errors.append(f"{label}: produs fără «ref» și fără «nume»")
        groups = [("dovezi", rule.get("dovezi") or [])] + [
            (f"contradictii[{i}]", c.get("dovezi") or []) for i, c in enumerate(rule.get("contradictii") or [])
        ]
        for name, evidence in groups:
            if not evidence:
                errors.append(f"{label}: «{name}» nu are nicio dovadă")
            for i, ev in enumerate(evidence):
                ev["_error"] = check_evidence(ev, convs, states, f"{label} {name}[{i}]")
                if ev["_error"]:
                    errors.append(ev["_error"])
    return errors


# --- page -------------------------------------------------------------------------------------------------


def evidence_item(ev, convs, recs_by_conv):
    conv = convs[ev["conv"]]
    m = next(m for m in conv["messages"] if m["id"] == ev["src"])
    recs = recs_by_conv[conv["id"]]
    return {
        "conv": conv["id"],
        "nr": conv["nr"],
        "client": conv["client_name"],
        "subject": conv["subject"],
        "titles": [r["title"] for r in recs if r["title"]],
        "state": next((s for s in USED_STATES if s in {r["state"] for r in recs}), ""),
        "src": ev["src"],
        "date": m["local_date"],
        "from": "AKRO" if m["is_akro"] else "client",
        "quote": ev["citat"],
        "for": ev["pentru"],
        "note": ev.get("nota") or "",
    }


def offered_lines(conv, refs):
    """Every offered line of the rule's products in one conversation, with its own price and currency."""
    out = []
    for o in conv["offers"]:
        if o["resent"]:
            continue
        for line in o["lines"]:
            ref = line["ref"] or (line["product"] or {}).get("ref")
            if ref in refs:
                out.append(
                    {
                        "conv": conv["id"],
                        "nr": conv["nr"],
                        "offer": o["number"],
                        "kind": o["kind"],
                        "date": o["sent"][:10],
                        "ref": ref,
                        "name": line["name"],
                        "qty": line["qty"],
                        "uom": line["uom"],
                        "price": line["price"],
                        "discount": line["discount"],
                        "currency": line["currency"] or o["currency"],
                    }
                )
    return out


def page_rules(rules, convs, records, nomenclature):
    by_ref = nomenclature[1]
    recs_by_conv = collections.defaultdict(list)
    for rec in records:
        recs_by_conv[rec["conv"]].append(rec)
    out = []
    for rule in rules:
        evidence = [evidence_item(e, convs, recs_by_conv) for e in rule.get("dovezi") or [] if not e["_error"]]
        contradictions = [
            {
                "text": c.get("text") or "",
                "evidence": [evidence_item(e, convs, recs_by_conv) for e in c.get("dovezi") or [] if not e["_error"]],
            }
            for c in rule.get("contradictii") or []
        ]
        contradictions = [c for c in contradictions if c["evidence"]]
        if not evidence:
            continue
        conv_ids = list(dict.fromkeys(e["conv"] for e in evidence + [e for c in contradictions for e in c["evidence"]]))
        offer = rule.get("oferta") or {}
        products = [
            {
                "ref": p.get("ref") or "",
                "name": by_ref[p["ref"]]["Nume"] if p.get("ref") in by_ref else p.get("nume") or "",
                "role": p.get("rol") or "",
                "known": p.get("ref") in by_ref,
            }
            for p in offer.get("produse") or []
            if p.get("ref") in by_ref or (not p.get("ref") and p.get("nume"))
        ]
        refs = {p["ref"] for p in products if p["known"]}
        # conversations about the same deal (a forward, the order after the offer) count once
        deals = len({convs[cid]["topic"] for cid in conv_ids})
        if contradictions:
            confidence = CONFIDENCE_CONTRADICTORY
        elif deals >= SURE_MIN_CONVERSATIONS:
            confidence = CONFIDENCE_SURE
        else:
            confidence = CONFIDENCE_HINT
        out.append(
            {
                "code": rule["cod"],
                "title": rule.get("titlu") or "",
                "explanation": rule.get("explicatie") or "",
                "category": rule.get("categorie") or "",
                "when": rule.get("cand") or "",
                "clarifications": rule.get("clarificari") or [],
                "products": products,
                "services": offer.get("servicii") or [],
                "documents": offer.get("documente") or [],
                "conditions": offer.get("conditii") or [],
                "evidence": evidence,
                "contradictions": contradictions,
                "convs": conv_ids,
                "conversations": len(conv_ids),
                "frequency": deals,
                "confidence": confidence,
                "lines": [line for cid in conv_ids for line in offered_lines(convs[cid], refs)],
            }
        )
    return out


def write_page(data, path, summary, headline):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / "template_reguli.html").read_text(encoding="utf-8")
    # the data goes in last, so a quote can never be mistaken for one of the other placeholders
    page = (
        page.replace("__SUMMARY_LINE__", html.escape(headline))
        .replace("__SUMMARY__", summary_html(summary))
        .replace("__NAV__", nav_html(path.name))
        .replace("/*__DATA__*/{}", payload)
    )
    path.write_text(page, encoding="utf-8")


def build_outputs(convs, records, nomenclature, args):
    rules = load_rules(p for p in sorted(Path(args.reguli).glob("*.json")) if p.name != GLOSSARY_FILE)
    glossary_path = Path(args.reguli) / GLOSSARY_FILE
    glossary = load_glossary(glossary_path) if glossary_path.exists() else []
    errors = check_rules(rules, convs, records, nomenclature)
    shown = page_rules(rules, convs, records, nomenclature)
    complete = {r["conv"] for r in records if r["state"] == STATE_COMPLETE}
    cited = {cid for r in shown for cid in r["convs"]}
    confidence = collections.Counter(r["confidence"] for r in shown)
    summary = [
        (
            "Reguli",
            [
                ("Reguli afișate", len(shown)),
                ("Scoase din pagină: niciun citat nu s-a regăsit în emailuri", len(rules) - len(shown)),
                ("Sigure: se văd în cel puțin 3 afaceri diferite", confidence[CONFIDENCE_SURE]),
                ("Indicii: se văd în 1 sau 2 afaceri", confidence[CONFIDENCE_HINT]),
                ("Contradictorii: unele conversații arată altceva", confidence[CONFIDENCE_CONTRADICTORY]),
            ],
        ),
        (
            "Conversații",
            [
                ("Clientul a cerut ceva și AKRO a trimis ofertă", len(complete)),
                ("Din acestea, folosite ca dovadă pentru cel puțin o regulă", len(complete & cited)),
                ("Toate conversațiile folosite ca dovadă, inclusiv cele fără ofertă", len(cited)),
            ],
        ),
    ]
    headline = (
        f"{number(len(shown))} reguli ({number(confidence[CONFIDENCE_SURE])} sigure, "
        f"{number(confidence[CONFIDENCE_HINT])} indicii, {number(confidence[CONFIDENCE_CONTRADICTORY])} contradictorii)"
        f" · folosesc {number(len(complete & cited))} din cele {number(len(complete))} conversații cu cerere și ofertă"
    )
    data = {
        "generated": datetime.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M"),
        "categories": CATEGORIES,
        "confidences": CONFIDENCES,
        "rules": shown,
        "glossary": glossary,
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_page(data, out / "reguli.html", summary, headline)
    print(summary_text(summary))
    if errors:
        print(f"  ! {len(errors)} probleme (dovezile respinse nu apar în pagină):")
        for e in errors:
            print(f"    {e}")
    print(f"Gata. Pagina: {out / 'reguli.html'}")
    if not (out / "emailuri.html").exists():
        print(f"  ! {out / 'emailuri.html'} lipsește: linkurile spre conversații merg după genereaza_emailuri.py")


def main():
    ap = argparse.ArgumentParser(description="Generează catalogul de reguli de ofertare (output/reguli.html).")
    ap.add_argument("--mesaje", default=str(HERE / "date" / "mesaje.json"), help="mesajele scrise de extrage_pst.py")
    ap.add_argument("--oferte", default=str(HERE / "Oferte Alex_Q3 2026.xlsx"), help="lista de oferte din Odoo (.xlsx)")
    ap.add_argument(
        "--nomenclator", default=str(HERE / "output" / "produse.csv"), help="nomenclatorul din genereaza.py"
    )
    ap.add_argument("--analiza", default=str(HERE / "analiza"), help="folderul cu analiza conversațiilor (*.json)")
    ap.add_argument("--reguli", default=str(HERE / "reguli"), help="folderul cu regulile (*.json)")
    ap.add_argument("--out", default=str(HERE / "output"), help="unde se scrie pagina (implicit output)")
    ap.add_argument("--loturi", help="doar scrie cererile de citit, pe categorii, în acest folder")
    ap.add_argument("--verifica", nargs="+", help="doar verifică dovezile din aceste fișiere de reguli")
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
    if args.loturi:
        for name, n in write_batches(convs, records, args.loturi):
            print(f"  {name}: {n} cereri")
        print(f"Gata. Loturile: {args.loturi}")
        return
    if args.verifica:
        rules = load_rules(args.verifica)
        errors = check_rules(rules, convs, records, nomenclature)
        print(f"{len(rules)} reguli verificate, {len(errors)} erori")
        for e in errors:
            print(f"  ! {e}")
        sys.exit(1 if errors else 0)
    build_outputs(convs, records, nomenclature, args)


if __name__ == "__main__":
    main()
