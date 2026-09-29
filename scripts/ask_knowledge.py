"""Technical / operating knowledge routes for ``ask.py``.

Each route answers from an existing, source-grounded Academy tool
(Q-codes, RS(T), Morse, RF wavelength, repeater snapshot, Maidenhead
locator). None of them produces a legal verdict: every answer is
technical or operating information with the tool's own source IDs.

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
REPEATER_KEY_RE = re.compile(r"(?<![a-z0-9])(role\w*|tekrarlayici\w*|repeater\w*)")


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
        grid_route(text, question),
    ]
    return [r for r in routes if r]
