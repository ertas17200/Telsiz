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
- `ACADEMY.TOOL.MORSE-TRAINER`
- `ACADEMY.TOOL.QCODE-RST-TRAINER`
- `ACADEMY.TOOL.QSO-LOG-ADIF`
- `ACADEMY.TOOL.RF-WAVELENGTH`
- `ACADEMY.DEVICE.YAESU.FTM400`

Grounded pratik sınav katmanı için [EXAM.md](EXAM.md) ve `exam_questions.json` kullanılır. Bu banka yalnız verified source/rule zincirleri alınır ve banka `practice_only` kalır.

İlk deterministic operator tool: [GRID_LOCATOR.md](GRID_LOCATOR.md) / `scripts/grid_locator.py`. Bu araç `ACADEMY.TOOL.GRID-LOCATOR` modülüne bağlıdır ve hukuki verdict üretmez.

Kaynak-grounded Mors eğiticisi: [MORSE_TRAINER.md](MORSE_TRAINER.md) / `scripts/morse_trainer.py`; veri kaynağı `ITU.R.M1677.1`.

Kaynak-grounded Q-code/RS(T) eğiticisi: [QCODE_RST_TRAINER.md](QCODE_RST_TRAINER.md) / `scripts/qcode_rst_trainer.py`; Q-code için IARU EOP 4.2.0 + ITU-R M.1172, RS(T) için IARU EOP 4.2.0 + VHF Handbook 10.02 kullanılır.

Kaynak-grounded QSO log/ADIF exporter: [QSO_LOG_ADIF.md](QSO_LOG_ADIF.md) / `scripts/qso_log_adif.py`; bounded uygulama sözleşmesi `ADIF.SPEC.3.1.7` kaynağına bağlıdır.

Kaynak-grounded RF wavelength/electrical-length calculator: [RF_WAVELENGTH.md](RF_WAVELENGTH.md) / `scripts/rf_wavelength.py`; exact SI `c` değeri `BIPM.SI.DEFINING_CONSTANTS` kaynağından gelir ve fiziksel anten kesim boyu garantisi vermez.

Yaesu FTM-400 cihaz/manual katmanı: [DEVICE_FTM400.md](DEVICE_FTM400.md) / `scripts/device_firmware_guard.py`; DR/DE ile XDR/XDE firmware aileleri fail-closed ayrılır ve package-specific upgrade manual doğrulanmadan update prosedürü verilmez.

## Doğrulama

```bash
python scripts/validate_academy.py
python scripts/validate_exam.py
python scripts/validate_morse.py
python scripts/validate_operator_codes.py
python scripts/validate_qso_log.py
python scripts/validate_rf_calculator.py
python scripts/validate_device_manuals.py
python -m unittest discover -s tests -p "test_*.py" -v
```

CI aynı sözleşmeyi GitHub Actions üzerinde doğrular.
