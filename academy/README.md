# Telsiz Academy

Bu dizin, Telsiz bilgi tabanının kullanıcıya dönük eğitim katmanıdır. Kanonik manifest `academy/academy.json` dosyasıdır.

## Güven sözleşmesi

Academy, mevcut güven zincirinin **üstünde** çalışır; onu atlamaz:

`official/trusted source -> source registry -> grounded rule/data -> validator -> Academy presentation`

- `source_grounded` modüller yalnız kayıtlı ve doğrulanmış kaynak/rule kimliklerine bağlanabilir.
- `legal_content=true` olan bir modül yalnız `verified + current + official_legal` kaynaklara ve `verified + legal` kurallara dayanabilir.
- `educational_only` modüller kaynak veya rule iddiası taşıyamaz; yalnız genel eğitim/araç mantığı sunabilir.
- Community adayları yalnız `educational_only` fikir/provenance referansı olabilir; hukuki hüküm veya Türkiye'de yayın izni oluşturamaz.
- `legal_verdicts` her Academy modülünde zorunlu olarak `false` kalır. İzin/yasak kararı yalnız mevcut fail-closed karar motorunda verilir.

## İlk manifest modülleri

- `ACADEMY.TR.CORE-COMPLIANCE`
- `ACADEMY.TR.EXAM-OPERATIONS`
- `ACADEMY.IARU.BANDPLAN-PRACTICE`
- `ACADEMY.TOOL.GRID-LOCATOR`

## Doğrulama

```bash
python scripts/validate_academy.py
python -m unittest discover -s tests -p "test_*.py" -v
```

CI aynı sözleşmeyi GitHub Actions üzerinde doğrular.
