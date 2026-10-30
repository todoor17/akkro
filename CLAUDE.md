# AKRO: analiza datelor pentru agentul de ofertare

Proiect pentru clientul **AKRO SRL** (Brașov, akro.ro; în tichete și în numele folderului scris „AKKRO”). AKRO vinde
echipamente de tratare a apei (stații de dedurizare, filtre, osmoză, UV, pompe dozatoare, chimicale, mase filtrante) și
servicii. Scopul: să înțelegem din datele lor (nomenclator Odoo, emailuri, oferte, comenzi către furnizori) cum fac
ofertele, ca bază pentru un agent AI de ofertare. Tichetele vin din Trello (ex. 22976, 23023), pe faze.

`README.md` are detaliile fiecărei faze (regenerare, ce calculează scriptul, ce vine din analiză). Fișierele
`*/INSTRUCTIUNI.md` spun cum se scrie analiza fiecărei faze. Citește-le înainte să lucrezi la o fază.

## Fazele și paginile

Fiecare fază = un script `genereaza*.py` + un template HTML + (de la Faza 2) un folder cu analiza scrisă de mână/AI.
Toate paginile se scriu în `output/`, au același meniu (`PAGES` din `genereaza.py`) și se deschid cu dublu-click.

| Faza | Pagina | Script | Template | Analiza (scrisă) | Tichet / întrebare |
|---|---|---|---|---|---|
| 1 | `produse.html` (+ `produse.csv/.xlsx`, `raport.csv`) | `genereaza.py` | `template.html` | `fise_reguli.json`, `descrieri_categorii.json` | nomenclatorul standardizat + fișe tehnice lipsă |
| 2 | `emailuri.html` (+ `raport_emailuri.*`) | `extrage_pst.py`, `genereaza_emailuri.py` | `template_emailuri.html` | `analiza/lot_*.json` | conversațiile din PST: cerere, clarificări, ofertă; `raspunsuri_intrebari.html` (tichet 22976, scris de mână) |
| 3 | `reguli.html` | `genereaza_reguli.py` | `template_reguli.html` | `reguli/*.json`, `reguli/glosar.json`, `reguli/VERIFICARE.md` | regulile de ofertare („clientul cere X → AKRO întreabă Y → oferă Z”) |
| 4 | `statii.html`, `alamo.html` | `genereaza_statii.py` | `template_statii.html`, `template_alamo.html` | `statii/lot_*.json`, `statii/tipuri.json`, `alamo/lot_01.json` | ofertele pe tipuri de stații; cererile către furnizorul ALAMO |
| 5 | `componente.html` | `genereaza_componente.py` | `template_componente.html` | `componente/lot_*.json`, `componente/raspunsuri.json` | tichet 23023: din ce sunt făcute stațiile (cerință → soluție → comandă furnizor) |

Scripturile se importă între ele (Faza 5 refolosește funcții din 1–4): `genereaza_statii.py` importă din
`genereaza_emailuri.py` și `genereaza_reguli.py`; `genereaza_componente.py` din toate. Schimbările într-o fază timpurie
se propagă: regenerează toate paginile după ele.

## Regenerarea completă (ordinea contează)

```bash
cd ~/workspace/akkro-nomenclator
python3 genereaza.py "/mnt/c/Users/rczxc/Downloads/akro/produse/Produs (product.template) (1).xlsx"   # Faza 1, scrie output/produse.csv (citește și folderul Drive cu fișe, are nevoie de rețea)
# doar dacă s-a schimbat PST-ul (durează ~15 min; output/atasamente are ~550 MB):
#   docker build -t akkro-pst -f Dockerfile.pst .
#   docker run --rm --user "$(id -u):$(id -g)" -v "/mnt/c/Users/rczxc/Downloads/akro/email":/in:ro -v "$PWD":/work akkro-pst python3 extrage_pst.py /in/exportAI.pst
python3 genereaza_emailuri.py     # Faza 2
python3 genereaza_reguli.py       # Faza 3
python3 genereaza_statii.py       # Faza 4 (ambele pagini)
python3 genereaza_componente.py   # Faza 5
```

Fiecare script are și `--loturi <folder>` (scrie textul de citit pentru analiză, în `date/loturi*`) și
`--verifica <fișiere>` (verifică citatele dintr-un fișier de analiză; trebuie să iasă 0 erori).

## Unde sunt datele

- **Documentele primite de la client** (nu sunt în repo): `C:\Users\rczxc\Downloads\akro` =
  `/mnt/c/Users/rczxc/Downloads/akro`:
  - `email/exportAI.pst` (1,6 GB, 2.205 mesaje, 01.07–15.10.2026, 660 de conversații);
  - `produse/Produs (product.template) (1).xlsx` (exportul Odoo de produse), `produse/Oferte Alex_Q3 2026.xlsx`;
  - `Fise tehnice/` (copia folderului Drive cu fișe; fișele stațiilor DEC, BS-D2/T2, Ecomix, CR100 ...);
  - `Comanda_de_achizitie_Q3_202_6_(purchase.order)_(1)_(1).xlsx` (comenzile către ALAMO, T3 2026);
  - notițe `.docx` din ședințe (AM, IZA, Alisa), încă nefolosite.
- **În repo:** `Oferte Alex_Q3 2026.xlsx` și `Comanda de achizitie_Q3 2026.xlsx` (copii ale exporturilor Odoo; datele
  din Excel nu se editează niciodată de mână), `date/mesaje.json` (PST-ul extras: mesaje, destinatari, textul
  atașamentelor), `date/loturi*/` (textele de citit pentru analiză, regenerabile).
- **Folderul Drive cu fișe tehnice:** ID `1awNY200Ee6N5V21YT50wkgHcwc7k4Oka` (`DEFAULT_DRIVE_FOLDER` din `genereaza.py`);
  trebuie să rămână partajat cu link. Folderul Drive cu resursele tichetelor:
  https://drive.google.com/drive/folders/1lOL17JmqOOkcBTjBL6rLv_EuvZGKLnXY
- **Pachetul trimis clientului:** `C:\Users\rczxc\Downloads\AKRO_analiza_faze_1-5` (paginile + `atasamente/` doar cu
  fișierele spre care duc linkurile). Nu se actualizează singur: după regenerare se copiază paginile din nou.
- Site-ul furnizorului ALAMO WATER POLAND: https://alamowaterpoland.com/products/ (doar categorii, fără produse
  individuale).

## Regulile de lucru (le respectă toate fazele)

- **Nu se ghicește.** Fiecare informație scrisă la analiză are `src` (id-ul mesajului, `m...`) și `citat` (fragment
  COPIAT EXACT din textul mesajului sau al unui atașament al lui: 4–25 de cuvinte, o singură linie, fără „...”).
  Scriptul verifică citatele; ce nu se verifică nu apare în pagină și e listat la rulare. Ce lipsește se marchează
  („lipsește”, „de confirmat”, „indiciu”), nu se completează din presupuneri.
- **Ce calculează scriptul nu se scrie la analiză** (frecvențe, încrederea regulilor, prețuri, stări Odoo, legături
  automate). Monedele (EUR/RON) nu se adună și prețurile nu se mediază.
- **Textele sunt în română**, pe înțelesul oricui: propoziții întregi, fără simboluri în loc de cuvinte (`→`, `~`, `/`,
  `vs`), fără id-uri interne în texte (scrie „conversația 194”, numărul din `emailuri.html`). Termenii tehnici noi se
  adaugă în `reguli/glosar.json` (`termen`, `forme` = regex, `exact`, `explicatie`) și apar subliniați în toate paginile.
- În română nu se folosește niciodată „pleacă / a plecat / să plece”: pentru emailuri, oferte, comenzi se scrie
  „se trimite / s-a trimis”.
- **Paginile conțin date de clienți, prețuri și costuri: sunt documente interne.** Nu se publică (nici ca Artifact).
- Doar Python 3 standard library pe host (fără pip). Pe host nu există `pdftotext`, `openpyxl`, `ruff`:
  - text din PDF: imaginea Docker `akkro-pst` (are poppler-utils);
  - Excel: `read_xlsx_rows` din `genereaza.py`;
  - format/lint: `docker run --rm -u $(id -u):$(id -g) -v $PWD:/w -w /w ghcr.io/astral-sh/ruff:0.6.9 format --line-length 120 <fișier>`
    (și `check --line-length 120`); fișierele existente sunt curate cu aceste setări.
- Codul imită stilul existent: comentarii și docstring-uri în engleză, texte pentru utilizator în română, constante
  sus, funcții mici; template-urile au aceeași paletă, temă luminoasă/întunecată, coloane care se strâng, emailuri cu
  citatul subliniat. Un template nou se construiește din piesele lui `template_alamo.html`.
- Nu se testează paginile în browser din proprie inițiativă: se verifică doar sintaxa JS
  (`node --check` pe scriptul extras din pagină); utilizatorul deschide paginile.
- Proiectul nu e repo git separat (e un folder neurmărit în repo-ul `~/workspace`): nu se fac branch-uri sau commit-uri.

## Fluxul pentru o analiză nouă (orice fază)

1. `python3 genereaza_<faza>.py --loturi date/loturi_<faza>` scrie textele de citit;
2. se citește lotul (și, la nevoie, textul complet din `date/mesaje.json`) și se scrie JSON-ul după `INSTRUCTIUNI.md`;
3. `python3 genereaza_<faza>.py --verifica <fișier>` până la 0 erori (de obicei citatul nu e exact: în PDF-uri liniile
   se rup, ia un fragment mai scurt dintr-o singură linie);
4. se regenerează pagina (și celelalte, dacă s-a schimbat glosarul sau meniul).

## Ce știm despre date (util pentru fazele următoare)

- PST-ul: conversațiile se grupează după identificatorul Outlook, `In-Reply-To/References`, apoi subiect. Id-urile
  `c...` (conversații) și `m...` (mesaje) sunt stabile la o nouă extragere a aceluiași PST. Conversațiile despre
  aceeași afacere se leagă prin numerele comune (S0xxxx ofertă/comandă AKRO, P0xxxx comandă către furnizor, nr. SAP).
- Documentele Odoo din emailuri: oferte, confirmări de comandă, proforme (S0xxxx); liniile au `[Referință internă]`
  (cod din nomenclator, ex. `[13-001258]`). Starea ofertelor vine din `Oferte Alex_Q3 2026.xlsx` (doar T3 2026).
- Stațiile de dedurizare AKRO (seria DEC: `DEC <litri>/V` simplex, `/DUPLEX`, twin) sunt asamblate la Brașov din piese
  ALAMO. Oferta către client are o singură linie pentru stație; comanda AKRO către ALAMO („Comandă de achiziție -
  P0xxxx”, PDF cu text) are piesele cu cod furnizor + cod nomenclator; confirmarea ALAMO („Order SO…”) are prețuri EUR
  fără cod de nomenclator. Legătura comandă → ofertă: câmpul „Document sursă” din Excel-ul `purchase.order`.
- Fișele tehnice DEC nu au lista de piese, doar dimensiunile; diametrul × înălțimea coloanei (cm) corespund buteliei
  în țoli (34x140 → 13x54, 54x158 → 21x62, 61x183 → 24x72, 77x183 → 30x72). Fișe pe model se găsesc și ca atașamente în
  emailurile de ofertă.
- `CR100.pdf` din folderul de fișe conține și o fișă de securitate (pagina 11), deși `raspunsuri_intrebari.html` spune
  că doar Turbidex_SDS e fișă de securitate (de corectat dacă se revine la tichetul 22976).

## Starea la 30.10.2026

- Fazele 1–4: terminate și trimise (pachetul din Downloads, 28.10). Faza 3 reverificată integral (`reguli/VERIFICARE.md`).
- Faza 5 (tichet 23023): pagina făcută; analizate 4 stații (pilotul KDC S02518, Airbus S02613, Proconcord S02575 +
  Rominserv S02769), răspunsurile la cele 3 întrebări în `componente/raspunsuri.json`. Din 17 stații vândute, 13 nu au
  încă analiza componentelor; următorul candidat: Șoarș S02430 (filtre FDC/FCC, legate în Odoo de P01372). Proconcord
  rămâne cu lanț „parțial” (cererea clientului nu e în emailuri). Pachetul din Downloads conține și Faza 5 (copiat 30.10).
- Problemă cunoscută, preexistentă: în `raport_emailuri.csv` unele liste de numere de conversații ies în altă ordine la
  fiecare rulare (conținut identic).
