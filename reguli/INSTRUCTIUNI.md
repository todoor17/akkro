# Reguli de ofertare AKRO: instrucțiuni pentru o categorie

Context: AKRO SRL (Brașov) vinde echipamente de tratare a apei și servicii. O **regulă de ofertare** spune cum
ajunge AKRO de la ce cere clientul, prin clarificările pe care le cere, la oferta trimisă: „când clientul cere X,
AKRO întreabă Y și oferă Z”. Nu sunt reguli tehnice de proiectare și nu vin din cunoștințe generale: o regulă
există doar dacă se vede în conversații.

Lotul (`date/loturi_reguli/reguli_<categorie>_<n>.txt`) are, pentru fiecare cerere a categoriei:

- `RÂND ...` (o cerere a clientului; o conversație cu două cereri diferite are două rânduri): analiza din Faza 2,
  adică cerința, cerințele finale, clarificările, fișa de securitate și rezultatul, fiecare cu `[m...]` (id-ul
  mesajului) și «citatul» verificat;
- `PREȚURI ...`: liniile ofertelor PDF Odoo cu cod (Referință internă), cantitate, preț, monedă și termenii;
- `CONVERSAȚIA ...`: conversația întreagă, mesaj cu mesaj (la fel ca în lotul Faza 2).

Cererile `Completă` sunt sursa principală. `Fără ofertă` și `După vânzare` se folosesc **doar pentru
clarificări** (ce întreabă AKRO); generatorul respinge orice altă dovadă din ele.

## Ce scrii

Un fișier `reguli/<categorie>.json` (ex. `reguli/13.json`, `reguli/general.json`): o listă de reguli. Textele
sunt în română.

```json
{
  "cod": "R12-01",
  "titlu": "Antiscalant pentru osmoză: GEL ANTISCALANT RO1 la bidon de 25 kg",
  "categorie": "12-Chimicale pentru conditionare si intretinere",
  "cand": "Clientul cere antiscalant pentru o stație de osmoză, cu sau fără cantitate.",
  "clarificari": ["Ce cantitate (câte bidoane de 25 kg)?", "Livrare la adresa clientului sau ridicare?"],
  "oferta": {
    "produse": [{"ref": "12-002026", "rol": "antiscalantul ofertat"}],
    "servicii": ["transport inclus în sarcina AKRO"],
    "documente": ["fișa tehnică SP0222 (RO și EN)", "fișa de securitate (RO și EN)"],
    "conditii": ["plată 100% în avans"]
  },
  "dovezi": [
    {"conv": "c2134404", "src": "m2134404", "citat": "Las anexata si fisa de securitate a produsului nostru",
     "pentru": "ofertă", "nota": "fișa de securitate trimisă din proprie inițiativă, odată cu oferta"}
  ],
  "contradictii": []
}
```

### Câmpuri

- `cod`: `R<categorie>-<nr>`, ex. `R13-04`; pentru regulile generale `RG-<nr>`. Unic.
- `categorie`: exact una din: `01-Filtre impuritati` · `08-Osmoza si filtrare pe membrane` · `10-Ozonatoare` ·
  `11-Pompe de dozare` · `12-Chimicale pentru conditionare si intretinere` · `13-Filtre multistrat diferite medii` ·
  `14-Componente pentru filtre multistrat` · `16-Prestari servicii` · `21-Aparatura de analiza si control` ·
  `23-Diverse materiale, consumabile` · `25-Produse ocazionale unicate` · `27-Uv` · `Altele / neclar` ·
  `Toate categoriile` (doar regulile generale: termeni, documente, felul cererii, valabile peste categorii).
- `cand`: ce cere clientul ca regula să se aplice (tipul cererii, parametrii dați sau lipsă).
- `explicatie`: regula spusă pe înțelesul oricui, în 2–4 propoziții, ca și cum i-ai explica-o unui coleg nou: ce
  cere clientul, ce face AKRO și, doar dacă reiese din emailuri, de ce. Fără prescurtări neexplicate, fără prețuri,
  fără nimic care nu e în regulă sau în dovezile ei. Pagina o arată prima, la „Pe scurt”.
- `clarificari`: întrebările pe care AKRO le pune înainte de ofertă (sau clientul, dacă schimbă oferta). Listă goală
  dacă AKRO ofertează direct.
- `oferta.produse`: `{"ref": "<Referință internă>", "rol": "..."}`; codul trebuie să existe în nomenclator
  (generatorul verifică). Produs fără cod în ofertă: `{"ref": null, "nume": "<numele din ofertă>", "rol": "..."}`.
  Nu scrie prețuri: pagina arată singură, pe fiecare conversație-dovadă, liniile ofertate cu prețul și moneda lor.
- `oferta.servicii`: transport, montaj, PIF, deplasare, analiză apă etc. adăugate de AKRO.
- `oferta.documente`: ce atașează AKRO (fișă tehnică, fișă de securitate, desen, schemă, certificat, manual).
- `oferta.conditii`: plată, livrare, termen, valabilitate, garanție, reducere; doar ce apare în oferte sau în emailuri.
- `dovezi`: minimum una. `conv` = id-ul conversației (`c...`), `src` = id-ul mesajului (`m...`) din ACEEAȘI
  conversație, `citat` = fragment COPIAT EXACT din textul mesajului sau al unui atașament al lui (4–25 de cuvinte,
  o singură linie, fără „...”, fără corecturi), `pentru` ∈ `cerere`, `clarificare`, `ofertă`, `nota` = ce arată
  dovada (o frază). Citatul trebuie să dovedească partea regulii pentru care e pus. Pune câte o dovadă pentru
  FIECARE conversație în care se vede regula: numărul de conversații diferite e frecvența, iar de la 3 conversații
  regula e „sigură”. Poți folosi citatele din blocul `RÂND` (sunt deja verificate) sau altele din mesaje.
- `contradictii`: când conversațiile nu se potrivesc (aceeași cerere, alt produs, altă întrebare, alt termen):
  `{"text": "ce diferă", "dovezi": [...]}` cu dovezile părții care contrazice. NU alegi o variantă: le păstrezi
  pe amândouă. O regulă cu contradicții apare ca „contradictorie”.

Încrederea și frecvența nu se scriu: le calculează generatorul din dovezi. Frecvența e numărul de afaceri diferite
(conversațiile legate prin același număr de document AKRO se numără o dată); de la 3 afaceri fără contradicții regula e
„sigură”, cu 1–2 e „indiciu”, cu contradicții e „contradictorie”.

## Cum se scrie textul

Regulile le citesc oameni de la AKRO și din echipa noastră, nu doar specialiști:

- scrie propoziții întregi, în cuvinte obișnuite; fără simboluri în loc de cuvinte (`~`, `→`, `vs`): „aprox. 5 mc/h”,
  „115 saci devin 120”, „sau”;
- nu scrie id-uri interne (`c2122596`, `m2134404`) în texte: scrie „conversația 194” (numărul din `emailuri.html`).
  Id-urile stau doar în câmpurile `conv` și `src`;
- când pomenești o categorie, scrie și numele: „(categoria 13: stații de tratare și filtre multistrat)”;
- termenii de meserie și prescurtările (PIF, racord, UVT, big bag ...) se explică în `reguli/glosar.json`, iar pagina
  le arată explicația. Dacă folosești un termen care nu e acolo, adaugă-l: `termen`, `forme` (expresiile regulate după
  care e găsit în text), `exact` (true = contează majusculele, pentru prescurtări) și `explicatie` (una-două propoziții,
  fără alte prescurtări).

## Ce e o regulă bună

- Generalizează peste conversații: „La cerere de cartușe de schimb cu dimensiune și finețe date, AKRO
  ofertează direct codul echivalent din gama proprie, fără clarificări” e o regulă; „Clientul X a cerut 6
  cartușe” nu e.
- O cerere care apare o singură dată poate da o regulă (indiciu), dacă arată un tipar de ofertare clar
  (ex. ce întrebări pune AKRO pentru o stație de dedurizare).
- Separă după tipul cererii: client care dă codul exact / client care dă doar aplicația și parametrii / client
  care cere înlocuirea a ceva existent / licitație cu fișă tehnică de corespondență / service.
- Notează ce întreabă AKRO când lipsesc date (debit, analiza apei, racord, dimensiuni, cantitate) și ce oferă
  când nu întreabă nimic.
- Monedele nu se amestecă și prețurile nu se mediază (le arată pagina).

## Verificare (obligatoriu)

    python3 genereaza_reguli.py --verifica reguli/<categorie>.json

Repară fiecare eroare și rulează din nou până ies 0 erori (de obicei citatul nu e copiat exact: copiază-l din
nou, mai scurt, dintr-o singură linie a mesajului).
