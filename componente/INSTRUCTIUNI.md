# Din ce sunt făcute stațiile: instrucțiuni pentru o stație vândută

Context: AKRO SRL (Brașov) asamblează stațiile de dedurizare și filtrele automate din piese cumpărate de la ALAMO WATER
POLAND: vane Clack, butelii, distribuitoare, rășini și mase filtrante, vase de saramură. Oferta către client are o
singură linie pentru stație (ex. `[13-001258] DEC 250/V`); comanda AKRO către ALAMO are piesele. Din cele două aflăm din
ce e făcută o stație și ce parametri ai cererii duc la ce piese.

Lotul (`date/loturi_componente/componente_<oferta>.txt`) are, pentru o stație vândută:

- `OFERTA ...` și `RÂND ...`: oferta și analiza din Faza 2 a cererii (cerința, cerințele finale, clarificările);
- `PREȚURI ...`: liniile PDF-urilor Odoo trimise clientului;
- `VÂNDUTĂ ...`: data vânzării, starea lanțului și ce lipsește din el;
- `COMANDA ...`: fiecare comandă către ALAMO legată de vânzare, cu felul legăturii (`legată în Odoo`, `numită în PDF-ul
  comenzii`, `legată în Faza 4, de confirmat`, `indiciu din perioadă`), liniile comenzii AKRO (`[cod nomenclator]
  [cod furnizor] nume | cantitate | grupă`) și ale confirmării ALAMO (cu prețul în EUR);
- `CONVERSAȚIA ...`: conversațiile cu clientul și cu ALAMO, mesaj cu mesaj.

Un `indiciu din perioadă` e doar o comandă din aceeași perioadă pe care nicio altă vânzare nu o explică. Îl folosești
numai dacă emailurile arată că piesele lui sunt pentru această stație (atunci îl treci la `comenzi`, cu o observație
care spune de unde se vede).

## Ce scrii

Un fișier `componente/lot_<n>.json`: o listă cu câte un obiect pe stație vândută analizată. Textele sunt în română.

```json
{
  "oferta": "S02518",
  "statii": 4,
  "cerinta": [
    {"camp": "tip echipament", "text": "4 stații simplex cu vană WS2 și 250 L de rășină.", "src": "m2107620",
     "citat": "STATIE DE DEDURIZARE SIMPLEX WS2-250 LITRI MF001502-4 buc"}
  ],
  "solutie": [
    {"camp": "model", "text": "DEC 250/V, simplex, 250 L rășină, vană Clack CI de 2\".", "src": "m2144164",
     "citat": "[13-001258] DEC 250/V - Statie dedurizare simplex, 250L rasina, vana Clack CI"}
  ],
  "comenzi": ["P01380"],
  "componente": [
    {"ref": "14-003079", "rol": "butelia de 21x62 țoli, în care stă rășina", "cantitate": 1, "unitate": "buc",
     "src": "m2147556", "citat": "[CN-2162-4] 21x62-4 [14-003079]"}
  ],
  "observatii": [
    {"text": "Nisipul suport nu se comandă de la ALAMO.", "src": "m2147556",
     "citat": "4 x simplex softeners - 250L each, with NHWBP and Clack Valve 2\" CI [ without sand]"}
  ]
}
```

### Câmpuri

- `oferta`: cheia ofertei din linia `OFERTA` (`S0xxxx`), exact cum e scrisă.
- `statii`: câte stații identice s-au vândut (KDC: 4). Cantitățile pe stație se împart la acest număr.
- `cerinta`: parametrii tehnici ceruți de client, câte unul pe obiect: `camp` ∈ `tip echipament`, `debit`, `capacitate`,
  `cantitate`, `racord`, `tensiune`, `calitate apă`, `aplicație`, `termen`, `loc livrare`, `buget`, `altele`. Citatul vine
  din emailurile vânzării (cu clientul sau cu ALAMO). Listă goală dacă cererea clientului nu e în emailuri: pagina
  marchează atunci lipsa, nu o completezi din emailurile AKRO.
- `solutie`: ce a ofertat AKRO: configurația (simplex, duplex, twin), modelul, volumul de rășină, vana, racordul,
  dimensiunile din fișa tehnică trimisă, livrarea. `camp` e un cuvânt liber (`configurație`, `model`, `racord`,
  `dimensiuni`, `livrare` ...).
- `comenzi`: comenzile către furnizor care sunt pentru această stație, din cele din lot.
- `componente`: piesele stației de pe acele comenzi, câte una pe cod. `ref` = codul din nomenclator de pe linia comenzii
  (generatorul verifică că există și că e pe una din `comenzi`); `rol` = ce face piesa în stație, pe înțelesul oricui;
  `cantitate` și `unitate` = pe o stație; `src` = mesajul AKRO care trimite PDF-ul comenzii; `citat` = linia din PDF.
  Piesele comandate pentru altceva (stoc, altă lucrare, alt echipament din aceeași ofertă) nu intră aici: le spui la
  `observatii`.
- `observatii`: ce merită știut despre drumul de la ofertă la comandă: când s-a comandat față de confirmarea clientului,
  ce a înlocuit sau nu avea ALAMO, ce piese din ofertă nu sunt pe comandă, ce piese de pe comandă nu sunt ale stației.
  Citatul poate veni din orice email.

Fiecare element are `src` (id-ul mesajului, `m...`) și `citat`: un fragment COPIAT EXACT din textul mesajului sau al
unui atașament al lui (PDF-ul ofertei sau al comenzii), 4–25 de cuvinte, o singură linie, fără „...”. Nu scrie id-uri
interne în texte și nu scrie prețuri (pagina le arată din PDF-uri).

## Răspunsurile la întrebări: `componente/raspunsuri.json`

O listă cu câte un obiect pentru fiecare întrebare din tichet, cu textul întrebării exact:

- `Ce componente formează o stație de dedurizare?`
- `De ce parametri ai cerinței depinde configurația?`
- `Ce se comandă de la furnizor pentru fiecare stație?`

`raspuns` e o listă de paragrafe; `dovezi` e o listă de `{src, citat, nota}` (`nota` = ce arată dovada). Fiecare
afirmație din răspuns trebuie să se sprijine pe o dovadă sau pe stațiile analizate. Când o concluzie vine din puține
stații, scrie asta.

## Verificare (obligatoriu)

    python3 genereaza_componente.py --verifica componente/lot_<n>.json componente/raspunsuri.json

Repară fiecare eroare și rulează din nou până ies 0 erori. De obicei citatul nu e copiat exact: în PDF-uri o linie se
rupe des (descrierea, apoi cantitatea și prețul), așa că ia un fragment mai scurt dintr-o singură linie a textului
(textul PDF-ului e în `date/mesaje.json`, la atașamentele mesajului).
