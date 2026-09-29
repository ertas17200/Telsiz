# Telsiz'e Soru Sor — Kaynaklı Cevap Motoru (`scripts/ask.py`)

`ask.py`, bilgi tabanının cevap katmanıdır (P10). Türkçe bir soruyu, `docs/AI_ANSWER_POLICY.md` formatında, her cümlesi kaynağa bağlı bir cevaba çevirir. İçinde dil modeli yoktur; cevap tamamen deterministiktir.

```bash
python scripts/ask.py "C sınıfı belgeyle 145 MHz'te 10 W kullanabilir miyim?"
python scripts/ask.py --json "Şifreli haberleşme yapabilir miyim?"   # LLM için grounding paketi
python scripts/ask.py --self-check                                     # data/answer_intents.json doğrulaması
```

Örnek:

```text
Soru: C sınıfı belgeyle 145 MHz'te 10 W kullanabilir miyim?

Kısa cevap:
- C sınıfı, 145 MHz: HAYIR — istenen 10 W (verici çıkış gücü), doğrulanmış sınırı (5 W (verici çıkış gücü)) aşıyor.

Resmî / hukuki dayanak:
- C sınıfı amatör telsizcilerin 144-146 MHz bandındaki verici çıkış gücü 5 W seviyesini geçemez.
  [TR.AMATEUR.C_144_146_MAX_5W; TR.BTK.FTM.TECH.2022-IK-SYD-245; ... document_page=43-44/47]
...
Kaynaklar:
- Frekans Tahsisinden Muaf Telsiz Cihaz ve Sistemlerine İlişkin Teknik Ölçütler — BTK (official_legal, verified; sha256 eff832fc30df…)
```

## Güvenlik sözleşmesi

| Kural | Nasıl sağlanır |
|---|---|
| Kendi hukuki cümlesini yazmaz | Hukuki cümleler yalnız doğrulanmış `legal` kuralların `claim` metnidir; frekans kararları sabit şablonlardan üretilir. |
| Yalnız doğrulanmış kaynak | Kural `verified` ve kaynağı `verified` değilse cevaba girmez (test: doğrulanmamış kural → cevap yok). |
| IARU/TRAC hukuki dayanak olamaz | `amateur_practice` kuralları yalnız "Amatör uygulama" bölümünde; "Resmî dayanak" bölümüne giremez. |
| Frekans tek başına izin değildir | Karar `frequency_lookup.evaluate()`'ten gelir; partial tabloda "izin var" cevabı üretilmez (test ızgarası). |
| Satır yoksa "yasak" denmez | Listelenmeyen frekans için "izin dayanağı yok — BİLİNMİYOR (yasak kanıtı değil)" + en yakın listelenen alt bantlar. |
| Güç esası karışmaz | e.i.r.p. sınırı yalnız e.i.r.p. isteğiyle ("5 W e.i.r.p.") karşılaştırılır. |
| Doğrulanmamış mevzuat | Konu yalnız `pending` kaynağa dayanıyorsa kesin hüküm verilmez; açıkça "henüz doğrulanmadı" denir. |
| Eşleşme yoksa | "Bu soruyu doğrulanmış kaynaklarla cevaplayamıyorum" (`fail_closed = true`); tahmin yok. |
| Kaynak çatışmaları | İlgili ham satırın açık çatışmaları (ör. `TR-BTK-EMISSION-001`) cevapta listelenir, düzeltilmez. |

## Soru anlama

- Frekans: `145 MHz`, `433,5 MHz`, `136 kHz`, `10,45 GHz` (ondalık virgül desteklenir).
- Belge sınıfı: `A/B/C sınıfı` (birden fazla sınıf ayrı ayrı değerlendirilir; sınıf yoksa A, B ve C ayrı gösterilir).
- Güç: `10 W`, `5 watt`; `e.i.r.p.`/`eirp` geçerse güç esası e.i.r.p. kabul edilir, aksi halde verici çıkış gücü.
- Konu: `data/answer_intents.json` içindeki anahtar kelimeler (Türkçe büyük/küçük harf ve aksan duyarsız, kelime başından eşleşir). Bir niyet yalnız **doğrulanmış kural veya kaynak ID'si** seçer; kendi metni yoktur. `--self-check` ve CI bunu zorlar.

## Teknik / işletme soruları

Hukuki olmayan sorular mevcut, kaynaklı Academy araçlarından cevaplanır (`scripts/ask_knowledge.py`). Bu cevaplar hiçbir zaman hukuki dayanak üretmez.

| Soru örneği | Kaynak / araç |
|---|---|
| "QTH ne demek?" | Q kodları — IARU R1 işletme kaynağı |
| "Karşı istasyon 59 rapor verdi" · "RST 599" | RS(T) ölçeği — IARU R1 |
| `Mors "CQ TEST"` · "Mors ... --- ... ne demek?" | ITU-R M.1677-1 |
| "145 MHz için çeyrek dalga anten boyu" · "7,1 MHz dipol hız faktörü 0,95" | Dalga boyu hesabı — BIPM SI sabitleri (varsayımlar yazılır) |
| "Ankara röleleri hangileri?" | TRAC röle anlık görüntüsü (dernek bilgisi; BTK izni değildir) |
| "KN41 locator nerede?" · "41.0, 29.0 grid locator" | Maidenhead eğitim aracı |
| "ADIF kaydında hangi alanlar zorunlu?" · `ADIF <CALL:6>TA1ABC…<EOR>` | ADIF 3.1.7 — Telsiz'in sınırlı QSO sözleşmesi; BAND/MODE değer listeleri denetlenmez ve bu sınır cevapta yazılır |
| "FT8 nedir?" · "FT8 ve FT4 farkı" | ft8_lib (commit-pinned) — **topluluk kaynağı**, her cevapta etiketlenir |
| "APRS APDW16 hangi cihaz?" | APRS cihaz kimliği veritabanı (aprsorg/aprs-deviceid, commit-pinned, CC BY-SA 2.0); kaynak README'nin arama kuralı: tam eşleşme → en uzun joker eşleşme, eşit eşleşmede tek cihaz seçilmez |
| `Mic-E "_3" hangi cihaz?` · `Mic-E ">="` | Aynı veritabanının Mic-E dizinleri (yeni tip sonek / eski Kenwood önek+sonek); yalnız tam eşleşme |
| "AX.25 FCS nasıl hesaplanır?" · "paket radyo AFSK tonları" | Dire Wolf (commit-pinned, GPL-2.0; yalnız olgusal değerler) — **topluluk kaynağı**, her cevapta etiketlenir |

Hangi alanların kapsandığı: [KNOWLEDGE_COVERAGE.md](KNOWLEDGE_COVERAGE.md).

## Kapsam

Cevap kalitesi bilgi tabanının kapsamıyla sınırlıdır: frekans tablosu hâlâ `partial`, P1–P3 mevzuat metinleri `pending`. Motor bu sınırları gizlemez; her cevapta karar durumu ve eksik boyutlar açıkça yazılır.
