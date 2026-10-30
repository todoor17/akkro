# Analiza conversațiilor AKRO — instrucțiuni pentru un lot

Context: AKRO SRL (Brașov, akro.ro) vinde echipamente de tratare a apei (filtre, dedurizare, osmoză, UV,
pompe dozatoare, ozonatoare, chimicale, mase filtrante) și servicii (montaj, PIF, mentenanță). Lotul conține
conversații de email extrase din PST, câte un bloc `CONVERSAȚIA <id>` cu mesajele în ordine cronologică.
Pentru fiecare mesaj vezi textul NOU (citatele din mesajele anterioare au fost scoase). La primul mesaj și la
forward-uri apare și `[CITAT DIN MESAJE ANTERIOARE / REDIRECȚIONATE]` — e tot textul acelui mesaj (sursă validă).
`OFERTĂ Sxxxxx` = PDF Odoo trimis de AKRO (ofertă, confirmare de comandă sau proformă), deja parsat automat.
Mesajele foarte lungi sunt trunchiate în lot: când cererea inițială pare să lipsească, caut-o în textul complet
al mesajului din `date/mesaje.json`.
Textul atașamentelor primite de la client apare sub `[ATAȘAMENT: ...]` și e sursă validă pentru mesajul acela.

## Ce scrii

Un singur fișier JSON: o listă cu câte un obiect pentru FIECARE conversație din lot (nu sări niciuna).
Scrie textele în română. Nu ghici: ce nu reiese din emailuri nu se scrie (sau se scrie "necunoscut" acolo unde
schema o cere). Fiecare informație are sursă: `src` = id-ul mesajului (`m...`) din ACEEAȘI conversație, iar
`citat` = un fragment COPIAT EXACT din textul acelui mesaj (sau din textul unui atașament al lui), 4–25 de cuvinte,
fără „...” în mijloc, fără să-l reformulezi, fără să corectezi greșelile sau diacriticele. Citatul trebuie să
dovedească informația (nu „Buna ziua”).

```json
{
  "conv": "c2100932",
  "tip": "client",
  "client": {"text": "COMPANIA REGIONALA DE APA BACAU", "src": "m2100932", "citat": "COMPANIA REGIONALA DE APA BACAU"},
  "descriere": null,
  "cereri": [
    {
      "titlu": "Cărbune activ LG85 și nisip cuarțos 2-4 mm",
      "categorie": "14-Componente pentru filtre multistrat",
      "cerinta": {"text": "Cere ofertă pentru 1350 kg cărbune activ LG85 și 300 kg nisip cuarțos 2-4 mm.",
                  "src": "m2100932", "citat": "Carbune activ granulat LG85(0.6-2.4mm)pentru filtrarea apei-1350kg"},
      "cerinte_finale": [
        {"camp": "cantitate", "text": "1350 kg cărbune activ LG85 (0.6-2.4 mm)", "src": "m2100932", "citat": "Carbune activ granulat LG85(0.6-2.4mm)pentru filtrarea apei-1350kg"},
        {"camp": "cantitate", "text": "300 kg nisip cuarțos 2-4 mm", "src": "m2100932", "citat": "Nisip cuartos 2-4mm-300kg"}
      ],
      "clarificari": [],
      "telefon": [],
      "fisa_securitate": [],
      "oferte": ["S02532"],
      "oferta_in_text": [],
      "rezultat": {"valoare": "necunoscut", "text": null, "src": null, "citat": null}
    }
  ]
}
```

### Câmpuri

- `tip`: `client` (cineva cere/primește ofertă, comandă sau service de la AKRO, inclusiv licitații, firme de
  construcții, primării, persoane fizice), `furnizor` (AKRO cumpără: comenzi P0xxxx, cotații de la producători,
  transport, facturi primite, certificate de calitate de la furnizori), `intern` (doar oameni AKRO),
  `marketing` (ofertă nesolicitată, newsletter, recrutare, evenimente), `altele` (orice altceva).
- `client`: firma partenerului (din semnătură, din numele din ofertă, din domeniu) — pentru `client` și
  `furnizor`. Pentru o persoană fizică: numele persoanei. `null` dacă nu reiese.
- `descriere`: doar pentru `furnizor`/`intern`/`marketing`/`altele`: o frază despre ce e conversația, cu sursă
  (`{"text","src","citat"}`). Pentru acestea `cereri` = `[]`.
- `cereri`: pentru `client`. De obicei una. Dacă clientul cere lucruri diferite în aceeași conversație (ex. o
  stație de dedurizare ȘI lămpi UV, ofertate separat), fă câte o cerere pentru fiecare.
  - `titlu`: 3–10 cuvinte, ce se cere.
  - `categorie`: EXACT una din lista de mai jos.
  - `cerinta`: ce a cerut clientul INIȚIAL — `text` = o frază scurtă; citatul din mesajul clientului. Dacă
    cererea inițială nu se vede (ex. conversația începe cu oferta AKRO), `cerinta` = `null`.
  - `cerinte_finale`: cerințele după clarificări, câte una pe parametru: `camp` ∈ `tip echipament`, `debit`,
    `capacitate`, `cantitate`, `racord`, `tensiune`, `calitate apă`, `aplicație`, `termen`, `loc livrare`,
    `buget`, `altele`. Doar ce apare scris.
  - `clarificari`: în ordine cronologică; fiecare `{"intrebare": {text,src,citat} | null, "raspuns":
    {text,src,citat} | null, "schimbare": "ce s-a precizat sau modificat față de cererea inițială"}`.
    Întrebările pot fi puse de AKRO sau de client (ex. clientul cere detalii despre oferta trimisă).
    Propunerile AKRO (echipamentul ofertat, termenul AKRO) nu sunt cerințe ale clientului.
    Nu pune aici mesajele de follow-up fără conținut („Ne puteți da un feedback?” e follow-up, nu
    clarificare — dar dacă e singurul semn al rezultatului, folosește-l la `rezultat`).
  - `telefon`: discuții telefonice menționate în emailuri (`text` = ce s-a stabilit, dacă reiese).
  - `fisa_securitate`: orice mențiune de fișă de securitate / fișă cu date de securitate / FDS / SDS / MSDS /
    safety data sheet (în text sau ca nume de atașament) — `text` = cine o cere sau o trimite, pentru ce produs,
    și dacă e trimisă separat sau împreună cu fișa tehnică; `moment` ∈ `înainte de ofertă`, `odată cu oferta`,
    `după ofertă`, `fără ofertă`.
  - `oferte`: numerele ofertelor PDF (din liniile `OFERTĂ Sxxxxx`) care răspund la această cerere.
  - `oferta_in_text`: când AKRO dă prețul direct în corpul emailului (fără PDF Odoo): `{text,src,citat}`.
  - `rezultat`: `valoare` ∈ `acceptată` (comandă, confirmare, „vă rog facturați”), `AKRO nu a ofertat` (AKRO refuză:
    nu are produsul, nu are aviz, nu lucrează în domeniu), `respinsă` (clientul refuză, „am ales
    alt furnizor”, anulare), `fără răspuns` (AKRO a cerut feedback și clientul n-a mai răspuns în conversație),
    `necunoscut`. Cu sursă când nu e `necunoscut`.

### Categorii (folosește exact unul dintre texte)
01-Filtre impuritati · 08-Osmoza si filtrare pe membrane · 10-Ozonatoare · 11-Pompe de dozare ·
12-Chimicale pentru conditionare si intretinere · 13-Filtre multistrat diferite medii ·
14-Componente pentru filtre multistrat · 16-Prestari servicii · 21-Aparatura de analiza si control ·
23-Diverse materiale, consumabile · 25-Produse ocazionale unicate · 27-Uv · Altele / neclar
(Stații de dedurizare, filtre multimedia/ecomix/carbune = 13; rășini, nisip, cărbune, mase filtrante = 14;
sare pentru dedurizare, antiscalant, chimicale = 12;
cartușe și filtre mecanice = 01; clorinare/dozare = 11; mentenanță, PIF, montaj = 16.)

## Verificare (obligatoriu)

După ce scrii fișierul, rulează:

    python3 genereaza_emailuri.py --verifica analiza/<lot>.json

Repară fiecare eroare (de obicei citatul nu e copiat exact — copiază-l din nou, mai scurt, dintr-o singură
linie a mesajului) și rulează din nou până ies 0 erori. Nu șterge informația ca să scapi de eroare decât dacă
chiar nu are sursă.
