"""Technical / operating knowledge routes for ``ask.py``.

Each route answers from an existing, source-grounded Academy tool
(Q-codes, RS(T), Morse, RF wavelength, repeater snapshot, Maidenhead
locator, FT8/FT4 parameters, APRS device identifiers, AX.25 parameters).
None of them produces a legal verdict: every answer is technical or
operating information with the tool's own source IDs.

A route returns ``None`` when the question does not concern it, or a dict
``{"topic", "short", "lines", "source_ids"}``.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
    return sys.modules[name]


qrt = _load_module("qcode_rst_trainer")
morse = _load_module("morse_trainer")
rfw = _load_module("rf_wavelength")
rep = _load_module("repeater_lookup")
grid = _load_module("grid_locator")
vdm = _load_module("validate_digital_modes")
aprs = _load_module("aprs_deviceid")
vax = _load_module("validate_ax25")
sat = _load_module("satellite_lookup")
emc = _load_module("emergency_comms")

QCODE_RE = re.compile(r"(?<![a-z0-9])(q[a-z]{2})(?![a-z0-9])")
RST_KEY_RE = re.compile(r"(?<![a-z0-9])(rst|rs|rapor\w*|sinyal raporu)(?![a-z0-9])")
RST_DIGITS_RE = re.compile(r"(?<!\d)([1-5][1-9][1-9]?)(?![\d,.])")
MORSE_KEY_RE = re.compile(r"(?<![a-z0-9])mors\w*")
QUOTED_RE = re.compile(r"[\"“”«»]([^\"“”«»]+)[\"“”«»]")
MORSE_SIGNAL_RE = re.compile(r"(?:[.\-]+(?:\s+|\s*/\s*))*[.\-]+")
WAVE_KEY_RE = re.compile(r"dalga ?boy|anten boy|anten uzunlu|ceyrek dalga|yarim dalga|dipol|lambda")
VF_RE = re.compile(r"(?:vf|hiz faktor\w*|velocity factor)\s*[:=]?\s*(0[.,]\d+|1(?:[.,]0+)?)(?![\d])")
GRID_KEY_RE = re.compile(r"(?<![a-z0-9])(locator|lokator\w*|grid|maidenhead|qth locator)")
GRID_CODE_RE = re.compile(r"(?<![a-z0-9])([a-r]{2}\d{2}(?:[a-x]{2})?)(?![a-z0-9])")
COORD_RE = re.compile(r"(-?\d{1,2}\.\d+)\s*[,; ]\s*(-?\d{1,3}\.\d+)")
DIGITAL_MODE_RE = re.compile(r"(?<![a-z0-9])(ft8|ft4)(?![a-z0-9])")
APRS_KEY_RE = re.compile(r"(?<![a-z0-9])(aprs|tocall\w*|mic-?e)(?![a-z0-9])")
MICE_KEY_RE = re.compile(r"(?<![a-z0-9])mic-?e(?![a-z0-9])")
MICE_CODE_RE = re.compile(r"[\"“”«»`']([^\"“”«»`']{1,2})[\"“”«»`']")
AX25_KEY_RE = re.compile(r"(?<![a-z0-9])(ax\.?25|hdlc|afsk|fcs|paket radyo\w*|packet radio|bit doldurma|bit stuffing)(?![a-z0-9])")
TOCALL_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]{3,5})(?:-\d{1,2})?(?![A-Za-z0-9])")
REPEATER_KEY_RE = re.compile(r"(?<![a-z0-9])(role\w*|tekrarlayici\w*|repeater\w*)")
SATELLITE_KEY_RE = re.compile(r"(?<![a-z0-9])(uydu\w*|satellite\w*|transponder\w*|uplink\w*|downlink\w*)(?![a-z0-9])")
EMERGENCY_KEY_RE = re.compile(r"(?<![a-z0-9])(afet\w*|acil(?:\s+durum)?\w*|emergency\w*|tamp|kriz\w*|s[1-4])(?![a-z0-9])")


def _tr(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _json(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def qcode_route(text: str, question: str) -> dict | None:
    data = _json("q_codes.json")
    known = {item["code"] for item in data["codes"]}
    codes = []
    for raw in QCODE_RE.findall(text):
        code = raw.upper()
        if code in known and code not in codes:
            codes.append(code)
    if not codes:
        return None
    short = []
    for code in codes:
        item = qrt.lookup_qcode(code, data)
        short.append(
            f"{code} — soru biçimi ({code}?): {item['question_summary']} / bildirim biçimi: "
            f"{item['statement_summary']} (kaynak özeti, EN)"
        )
    return {
        "topic": "Q kodu",
        "short": short,
        "lines": [],
        "source_ids": list(data["source_ids"]),
    }


def rst_route(text: str, question: str) -> dict | None:
    if not RST_KEY_RE.search(text):
        return None
    match = RST_DIGITS_RE.search(text)
    if not match:
        return None
    report = match.group(1)
    mode = "cw" if len(report) == 3 else "phone"
    try:
        parsed = qrt.parse_rst(report, mode)
    except ValueError as exc:
        return {
            "topic": "RS(T) raporu",
            "short": [f"'{report}' geçerli bir RS(T) raporu değil: {exc}."],
            "lines": [],
            "source_ids": list(_json("rst_reports.json")["source_ids"]),
        }
    parts = [
        f"R={parsed['readability']['value']} (okunabilirlik: {parsed['readability']['summary']})",
        f"S={parsed['strength']['value']} (sinyal gücü: {parsed['strength']['summary']})",
    ]
    if parsed["tone"]:
        parts.append(f"T={parsed['tone']['value']} (ton: {parsed['tone']['summary']})")
    kind = "CW (RST, 3 hane)" if mode == "cw" else "ses (RS, 2 hane)"
    return {
        "topic": "RS(T) raporu",
        "short": [f"{report} raporu, {kind}: " + "; ".join(parts) + " (kaynak özeti, EN)."],
        "lines": [],
        "source_ids": list(parsed["source_ids"]),
    }


def morse_route(text: str, question: str) -> dict | None:
    if not MORSE_KEY_RE.search(text):
        return None
    source = _json("morse_code.json")["source_id"]
    quoted = QUOTED_RE.findall(question)
    # A signal needs a dash or at least two space/slash separated tokens, so a
    # trailing ellipsis ("...") is never decoded as a letter.
    signals = [
        m.group(0) for m in MORSE_SIGNAL_RE.finditer(question)
        if "-" in m.group(0) or len(re.split(r"[\s/]+", m.group(0).strip())) >= 2
    ]
    short, lines = [], []
    for value in quoted:
        if re.fullmatch(r"[\s.\-/]+", value):
            continue
        try:
            short.append(f"\"{value}\" Mors karşılığı: {morse.encode_text(value)}")
        except ValueError as exc:
            short.append(f"\"{value}\" Mors'a çevrilemedi: {exc}.")
    for value in quoted + signals:
        if not re.fullmatch(r"[\s.\-/]+", value):
            continue
        try:
            short.append(f"{value.strip()} çözümü: {morse.decode_morse(value)}")
        except ValueError as exc:
            short.append(f"{value.strip()} çözülemedi: {exc}.")
    if not short:
        short.append(
            "Çevrilecek metni tırnak içinde yazın (ör. Mors \"CQ TEST\") veya çözülecek sinyali nokta/çizgi ile verin "
            "(ör. ... --- ...)."
        )
    lines.append("Harf aralığı boşluk, kelime aralığı '/' ile gösterilir.")
    return {"topic": "Mors", "short": short, "lines": lines, "source_ids": [source]}


def wavelength_route(text: str, frequencies_mhz: list[float]) -> dict | None:
    if not WAVE_KEY_RE.search(text) or not frequencies_mhz:
        return None
    contract = rfw.load_contract()
    vf_match = VF_RE.search(text)
    vf = float(vf_match.group(1).replace(",", ".")) if vf_match else 1.0
    short, lines = [], []
    for freq in frequencies_mhz:
        calc = rfw.calculate(freq, "MHz", vf, contract)
        label = f"{freq:g}".replace(".", ",")
        short.append(
            f"{label} MHz (hız faktörü {vf:g}): λ = {_tr(calc['propagation_wavelength_m'])} m, "
            f"λ/2 = {_tr(calc['half_wave_m'])} m, λ/4 = {_tr(calc['quarter_wave_m'])} m (elektriksel uzunluk)."
            .replace(f"hız faktörü {vf:g}", f"hız faktörü {vf:g}".replace(".", ","))
        )
    lines.extend(f"varsayım (EN): {a}" for a in calc["assumptions"])
    if not vf_match:
        lines.append("Hız faktörü belirtilmedi; 1 (boş uzay) kullanıldı. Kablo/eleman için 'hız faktörü 0,66' gibi yazın.")
    return {"topic": "Dalga boyu / anten uzunluğu", "short": short, "lines": lines, "source_ids": [calc["source_id"]]}


def repeater_route(text: str, question: str) -> dict | None:
    if not REPEATER_KEY_RE.search(text):
        return None
    registry = rep.load_registry()
    fold = lambda s: s.replace("İ", "i").replace("I", "ı").lower().translate(str.maketrans("çğıöşü", "cgiosu"))
    branches = sorted({r["branch"] for r in registry["records"]})
    hits = [b for b in branches if fold(b.split(" - ")[0]) in text]
    if not hits:
        return None
    short, lines = [], []
    for branch in hits:
        found = rep.search_repeaters(branch=branch, registry=registry)["results"]
        found = [r for r in found if r["branch"] == branch]
        for r in found:
            short.append(
                f"{r['branch']} / {r['site']} ({r['band']}): RX {r['rx_mhz']:g} MHz, TX {r['tx_mhz']:g} MHz — "
                f"dernek durumu: {r['operational_status']}"
            )
    lines.append(f"TRAC anlık görüntüsü {registry['snapshot_id']} (gözlem: {registry['observed_at']}).")
    lines.append("Resmî izin durumu her kayıt için doğrulanmadı; dernek bilgisi BTK izni yerine geçmez.")
    return {"topic": "Röle listesi (dernek bilgisi)", "short": short, "lines": lines,
            "source_ids": [registry["operational_source_id"]]}


def digital_mode_route(text: str, question: str) -> dict | None:
    wanted = []
    for mode in DIGITAL_MODE_RE.findall(text):
        if mode.upper() not in wanted:
            wanted.append(mode.upper())
    if not wanted:
        return None
    payload = _json("digital_modes.json")
    shared = payload["shared"]
    message_bits = shared["ldpc_k"] - shared["crc_width"]
    short = []
    for mode in payload["modes"]:
        if mode["id"] not in wanted:
            continue
        d = vdm.derived(mode)
        ramp = f" + {mode['ramp_symbols']} rampa" if mode["ramp_symbols"] else ""
        short.append(
            f"{mode['id']}: {d['tones']}-FSK ({mode['bits_per_symbol']} bit/sembol); sembol süresi "
            f"{_tr(mode['symbol_period_s'])} s → ton aralığı {_tr(d['tone_spacing_hz'], 3)} Hz, sembol hızı "
            f"{_tr(d['symbol_rate_baud'], 3)} baud; {mode['total_symbols']} sembol ({mode['data_symbols']} veri + "
            f"{mode['sync_groups']}×{mode['sync_group_length']} Costas senkron{ramp}); yayın süresi "
            f"{_tr(d['transmission_s'], 2)} s, zaman dilimi {_tr(mode['slot_time_s'], 1)} s; {message_bits} bit mesaj + "
            f"{shared['crc_width']} bit CRC, LDPC({shared['ldpc_n']},{shared['ldpc_k']}) "
            "[topluluk kaynağı; resmî protokol belgesiyle doğrulama bekliyor]."
        )
    prov = payload["provenance"]
    lines = [
        "Güven seviyesi: topluluk (bağımsız açık kaynak uygulama) — " + payload["trust_note"],
        f"Kaynak commit: {prov['repository']} @ {prov['commit'][:12]} ({prov['license']}); değerler satır "
        "numaralarıyla data/digital_modes.json içinde.",
    ]
    lines.extend(f"Bu kaynağın belirtmediği: {item}" for item in payload["not_stated_by_source"])
    return {"topic": "Dijital mod parametreleri", "short": short, "lines": lines, "source_ids": [payload["source_id"]]}


def aprs_route(text: str, question: str) -> dict | None:
    if not APRS_KEY_RE.search(text):
        return None
    payload = _json("aprs_deviceid.json")
    classes = {c["class"]: c["shown"] for c in payload["classes"]}
    short = []
    if MICE_KEY_RE.search(text):
        for code in MICE_CODE_RE.findall(question):
            result = aprs.lookup_mice(code, payload)
            if result["status"] == "not_found":
                short.append(f"Mic-E \"{code}\": veritabanında eşleşen kayıt yok (tahmin edilmez).")
            for entry in result["matches"]:
                short.append(f"{aprs.describe_mice(entry, classes)} ({entry['locator']}).")
        if not short:
            short.append("Mic-E cihaz kodunu tırnak içinde yazın: yeni tip 2 karakterlik yorum soneki (ör. \"_3\") "
                         "veya eski Kenwood 1 karakterlik önek (+ isteğe bağlı sonek, ör. \">=\"). "
                         "Mic-E konum kodlamasının kendisi henüz kaynaklı olarak kapsanmıyor.")
    for token in TOCALL_TOKEN_RE.findall(question):
        if token.upper() in {"APRS", "TOCALL", "MIC-E"} or not any(ch.isdigit() for ch in token) and not token.isupper():
            continue
        result = aprs.lookup(token, payload)
        if result["status"] == "not_found":
            short.append(f"{result['tocall']}: veritabanında eşleşen kayıt yok (tanımsız veya yeni tahsis; tahmin edilmez).")
        elif result["status"] == "ambiguous":
            options = "; ".join(aprs.describe(e, classes) for e in result["matches"])
            short.append(f"{result['tocall']}: birden fazla eşit eşleşme, tek cihaz seçilmez — {options}.")
        else:
            how = "tam eşleşme" if result["status"] == "exact" else "joker eşleşme"
            short.append(f"{result['tocall']}: {aprs.describe(result['matches'][0], classes)} ({how}; "
                         f"{result['matches'][0]['locator']}).")
    if not short:
        short.append("APRS konusunda bilgi tabanı şu an yalnız cihaz kimliği (tocall) sorgusunu kaynaklı cevaplar; "
                     "paketin hedef çağrı işaretini yazın, ör. \"APRS APDW16 hangi cihaz?\". "
                     "APRS protokolü ve frekansları henüz kaynaklı olarak kapsanmıyor.")
    prov = payload["provenance"]
    lines = [
        payload["trust_note"],
        "Arama kuralı (kaynak README): önce jokersiz tam eşleşme, sonra en uzun joker eşleşme "
        "(? = herhangi karakter, n = rakam, * = geri kalan); Mic-E kodları yalnız tam eşleşir.",
        f"Kaynak: {payload['license']['attribution']}",
        f"Commit: {prov['repository']} @ {prov['commit'][:12]}; uyarlama: data/aprs_deviceid.json (CC BY-SA 2.0).",
    ]
    return {"topic": "APRS cihaz kimliği (tocall / Mic-E)", "short": short, "lines": lines,
            "source_ids": [payload["source_id"]]}


def ax25_route(text: str, question: str) -> dict | None:
    if not AX25_KEY_RE.search(text):
        return None
    payload = _json("ax25_parameters.json")
    v = vax.values(payload)
    d = vax.derived(v)
    label = "[topluluk kaynağı; AX.25 2.2 / APRS belgesiyle doğrulama bekliyor]"
    short = [
        f"Çerçeve: bayrak 0x{v['hdlc_flag']:02X} ile başlar ve biter; adres alanı adres başına "
        f"{v['address_field_bytes']} bayt, {v['min_addresses']}–{v['max_addresses']} adres (hedef + kaynak + en fazla "
        f"{v['max_repeaters']} digipeater); APRS UI çerçevesinde kontrol 0x{v['ui_frame_control']:02X}, PID "
        f"0x{v['aprs_pid']:02X} {label}.",
        f"Bit düzeyi: baytlar en düşük bitten başlayarak (LSB önce) NRZI ile gönderilir; art arda "
        f"{v['bit_stuffing_run']} adet 1'den sonra bir 0 eklenir (bayrakta uygulanmaz) {label}.",
        f"FCS: CRC-16, yansıtılmış polinom 0x{v['fcs_polynomial_reflected']:04X} (CCITT x^16+x^12+x^5+1), başlangıç "
        f"0x{v['fcs_init']:04X}, son XOR 0x{v['fcs_final_xor']:04X}; önce düşük bayt gönderilir. "
        f"\"123456789\" için hesap: 0x{vax.fcs(b'123456789', v):04X} {label}.",
        f"1200 baud AFSK (Dire Wolf varsayılanı): mark {v['afsk1200_mark_hz']} Hz, space {v['afsk1200_space_hz']} Hz "
        f"(fark {d['afsk_shift_hz']} Hz), bit süresi {_tr(d['bit_time_us'], 1)} µs {label}.",
    ]
    prov = payload["provenance"]
    lines = [
        "Güven seviyesi: topluluk (bağımsız açık kaynak uygulama) — " + payload["trust_note"],
        f"Kaynak commit: {prov['repository']} @ {prov['commit'][:12]} ({prov['license']}); her değer satır "
        "numarasıyla data/ax25_parameters.json içinde.",
    ]
    lines.extend(f"Bu kaynağın belirtmediği: {item}" for item in payload["not_stated_by_source"])
    return {"topic": "AX.25 / paket radyo parametreleri", "short": short, "lines": lines,
            "source_ids": [payload["source_id"]]}




def emergency_route(text: str, question: str) -> dict | None:
    if not EMERGENCY_KEY_RE.search(text):
        return None
    registry = emc.load_registry()
    result = emc.answer_topic(question, registry)
    lines = [
        "AFAD/TAMP resmî koordinasyon bağlamı ile IARU amatör işletme/eğitim rehberi ayrı otorite katmanlarıdır.",
        "IARU rehberi hukuki izin veya Türkiye'de resmî görevlendirme kaynağı değildir.",
        registry["authority_contract"]["instruction_priority"],
    ]
    lines.extend(registry["unsupported_claims"])
    return {
        "topic": "Acil durum / afet haberleşmesi",
        "short": result["short"],
        "lines": lines,
        "source_ids": result["source_ids"],
    }


def satellite_route(text: str, question: str) -> dict | None:
    registry = sat.load_registry()
    hits = sat.find_mentions(question, registry)
    if not hits:
        return None
    if not SATELLITE_KEY_RE.search(text):
        # Exact known aliases such as ISS/SO-50/AO-73/AO-91 are strong enough
        # to route only when the question also asks a radio-specific field.
        if not re.search(r"(?<![a-z0-9])(aprs|frekans\w*|fm|ssb|lsb|usb|bpsk|afsk|telemetr\w*)(?![a-z0-9])", text):
            return None
    short = []
    lines = [
        registry["trust_note"],
        f"Snapshot: {registry['snapshot_id']} (observed {registry['observed_at']}); upstream mutable.",
        f"Lisans/atıf: {registry['license']['attribution']} — {registry['license']['name']}.",
        "Uydu verisi teknik referanstır; Türkiye'de yayın izni, frekans tahsisi veya belge yetkisi oluşturmaz.",
    ]
    for item in hits:
        aliases = ", ".join(item["aliases"])
        sat_label = f"{item['name']} ({aliases}; NORAD {item['norad_id']})" if aliases else f"{item['name']} (NORAD {item['norad_id']})"
        for tx in item["transmitters"]:
            short.append(f"{sat_label}: {sat.describe_transmitter(tx)}.")
        short.append("Uydu verisi teknik referanstır; hukuki izin sonucu UNKNOWN kalır.")
    return {
        "topic": "Uydu haberleşmesi (SatNOGS teknik snapshot)",
        "short": short,
        "lines": lines,
        "source_ids": [registry["source_id"]],
    }


def grid_route(text: str, question: str) -> dict | None:
    if not GRID_KEY_RE.search(text):
        return None
    short = []
    for code in GRID_CODE_RE.findall(text):
        try:
            b = grid.maidenhead_bounds(code)
        except ValueError:
            continue
        short.append(
            f"{b['locator']}: merkez yaklaşık {_tr(b['center_latitude'], 4)}°, {_tr(b['center_longitude'], 4)}° "
            f"(enlem {b['latitude_min']:g}…{b['latitude_max']:g}, boylam {b['longitude_min']:g}…{b['longitude_max']:g})."
        )
    for lat, lon in COORD_RE.findall(question):
        try:
            short.append(f"{lat}, {lon} → locator {grid.maidenhead_encode(float(lat), float(lon))}.")
        except ValueError as exc:
            short.append(f"{lat}, {lon} çevrilemedi: {exc}.")
    if not short:
        return None
    return {"topic": "Maidenhead locator", "short": short,
            "lines": ["Eğitim aracı (ACADEMY.TOOL.GRID-LOCATOR): deterministik Maidenhead hesabı; kaynak/izin iddiası taşımaz."],
            "source_ids": []}


def technical_routes(text: str, question: str, frequencies_mhz: list[float]) -> list[dict]:
    routes = [
        qcode_route(text, question),
        rst_route(text, question),
        morse_route(text, question),
        wavelength_route(text, frequencies_mhz),
        repeater_route(text, question),
        digital_mode_route(text, question),
        aprs_route(text, question),
        ax25_route(text, question),
        emergency_route(text, question),
        satellite_route(text, question),
        grid_route(text, question),
    ]
    return [r for r in routes if r]
