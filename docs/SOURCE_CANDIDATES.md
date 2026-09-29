# Aday Kaynaklar (doğrulanmamış)

Kanonik kayıt: `data/source_candidates.json`. Bu kayıtlar yalnız **keşif** içindir: hiçbir kural, frekans satırı veya cevap bunlara dayanamaz (validator zorlar). Bir aday doğrulandığında gerçek metadata ile `data/sources.json` içine taşınır ve bu dosyadan silinir.

Kurallar:

- `canonical_url` her zaman `null`; kanonik URL doğrulanınca kayıt `sources.json`'a terfi eder.
- Resmî olmayan adaylar `cannot_support: legal_claims` beyan etmek zorundadır.
- `unlocks` alanındaki faz, frekans alanı, çatışma ve kural referansları mevcut kayıtlara karşı doğrulanır.
- Bir aday doğrulanmadan hiçbir durum `verified` olamaz; izin verilen durumlar `candidate_unverified` ve `candidate_inaccessible`.

| ID | Beklenen tür | Faz | Ne sağlar | Gerekli erişim |
|---|---|---|---|---|
| `CAND.TR.BTK.NATIONAL_FREQUENCY_PLAN` | official_legal | P0 | Amatör tahsislerinin birincil/ikincil statüsü (alan: allocation_status) | www.btk.gov.tr |
| `CAND.TR.BTK.FTM.TECH.AMENDMENT_HISTORY` | official_legal | P0 | Madde/tablo numaralandırması ve birim yazımı uyuşmazlıklarının sürüm geçmişinden çözülmesi (çatışma: TR-BTK-NUMBERING-001, TR-BTK-UNIT-001, TR-BTK-EMISSION-001) | www.btk.gov.tr |
| `CAND.TR.RG.FTM.REGULATION.PUBLICATION` | official_legal | P2 | Yayım tarihi/sayısı ve değişikliklerin resmî provenance'ı | www.resmigazete.gov.tr, www.mevzuat.gov.tr |
| `CAND.TR.RG.KEGM.EXAM.REGULATION.PUBLICATION` | official_legal | P3, P4, P5, P6 | Yayım/yürürlük provenance'ı; belge sınıfı, çağrı işareti, sınav ve yenileme hükümlerinin doğrulanacağı metin | www.resmigazete.gov.tr, www.mevzuat.gov.tr |
| `CAND.ITU.RR` | official_legal | P1, P10 | Amatör servis tanımı, uluslararası tahsis tablosu/dipnotları, amatör servis hükümleri (şifreleme, üçüncü taraf trafiği, acil durum) (kural: TR.AMATEUR.NO_OBSCURING_ENCRYPTION) | www.itu.int |
| `CAND.CEPT.TR-61-01` | official_legal | P4, P5 | Yabancı amatörlerin Türkiye'de çalışması ve CEPT lisans eşdeğerliği | www.cept.org, docdb.cept.org, efis.cept.org |
| `CAND.CEPT.TR-61-02` | official_legal | P4, P6 | Harmonize sınav müfredatı ve belge sınıflarının CEPT karşılığı | www.cept.org, docdb.cept.org, efis.cept.org |
| `CAND.CEPT.ECC-REC-05-06` | official_legal | P4 | Başlangıç sınıfı lisansın CEPT karşılığı | www.cept.org, docdb.cept.org, efis.cept.org |
| `CAND.TR.KEGM.EXAM_GUIDE` | official_technical | P6 | Sınav konuları, başvuru ve belge işlemleri | www.kiyiemniyeti.gov.tr |
| `CAND.TR.KEGM.CALLSIGN_POLICY` | official_technical | P5 | Çağrı işareti yapısı, önekler, özel çağrı işaretleri | www.kiyiemniyeti.gov.tr |
| `CAND.TR.BTK.AMATEUR_REPEATER_LIST` | official_technical | P7 | Kurulu dernek tekrarlayıcılarının resmî listesi | www.btk.gov.tr |
| `CAND.IARU.R1.HF_BANDPLAN_DOC` | amateur_association | P8 | HF alt bant/mod tavsiyeleri (yalnız çalışma pratiği) | www.iaru-r1.org |
| `CAND.TR.RG.AFAD.MUDAHALE.REGULATION.2025-10809` | official_legal | P8 | 31.12.2025/10809 current Yönetmeliğin origin exact-text/byte doğrulaması; 2022/5211 supersession ve güncel TAMP dayanağı | www.resmigazete.gov.tr, www.mevzuat.gov.tr |
| `CAND.TR.TRAC.EXAM_STUDY` | amateur_association | P9 | Eğitim içeriği ve teknik açıklamalar | trac.org.tr |
| `CAND.COMMUNITY.ARCH-YUNUS.AMATOR-TELSIZ-REHBERI` — *erişilebilir / doğrulanmamış* | community | P11 | Eğitim/araç fikirleri ve çapraz kontrol; tek başına kural üretmez | github.com |

## Öncelik

1. `CAND.TR.BTK.FTM.TECH.AMENDMENT_HISTORY` ve `CAND.TR.BTK.NATIONAL_FREQUENCY_PLAN` — P0'ı açar (çatışmalar ve `allocation_status`).
2. `CAND.ITU.RR` — şifreleme/acil durum hükümleri için ikinci resmî kaynak (TR iç hukuk etkisi ayrıca doğrulanmalı).
3. Resmî Gazete yayım kayıtları — P2/P3 provenance.

Erişim durumu: `docs/SOURCE_ACCESS_LOG.md`.

## P11 topluluk referansı durumu

`arch-yunus/Amator-Telsiz-Rehberi` 2026-09-28 tarihinde GitHub üzerinden erişilebilir olarak yeniden doğrulandı. Depo yapısı ve lisansı incelendi; buna rağmen `community` güven seviyesinde kalır. İçeriklerinden hukuki izin, Türkiye frekans yetkisi veya doğrulanmış teknik hüküm türetilemez. Uygulanabilecek fikirler `docs/COMMUNITY_REFERENCE_REVIEW.md` içinde ayrı backlog olarak tutulur.

## Açık kaynak depo adayları (2026-09-29)

Açık GitHub depoları taranırken bulunan, bu turda doğrulanamayan veya lisans kararı bekleyen kaynaklar:

| ID | Beklenen tür | Ne sağlar | Durum |
|---|---|---|---|
| `CAND.QEX.FT4_FT8_PROTOCOLS` | technical_manual | FT8/FT4 parametrelerinin protokol yazarlarının makalesiyle doğrulanması | physics.princeton.edu erişilemedi |
| `CAND.WSJTX.REFERENCE_SOURCE` | technical_manual | Referans uygulamayla çapraz doğrulama | Resmî depo erişimi yok; aynalar kullanılmaz |
| `CAND.ETSI.TS_102_361_1` | technical_manual | ETSI DMR hava arayüzü — MMDVMHost DMR parametrelerinin doğrulanması | www.etsi.org erişimi reddedildi (403) |
| `CAND.JARL.DSTAR_SPEC` | technical_manual | JARL D-STAR belgesi — D-STAR parametrelerinin doğrulanması | www.jarl.com erişimi reddedildi (403) |
| `CAND.TAPR.AX25_2_2` | technical_manual | AX.25 2.2 standardı — Dire Wolf parametrelerinin doğrulanması | www.tapr.org erişimi reddedildi (403) |
| `CAND.APRS.PROTOCOL_1_0_1` | technical_manual | APRS 1.0.1 protokol belgesi — UI/PID ve Mic-E doğrulaması | www.aprs.org erişimi reddedildi (403) |

Kaydedilen yeni kaynaklar: `OSS.KGOBA.FT8_LIB` (community, commit-pinned) — ayrıntı `data/digital_modes.json`; `OSS.WB2OSZ.DIREWOLF` (community, commit-pinned) — ayrıntı `data/ax25_parameters.json`; `OSS.G4KLX.MMDVMHOST` (community, commit-pinned) — ayrıntı `data/digital_voice.json`.

## Promoted candidates

- `CAND.APRS.DEVICEID` → `APRS.DEVICEID.TOCALLS` on 2026-09-29 after the user accepted the CC BY-SA 2.0 licence. The adapted tocall index (`data/aprs_deviceid.json`) is commit-pinned, keeps the attribution and change notice, omits personal contact fields and cannot prove legal permission.
- `CAND.TR.TRAC.REPEATER_LIST` → `TR.TRAC.REPEATER.LIST` on 2026-09-28 after the live TRAC Röle Bilgileri page was read and registered. The promoted source remains `amateur_association` and cannot prove official permission.

- `CAND.IARU.R1.EMCOMM_GUIDE` → `IARU.R1.EMCOMM.PROCEDURES` on 2026-09-29 after the IARU Region 1 Emergency Operating Procedures page was verified. The promoted source remains `amateur_association` and cannot create Turkish legal permission or official assignment.


## AFAD legal-basis correction — 2026-09-29

- `CAND.TR.AFAD.MUDAHALE_REGULATION.2022` was retired as the wrong current-law target.
- The 2022/5211 text is now retained as historical/repealed source `TR.AFAD.MUDAHALE.REGULATION.2022-5211`.
- Current instrument metadata points to 31.12.2025/10809, RG 33124 5. Mükerrer.
- Exact Official Gazette PDF URL was resolved, but origin body/raw bytes were inaccessible in this verification environment.
- Therefore `TR.AFAD.MUDAHALE.REGULATION.2025-10809` remains `pending` and `CAND.TR.RG.AFAD.MUDAHALE.REGULATION.2025-10809` remains `candidate_inaccessible`.
- No mirror or consolidated copy is promoted to legal authority.
