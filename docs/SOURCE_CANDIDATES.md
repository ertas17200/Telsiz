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
| `CAND.IARU.R1.EMCOMM_GUIDE` | amateur_association | P8 | Acil durum işletme pratiği | www.iaru-r1.org |
| `CAND.TR.TRAC.REPEATER_LIST` | amateur_association | P9 | Türkiye'deki röle frekansları ve ton bilgileri (pratik bilgi) | trac.org.tr |
| `CAND.TR.TRAC.EXAM_STUDY` | amateur_association | P9 | Eğitim içeriği ve teknik açıklamalar | trac.org.tr |
| `CAND.COMMUNITY.ARCH-YUNUS.AMATOR-TELSIZ` — *erişilemedi* | community | P11 | Keşif ve çapraz kontrol | github.com |

## Öncelik

1. `CAND.TR.BTK.FTM.TECH.AMENDMENT_HISTORY` ve `CAND.TR.BTK.NATIONAL_FREQUENCY_PLAN` — P0'ı açar (çatışmalar ve `allocation_status`).
2. `CAND.ITU.RR` — şifreleme/acil durum hükümleri için ikinci resmî kaynak (TR iç hukuk etkisi ayrıca doğrulanmalı).
3. Resmî Gazete yayım kayıtları — P2/P3 provenance.

Erişim durumu: `docs/SOURCE_ACCESS_LOG.md`.
