# Conversațiile cu ALAMO: instrucțiuni

Context: AKRO SRL (Brașov) vinde echipamente de tratare a apei. ALAMO WATER POLAND (`alamowaterpoland.com`) e
unul dintre furnizorii ei: AKRO îi cere oferte (preț, disponibilitate, date tehnice) și îi trimite comenzi
(`P0xxxx`, PDF-ul Odoo „Comandă de achiziție”). Vrem să vedem cererile către ALAMO și, unde se poate dovedi, ce
ofertă către un client a stat în spatele lor, ca să comparăm ce a cerut AKRO furnizorului cu ce a ofertat clientului.

Lotul `date/loturi_statii/alamo_01.txt` are fiecare conversație în care AKRO scrie către o adresă ALAMO, mesaj
cu mesaj, plus:

- `[TEXTUL ATAȘAMENTULUI TRIMIS DE AKRO ...]`: textul documentelor trimise de AKRO (comenzile de achiziție cu
  codurile interne AKRO între paranteze drepte, ex. `[14-001038]`);
- `CANDIDAȚI`: ofertele către clienți care au același cod AKRO ca o comandă din conversație și au fost trimise la
  cel mult 60 de zile de ea. Sunt doar indicii, calculate automat: un cod de rășină sau de transformator apare în
  multe oferte. NU sunt legături.

`date/loturi_statii/oferte_clienti.txt` are toate ofertele trimise clienților, cu liniile lor: acolo cauți oferta
care se potrivește cu o cerere către ALAMO.

## Ce scrii

Un fișier `alamo/lot_01.json`: o listă cu câte un obiect pentru FIECARE conversație din lot. Textele sunt în română.

```json
{
  "conv": "c2139044",
  "etichete": ["cerere de ofertă", "comandă"],
  "rezumat": {"text": "AKRO cere preț pentru butelii FRP de 24\" mai scurte; după oferta ALAMO trimite comanda P01372.",
              "src": "m2139044", "citat": "FRP pressure vessels 24"},
  "cereri": [
    {"text": "Preț și disponibilitate pentru butelii FRP de 24\" mai scurte decât 24x72", "src": "m2139044", "citat": "..."}
  ],
  "raspunsuri": [
    {"text": "ALAMO trimite oferta SQ000833: 400 de saci Pyrolox la 43,17 EUR sacul, ex works", "src": "m2100484", "citat": "..."}
  ],
  "legaturi": [
    {"oferta": "S02575", "text": "Comanda P01372 are aceleași filtre (2 cu Pyrolox, 2 cu cărbune activ, butelii 24x65) ca oferta S02575 pentru PROCONCORD, trimisă cu 2 săptămâni înainte.",
     "dovezi": [
       {"src": "m2145732", "citat": "2 x filters - 2\"CI clack - with pyrolux - tank 24x65", "nota": "ce comandă AKRO de la ALAMO"},
       {"src": "m21xxxxx", "citat": "...", "nota": "aceeași configurație în oferta către client"}
     ]}
  ]
}
```

### Câmpuri

- `conv`: id-ul conversației (`c...`) din linia `CONVERSAȚIA`.
- `etichete`: ce fel de conversație e, în ordinea în care apar, din: `cerere de ofertă` (AKRO cere preț,
  disponibilitate, termen sau date tehnice, înainte să comande), `comandă` (AKRO trimite sau modifică o comandă
  P0xxxx), `confirmare de comandă` (ALAMO confirmă comanda), `livrare` (expediere, packing slip, transport, status),
  `factură`, `altele`. Prima e cea mai importantă.
- `rezumat`: o frază despre conversație, cu sursă.
- `cereri`: ce cere AKRO de la ALAMO (produse, cantități, întrebări), câte un obiect pe cerere, cu sursa în mesajul
  AKRO. Pentru o comandă: ce comandă. Listă goală dacă AKRO nu cere nimic (ex. doar confirmă primirea).
- `raspunsuri`: ce răspunde ALAMO la cereri: preț, monedă, termen, disponibilitate, ce lipsește. Listă goală dacă
  ALAMO nu răspunde în conversație.
- `legaturi`: ofertele către clienți legate de conversație, **doar cu dovadă**. Pagina le arată toate ca „de
  confirmat”. O legătură are dovadă când:
  - conversația (sau un mesaj intern) pomenește clientul, proiectul sau numărul ofertei/comenzii clientului; sau
  - AKRO cere sau comandă de la ALAMO aceeași configurație (aceleași produse, în cantitatea potrivită) ca o ofertă
    trimisă clientului cu puțin înainte, iar data se potrivește. Un singur cod comun (rășină, transformator, coș de
    distribuție) NU ajunge.
  - `oferta`: cheia ofertei din `oferte_clienti.txt` (`S0xxxx` sau `email-...`).
  - `text`: de ce sunt legate, pe înțelesul oricui: ce se potrivește și ce diferă.
  - `dovezi`: cel puțin o dovadă din conversația ALAMO și, când legătura vine din potrivirea produselor, una din
    oferta clientului. `src` poate fi orice mesaj din PST (și cel care trimite PDF-ul ofertei către client), `citat`
    = fragment COPIAT EXACT din textul mesajului sau al unui atașament al lui (4–25 de cuvinte, o singură linie,
    fără „...”), `nota` = ce arată.
  Dacă nu găsești nicio dovadă, `legaturi` = `[]`. Nu ghici.

## Verificare (obligatoriu)

    python3 genereaza_statii.py --verifica alamo/lot_01.json

Repară fiecare eroare și rulează din nou până ies 0 erori.
