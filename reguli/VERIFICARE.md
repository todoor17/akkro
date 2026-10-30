# Verificarea regulilor de ofertare (26.10.2026)

Fiecare dintre cele 188 de reguli din `reguli/*.json` a fost verificată din nou, afirmație cu afirmație, pe textul
complet al conversațiilor (toate mesajele și textul atașamentelor), nu pe loturile scurtate folosite la extragere.
Resursele din folderul de referință (PST-ul `exportAI.pst` cu 2.205 mesaje, lista de oferte Odoo, nomenclatorul,
fișele tehnice din Drive) sunt aceleași cu cele din care s-au generat paginile; lista de oferte din folder are alt
checksum doar pentru că a fost salvată din nou, rândurile sunt identice.

## Ce s-a verificat la fiecare regulă

- **Fapte:** fiecare afirmație din titlu, „când se aplică”, întrebări, produse, servicii, documente, condiții,
  contradicții, note și explicație apare în cel puțin una dintre conversațiile-dovadă (în toate, dacă textul spune
  „de obicei”, „mereu” sau „fără întrebări”). Ce nu apărea s-a corectat sau s-a scos.
- **Se aplică exact cum e scrisă:** în fiecare conversație-dovadă. Unde o conversație arăta altceva, a devenit
  contradicție sau regula a fost restrânsă la cazul pe care îl acoperă cu adevărat.
- **Contraexemple:** toate cererile categoriei au fost parcurse pentru cazuri în care regula se aplica, dar AKRO a
  făcut altfel; s-au adăugat ca contradicții.
- **Produse:** codurile există în nomenclator și au fost chiar ofertate în conversațiile-dovadă.
- **Numărare:** conversațiile despre aceeași afacere (legate prin același număr de document AKRO) se numără acum o
  singură dată; două reguli au trecut astfel de la „sigură” la „indiciu” (R14-12, R16-15).

## Rezultat

| | Înainte | După |
|---|---|---|
| Reguli | 188 | 188 (niciuna ștearsă: fiecare are cel puțin o conversație care o susține) |
| Corectate de fond | | 156 |
| Sigure | 84 | 52 |
| Indicii | 81 | 82 |
| Contradictorii | 23 | 54 |

Corecturile cele mai dese: „fără întrebări” sau „direct” acolo unde AKRO a pus întrebări; „mereu” sau „de obicei”
văzut într-o singură conversație; motive („pentru că…”) care nu apar în emailuri; întrebări puse intern, la un coleg,
trecute drept întrebări către client; reguli generale numărate pe toate ofertele (plată, garanție, monedă, transport,
fișă tehnică), unde „de obicei” nu se confirma.

Limită cunoscută: conversațiile „După vânzare” și „Fără ofertă” pot fi folosite doar ca dovezi pentru întrebările
puse de AKRO (cerință din tichet). Unde ele ar fi confirmat sau contrazis ce oferă AKRO, sunt pomenite mai jos, dar nu
apar ca dovezi în pagină. Un forward intern fără număr de document (conversațiile 104 și 316, Carpathian Springs) nu e
legat automat de afacerea lui și se numără de două ori la R10-02, R10-06 și R10-08.

Mai jos: rapoartele de verificare pe grupuri, cu o linie pe regulă și numerele conversațiilor din `emailuri.html`.


## Grupul 13

Verificare: 25 de reguli. Am citit integral toate conversațiile-dovadă din textul complet al conversațiilor și toate celelalte cereri ale categoriei din `reguli_13_1.txt` și `reguli_13_2.txt` (inclusiv 556, 16, 68, 96, 331, 631 și conversațiile „După vânzare”).
`python3 genereaza_reguli.py --verifica reguli/13.json` → **25 reguli verificate, 0 erori**. În câmpurile `explicatie` nu există — sau –.

### Pe reguli

- **R13-01**: corectat. Conversația 73 (licitația Regimentul 46) nu arată regula: acolo AKRO a ofertat direct stația simplex de 350 L, echivalentă cu cea din caietul de sarcini, și a enumerat datele de dimensionare abia după ofertă. Am mutat-o la contradicții. `cand` exclude acum reofertarea unei configurații cumpărate anterior. Nota pentru 469 spune acum că acolo AKRO a cerut doar țeava, consumul zilnic și o fotografie.
- **R13-02**: corectat. În 372 fișele tehnice au plecat abia la cererea clientului, iar cele două variante de racord apar doar acolo. Am adăugat plata 100% în avans (372, 377) și am rescris textul („uneori două variante”).
- **R13-03**: corectat. Explicația pomenea licitațiile, dar nicio dovadă nu e o licitație: le-am scos. Rolul 13-001164 trecea „11–15 mc/h”, dar dovada 375 dă 11–12 mc/h. `cand` exclude acum stațiile mici de 1" (R13-04), duplexul de 700 L de licitație (R13-19) și reofertarea (R13-05). Am adăugat condiția „montajul, asamblarea și PIF-ul nu sunt incluse”, văzută în toate cele 6 dovezi (210, 407, 376, 595, 569, 375).
- **R13-04**: corectat. Termenul era „10 zile – 2 săptămâni”, dar 404 dă 2–3 săptămâni, așa că l-am făcut „aprox. 10 zile până la 3 săptămâni”. Am adăugat că stația twin de 100 L pleacă fără rășina încărcată (586). Am corectat nota pentru 649.
- **R13-05**: corectat. Termenul: oferta dă 2–4 săptămâni, e-mailul din 47 dă 2–3. Telefonul de confirmare apare doar în 47 (în 207 clientul a cerut exact aceeași configurație), deci explicația nu mai spune „AKRO confirmă la telefon” ca pas general. Am adăugat plata 30% avans și 70% la 30 de zile (47, 207).
- **R13-06**: corectat. Am găsit contraexemple: 372, 586, 569, 601 și 73, oferte de dedurizare fără niciun filtru pus sau recomandat. Le-am pus într-o contradicție nouă. Am adăugat dovezile 407 (NW500 în ofertă) și 469 (filtru recomandat cu preț). Filtrul recomandat nu e mereu un NW: în 472 și 512 era un filtru Y sau unul de 10" cu cartuș inox. Prețul estimativ lipsește în 404.
- **R13-07**: corectat de fond. Regula („stația se livrează gata asamblată”) era contrazisă de majoritatea ofertelor pentru stații mari: 376, 407, 595, 569, 375, 47, 207, 73, 153 și 5 exclud asamblarea, iar 210 a plecat pe paleți, dezasamblată. Diferența vine din mărimea stației, așa că am restrâns `cand` la stațiile mici (simplex sau twin de până la aprox. 75 L pe coloană și sistemele pentru casă). Am scos dovada 210 (stație de 450 L dezasamblată, doar presetată) și am adăugat 601 („gata asamblate”). Vechea contradicție (207, 569, 586, stații mari) a fost înlocuită de una nouă, doar cu twin-ul de 16 L din 569. Documentul „fișa cu setările efectuate” apărea doar la 210 și l-am scos.
- **R13-09**: corectat. Explicația spunea că AKRO cere buletinul și telefonul, dar asta s-a întâmplat doar în 114 (buletin de la un laborator neacreditat). Livrarea „gata asamblată” e contrazisă de 153 (stație de 200 L, asamblare neinclusă), așa că am păstrat-o doar pentru sistemele mici. Am adăugat două contradicții noi: 156 (locuință off-grid, AKRO recomandă osmoză sub chiuvetă) și 57 (uz casnic, flux estimat cu osmoză). Am extins `cand` la fermă și anexe sanitare (347 și 153 nu sunt case).
- **R13-10**: corectat de fond. Regula spunea „la orice stație cu rășină (dedurizare, Ecomix)”, dar nicio ofertă de dedurizare (372, 377, 376, 595, 407, 569, 586, 601, 404, 47, 207, 210) nu dă cifrele de regenerare. Toate dovezile sunt oferte Ecomix (114, 347, 153) sau întrebarea de întreținere din 27, așa că am restrâns `cand` la acestea. Consumul de apă aruncată apare doar în 114 și 153: textul spune acum „adesea”.
- **R13-11**: corectat. Explicația spunea că AKRO „întreabă dacă aplicația e pentru o casă”, dar întrebarea apare o singură dată (266). Contradicție nouă: 565 (filtru de arsen pentru o casă) și 372 (apartament), ofertate direct, fără precizarea despre lucrul industrial.
- **R13-12**: corectat. Am scos dovada 266: acolo e un filtru pentru un foraj de casă, fără debit, deci nu e cererea din `cand`. Rămâne doar 57.
- **R13-13**: corectat. Contradicție nouă: 556 (filtre Turbidex de licitație) și 347 (filtru cu nisip de 60 L), ofertate fără niciun avertisment despre spălare. Înălțimea de 2,3 m e precizată acum ca valabilă la filtrele de 80 L (632).
- **R13-14**: corectat. Explicația spunea că dezinfecția e estimată „doar în textul e-mailului”, dar în 153 UV-ul VP950 e pus în ofertă. Contradicție nouă: 347, unde AKRO a propus pentru turbiditate un singur FNC60 opțional.
- **R13-16**: corectat minor. Întrebarea „se acceptă fără aviz?” apare doar în 172, așa că explicația spune acum „într-un caz”. În `cand` am explicat abrevierea FAM.
- **R13-18**: OK.
- **R13-19**: corectat minor. Am adăugat condițiile din 606 și 619: montajul și PIF-ul nu sunt incluse, iar garanția de 12 luni poate fi extinsă la 5 ani contra 5% pe an.
- **R13-20**: corectat. Condiția „fără tablou de automatizare” apare doar la licitația Buftea (606, 619) și e precizată acum așa. Am adăugat dovada 580 (Drăgănești: TPG 603, rezervor de 100 L, contor WPD DN80).
- **R13-21**: corectat de fond. AKRO nu a întrebat niciodată în scris ce diametru are țeava: în 472 a ofertat ambele mărimi cu regula de alegere, iar în 350 mărimea s-a lămurit la telefon. „Transport inclus” e adevărat doar în 472. În 350 livrarea e o linie separată în ofertă (16-003005), la fel în comenzile de pe site (273, 603, 642). Am scos „transport inclus” din titlu și am rescris condițiile.
- **R13-22**: OK.
- **R13-23**: OK.
- **R13-24**: OK.
- **R13-25**: OK.
- **R13-27**: corectat. Titlul spunea că AKRO atașează fotografii, ca regulă generală. În realitate doar 114, 347 și 210 le au, iar ofertele 376, 595 și 407 nu. Am adăugat o contradicție, iar titlul spune acum „la unele oferte”.
- **R13-28**: corectat. Conversația 569 contrazice regula: clientul a cerut fișe tehnice și certificate de calitate, iar AKRO a trimis doar fișele. Am mutat-o la contradicții. Am scos documentul „fișele tehnice ale stațiilor” (venea din 569). Manualul DEC e trimis o singură dată (210). Dovada 210 are acum sursa în mesajul care conține atașamentele (m2144292).
- **R13-29**: corectat. Contradicție nouă: 26, unde aceluiași client (Artrom) AKRO i-a trimis totuși un desen de mână pentru amplasarea bazinului. Am golit `clarificari`, pentru că întrebarea listată era a clientului, nu a AKRO, și nu a schimbat oferta.

### Reguli șterse sau unite

Niciuna.

### Contradicții noi (11)

- R13-01: 73 (ofertă directă după caietul de sarcini, datele cerute după ofertă).
- R13-06: 372, 586, 569, 601, 73 (fără filtru de impurități).
- R13-07: 569 (twin de 16 L fără asamblare). Am scos vechea contradicție cu stațiile mari (207, 569, 586), care acum sunt în afara `cand`.
- R13-09: 156 (osmoză sub chiuvetă la locuința off-grid).
- R13-09: 57 (uz casnic, flux cu osmoză).
- R13-11: 565, 372 (ofertă directă pentru locuințe, fără precizarea despre industrie).
- R13-13: 556, 347 (filtre cu masă filtrantă fără avertismente).
- R13-14: 347 (un singur filtru cu nisip, opțional).
- R13-27: 376, 595, 407 (oferte fără fotografii).
- R13-28: 569 (doar fișe tehnice, fără certificate).
- R13-29: 26 (desen de mână pentru bazin).

### Dovezi scoase sau mutate

- R13-01: 73, mutată la contradicții.
- R13-07: 210, scoasă (stație mare, livrată dezasamblată).
- R13-12: 266, scoasă (nu se potrivește cu `cand`).
- R13-28: 569, mutată la contradicții. La dovada 210 am schimbat sursa în m2144292.

### Dovezi adăugate

- R13-06: 407 (NW500 în ofertă) și 469 (filtru recomandat).
- R13-07: 601 (stație twin de 50 L livrată gata asamblată).
- R13-20: 580 (clorinare volumetrică la Drăgănești).

### Observații (fără modificări)

- 660 (FDC 150 cu TPG 603, rezervor de 50 L și contor de 1" cu impuls) și 21 (Șoarș) arată tot clorinarea volumetrică. Fiind „După vânzare”, nu pot fi dovezi de ofertă pentru R13-20.
- 404 are atașată o fotografie „Statie dedurizare twin.jpg”, dar nu există un text care să poată fi citat pentru R13-27.


## Grupul 14

25 de reguli verificate față de textul complet al conversațiilor și lotul reguli_14_1.txt. `--verifica`: 25 reguli verificate, 0 erori. Nicio liniuță lungă în `explicatie`.

### Pe regulă

- **R14-01**: scoasă dovada din conversația 219: acolo s-au cerut 1 t și 1 t, iar AKRO a prezentat ambele ambalări, deci cazul ține de R14-03. Odată cu ea a ieșit din regulă și condiția „comandă minimă 4-5 t”. `cand` nu mai cere „pentru filtre”, pentru că în conversațiile 305, 374 și 415 utilizarea nu e spusă (în 374 nisipul era pentru o conductă). Am scos „saci de rafie”, care nu apare nicăieri. Plata e scrisă ca 50% avans, cu restul la livrare, la gata de livrare sau la încărcarea din carieră (conversațiile 82, 305, 415, 200). Nota pentru 200 spune acum că era o comandă directă, cu 700-900 kg pe granulație.
- **R14-02**: `cand` restrâns la nisipul la big bag și la zeolit, adică materialele care vin din carieră. Nota pentru 219 spune că acolo nu se pomenește iarna. „De la plata avansului” apare doar în conversația 305 și e scris așa. Explicația spune că iarna a fost exclusă în 3 oferte, nu „mereu”.
- **R14-03**: `cand` precizat (fără ambalare indicată, în jur de o tonă pe granulație sau fără cantitate). Contradicție nouă din conversația 81: 300 kg de nisip 2-4 mm ofertate direct pe cod, fără variante și fără minim. La produse am notat că au fost ofertate în text.
- **R14-04**: scoasă afirmația că AKRO întreabă tipul filtrelor când clientul cere un singur sort. În conversația 121 a întrebat de alte granulații la 240 t, iar în 415 și 81 sortul unic a fost ofertat fără întrebări. Clarificările vin acum din conversațiile reale: tipul filtrelor (80) și alte granulații la cantități foarte mari (121). Am adăugat dovada din conversația 257 (oferta NOBEL în trei sorturi).
- **R14-05**: scos „face la fel când clientul nu spune utilizarea”. În conversațiile 415 și 219 clientul nu a spus utilizarea și a primit exact granulația cerută. Rămâne cazul real din 374: s-a cerut nisip de râu de 2-3 mm, AKRO poate da doar nisip de carieră și a ofertat 1-3 mm.
- **R14-06**: adăugată dovada din conversația 170 (Fără ofertă, ca clarificare): aceeași cerere de 240 t pe 0,8-1,2 mm, refuzată direct, fără întrebări, la câteva zile după 121. Explicația descrie ambele cazuri.
- **R14-07**: scoasă dovada din conversația 394. Acolo nu se vede ce cărbune a cerut clientul, iar „cărbunele ofertat de AKRO este bituminos” apare în lista de diferențe, deci clientul ceruse probabil alt tip. Am adăugat conversația 80 (LG85 pus direct în oferta de înlocuire, fără întrebări despre tip). „Este întrebat” a devenit „poate fi întrebat”.
- **R14-08**: transportul inclus e valabil doar în România (conversația 571). La 121 (Republica Moldova) prețul e franco fabrica din Polonia. Clarificarea pomenește și big bag-ul de 1000 L întrebat în 121. `cand` a devenit „la tonă”.
- **R14-09**: `cand` restrâns la cărbunele cerut ca produs separat, fără înlocuirile cu manoperă (80) și fără sistemele complete (394). Contradicție nouă din conversația 81: 1350 kg de LG85 pentru un operator de apă, cu oferta trimisă fără niciun document. Documentele sunt corectate: fișa tehnică atașată în 121 și în 571 este fișierul pentru LGCO 85 (în 121 a observat și clientul), iar atestul PZH din 121 era expirat și a fost retrimis. La 206 fișa tehnică fusese cerută de client.
- **R14-10**: „trimite documentul” nu e adevărat peste tot. În conversația 82 avizul doar e pomenit, deci explicația spune „îl pomenește sau îl trimite”. Contradicție nouă din conversația 80: stație de apă potabilă, nisip și cărbune ofertate fără aviz pomenit sau atașat.
- **R14-11**: „la licitațiile” a devenit „la o licitație din Republica Moldova”, pentru că e un singur caz. Restul se confirmă.
- **R14-12**: AKRO nu a întrebat dimensiunile (în conversația 80 clientul le-a dat singur, cu fotografii), așa că am scos „și ce dimensiuni au” din clarificări. Crepinele NOBEL țin de un singur operator (257 și 310), nu „la filtrele NOBEL” în general. Am scos „golirea” de la servicii, pentru că apare doar în 629 (După vânzare). Rolul pentru 16-002001 e aliniat cu numele din nomenclator: linia de deplasare, cu descriere extinsă.
- **R14-13**: titlul spunea „fără cost pentru serviciul de schimb”, ceea ce se poate citi ca „gratuit”. Acum spune „fără ofertă pentru serviciul de schimb”. Explicația adaugă mențiunea din ofertă că schimbul nu e inclus.
- **R14-14**: AKRO nu a întrebat dacă crepina e ruptă. Clientul a semnalat rășină în flux, iar AKRO a explicat că, dacă crepina de jos e ruptă, cel mai probabil nu încarcă butelia (conversația 55). Am mutat informația de la clarificări la condiții. Contradicție nouă din conversația 400: termenul scris pe confirmare e de 4-5 zile, nu 3-4 zile lucrătoare. Rolul pentru 16-001004 e aliniat la nomenclator (cod de manoperă). Confirmarea din iulie, din conversația 55, nu avea cod.
- **R14-15**: „prețul de listă de la 40 de saci” nu apare nicăieri. În conversația 326 apare doar „comanda minimă 40 de saci”, într-o listă de prețuri. Contradicție nouă din conversația 278: 4 saci ofertați, sub minim, cu termen de 3-5 săptămâni.
- **R14-16**: `cand` acoperă și cererea pentru mai multe stații fără adrese date (643) și comenzile separate pe adrese (200). Explicația spune că DACHSER și RABEN au fost propuse după ce clientul a spus că are o ofertă mai bună (69).
- **R14-17**: regula spunea că AKRO face ambele lucruri în ofertă. De fapt, numărul de TIR-uri și accesul apar împreună doar în conversația 82. În 121 apare doar estimarea, și asta înainte de ofertă (am schimbat `pentru` în clarificare), iar în 80 apare doar accesul. Am adăugat dovada din conversația 69: prețul e calculat presupunând acces TIR în ambele stații. Titlul și explicația sunt rescrise.
- **R14-18**: OK (am adăugat densitatea de 1,54 kg pe litru din oferta din conversația 82).
- **R14-19**: adăugate condițiile din ofertă: saci de 20 kg, minim 500 kg, livrare inclusă, 15 zile, 50% avans. Explicația spune că fișa tehnică a fost cerută de client și că AKRO a ofertat 500 kg deși caietul de sarcini pomenea o tonă.
- **R14-20**: „de obicei” a devenit cazul unic (conversația 326). Zeolitul și Turbidex-ul de pe lista clientului nu au primit preț, lucru notat acum. Am trecut și nisipul la produsele fără cod.
- **R14-21**: OK.
- **R14-22**: „ofertează strict ce are” e o lectură greșită a frazei „generată strict pentru echipamentele solicitate”. Pompa a fost înlocuită cu alt model, iar modulul de relee a rămas deoparte pentru că vanele îl au deja. Titlul și explicația sunt rescrise. Rolul pentru 14-001010 nu mai pomenește „230/12 V”, pentru că nomenclatorul spune 230/15 V. Am adăugat pompa 11-002012 și condițiile ofertei.
- **R14-23**: precizat că clientul ceruse acum exact cartușele de 10 și 5 microni, iar AKRO a semnalat diferența față de comenzile vechi. Am adăugat discountul de 3% și pungile de bile.
- **R14-25**: „arsen în creștere” nu apare în conversația 521. AKRO a scris că rezultatele par bune, cu ieșirea în jur de 6. Titlul, `cand` și explicația sunt corectate.
- **R14-26**: OK. Am rescris doar textele cu „/” și serviciul de service (solicitat de AKRO de la 9 noiembrie, nu „la cerere”).

### Reguli șterse sau unite
Niciuna.

### Contradicții noi (6)
- R14-03: conversația 81 (300 kg ofertate direct pe cod, fără minimul de 1000 kg).
- R14-09: conversația 81 (LG85 de 1350 kg, fără documente).
- R14-10: conversația 80 (stație de apă potabilă, fără aviz sanitar).
- R14-14: conversația 400 (termen de 4-5 zile, nu 3-4 zile lucrătoare).
- R14-15: conversația 278 (4 saci, sub minimul de 40).
- R14-06: în loc de contradicție, conversația 170 a intrat ca dovadă, pentru că refuzul e același.

### Dovezi scoase
- R14-01: conversația 219 (cazul ține de R14-03).
- R14-07: conversația 394 (nu se vede cererea de cărbune, iar tipul bituminos apare ca diferență).

### Dovezi adăugate
- R14-04: conversația 257.
- R14-06: conversația 170 (clarificare).
- R14-07: conversația 80.
- R14-17: conversația 69.

### Observații fără modificări în fișier
- Conversațiile 629 și 50 (După vânzare) arată o înlocuire NOBEL fără crepine și un termen de 4-5 zile la butelii. Nu pot intra ca dovezi de ofertă (generatorul primește din ele doar clarificări). Am ținut cont de ele doar formulând R14-12 și R14-14 mai prudent.
- Conversația 215 (Fără ofertă) arată o întrebare AKRO despre postarea ofertei în SEAP: un singur produs sau repere separate. Nicio regulă din acest fișier nu o acoperă.


## Grupul 01 și 10

Fișiere: `reguli/01.json` (01-Filtre impuritati, 21 reguli), `reguli/10.json` (10-Ozonatoare, 8 reguli).
Surse: `date/loturi_reguli/reguli_01_1.txt`, `reguli_10_1.txt` (citite integral) și textul complet al conversațiilor.
`--verifica`: 01.json 21 reguli, 0 erori; 10.json 8 reguli, 0 erori. Nicio liniuță (— sau –) în `explicatie`.
Scripturile cu modificările: `SCRATCH/verificare/grup_01_10_work/fix01.py`, `fix10.py`. Originalele sunt copiate în același folder.

### 10-Ozonatoare

- R10-01: corectat. „Capacitatea o dă clientul” nu apare nicăieri: la conv. 146 s-a stabilit la telefon, la conv. 104 a propus-o AKRO (dublu față de primul aparat). „Fișa tehnică a seriei” apare doar la 146; la 104 s-a trimis doar descrierea GP60. Am scos produsul 10-001080 (G-P30), care nu e ofertat în nicio conversație-dovadă. `cand` restrâns la generatoare standard, cu excluderea celor speciale. Am adăugat condițiile de plată din cele două oferte și o dovadă pentru discuția telefonică și atașamente (146).
- R10-02: corectat ușor. Nota spunea „a doua listă”, dar sunt trei runde de întrebări (104). Am adăugat întrebările care lipseau: debitul maxim și mediu, modul de lucru al bazinelor. Simbolurile au devenit cuvinte.
- R10-03: corectat. „Persoane fizice, uneori din străinătate” se sprijinea pe un singur caz (296, Bulgaria). AKRO nu „întreabă întâi”: în primul mesaj a răspuns tehnic (Krausen, gamă rezidențială, pompă de aer), a trimis fișa tehnică și abia apoi a pus întrebările. Prețul l-a dat doar după ce l-a cerut clientul. Produsul rămâne fără cod (`ref: null`, ofertat doar în text), iar în rol am trecut codul din nomenclator, 10-001045.
- R10-04: corectat. Clarificarea „instalația lucrează pe recirculare?” nu era o întrebare: AKRO a spus că instalația trebuie să lucreze pe recirculare (435). În explicație am pus motivul scris în email: datele îi trebuiau ca să ceară o recomandare de generator.
- R10-05: corectat. Clarificarea „Acceptați modelul disponibil?” nu a fost pusă nicăieri. La 192 AKRO a trimis direct confirmarea pentru G-P30, fără să ceară acordul. La 296 doar a anunțat că are în stoc numai modelul de 1 g/h. Am scos clarificarea și am rescris titlul și explicația.
- R10-06: corectat ușor. Clarificarea a fost reformulată după textul real („în funcție de soluția aleasă și debite... buget”, 104), iar „+” din titlu a devenit cuvânt.
- R10-07: corectat ușor. Contradicția (104) are acum și linia ofertei cu „18 sapt.”, nu doar contractul. Id-ul S02573 din condiții l-am înlocuit cu numărul conversației.
- R10-08: corectat. „Nu a trimis ofertă, pentru că WEDECO n-a dat un răspuns favorabil” era o cauzalitate prea tare: emailul spune doar că încă nu are răspuns și că revine. Am adăugat conversația 435 (HVAC), unde AKRO strânge date ca să „solicite o recomandare de generator”, și am lărgit `cand` pentru aplicațiile pe aer.

### 01-Filtre impuritati

- R01-01: corectat. „Clientul poate lua doar ce e pe stoc” a devenit ce s-a întâmplat la 173: AKRO a ofertat la 1 micron doar setul din stoc, iar clientul a ales doar stocul. Clarificarea nu mai conține varianta „sau livrăm doar ce e în stoc”, care a fost alegerea clientului, nu întrebarea AKRO. Am adăugat termenul de 2-3 săptămâni de la 97, unde setul a venit împreună cu un filtru nou.
- R01-02: corectat. „AKRO nu mai pune întrebări” a devenit „fără întrebări scrise”, pentru că la 97 a existat întâi o discuție telefonică. Consola din inox a fost adăugată doar la NW500 (97), nu și la NW800 (526).
- R01-03: corectat. Întrebările (tip de filtru, debit, turbiditate, fișă tehnică) apar doar la 386, unde cererea era vagă. La 338 debitul era dat și AKRO a recomandat direct un decantor sau NW400, fără întrebări. La 84 NW400 e o treaptă grosieră aleasă de AKRO. `cand`, rolul produsului și condițiile au fost rescrise după aceste cazuri.
- R01-04: corectat. La 232 AKRO nu a pus întrebările despre finețe, sursă și alimentare: după telefon a trimis cererea direct la DROP. `cand` restrâns la cererile fără finețe sau date despre apă, pentru că la 556, cu toate datele date, AKRO a ofertat direct un SUF.
- R01-05: corectat. Afirmația „dacă e codul altui producător (CUNO, Atlas), AKRO ofertează echivalentul și scrie corespondența” e falsă. La 328 clientul a dat chiar codul AKRO (PRNW050-29), iar AKRO a adăugat pe ofertă echivalentul CUNO. La 272 cartușul Atlas e chiar produsul Atlas. La 395 codul intern scris de client era al altui cartuș, iar AKRO a ofertat după denumire. Conversația 272 a trecut la contradicții, iar produsele ei (01-010101, 01-010205) au ieșit din regulă. Termenele au fost corectate la „25 de zile până la 7 săptămâni”.
- R01-06: corectat ușor. Ordinea reală la 339: întâi întrebarea despre prindere și utilizare, apoi telefonul, apoi carcasa identificată din istoric. Explicația a fost rescrisă, cu termenii explicați.
- R01-07: OK, cu completări: rezultatul de la 72 (producătorul nu a cotat FA20CASX5) și nota de la 272 („12, de preferat 6”).
- R01-08: OK. Am rescris doar explicația și notele (37: clientul a refuzat carcasele cu racord de 1").
- R01-09: corectat. Conversația 112 era în același timp dovadă și contradicție. Acolo AKRO a lăsat 100 de saci în ofertă și a cerut minimum 150 pe comandă, deci nu e „50 pe model, ofertat direct”. Am scos-o din `dovezi` (rămâne la contradicții) și am scos produsul 01-011080. Am înlocuit „fiindcă” din explicație cu „Au fost și excepții”.
- R01-10: corectat ușor. „Uneori urgent” a devenit „o dată”. Ambele cereri vin de la același șantier naval, de la departamente diferite.
- R01-11: corectat. Fișa tehnică pentru verificarea echivalenței s-a trimis doar la 113, nu și la 334 sau 336. La 336 AKRO a ofertat direct, fără întrebări. Sacii din poze (169, 204) erau chiar Allied Filters, nu un echivalent.
- R01-12: corectat. UV-ul a fost întrebat sau propus opțional doar la 84; la 251 a fost inclus direct. Setul de rezervă apare doar la 84. Am adăugat că 84 a comandat în final varianta redusă (o carcasă, cartușe de 1 micron).
- R01-13: corectat, cu o contradicție nouă. În oferta revizuită de la 84 (o carcasă și 6 cartușe, care a fost comandată) kitul cu manometru și ventil nu mai apare.
- R01-14: corectat. „Înainte de ofertă, AKRO verifică la producător” e adevărat doar la 608; la celelalte e doar termenul trecut în ofertă.
- R01-15: corectat, cu o contradicție nouă. La 608 AKRO a spus explicit doar abaterile la ATEX și la racord. Restul nu a fost menționat în email: doar cartușe de 5 microni (nu și de 10), fără varianta duplex, livrare EXW Brașov în loc de DAP Chișinău, carcasă 316 standard. „De multe ori licitație” e adevărat doar pentru 2 din 4 cazuri, așa că am precizat.
- R01-16: corectat. Certificatul CE1935 pentru apă potabilă apare doar la 51 (spital), nu în oferta pentru filtrele Y de la 426. La 426 AKRO a ofertat câte două site de rezervă pe filtru, deși clientul ceruse una (am trecut asta în notă).
- R01-17: corectat. Condiția „fără montaj și PIF” apare doar la 556. La 51 AKRO a luat varianta FMA de la producător. „Ofertează direct” a devenit „fără întrebări către client”.
- R01-18: corectat. Întrebarea „Cine este clientul?” (140) a fost pusă intern, unui coleg de la Spectra, nu clientului. Am scos clarificarea, dovada respectivă și afirmația din explicație. Validarea schemei e pusă acum ca întrebarea clientului, cu răspunsul AKRO.
- R01-19: OK. Am trecut explicația la trecut, pentru că e un singur caz (459).
- R01-20: corectat. Regula se sprijinea pe un singur client („unii clienți”). Am adăugat conversațiile 102, 1 și 37, cu documentele trimise în fiecare. Explicația spune acum și că certificatele pentru carcasele și cartușele fabricate pe comandă vin după producție (1).
- R01-21: corectat. Clarificările erau afirmații ale AKRO; acum sunt întrebările clientului, cu răspunsul AKRO. Am scos „Nu a ofertat nimic, fiindcă nu avea în stoc” (cauzalitate care nu apare în email). Cuvântul „anume” l-am adăugat în titlu.

### Reguli șterse sau unite

Niciuna.

### Contradicții noi (3)

- R01-05: conversația 272. La o comandă cu coduri, AKRO a cerut întâi acordul pentru cutia completă și pentru termenul de 7-8 săptămâni.
- R01-13: conversația 84. În oferta revizuită, comandată apoi, kitul de manometru și ventil lipsește.
- R01-15: conversația 608. Abaterile nemenționate în email: doar 5 microni, fără duplex, livrare EXW în loc de DAP.

R10-07 avea deja o contradicție; am completat-o cu linia ofertei.

### Dovezi scoase

- R01-05: c2111748 (272), mutată la contradicții.
- R01-09: c2102276 (112), cele două dovezi din `dovezi`; conversația rămâne la contradicție.
- R01-18: c2103876 m2140100 (140), întrebarea internă „Cine este clientul”.

### Dovezi adăugate

- R10-01: c2140420 m2140420 (146), discuția telefonică și atașamentele.
- R10-07: contradicție, c2101892 m2109540 (104), linia ofertei cu 18 săptămâni.
- R10-08: c2156484 m2156484 (435), clarificare.
- R01-05: contradicție, c2111748 m2148388 (272).
- R01-13: contradicție, c2101060 m2146468 (84).
- R01-15: contradicție, c2164612 m2164612 (608), două citate.
- R01-20: c2101860 m2138052 (102), c2134212 m2143684 (1), c2098436 m2098436 (37, mesaj din 2024 citat în conversație). Toate trei sunt marcate „clarificare”, pentru că sunt conversații Fără ofertă sau După vânzare.

### Produse scoase

- R10-01: 10-001080, neofertat în conversațiile-dovadă.
- R01-05: 01-010101 și 01-010205, care apăreau doar în conversația 272, acum contradicție.
- R01-09: 01-011080, care apărea doar în 112, acum contradicție.

### Observații

- Oferta inițială pentru G-P20 din conversația 192 (cu broșura seriei GP și manualul în română) ar susține R10-01. Conversația e însă După vânzare, iar generatorul nu acceptă din ea dovezi de ofertă.
- R10-02, R10-06 și R10-08 numără conversațiile 104 și 316 ca două conversații, deși 316 e redirecționarea internă a aceluiași fir cu Carpathian Springs.


## Grupul 11 și 12

Fișiere: `reguli/11.json` (16 reguli), `reguli/12.json` (14 reguli). Surse: textul complet al conversațiilor, `date/loturi_reguli/reguli_11_1.txt`, `reguli_12_1.txt` (citite integral), `output/produse.csv`.
Verificare: `python3 genereaza_reguli.py --verifica reguli/11.json` → 16 reguli verificate, 0 erori; `reguli/12.json` → 14 reguli verificate, 0 erori. Nicio liniuță — sau – în `explicatie`.
Script: `SCRATCH/verificare/fix_11_12.py` (originalele salvate în `SCRATCH/verificare/11.orig.json`, `12.orig.json`).

### Categoria 11

- **R11-01**: corectat. „În email scrie stocul și termenul” nu e adevărat mereu: conversația 65 are doar oferta, fără stoc sau termen. Acum spune că în 4 din 5 conversații (137, 281, 545, 646) apare termenul de 5-10 zile, iar stocul furnizorului doar în 137 și 281. Regula cu „3 săptămâni / august” e marcată ca văzută o singură dată (137). `cand` rescris fără „/”.
- **R11-02**: corectat. Clarificarea „Ce diametru are conducta?” nu apare în nicio conversație-dovadă (diametrul vine din documentație, iar în 606 AKRO a presupus DN100), așa că am scos-o. Lancea lipsește din oferta pentru Focuri (242), lucru notat acum. „Livrarea inclusă” nu e valabilă la 149 (transport Pallex plătit separat), iar „montaj și PIF neincluse” s-a adăugat (31, 242, 280, 397, 606). Rolul supapei 11-002005: „când fișa o cere” nu se confirmă, acum spune „inclusă la licitația Amnaș” (31).
- **R11-04**: corectat. AKRO nu a întrebat „PIF sau asistență?”. După discuția telefonică a prezentat cele două variante, iar clientul a ales (149). `cand` reformulat: clientul cere oferta și întreabă de transport și PIF, nu „comandă”. Am scos prețurile din notă.
- **R11-05**: corectat. AKRO a întrebat dacă se acceptă doar echipamentele în 242 și 105. La licitația Amnaș/Săliște (31 și 54) a exclus direct containerul, fără să întrebe, iar asta e acum contradicție.
- **R11-07**: corectat. Am adăugat întrebarea „În ce stadiu se află proiectul?” (171, 168) și o dovadă de clarificare din 171. Am rescris explicația.
- **R11-08**: corectat. „AKRO întreabă cum trebuie să funcționeze” e adevărat în 168 și 397, dar nu în 171, unde AKRO a ales singur comanda din panou și a explicat. Am mutat aici panoul K800 KPS06 și senzorul FCL5 (11-002158, 11-002159), plus avertismentul despre apa aruncată la canal (397), adică varianta „pompa după contor, panoul doar verifică”.
- **R11-09**: corectat. „Ofertează fără întrebări” e fals: în 171 AKRO a întrebat stadiul, fișa și datele de montaj înainte de ofertă. La 397 panoul nu comandă pompa (pompele dozează după contor), așa că am mutat cazul la contradicții și am scos de la produse KPS06 și FCL5. Am adăugat supapa 11-002005 (ofertată în 171) și condiția „montaj și PIF neincluse”.
- **R11-10**: corectat. „Le ofertează fără întrebări” e fals pentru 397, unde AKRO a pus multe întrebări înainte. Am scos afirmația.
- **R11-11**: corectat. „Nu poate garanta rezistența materialelor” e o exagerare: AKRO a scris că „nu știe în ce măsură vor fi afectate materialele” (53). Am adăugat condițiile din ofertă: livrare inclusă, fără montaj și PIF, garanție 12 luni deși clientul ceruse 3 ani (cu dovadă).
- **R11-12**: corectat. TPG 800 avea `ref: null`, dar există în nomenclator: 11-002040. Ambele pompe sunt marcate „propusă, fără cotație” (332, fără răspuns de la client).
- **R11-13**: corectat. Contorul cu impulsuri nu e „adăugat de AKRO”: clientul l-a cerut (apometru de 1/2 sau 3/4 țol), iar AKRO a ofertat unul de 1 țol (470). Notele pentru 438 și 533 spun acum că e vorba de comenzi din oferta S02795 făcută anterior. Fișa APG a fost trimisă la confirmarea comenzii.
- **R11-14**: OK pe fond. Am scos prețul senzorului de nivel din condiții și am reformulat explicația.
- **R11-15**: corectat. Contradicția (robineți DN80 și filtre Y la Amnaș) nu ține de `cand`: sunt armături pe conducta principală, nu fitinguri pentru punctul de injecție, iar la Amnaș fitingurile injectorului au fost chiar excluse. Am scos contradicția. Explicația spune acum ambele lucruri, iar titlul precizează „pentru punctul de injecție”.
- **R11-16**: OK.
- **R11-17**: OK. Doar `cand` și `servicii` au fost rescrise fără „/” și „;”.
- **R11-18**: OK. Doar titlul, `servicii` și o notă au fost rescrise fără simboluri („+”, „/”).

### Categoria 12

- **R12-01**: corectat. Termenul de 2-3 zile apare doar în emailurile 454 și 585. Ofertele scrise au 15 zile pentru 20 de bidoane (560) și 5 zile (470), iar asta e acum contradicție. Am adăugat dovada din 470 (antiscalant ofertat direct, din stoc).
- **R12-02**: OK pe fond. Am adăugat dovada din 470 (fișa de securitate și SP0222 atașate la oferta comună cu pompa) și am explicat în text ce e fișa de securitate.
- **R12-03**: corectat. În 470 clientul a cerut preț și ambalare fără cantitate, iar AKRO a ofertat un singur bidon, fără reducere. E contradicție nouă. Nota pentru 30 spune acum exact ce s-a întâmplat: subiectul cererii este „Bidon 25kg”, s-a ofertat 1 bidon fără reducere și s-a anunțat 8% de la 2 bidoane.
- **R12-04**: OK.
- **R12-05**: corectat. „De regulă operator de apă potabilă” se bazează pe un singur caz (560), așa că am scris „un operator de apă potabilă”. „Concentratul osmozei” a fost înlocuit cu formularea din email: antiscalantul rămâne în membrane și pleacă la canal.
- **R12-06**: corectat. „Confirmă imediat” nu e valabil în 162 (AKRO a lămurit întâi cantitatea). „Trimite prin Pallex” se vede doar în 248 și 613, nu în 162 și 527. Am scos „CMR” (nu e în glosar) și „/”.
- **R12-07**: OK.
- **R12-08**: corectat. „Clientul e întrebat ce cantitate intră pe fiecare lună” e fals pentru 527: clientul a dat de la început împărțirea 60 și 60, iar AKRO a făcut direct confirmările. AKRO a întrebat doar în 162, după ce cantitatea s-a schimbat de la 115 la 120 de saci.
- **R12-09**: corectat. La biocidul Vinkocide (486) AKRO nu a refuzat pe loc: a căutat întâi un echivalent (asta e regula R12-11), așa că am restrâns `cand` la chimicale generice, nu produse de marcă, și am scos dovada din 486. Am scos și dovada din 187 (cererea era pentru o pompă, nu pentru chimicale, și e acoperită de R12-10). Afirmația „vinde și dezincrustant” nu mai e susținută de dovezile rămase, așa că am scos-o. Am adăugat cazul cărbunelui activ granular din 643.
- **R12-10**: corectat. Produsul avea `ref: null`, dar BOILER CLEANER P 10 kg există în nomenclator: 12-002011.
- **R12-11**: corectat. Întrebările despre canistre și despre prețul pe kilogram au apărut fiecare doar într-o conversație (486, respectiv 541), deci explicația spune acum „după caz”. Am adăugat rezultatele (cu dovezi): producătorul nu a avut echivalent pentru biocid (486), iar pentru antiscalant AKRO a propus GEL RO 1, dar prețul cerut nu putea fi atins (541).
- **R12-12**: corectat. „Din gama producătorului GEL” nu se vede în conversația-dovadă 363 (se confirmă doar în 362, care nu e cerere de ofertă), așa că am scris generic „producător”. Am adăugat linia de transport 16-003006 (fără preț) și plata la 30 de zile, ambele din ofertă.
- **R12-13**: OK.
- **R12-14**: OK.

### Reguli șterse sau unite

Niciuna.

### Contradicții noi (4)

- R11-05: licitația Amnaș/Săliște, unde containerul a fost exclus direct, fără întrebare (conversațiile 31 și 54).
- R11-09: stația Regie-UPB, unde pompele dozează după contor și panoul K800 doar verifică clorul (397).
- R12-01: termene de livrare de 15 zile (560) și 5 zile (470) în ofertele scrise.
- R12-03: un singur bidon, fără reducere, la o cerere fără cantitate (470).

Contradicție scoasă (1): R11-15, robineții și filtrele Y pe conducta principală (31), care nu sunt fitinguri pentru punctul de injecție.

### Dovezi scoase sau mutate

- R11-05: 31 și 54 mutate din dovezi la contradicții.
- R11-09: 397 (2 dovezi) mutat la contradicții.
- R12-09: scoase 486 (biocid, intră la R12-11) și 187 (cerere de pompă, intră la R12-10).

### Dovezi adăugate

- R11-07: 171 (întrebarea despre stadiul proiectului).
- R11-08: 397 (avertismentul despre apa aruncată la canal, pompele merg după contor).
- R11-09: 171 (clarificarea dinaintea ofertei); contradicția: 397 (pompele dozează după debit).
- R11-11: 53 (cererea de garanție de 3 ani).
- R12-01: 470 (ofertă); contradicția: 560 și 470.
- R12-02: 470.
- R12-03: contradicția: 470.
- R12-11: 486 (răspunsul negativ) și 541 (GEL RO 1 propus ca echivalent).

### Alte observații

- Conversațiile 15 (ofertă directă TPG 603, „Produsul este in stoc!”) și 54 (oferta Săliște) susțin R11-01, R11-02 și R11-16. Pentru că sunt `Fără ofertă`, generatorul le acceptă doar ca dovezi de clarificare, așa că nu le-am adăugat la acele reguli.
- Conversația 283 (Climatec) are doar un email intern cu echivalentele propuse (TPG 800, K800), fără răspuns către client, deci nu poate fi folosită ca dovadă.


## Grupul 08 și 27

Fișiere: `reguli/08.json` (16 reguli, categoria 08: osmoză și filtrare pe membrane) și `reguli/27.json` (10 reguli, categoria 27: UV).
Surse citite integral: conversațiile 56, 154, 157, 188, 249, 284, 292, 458, 482, 34, 303, 431, 425 (pentru 08) și 140, 176, 226, 509, 556, 606, 94, 115, 146, 178, 283, 391, 393, 451, 453, 475, 536, 596, 181 (pentru 27).

`python3 genereaza_reguli.py --verifica`: 08.json are 16 reguli verificate și 0 erori, 27.json are 10 reguli verificate și 0 erori. Câmpurile `explicatie` nu conțin „—” sau „–”.

### Reguli din 08.json

- **R08-01**: corectată. Conv. 303 (osmoză casnică) și 34 (osmoză de 80 mc/h refuzată) nu arătau regula. Le-am scos de aici, ele rămân la R08-12 și R08-11. Am scos și clarificarea despre pretratare, care venea doar din ele. Conv. 154 avea buletinele de analiză, deci nu se potrivea cu „fără buletin”. AKRO a dat acolo un buget pe o ipoteză (16-18 mc/h în sursă) în același email cu întrebările. Am rescris `cand` („lipsesc datele de dimensionare”) și explicația („dă cel mult un buget estimativ, pe ipoteze spuse clientului”). Am adăugat clarificările care se văd: schimburile (56) și calitatea dorită la ieșire (56, 188).
- **R08-03**: corectată. „Oferta oficială vine doar dacă o cere clientul și dă CUI-ul” se vede doar în 188, așa că acum scrie „într-un caz”. Excluderile sunt puse „după caz”: bazinul (56), automatizarea by-pass-ului (154), inoxul, montajul și SCADA (188), transportul, montajul, PIF-ul, bazinul, pompa și UV-ul (249). Am restrâns `cand` la cererile fără listă de echipamente. Conv. 157 (cerere de achiziție cu lista completă) a primit direct o ofertă atașată, nu un buget în email. La 249, bugetul era preț net de achiziție pentru Spectra.
- **R08-04**: corectată. „Fără alte întrebări” era fals: în 56 și 188 AKRO a întrebat mult înainte. Fluxul complet (bazin, UV și pompă) apare doar în 188. În 157 au fost bazin și două UV-uri, fără pompă, iar fluxul era cel dat de client, cu filtre de nisip. În 56 bazinul final a rămas în afara bugetului. Am rescris `cand`, `conditii` și explicația, am adăugat documentele (fișele ca linkuri, 188) și am precizat la montaj „conversația 157”.
- **R08-05**: corectată. Clorul ca oxidant apare doar în 249 (în 56 scrie „oxidant + sodă”). „Flux obligatoriu” e spus doar în 249. Dedurizarea parțială apare doar în 56. Am lărgit `cand` și la conductivitate mare.
- **R08-06**: OK. Am schimbat doar formularea din `cand`: la 154 sunt „două surse ale unei primării”, nu „două puțuri”.
- **R08-07**: corectată. `cand` spunea „conductivitate sau cloruri peste normă”, dar la 154 (Moara Arsă) peste normă sunt sulfații și duritatea, iar conductivitatea și clorurile sunt în normă. Apa amestecată e „doar filtrată” (154: filtrare mecanică grosieră).
- **R08-08**: corectată. AKRO a întrebat de presiune doar în 154. În 56 și 188 a scris condiția direct în propunere.
- **R08-09**: corectată. `cand` („AKRO trimite fluxul unei osmoze noi”) era contrazis de 154, 249 și 157, unde nu s-au dat costuri de exploatare. L-am restrâns la clientul final care cere și costurile de exploatare (56 cere CAPEX și OPEX, 188 cere mentenanță și consumabile) și am adăugat cele două dovezi de cerere. Costul pe mc apare doar în 56, așa că acum scrie „într-un caz”.
- **R08-10**: corectată. „Din primul răspuns” era fals pentru 56, unde fotografia a venit în al doilea mesaj, după întrebări. În 188 a venit în primul răspuns, dar cu etapele proiectului, nu cu variantele de dimensionare. `cand` e acum „client final nou”.
- **R08-11**: corectată. Câmpul `clarificari` conținea o explicație, nu întrebări. Am pus întrebările din 34 (caiet de sarcini, pretratare, buget, număr de linii), iar explicația am mutat-o în `conditii`. Am adăugat dovada din 34 despre pretratare.
- **R08-12**: OK pe fond. Am adăugat dovada din 303 pentru clarificarea despre capacitate și pretratare, care nu avea dovadă. „Recunoaște un sistem casnic” a devenit „bănuiește”, fiindcă AKRO scrie „mă duce cu gândul”.
- **R08-13**: corectată. În 292 AKRO a întrebat locul și urgența, deci nu a ofertat „direct, fără întrebări”. Am restrâns `cand` la cantități obișnuite și am mutat dovezile din 292 la R08-15. Fișa tehnică a fost atașată doar la 458, unde cererea o cerea, și la 292. Stocul din Belgia apare în 284 și 482, nu în 458, unde marfa se ridică din Brașov. Am adăugat dovada din 482 (Belgia).
- **R08-14**: corectată, la formulare. Conv. 482 nu leagă prețul de stoc, ci păstrează prețul de anul trecut. Titlul și condițiile acoperă acum ambele situații.
- **R08-15**: corectată. Am adăugat ce lipsea din 292: stocul confirmat în Belgia, termenul de 10-14 zile, plata 100% în avans și „reducerea maximă” (3 dovezi noi).
- **R08-16**: corectată. Din 458 nu se poate confirma că cererea nu dădea modelul pompei (anexa RFQ nu e în text). Acum `cand` spune „AKRO nu poate identifica exact echipamentul”. Am adăugat clarificările din 425: fotografii de ansamblu, anul montajului, mentenanța făcută.
- **R08-17**: OK. Am precizat doar `conditii`.

### Reguli din 27.json

- **R27-01**: corectată, la detalii. Manualul se vede doar în 226. Termenele de livrare (6-8 săptămâni în 140, 7-10 în 226) sunt acum legate de conversațiile lor. Nota pentru 226 spune că propunerea „face abstracție de caietul de sarcini”. Contradicția NUVONIC (453) rămâne.
- **R27-02**: OK. Am schimbat doar formularea (simbolul „/” din clarificări).
- **R27-03**: OK. Am scos „AKRO/Spectra” din servicii.
- **R27-04**: corectată. În 226 nu se vede că fișa ar fi cerut apă caldă: AKRO a pus opțiunea în propunerea proprie. Am rescris `cand` („sistemul trebuie să lucreze și cu apă caldă”) și am pus în explicație „într-un caz… în altul” pentru documente.
- **R27-05**: corectată și cu contradicție nouă. La 606 (spitalul din Buftea), fișa F5-06 cerea curățarea manuală a tecilor, dar AKRO a ofertat SITA AM 96 ECO PLUS. Fișa lui trimisă cu oferta are „Manual NO” și curățarea automată doar ca variantă separată, neofertată. La 226, modelul 80/3 a fost ofertat fără varianta RM, cea cu curățare manuală. Am scos și „de regulă” din titlu.
- **R27-06**: corectată. La 453 UV-ul era NUVONIC, nu SITA, așa că explicația spune acum „sterilizatorul UV”. La 606 (F5-07) clorinarea nu e pe recirculare, ci proporțională, cu contor cu impulsuri și fără panou. Am lărgit `cand`, am adăugat contorul 23-001189 (ofertat în S02934) și dovada din 606. Fișele ca linkuri Google Drive se văd în 226 și 453. „De regulă la spitale” a devenit „mai ales”, fiindcă la 226 nu se știe dacă e spital.
- **R27-07**: corectată. Ideea filtrului cu autocurățare a venit de la colega de la Spectra, iar AKRO a dat doar modelul și fișa. Întrebarea a fost despre schema instalației, nu direct despre filtre. Produsul 01-008099 nu a fost ofertat în conversația-dovadă (146, Fără ofertă), așa că l-am scos din `produse` și l-am trecut în titlu și în `conditii`. Am adăugat dovada cu răspunsul clientului.
- **R27-08**: corectată. „Persoanele fizice o primesc după dovada plății” se sprijinea pe un singur caz (176), acum scrie „unei persoane fizice”. Am scos prețul din textul contradicției. Am scos și „livrarea separată pe factură” ca diferență, fiindcă și în 176 livrarea a fost facturată (factura din 181).
- **R27-09**: corectată. „La sistemele livrate de AKRO, inițiativa vine de la AKRO” era o generalizare dintr-un singur caz (176). Acum e descris cazul văzut.
- **R27-10**: corectată. „Fără clorinare” era recomandarea AKRO, nu cererea clientului, așa că am rescris `cand`. Clarificarea despre recirculare era o afirmație a AKRO: am mutat-o în `conditii`, unde am pus și „fără clor”. Ceața de apă, cerută separat de client, nu a primit răspuns, deci nu mai e în `cand`.

### Reguli șterse sau unite

Niciuna. R08-13 și R08-15 se suprapuneau pe conv. 292. Le-am separat prin `cand` (cantitate obișnuită față de lot foarte mare), fără să le unesc.

### Contradicții noi

- R27-05: licitația pentru spitalul din Buftea (606), cu UV fără sistem de curățare deși fișa îl cerea, și LICAM PREST (226), cu modelul de 20 m³/h fără varianta RM.

### Dovezi scoase

- R08-01: conv. 303 (m2150052) și conv. 34 (m2135204). Nu arătau regula și sunt mutate la R08-12 și R08-11.
- R08-13: conv. 292 (două dovezi: depozitul din Belgia și termenul de 10-14 zile), mutate la R08-15.

### Dovezi adăugate

- R08-09: conv. 56 (cere CAPEX și OPEX) și conv. 188 (cere mentenanță și consumabile).
- R08-11: conv. 34 (pretratarea neclară).
- R08-12: conv. 303 (capacitatea și pretratarea).
- R08-13: conv. 482 (stoc în Belgia, oferta din februarie).
- R08-15: conv. 292 (stocul din Belgia, termenul de 10-14 zile, reducerea maximă).
- R27-06: conv. 606 (fără tablou separat, dozare proporțională).
- R27-07: conv. 146 (clientul spune că nu există filtrare sau ozonizare).
- R27-05, la contradicție: conv. 606 și 226.

### Observații: cazuri care nu au putut fi folosite

- Conv. 431 (După vânzare): membrane PWG 4040ND pe contract, cu termen de 5-7 săptămâni și cu manopera de schimb inclusă. Ar fi o variantă la R08-13, dar generatorul nu acceptă dovezi de ofertă din „După vânzare”.
- Conv. 115 (teacă de cuarț cerută cu codul AKRO): fără răspuns în conversație, deci nu e nici dovadă, nici contraexemplu la R27-08.
- Conv. 140: Spectra a cerut de la AKRO configurația de filtrare, cu coduri, iar AKRO a răspuns cu conflictul de proiect („codurile le trimite Dl Aurel”). E altă situație decât R08-17, unde se cere o soluție completă, așa că nu am pus-o la contradicții.
- Conv. 283, 391, 393, 451, 475, 536, 596 și 94 (UV, Fără ofertă): nu au clarificări AKRO către client care să susțină sau să contrazică vreo regulă.


## Grupul 16, 21, 23 și Altele

Fișiere: `reguli/16.json` (13 reguli), `reguli/21.json` (2), `reguli/23.json` (3), `reguli/altele.json` (6). Total 24 de reguli verificate.
Copii ale fișierelor dinainte: `SCRATCH/verificare/backup_grup16/`. Scripturi: `fix_grup16_mici.py`, `fix_grup16_16.py`.

`--verifica`: 16.json 13 reguli, 0 erori · 21.json 2 reguli, 0 erori · 23.json 3 reguli, 0 erori · altele.json 6 reguli, 0 erori. Nicio liniuță lungă (— –) în `explicatie`.

### Pe reguli

#### 16-Prestari servicii
- **R16-01**: corectat. Clarificarea adăugată: când clientul nu e în baza AKRO, AKRO întreabă dacă sistemul a fost cumpărat prin altă firmă și cere o poză (conversația 331, dovadă nouă). Notele precizează unde AKRO a ofertat fără întrebări (383, 428, 575) și unde a întrebat (261, 331). „Curățare capete de vană” scos din servicii: nu apare în nicio dovadă. Rolul liniei 16-002001 spune și numele din nomenclator (deplasare, o persoană și diurnă). Explicație rescrisă.
- **R16-02**: corectat. Eticheta și CMR-ul pentru ridicare apar doar în 263 și 563; în 86 colegii au trimis eticheta și CMR-ul pentru retur. `cand` spune acum și când NU se aplică: pentru buteliile instalației Decker, același client a primit refuz (conversația 100). Rolul 16-001004 arată numele din nomenclator. Explicație rescrisă.
- **R16-03**: corectat puțin. Adăugate plata la 30 de zile (S02555) și faptul că intervenția s-a făcut la 6 zile de la comandă (131). Rolul 16-002001 arată numele din nomenclator. În explicație s-a adăugat ce e osmoza.
- **R16-04**: corectat. Dovada din 103 (S02551: masă și manoperă pe o singură linie 16-001004, ca variantă propusă de AKRO) contrazice „materialele pe linii cu cod”, așa că a fost mutată la contradicții. Contradicție nouă: 82, unde AKRO a refuzat serviciul de schimb al nisipului la filtrele unei uzine de apă și a ofertat doar nisipul. Motivul „aprovizionarea materialelor” pentru termenul de 2-4 săptămâni a fost scos: nu e scris în email. Explicație rescrisă.
- **R16-05**: OK. Doar rolul PC003 precizează că a fost propus în textul emailului (234).
- **R16-07**: corectat. „Firmă de mentenanță a clădirii”: clientul e un constructor (Coral Construct, 142 și 378). „Cantitatea = kilometri” nu e scris nicăieri, așa că a devenit „cantitatea după distanță: 50 pentru Brașov, 600 pentru Iași”. Adăugate plata 100% în avans și motivul pentru care cartușul e singurul consumabil (la ultima revizie nu au fost probleme, 378). Rolurile 16-001011 și 16-001010 arată numele din nomenclator.
- **R16-08**: corectat puțin. Avertismentul vine în oferta (331) sau în confirmarea (142) de verificare. Termenul de 2-3 săptămâni plus 10 zile e marcat ca fiind „într-un caz”. Rolul 16-001015 arată numele din nomenclator (materiale pentru montaj).
- **R16-09**: corectat. „Vanele Siata nu se mai produc” era exagerat: Pentair a oprit producția *unor* vane Siata (103). Adăugat că ofertele au plecat la o oră după întrebări, fără răspunsul clientului. Explicație rescrisă.
- **R16-10**: corectat. Contradicție nouă: 331 (verificare de clorinare fără defect descris), unde AKRO nu a cerut descrierea defectului și nici poze cu panoul, ci a întrebat de unde e sistemul și a cerut o fotografie. „Întreabă dacă are probleme acum” și „număr de contact” apar doar în 19, deci au devenit „uneori”.
- **R16-11**: corectat. Regula descria ca practică ce era doar termenul scris în ofertă. Acum regula e termenul anunțat (1-2 săptămâni sau 7-10 zile), iar contradicția adună cazurile în care intervenția s-a făcut în 1-3 zile. 142 a fost adăugată la contradicție: plata pe 23.07, intervenția pe 24.07, deși confirmarea spunea maximum 14 zile. Dovadă nouă: 331 (comanda pe 01.09, intervenția pe 10.09). Notele arată datele reale.
- **R16-12**: corectat. „Orice intervenție” nu se confirmă: în 131 AKRO a anunțat finalizarea înlocuirii membranelor fără proces verbal atașat (atașamentul era comanda clientului). Asta e acum contradicție. Titlul și `cand` nu mai spun „orice”.
- **R16-14**: corectat. În 331 clientul nu a cerut datele în scris: AKRO a anunțat singur că le trimite, după o discuție la telefon. Nota și `cand` au fost corectate, iar prescurtarea CI a fost scrisă în cuvinte.
- **R16-15**: corectat. Lipsea faptul cel mai important: în martie AKRO a ofertat doar pompele cu PIF și a refuzat execuția traseului, iar în iunie a revenit cu execuția prin colaborator (157). Adăugate scadența execuției (30 de zile de la finalizarea lucrărilor) și clarificarea de după PIF (245: modificări față de comandă și factura schimbată). Explicație rescrisă.

#### 21-Aparatura de analiza si control
- **R21-01**: corectat. Termenul era doar 5-10 zile (471); în 379 a fost 5-7 zile. Ambele sunt acum în text. „Rotunjită la DN-ul standard” era o deducție: AKRO a ofertat DN80 la o cerere de DN75 fără să explice alegerea. Adăugată plata 100% în avans. Explicație rescrisă.
- **R21-02**: OK.

#### 23-Diverse materiale, consumabile
- **R23-01**: corectat. „Ofertează EDC pentru că trimite semnalul la fel” era motivul greșit: EDC era singura variantă din stocul furnizorului, iar „trimite semnal la fel” a fost doar precizarea lui AKRO (320). 23-001189 nu are linie OFERTĂ în 23; rolul spune acum că AKRO a trimis confirmarea de comandă acolo. Explicație rescrisă.
- **R23-02**: corectat. Adăugat serviciul de postare în SICAP pentru clientul public, cu dovadă nouă (67, m2136356). Adăugate plata în avans și faptul că linia ofertei arată 10 zile, iar emailul 5-7 zile.
- **R23-04**: corectat. „AKRO refuză” a devenit „nu face ofertă”: AKRO spune că produsul se mai aduce doar la palet întreg (494). Simbolul „x” a fost scris în cuvinte.

#### Altele / neclar
- **RA-01**: corectat. „Precizează domeniul său” a apărut doar în 337 și 473, nu și în 508. În 606 stația de ape uzate a fost lăsată deoparte fără nicio explicație în email, iar `conditii` și nota spun acum asta.
- **RA-02**: OK.
- **RA-03**: corectat puțin. Explicația începe acum de la întâlnire, pentru ordinea reală a pașilor (453). Adăugate două dovezi de clarificare din aceeași conversație: întrebarea despre aspirația din bazine (m2157860) și întrebările producătorului UV (m2097380).
- **RA-04**: corectat puțin. „Fișa tehnică pentru fiecare echipament” era prea larg: pentru lance nu e fișă. Acum lista arată fișele atașate de fapt (606). În explicație s-a adăugat formularul F5.
- **RA-05**: corectat. Dovada era un citat dintr-un mesaj retrimis în 532 (alt subiect, rezervorul). A fost înlocuită cu conversația originală, 510 (S02863), cu trei dovezi: confirmarea fineței, cele 2 pungi de bile și reducerea de 3%. Adăugat produsul 11-002100 (bilele de curățare). „Finețea ofertată” a devenit „finețea cerută”, pentru că diferența era între cerere și achizițiile trecute.
- **RA-06**: OK.

### Reguli șterse sau unite
Niciuna.

### Contradicții noi
1. R16-04: conversația 103. Masa și manopera pe o singură linie 16-001004 (dovadă mutată din `dovezi`).
2. R16-04: conversația 82. Serviciul de schimb a fost refuzat la filtrele atmosferice ale unei uzine, AKRO a ofertat doar nisipul.
3. R16-10: conversația 331. La o verificare fără defect, AKRO a întrebat de proveniența sistemului, nu de defect și de panou.
4. R16-12: conversația 131. Email de finalizare fără proces verbal.
5. R16-11 (contradicție existentă, extinsă): conversația 142. Intervenția s-a făcut a doua zi după plată.

### Dovezi scoase sau adăugate
- Scoase: R16-04, conversația 103 (mutată la contradicții); RA-05, conversația 532 (înlocuită cu 510).
- Adăugate: R16-01, 331 (clarificare); R16-11, 331 (ofertă); R16-11 la contradicție, 142; R16-15, 157 (refuzul traseului din martie și scadența execuției) și 245 (clarificare după PIF); R23-02, 67 (SICAP); RA-03, 453 (două clarificări); RA-05, 510 (trei dovezi).

### Neadăugate, cu motiv
Conversațiile După vânzare 19, 75, 148, 191, 271, 279 și 352 confirmă tipare din R16-04, R16-08 și R16-12, dar ar fi intrat ca dovezi de ofertă, iar generatorul acceptă din ele doar clarificări. În 352, factura a venit în același email cu procesul verbal, deci e o abatere de la R16-12. Nu a putut fi pusă ca dovadă din același motiv.


## Grupul reguli generale

Sursa numerelor: conversațiile complete cu document Odoo (ofertă sau confirmare de comandă) din textul complet al conversațiilor, numărate pe conversație; numerele de conversație sunt câmpul `nr`.

### Pe reguli

- **RG-01** – dovezi noi: conversațiile 545, 137, 207, 586, 395; contradicție nouă (conversațiile 292 și 272: întrebări sau cantitate schimbată deși codul era exact); «cand» restrâns la produse din portofoliu
- **RG-02** – scoasă dovada din conversația 394 (AKRO avea pompa AML, doar a preferat alt model); conversația 187 (PROMAX 20) mutată la contradicție, fiindcă nu s-a propus un echivalent; dovezi noi: conversațiile 426 și 486; contradicție nouă: fără echivalent AKRO refuză (conversațiile 14, 486, 187)
- **RG-03** – dovezi noi: conversațiile 57, 469, 266; explicația nu mai spune că analiza se cere «întâi» (ordinea întrebărilor diferă de la caz la caz)
- **RG-04** – clarificări dublate unite; nota conversației 242 rescrisă (arăta altceva decât citatul); contradicție nouă: licitații ofertate direct, fără întrebări (conversațiile 31, 73, 601)
- **RG-05** – «de obicei» scos din explicație; nota conversației 606 rescrisă; contradicție nouă: licitații refuzate pentru că AKRO nu avea nimic apropiat (conversațiile 109, 133, 107)
- **RG-06** – scoasă conversația 107 (AKRO nu a ofertat nimic, nu doar o parte; mutată la contradicțiile regulii despre licitații); dovezi noi: conversațiile 31, 580, 643
- **RG-07** – dovadă nouă: conversația 121; contradicție nouă: conversația 457 (refuz direct, fără întrebare); explicația nu mai spune că AKRO întreabă de fiecare dată
- **RG-08** – frecvența corectată: fișa tehnică apare în aproximativ 60 din 99 de conversații cu ofertă, nu la orice ofertă; fișa de securitate pleacă la antiscalant în toate cele 6 conversații, dar la cărbunele activ doar în 2 din 4; dovezi noi: conversațiile 560, 454, 121; două contradicții noi (conversațiile 65, 284, 112, 69; 206, 81)
- **RG-09** – «de obicei» înlocuit cu numărătoarea reală pe cele 79 de conversații complete cu produse de acest tip: 100% avans în 29, 30 sau 45 de zile în 21, plată împărțită în 12, de stabilit la contractare în 1, fără termen tipărit în 16; scos «clienți fără istoric de credit» (nu reiese din emailuri); dovezile și contradicțiile cuprind acum toate conversațiile (29, 21 și 13)
- **RG-10** – «de obicei 50/50» corectat cu numărătoarea pe cele 45 de conversații complete cu stații și echipamente: 50% avans și 50% la gata de livrare în 10, de stabilit la contractare în 16, alte eșalonări în 13, integral în avans sau la 30 de zile în 5; mutate la regula consumabilelor conversațiile 394, 206, 646, 216 (componente, cărbune, pompe, service); conversația 84 mutată la «alte eșalonări» (50% la livrare, nu la gata de livrare); contradicție nouă: plată integrală în avans sau la 30 de zile
- **RG-11** – scoasă conversația 646 (clientul nu a cerut alt termen; AKRO a păstrat din proprie inițiativă condițiile din 2022); dovadă nouă: conversația 397 (aprobarea managerului general); «de regulă, cu aprobare internă» înlocuit cu ce s-a văzut: acceptare, uneori cu aprobarea conducerii
- **RG-12** – «de obicei» confirmat și numărat: «In sarcina Akro» în 111 din 124 conversații complete cu document Odoo (la serviciile fără livrare termenul lipsește); dovezile cuprind acum toate cele 111 conversații; conversația 149 rămâne doar la contradicție (oferta avea livrarea în sarcina beneficiarului)
- **RG-13** – «de obicei scrie în email» corectat: mențiunea «transport inclus» apare în 14 conversații și transportul estimat separat în 3, dar în 17 conversații oferta are o linie separată de livrare cu preț (contradicție nouă cu toate aceste conversații); dovezi noi: conversațiile 15, 7, 82, 278, 305, 374, 415, 586
- **RG-14** – intervalele corectate: din stocul din Brașov 1-3 zile (conversațiile 15, 585), din stocul furnizorului până la 2 săptămâni (conversația 284), la producător până la 18 săptămâni (conversația 104); termenul apare și pe linia ofertei Odoo (în 29 de conversații), nu doar în email; dovezi noi: conversațiile 15, 585, 284, 104
- **RG-15** – dovezi noi: conversațiile 113, 204, 162, 336
- **RG-16** – «ofertele trec de obicei 12 luni, la echipamente și la produse» corectat: rândul de garanție lipsește în 65 din 124 conversații (consumabile, chimicale, mase filtrante, servicii), deci «cand» e restrâns la echipamente; 12 luni în 47 conversații, 24 de luni în 12; dovezile și contradicția cuprind acum toate aceste conversații
- **RG-17** – explicația și contradicția completate cu garanția standard de 24 de luni de la UMF Timișoara (conversația 601); clarificarea «Se acceptă extinderea contra cost?» scoasă (AKRO nu o pune, doar spune costul); notele rescrise
- **RG-18** – scoase din dovezi conversațiile 375 și 580 (arătau montajul și PIF-ul incluse, deci erau deja contradicții); scoasă contradicția despre transportul de la Terax (nu ține de montaj, iar PIF-ul contra cost din aceeași conversație susține regula); note rescrise
- **RG-19** – «adesea» numărat: reducere reală pe linie în 26 din 124 conversații complete cu document Odoo (plus două doar cu un produs bonus la 99%); condiția «discount mai mare la plata în avans» corectată în «reducere valabilă doar la plata integrală în avans» (conversația 140); dovadă nouă: conversația 153 (produs bonus cu 99%)
- **RG-20** – numărat: 30 de zile în 93 din 94 conversații complete cu oferta tipărită (excepția de 48 de zile era deja la contradicții); dovezile cuprind acum toate cele 93 de conversații (la două dintre ele dovada rămasă e cererea clientului privind valabilitatea, câte una pe conversație); dovadă de cerere nouă: conversația 188
- **RG-21** – frecvența corectată: din 60 de conversații complete în care clientul nu mai scrie după ofertă, AKRO revine doar în 6 (în total cere feedback în 9 conversații); contradicție nouă cu exemple fără revenire (conversațiile 284, 65, 113)
- **RG-22** – dovadă nouă: conversația 157
- **RG-23** – dovezi noi: conversațiile 234 și 140
- **RG-24** – scoase din dovezi conversațiile 7, 472, 565 (erau deja contradicții: preț în lei cu TVA pentru persoane fizice); «cand» lărgit cu pozițiile opționale de lângă o ofertă Odoo (conversațiile 377, 595, 632 aveau și ofertă Odoo); note rescrise
- **RG-25** – «EUR la echipamente și produse din import» corectat: EUR în 60 și RON în 40 din 99 conversații complete cu ofertă Odoo, inclusiv stații în RON; conversația 30 (antiscalant) avea oferta în EUR și confirmarea în RON; dovezile și contradicția cuprind acum toate conversațiile
- **RG-26** – scoasă conversația 560 (clientul anunță achiziția prin SEAP, dar conversația nu arată postarea făcută de AKRO); clarificări dublate unite
- **RG-27** – OK (doar o clarificare rescrisă fără paranteză prescurtată)
- **RG-28** – «cand» și titlul lărgite: trei dovezi (conversațiile 171, 469, 435) arătau poze cerute pentru montajul unui echipament nou, nu pentru service; clarificări dublate unite; note rescrise
- **RG-29** – «în cantitate mică» scos (prin formular au venit și cereri de 7 și 23 de tone de nisip); «de regulă direct» înlocuit cu «adesea»; condiția «cu livrare inclusă» scoasă (unele oferte au livrarea pe linie separată); contradicție nouă: întrebări înainte de ofertă (conversațiile 80 și 296)

### Reguli șterse sau unite

Niciuna. Fiecare regulă are cel puțin o conversație care o susține, iar regulile nu se suprapun (plata la consumabile și plata la echipamente au rămas separate, cu grupe de conversații disjuncte).

### Contradicții noi (11) și contradicții existente rescrise

Cele marcate «rescrisă» existau deja; textul lor a fost corectat și dovezile completate cu toate conversațiile numărate.

- RG-01: Și la cereri pe cod exact AKRO a pus uneori întrebări înainte de ofertă: la 100 de membrane ESPA2 MAX a întrebat locul și termenul de livrare dorit, iar la cartușele Atlas CA-SE-10-SX a propus cutia întreagă de 12 bucăți și un termen de 7-8 săptămâni, cerând acceptul clientului. (conversațiile 272, 292)
- RG-02: Când nu există niciun echivalent, AKRO nu propune nimic în loc: spune că nu are produsul (cartușul pentru sablare, biocidul Vinkocide DBNPA 20) sau oferă doar un produs înrudit (la pompa de spălare PROMAX 20, doar soluția de dezincrustare). (conversațiile 14, 187, 486)
- RG-04: La unele licitații cu caiet de sarcini sau fișă tehnică AKRO a trimis direct oferta, fără să întrebe stadiul, beneficiarul sau bugetul (Amnaș, Regimentul 46 Sibiu, UMF Timișoara). (conversațiile 31, 73, 601)
- RG-05: La unele licitații AKRO nu a avut nimic apropiat și a refuzat ofertarea: stația cabinet casnică de 10 litri pentru creșa din Alexandru cel Bun, filtrele PN20 de la Saschiz și echipamentele PN16 cu automatizare pentru Spitalul Gerota. (conversațiile 107, 109, 133)
- RG-07: La stațiile de electroclorinare pentru un proiect din Argeș AKRO nu a mai întrebat dacă oferta se acceptă fără certificări: a spus direct că nu are certificarea de biocid și avizul sanitar cerute și nu a ofertat. (conversațiile 457)
- RG-08: La multe comenzi pe cod oferta a plecat fără fișă tehnică, de exemplu la pompele TPG600, la membranele HSRO, la sacii filtranți nylon și la cele 10 tone de Pyrolox. (conversațiile 65, 69, 112, 284)
- RG-08: La cărbunele activ fișa de securitate nu a plecat mereu: la cărbunele pudră s-a trimis doar fișa tehnică, iar la cărbunele LG85 cu nisip oferta a plecat fără niciun document atașat. (conversațiile 81, 206)
- RG-09: (rescrisă) La produse de același tip (cartușe, antiscalant, pompe, contoare, mase filtrante, piese, servicii) oferta are «Condiții de plată: 30 de zile» (20 de conversații) sau 45 de zile (membranele pentru Coca-Cola); de câteva ori clientul, de pildă o instituție care cumpără prin SEAP, ceruse el plata la 30 de zile. (conversațiile 46, 55, 69, 81, 131, 234, 272, 284, 320, 339, 363, 383, 400, 438, 510, 516, 526, 533, 545, 560, 589)
- RG-10: (rescrisă) La 16 oferte de stații și proiecte (multe pentru licitații) plata nu se fixează: «se va stabili» sau «se va discuta la momentul contractarii». (conversațiile 31, 53, 57, 73, 153, 171, 226, 251, 376, 453, 556, 580, 595, 601, 619, 632)
- RG-10: (rescrisă) Alte eșalonări în aceeași situație (13 conversații): 30% avans și 70% la 30 de zile, 40% avans, 30% la gata de livrare și 30% la 30 de zile, 30% avans și restul la 15 zile, 50% avans și restul la livrare sau la 5 ori 15 zile după livrare, 35% avans și 65% la gata de livrare, ori formula de licitație «O.P., cash, CEC sau bilet la ordin». (conversațiile 5, 47, 51, 84, 104, 188, 207, 397, 404, 569, 586, 606, 608)
- RG-10: Câteva oferte de echipamente au avut plata integrală în avans (stațiile pentru un apartament și un penthouse, UV și clorinare pentru un spital) sau la 30 de zile (stația de dedurizare pentru Airbus, filtrele Y). (conversațiile 140, 210, 372, 377, 426)
- RG-13: În 17 conversații oferta din Odoo are livrarea pe o linie separată, cu preț propriu («Livrare si ambalare», «Livrare si ambalare pallex - intern», «AMBALARE LIVRARE ASIGURARE», «Transport marfa»), mai ales la comenzi mici de cartușe, saci filtranți și piese. (conversațiile 86, 112, 149, 263, 272, 301, 334, 336, 339, 350, 363, 395, 400, 509, 516, 563, 589)
- RG-16: (rescrisă) Alte oferte de echipamente, din aceleași categorii, au 24 de luni de la livrare (12 conversații, între care două licitații cu varianta «12/24 luni»). (conversațiile 5, 51, 73, 84, 114, 149, 210, 379, 471, 472, 601, 606)
- RG-21: În cele mai multe oferte rămase fără răspuns (54 din 60) conversația nu arată nicio revenire a AKRO, de exemplu la membranele pentru Coca-Cola, la pompele TPG600 sau la sacii filtranți Allied Filters. (conversațiile 65, 113, 284)
- RG-25: (rescrisă) Aceleași tipuri de produse au fost ofertate și în RON (40 de conversații): pompe SEKO, antiscalant RO1, membrane de osmoză, cartușe, stații de dedurizare, servicii. (conversațiile 8, 15, 67, 69, 81, 82, 97, 103, 114, 137, 173, 210, 261, 281, 292, 305, 331, 350, 363, 372, 375, 377, 378, 383, 395 ...)
- RG-29: La unele cereri din formular AKRO nu a ofertat direct, ci a pus întâi întrebări: la înlocuirea maselor filtrante (ce masă există, ce cantitate, ce tip de filtre) și la generatorul de ozon (scopul și capacitatea). (conversațiile 80, 296)

### Dovezi scoase și adăugate (numere de conversație)

- RG-01: dovezi adăugate (5): 137, 207, 395, 545, 586; la contradicții adăugate (2): 272, 292
- RG-02: dovezi adăugate (2): 426, 486; dovezi scoase (2): 187, 394; la contradicții adăugate (3): 14, 187, 486
- RG-03: dovezi adăugate (3): 57, 266, 469
- RG-04: la contradicții adăugate (3): 31, 73, 601
- RG-05: la contradicții adăugate (3): 107, 109, 133
- RG-06: dovezi adăugate (3): 31, 580, 643; dovezi scoase (1): 107
- RG-07: dovezi adăugate (1): 121; la contradicții adăugate (1): 457
- RG-08: dovezi adăugate (3): 121, 454, 560; la contradicții adăugate (6): 65, 69, 81, 112, 206, 284
- RG-09: dovezi adăugate (20): 30, 103, 137, 142, 169, 173, 204, 261, 281, 328, 334, 336, 379, 454, 458, 459, 470, 472, 482, 585; la contradicții adăugate (24): 55, 69, 80, 82, 131, 200, 206, 216, 234, 257, 284, 305, 310, 339, 383, 394, 400, 415, 438, 510, 526, 533, 571, 646; scoase din contradicții (1): 280
- RG-10: dovezi adăugate (6): 114, 242, 280, 407, 512, 565; dovezi scoase (3): 84, 206, 394; la contradicții adăugate (23): 5, 31, 84, 140, 153, 207, 210, 251, 372, 376, 377, 397, 404, 426, 453, 569, 586, 595, 601, 606, 608, 619, 632; scoase din contradicții (2): 216, 646
- RG-11: dovezi adăugate (1): 397; dovezi scoase (1): 646
- RG-12: dovezi adăugate (101): 15, 30, 31, 47, 51, 53, 57, 69, 73, 80, 81, 82, 84, 86, 97, 103, 104, 112, 113, 114, 137, 138, 140, 153, 162, 171, 173, 200, 204, 206, 207, 210, 216, 226, 242, 248, 251, 257, 261, 263, 272, 280, 281, 284, 292, 301, 305, 310, 320, 328, 331, 334, 336, 339, 350, 363, 375, 376, 377, 379, 395, 397, 400, 404, 407, 415, 426, 438, 453, 454, 459, 470, 472, 482, 509, 510, 512, 516, 526, 527, 533, 545, 556, 560, 563, 565, 569, 571, 575, 580, 585, 586, 589, 595, 601, 613, 614, 619, 632, 646, 649
- RG-13: dovezi adăugate (8): 7, 15, 82, 278, 305, 374, 415, 586; la contradicții adăugate (16): 86, 112, 263, 272, 301, 334, 336, 339, 350, 363, 395, 400, 509, 516, 563, 589
- RG-14: dovezi adăugate (4): 15, 104, 284, 585
- RG-15: dovezi adăugate (4): 113, 162, 204, 336
- RG-16: dovezi adăugate (40): 31, 47, 53, 57, 65, 104, 137, 138, 153, 171, 207, 226, 242, 251, 280, 281, 320, 347, 372, 375, 376, 377, 397, 404, 426, 453, 459, 533, 545, 556, 565, 569, 580, 586, 595, 614, 619, 632, 646, 649; la contradicții adăugate (7): 5, 51, 114, 210, 472, 601, 606
- RG-17: la contradicții adăugate (1): 601
- RG-18: dovezi scoase (2): 375, 580; scoase din contradicții (1): 149
- RG-19: dovezi adăugate (1): 153
- RG-20: dovezi adăugate (81): 5, 15, 30, 31, 47, 53, 57, 69, 73, 80, 81, 82, 84, 97, 103, 104, 112, 113, 114, 137, 140, 149, 153, 171, 173, 204, 206, 210, 216, 226, 234, 242, 251, 257, 261, 280, 281, 284, 292, 305, 320, 331, 334, 336, 339, 347, 350, 363, 372, 375, 376, 378, 379, 383, 395, 397, 404, 415, 426, 428, 453, 454, 459, 470, 510, 512, 516, 545, 560, 565, 569, 571, 580, 585, 586, 589, 601, 606, 619, 632, 646
- RG-21: la contradicții adăugate (3): 65, 113, 284
- RG-22: dovezi adăugate (1): 157
- RG-23: dovezi adăugate (2): 140, 234
- RG-24: dovezi scoase (3): 7, 472, 565
- RG-25: dovezi adăugate (56): 5, 31, 46, 47, 51, 53, 57, 73, 80, 84, 104, 112, 113, 140, 146, 149, 153, 169, 171, 188, 204, 206, 207, 210, 216, 226, 234, 242, 251, 257, 280, 320, 334, 336, 339, 347, 376, 379, 394, 407, 426, 453, 458, 459, 510, 512, 516, 556, 569, 580, 589, 595, 606, 608, 619, 632; la contradicții adăugate (35): 15, 67, 69, 81, 82, 97, 114, 173, 210, 261, 281, 305, 331, 350, 363, 372, 375, 377, 378, 383, 397, 404, 415, 428, 454, 470, 472, 545, 560, 565, 571, 585, 586, 601, 646
- RG-26: dovezi scoase (1): 560
- RG-29: la contradicții adăugate (2): 80, 296

### Verificare

`python3 genereaza_reguli.py --verifica reguli/general.json` → 29 reguli verificate, 0 erori. Nicio liniuță de separare (— sau –) în câmpurile `explicatie`.
