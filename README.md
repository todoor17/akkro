# Nomenclator produse AKKRO

Lista standardizată de produse a clientului, ca bază pentru agentul de ofertare: pagina HTML filtrabilă
și raportul cu fișele tehnice lipsă.

## Regenerare

```bash
python3 genereaza.py "Produs (product.template).xlsx"
```

Doar Python 3, fără pachete de instalat. Scriptul:

1. citește exportul Odoo: rândurile cu `Nume` sunt produse, rândurile gri de grupare doar se numără;
2. listează folderul Drive cu fișe tehnice (trebuie să rămână partajat cu link, altfel scriptul se oprește);
3. leagă fișele de produse după regulile din `fise_reguli.json`;
4. scrie în `output/`:
   - `produse.html`: pagina filtrabilă;
   - `produse.xlsx`: același tabel, cu filtre pe coloane; foaia a doua conține raportul;
   - `produse.csv`: același tabel, separator `;` și virgulă zecimală (se deschide direct în Excel);
   - `raport.csv`: raportul.

Opțiuni: `--drive-folder <ID>` pentru alt folder Drive, `--out <folder>` pentru alt loc de ieșire.

Toate fișierele din `output/` conțin costurile, deci sunt documente interne: nu se publică.

Toate paginile proiectului (`produse.html`, `emailuri.html`, `reguli.html`, `statii.html`, `alamo.html`,
`componente.html`) au sus
același meniu, cu linkuri spre celelalte. Lista e `PAGES` din `genereaza.py`. Linkurile sunt relative: paginile și
folderul `atasamente/` trebuie să stea în același folder. Pentru a trimite totul cuiva, se copiază cele șase pagini și
doar atașamentele spre care duc linkurile din ele.

Atașamentele periculoase din emailuri nu au link în pagini. Sunt programe sau scripturi, ori arhive care conțin unul,
cum ar fi „Order.tar” cu un `.exe` înăuntru, trimis prin phishing. Pagina le arată doar numele, cu nota „atașament
periculos”. Le recunoaște `dangerous_member` din `genereaza_emailuri.py`.

## Fișe tehnice: `fise_reguli.json`

Fiecare fișier din Drive are o intrare cu una sau mai multe potriviri. O potrivire are:

- `nume`: o expresie regulată căutată în numele curățat al produsului (fără diferență între majuscule și minuscule);
- `subcategorie` (opțional): restrânge potrivirea la o subcategorie, ex. `^01-011`;
- `tip`: `exact` (produsul primește status `cu fișă`) sau `de confirmat` (fișă de familie sau generică; produsul primește status `fișă de confirmat`);
- `nota` (opțional, pe potrivire sau pe fișier): motivul, afișat în raport și la hover pe link.

Un fișier care nu e fișă tehnică (ex. un chestionar) primește `"potriviri": []` și o `nota`; apare în raport
la `Fișe tehnice fără produs`, cu nota ca motiv.

Regulile pentru stațiile de dedurizare DEC și BS-D2/BS-T2 conțin lista de volume din tabelul fiecărei fișe;
un volum care nu e în tabel rămâne cu status `fișă de confirmat`.

Un fișier nou în Drive fără regulă apare în raport la `Fișe tehnice fără produs`. Ca să fie legat, se
adaugă o intrare aici și se rulează din nou scriptul. Datele din Excel nu se editează niciodată de mână.

## Raport (`raport.csv`, separator `;`)

| Secțiune | Ce conține |
|---|---|
| Produse fără fișă tehnică | aceleași produse ca filtrul `fără fișă` din pagină |
| Fișe tehnice fără produs | fișiere din Drive fără regulă sau a căror regulă nu potrivește nimic |
| Produse cu fișă de confirmat | perechi produs + fișă de familie/generică, cu motivul |
| Nume duplicate | toate rândurile cu același nume (după curățarea spațiilor) |
| Produse fără categorie | produsele din `All`, `All / Expenses`, `All / Deliveries` |
| Rânduri gri cu alt număr de produse | rândurile gri al căror număr din paranteză diferă de produsele de sub ele |

## Faza 2: analiza emailurilor (`emailuri.html`)

Pentru fiecare conversație din PST-ul AKRO, pagina arată ce a cerut clientul, clarificările și oferta trimisă,
cu link la mesajul sursă pentru fiecare informație.

### Regenerare

```bash
# 1. PST -> date/mesaje.json + output/atasamente/ (Docker: libpff nu se instalează pe host)
docker build -t akkro-pst -f Dockerfile.pst .
docker run --rm --user "$(id -u):$(id -g)" -v "<folderul cu pst-ul>":/in:ro -v "$PWD":/work akkro-pst \
    python3 extrage_pst.py /in/exportAI.pst

# 2. pagina și raportul (doar Python 3)
python3 genereaza_emailuri.py
```

Extragerea durează aproximativ 15 minute pentru 1,6 GB. Generatorul are nevoie și de:

- `output/produse.csv`: nomenclatorul scris de `genereaza.py` (Task 1);
- `Oferte Alex_Q3 2026.xlsx`: lista de oferte din Odoo (număr, client, stare); altă cale: `--oferte`;
- `analiza/*.json`: analiza conversațiilor (vezi mai jos).

Scrie în `output/`:

- `emailuri.html`: pagina, se deschide cu dublu-click; linkurile de atașamente merg spre `output/atasamente/`,
  deci folderul `output` se mută întreg;
- `raport_emailuri.csv`, `raport_emailuri.xlsx`: raportul (separator `;`); foaia a doua din xlsx e eșantionul
  de 20 de conversații pentru verificarea de mână, cu coloanele de completat;
- `raspunsuri_intrebari.html`: răspunsurile la cele două întrebări din tichet. Sunt scrise de mână în
  `raspunsuri_intrebari.html` din rădăcina proiectului; generatorul doar le copiază lângă pagină.

`output/` conține numai fișiere generate și se poate șterge oricând. Se reface în ordinea: `genereaza.py` (Task 1,
scrie `output/produse.csv`), `extrage_pst.py` (atașamentele), apoi `genereaza_emailuri.py`.

Toate conțin date despre clienți: documente interne, nu se publică.

### Ce face automat și ce vine din analiză

Automat (`genereaza_emailuri.py`), reproductibil la fiecare rulare:

- grupează mesajele în conversații: identificatorul Outlook de conversație, apoi `In-Reply-To`/`References`,
  apoi subiectul fără `Re:`/`Fw:` cu cel puțin un participant extern comun (marcat `Grupare nesigură`);
- exclude spam-ul, calendarul, notificările de livrare eșuată, răspunsurile automate și newsletterele la care
  AKRO nu a răspuns; apar în vederea `Mesaje excluse`, cu motivul;
- identifică partenerul după domeniul adresei (adresele personale gmail/yahoo... rămân persoana); numele firmei
  vine din lista de oferte Odoo, altfel din semnătură (analiză), altfel din domeniu;
- citește PDF-urile Odoo din mesajele trimise de AKRO: oferte, confirmări de comandă și proforme (număr, date,
  linii, condiții, total; proformele sunt facturi de avans, fără linii de produs). Leagă fiecare linie de
  nomenclator: după `Referință internă`; altfel după nume (mereu `de confirmat`); liniile de transport, manoperă,
  deplasare și reduceri, de produsele de tip service (tot după nume, deci tot `de confirmat`); restul
  `în afara nomenclatorului`. O confirmare de comandă sau o proformă contează ca ofertă trimisă;
- calculează stările: `Completă` / `Fără ofertă` / `Fără cerință clară` / `După vânzare` (clientul a comandat deja:
  factură, contract, livrare, comandă pe site) / `Nu e cerere de ofertă` (furnizori, intern, marketing) și semnele
  `Client neidentificat` (doar unde e de așteptat un client) și `Grupare nesigură`;
- leagă conversațiile despre aceeași afacere într-un subiect, prin numerele comune: documentul AKRO (S02400),
  comanda AKRO către furnizor (P01380) sau comanda SAP a clientului (4501270935). Un număr care apare în peste 8
  conversații e considerat referință generală și nu leagă. Pagina le arată grupate și cu fluxul în ordine
  cronologică;
- raportul are și secțiunea `Contradicții email / Odoo de verificat` (acceptată în emailuri, anulată în Odoo etc.).

Din analiză (`analiza/*.json`): tipul conversației, cererea inițială, cerințele finale, clarificările, discuțiile
telefonice, mențiunile de fișă de securitate, ofertele date direct în text și rezultatul. Fiecare element are
`src` (id-ul mesajului) și `citat` (fragment exact din mesaj). Generatorul verifică fiecare citat în mesajul
indicat; ce nu se verifică nu apare în pagină și e listat în raport.

Regulile după care se scrie analiza sunt în `analiza/INSTRUCTIUNI.md`. Pentru o conversație nouă sau după o nouă
extragere:

```bash
python3 genereaza_emailuri.py --loturi date/loturi           # textul conversațiilor, câte 40 pe fișier
python3 genereaza_emailuri.py --verifica analiza/lot_01.json  # verifică sursele unui fișier de analiză
```

Id-urile conversațiilor (`c...`) vin din id-ul primului mesaj din PST, deci rămân aceleași la o nouă extragere
a aceluiași PST.

## Faza 3: reguli de ofertare (`reguli.html`)

Pagina `reguli.html` arată regulile după care AKRO face ofertele: când clientul cere un anumit lucru, ce întreabă AKRO
și ce trimite în ofertă. Regulile sunt scoase numai din emailurile analizate în Faza 2. Fiecare are cel puțin un email
ca dovadă, cu fragmentul copiat exact din el.

### Regenerare

```bash
python3 genereaza_reguli.py
```

Scriptul are nevoie de aceleași fișiere ca `genereaza_emailuri.py` (emailurile extrase, nomenclatorul, lista de oferte
Odoo, analiza din Faza 2) și de regulile din `reguli/`. Scrie `output/reguli.html`, care se deschide cu dublu-click.
Linkurile „conv. N” deschid conversația în `output/emailuri.html`, deci cele două pagini trebuie să stea în același
folder. Pagina conține date despre clienți: e document intern, nu se publică.

### Ce e scris la analiză și ce calculează scriptul

Scrise la analiză, în `reguli/`:

- un fișier pe categorie de produse (`01.json`, `13.json` ...) și `general.json` pentru regulile care țin de toate
  categoriile (plată, livrare, documente). Fiecare regulă spune când se aplică, ce întreabă AKRO, ce oferă (produse cu
  codul din nomenclator, servicii, documente, condiții), în ce emailuri se vede și, unde e cazul, ce emailuri o
  contrazic. Cum se scriu: `reguli/INSTRUCTIUNI.md`;
- `glosar.json`: explicațiile termenilor tehnici și ale prescurtărilor (PIF, racord, UVT ...). Pagina subliniază
  termenii în reguli și arată explicația; un termen nou se adaugă aici.

`reguli/VERIFICARE.md` descrie ultima verificare a regulilor pe textul complet al conversațiilor: ce s-a verificat,
rezultatul și, pe fiecare regulă, ce s-a corectat și de ce.

Calculat de script la fiecare rulare:

- verifică fiecare dovadă: emailul există în conversația indicată și fragmentul citat chiar apare în el. Ce nu se
  verifică nu apare în pagină și e afișat la rulare. O regulă rămasă fără nicio dovadă nu apare;
- din conversațiile fără ofertă sau despre o comandă deja făcută acceptă doar dovezi pentru întrebările puse de AKRO,
  nu pentru ce oferă AKRO;
- verifică dacă există în nomenclator codurile produselor;
- numără în câte afaceri diferite apare regula (conversațiile legate prin același număr de document AKRO, de exemplu
  oferta și comanda trimisă separat, se numără o dată) și stabilește cât de sigură e: „sigură” (cel puțin 3 afaceri și
  nicio contradicție), „indiciu” (1 sau 2 afaceri), „contradictorie” (unele conversații arată altceva; ambele variante
  rămân în pagină);
- arată, pentru fiecare conversație-dovadă, prețurile din ofertă la produsele regulii, în moneda ofertei. Nu face medii.

### Pentru o analiză nouă

```bash
python3 genereaza_reguli.py --loturi date/loturi_reguli   # scrie, pe categorii, textul de citit: analiza din Faza 2, prețurile și emailurile
python3 genereaza_reguli.py --verifica reguli/13.json     # verifică dovezile dintr-un fișier de reguli
```

## Faza 4: ofertele pe tipuri de stații (`statii.html`) și cererile către ALAMO (`alamo.html`)

`statii.html` arată ce tipuri de stații ofertează AKRO și, pentru fiecare tip, ofertele trimise. Pentru fiecare ofertă
arată ce a cerut clientul, clarificările, cerințele finale, oferta trimisă (cu PDF-ul) și toate emailurile cu clientul.
`alamo.html` arată, în ordine cronologică, conversațiile în care AKRO scrie furnizorului ALAMO WATER POLAND și, unde
există dovadă, ofertele către clienți legate de ele.

Fiecare pagină are o secțiune „Cum se citește pagina”. Termenii tehnici (duplex, vană Clack, PIF, EXW ...) sunt
subliniați și explicați la trecerea cu mouse-ul, iar la sfârșitul ofertei sau conversației deschise sunt toți scriși, cu
explicația lor. Explicațiile vin din glosarul din Faza 3, `reguli/glosar.json`; un termen nou se adaugă acolo și apare
în toate paginile (altă cale: `--glosar`).

### Regenerare

```bash
python3 genereaza_statii.py
```

Scriptul are nevoie de aceleași fișiere ca `genereaza_emailuri.py` și de analizele din `statii/` și `alamo/`. Scrie în
`output/` cele două pagini, care se deschid cu dublu-click. Linkurile spre PDF-uri și atașamente merg în
`output/atasamente/`, iar cele spre conversații în `emailuri.html`, deci folderul `output` se mută întreg. Paginile conțin
date despre clienți și prețuri: sunt documente interne, nu se publică.

### Ce e scris la analiză și ce calculează scriptul

Scrise la analiză:

- `statii/lot_*.json`: pentru fiecare ofertă trimisă unui client, stațiile pe care le conține și tipul lor, cu emailul și
  fragmentul copiat exact din el (de obicei linia din PDF-ul ofertei). O ofertă doar cu piese, consumabile sau servicii
  are lista goală și o frază despre ce conține. Cum se scriu: `statii/INSTRUCTIUNI.md`;
- `statii/tipuri.json`: tipurile de stații, cu o definiție pe înțelesul oricui. Tipurile nu au fost stabilite dinainte:
  au ieșit din prima citire a tuturor ofertelor, apoi numele care spuneau același lucru au fost unite;
- `alamo/lot_01.json`: pentru fiecare conversație cu ALAMO, eticheta (cerere de ofertă, comandă, confirmare de comandă,
  livrare, factură, altele), ce cere AKRO, ce răspunde ALAMO și ofertele către clienți legate, fiecare cu dovezi. Cum se
  scriu: `alamo/INSTRUCTIUNI.md`.

Calculat de script la fiecare rulare:

- ofertele trimise: o ofertă e un număr de document Odoo (cu versiunile, confirmarea de comandă și proforma lui) găsit
  într-o conversație cu un client, sau un preț scris direct în email. Valoarea e totalul cu TVA al ultimei versiuni
  trimise, în moneda ei (EUR sau RON; monedele nu se adună). Prețurile de pe liniile ofertei sunt fără TVA. Starea vine din lista de oferte Odoo; lista primită acoperă trimestrul 3 2026, așa că o ofertă care lipsește
  din ea apare ca „nu e în lista Odoo”;
- emailurile unei oferte: toate conversațiile cu clientul legate prin același număr de document (ca în `emailuri.html`),
  în ordine cronologică. Un email găsit de două ori în PST (Sent Items și Cc în Inbox) apare o dată;
- conversațiile cu ALAMO: cele în care AKRO trimite cel puțin un email la o adresă `alamowaterpoland.com`. Un email
  către ALAMO e un email trimis de pe o adresă AKRO care are o adresă ALAMO la Către sau Cc; trimis la mai mulți oameni
  de la ALAMO, se numără o dată;
- candidații de legătură pentru analiză: ofertele către clienți care au un cod AKRO comun cu o comandă către ALAMO și sunt
  trimise la cel mult 60 de zile de ea. Pagina arată doar legăturile confirmate cu dovezi la analiză, toate marcate
  „de confirmat”;
- verifică fiecare citat în emailul indicat. Ce nu se verifică nu apare în pagini și e afișat la rulare.

### Pentru o analiză nouă

```bash
python3 genereaza_statii.py --loturi date/loturi_statii              # ofertele, conversațiile ALAMO și indexul ofertelor
python3 genereaza_statii.py --verifica statii/lot_01.json alamo/lot_01.json   # verifică citatele și tipurile
```

## Faza 5: din ce sunt făcute stațiile (`componente.html`)

`componente.html` arată stațiile vândute de AKRO și, pentru fiecare, drumul de la cerere la furnizor: ce a cerut clientul,
ce i-a ofertat AKRO și ce a comandat AKRO de la ALAMO WATER POLAND ca să construiască stația, trei blocuri alăturate, cu
emailurile în ordine cronologică. Din comparația lor ies componentele unei stații (cod din nomenclator, rol, în câte
stații apar) și răspunsurile scrise la cele trei întrebări din tichetul 23023, cu dovezi.

### Regenerare

```bash
python3 genereaza_componente.py
```

Scriptul are nevoie de aceleași fișiere ca `genereaza_statii.py` și de lista comenzilor de achiziție din Odoo,
`Comanda de achizitie_Q3 2026.xlsx` (exportul `purchase.order`, atașat la tichet; altă cale: `--comenzi`). Scrie
`output/componente.html`, care se deschide cu dublu-click. Linkurile spre PDF-uri merg în `output/atasamente/`, iar cele
spre conversații în `emailuri.html`, `statii.html` și `alamo.html`, deci folderul `output` se mută întreg. Pagina conține
date despre clienți și prețuri: e document intern, nu se publică.

### PDF-urile comenzilor se citesc automat

Da. PDF-urile comenzilor AKRO către ALAMO („Comandă de achiziție - P0xxxx”) și ale confirmărilor ALAMO („Order
SO…”) au text, nu sunt scanate, iar `extrage_pst.py` îl scoate deja în `date/mesaje.json`. Pe o linie a comenzii AKRO
sunt codul furnizorului, descrierea, codul din nomenclator, data și cantitatea; scriptul le citește și când descrierea
se rupe pe mai multe rânduri în jurul datei. Confirmarea ALAMO are codul ALAMO, cantitatea și prețul în EUR, dar nu și
codul din nomenclator, așa că se compară cu comanda AKRO doar după descriere. Lista Odoo are 18 comenzi către ALAMO în
trimestrul 3; PDF-ul a 8 dintre ele nu e în emailuri (cererile de ofertă „CdO” rămase în Odoo și P01229, P01502), deci la
ele se cunoaște doar rândul din listă. Pagina arată numerele exacte la „Comenzile către ALAMO”.

### Ce e scris la analiză și ce calculează scriptul

Scrise la analiză, în `componente/`:

- `lot_*.json`: pentru stațiile analizate, cerința tehnică a clientului, soluția ofertată, comenzile care sunt pentru
  stație, piesele stației cu rolul și cantitatea pe stație, și observațiile, fiecare cu emailul și fragmentul copiat
  exact (piesele, din PDF-ul comenzii). Cum se scriu: `componente/INSTRUCTIUNI.md`. Pilotul: KDC (S02518), Airbus
  (S02613), Proconcord (S02575) și Rominserv (S02769), a cărei comandă către ALAMO numește oferta clientului;
- `raspunsuri.json`: răspunsurile la cele trei întrebări din tichet, cu dovezi.

Termenii noi (DLFC, saramură, distribuitor) sunt în glosarul din Faza 3, `reguli/glosar.json`.

Calculat de script la fiecare rulare:

- comenzile către ALAMO: rândurile din lista Odoo și comenzile găsite doar în emailuri, cu liniile ultimei versiuni a
  comenzii AKRO trimise și cu confirmările ALAMO;
- stațiile vândute: ofertele cu cel puțin o stație (din `statii/`) pe care clientul le-a comandat: „Comandă de vânzare” în
  Odoo, o confirmare de comandă trimisă sau o comandă către furnizor făcută pentru ele;
- legătura vânzare – comandă către furnizor, de la cea mai sigură la cea mai slabă: „Document sursă” din lista Odoo;
  numărul ofertei scris în PDF-ul comenzii; legătura din Faza 4 (`alamo/`, de confirmat); pentru stațiile asamblate din
  butelie, vană și mediu filtrant, comenzile din aceeași perioadă (30 de zile înainte, 60 după vânzare) pe care nicio altă
  vânzare nu le explică, arătate doar ca indicii;
- lanțul fiecărei stații (`complet`, `parțial`, `fără comandă`) și ce lipsește din el, scris, nu ghicit;
- tabelul componentelor: pentru fiecare cod, numele și grupa din nomenclator, rolurile și în câte stații apare;
- verifică fiecare citat în emailul indicat și fiecare cod de piesă în nomenclator și pe comenzile stației. Ce nu se
  verifică nu apare în pagină și e afișat la rulare.

### Pentru o analiză nouă

```bash
python3 genereaza_componente.py --loturi date/loturi_componente   # câte un fișier de citit pe stație vândută
python3 genereaza_componente.py --verifica componente/lot_01.json componente/raspunsuri.json
```
