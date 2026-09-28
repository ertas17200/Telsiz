# Amatör Frekans Tablosu — Atomik Veri Sözleşmesi

Kanonik kayıt: `data/frequency_table.json`
Kaynak: `TR.BTK.FTM.TECH.2022-IK-SYD-245`, MADDE 22 tablosu (PDF başlığı Tablo 25; madde içi atıf Tablo-26 — bkz. `SOURCE_CONFLICTS.md` TR-BTK-NUMBERING-001).

## Durum

`coverage_status = partial` — **BLOCKED_BY_MISSING_ARTIFACT**.
Tablonun tamamı henüz çıkarılmadı. Şu an yalnız doğrulanmış kurallardan türetilen iki satır vardır:

| Satır | Sınıf | Aralık | Maks. çıkış gücü | Diğer alanlar |
|---|---|---|---|---|
| `TR.FTM.AMATEUR.ROW.C.144-146` | C | 144–146 MHz | 5 W | NOT_EXTRACTED |
| `TR.FTM.AMATEUR.ROW.C.430-440` | C | 430–440 MHz | 5 W | NOT_EXTRACTED |

## Fail-closed kurallar (validator + test ile zorlanır)

- `null` alan = NOT_EXTRACTED; "kısıtlama yok" anlamına gelmez.
- `partial` kapsam bir `coverage_blocker` gerektirir.
- `complete` kapsam; blocker olmamasını, kaynağın `verified` olmasını ve kaynakta `content_sha256` bulunmasını gerektirir.
- `verified` satır yalnız `verified` + `official_legal` + `current` kaynağa dayanabilir.
- `derived_from_rule` taşıyan satır, ilgili kuralın parametreleriyle çelişemez.

## Lookup davranışı (`scripts/frequency_lookup.py`)

- Tabloda satır bulunması `legal_to_transmit = true` anlamına gelmez.
- `legal_to_transmit = true` yalnız kapsam `complete` **ve** eşleşen satırın tüm kısıtlama alanları çıkarılmışsa döner.
- Kapsam `partial` iken eşleşme yoksa sonuç `UNKNOWN_NOT_EXTRACTED` olur; "yasak" denmez.
- Bir sınıfın satırı başka sınıfa genellenmez (örn. C satırı B için kullanılmaz).

## Tam çıkarım için gerekli adım

1. Resmî PDF'yi BTK'dan byte olarak indir, `content_sha256` kaydet.
2. Her satırı ve dipnotu tek tek aktar; okunamayan hücreyi `null` bırak.
3. Tüm satırlar ve dipnotlar aktarıldıktan sonra `coverage_status = complete` yap.
