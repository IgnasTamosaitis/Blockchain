# Hash generatorius (v0.1 (savadarbis))

## Reikalavimai

Sukurta maišos funkcija **Pulse256** atitinka šiuos reikalavimus:

1. **Įėjimas (Input)**  
   - Maišos funkcijos įėjimas gali būti bet kokio dydžio simbolių eilutė (angl. string).

2. **Išėjimas (Output)**  
   - Maišos funkcijos išėjimas visuomet yra **fiksuoto dydžio** rezultatas.  
   - Pageidautina: **256 bitų**, t. y. **64 simbolių hex** eilutė.

3. **Deterministiškumas**  
   - Maišos funkcija yra deterministinė.  
   - Tam pačiam įvedimui (input) išvedimas (output) visuomet yra tas pats.

4. **Efektyvumas**  
   - Maišos reikšmė bet kokiai input reikšmei apskaičiuojama greitai ir efektyviai.

5. **Vienkryptiškumas (One-way)**  
   - Iš hash rezultato praktiškai neįmanoma atgaminti pradinio įvedimo (input).

6. **Atsparumas kolizijoms**  
   - Maišos funkcija yra atspari kolizijoms – labai mažai tikėtina, kad skirtingos įvestys duotų tą patį hash.

7. **Lavinos efektas (Avalanche effect)**  
   - Bent minimaliai pakeitus įvedimą (pvz., vietoj `"Lietuva"` pateikus `"lietuva"`), hash rezultatas keičiasi **iš esmės**.


## 1. Idėja (pseudo-kodas)

```text
Funkcija Pulse256(duomenys):
    1. Pridėti padding:
       - Prie pranešimo pridėti 0x80
       - Užpildyti nuliais iki 32*n - 8 baitų
       - Gale pridėti pranešimo ilgį (8 baitai)

    2. Inicializuoti pradinę būseną (v[0..3]):
       - Paimti konstantą C
       - Apskaičiuoti s1, s2, s3
       - Užkrauti v su pranešimo ilgiu ir baitų suma

    3. Padalinti pranešimą į 32 baitų blokus.
       Kiekviename bloke:
          - Paversti į 4 * 64 bitų skaičius
          - Vykdyti 8 maišymo round'us:
             * Pridėti konstantas
             * Rotuoti ir XOR’inti
             * Dauginti iš konstantų
             * Sumaišyti poras rotacijomis

    4. Baigus blokus:
       - Atlikti dar 12 papildomų maišymo round’ų su „fake_m“

    5. Sukombinuoti galutinę būseną:
       - out = [v0 ^ v2, v1 ^ v3, v0 ^ v1, v2 ^ v3]
       - Konvertuoti į 256 bitų hex eilutę

    Grąžinti: 64 simbolių hex eilutę

## Testavimas

### Maišos funkcijos deterministinumas
Maišos funkcija yra deterministinė. Tai reiškia, kad sumaišius tą patį simbolį ar įvestį, rezultatas visada bus identiškas.  
Visi testai buvo atlikti **mažiausiai 5 kartus**, kad įsitikinti, jog rezultatas nesikeičia.

**Pavyzdžiai:**

| Įvestis | Pulse256 hash |
|---------|---------------|
| `a` | `hash'as` |
| `Lietuva` | `hash'as` |
| `lietuva` | `hash'as` |
| `lietuva!` | `hash'as` |
| `Lietuva!` | `hash'as` |

---

### Maišos funkcijos efektyvumas
Maišos funkcijos efektyvumas buvo patikrintas įvairių ilgių įvestims.  
(Galima pridėti screenshot’ą: ``)

---

### Kolizijos patikra
Sugeneruota **100 000 eilučių porų**, skirtų kolizijų patikrai:

- 25 000 porų, ilgis 10 simbolių  
- 25 000 porų, ilgis 100 simbolių  
- 25 000 porų, ilgis 500 simbolių  
- 25 000 porų, ilgis 1000 simbolių  

Rezultatas: **nei vienoje poroje maišos nesutapo**, kolizijų nerasta.

**Rezultatų lentelė (vieno simbolio pakeitimas – hash skirtumai):**

| Ilgis (simboliais) | Time taken to read data |
|------------------|-----------------------|
| 10 | 0 |
| 100 | 0 |
| 500 | 0 |
| 1000 | 0 |

**Hash’ų procentinis „skirtingumas“ vieno simbolio pakeitimo atveju:**

| Metric | Value |
|--------|-------|
| Number of pairs | 50,000 |
| Min Hex Difference | % |
| Max Hex Difference | % |
| Avg Hex Difference | % |
| Min Bit Difference | % |
| Max Bit Difference | % |
| Avg Bit Difference | % |

---

**Išvada:**  
- Hash funkcija yra deterministinė.  
- Nedidelis įvesties pakeitimas lemia reikšmingą hash pokytį (lavinos efektas).  
- Kolizijų testuose nerasta net tarp 100 000 eilučių porų, todėl funkcijos pasiskirstymas yra geras ir efektyvus.
