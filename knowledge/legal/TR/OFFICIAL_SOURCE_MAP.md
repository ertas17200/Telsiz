# Türkiye Resmî Kaynak Haritası — Faz 2

**Doğrulama tarihi:** 2026-09-28  
**Politika:** OFFICIAL_SOURCE_FIRST / FAIL_CLOSED

Bu belge, amatör telsizcilik sorularında hangi resmî kaynağın hangi amaçla kullanılacağını ve hangilerinin henüz tam metin doğrulamasının beklediğini gösterir.

## VERIFIED — cevap üretiminde kullanılabilir

### TR.BTK.FTM.TECH.2022-IK-SYD-245
BTK'nın Frekans Tahsisinden Muaf Telsiz Cihaz ve Sistemlerine İlişkin Teknik Ölçütler kararıdır. Amatör istasyonların frekans, güç, emisyon ve kullanım kısıtlamaları için birincil teknik kaynaktır.

### TR.BTK.RADIO.PROCEDURES
BTK'nın Telsiz İşlemlerine İlişkin Usul ve Esaslar sayfasıdır. Özellikle amatör telsiz derneklerinin tekrarlayıcı/role ve link bağlantılı sistemlerine ilişkin başvuru, sorumlu amatör telsizci ve kurma-kullanma izni işlemlerinde kullanılır.

### TR.BTK.AMATEUR_OVERVIEW
BTK'nın güncel amatör telsizcilik açıklamasıdır. Kurumsal görev ayrımı ve bireysel amatör istasyonların genel muafiyet çerçevesi için yardımcı resmî kaynaktır.

### TR.KEGM.AMATEUR.FAQ
KEGM'nin sınav, belge, çağrı işareti ve operasyonel işlemler için güncel resmî SSS kaynağıdır.

## PENDING — kanonik hedef bulundu, exact-text doğrulaması tamamlanmadı

### TR.BTK.EHK.5809
5809 sayılı Elektronik Haberleşme Kanununun kanonik Mevzuat Bilgi Sistemi hedefi BTK'nın resmî sayfasından doğrulandı. Ancak bu oturumda hedef sayfa zaman aşımına uğradı. Tam metin yakalanmadan bu kayıt tek başına kesin madde metni üretmek için kullanılamaz.

### TR.BTK.FTM.REGULATION.2018
FTM Yönetmeliğinin adı, 27.11.2018 tarihi ve 30608 sayılı Resmî Gazete bilgisi BTK'nın güncel sayfasında doğrulandı; Mevzuat Bilgi Sistemi hedefi de resmî BTK sayfasından elde edildi. Exact-text fetch tamamlanmadığı için kayıt pending'dir.

### TR.KEGM.AMATEUR.EXAM.REGULATION
KEGM'nin güncel Yönetmelikler sayfası Amatör Telsizcilik Sınav ve Belgelendirme Yönetmeliğini MevzuatNo 13769 hedefiyle listeler. Exact-text fetch tamamlanana kadar pending'dir.

## AI karar kuralı

1. Definitif hukuk hükmü için `verified + official_legal` kayıt aranır.
2. Sadece `pending` kayıt varsa AI kesin hüküm vermemeli; kaynak doğrulamasının tamamlanması gerektiğini belirtmelidir.
3. Kurumsal açıklama (`official_technical`) kanun/yönetmelik metninin yerine geçirilmez.
4. Amatör dernek yayını veya topluluk kaynağı hiçbir koşulda daha üst düzey resmî kaynağı sessizce geçersiz kılamaz.
