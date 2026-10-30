#!/usr/bin/env python3
"""Builds the AKKRO email analysis page (requests, clarifications, offers) and its report.

Usage:
    python3 genereaza_emailuri.py [--mesaje date/mesaje.json] [--oferte "Oferte Alex_Q3 2026.xlsx"] [--out output]
    python3 genereaza_emailuri.py --loturi date/loturi   # only writes the conversations to analyse, in batches

Inputs:
  - date/mesaje.json: every message of the PST, written by extrage_pst.py;
  - output/produse.csv: the product nomenclature from genereaza.py (Task 1);
  - the Odoo offer list (Oferte Alex_Q3 2026.xlsx): offer number, client and state;
  - analiza/*.json: what each conversation asks for, its clarifications and outcome, each item with the
    message it comes from and the exact quote (written by reading the conversations from --loturi).

Outputs (in --out):
  - emailuri.html: standalone page, opens with a double click (client data - internal only);
  - raport_emailuri.csv, raport_emailuri.xlsx: counts per state and folder, products outside the
    nomenclature, matches to confirm, unreadable attachments, requests per category, the check sample.

Standard library only.
"""

import argparse
import collections
import csv
import datetime
import hashlib
import html
import json
import random
import re
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

from genereaza import fold, nav_html, number, read_xlsx_rows, summary_html, summary_text, write_csv, write_xlsx

HERE = Path(__file__).resolve().parent
LOCAL_TZ = ZoneInfo("Europe/Bucharest")
AKRO_DOMAINS = {"akro.ro", "spectra.ro", "kalyxx.ro"}  # AKRO brands, on the letterhead of every offer
PUBLIC_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.ro",
    "yahoo.co.uk",
    "yahoo.fr",
    "yahoo.de",
    "yahoo.it",
    "hotmail.com",
    "hotmail.ro",
    "outlook.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "ymail.com",
    "aol.com",
    "gmx.com",
    "gmx.de",
    "gmx.net",
    "mail.com",
    "protonmail.com",
    "proton.me",
    "zoho.com",
    "web.de",
}

# states of a conversation (section 2 of the ticket) and the extra one for non-client conversations
STATE_COMPLETE = "Completă"
STATE_NO_OFFER = "Fără ofertă"
STATE_NO_REQUEST = "Fără cerință clară"
STATE_AFTER_SALE = "După vânzare"  # the client already ordered: invoice, contract, delivery, web-shop order
STATE_NOT_A_REQUEST = "Nu e cerere de ofertă"
STATES = [STATE_COMPLETE, STATE_NO_OFFER, STATE_NO_REQUEST, STATE_AFTER_SALE, STATE_NOT_A_REQUEST]
# a client is expected only in these conversation types; internal mail and advertising have none
TYPES_WITH_CLIENT = {"client", "furnizor", "altele", ""}
FLAG_NO_CLIENT = "Client neidentificat"
FLAG_UNSURE = "Grupare nesigură"
FLAGS = [FLAG_NO_CLIENT, FLAG_UNSURE]
CONVERSATION_TYPES = {
    "client": "Client",
    "furnizor": "Furnizor (AKRO cumpără)",
    "intern": "Discuție internă AKRO",
    "marketing": "Reclamă sau ofertă nesolicitată",
    "altele": "Altele",
}
MATCH_REF = "referință"
MATCH_NAME = "de confirmat"
MATCH_SERVICE = "serviciu"
MATCH_NONE = "în afara nomenclatorului"
UNKNOWN = "necunoscut"
SAMPLE_SIZE = 20
SAMPLE_SEED = 22976  # fixed, so the check sample stays the same between runs

# --- reading the messages ---------------------------------------------------------------------------------

EXCLUDED_CLASSES = [
    (re.compile(r"^IPM\.(Schedule|Appointment)", re.I), "invitație de calendar"),
    (re.compile(r"^REPORT\..*\.(NDR|DR)$", re.I), "emailul nu a ajuns (notificare automată)"),
    (re.compile(r"^REPORT\..*IPN", re.I), "confirmare de citire"),
    (re.compile(r"^IPM\.Note\.Rules\.(OofTemplate|ReplyTemplate)", re.I), "răspuns automat"),
]
AUTO_REPLY_SUBJECT = re.compile(
    r"^(automatic reply|auto(matic)?[- ]?reply|răspuns automat|raspuns automat|out of office|abwesenheit|"
    r"automatyczna odpowied|risposta automatica|réponse automatique|respuesta automática|autosvar|"
    r"automatisch antwoord|absent)",
    re.I,
)
BOUNCE_SUBJECT = re.compile(
    r"^(delivery status notification|undeliverable|undelivered mail|mail delivery (failed|failure)|"
    r"nedistribuibil|returned mail|non remis|delivery has failed|failure notice)",
    re.I,
)
READ_RECEIPT_SUBJECT = re.compile(r"^(read|citit|gelesen|lu|przeczytano|letto):", re.I)
NO_REPLY_SENDER = re.compile(
    r"(^|[._-])(no-?reply|do-?not-?reply|mailer-daemon|postmaster|notifications?|newsletter)" r"([._-]|@)", re.I
)
SPAM_SUBJECT = re.compile(r"^\[spam\]|\[bitdefender", re.I)
# safety data sheets: mentioned in a message, named in an attachment, or an attachment that is one
SDS_MENTION = re.compile(
    r"fi[sș][aăe]? (cu date |de date )?de securitate|fi[sș]ele? de securitate|(?<![a-z])(m?sds|fds)(?![a-z])|"
    r"safety data sheet|sicherheitsdatenblatt|scheda di sicurezza|karta charakterystyki",
    re.I,
)
SDS_DOCUMENT = re.compile(
    r"fi[sș]a (cu|de) date de securitate|safety data sheet|sicherheitsdatenblatt|scheda (di|dei) dati di "
    r"sicurezza|karta charakterystyki|(regulamentul|regulation|regolamento) \((ce|ec|ue|eu)\) n[ro]\.? ?1907/2006",
    re.I,
)


# programs and scripts: phishing mails send them as "Order.tar" or "DHL form.zip"; the pages never link them
DANGEROUS_EXT = {
    "exe",
    "scr",
    "com",
    "pif",
    "bat",
    "cmd",
    "js",
    "jse",
    "vbs",
    "vbe",
    "wsf",
    "hta",
    "ps1",
    "msi",
    "lnk",
    "jar",
}
DANGEROUS_NAME = re.compile(
    rb"[^\\/\x00]{1,200}\.(?:" + "|".join(sorted(DANGEROUS_EXT)).encode() + rb")(?![a-z0-9])", re.I
)
ARCHIVE_EXT = {"zip", "tar", "tgz", "gz", "rar", "7z"}


def dangerous_member(path, ext):
    """The program or script an attachment is or carries (an archive holding an .exe), "" when there is none."""
    if ext in DANGEROUS_EXT:
        return path.name
    if ext not in ARCHIVE_EXT or not path.is_file():
        return ""
    try:
        if ext == "zip":
            names = zipfile.ZipFile(path).namelist()
        elif ext in ("tar", "tgz") or tarfile.is_tarfile(path):
            names = tarfile.open(path).getnames()
        else:  # gzip, rar and 7z keep the file names in plain text near the start (gzip: the original name)
            names = [n.decode("utf-8", "replace") for n in DANGEROUS_NAME.findall(path.read_bytes()[:65536])]
    except (OSError, zipfile.BadZipFile, tarfile.TarError):
        return ""
    found = next((n for n in names if n.rsplit(".", 1)[-1].lower() in DANGEROUS_EXT), "")
    stem = path.name.rsplit(".", 1)[0]  # a byte of the archive header can stick to the front of a scanned name
    return found[found.index(stem) :] if stem and stem in found else found


def load_messages(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    messages = data["messages"]
    for m in messages:
        m.setdefault("subject", "")
        m.setdefault("body", "")
        m.setdefault("attachments", [])
        m.setdefault("recipients", [])
        for a in m["attachments"]:
            danger = dangerous_member(HERE / "output" / a["path"], a.get("ext", "")) if a.get("path") else ""
            if danger:
                a.update(path="", reason=f"periculos: {danger}")
        m["from_email"] = (m.get("from_email") or "").lower()
        m["is_akro"] = domain(m["from_email"]) in AKRO_DOMAINS
        m["local_date"] = local_time(m.get("date", ""))
    return data["pst"], messages


def local_time(iso):
    if not iso:
        return ""
    dt = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")


def domain(address):
    return address.rsplit("@", 1)[-1].lower() if "@" in address else ""


def exclusion(m):
    """Why a message stays out of the conversations ("" = it goes in). Newsletters are decided later,
    per conversation, because only a conversation AKRO never answered counts as one."""
    if m.get("error"):
        return "mesajul nu s-a putut citi din PST"
    if m["folder"].split("/")[-1].lower() in ("spam", "junk email") or SPAM_SUBJECT.search(m["subject"]):
        return "spam"
    for pattern, reason in EXCLUDED_CLASSES:
        if pattern.search(m.get("class", "")):
            return reason
    if BOUNCE_SUBJECT.search(m["subject"]) or re.match(r"mailer-daemon@", m["from_email"]):
        return "emailul nu a ajuns (notificare automată)"
    if READ_RECEIPT_SUBJECT.search(m["subject"]):
        return "confirmare de citire"
    headers = m.get("headers", {})
    if AUTO_REPLY_SUBJECT.search(m["subject"]) or headers.get("auto-submitted", "").lower().startswith("auto-replied"):
        return "răspuns automat (de ex. plecat din birou)"
    return ""


def is_bulk(m):
    headers = m.get("headers", {})
    return bool(
        headers.get("list-unsubscribe")
        or headers.get("list-id")
        or headers.get("precedence", "").lower() in ("bulk", "list", "junk")
        or headers.get("auto-submitted", "").lower().startswith("auto-generated")
        or NO_REPLY_SENDER.search(m["from_email"])
    )


# --- new text vs. quoted text -----------------------------------------------------------------------------

QUOTE_HEADER_FROM = re.compile(r"^\*?(From|De la|De|Von|Od|Da|Van|Expéditeur|Expeditor|Feladó)\s*:\*?\s*\S", re.I)
QUOTE_HEADER_NEXT = re.compile(
    r"^\*?(Sent|Trimis|Date|Data|Gesendet|Wysłano|Wysłane|Inviato|Envoyé|Verzonden|Elküldve|To|Către|Catre|An|Do|"
    r"Subject|Subiect|Betreff|Temat|Oggetto|Objet|Onderwerp|Tárgy)\s*:",
    re.I,
)
QUOTE_SEPARATOR = re.compile(
    r"^(-{2,}\s*(original message|mesaj original|mesajul original|ursprüngliche nachricht|forwarded message|"
    r"mesaj redirecționat|mesaj redirectionat|wiadomość oryginalna|messaggio originale|message d'origine)"
    r"\s*-{0,}|_{20,})\s*$",
    re.I,
)
QUOTE_WROTE = re.compile(
    r"^(on|pe|în|in|am|le|el|il|w dniu|op|dnia)\b.{4,300}\b(wrote|a scris|schrieb|a écrit|escribió|ha scritto|"
    r"napisał|napisała|scrisese|schreef|írta)\s*:?\s*$",
    re.I,
)


def quote_start(body):
    """Offset where the quoted earlier messages start (len(body) when there are none)."""
    lines = body.split("\n")
    offset = 0
    for i, line in enumerate(lines):
        joined = f"{line} {lines[i + 1]}" if i + 1 < len(lines) else line
        if (
            QUOTE_SEPARATOR.match(line)
            or QUOTE_WROTE.match(line)
            or (QUOTE_WROTE.match(joined) and len(line) > 20)
            or (QUOTE_HEADER_FROM.match(line) and any(QUOTE_HEADER_NEXT.match(n) for n in lines[i + 1 : i + 6]))
            or line.startswith(">")
        ):
            return offset
        offset += len(line) + 1
    return len(body)


def squash(text):
    """Whitespace-insensitive, case-insensitive, no diacritics: how quotes are compared with the messages."""
    return re.sub(r"\s+", " ", fold(text)).strip()


# --- grouping into conversations --------------------------------------------------------------------------

SUBJECT_PREFIX = re.compile(
    r"^\s*((re|fw|fwd|tr|aw|wg|r|rif|i|odp|pd|sv|vs|ref|răsp\.?|rasp\.?|redirecționat|"
    r"antw|res|enc)\s*(\[\d+\])?\s*:\s*|\[(external|extern)\]\s*)+",
    re.I,
)


def normalized_subject(subject):
    return squash(SUBJECT_PREFIX.sub("", subject or ""))


def message_ids(text):
    return re.findall(r"<[^<>\s]+>", text or "")


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def external_addresses(m):
    found = [m["from_email"]] + [r["email"] for r in m["recipients"]]
    return {a for a in found if a and domain(a) not in AKRO_DOMAINS}


def group_conversations(messages):
    """Lists of message indexes: Outlook conversation id, then In-Reply-To/References, then (marked unsure)
    the subject without Re:/Fw: shared by the same participants."""
    uf = UnionFind(len(messages))
    by_guid, by_msgid = {}, {}
    for i, m in enumerate(messages):
        ci = m.get("conversation_index", "")
        if len(ci) >= 44:  # 1 reserved byte + 5 bytes time + 16 bytes conversation GUID
            guid = ci[12:44]
            if guid in by_guid:
                uf.union(by_guid[guid], i)
            else:
                by_guid[guid] = i
        for mid in message_ids(m.get("message_id", "")):
            by_msgid.setdefault(mid, i)
    for i, m in enumerate(messages):
        for mid in message_ids(m.get("in_reply_to", "")) + message_ids(m.get("references", "")):
            if mid in by_msgid:
                uf.union(by_msgid[mid], i)

    groups = collections.defaultdict(list)
    for i in range(len(messages)):
        groups[uf.find(i)].append(i)
    # fallback: groups with the same subject and at least one external participant in common
    unsure = set()
    by_subject = collections.defaultdict(list)
    for root, members in groups.items():
        subjects = {normalized_subject(messages[i]["subject"]) for i in members} - {""}
        for s in subjects:
            by_subject[s].append(root)
    for roots in by_subject.values():
        roots = sorted(set(roots))
        for a_pos, a in enumerate(roots):
            ext_a = set().union(*(external_addresses(messages[i]) for i in groups[a]))
            for b in roots[a_pos + 1 :]:
                ext_b = set().union(*(external_addresses(messages[i]) for i in groups[b]))
                if ext_a & ext_b and uf.find(a) != uf.find(b):
                    uf.union(a, b)
                    unsure.add(uf.find(a))
    final = collections.defaultdict(list)
    for i in range(len(messages)):
        final[uf.find(i)].append(i)
    unsure_roots = {uf.find(r) for r in unsure}
    out = []
    for root, members in final.items():
        members.sort(key=lambda i: (messages[i]["date"], i))
        out.append((members, root in unsure_roots))
    out.sort(key=lambda g: (messages[g[0][0]]["date"], g[0][0]))
    return out


# --- the other party --------------------------------------------------------------------------------------


def party_key(address):
    d = domain(address)
    return address if d in PUBLIC_DOMAINS else d


def counterparty(conv_messages):
    """(key, address list) of the client/supplier: the external domain that writes to AKRO most, else the
    one AKRO writes to (To before Cc). Personal addresses (gmail, yahoo...) are the person, by address."""
    votes = collections.Counter()
    addresses = collections.defaultdict(set)
    for m in conv_messages:
        if not m["is_akro"] and m["from_email"] and domain(m["from_email"]) not in AKRO_DOMAINS:
            key = party_key(m["from_email"])
            votes[key] += 10
            addresses[key].add(m["from_email"])
        for r in m["recipients"]:
            if r["email"] and domain(r["email"]) not in AKRO_DOMAINS:
                key = party_key(r["email"])
                votes[key] += 3 if (m["is_akro"] and r["field"] == "to") else 1
                addresses[key].add(r["email"])
    if not votes:
        return "", []
    key = votes.most_common(1)[0][0]
    return key, sorted(addresses[key])


def display_names(conv_messages, addresses):
    names = collections.Counter()
    wanted = set(addresses)
    for m in conv_messages:
        if m["from_email"] in wanted and m["from_name"] and "@" not in m["from_name"]:
            names[m["from_name"]] += 1
        for r in m["recipients"]:
            if r["email"] in wanted and r["name"] and "@" not in r["name"]:
                names[r["name"]] += 1
    return [n for n, _ in names.most_common()]


# --- offers -----------------------------------------------------------------------------------------------

# Odoo sale documents: the offer, and after acceptance the order confirmation or the proforma invoice
OFFER_TITLE = re.compile(
    r"^\s*(?P<kind>Ofert[aă]|Confirmare de comand[aă]|Factur[aă] proform[aă]|Proforma Invoice|Quotation)\s+#?\s*"
    r"(?P<number>S\d{4,6}(?:-\d+)?)\s*$",
    re.M,
)
DOC_KIND = {
    "oferta": "Ofertă",
    "confirmare de comanda": "Confirmare de comandă",
    "factura proforma": "Factură proformă",
    "proforma invoice": "Factură proformă",
    "quotation": "Ofertă",
}
# the English Odoo layout ("Quotation # S02926"): its numbers and dates are rewritten to the Romanian layout first
ENGLISH_NUMBER = re.compile(r"(?<![\d.,])(-?\d{1,3}(?:,\d{3})*)\.(\d{2,3})(?![\d.,])")
ENGLISH_DATE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
ENGLISH_WORDS = [
    ("Quotation Date:", "Data ofertă:"),
    ("Expiration:", "Expiră:"),
    ("Untaxed Amount", "Valoare fără taxe"),
    ("Payment terms:", "Metoda de plata:"),
    ("Delivery:", "Modul de livrare:"),
    ("DESCRIPTION", "DESCRIERE"),
    ("Expected:", "Termeni:"),
    ("Page:", "Pagina:"),
    ("VAT Exempt", "TVA scutit"),
]


def romanian_layout(text):
    for en, ro in ENGLISH_WORDS:
        text = text.replace(en, ro)
    text = ENGLISH_DATE.sub(lambda m: f"{m.group(2)}.{m.group(1)}.{m.group(3)}", text)  # MM/DD/YYYY
    return ENGLISH_NUMBER.sub(lambda m: f"{m.group(1).replace(',', '.')},{m.group(2)}", text)


OFFER_DATE = re.compile(
    r"Data [^:\n]{0,20}:\s+(?P<exp>Expiră:)?.*\n\s*(?P<date>\d{2}\.\d{2}\.\d{4})"
    r"(?:\s+(?P<expires>\d{2}\.\d{2}\.\d{4}))?"
)
AMOUNT = r"-?\d{1,3}(?:\.\d{3})*,\d{2}"
CURRENCY = r"(?:\s?(?P<cur>€|RON|EUR|USD|lei))?"
# "[01-008188] description 1,00 buc 2.271,12 [10,00] 2.271,12 €" (pdftotext output, single spaces)
LINE_TAIL = re.compile(
    rf"\s(?P<qty>\d+(?:\.\d{{3}})*,\d{{2,3}})\s(?P<uom>[^\d\s-][^\s]*(?:\s[^\d\s-][^\s]*)?)\s(?P<pu>{AMOUNT})"
    rf"(?:\s(?P<disc>\d+,\d{{2}}))?(?:\s\d+%\s[\d.,]+)?\s(?P<sum>{AMOUNT}){CURRENCY}\s*$"  # proformas: VAT % + VAT
)
# a line with only the amount (Odoo service lines without quantity): "... reglare instalatie 544,00 €"
LINE_AMOUNT_ONLY = re.compile(rf"(?:^|\s)(?P<sum>{AMOUNT}){CURRENCY}\s*$")
LINE_REF = re.compile(r"^\s*\[(?P<ref>[^\]]+)\]\s*(?P<desc>.*)$")
ODOO_REF = re.compile(r"\[(?P<ref>\d{2}-\d{6}|[A-Za-z]+_\d{3})\]")
# totals; on proformas they share their line with the payment terms or the bank accounts
TOTAL_LINE = re.compile(
    rf"(^\s*(TVA\b.*?|VAT\b.*?|\d+% VAT)|Valoare fără taxe|\bTotal|\b(TVA|VAT) \d+%)\s+{AMOUNT}", re.I
)
AKRO_VAT = "RO14205979"  # on the letterhead of AKRO's own documents; suppliers using Odoo have S-numbers too
TERMS = re.compile(
    r"^\s*(Modul de livrare|Metoda de plat[aă]|Termen(ul)? de plat[aă]|Condi[țt]ii de plat[aă]|"
    r"Termen(ul)? de livrare|Garan[țt]ie|Valabilitate[a]?|Condi[țt]ii de livrare|Transport)\s*:\s*"
    r"(?P<value>.+)$",
    re.I | re.M,
)
PAGE_NOISE = re.compile(
    r"^\s*(Str\. Zizinului|Tel: \+40|Pagina: \d|AKRO SRL\s*$|RO14205979|J2001000977088|"
    r"DESCRIERE\b|Subtotal\b|(PRICE|UNITAR)\s*$)",
    re.I,
)
SECTION = re.compile(r"^\s*\d{1,2}\.\s*(?P<title>[^\d\s][^\[\]]{2,120})$")


def to_float(text):
    return float(text.replace(".", "").replace(",", ".")) if text else None


def parse_offer(text):
    """Kind, number, dates, product lines, terms and total of an Odoo offer, order confirmation or proforma PDF
    (pdftotext output).
    A description wraps onto the following lines; text after a blank line belongs to the next product."""
    title = OFFER_TITLE.search(text)
    if not title or not re.match(rf"\s*AKRO SRL\s+{AKRO_VAT}", text):  # AKRO's letterhead, not a supplier's
        return None
    if title.group("kind") == "Quotation":
        text = romanian_layout(text)
        title = OFFER_TITLE.search(text)
    dates = OFFER_DATE.search(text)
    lines, current, pending, section, in_subtotal = [], None, [], "", False
    for raw in text[title.end() :].split("\n"):
        stripped = raw.strip()
        if re.match(r"^Termeni\s*:?", stripped):
            break
        if in_subtotal:  # a subtotal label wrapped onto the next line(s), up to its amount
            in_subtotal = not LINE_AMOUNT_ONLY.search(raw)
            continue
        if not stripped:
            # text followed by a blank line, not by an amount, is a heading over the next products
            if pending:
                section = " ".join(pending)
            current, pending = None, []
            continue
        if PAGE_NOISE.match(raw) or TOTAL_LINE.search(raw):
            in_subtotal = stripped.lower().startswith("subtotal") and not LINE_AMOUNT_ONLY.search(raw)
            current, pending = None, []
            continue
        tail = LINE_TAIL.search(raw)
        amount_only = None if tail else LINE_AMOUNT_ONLY.search(raw)
        if tail or (amount_only and (pending or LINE_REF.match(raw) or current is None)):
            match = tail or amount_only
            # a numbered heading right above the product ("5.Instalatie de filtrare") is the section
            while pending and SECTION.match(pending[0]):
                section = SECTION.match(pending.pop(0)).group("title").strip()
            head = " ".join(pending + [raw[: match.start()].strip()]).strip()
            ref_match = ODOO_REF.search(head)
            current = {
                "ref": ref_match.group("ref") if ref_match else "",
                "name": re.sub(r"\s+", " ", ODOO_REF.sub(" ", head, count=1)).strip(),
                "qty": to_float(tail.group("qty")) if tail else None,
                "uom": tail.group("uom") if tail else "",
                "price": to_float(tail.group("pu")) if tail else None,
                "discount": to_float(tail.group("disc")) if tail and tail.group("disc") else None,
                "amount": to_float(match.group("sum")),
                "currency": (match.group("cur") or "").replace("€", "EUR").replace("lei", "RON"),
                "section": section,
            }
            lines.append(current)
            pending = []
        elif LINE_REF.match(raw):
            current, pending = None, pending + [stripped] if pending and SECTION.match(pending[-1]) else [stripped]
        elif current is not None and not SECTION.match(raw):
            current["name"] = f"{current['name']} {stripped}"
        elif SECTION.match(raw):
            current, pending = None, [stripped]
        elif not re.match(r"^(Data ofertă|\d{2}\.\d{2}\.\d{4}\s)", stripped):
            pending.append(stripped)
    kind = DOC_KIND[fold(title.group("kind"))]
    # a proforma for an advance payment has one line "Plată în avans a 50,00%": not a product
    lines = [line for line in lines if not fold(line["name"]).startswith("plata in avans")]
    currency = next((line["currency"] for line in lines if line["currency"]), "")
    for line in lines:
        line["currency"] = line["currency"] or currency
    total = re.search(rf"(?:^|\s)Total\s+(?P<amount>{AMOUNT}){CURRENCY}", text, re.M)
    terms = [(m.group(1).strip(), m.group("value").strip()) for m in TERMS.finditer(text)]
    return {
        "kind": kind,
        "number": title.group("number"),
        "date": dates.group("date") if dates else "",
        "expires": dates.group("expires") if dates and dates.group("exp") and dates.group("expires") else "",
        "lines": lines,
        "terms": terms,
        "total": to_float(total.group("amount")) if total else None,
        "currency": ((total.group("cur") if total else "") or currency).replace("€", "EUR").replace("lei", "RON"),
    }


def load_odoo_offers(path):
    rows = read_xlsx_rows(path)
    header = [h.strip() for h in rows[0]]
    col = {h: i for i, h in enumerate(header)}
    offers = {}
    for row in rows[1:]:
        if not any(row):
            continue

        def get(h, row=row):
            return row[col[h]].strip() if col.get(h) is not None and col[h] < len(row) else ""

        number_ = get("Referință comandă")
        created = get("Data creării")
        try:  # Excel serial date
            created = (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(created))).strftime("%Y-%m-%d")
        except ValueError:
            pass
        offers[number_] = {
            "number": number_,
            "created": created,
            "client": get("Client"),
            "state": get("Stare"),
            "total": get("Total"),
            "total_eur": get("Total (EUR)"),
            "team": get("Echipa de vânzări"),
        }
    return offers


# --- nomenclature -----------------------------------------------------------------------------------------

SERVICE_WORDS = re.compile(
    r"\b(transport|livrare|ambalare|manopera|montaj|punere in functiune|pif|deplasare|"
    r"diurna|cazare|service|instruire|proiectare|discount|reducere|avans|garantie)\b"
)
STOP_WORDS = {"de", "si", "cu", "la", "pentru", "din", "in", "pe", "the", "and", "for", "with", "x", "tip", "mm"}


def tokens(text):
    return {t for t in re.findall(r"[a-z0-9]+(?:[.,/][a-z0-9]+)*", fold(text)) if t not in STOP_WORDS and len(t) > 1}


def load_nomenclature(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        products = list(csv.DictReader(f, delimiter=";"))
    by_ref, by_name = {}, {}
    for p in products:
        if p["Referință internă"]:
            by_ref.setdefault(p["Referință internă"].strip(), p)
        by_name.setdefault(squash(p["Nume"]), p)
    services = [p for p in products if p["Tip produs"] == "Service" or p["Categorie"].startswith("16-")]
    return products, by_ref, by_name, services


def match_product(line, nomenclature):
    """Links an offer line to the nomenclature: by internal reference, else by name (always "de confirmat"),
    service lines to the service products; nothing found -> outside the nomenclature."""
    products, by_ref, by_name, services = nomenclature
    ref = line["ref"]
    if ref and ref in by_ref:
        return MATCH_REF, by_ref[ref], ""
    name = squash(line["name"])
    is_service = bool(SERVICE_WORDS.search(name)) and not ref
    if is_service:
        if re.search(r"\b(reducere|discount)\b", name):  # discount lines go to the discount products only
            services = [p for p in services if re.search(r"\b(reducere|discount)\b", fold(p["Nume"]))] or services
        wanted = tokens(line["name"])
        best = max(
            services,
            key=lambda p: len(tokens(p["Nume"]) & wanted) / len(tokens(p["Nume"]) | wanted or {""}),
            default=None,
        )
        if best and tokens(best["Nume"]) & wanted:
            return MATCH_SERVICE, best, "Serviciu fără cod, legat automat de serviciul cu numele cel mai apropiat."
        return MATCH_SERVICE, None, "Serviciu fără cod; în nomenclator nu există un serviciu cu nume apropiat."
    if name in by_name:
        return (
            MATCH_NAME,
            by_name[name],
            "Același nume ca în nomenclator, dar "
            + ("cu alt cod decât cel din ofertă." if ref else "linia din ofertă nu are cod."),
        )
    # closest name by shared words; shown only as a candidate to confirm
    wanted = tokens(line["name"])
    if wanted:
        scored = ((len(wanted & tokens(p["Nume"])) / len(wanted | tokens(p["Nume"])), p) for p in products)
        score, best = max(scored, key=lambda s: s[0])
        if score >= 0.5:
            return MATCH_NAME, best, f"Produsul cu numele cel mai apropiat ({round(score * 100)}% din cuvinte comune)."
    reason = (
        f"Codul {ref} nu există în nomenclator."
        if ref
        else "Linia nu are cod și niciun produs din nomenclator nu are un nume apropiat."
    )
    return MATCH_NONE, None, reason


# --- conversations ----------------------------------------------------------------------------------------


def sds_mentions(conv_messages):
    """Where a conversation mentions a safety data sheet: in the new text of a message, in an attachment name,
    or an attachment whose first page is a safety data sheet."""
    hits = []
    for m in conv_messages:
        side = "AKRO" if m["is_akro"] else "partener"
        for match in SDS_MENTION.finditer(m["body"][: m["new_len"]]):
            context = m["body"][max(0, match.start() - 60) : match.end() + 60].replace("\n", " ").strip()
            hits.append({"message": m["id"], "date": m["local_date"], "side": side, "where": "text", "detail": context})
        for a in m["attachments"]:
            if SDS_MENTION.search(a["name"]) or SDS_DOCUMENT.search((a.get("text") or "")[:1500]):
                hits.append(
                    {
                        "message": m["id"],
                        "date": m["local_date"],
                        "side": side,
                        "where": "atașament",
                        "detail": a["name"],
                    }
                )
    return hits


def build_conversations(messages, odoo, nomenclature):
    """Conversations with their messages, party, offers (parsed and matched) and the excluded messages."""
    excluded = []
    kept = []
    for m in messages:
        m["exclusion"] = exclusion(m)
        (excluded if m["exclusion"] else kept).append(m)

    conversations = []
    for members, unsure in group_conversations(kept):
        conv_messages = [kept[i] for i in members]
        if not any(m["is_akro"] for m in conv_messages) and all(is_bulk(m) for m in conv_messages):
            for m in conv_messages:
                m["exclusion"] = "newsletter sau mesaj automat, fără răspuns de la AKRO"
                excluded.append(m)
            continue
        conversations.append({"messages": conv_messages, "unsure": unsure})

    seen_offer_texts = {}
    for nr, conv in enumerate(conversations, start=1):
        conv_messages = conv["messages"]
        first = conv_messages[0]
        conv["id"] = f"c{first['id'][1:]}"
        conv["nr"] = nr
        conv["subject"] = next((m["subject"] for m in conv_messages if m["subject"]), "(fără subiect)")
        key, addresses = counterparty(conv_messages)
        conv["party_key"], conv["party_addresses"] = key, addresses
        conv["party_names"] = display_names(conv_messages, addresses)
        for m in conv_messages:
            start = quote_start(m["body"])
            m["new_len"] = start
        conv["sds"] = sds_mentions(conv_messages)
        conv["offers"] = []
        for m in conv_messages:
            if not m["is_akro"]:
                continue
            for a in m["attachments"]:
                offer = parse_offer(a.get("text", "")) if a.get("ext") == "pdf" else None
                if not offer:
                    continue
                digest = hashlib.sha1(squash(a["text"]).encode()).hexdigest()
                offer.update(
                    {
                        "message": m["id"],
                        "sent": m["local_date"],
                        "file": a["name"],
                        "path": a["path"],
                        "digest": digest,
                        "resent": (offer["number"], digest) in seen_offer_texts,
                    }
                )
                seen_offer_texts.setdefault((offer["number"], digest), m["id"])
                for line in offer["lines"]:
                    kind, product, note = match_product(line, nomenclature)
                    line["match"] = kind
                    line["match_note"] = note
                    line["product"] = (
                        {
                            "ref": product["Referință internă"],
                            "name": product["Nume"],
                            "category": product["Categorie"],
                            "subcategory": product["Subcategorie"],
                        }
                        if product
                        else None
                    )
                odoo_row = odoo.get(offer["number"]) or odoo.get(offer["number"].split("-")[0])
                offer["odoo"] = odoo_row
                conv["offers"].append(offer)
        # versions: the same offer number sent again with a different content (offers only)
        versions = collections.defaultdict(list)
        for offer in conv["offers"]:
            base = (offer["kind"], offer["number"].split("-")[0])
            if offer["digest"] not in [o["digest"] for o in versions[base]]:
                versions[base].append(offer)
            offer["version"] = [o["digest"] for o in versions[base]].index(offer["digest"]) + 1
    return conversations, excluded


ANALYSIS_TEXT_LIMIT = 6000  # characters of new text per message given to the analysis
ANALYSIS_ATTACHMENT_LIMIT = 1500
ANALYSIS_QUOTE_LIMIT = 4000
FORWARD_SUBJECT = re.compile(r"^\s*(fw|fwd|tr|wg|i|redirecționat|redirectionat)\s*:", re.I)


def conversation_text(conv):
    """Plain-text dump of one conversation: header, parsed offers, messages and the client's attachments."""
    out = [f"\n{'=' * 100}\nCONVERSAȚIA {conv['id']} (nr. {conv['nr']}) | subiect: {conv['subject']}"]
    out.append(
        f"Partener (după adrese): {conv['party_key'] or '-'} {', '.join(conv['party_names'][:3])}"
        f" | grupare nesigură: {'da' if conv['unsure'] else 'nu'}"
    )
    for o in conv["offers"]:
        lines = "; ".join(
            f"[{line['ref'] or '-'}] {line['name'][:80]} x{line['qty']} {line['uom']}" for line in o["lines"][:15]
        )
        odoo_state = o["odoo"]["state"] if o["odoo"] else "nu e în lista Odoo"
        out.append(
            f"OFERTĂ {o['number']} v{o['version']} trimisă {o['sent']} în {o['message']} (Odoo: {odoo_state}): {lines}"
        )
    for i, m in enumerate(conv["messages"]):
        to = ", ".join(f"{r['name']} <{r['email']}>" for r in m["recipients"] if r["field"] == "to")
        cc = ", ".join(r["email"] for r in m["recipients"] if r["field"] == "cc")
        out.append(
            f"\n--- MESAJ {m['id']} | {m['local_date']} | {m['folder']} | "
            f"{'AKRO' if m['is_akro'] else 'EXTERN'}\nDe la: {m['from_name']} <{m['from_email']}>"
            f"\nCătre: {to}" + (f"\nCc: {cc}" if cc else "") + f"\nSubiect: {m['subject']}"
        )
        new = m["body"][: m["new_len"]].strip()
        out.append(new[:ANALYSIS_TEXT_LIMIT] + (" [...trunchiat]" if len(new) > ANALYSIS_TEXT_LIMIT else ""))
        quoted = m["body"][m["new_len"] :].strip()
        # the history before the first message (older than the PST) and forwarded mails are not
        # elsewhere in the conversation; later quotes repeat earlier messages
        if quoted and (i == 0 or FORWARD_SUBJECT.match(m["subject"])):
            out.append("[CITAT DIN MESAJE ANTERIOARE / REDIRECȚIONATE]\n" + quoted[:ANALYSIS_QUOTE_LIMIT])
        for a in m["attachments"]:
            if a["inline"]:
                continue
            is_offer = any(o["message"] == m["id"] and o["file"] == a["name"] for o in conv["offers"])
            desc = "ofertă Odoo, parsată mai sus" if is_offer else (a["reason"] or "text extras")
            out.append(f"[ATAȘAMENT: {a['name']} | {desc}]")
            # what AKRO sends (datasheets, drawings) is listed by name; what the client sends is read
            if a["text"] and not is_offer and not m["is_akro"]:
                out.append(a["text"][:ANALYSIS_ATTACHMENT_LIMIT])
    return "\n".join(out)


def write_batches(conversations, folder, size):
    """Plain-text dumps of the conversations, size per file, for reading and writing analiza/*.json."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("lot_*.txt"):
        old.unlink()
    for start in range(0, len(conversations), size):
        chunk = conversations[start : start + size]
        text = "\n".join(conversation_text(conv) for conv in chunk)
        (folder / f"lot_{start // size + 1:02d}.txt").write_text(text, encoding="utf-8")
    return (len(conversations) + size - 1) // size


# --- analysis (analiza/*.json) ----------------------------------------------------------------------------

OUTCOME_ACCEPTED = "acceptată"
OUTCOME_AKRO_DECLINED = "AKRO nu a ofertat"  # AKRO turned the request down (not in its range, no approval...)
OUTCOMES = [OUTCOME_ACCEPTED, "respinsă", "fără răspuns", OUTCOME_AKRO_DECLINED, UNKNOWN]


def sourced_items(entry):
    """Every {text, src, citat} item of one conversation analysis, with a label for error messages."""

    def walk(value, label):
        if isinstance(value, dict):
            if "src" in value and (value.get("src") or value.get("citat")):  # {"valoare": "necunoscut", "src": null}
                yield label, value
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    yield from walk(v, f"{label}.{k}")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                yield from walk(v, f"{label}[{i}]")

    yield from walk(entry, entry.get("conv", "?"))


def message_texts(m):
    texts = [m["body"]] + [a["text"] for a in m["attachments"] if a.get("text")]
    return [squash(t) for t in texts]


def check_analysis(entries, conversations):
    """Errors: unknown conversations, sources outside the conversation, quotes not found in the source message.
    An item that fails is dropped from the page - nothing is shown without a verified source."""
    by_id = {c["id"]: c for c in conversations}
    errors = []
    for entry in entries:
        conv = by_id.get(entry.get("conv"))
        if not conv:
            errors.append(f"{entry.get('conv')}: conversație necunoscută")
            continue
        if entry.get("tip") not in CONVERSATION_TYPES:
            errors.append(f"{conv['id']}: tip necunoscut {entry.get('tip')!r}")
        msgs = {m["id"]: m for m in conv["messages"]}
        for label, item in sourced_items(entry):
            m = msgs.get(item.get("src"))
            quote = squash(item.get("citat") or "")
            if not m:
                item["_error"] = f"sursa {item.get('src')} nu e în conversație"
            elif len(quote) < 3:
                item["_error"] = "citat lipsă"
            elif not any(quote in t for t in message_texts(m)):
                item["_error"] = f"citatul nu apare în {m['id']}: {item.get('citat')[:80]!r}"
            if item.get("_error"):
                errors.append(f"{label}: {item['_error']}")
        for req in entry.get("cereri", []):
            outcome = (req.get("rezultat") or {}).get("valoare")
            if outcome and outcome not in OUTCOMES:
                errors.append(f"{conv['id']}: rezultat necunoscut {outcome!r}")
    missing = sorted(set(by_id) - {e.get("conv") for e in entries}, key=lambda c: by_id[c]["nr"])
    return errors, missing


def load_analysis(folder):
    entries = []
    for path in sorted(Path(folder).glob("*.json")):
        entries.extend(json.loads(path.read_text(encoding="utf-8")))
    return entries


# --- records, states, clients -----------------------------------------------------------------------------


def clean_item(item, msgs):
    """A sourced item for the page: text, source message, its date and the quote; None if it failed the check."""
    if not item or item.get("_error") or not (item.get("src") or item.get("citat")):
        return None
    m = msgs.get(item["src"])
    return {
        "text": item.get("text") or "",
        "src": item["src"],
        "quote": item.get("citat") or "",
        "date": m["local_date"] if m else "",
        "extra": {k: item[k] for k in ("camp", "moment") if item.get(k)},
    }


def clean_list(items, msgs):
    return [c for c in (clean_item(i, msgs) for i in items or []) if c]


def company(odoo_client):
    """ "GRUP PRIMACONS SRL, Maria Ilie" -> "GRUP PRIMACONS SRL" (Odoo: company, contact person)."""
    return odoo_client.split(",")[0].strip()


def build_records(conversations, analysis):
    """One record per request (a conversation asking for two different things gives two linked records),
    one record for every other conversation. Each record gets its state and flags."""
    by_conv = {e["conv"]: e for e in analysis}
    records = []
    for conv in conversations:
        msgs = {m["id"]: m for m in conv["messages"]}
        entry = by_conv.get(conv["id"], {})
        conv["analysed"] = bool(entry)
        conv["type"] = entry.get("tip") if entry.get("tip") in CONVERSATION_TYPES else ("" if not entry else "altele")
        odoo_names = [company(o["odoo"]["client"]) for o in conv["offers"] if o["odoo"]]
        client_item = clean_item(entry.get("client"), msgs) if conv["type"] in TYPES_WITH_CLIENT else None
        conv["client_link"] = ""
        if conv["type"] not in TYPES_WITH_CLIENT:
            conv["client_name"], conv["client_source"] = "", ""
        elif odoo_names:
            conv["client_name"] = collections.Counter(odoo_names).most_common(1)[0][0]
            conv["client_source"] = "numele din oferta Odoo"
            conv["client_link"] = next(o["message"] for o in conv["offers"] if o["odoo"])
        elif client_item:
            conv["client_name"] = client_item["text"]
            conv["client_source"] = "numele găsit în emailuri"
        elif conv["party_key"] and domain(conv["party_key"]) in PUBLIC_DOMAINS and conv["party_names"]:
            conv["client_name"] = conv["party_names"][0]
            conv["client_source"] = "numele din adresa de email"
        else:
            conv["client_name"] = conv["party_key"]
            conv["client_source"] = "după domeniul adresei de email" if conv["party_key"] else ""
        conv["client_item"] = client_item
        conv["description"] = clean_item(entry.get("descriere"), msgs)

        requests = entry.get("cereri") or []
        if conv["type"] != "client" or not requests:
            requests = [None]
        numbers = [o["number"] for o in conv["offers"]]
        claimed = {n for r in requests if r for n in (r.get("oferte") or [])}
        for idx, req in enumerate(requests):
            rec = {
                "rid": conv["id"] if len(requests) == 1 else f"{conv['id']}-{idx + 1}",
                "conv": conv["id"],
                "nr": conv["nr"] if len(requests) == 1 else f"{conv['nr']}.{idx + 1}",
                "part": idx + 1,
                "parts": len(requests),
            }
            if req is None:
                rec.update(
                    {
                        "title": "",
                        "category": "",
                        "request": None,
                        "final": [],
                        "clarifications": [],
                        "phone": [],
                        "sds": [],
                        "offer_text": [],
                        "outcome": None,
                        "offers": numbers if conv["type"] == "client" else [],
                    }
                )
            else:
                wanted = [n for n in (req.get("oferte") or []) if n in numbers]
                if len(requests) == 1:  # a single request answers to every offer of the conversation
                    wanted = numbers
                elif idx == 0:  # offers no request claimed stay with the first one
                    wanted += [n for n in numbers if n not in claimed and n not in wanted]
                outcome = req.get("rezultat") or {}
                rec.update(
                    {
                        "title": req.get("titlu") or "",
                        "category": req.get("categorie") or "Altele / neclar",
                        "request": clean_item(req.get("cerinta"), msgs),
                        "final": clean_list(req.get("cerinte_finale"), msgs),
                        "clarifications": [
                            {
                                "question": clean_item(c.get("intrebare"), msgs),
                                "answer": clean_item(c.get("raspuns"), msgs),
                                "change": c.get("schimbare") or "",
                            }
                            for c in req.get("clarificari") or []
                            if clean_item(c.get("intrebare"), msgs) or clean_item(c.get("raspuns"), msgs)
                        ],
                        "phone": clean_list(req.get("telefon"), msgs),
                        "sds": clean_list(req.get("fisa_securitate"), msgs),
                        "offer_text": clean_list(req.get("oferta_in_text"), msgs),
                        "outcome": (
                            {"value": outcome.get("valoare"), **(clean_item(outcome, msgs) or {})}
                            if outcome.get("valoare") in OUTCOMES
                            else None
                        ),
                        "offers": list(dict.fromkeys(wanted)),
                    }
                )
            has_offer = bool(rec["offers"] or rec["offer_text"])
            accepted = (rec["outcome"] or {}).get("value") == OUTCOME_ACCEPTED
            if conv["type"] != "client":
                state = STATE_NOT_A_REQUEST
            elif accepted and not (rec["request"] and has_offer):
                # the offer predates these emails or never existed (web-shop order): the talk is about the order
                state = STATE_AFTER_SALE
            elif rec["request"]:
                state = STATE_COMPLETE if has_offer else STATE_NO_OFFER
            else:
                state = STATE_NO_REQUEST
            flags = []
            if conv["type"] in TYPES_WITH_CLIENT and not conv["party_key"] and not client_item:
                flags.append(FLAG_NO_CLIENT)
            if conv["unsure"]:
                flags.append(FLAG_UNSURE)
            rec.update({"state": state, "flags": flags, "has_offer": has_offer})
            records.append(rec)
    return records


def client_key(conv):
    if conv["type"] not in TYPES_WITH_CLIENT:
        return ""
    if conv["party_key"]:
        return conv["party_key"]
    if conv["client_item"]:
        return "nume:" + squash(conv["client_item"]["text"])
    return ""


# --- page and report --------------------------------------------------------------------------------------

STATE_PLURAL = {
    STATE_COMPLETE: "complete",
    STATE_NO_OFFER: "fără ofertă",
    STATE_NO_REQUEST: "fără cerință clară",
    STATE_AFTER_SALE: "după vânzare",
}


def attachment_note(reason):
    """extrage_pst.py's reason for an attachment without text, in words a reader understands."""
    if not reason:
        return ""
    if reason == "PDF fără text (scanat)":
        return "PDF scanat, textul nu se poate citi automat"
    if reason == "imagine":
        return "imagine, nu se citește automat"
    if reason.startswith("tip necitit"):
        return f"fișier {reason.split('(', 1)[-1].rstrip(')')}, nu se citește automat"
    if reason == "fără extensie":
        return "fișier fără extensie, nu se citește automat"
    if reason == "fără text":
        return "fișierul nu conține text"
    if reason.startswith("periculos: "):
        program = reason.split(": ", 1)[1].rsplit("/", 1)[-1]
        return f"atașament periculos: conține programul «{program}»; nu e inclus și nu trebuie deschis"
    if reason.startswith("eroare la citire"):
        return "fișierul nu s-a putut deschide"
    return reason


# numbers that tie conversations about the same deal together: AKRO's sale document (S02400, also written
# S2400), AKRO's purchase order to a supplier (P01380) and a client's SAP purchase order (4501270935)
TOPIC_KEY = re.compile(r"\b(S0\d{4}|S2\d{3}|P0\d{4}|4[45]\d{8})\b")
TOPIC_KEY_MAX_CONVS = 8  # a number quoted in more conversations than this is a reference, not a deal


def link_topics(conversations, odoo):
    """Groups conversations that share a deal number into topics: conv["topic"] is the id of the topic's first
    conversation and conv["topic_keys"] the numbers that link it. Conversations without a shared number stay alone."""
    known = {o["number"].split("-")[0] for c in conversations for o in c["offers"]} | {n.split("-")[0] for n in odoo}
    keys = {}
    for conv in conversations:
        found = {o["number"].split("-")[0] for o in conv["offers"]}
        for m in conv["messages"]:
            text = " ".join([m["subject"], m["body"], *(a["name"] for a in m["attachments"])])
            for key in TOPIC_KEY.findall(text):
                key = "S0" + key[1:] if key.startswith("S2") else key
                if not key.startswith("S") or key in known:  # an S-number only if it is a real AKRO document
                    found.add(key)
        keys[conv["id"]] = found
    uses = collections.Counter(k for found in keys.values() for k in found)
    uf = UnionFind(len(conversations))
    first = {}
    for i, conv in enumerate(conversations):
        for key in keys[conv["id"]]:
            if uses[key] > TOPIC_KEY_MAX_CONVS:
                continue
            if key in first:
                uf.union(first[key], i)
            else:
                first[key] = i
    for i, conv in enumerate(conversations):
        root = conversations[uf.find(i)]  # conversations are in date order, so the root is the earliest
        conv["topic"] = root["id"]
        conv["topic_keys"] = sorted(k for k in keys[conv["id"]] if uses[k] > 1 and uses[k] <= TOPIC_KEY_MAX_CONVS)


def page_data(pst_name, conversations, records, excluded, odoo):
    clients = {}
    for conv in conversations:
        key = client_key(conv)
        conv["client"] = key
        if not key:
            continue
        c = clients.setdefault(
            key, {"key": key, "names": collections.Counter(), "emails": set(), "types": set(), "convs": []}
        )
        c["names"][conv["client_name"]] += 1
        c["emails"].update(conv["party_addresses"])
        if conv["type"]:
            c["types"].add(conv["type"])
        c["convs"].append(conv["id"])
    client_list = [
        {
            "key": c["key"],
            "name": c["names"].most_common(1)[0][0] or c["key"],
            "emails": sorted(c["emails"]),
            "types": sorted(c["types"]),
            "convs": c["convs"],
        }
        for c in clients.values()
    ]
    messages = {}
    convs = []
    for conv in conversations:
        for m in conv["messages"]:
            messages[m["id"]] = {
                "date": m["local_date"],
                "folder": m["folder"],
                "akro": m["is_akro"],
                "from": f"{m['from_name']} <{m['from_email']}>" if m["from_email"] else m["from_name"],
                "to": ", ".join(r["name"] or r["email"] for r in m["recipients"] if r["field"] == "to"),
                "cc": ", ".join(r["name"] or r["email"] for r in m["recipients"] if r["field"] == "cc"),
                "subject": m["subject"],
                "body": m["body"],
                "newLen": m["new_len"],
                "att": [
                    {
                        "name": a["name"],
                        "path": a["path"],
                        "reason": attachment_note(a["reason"]),
                        "inline": a["inline"],
                    }
                    for a in m["attachments"]
                    if not a["inline"]
                ],
            }
        dates = [m["local_date"] for m in conv["messages"]]
        convs.append(
            {
                "id": conv["id"],
                "nr": conv["nr"],
                "subject": conv["subject"],
                "first": dates[0],
                "last": dates[-1],
                "client": conv["client"],
                "clientName": conv["client_name"],
                "clientSource": conv["client_source"],
                "clientItem": conv["client_item"],
                "clientLink": conv["client_link"],
                "type": conv["type"],
                "description": conv["description"],
                "unsure": conv["unsure"],
                "topic": conv["topic"],
                "topicKeys": conv["topic_keys"],
                "messages": [m["id"] for m in conv["messages"]],
                "sds": conv["sds"],
                "offers": [
                    {
                        k: o[k]
                        for k in (
                            "kind",
                            "number",
                            "version",
                            "date",
                            "expires",
                            "sent",
                            "message",
                            "file",
                            "path",
                            "lines",
                            "terms",
                            "total",
                            "currency",
                            "resent",
                        )
                    }
                    | {"odoo": o["odoo"]}
                    for o in conv["offers"]
                ],
            }
        )
    return {
        "pst": pst_name,
        "generated": datetime.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M"),
        "types": CONVERSATION_TYPES,
        "states": STATES,
        "flags": FLAGS,
        "clients": client_list,
        "convs": convs,
        "records": records,
        "messages": messages,
        "excluded": [
            {
                "id": m["id"],
                "date": m.get("local_date", ""),
                "folder": m.get("folder", ""),
                "from": m.get("from_email", ""),
                "subject": m.get("subject", ""),
                "reason": m["exclusion"],
            }
            for m in sorted(excluded, key=lambda m: m.get("date", ""))
        ],
    }


REPORT_HEADER = ["Secțiune", "Element", "Număr", "Detalii", "Conversații"]


def conv_numbers(nrs):
    return ", ".join(str(n) for n in sorted(set(nrs), key=lambda n: float(str(n).split(".")[0])))


def build_report(messages, conversations, records, excluded, odoo, errors, missing):
    rows = []
    add = lambda section, element, count="", details="", convs="": rows.append(  # noqa: E731
        [section, element, count, details, convs]
    )
    folders = collections.Counter(m["folder"] for m in messages)
    for folder, n in sorted(folders.items()):
        add("Mesaje citite din PST", folder, n)
    add("Mesaje citite din PST", "Total", len(messages))
    for reason, n in collections.Counter(m["exclusion"] for m in excluded).most_common():
        add("Mesaje excluse", reason, n)
    in_convs = sum(len(c["messages"]) for c in conversations)
    add("Mesaje în conversații", "Total", in_convs, f"în {len(conversations)} conversații")
    ok = in_convs + len(excluded) == len(messages)
    add(
        "Control",
        "în conversații + excluse = citite",
        in_convs + len(excluded),
        f"{in_convs} + {len(excluded)} = {in_convs + len(excluded)}; citite: {len(messages)} -> "
        + ("corect" if ok else "DIFERENȚĂ"),
    )

    by_conv = {c["id"]: c for c in conversations}
    for state in STATES:
        recs = [r for r in records if r["state"] == state]
        add(
            "Înregistrări pe stare",
            state,
            len(recs),
            f"în {len({r['conv'] for r in recs})} conversații",
            conv_numbers(r["nr"] for r in recs),
        )
    for flag in FLAGS:
        recs = [r for r in records if flag in r["flags"]]
        add(
            "Înregistrări pe stare",
            flag,
            len(recs),
            f"în {len({r['conv'] for r in recs})} conversații",
            conv_numbers(r["nr"] for r in recs),
        )
    for t, label in CONVERSATION_TYPES.items():
        convs = [c for c in conversations if c["type"] == t]
        add("Conversații pe tip", label, len(convs))
    add(
        "Conversații pe tip",
        "Total conversații / înregistrări",
        len(conversations),
        f"{len(records)} înregistrări (o conversație cu cereri diferite are câte o înregistrare pe cerere)",
    )

    # products: counted once per offer version, not per resend of the same PDF
    outside, to_confirm, services = collections.defaultdict(lambda: {"n": 0, "convs": [], "note": ""}), {}, {}
    for conv in conversations:
        for o in conv["offers"]:
            if o["resent"]:
                continue
            for line in o["lines"]:
                if line["match"] == MATCH_NONE:
                    item = outside[line["name"]]
                    item["n"] += 1
                    item["convs"].append(conv["nr"])
                    item["note"] = line["match_note"]
                elif line["match"] in (MATCH_NAME, MATCH_SERVICE):
                    key = (line["name"], (line["product"] or {}).get("ref", ""))
                    group = to_confirm if line["match"] == MATCH_NAME else services
                    item = group.setdefault(key, {"n": 0, "convs": [], "line": line})
                    item["n"] += 1
                    item["convs"].append(conv["nr"])
    for name, item in sorted(outside.items(), key=lambda kv: -kv[1]["n"]):
        add("Produse ofertate în afara nomenclatorului", name, item["n"], item["note"], conv_numbers(item["convs"]))
    for (name, _ref), item in sorted(to_confirm.items(), key=lambda kv: -kv[1]["n"]):
        p = item["line"]["product"]
        add(
            "Potriviri cu nomenclatorul de confirmat",
            name,
            item["n"],
            f"-> [{p['ref']}] {p['name']} ({item['line']['match_note']})",
            conv_numbers(item["convs"]),
        )
    for (name, _ref), item in sorted(services.items(), key=lambda kv: -kv[1]["n"]):
        p = item["line"]["product"]
        add(
            "Linii de serviciu legate după nume de produse service (de confirmat)",
            name,
            item["n"],
            f"-> [{p['ref']}] {p['name']}" if p else "niciun produs service potrivit",
            conv_numbers(item["convs"]),
        )

    for conv in conversations:
        for m in conv["messages"]:
            for a in m["attachments"]:
                if not a["inline"] and not a.get("text"):
                    add(
                        "Atașamente care nu se pot citi",
                        a["name"],
                        "",
                        f"{attachment_note(a['reason'])}; mesaj {m['id']} {m['local_date']}",
                        str(conv["nr"]),
                    )

    # the emails and Odoo tell different stories: a person has to look
    for r in records:
        conv = by_conv[r["conv"]]
        odoo_states = {o["odoo"]["state"] for o in conv["offers"] if o["number"] in r["offers"] and o["odoo"]}
        outcome = (r["outcome"] or {}).get("value")
        if (outcome == OUTCOME_ACCEPTED and odoo_states and odoo_states <= {"Anulat"}) or (
            outcome in ("respinsă", OUTCOME_AKRO_DECLINED) and "Comandă de vânzare" in odoo_states
        ):
            add(
                "Contradicții email / Odoo de verificat",
                conv["subject"],
                "",
                f"emailuri: {outcome}; Odoo: {', '.join(sorted(odoo_states))} ({', '.join(r['offers'])})",
                str(r["nr"]),
            )

    for conv in conversations:
        for hit in conv["sds"]:
            add(
                "Mențiuni de fișă de securitate",
                f"{hit['where']} ({hit['side']})",
                "",
                f"{hit['date']} · {hit['message']} · {hit['detail']}",
                str(conv["nr"]),
            )

    categories = collections.Counter(r["category"] for r in records if r["category"])
    for category, n in categories.most_common():
        add("Cereri pe categorie de produs", category, n)

    in_mail = {o["number"] for c in conversations for o in c["offers"]}
    in_mail_base = {n.split("-")[0] for n in in_mail}
    for number_, o in sorted(odoo.items()):
        if number_ not in in_mail and number_.split("-")[0] not in in_mail_base:
            add(
                "Oferte din lista Odoo fără email în PST", number_, "", f"{o['created']} · {o['client']} · {o['state']}"
            )
    for conv in conversations:
        for o in conv["offers"]:
            if not o["odoo"] and not o["resent"]:
                add(
                    "Oferte din emailuri care nu sunt în lista Odoo",
                    o["number"],
                    "",
                    f"{o['sent']} · {o['file']}",
                    str(conv["nr"]),
                )

    for e in errors:
        add("Analiză: surse respinse (informația nu apare în pagină)", e)
    for conv_id in missing:
        add("Analiză: conversații neanalizate", conv_id, "", by_conv[conv_id]["subject"], str(by_conv[conv_id]["nr"]))

    rng = random.Random(SAMPLE_SEED)
    sample = rng.sample(records, min(SAMPLE_SIZE, len(records)))
    sample_rows = [
        [
            r["nr"],
            by_conv[r["conv"]]["subject"],
            by_conv[r["conv"]]["client_name"],
            r["state"],
            ", ".join(r["flags"]),
            "",
            "",
            "",
        ]
        for r in sorted(sample, key=lambda r: float(str(r["nr"]).split(".")[0]))
    ]
    sample_header = [
        "Nr.",
        "Subiect",
        "Client",
        "Stare",
        "Semne",
        "Verificat de",
        "Data verificării",
        "Rezultat (corect / ce diferă)",
    ]
    return rows, sample_header, sample_rows


def write_page(data, path, summary, headline):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / "template_emailuri.html").read_text(encoding="utf-8")
    # the data goes in last, so an email text can never be mistaken for one of the other placeholders
    page = (
        page.replace("__SUMMARY_LINE__", html.escape(headline))
        .replace("__SUMMARY__", summary_html(summary))
        .replace("__NAV__", nav_html(path.name))
        .replace("/*__DATA__*/{}", payload)
    )
    path.write_text(page, encoding="utf-8")


def build_outputs(pst_name, messages, conversations, excluded, odoo, nomenclature, args):
    analysis = load_analysis(args.analiza)
    errors, missing = check_analysis(analysis, conversations)
    records = build_records(conversations, analysis)
    link_topics(conversations, odoo)
    data = page_data(pst_name, conversations, records, excluded, odoo)
    report, sample_header, sample_rows = build_report(messages, conversations, records, excluded, odoo, errors, missing)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    states = collections.Counter(r["state"] for r in records)
    in_convs = sum(len(c["messages"]) for c in conversations)
    summary = [
        ("Mesaje", [("Citite din PST", len(messages)), ("În conversații", in_convs), ("Excluse", len(excluded))]),
        (
            "Conversații",
            [
                ("Conversații", len(conversations)),
                ("Rânduri în listă (o cerere = un rând)", len(records)),
                ("Clienți și parteneri", len(data["clients"])),
            ],
        ),
        ("Stare", [(s, states[s]) for s in STATES] + [(f, sum(f in r["flags"] for r in records)) for f in FLAGS]),
    ]
    headline = " · ".join(
        [f"{number(len(conversations))} conversații", f"{number(len(messages))} mesaje"]
        + [f"{number(states[s])} {STATE_PLURAL[s]}" for s in STATES[:4]]
    )
    written = [out / name for name in ("emailuri.html", "raport_emailuri.csv", "raport_emailuri.xlsx")]
    write_page(data, written[0], summary, headline)
    write_csv(
        written[1],
        REPORT_HEADER,
        report
        + [[]]
        + [["Eșantion de verificare", *sample_header]]
        + [["Eșantion de verificare", *r] for r in sample_rows],
    )
    write_xlsx(written[2], [("Raport", REPORT_HEADER, report), ("Eșantion verificare", sample_header, sample_rows)])
    # the answers are written by hand; copied next to the page so their links to emailuri.html work
    answers = HERE / "raspunsuri_intrebari.html"
    if answers.exists():
        shutil.copyfile(answers, out / answers.name)

    print(summary_text(summary))
    if errors or missing:
        print(f"  ! analiză: {len(errors)} surse respinse, {len(missing)} conversații neanalizate (detalii în raport)")
    print(f"Gata. Pagina: {written[0]}")
    print(f"      Raportul: {written[1]}, {written[2]} (eșantionul de verificare în foaia a doua)")
    if answers.exists():
        print(f"      Răspunsurile la întrebări: {out / answers.name}")


def main():
    ap = argparse.ArgumentParser(
        description="Generează pagina cu analiza emailurilor (output/emailuri.html) și raportul "
        "(output/raport_emailuri.csv)."
    )
    ap.add_argument("--mesaje", default=str(HERE / "date" / "mesaje.json"), help="mesajele scrise de extrage_pst.py")
    ap.add_argument("--oferte", default=str(HERE / "Oferte Alex_Q3 2026.xlsx"), help="lista de oferte din Odoo (.xlsx)")
    ap.add_argument(
        "--nomenclator", default=str(HERE / "output" / "produse.csv"), help="nomenclatorul din genereaza.py"
    )
    ap.add_argument("--analiza", default=str(HERE / "analiza"), help="folderul cu analiza conversațiilor (*.json)")
    ap.add_argument("--out", default=str(HERE / "output"), help="unde se scriu pagina și raportul (implicit output)")
    ap.add_argument("--loturi", help="doar scrie conversațiile de analizat, în loturi, în acest folder")
    ap.add_argument("--marime-lot", type=int, default=40, help="conversații pe lot (implicit 40)")
    ap.add_argument("--verifica", nargs="+", help="doar verifică sursele din aceste fișiere de analiză")
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

    pst_name, messages = load_messages(args.mesaje)
    odoo = load_odoo_offers(args.oferte)
    nomenclature = load_nomenclature(args.nomenclator)
    conversations, excluded = build_conversations(messages, odoo, nomenclature)

    if args.loturi:
        n = write_batches(conversations, args.loturi, args.marime_lot)
        print(f"{len(conversations)} conversații în {n} loturi, în {args.loturi}")
        return
    if args.verifica:
        entries = [e for path in args.verifica for e in json.loads(Path(path).read_text(encoding="utf-8"))]
        errors, _ = check_analysis(entries, conversations)
        print(f"{len(entries)} conversații verificate, {len(errors)} erori")
        for e in errors:
            print(f"  ! {e}")
        sys.exit(1 if errors else 0)
    build_outputs(pst_name, messages, conversations, excluded, odoo, nomenclature, args)


if __name__ == "__main__":
    main()
