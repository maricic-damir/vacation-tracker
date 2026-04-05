# Vacation Tracker - Korisnički priručnik (Srpski)

## Sadržaj
1. [Uvod](#uvod)
2. [Instalacija i podešavanje](#instalacija-i-podešavanje)
3. [Konfiguracija pri prvom pokretanju](#konfiguracija-pri-prvom-pokretanju)
4. [Pregled korisničkog interfejsa](#pregled-korisničkog-interfejsa)
5. [Upravljanje zaposlenima](#upravljanje-zaposlenima)
6. [Konfiguracija radnih dana](#konfiguracija-radnih-dana)
7. [Upravljanje danima godišnjeg odmora](#upravljanje-danima-godišnjeg-odmora)
8. [Upravljanje praznicima](#upravljanje-praznicima)
9. [Poslovna pravila i kalkulacije](#poslovna-pravila-i-kalkulacije)
10. [Izveštaji i štampanje](#izveštaji-i-štampanje)
11. [Rešavanje problema](#rešavanje-problema)

---

## Uvod

**Vacation Tracker** je desktop aplikacija dizajnirana da vam pomogne u praćenju dana godišnjeg odmora zaposlenih u skladu sa srpskim zakonima o radu. Aplikacija je napravljena za Windows i može se deliti između dva korisnika čuvanjem baze podataka u sinhronizovanom folderu (npr. OneDrive).

### Ključne funkcionalnosti
- Praćenje dana godišnjeg odmora za više zaposlenih
- **Fleksibilni radni rasporedi**: Podrška za 5-dnevnu (pon-pet) i 6-dnevnu radnu nedelju
- **Pametne kalkulacije godišnjeg**: Automatska kalkulacija radnih dana (isključuje odgovarajuće vikende i praznike)
- **Ispravne kvote godišnjeg**: 20 dana za 5-dnevne radnike, 24 dana za 6-dnevne radnike
- Podrška za različite tipove ugovora (na određeno i neodređeno vreme)
- Filtriranje praznika po veri (pravoslavni i katolički)
- Automatski prenos neiskorišćenih dana na kraju godine
- Kompletna istorija i izveštavanje o godišnjem odmoru
- Dvojezični interfejs (engleski i srpski)

---

## Instalacija i podešavanje

### Sistemski zahtevi
- **Operativni sistem:** Windows 10 ili noviji (može i na macOS/Linux sa Python-om)
- **Python:** 3.10 ili viši (samo ako se pokreće iz izvornog koda)
- **Prostor na disku:** ~50 MB za aplikaciju + bazu podataka

### Opcije instalacije

#### Opcija 1: Korišćenje samostalne EXE datoteke (preporučeno za Windows)
1. Preuzmite `VacationTracker.exe` iz vašeg izvora distribucije
2. Postavite EXE datoteku u folder po vašem izboru
3. Dvoklikom na `VacationTracker.exe` pokrenite aplikaciju
4. Instalacija Python-a nije potrebna!

#### Opcija 2: Pokretanje iz izvornog koda
1. Instalirajte Python 3.10 ili viši sa [python.org](https://python.org)
2. Raspakujte vacation_tracker folder na željenu lokaciju
3. Otvorite Command Prompt ili Terminal u vacation_tracker folderu
4. Instalirajte zavisnosti:
   ```bash
   pip install -r requirements.txt
   ```
5. Pokrenite aplikaciju:
   ```bash
   python main.py
   ```

### Kreiranje EXE datoteke (napredno)
Ako želite da sami kreirate samostalnu EXE datoteku iz izvornog koda:
```bash
pip install pyinstaller
pyinstaller vacation_tracker.spec
```
EXE datoteka će biti kreirana u `dist/` folderu.

---

## Konfiguracija pri prvom pokretanju

### Podešavanje lokacije baze podataka

Kada pokrenete aplikaciju prvi put, biće vam zatraženo da odaberete gde da se čuva datoteka baze podataka.

#### Prvo pokretanje (nema postojeće baze)
1. Pojaviće se dijalog: **"Choose database location"**
2. Kliknite **Browse** da odaberete folder
3. **Važno:** Ako delite sa drugim korisnikom, odaberite sinhronizovan folder (npr. OneDrive, Google Drive)
4. Kliknite **Save**
5. Datoteka `vacation.db` će biti kreirana u odabranom folderu

#### Pronalaženje postojeće baze podataka
Ako je aplikacija ranije konfigurirana ali ne može da pronađe bazu (npr. na novom računaru ili nakon pomeranja datoteka):
1. Pojaviće se dijalog: **"Locate database"**
2. Kliknite **Browse** da pronađete postojeću `vacation.db` datoteku
3. Navigirajte do mesta gde je datoteka smeštena (npr. OneDrive folder)
4. Odaberite datoteku i kliknite **Open**

### Lokacija konfiguracijske datoteke
Aplikacija pamti lokaciju vaše baze u konfiguracionoj datoteci:
- **Windows:** `C:\Users\VašeIme\AppData\Roaming\VacationTracker\config.ini`
- **macOS/Linux:** `~/.VacationTracker/config.ini`

Ova datoteka sadrži samo putanju do vaše baze - NE sadrži stvarne podatke o zaposlenima.

---

## Pregled korisničkog interfejsa

### Glavni ekrani

Aplikacija ima tri glavna ekrana:

#### 1. Ekran liste zaposlenih (početni ekran)
Ovo je glavni ekran koji vidite kada otvorite aplikaciju.

**Šta vidite:**
- Tabela koja prikazuje sve zaposlene sa kolonama:
  - **JMBG:** Jedinstveni matični broj građanina
  - **Ime:** Puno ime (Ime + Prezime)
  - **Ugovor:** Tip ugovora (Na određeno / Na neodređeno vreme)
  - **Početak ugovora:** Datum kada je zaposlenje počelo
  - **Preostalo dana:** Preostali dani godišnjeg za trenutnu godinu
  - **Status:** Aktivan ili Arhiviran

**Akcije koje možete preduzeti:**
- **Dvoklikom na red:** Otvara detaljni prikaz za tog zaposlenog
- **Dugme Dodaj zaposlenog:** Dodaje novog zaposlenog u sistem
- **Dugme Svi rasporedi:** Prikazuje sve zakazane i završene godišnje odmore
- **Dugme Praznici / Podešavanja:** Upravljanje državnim praznicima i neradnim danima

**Prebacivanje jezika:**
- Gornji desni ugao: Prebacivanje između engleskog i srpskog

#### 2. Ekran detalja zaposlenog
Otvara se kada dvokliknete na zaposlenog iz liste.

**Šta vidite:**
- **Detalji zaposlenog:** JMBG, ime, informacije o ugovoru, vera
- **Tabela godišnjeg balansa:** Prikazuje raspored dana godišnjeg za trenutnu godinu
  - Dana na početku: Početna alokacija za godinu (20 za 5-dnevne, 24 za 6-dnevne radnike)
  - Preneto: Dani preneti iz prethodne godine (važe samo do juna)
  - Zarađeno: Dodatni dani zarađeni (darivanje krvi, prekovremeni rad, itd.)
  - Iskorišćeno: Ukupno uzeti dani
  - Preostalo: Preostali dostupni dani
- **Tabela iskorišćenih slobodnih dana:** Svi završeni godišnji odmori sa detaljima odbitaka
- **Tabela zarađenih dana:** Istorija zarađenih dodatnih dana

**Akcije koje možete preduzeti:**
- **Nazad na listu:** Povratak na listu zaposlenih
- **Dugme Datum / Tip ugovora:** Uređivanje informacija o ugovoru i veri
- **Dugme Postavi prenete dane:** Postavlja koliko je dana preneto iz prethodne godine
- **Dugme Zakaži godišnji / slobodan dan:** Rezerviše novi period godišnjeg
- **Dugme Dodaj zarađene dane:** Dodaje dodatne zarađene dane (darivanje krvi, itd.)
- **Dugme Štampaj:** Generiše izveštaj za štampanje za ovog zaposlenog

#### 3. Ekran svih raspoređa
Prikazuje sve zapise o godišnjem odmoru svih zaposlenih.

**Šta vidite:**
- Tabela sa kolonama:
  - **JMBG:** Identifikator zaposlenog
  - **Ime:** Ime zaposlenog
  - **Datum rezervacije:** Kada je godišnji zakazan
  - **Početak:** Datum početka godišnjeg
  - **Kraj:** Datum kraja godišnjeg
  - **Dani:** Broj radnih dana oduzet
  - **Status:** Završeno ili Zakazano

**Akcije koje možete preduzeti:**
- **Nazad na listu:** Povratak na listu zaposlenih
- Pregled svih godišnjih odmora na jednom mestu za potrebe planiranja

---

## Upravljanje zaposlenima

### Dodavanje novog zaposlenog

1. Sa **ekrana liste zaposlenih**, kliknite **Dodaj zaposlenog**
2. Popunite formu:
   - **JMBG:** 13-cifreni jedinstveni matični broj (obavezno, mora biti jedinstven)
   - **Ime:** Ime zaposlenog (obavezno)
   - **Prezime:** Prezime zaposlenog (obavezno)
   - **Vera:** Pravoslavna ili Katolička (utiče na to koji praznici se primenjuju)
   - **Tip ugovora:** 
     - **Na neređeno vreme:** Stalno zaposlenje (automatski dobija dane godišnjeg)
     - **Na određeno vreme:** Privremeni ugovor
   - **Datum početka ugovora:** Kada je zaposlenje počelo (opciono, koristi se za proporcionalno računanje)
   - **Datum kraja ugovora:** Kada ugovor ističe (samo za ugovore na određeno vreme)
   - **Radni dani nedeljno:** 5 dana (pon-pet) ili 6 dana (pon-sub)
3. Kliknite **Sačuvaj**

**Važne napomene:**
- Ugovori na neređeno vreme automatski dobijaju dane godišnjeg na početku svake kalendarske godine:
  - **20 dana** za zaposlene sa 5-dnevnom radnom nedeljom
  - **24 dana** za zaposlene sa 6-dnevnom radnom nedeljom
- Ugovori na određeno vreme počinju sa 0 dana i moraju se ručno konfigurisati
- Podešavanje vere određuje koji verski praznici se računaju kao neradni dani
- Podešavanje radnih dana nedeljno utiče i na kvotu godišnjeg i na kalkulacije vikenda

### Uređivanje informacija o ugovoru zaposlenog

1. Otvorite ekran detalja zaposlenog (dvoklikom iz liste)
2. Kliknite **Datum / Tip ugovora**
3. Izmenite informacije:
   - Promenite tip ugovora (određeno ↔ neređeno vreme)
   - Ažurirajte datum kraja ugovora
   - Ažurirajte datum početka ugovora
   - Promenite veru (Pravoslavna ↔ Katolička)
   - Promenite radne dane nedeljno (5 ↔ 6 dana)
4. Kliknite **Sačuvaj**

**Efekat promena:**
- Promena sa određenog na neređeno vreme će dodeliti dane godišnjeg za trenutnu godinu (20 ili 24 dana na osnovu radnog raspoređa)
- Promena radnih dana nedeljno će preračunati kvotu godišnjeg za trenutnu godinu
- Promena vere će preračunati postojeće zapise godišnjeg na osnovu novog skupa praznika

### Arhiviranje zaposlenih

Trenutno, zaposleni ne mogu biti obrisani iz sistema (radi čuvanja istorijskih zapisa). Međutim, neaktivni zaposleni mogu biti označeni statusom "Arhiviran" da se sakriju iz aktivnih listi.

*Napomena: Ova funkcionalnost može biti dodana u budućoj verziji.*

---

## Konfiguracija radnih dana

### Razumevanje radnih raspoređa

Aplikacija podržava dva tipa radnih raspoređa koji utiču na kalkulacije godišnjeg:

#### 5-dnevna radna nedelja (ponedeljak-petak)
- **Moderni kancelarijski raspored**
- **Kvota godišnjeg**: 20 dana godišnje za ugovore na neređeno vreme
- **Vikendi**: Subota i nedelja su neradni dani (nikad se ne oduzimaju od godišnjeg)
- **Najbolje za**: Kancelarijske radnike, rad na daljinu, moderna preduzeća

#### 6-dnevna radna nedelja (ponedeljak-subota)  
- **Tradicionalni raspored**
- **Kvota godišnjeg**: 24 dana godišnje za ugovore na neređeno vreme
- **Vikendi**: Samo nedelja je neradni dan (subota je radni dan)
- **Najbolje za**: Maloprodaju, proizvodnju, tradicionalna preduzeća

### Podešavanje radnog raspoređa za nove zaposlene

Kada dodajete novog zaposlenog:

1. Popunite osnovne informacije (JMBG, ime, itd.)
2. Potražite padajući meni **"Radni dani nedeljno"**
3. Odaberite:
   - **5 dana nedeljno** za radnike ponedeljak-petak
   - **6 dana nedeljno** za radnike ponedeljak-subota
4. Sistem automatski postavlja ispravnu kvotu godišnjeg

### Promena radnog raspoređa za postojeće zaposlene

1. Otvorite ekran detalja zaposlenog (dvoklikom iz liste)
2. Kliknite **"Datum / Tip ugovora"**
3. Pronađite padajući meni **"Radni dani nedeljno"**
4. Promenite sa 5 na 6 dana (ili obrnuto)
5. Kliknite **Sačuvaj**

**Šta se dešava kada promenite raspored:**
- Kvota godišnjeg se automatski preračunava za trenutnu godinu
- Buduće kalkulacije godišnjeg koriste nova pravila za vikende
- Postojeći zapisi godišnjeg ostaju nepromenjeni

### Uticaj na kalkulacije godišnjeg

Radni raspored utiče na to kako se računaju dani godišnjeg:

**Primer: Zaposleni traži subotu-nedelju slobodno**

- **5-dnevni radnik**: 0 dana oduzeto (oba su vikendi)
- **6-dnevni radnik**: 1 dan oduzet (subota je radni dan, nedelja je vikend)

**Primer: Zaposleni traži ponedeljak-petak slobodno (5 radnih dana, bez praznika)**

- **5-dnevni radnik**: 5 dana oduzeto
- **6-dnevni radnik**: 5 dana oduzeto (isti rezultat)

---

## Upravljanje danima godišnjeg odmora

### Razumevanje tipova dana

Aplikacija prati tri tipa dana godišnjeg odmora:

1. **Dani na početku**
   - Dodeljeni na početku svake godine na osnovu radnog raspoređa:
     - **20 dana** za zaposlene sa 5-dnevnom radnom nedeljom (ugovori na neređeno vreme)
     - **24 dana** za zaposlene sa 6-dnevnom radnom nedeljom (ugovori na neređeno vreme)
   - 0 dana za ugovore na određeno vreme (osim ako se ručno ne postavi)

2. **Preneti dani**
   - Neiskorišćeni dani iz prethodne godine
   - **Važno:** Važe samo do 30. juna trenutne godine
   - Posle juna, preneti dani se više ne računaju u "Preostalo dana"

3. **Zarađeni dani**
   - Dodatni dani zarađeni tokom godine
   - Primeri: darivanje krvi, kompenzacija prekovremenog rada, posebno priznanje
   - Ovi dani se mogu koristiti bilo kada

### Redosled oduzimanja

Kada zaposleni uzme godišnji, dani se oduzimaju ovim redosledom:

1. **Prvo:** Preneti dani (iz prethodne godine)
2. **Drugo:** Dani na početku (alokacija ove godine)
3. **Treće:** Zarađeni dani (darivanje krvi, itd.)

Ovo osigurava da se preneti dani koriste pre nego što isteknu u junu.

### Zakazivanje godišnjeg odmora

1. Otvorite ekran detalja zaposlenog
2. Kliknite **Zakaži godišnji / slobodan dan**
3. Unesite detalje godišnjeg:
   - **Datum rezervacije:** Današnji datum (automatski popunjen)
   - **Datum početka:** Prvi dan godišnjeg
   - **Datum kraja:** Poslednji dan godišnjeg
4. Kliknite **Sačuvaj**

**Šta se dešava:**
- Aplikacija računa radne dane između datuma početka i kraja
- Vikendi se automatski isključuju na osnovu radnog raspoređa zaposlenog:
  - **5-dnevni radnici**: Subota i nedelja se isključuju (ne oduzimaju se)
  - **6-dnevni radnici**: Samo nedelja se isključuje (subota se oduzima ako se traži)
- Državni praznici se automatski isključuju (na osnovu vere zaposlenog)
- Dani se oduzimaju prema redosledu prioriteta
- Ako je datum početka u prošlosti, videćete upozorenje (godišnji se odmah označava kao završen)

**Primeri:**

**Primer 1: 5-dnevni radnik rezerviše ponedeljak-petak (13-17. januar 2026)**
- Ukupno kalendarskih dana: 5
- Radni dani: 5 (nema vikenda ili praznika u ovom opsegu)
- Oduzeto dana: 5 radnih dana

**Primer 2: 6-dnevni radnik rezerviše ponedeljak-subotu (13-18. januar 2026)**
- Ukupno kalendarskih dana: 6
- Radni dani: 6 (subota je radni dan za 6-dnevne radnike)
- Oduzeto dana: 6 radnih dana

**Primer 3: 5-dnevni radnik rezerviše subotu-nedelju**
- Ukupno kalendarskih dana: 2
- Radni dani: 0 (oba su vikendi za 5-dnevne radnike)
- Oduzeto dana: 0 radnih dana

**Primer 4: Ako period uključuje državni praznik (npr. 15. januar je praznik)**
- Ukupno kalendarskih dana: 5 (13-17. januar)
- Radni dani: 4 (isključujući 15. januar praznik)
- Oduzeto dana: 4 radna dana (isto za 5-dnevne i 6-dnevne radnike)

### Dodavanje zarađenih dana

Kada zaposleni zaradi dodatne dane godišnjeg:

1. Otvorite ekran detalja zaposlenog
2. Kliknite **Dodaj zarađene dane**
3. Popunite formu:
   - **Datum zarađivanja:** Datum kada su dani zarađeni
   - **Broj dana:** Koliko dana da se doda
   - **Razlog/Napomene:** Zašto su ovi dani zarađeni (npr. "Darivanje krvi", "Kompenzacija prekovremenog")
4. Kliknite **Sačuvaj**

**Česti razlozi za zarađene dane:**
- Darivanje krvi (1 dan po darivanju, obično)
- Kompenzacija prekovremenog rada (prema politici kompanije)
- Posebno priznanje ili nagrade
- Druge ugovorne obaveze

### Postavljanje prenesenih dana

Na početku svake godine, možda će trebati da postavite koliko dana zaposleni prenosi iz prethodne godine:

1. Otvorite ekran detalja zaposlenog
2. Kliknite **Postavi prenete dane**
3. Odaberite godinu (obično trenutnu godinu)
4. Unesite broj prenesenih dana
5. Kliknite **Sačuvaj**

**Važno:**
- Ovo treba uraditi rano u godini (januar)
- Preneti dani važe samo do 30. juna
- Posle juna, ovi dani se više ne računaju u kalkulaciju "Preostalo dana"

### Automatsko završavanje godišnjih odmora

Aplikacija automatski označava godišnje odmore kao "završene" kada im prođe datum kraja:

- **Pri pokretanju:** Svaki godišnji sa `datum_kraja < danas` se označava kao završen
- **Oduzimanja primenjena:** Radni dani se računaju i oduzimaju iz odgovarajućih kategorija
- **Status promenjen:** Sa "Zakazano" na "Završeno"

Ne morate ništa da radite - ovo se dešava automatski!

---

## Upravljanje praznicima

### Razumevanje radnih dana

**Dani godišnjeg se računaju na osnovu radnog raspoređa zaposlenog!**

Aplikacija automatski rukuje:
- **Vikendi:** Isključeni na osnovu radnog raspoređa
  - **5-dnevni radnici**: Subota i nedelja se nikad ne računaju
  - **6-dnevni radnici**: Samo nedelja se nikad ne računa (subota se računa kao radni dan)
- **Državni praznici:** Srpski državni i verski praznici se nikad ne računaju

### Učitavanje državnih praznika

#### Metoda 1: Automatsko preuzimanje sa sajta Ministarstva (preporučeno)

1. Sa **ekrana liste zaposlenih**, kliknite **Praznici / Podešavanja**
2. U dijalogu, odaberite godinu (npr. 2026)
3. Kliknite **Preuzmi sa sajta Ministarstva**
4. Pregledajte učitane praznike u tabeli
5. Kliknite **Sačuvaj**
6. Sačekajte preračunavanje (postojeći zapisi godišnjeg će biti ažurirani)

**Koji praznici se učitavaju:**
- Državni praznici (primenjuju se na sve)
- Pravoslavni praznici (primenjuju se na pravoslavne zaposlene)
- Katolički praznici (primenjuju se na katoličke zaposlene)

Za 2026, ovo uključuje 13 zvaničnih srpskih praznika:
- Nova godina: 1-2. januar (državni)
- Pravoslavni Božić: 7. januar (samo pravoslavni)
- Dan državnosti: 15-17. februar (državni)
- Pravoslavni Uskrs: 10-13. april (samo pravoslavni)
- Praznik rada: 1-2. maj (državni)
- Dan primirja: 11. novembar (državni)

#### Metoda 2: Ručno unošenje

Ako treba da dodate praznik koji nije u zvaničnoj listi:

1. Kliknite **Praznici / Podešavanja**
2. Odaberite godinu
3. U tabeli, možete ručno dodati redove:
   - **Datum:** Odaberite datum
   - **Naziv (srpski):** Naziv praznika na srpskom
   - **Naziv (engleski):** Naziv praznika na engleskom
   - **Tip:** Državni, Pravoslavni, Katolički, ili Ostali verski
4. Kliknite **Sačuvaj**

### Filtriranje praznika po veri

**Kako funkcioniše:**
- **Državni praznici:** Primenjuju se na SVE zaposlene (pravoslavne i katoličke)
- **Pravoslavni praznici:** Primenjuju se samo na zaposlene označene kao pravoslavni
- **Katolički praznici:** Primenjuju se samo na zaposlene označene kao katolički

**Primer:**
Pravoslavni Božić (7. januar) pada u utorak:

**Za pravoslavnog zaposlenog:**
- 7. januar je isključen iz brojanja dana godišnjeg (verski praznik)
- Ako rezerviše 6-8. januar: Samo 6. i 8. januar se računaju kao radni dani (2 dana oduzeto)

**Za katoličkog zaposlenog:**
- 7. januar je regularni radni dan
- Ako rezerviše 6-8. januar: Sva tri dana se računaju kao radni dani (3 dana oduzeto)

**Zašto je ovo važno:**
Ovo osigurava fer tretman prema srpskom zakonu o radu, koji poštuje verske praznike za svaku veru uz održavanje tačnih kalkulacija radnog raspoređa.

### Brisanje praznika

Ako treba da obrišete sve praznike za određenu godinu:

1. Kliknite **Praznici / Podešavanja**
2. Odaberite godinu
3. Kliknite **Obriši sve praznike za godinu**
4. Potvrdite akciju
5. Svi praznici za tu godinu će biti obrisani

**Upozorenje:** Ovo će preračunati sve zapise godišnjeg! Koristite oprezno.

### Godišnje održavanje

**Na početku svake nove godine:**
1. Kliknite **Praznici / Podešavanja**
2. Odaberite novu godinu (npr. 2027)
3. Kliknite **Preuzmi sa sajta Ministarstva**
4. Pregledajte i kliknite **Sačuvaj**

Ovo traje oko 30 sekundi i osigurava tačne kalkulacije za novu godinu.

---

## Poslovna pravila i kalkulacije

### Automatske kalkulacije

Aplikacija rukuje mnogim kalkulacijama automatski:

#### 1. Kalkulacija radnih dana
Kada se zakaže godišnji:
- Prebroji sve kalendarske dane između datuma početka i kraja (uključujući krajnje)
- Isključi vikende na osnovu radnog raspoređa zaposlenog:
  - **5-dnevni radnici**: Isključi subotu i nedelju
  - **6-dnevni radnici**: Isključi samo nedelju (subota je radni dan)
- Isključi državne praznike (na osnovu vere zaposlenog)
- Rezultat = stvarni radni dani za oduzimanje

#### 2. Prioritet oduzimanja dana
Dani se oduzimaju ovim redosledom:
1. Preneti dani (iz prethodne godine)
2. Dani na početku (alokacija ove godine)
3. Zarađeni dani (dodatni dani)

Ovo je vidljivo u tabeli "Iskorišćeni slobodni dani" na ekranu detalja zaposlenog.

#### 3. Isticanje prenesenih dana
Posle 30. juna:
- Preneti dani se više ne uključuju u kalkulaciju "Preostalo dana"
- I dalje se pojavljuju u tabeli balansa za referencu
- Zaposlene treba podsticati da koriste prenete dane pre juna

#### 4. Alokacija za ugovore na neređeno vreme
1. januara svake godine:
- Ugovori na neređeno vreme automatski dobijaju dane godišnjeg na osnovu radnog raspoređa:
  - **20 dana** za 5-dnevne radnike
  - **24 dana** za 6-dnevne radnike
- Ovo se radi tokom procesa prenosa godine
- Nije potrebna ručna intervencija

### Proporcionalno računanje datuma početka ugovora

Ako zaposleni počinje usred godine sa ugovorom na neređeno vreme:

**Primer:** 6-dnevni radnik počinje 1. jula 2026
- Kvota cele godine: 24 dana
- Proporcionalno za 6 meseci (jul-decembar): 12 dana
- Aplikacija automatski računa ovo na osnovu datuma početka i radnog raspoređa

**Primer:** 5-dnevni radnik počinje 1. jula 2026
- Kvota cele godine: 20 dana
- Proporcionalno za 6 meseci (jul-decembar): 10 dana

**Formula:** `(kvota_cele_godine × preostali_meseci) ÷ 12`
Gde je kvota_cele_godine 20 dana (5-dnevni radnici) ili 24 dana (6-dnevni radnici)

### Rukovanje prošlim datumima

Ako pokušate da zakažete godišnji sa datumom početka u prošlosti:
1. Videćete upozorenje: "Datum početka je u prošlosti. Da li želite da nastavite?"
2. Ako kliknete **Da**:
   - Godišnji se čuva
   - Odmah se označava kao "Završen"
   - Dani se oduzimaju od balansa zaposlenog

Ovo je korisno za unošenje istorijskih zapisa godišnjeg.

---

## Izveštaji i štampanje

### Izveštaj detalja zaposlenog

Sa ekrana detalja zaposlenog, kliknite dugme **Štampaj**:

**Šta je uključeno:**
- Informacije o zaposlenom (ime, JMBG, detalji ugovora)
- Raspored balansa trenutne godine
- Kompletna lista iskorišćenih slobodnih dana
- Kompletna lista zarađenih dana
- Sažetak ukupnih vrednosti

**Opcije izlaza:**
- Štampanje direktno na štampač
- Čuvanje kao PDF (ako imate instaliran PDF štampač)

*Napomena: Dijalog za štampanje upravlja vaš operativni sistem.*

### Pregled svih raspoređa

Kliknite **Svi raspoređi** iz liste zaposlenih:

**Slučajevi korišćenja:**
- Vidite ko je na godišnjem u određenim datumima
- Planirajte buduće raspoređe godišnjeg
- Verifikujte zapise godišnjeg svih zaposlenih
- Proverite konflikte u raspoređivanju

**Opcije filtriranja/sortiranja:**
- Trenutno prikazuje sve zapise sortirane po datumu rezervacije
- Koristite Ctrl+F (u većini pregledača) za pretragu unutar tabele

*Napomena: Napredno filtriranje može biti dodano u budućoj verziji.*

---

## Rešavanje problema

### Česti problemi i rešenja

#### 1. Datoteka baze podataka nije pronađena

**Problem:** Aplikacija ne može da pronađe `vacation.db` datoteku

**Rešenja:**
- Proverite da li datoteka postoji na očekivanoj lokaciji (OneDrive folder)
- Ako koristite OneDrive, osigurajte se da je potpuno sinhronizovan (proverite status sinhronizacije OneDrive-a)
- Koristite dijalog "Locate database" da ručno pronađete datoteku
- Ako je datoteka izgubljena, možda će trebati da je vratite iz rezervne kopije

#### 2. Netačan broj dana

**Problem:** Dani godišnjeg se ne poklapaju sa vašim očekivanjima

**Mogući uzroci:**
- Praznici nisu učitani za godinu → Prvo učitajte praznike
- Pogrešna vera postavljena za zaposlenog → Proverite podešavanje vere zaposlenog
- Pogrešan radni raspored postavljen za zaposlenog → Proverite radne dane nedeljno
- Kalkulacija vikenda ne odgovara očekivanjima → Verifikujte radni raspored zaposlenog (5-dnevni vs 6-dnevni)
- Preneti dani su istekli posle juna → Ovo je očekivano ponašanje

**Rešenje:**
- Verifikujte da su praznici učitani: Kliknite "Praznici / Podešavanja" i proverite za vašu godinu
- Verifikujte da vera zaposlenog odgovara njihovoj stvarnoj veri
- Verifikujte radni raspored zaposlenog (5-dnevni ili 6-dnevni radna nedelja)
- Zapamtite: Kalkulacija radnih dana zavisi od radnog raspoređa zaposlenog

#### 3. Aplikacija se neće pokrenuti

**Problem:** Dvoklikom na EXE ne radi ništa ili prikazuje grešku

**Rešenja:**
- Proverite da li antivirus blokira aplikaciju
- Desni klik → "Run as Administrator"
- Ako koristite Python: Proverite da su sve zavisnosti instalirane (`pip install -r requirements.txt`)
- Proverite Windows Event Viewer za detalje greške

#### 4. Promene se ne pojavljuju na drugom računaru

**Problem:** Drugi korisnik ne vidi ažuriranja koje je napravio prvi korisnik

**Rešenja:**
- Osigurajte se da oba korisnika NE pokreću aplikaciju istovremeno
- Proverite status sinhronizacije OneDrive-a na oba računara
- Zatvorite i ponovo otvorite aplikaciju da se ponovo učita baza podataka
- Dozvolite 1-2 minuta da OneDrive sinhronizuje promene

#### 5. Prikazuje se pogrešna godina

**Problem:** Balans godine prikazuje pogrešnu godinu ili nema podataka

**Rešenja:**
- Osigurajte se da je balans godine kreiran za trenutnu godinu
- Proverite da li zaposleni treba prenos godine iz prethodne godine
- Verifikujte da je tip ugovora ispravno postavljen (na neređeno vreme treba automatski da dodeli dane)

### Najbolje prakse

1. **Deljenje OneDrive-a:**
   - Samo jedan korisnik treba da pokreće aplikaciju u isto vreme
   - Sačekajte da se sinhronizacija završi pre nego što drugi korisnik otvori aplikaciju
   - Proverite ikonu statusa sinhronizacije OneDrive-a u sistemskoj traci

2. **Redovne rezervne kopije:**
   - Periodično kopirajte `vacation.db` na rezervnu lokaciju
   - OneDrive verzije mogu pomoći u oporavku od slučajnih promena

3. **Proces kraja godine:**
   - Krajem decembra, pripremite se za prenos godine
   - Podsetite zaposlene da koriste prenete dane pre juna
   - Učitajte praznike za novu godinu početkom januara

4. **Unos podataka:**
   - Unosite godišnje odmore čim se odobri
   - Držite zapise zarađenih dana ažurne sa razlozima
   - Koristite konzistentno imenovanje u poljima napomena

---

## Prečice na tastaturi

- **Dvoklikom na red:** Otvori detalje zaposlenog
- **Escape:** Zatvori dijaloge i vrati se na prethodni ekran
- **Tab:** Navigacija između polja forme
- **Enter:** Potvrdi forme (kada OK/Sačuvaj dugme ima fokus)

---

## Podrška i dodatna pomoć

### Tehnička dokumentacija

Za programere i napredne korisnike, pogledajte:
- `IMPLEMENTATION_SUMMARY.md` - Tehnički detalji implementacije
- `WORKING_DAYS_IMPLEMENTATION.md` - Logika kalkulacije radnih dana
- `RELIGION_IMPLEMENTATION.md` - Filtriranje po veri
- `DEDUCTION_ORDER_IMPLEMENTATION.md` - Prioritet oduzimanja dana

### Šema baze podataka

Aplikacija koristi SQLite sa sledećim glavnim tabelama:
- `employees` - Informacije o zaposlenima
- `employee_year_balance` - Godišnje alokacije dana godišnjeg
- `vacation_records` - Svi zakazani i završeni godišnji odmori
- `earned_days` - Dodatni zarađeni dani
- `non_working_days` - Državni praznici

Možete koristiti bilo koji SQLite pregledač da istražite bazu ako je potrebno.

---

## Informacije o verziji

**Trenutna verzija:** 2.0

**Najnovije funkcionalnosti:**
- **Fleksibilni radni raspoređi**: Podrška za 5-dnevnu (pon-pet) i 6-dnevnu radnu nedelju
- **Pametne kvote godišnjeg**: 20 dana za 5-dnevne radnike, 24 dana za 6-dnevne radnike
- **Poboljšano rukovanje vikendima**: Oduzimanje vikenda na osnovu radnog raspoređa zaposlenog
- Kalkulacija radnih dana (isključuje odgovarajuće vikende i praznike)
- Filtriranje praznika po veri (pravoslavni/katolički)
- Praćenje oduzimanja (prikazuje iz koje kategorije su dani uzeti)
- Dvojezična podrška (engleski/srpski)
- Automatsko završavanje godišnjeg
- Funkcionalnost prenosa godine
- Interfejs za upravljanje praznicima

---

## Licenca i pravni aspekti

Ova aplikacija se pruža kakva jeste za praćenje dana godišnjeg odmora u skladu sa srpskim zakonima o radu. Korisnici su odgovorni za osiguravanje usklađenosti sa važećim zakonima i propisima.

**Privatnost podataka:**
- Svi podaci se čuvaju lokalno u vašoj `vacation.db` datoteci
- Nikakvi podaci se ne šalju na spoljne servere
- Vi kontrolišete gde se baza podataka čuva
- Preporučuju se redovne rezervne kopije

---

## Karta brzih referenci

### Prvo podešavanje
1. Pokrenite aplikaciju → Odaberite lokaciju baze (OneDrive preporučeno)
2. Kliknite "Praznici / Podešavanja" → Odaberite godinu → "Preuzmi sa sajta Ministarstva" → Sačuvaj
3. Dodajte zaposlene preko dugmeta "Dodaj zaposlenog"
4. **Važno**: Postavite radne dane nedeljno (5 ili 6 dana) za svakog zaposlenog

### Dnevna upotreba
1. **Zakaži godišnji:** Dvoklikom na zaposlenog → "Zakaži godišnji" → Unesite datume → Sačuvaj
2. **Proveri preostale dane:** Pogledajte kolonu "Preostalo dana" u listi zaposlenih
3. **Dodaj zarađene dane:** Dvoklikom na zaposlenog → "Dodaj zarađene dane" → Unesite info → Sačuvaj

### Kraj godine
1. Učitajte praznike za novu godinu (januar)
2. Postavite prenete dane za zaposlene (početak januara)
3. Verifikujte da su svi godišnji odmori prethodne godine označeni kao završeni

### Česti zadaci
- **Promeni ugovor:** Detalji zaposlenog → "Datum / Tip ugovora"
- **Promeni radni raspored:** Detalji zaposlenog → "Datum / Tip ugovora" → Radni dani nedeljno
- **Pogledaj sve godišnje:** Dugme "Svi raspoređi"
- **Štampaj izveštaj:** Detalji zaposlenog → Dugme "Štampaj"
- **Promeni jezik:** Padajući meni u gornjem desnom uglu

---

*Kraj korisničkog priručnika*