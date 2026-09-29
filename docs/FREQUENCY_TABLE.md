# Amatör Frekans Tablosu — Atomik Veri Sözleşmesi

Kanonik semantik kayıt: `data/frequency_table.json`  
Ham resmî transkripsiyon: `data/btk_amateur_table_raw.json`  
Emisyon referansı: `data/btk_emission_types.json`  
Kaynak: `TR.BTK.FTM.TECH.2022-IK-SYD-245`, MADDE 22.

## Durum

`coverage_status = partial`

Artık resmî BTK PDF içeriği doğrulanmış bir web-render yolu üzerinden okunmuş ve amatör frekans tablosundaki **33 görünür kaynak satırı** ham katmana aktarılmıştır. Ancak ham PDF byte'ları kod yürütme ortamına indirilemediği için artifact SHA-256 üretilememiştir. Ayrıca kaynak içindeki numaralandırma/emisyon/birim tutarsızlıkları açıktır.

Bu nedenle:

- **raw transcription:** 33/33 satır, programatik olarak doğrulanır;
- **emission reference:** 24 Tablo 26-1 tanımı;
- **semantic decision table:** hâlâ partial;
- **complete legal verdict:** kapalı.

## İki katmanlı model

### 1. Raw source transcription

`data/btk_amateur_table_raw.json` kaynak tablodaki görünür satırları korur:

- frekans min/max ve birim;
- kaynakta görülen güç ifadesi;
- emisyon kodları;
- belge sınıfları;
- kullanım kısıtlamalarının kaynak-anlamını koruyan kısa transkripsiyonu;
- PDF sayfa locator'ı;
- merged-cell inheritance notu;
- açık kaynak çatışmaları.

Bu katman karar vermek için tek başına kullanılmaz.

### 2. Semantic decision table

`data/frequency_table.json` AI karar motorunun fail-closed katmanıdır. Şimdilik yalnız atomik kurallarla doğrulanmış güç sınırlarını taşır: A sınıfı üç e.i.r.p. sınırı, ham tablonun görünür alt bantlarına bölünmüş C sınıfı 5 W sınırları ve A/B sınıfı 50–52 MHz genel 100 W sınırı. Her güç değeri bir `power_basis` taşır:

| Satır | Sınıf | Aralık | Doğrulanmış limit | Güç esası | Ham satır |
|---|---|---|---|---|---|
| `TR.FTM.AMATEUR.ROW.A.135.7-137.8-KHZ` | A | 135,7–137,8 kHz | 1 W | e.i.r.p. | 1 |
| `TR.FTM.AMATEUR.ROW.A.472-479-KHZ` | A | 472–479 kHz | 5 W | e.i.r.p. | 2 |
| `TR.FTM.AMATEUR.ROW.A.5351.5-5366.5-KHZ` | A | 5351,5–5366,5 kHz | 15 W | e.i.r.p. | 7 |
| `TR.FTM.AMATEUR.ROW.C.144-146` | C | 144–146 MHz | 5 W | verici çıkışı | 18 |
| `TR.FTM.AMATEUR.ROW.C.430.2-430.7` | C | 430,2–430,7 MHz | 5 W | verici çıkışı | 19 |
| `TR.FTM.AMATEUR.ROW.C.431.55-431.825` | C | 431,55–431,825 MHz (dernek tekrarlayıcı alt bandı) | 5 W | verici çıkışı | 20 |
| `TR.FTM.AMATEUR.ROW.C.432-432.975` | C | 432–432,975 MHz | 5 W | verici çıkışı | 21 |
| `TR.FTM.AMATEUR.ROW.C.433.4-433.575` | C | 433,4–433,575 MHz | 5 W | verici çıkışı | 22 |
| `TR.FTM.AMATEUR.ROW.C.435-437.975` | C | 435–437,975 MHz | 5 W | verici çıkışı | 23 |
| `TR.FTM.AMATEUR.ROW.C.439.15-439.425` | C | 439,15–439,425 MHz (dernek tekrarlayıcı alt bandı) | 5 W | verici çıkışı | 24 |
| `TR.FTM.AMATEUR.ROW.AB.50-52` | A, B | 50–52 MHz | 100 W (genel; beacon için ayrı 25 W koşulu henüz modellenmedi) | verici çıkışı | 17 |

**Güç esası (`power_basis`):** `transmitter_output` (verici/cihaz çıkış gücü) veya `eirp` (eşdeğer izotropik yayılan güç). e.i.r.p. anten kazancına ve hat kaybına bağlıdır; bu yüzden iki esas **hiçbir zaman birbirine çevrilmez**. Karar motoru istenen gücü yalnız aynı esastaki sınırla karşılaştırır (`--power-basis`, varsayılan `transmitter_output`); esas uyuşmazsa sonuç `UNKNOWN` olur. Örnek: 136 kHz'te "5 W" (verici çıkışı) → `UNKNOWN`; "5 W e.i.r.p." → `NOT_ALLOWED` (sınır 1 W e.i.r.p.).

Tablodaki "C sınıfı 430–440 MHz'te 5 W" ifadesi bir **güç sınırıdır, tahsis değildir**. Ham tabloda 430–440 MHz arası tek parça değil, yukarıdaki altı görünür alt banttır. Alt bantlar arasındaki boşluklar (ör. 433,0 MHz, 434 MHz, 438,5 MHz) için semantik satır yoktur ve karar `UNKNOWN` olur.

Validator iki kuralı zorlar:

- Kuraldan türetilen satır kuralın frekans kapsamının **içinde** kalmalıdır (alt bant olabilir, kapsamı aşamaz).
- Her semantik satır, sınıfını listeleyen **tek bir ham kaynak satırının içinde** kalmalıdır; alt bant boşluklarını kapsayan satır reddedilir.

Ham tabloda daha fazla veri bulunması, o verinin otomatik olarak `ALLOWED` kararı üretmesi anlamına gelmez.

## Kaynak çatışmaları

Aşağıdaki kayıtlar açık kaldığı sürece ham veriyi sessizce normalize etme:

- `TR-BTK-NUMBERING-001`: MADDE 22 → Tablo-26 atfı, fakat görünür başlık Tablo 25.
- `TR-BTK-EMISSION-001`: 28 MHz ve üstü emisyon hücresinde `F2B` tekrarı ve Tablo 26-1'de tanımsız `J2C`.
- `TR-BTK-UNIT-001`: 28000–29700 kHz satırındaki B-sınıfı koşul cümlesinde `28000-29700 MHz` yazımı.

## Raw validator

```bash
python scripts/validate_btk_raw.py
```

Validator en az şunları kanıtlar:

- 33/33 kaynak satırı;
- 24 benzersiz emisyon tanımı;
- sıralı source-row index;
- benzersiz frekans aralıkları;
- A/B/C sınıf setlerinin geçerliliği;
- locator sayfalarının 41–45/47 aralığında olması;
- `J2C` tutarsızlığının korunması ve sessizce `J3C` yapılmaması;
- semantic promotion'ın HOLD kalması;
- artifact SHA-256'ın uydurulmaması.

## Semantik satır modeli

| Alan | Tip | `null` anlamı |
|---|---|---|
| `frequency_min`, `frequency_max`, `unit` | sayı, sayı, kHz/MHz/GHz | zorunlu |
| `license_class` | A/B/C listesi | zorunlu |
| `maximum_output_power`, `power_unit` | pozitif sayı, mW/W/kW | NOT_EXTRACTED |
| `power_basis` | `transmitter_output` / `eirp` | güç yoksa `null`; güç varsa zorunlu |
| `emission`, `station_type`, `allowed_use`, `prohibited_use`, `special_conditions`, `footnotes` | metin listesi | NOT_EXTRACTED |
| `bandwidth`, `allocation_status` | metin | NOT_EXTRACTED |
| `satellite`, `repeater`, `beacon`, `emergency` | boolean | NOT_EXTRACTED |
| `source_id`, `source_locator`, `verification_status` | — | zorunlu |

`null` hiçbir zaman "kısıtlama yok" veya "izin var" demek değildir.

## Completeness gate

`coverage_status = complete` ancak aşağıdakilerin tümü geçerse mümkündür:

1. raw PDF artifact byte-for-byte elde edilmiş;
2. `source_url`, `fetched_at`, HTTP 200, MIME type, file size ve PDF page count kaydedilmiş;
3. SHA-256 hesaplanmış ve source registry'deki `content_sha256` ile eşleşmiş;
4. 33 kaynak satırı ile semantik satır/koşul dönüşümü uzlaştırılmış;
5. açık kaynak çatışmaları semantik yorumu etkiliyorsa çözülmüş veya açıkça modellenmiş;
6. tüm required semantic dimensions çıkarılmış;
7. validator + unit tests + exact-head CI PASS.

## Karar motoru

`scripts/frequency_lookup.py -> evaluate()` yalnız doğrulanmış semantik satırlardan karar verir.

- satır bulunmaması = `UNKNOWN`;
- partial tablo = blanket `ALLOWED` yok;
- IARU/TRAC = Türkiye için hukuki izin oluşturmaz;
- doğrulanmış güç sınırının **aynı güç esasında** açık aşımı = `NOT_ALLOWED`;
- farklı güç esası (ör. e.i.r.p. sınırına karşı verici çıkış gücü) = karşılaştırma yok, `UNKNOWN`;
- diğer eksik/çelişkili durumlar = `UNKNOWN`.

## NEXT

1. Resmî PDF'nin raw byte artifact'ını al.
2. SHA-256 + file size kaydet.
3. Raw 33 satırı semantik sınıf/güç/emisyon/özel-kullanım nesnelerine dönüştür.
4. J2C/F2B ve 28000-29700 MHz uyuşmazlıklarını çözmeden pozitif izin üretme.
5. Exact-head CI + merge + main CI sonrası ancak uygun ise `coverage_status=complete`.
