# Amatör Telsizcilik Bilgi Kapsamı Haritası

Bu belge, `scripts/ask.py` cevap motorunun amatör telsizciliğin hangi alanlarını **bugün** doğrulanmış kaynakla cevaplayabildiğini ve hangilerinin henüz kapsanmadığını gösterir. Kapsanmayan alanda motor tahmin etmez; "cevaplayamıyorum" der.

Durum anlamları: **VAR** = doğrulanmış kaynakla cevaplanıyor · **KISMİ** = bir kısmı cevaplanıyor, eksikler açıkça söyleniyor · **YOK** = henüz kaynak/veri yok.

## Mevzuat ve izin

| Alan | Durum | Bugün cevaplanan | Eksik / gerekli |
|---|---|---|---|
| Frekans ve güç sınırları | KISMİ | C sınıfı 144–146 ve 430–440 MHz alt bantları (5 W), A/B 50–52 MHz (100 W), A sınıfı 136 kHz / 472 kHz / 5 MHz (e.i.r.p.); 33 tablo satırının kapsam bilgisi | Çoklu güç (ör. "75 W, 400 W (PEP)") ve koşul modeli; 22 ham satır |
| Madde 22 işletme hükümleri | VAR | Teknik uygunluk, dummy load, A sınıfı kullanım, B/C gözetim, belgesiz eğitim, röle/deneysel, şifreleme yasağı | Madde 22'nin diğer fıkraları |
| Röle / tekrarlayıcı izni | KISMİ | Madde 22 f.12 + BTK usul kaynağına yönlendirme | Atomik izin süreci kuralları (P7) |
| Belge sınıfları, sınav, çağrı işareti, yenileme | KISMİ | KEGM SSS'ye yönlendirme; hüküm verilmez | KEGM Yönetmeliği tam metin doğrulaması (P3–P6) |
| 5809 sayılı Kanun, FTM Yönetmeliği | YOK | — | Resmî konsolide metin (P1–P2) |
| Yabancı amatörler / CEPT lisansı | YOK | — | CEPT T/R 61-01 + Türkiye uygulama durumu (aday kaynak) |

## İşletme ve teknik bilgi

| Alan | Durum | Bugün cevaplanan | Eksik / gerekli |
|---|---|---|---|
| Q kodları | VAR | 20 Q kodu (IARU işletme kaynağı) | Daha geniş Q kodu seti |
| RS(T) raporları | VAR | Ses (RS) ve CW (RST) raporlarının anlamı | — |
| Mors | VAR | Metin → Mors, Mors → metin (ITU-R M.1677-1) | — |
| Dalga boyu / anten elektriksel uzunluğu | VAR | λ, λ/2, λ/4, hız faktörü (BIPM sabitleri) | Fiziksel anten kesim boyu (varsayımlar açıkça yazılır) |
| Maidenhead locator | VAR | Locator ↔ koordinat (eğitim aracı) | — |
| Röle listesi | KISMİ | TRAC anlık görüntüsündeki şubeler (dernek bilgisi, izin kanıtı değil) | Diğer şehirler; güncel liste |
| QSO kaydı / ADIF | VAR | Sözleşme özeti; soruda verilen ADI kaydının ayrıştırılıp Telsiz QSO sözleşmesine göre denetlenmesi (`ADIF.SPEC.3.1.7`) | BAND/MODE değer listeleri (enumeration) denetimi |
| Cihaz bilgisi | KISMİ | Yaesu FTM-400 yazılım uyumluluğu (`device_firmware_guard.py`) | Diğer cihazlar |
| IARU band planı | KISMİ | "Ulusal kural esastır" ilkesi | Sürümlü HF/VHF band planı içeriği (aday kaynak) |
| Propagasyon | YOK | — | Güvenilir eğitim kaynağı |
| Dijital modlar (FT8, FT4) | KISMİ | FT8/FT4 modülasyon, sembol, zamanlama ve kodlama parametreleri — **topluluk katmanı** (`OSS.KGOBA.FT8_LIB`, commit-pinned) | Protokol yazarlarının belgesiyle doğrulama (`CAND.QEX.FT4_FT8_PROTOCOLS`, `CAND.WSJTX.REFERENCE_SOURCE`); bant genişliği ve çalışma frekansları kaynakta yok |
| APRS | KISMİ | Cihaz/yazılım kimliği: 417 tocall + 32 Mic-E kaydı (`APRS.DEVICEID.TOCALLS`, commit-pinned, CC BY-SA 2.0) | APRS protokol belgesi (`CAND.APRS.PROTOCOL_1_0_1`), Mic-E konum kodlaması, frekanslar |
| AX.25 / paket radyo | KISMİ | HDLC bayrağı, bit doldurma, bit sırası, FCS (CRC-16) ve 1200 baud AFSK tonları — **topluluk katmanı** (`OSS.WB2OSZ.DIREWOLF`, commit-pinned) | AX.25 2.2 standardıyla doğrulama (`CAND.TAPR.AX25_2_2`); 9600 baud ve diğer modemler |
| Dijital ses (DMR, D-STAR, System Fusion) | KISMİ | Çerçeve uzunlukları, ses/senkron bölümlemesi, DMR senkron desenleri, D-STAR/YSF senkron baytları — **topluluk katmanı** (`OSS.G4KLX.MMDVMHOST`, commit-pinned) | ETSI DMR / JARL D-STAR belgeleriyle doğrulama (`CAND.ETSI.TS_102_361_1`, `CAND.JARL.DSTAR_SPEC`); süreler, modülasyon, renk kodu/TG ve ağ kuralları |
| Uydu haberleşmesi | KISMİ | ISS, SO-50, AO-73, AO-91 için SatNOGS teknik snapshot; uplink/downlink/mod bilgisi; hukuki izin çıkarılmaz | Daha geniş uydu seti, güncellik otomasyonu, resmî/dernek kaynaklarıyla çapraz doğrulama |
| Acil durum haberleşmesi | KISMİ | AFAD TAMP resmî koordinasyon bağlamı; S1–S4; IARU R1 eğitim/mesaj doğruluğu ve ortak format ilkeleri; 2022/5211'in yürürlükten kalktığı ve current instrument'ın 31.12.2025/10809 olduğu metadata seviyesinde doğrulandı; afet bağlamından yayın izni/frekans yetkisi çıkarılmaz | 10809 current Yönetmeliğin origin Resmî Gazete exact-text/byte doğrulaması; güncel TAMP sürüm/provenance doğrulaması; olay/kurum bazlı güncel prosedürler |
| RF güvenliği / EMF | YOK | — | Resmî sınır değer kaynakları |
| Yarışmalar ve diplomalar | KISMİ | TRAC VHF/UHF yarışma kaynağı kayıtlı | ask.py entegrasyonu |

## Genişletme kuralı

Yeni bir alan yalnız şu sırayla eklenir: kaynak kaydı (`data/sources.json`, doğrulanmış) → atomik kural veya veri dosyası → validator + test → `ask.py` rotası/niyeti. Kaynaksız genel bilgi eklenmez.
