# Hash generatorius (v0.1 (savadarbis))

## Reikalavimai

Sukurta maišos funkcija atitinka šiuos reikalavimus:

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

## 1. Idėja (pseudo-kodas) be AI

```
Nustatome MASK64 = 2^64 - 1

FUNKCIJA rl(x, r):
    r = r mod 64
    grąžinti (x paslinktas kairėn r bitų AND MASK64) 
             OR (x paslinktas dešinėn (64 - r) bitų)

FUNKCIJA hash_string(text):
    nustatome pradinius skaičius a, b, c, d
    paverčiame text į baitus

    KIEKVIENAM baitui ch:
        a = a XOR ch
        a = rl(a, 7)
        a = (a * 33 + (ch XOR (ch >> 2))) mod 2^64

        b = b XOR rl(ch, 11)
        b = (b * 29 + (ch XOR (ch >> 4))) mod 2^64

        c = c XOR rl(ch, 19)
        c = (c * 35 + (ch XOR (ch >> 6))) mod 2^64

        d = d XOR rl(ch, 23)
        d = (d * 39 + (ch XOR (ch >> 8))) mod 2^64

    atlikti finalinį maišymą tarp a, b, c, d
    konvertuoti a, b, c, d į hex (16 simbolių kiekvienas)
    išvesti galutinį hash (64 simbolių)

FUNKCIJA hash_file(fname):
    pabandyti atidaryti failą
    jei pavyksta – perskaityti turinį ir kviesti hash_string
    jei nepavyksta – parodyti klaidą

PAGRINDINIS MENIU (ciklas):
    parodyti pasirinkimus:
        1 – Hash’inti failą
        2 – Hash’inti string
        q – Baigti

    nuskaitomas pasirinkimas:
        jei '1' – paprašyti failo pavadinimo ir kviesti hash_file
        jei '2' – paprašyti teksto ir kviesti hash_string
        jei 'q' – nutraukti programą
        kitaip – išvesti klaidos pranešimą

```

## 2. Idėja (pseudo-kodas) su AI

```
KONST MASK64 = 2^64 - 1
KONST C = 0x9E3779B97F4A7C15
KONST MC = [K0, K1, K2, K3]            // 4 maišymo konstantos
KONST R  = [13, 17, 43, 29]            // rotacijų dydžiai v[0..3]

FUNKCIJA rotl(x, r):
    GRĄŽINTI ((x << r) ARBA (x >> (64 - r))) & MASK64

FUNKCIJA rotr(x, r):
    GRĄŽINTI ((x >> r) ARBA (x << (64 - r))) & MASK64

FUNKCIJA u64_le(baitai[8]):
    GRĄŽINTI skaičių iš 8 baitų (little-endian)

FUNKCIJA to_le8(x):
    GRĄŽINTI 8 baitus (little-endian) iš x

// --- Padding ---
FUNKCIJA pad_message(msg):
    bitlen = msg.ilgis * 8
    out = msg + 0x80
    KOL (out.ilgis + 8) % 32 != 0:
        out += 0x00
    out += bitlen kaip 8 baitai (LE)
    GRĄŽINTI out

// --- Maišymo raundai ---
FUNKCIJA mix_rounds(v[4], m[4], rounds):
    UŽ r_idx NUO 0 IKI rounds-1:
        UŽ i NUO 0 IKI 3:
            add = ( m[(i + r_idx) mod 4] + MC[i] * (r_idx + 1) ) & MASK64
            v[i] = (v[i] + add) & MASK64
            v[(i - 1) mod 4] = v[(i - 1) mod 4] XOR rotr(v[i], R[i])
            v[i] = ( v[i] * (MC[(i + 1) mod 4] ARBA 1) ) & MASK64

        // „didysis sukimasis“ per poras
        a = rotl(v[0], 32) XOR v[2]
        b = rotl(v[1], 24) XOR v[3]
        c = rotr(v[2], 17) XOR v[0]
        d = rotr(v[3], 13) XOR v[1]
        v = [a, b, c, d]

// --- Pagrindinis hash ---
FUNKCIJA (data):
    data = pad_message(data)

    // sėklos iš C
    s0 = 0x0123456789ABCDEF
    s1 = (s0 * C + 1) & MASK64
    s2 = (s1 * C + 1) & MASK64
    s3 = (s2 * C + 1) & MASK64

    sum_bytes = visų data baitų suma (32 bitų)
    v = [
        s1 XOR data.ilgis,
        s2 XOR (data.ilgis << 1),
        s3 XOR (data.ilgis << 2),
        (s1 XOR s2 XOR s3) XOR sum_bytes
    ]

    // apdorojame po 32 baitus
    UŽ off NUO 0 ŽINGSNIS 32 IKI data.ilgis-32:
        block = data[off : off+32]
        m = [ u64_le(block[0:8]),
              u64_le(block[8:16]),
              u64_le(block[16:24]),
              u64_le(block[24:32]) ]
        mix_rounds(v, m, 8)

    // finalinis „užrakinimas“ su fake_m (12 kartų)
    UŽ r_idx NUO 0 IKI 11:
        fake_m = [
            v[(r_idx + 0) mod 4] XOR (C * (r_idx + 1)),
            v[(r_idx + 1) mod 4],
            v[(r_idx + 2) mod 4],
            v[(r_idx + 3) mod 4]
        ]
        mix_rounds(v, fake_m, 1)

    // išvesties žodžiai ir HEX
    out_words = [ v[0] XOR v[2],  v[1] XOR v[3],
                  v[0] XOR v[1],  v[2] XOR v[3] ]
    out_bytes = sujungti to_le8(x) kiekvienam x iš out_words
    GRĄŽINTI out_bytes kaip hex eilutę (64 simboliai)

// --- Vartotojo sąsaja ---
FUNKCIJA main(argv):
    SPAUSDINTI "1) Ivesti teksta ranka"
    SPAUSDINTI "2) Nuskaityti is failo"
    choice = įvestis

    JEI choice == "1":
        s = įvestas tekstas
        SPAUSDINTI "Hash:",( UTF-8(s) )
    KITAIP JEI choice == "2":
        filename = įvestas kelias
        BANDYTI:
            data = perskaityti failą kaip baitus
            SPAUSDINTI "Hash:", (data)
        JEI failas nerastas:
            SPAUSDINTI klaidą
    KITAIP:
        SPAUSDINTI netinkamą pasirinkimą

```


## Testavimas

### Išvedimo dydis

Patikrinome sugeneruotų hash reikšmių ilgį.
Nepriklausomai nuo įvesties dydžio ar turinio, rezultatas visada yra tokio paties ilgio – 256 bitai (64 šešioliktainiai simboliai).

Tai reiškia, kad tiek trumpas tekstas („b“), tiek ilgas failas sugeneruos vienodo ilgio hash eilutę, kas yra svarbi hash funkcijų savybė.

##### Pavyzdžiai:

|`b raide Hash`|`eb5cb7666affa01a358ed3e5c19c9bd6f7b1f85fece16b83bca79fa9eb345116`|
|`Labas pasauli Hash`|`ef21208d8e89951116062f8eb8b3aa5f3f12532000228af305154d44c1480954`|

---

### Deterministiškumas
Maišos funkcija yra deterministinė. Tai reiškia, kad sumaišius tą patį simbolį ar įvestį, rezultatas visada bus identiškas.  
Visi testai buvo atlikti **mažiausiai 5 kartus**, kad įsitikinti, jog rezultatas nesikeičia.

**Pavyzdžiai:**

| Įvestis | hash |
|---------|---------------|
| `a` | `eb5cb7661eb8f198358edb55871453e0ef41f85fc0e2bd0cf2ca3e5adb2c0921` |
| `Lietuva` | `b00670949db6f3943db888e55ab78a05d2d593620ab1e733fc14316b925ab8fc` |
| `lietuva` | `090c32eef6e281e80bf8c6104b1e500a47a9bbffde22f98cae77617155bcf9b4` |
| `lietuva!` | `17085f6353d990e6173f47b84f42987853d040179b1c9ffbcfc6037cf20976f5` |
| `Lietuva!` | `e7ba2c2b0d7500d06209c55bebd848ef066339a279eb0927872f282b1a16a9e8` |

---

### Efektyvumas

Norėdami įvertinti sukurto hash algoritmo našumą, atlikome eksperimentą su failu, kuriame yra 789 eilutės. Buvo matuojamas vidutinis hashavimo laikas, kai įvesties duomenų kiekis didinamas.

Rezultatai rodo, kad laikas auga proporcingai įvesties dydžiui – mažiems duomenų kiekiams algoritmas veikia beveik akimirksniu, o didesnėms įvestims laikas išauga, tačiau išlieka pakankamai efektyvus.

| Eilutės | Vidutinis laikas |
|--------|-------------------|
|1       |0.00010566 s       |
|2       |0.00016380 s      |
|4       |0.00030824 s      |
|8       |0.00054956 s      |
|16       |0.00105876 s      |
|32       |0.00246976 s      |
|64      |0.00523430 s      |
|128       |0.00882652 s      |
|256       |0.02026248 s      |
|512       |0.04499916 s      |

Žemiau pateiktas grafikas vizualiai parodo hashavimo laiko priklausomybę nuo eilučių skaičiaus

![image](https://raw.githubusercontent.com/IgnasTamosaitis/Blockchain/refs/heads/v0.1/img/foto_konst.png)

### Lavinos efektas

**Hash’ų procentinis „skirtingumas“ vieno simbolio pakeitimo atveju:**

Hash funkcijose svarbu, kad net pakeitus tik vieną simbolį įvestyje, gautas rezultatas skirtųsi.

Testavimui sugeneruota 100 000 eilučių porų, kurios skiriasi tik vienu simboliu (eilutės ilgis 64). Buvo palyginti gauti hash’ai:

| Rezultatai: |
| Bitų lygyje (iš 256 bitų): |
| Min: 61 bit (23.83 %) |
| Max: 162 bit (63.28 %) |
| Vidurkis: 127.44 bit (49.78 %) |
| Hex lygyje (iš 64 simbolių): |
| Min: 32 hex (50.00 %) |
| Max: 64 hex (100.00 %) |
| Vidurkis: 59.75 hex (93.36 %) |

** Išvada: **
* Rezultatai rodo, kad algoritmas pasižymi geru lavinos efektu – vidutiniškai apie pusė bitų skiriasi net ir pakeitus tik vieną įvesties simbolį. *

---

**Išvada:**  
- Hash funkcija yra deterministinė.  
- Nedidelis įvesties pakeitimas lemia reikšmingą hash pokytį (lavinos efektas).  
- Kolizijų testuose nerasta net tarp 100 000 eilučių porų, todėl funkcijos pasiskirstymas yra geras ir efektyvus.
