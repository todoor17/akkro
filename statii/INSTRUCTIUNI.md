# Ofertele pe tipuri de stații: instrucțiuni pentru un lot

Context: AKRO SRL (Brașov) vinde echipamente de tratare a apei și servicii. Vrem să vedem ce fel de stații
ofertează AKRO. Credem că sunt mai ales stații de dedurizare, dar tipurile **nu sunt stabilite dinainte**: le
găsești tu în oferte, iar pagina le arată așa cum ies.

Lotul (`date/loturi_statii/statii_<n>.txt`) are câte un bloc pentru fiecare ofertă trimisă unui client:

- `OFERTA <cheie> | client | trimisă | Odoo | conversații`: cheia e numărul Odoo (`S02518`). Pentru un preț dat
  direct în email, fără PDF, cheia e `email-<id rând>` (ex. `email-c2134404`);
- `RÂND ...`: analiza din Faza 2 a cererii (cerința, cerințele finale, clarificările, oferta în text, rezultatul);
- `PREȚURI ...`: liniile PDF-urilor Odoo (oferte, versiuni, confirmări de comandă), cu cod, cantitate și preț;
- după ofertele unei conversații urmează `CONVERSAȚIA ...`, conversația întreagă, mesaj cu mesaj.

## Ce scrii

Un fișier `statii/lot_<n>.json` (același număr ca lotul): o listă cu câte un obiect pentru FIECARE `OFERTA` din
lot, fără să sari vreuna. Textele sunt în română.

```json
[
  {
    "oferta": "S02518",
    "statii": [
      {"tip": "Stație de dedurizare + Ecomix", "text": "4 stații de dedurizare simplex de 250 L, cu vană Clack WS2 și by-pass",
       "src": "m2107620", "citat": "Statie de dedurizare simplex WS2 - 250L"}
    ],
    "continut": null
  },
  {
    "oferta": "S02679",
    "statii": [],
    "continut": "15 membrane de osmoză HSRO 390 FF, piese de schimb pentru o instalație existentă"
  }
]
```

### Ce e o stație

Un **echipament complet de tratare a apei, ofertat ca unitate**: are recipientul sau carcasa lui, mediul filtrant,
membrana sau lampa, și comanda (vană automată, tablou, controler), și funcționează singur după montaj. Exemple
posibile: stație de dedurizare, filtru automat multistrat, filtru de deferizare, filtru cu cărbune activ, instalație
de osmoză inversă, demineralizator, sistem UV, ozonator, stație de dozare/clorinare montată pe cadru, dedurizator
galvanic. Lista nu e închisă și nu e obligatorie: scrie ce vezi în ofertă.

O pompă dozatoare cu rezervor, lance și contor, ofertate pe linii separate, e stație („Stație de clorinare sau
dozare”) doar când AKRO le numește în ofertă sau în email stație, instalație, sistem sau kit; altfel sunt piese.

**Nu** sunt stații: piese de schimb și accesorii (vane, butelii goale, distribuitoare, transformatoare), consumabile
(rășină, nisip, cărbune, cartușe, membrane, sare, chimicale, lămpi UV de schimb), servicii (montaj, PIF, mentenanță,
analize), pompe dozatoare ofertate singure, aparate de măsură. O ofertă care are doar așa ceva primește
`"statii": []` și `continut` = o frază despre ce s-a ofertat.

### Câmpuri

- `oferta`: cheia din linia `OFERTA`, exact cum e scrisă.
- `statii`: câte un obiect pentru fiecare stație diferită din ofertă (ex. o stație de dedurizare ȘI un sistem UV
  = două obiecte; 4 stații de dedurizare identice = un obiect, cu numărul în `text`). Accesoriile unei stații
  (filtru Y, contor, by-pass, rezervor de sare) nu sunt stații separate. Dacă oferta are mai multe versiuni sau
  variante (ex. simplex sau duplex), scrie stațiile tuturor variantelor și spune în `text` că sunt variante.
  - `tip`: exact unul din tipurile din `statii/tipuri.json` (generatorul verifică). Dacă stația nu se potrivește
    cu niciunul, adaugă acolo un tip nou: `tip` (2–5 cuvinte, la singular, fără dimensiuni sau modele),
    `statie: true` și `definitie` (o propoziție pe înțelesul oricui). Tipurile au ieșit din prima citire a tuturor
    ofertelor, în care fiecare lot și-a ales singur numele; numele care spuneau același lucru au fost unite.
  - `text`: stația pe înțelesul oricui, cu ce o deosebește (simplex/duplex, volum de rășină sau debit, vană,
    aplicație), ca în ofertă.
  - `src` + `citat`: mesajul din care se vede stația și un fragment COPIAT EXACT din textul lui sau al unui
    atașament al lui (PDF-ul ofertei e atașamentul mesajului AKRO care îl trimite: id-ul `m...` din linia
    `OFERTĂ ... trimisă ... în m...`). 4–25 de cuvinte, o singură linie, fără „...”, fără corecturi. Cel mai bun
    citat e numele liniei din ofertă.
- `continut`: doar când `statii` e gol: ce conține oferta (o frază). Altfel `null`.

## Verificare (obligatoriu)

    python3 genereaza_statii.py --verifica statii/lot_<n>.json

Repară fiecare eroare și rulează din nou până ies 0 erori. De obicei citatul nu e copiat exact: copiază-l din nou,
mai scurt, dintr-o singură linie a mesajului sau a PDF-ului (textul PDF-ului e în `date/mesaje.json`, la
atașamentele mesajului).
