# Amatör Frekans Tablosu — Atomik Veri Sözleşmesi

Kanonik kayıt: `data/frequency_table.json`
Kaynak: `TR.BTK.FTM.TECH.2022-IK-SYD-245`, MADDE 22 tablosu (PDF başlığı Tablo 25; madde içi atıf Tablo-26 — bkz. `SOURCE_CONFLICTS.md` TR-BTK-NUMBERING-001).

## Durum

`coverage_status = partial` — **BLOCKED_BY_OFFICIAL_SOURCE_ACCESS** (bkz. `docs/SOURCE_ACCESS_LOG.md`).
Tablonun tamamı çıkarılmadı. Yalnız doğrulanmış kurallardan türetilen iki satır vardır:

| Satır | Sınıf | Aralık | Maks. çıkış gücü | Diğer alanlar |
|---|---|---|---|---|
| `TR.FTM.AMATEUR.ROW.C.144-146` | C | 144–146 MHz | 5 W | NOT_EXTRACTED |
| `TR.FTM.AMATEUR.ROW.C.430-440` | C | 430–440 MHz | 5 W | NOT_EXTRACTED |

## Satır modeli

| Alan | Tip | `null` anlamı |
|---|---|---|
| `frequency_min`, `frequency_max`, `unit` | sayı, sayı, kHz/MHz/GHz | zorunlu |
| `license_class` | A/B/C listesi | zorunlu |
| `maximum_output_power`, `power_unit` | pozitif sayı, mW/W/kW | NOT_EXTRACTED |
| `emission`, `station_type`, `allowed_use`, `prohibited_use`, `special_conditions`, `footnotes` | metin listesi | NOT_EXTRACTED |
| `bandwidth`, `allocation_status` | metin | NOT_EXTRACTED |
| `satellite`, `repeater`, `beacon`, `emergency` | boolean | NOT_EXTRACTED |
| `source_id`, `source_locator`, `verification_status` | — | zorunlu |

`null` hiçbir zaman "kısıtlama yok" demek değildir. `[]` yalnız kaynak satırında ilgili hükmün bulunmadığı doğrulandıktan sonra yazılabilir.

## Validator kuralları

- `verified` satır yalnız `verified` + `official_legal` + `current` kaynağa dayanır (IARU/TRAC/pending kaynak reddedilir).
- `derived_from_rule` taşıyan satır kural parametreleriyle çelişemez.
- Aynı sınıf için çakışan aralıkta, ayırt edici koşul olmadan farklı güç taşıyan satırlar reddedilir.
- Geçersiz aralık (min ≥ max, ≤ 0) ve pozitif olmayan güç reddedilir.
- `partial` kapsam bir `coverage_blocker` gerektirir.

## Completeness gate (`coverage_status = complete`)

Hepsi zorunludur; biri eksikse `partial` kalır:

1. `artifact`: `source_url`, `fetched_at`, `http_status = 200`, `content_type`, `file_size`, `sha256`, `pdf_page_count`.
2. `artifact.sha256` = kaynak kaydındaki `content_sha256`.
3. `row_count_reconciliation`: `table_start_locator`, `table_end_locator`, `source_rows_counted` (= çıkarılan satır sayısı), `footnotes_counted` = `footnotes_recorded`.
4. Her satır `verified` ve tüm kısıtlama alanları çıkarılmış (hiç `null` yok).
5. `coverage_blocker = null`.

## Karar motoru (`scripts/frequency_lookup.py` → `evaluate`)

Girdi: jurisdiction, license_class, frequency, emission, bandwidth, requested_power, station_type, context (simplex/repeater/satellite/beacon/emergency), acknowledged_conditions.

| Çıktı | Ne zaman |
|---|---|
| `ALLOWED` | Kapsam complete, eşleşen tüm satırlar ve tüm girdiler çözülmüş, koşul yok |
| `ALLOWED_WITH_CONDITIONS` | Aynı, fakat satırda özel koşul/dipnot var (`unacknowledged_conditions` listelenir) |
| `NOT_ALLOWED` | Eşleşen **her** satır isteği açıkça engelliyor (doğrulanmış güç sınırı aşımı, açıkça yasaklı kullanım; complete tabloda listelenmemiş emisyon / kapalı uydu-role-beacon bayrağı) |
| `UNKNOWN` | Diğer her durum: satır yok, girdi eksik, satır alanı çıkarılmamış, kapsam partial, jurisdiksiyon TR değil |

- Satır bulunmaması **asla** `NOT_ALLOWED` değildir.
- Yalnız frekansa bakılarak karar verilmez.
- Yalnız `verified` + `official_legal` + `current` kaynaklı satırlar karara girer.

## Tam çıkarım için gerekli adım

1. Resmî PDF'yi BTK'dan indir; `artifact` ve kaynak `content_sha256` kaydet.
2. Tablonun başlangıç/bitiş konumunu belirle; her satırı, devam satırını ve dipnotu aktar; okunamayan hücre `null`.
3. Satır ve dipnot sayımlarını `row_count_reconciliation` içinde uzlaştır.
4. Validator + test + exact-head CI → `coverage_status = complete`.
