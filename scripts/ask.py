#!/usr/bin/env python3
"""Deterministic, source-grounded answers to Turkish amateur-radio questions.

``ask.py`` is the answering layer of the knowledge base (P10). It never
writes legal prose of its own:

- legal statements are the verbatim ``claim`` of verified ``legal`` rules;
- frequency/power verdicts come from ``frequency_lookup.evaluate`` and are
  rendered from fixed templates;
- source-scope facts come from the evidence-only BTK scope index;
- IARU/TRAC material appears only in the amateur-practice section.

Every statement carries its rule/source id and locator. When nothing
verified matches, the answer says so (``fail_closed``) instead of guessing.

Usage:
    python scripts/ask.py "C sınıfı belgeyle 145 MHz'te kaç watt kullanabilirim?"
    python scripts/ask.py --json "Şifreli haberleşme yapabilir miyim?"
    python scripts/ask.py --self-check
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INTENTS = DATA / "answer_intents.json"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return sys.modules[name]


fl = _load_module("frequency_lookup")
fsl = _load_module("frequency_scope_lookup")
akn = _load_module("ask_knowledge")

TR_FOLD = str.maketrans("çğıöşüâîû", "cgiosuaiu")
FREQ_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(khz|mhz|ghz)(?![a-z])")
CLASS_RE = re.compile(r"(?<![a-z0-9])([abc])\s*(?:-\s*)?sinif")
POWER_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(w|watt|vat)(?![a-z])")
EIRP_RE = re.compile(r"e\.?i\.?r\.?p|eirp")
UNIT_TO_MHZ = {"khz": 0.001, "mhz": 1.0, "ghz": 1000.0}
BASIS_TR = {"transmitter_output": "verici çıkış gücü", "eirp": "e.i.r.p."}
ALL_CLASSES = ("A", "B", "C")


def normalize(text: str) -> str:
    """Turkish-aware lower-casing followed by ASCII folding."""
    text = text.replace("İ", "i").replace("I", "ı").lower()
    return text.translate(TR_FOLD)


def _number(value: str) -> float:
    return float(value.replace(",", "."))


def _fmt(value: float) -> str:
    return f"{value:g}".replace(".", ",")


def _fmt_freq(mhz: float) -> str:
    return f"{_fmt(mhz * 1000)} kHz" if mhz < 30 else f"{_fmt(mhz)} MHz"


def parse(question: str) -> dict:
    text = normalize(question)
    freqs = [_number(v) * UNIT_TO_MHZ[u] for v, u in FREQ_RE.findall(text)]
    classes = []
    for cls in CLASS_RE.findall(text):
        if cls.upper() not in classes:
            classes.append(cls.upper())
    powers = [_number(v) for v, _ in POWER_RE.findall(text)]
    return {
        "normalized": text,
        "frequencies_mhz": freqs,
        "license_classes": classes,
        "requested_power_w": powers[0] if powers else None,
        "requested_power_basis": "eirp" if EIRP_RE.search(text) else "transmitter_output",
    }


def _keyword_hit(text: str, keyword: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(normalize(keyword)), text) is not None


def match_intents(text: str, intents: list[dict]) -> list[dict]:
    return [i for i in intents if any(_keyword_hit(text, k) for k in i["keywords"])]


class Knowledge:
    def __init__(self) -> None:
        self.sources = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text("utf-8"))["sources"]}
        self.rules = {r["id"]: r for r in json.loads((DATA / "rules.json").read_text("utf-8"))["rules"]}
        self.table = json.loads((DATA / "frequency_table.json").read_text("utf-8"))
        self.scope = fsl.load_scope()
        self.intents = json.loads(INTENTS.read_text("utf-8"))["intents"]

    def usable_rule(self, rule_id: str) -> dict | None:
        rule = self.rules.get(rule_id)
        if rule is None or rule["verification_status"] != "verified":
            return None
        source = self.sources.get(rule["source_id"])
        if source is None or source["verification_status"] != "verified":
            return None
        return rule


def _locator(locator: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in locator.items() if isinstance(v, str) and v)


def _range_text(entry: dict) -> str:
    return f"{_fmt(entry['frequency_min'])}–{_fmt(entry['frequency_max'])} {entry['unit']}"


def _nearest_listed(kb: Knowledge, freq: float, cls: str, limit: int = 2) -> list[dict]:
    """Closest raw-scope entries for the class, within ±10 % of the frequency."""
    candidates = []
    for entry in kb.scope["entries"]:
        if cls not in entry["license_classes"]:
            continue
        factor = fsl.UNIT_TO_MHZ[entry["unit"]]
        low, high = entry["frequency_min"] * factor, entry["frequency_max"] * factor
        distance = max(low - freq, freq - high, 0.0)
        if distance <= 0.1 * freq:
            candidates.append((distance, low, entry))
    return [entry for _, _, entry in sorted(candidates, key=lambda c: (c[0], c[1]))[:limit]]


def _frequency_answer(kb: Knowledge, freq: float, classes: list[str], parsed: dict) -> dict:
    """Verdict lines, limits and raw-scope evidence for one frequency."""
    lines, limits, scope_notes, rule_ids, conflicts = [], [], [], [], set()
    for cls in classes or ALL_CLASSES:
        result = fl.evaluate(
            kb.table,
            kb.sources,
            fl.Request(
                license_class=cls,
                frequency_mhz=freq,
                requested_power_w=parsed["requested_power_w"],
                requested_power_basis=parsed["requested_power_basis"],
            ),
        )
        scope = fsl.lookup_scope(kb.scope, freq, cls)
        for row_id in result["rows"]:
            row = next(r for r in kb.table["rows"] if r["id"] == row_id)
            if row.get("derived_from_rule"):
                rule_ids.append(row["derived_from_rule"])
        for match in scope["matches"]:
            conflicts.update(match["conflict_ids"])
            note = f"ham satır {match['source_row_index']}: güç '{match['observed_power_text']}'"
            if match["source_restrictions"]:
                note += "; notlar (EN transkripsiyon): " + " | ".join(match["source_restrictions"])
            if note not in scope_notes:
                scope_notes.append(note)
        known = [
            f"{_fmt(k['max_output_power'])} {k['power_unit']} ({BASIS_TR.get(k['power_basis'], k['power_basis'])})"
            for k in result["known_limits"]
        ]
        limits.extend(f"{cls} sınıfı, {_fmt_freq(freq)}: azami {k}" for k in known)
        head = f"{cls} sınıfı, {_fmt_freq(freq)}"
        if result["legal_status"] == fl.NOT_ALLOWED:
            requested = f"{_fmt(parsed['requested_power_w'])} W ({BASIS_TR[parsed['requested_power_basis']]})"
            lines.append(f"{head}: HAYIR — istenen {requested}, doğrulanmış sınırı ({', '.join(known)}) aşıyor.")
        elif result["legal_status"] in (fl.ALLOWED, fl.ALLOWED_WITH_CONDITIONS):
            lines.append(f"{head}: izin var ({result['legal_status']}); koşullar: {', '.join(result['conditions']) or 'yok'}.")
        elif known:
            lines.append(
                f"{head}: doğrulanmış azami güç {', '.join(known)}. Tam izin kararı verilemez "
                "(emisyon, alt bant ve dipnot koşulları henüz karar tablosunda değil) — karar: BİLİNMİYOR."
            )
        elif scope["scope_status"] == "SOURCE_LISTED":
            rows = ", ".join(str(m["source_row_index"]) for m in scope["matches"])
            lines.append(
                f"{head}: BTK tablosunda bu sınıf için listeleniyor (ham satır {rows}), ancak güç ve koşullar "
                "henüz karar tablosuna aktarılmadı — karar: BİLİNMİYOR."
            )
        else:
            line = (
                f"{head}: BTK amatör tablosunda bu sınıf için listelenen bir aralıkta değil; bu bilgi tabanında "
                "bu frekans için izin dayanağı yok — karar: BİLİNMİYOR (tek başına yasak kanıtı sayılmaz)."
            )
            nearest = _nearest_listed(kb, freq, cls)
            if nearest:
                line += " En yakın listelenen aralıklar: " + ", ".join(
                    f"{_range_text(e)} (ham satır {e['source_row_index']})" for e in sorted(
                        nearest, key=lambda e: e["frequency_min"] * fsl.UNIT_TO_MHZ[e["unit"]]
                    )
                ) + "."
            lines.append(line)
    return {
        "frequency_mhz": freq,
        "lines": lines,
        "limits": limits,
        "scope_notes": scope_notes,
        "rule_ids": rule_ids,
        "conflict_ids": sorted(conflicts),
    }


def answer(question: str, kb: Knowledge | None = None) -> dict:
    kb = kb or Knowledge()
    parsed = parse(question)
    intents = match_intents(parsed["normalized"], kb.intents)

    legal_ids: list[str] = []
    practice_ids: list[str] = []
    reference_ids: list[str] = []
    pending_ids: list[str] = []
    short: list[str] = []
    technical: list[str] = []
    conflicts: set[str] = set()

    def add(target: list[str], ids: list[str]) -> None:
        for item in ids:
            if item not in target:
                target.append(item)

    technical_knowledge = akn.technical_routes(parsed["normalized"], question, parsed["frequencies_mhz"])
    # A wavelength or radio-noise question uses the frequency as a physical
    # input, not as a permission question; skip the legal verdict unless a
    # class or power was also asked about.
    wave_only = any(t["topic"].startswith(("Dalga boyu", "Radyo gürültüsü")) for t in technical_knowledge) and not (
        parsed["license_classes"] or parsed["requested_power_w"] is not None
    )
    for item in technical_knowledge:
        short.extend(item["short"])

    for freq in [] if wave_only else parsed["frequencies_mhz"]:
        part = _frequency_answer(kb, freq, parsed["license_classes"], parsed)
        short.extend(part["lines"])
        technical.extend(part["limits"] + part["scope_notes"])
        add(legal_ids, part["rule_ids"] + ["TR.AMATEUR.TECHNICAL_COMPLIANCE"])
        add(practice_ids, ["IARU.R1.NATIONAL_RULES_PREVAIL"])
        conflicts.update(part["conflict_ids"])
    if parsed["frequencies_mhz"] and not parsed["license_classes"] and not wave_only:
        short.append("Belge sınıfı belirtilmedi; yukarıda A, B ve C için ayrı ayrı gösterildi.")

    for intent in intents:
        add(legal_ids, intent["legal_rule_ids"])
        add(practice_ids, intent["practice_rule_ids"])
        add(reference_ids, intent["reference_source_ids"])
        add(pending_ids, intent["pending_source_ids"])

    legal = [r for r in (kb.usable_rule(i) for i in legal_ids) if r and r["authority"] == "legal"]
    practice = [r for r in (kb.usable_rule(i) for i in practice_ids) if r and r["authority"] == "amateur_practice"]
    if not parsed["frequencies_mhz"] or wave_only:
        specific = [r for r in legal if r["id"] != "TR.AMATEUR.TECHNICAL_COMPLIANCE"]
        short.extend(r["claim"] for r in (specific or legal))
        short.extend(f"Amatör uygulama (hukuki izin değildir): {r['claim']}" for r in practice)
    references = [kb.sources[i] for i in reference_ids if kb.sources.get(i, {}).get("verification_status") == "verified"]
    pending = [kb.sources[i] for i in pending_ids if kb.sources.get(i, {}).get("verification_status") != "verified"]
    for src in references:
        short.append(f"Güncel resmî işlem/usul bilgisi için bakınız: {src['title']} — {src['publisher']} ({src['url']}).")
    for src in pending:
        short.append(
            f"Bu konudaki resmî düzenleme ({src['title']}) henüz doğrulanmadı (durum: {src['verification_status']}); "
            "kesin hukuki hüküm verilemez."
        )
    fail_closed = not short and not legal and not practice and not references and not technical_knowledge

    source_ids: list[str] = []
    add(source_ids, [r["source_id"] for r in legal + practice] + [s["id"] for s in references + pending])
    add(source_ids, [
        sid for item in technical_knowledge for sid in item["source_ids"]
        if kb.sources.get(sid, {}).get("verification_status") == "verified"
    ])
    return {
        "question": question,
        "parsed": {k: v for k, v in parsed.items() if k != "normalized"},
        "intents": [i["id"] for i in intents],
        "fail_closed": fail_closed,
        "short_answer": short,
        "legal_basis": [
            {"rule_id": r["id"], "claim": r["claim"], "conditions": r["conditions"],
             "source_id": r["source_id"], "locator": _locator(r["source_locator"])}
            for r in legal
        ],
        "technical_limits": technical,
        "technical_knowledge": [
            {"topic": t["topic"], "summary": t["short"], "details": t["lines"], "source_ids": t["source_ids"]}
            for t in technical_knowledge
        ],
        "open_source_conflicts": sorted(conflicts),
        "amateur_practice": [
            {"rule_id": r["id"], "claim": r["claim"], "source_id": r["source_id"],
             "locator": _locator(r["source_locator"])}
            for r in practice
        ],
        "sources": [
            {"source_id": s["id"], "title": s["title"], "publisher": s["publisher"], "type": s["source_type"],
             "verification_status": s["verification_status"], "url": s["url"],
             "content_sha256": s.get("content_sha256")}
            for s in (kb.sources[i] for i in source_ids)
        ],
    }


def render(result: dict) -> str:
    out = [f"Soru: {result['question']}", ""]
    if result["fail_closed"]:
        out += [
            "Kısa cevap:",
            "- Bu soruyu doğrulanmış kaynaklarla cevaplayamıyorum. Bilgi tabanında eşleşen doğrulanmış "
            "kural, frekans satırı veya resmî kaynak yok; tahmin yürütülmedi.",
        ]
        return "\n".join(out)
    out += ["Kısa cevap:"] + [f"- {line}" for line in result["short_answer"]]
    if result["legal_basis"]:
        out += ["", "Resmî / hukuki dayanak:"]
        for item in result["legal_basis"]:
            out.append(f"- {item['claim']} [{item['rule_id']}; {item['source_id']}; {item['locator']}]")
            out += [f"    koşul: {c}" for c in item["conditions"]]
    if result["technical_limits"] or result["open_source_conflicts"]:
        out += ["", "Teknik sınırlar:"] + [f"- {line}" for line in result["technical_limits"]]
        out += [f"- açık kaynak çatışması: {c} (sessizce düzeltilmez)" for c in result["open_source_conflicts"]]
    detailed = [item for item in result["technical_knowledge"] if item["details"]]
    if detailed:
        out += ["", "Teknik / işletme bilgisi (hukuki izin değildir):"]
        for item in detailed:
            out.append(f"- {item['topic']}:")
            out += [f"    {line}" for line in item["details"]]
    if result["amateur_practice"]:
        out += ["", "Amatör uygulama / IARU / TRAC tavsiyesi (hukuki izin değildir):"]
        out += [f"- {p['claim']} [{p['rule_id']}; {p['source_id']}]" for p in result["amateur_practice"]]
    out += ["", "Kaynaklar:"]
    for src in result["sources"]:
        sha = f"; sha256 {src['content_sha256'].removeprefix('sha256:')[:12]}…" if src["content_sha256"] else ""
        out.append(f"- {src['title']} — {src['publisher']} ({src['type']}, {src['verification_status']}{sha}) {src['url']}")
    return "\n".join(out)


def self_check(kb: Knowledge | None = None) -> list[str]:
    """Problems in answer_intents.json; empty list means valid."""
    kb = kb or Knowledge()
    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_keywords: dict[str, str] = {}
    for intent in kb.intents:
        iid = intent.get("id", "?")
        if iid in seen_ids:
            problems.append(f"{iid}: duplicate intent id")
        seen_ids.add(iid)
        if not intent.get("keywords"):
            problems.append(f"{iid}: keywords required")
        for kw in intent.get("keywords", []):
            key = normalize(kw)
            if key in seen_keywords and seen_keywords[key] != iid:
                problems.append(f"{iid}: keyword '{kw}' already used by {seen_keywords[key]}")
            seen_keywords[key] = iid
        for rid in intent.get("legal_rule_ids", []):
            rule = kb.usable_rule(rid)
            if rule is None or rule["authority"] != "legal":
                problems.append(f"{iid}: {rid} is not a verified legal rule on a verified source")
        for rid in intent.get("practice_rule_ids", []):
            rule = kb.usable_rule(rid)
            if rule is None or rule["authority"] != "amateur_practice":
                problems.append(f"{iid}: {rid} is not a verified amateur_practice rule")
        for sid in intent.get("reference_source_ids", []):
            if kb.sources.get(sid, {}).get("verification_status") != "verified":
                problems.append(f"{iid}: reference source {sid} must exist and be verified")
        for sid in intent.get("pending_source_ids", []):
            src = kb.sources.get(sid)
            if src is None or src["verification_status"] == "verified":
                problems.append(f"{iid}: pending source {sid} must exist and be unverified")
        if not any(intent.get(k) for k in ("legal_rule_ids", "practice_rule_ids", "reference_source_ids", "pending_source_ids")):
            problems.append(f"{iid}: intent selects nothing")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("question", nargs="?")
    parser.add_argument("--json", action="store_true", help="print the grounding bundle as JSON")
    parser.add_argument("--self-check", action="store_true", help="validate data/answer_intents.json")
    args = parser.parse_args(argv)
    if args.self_check:
        problems = self_check()
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        if problems:
            return 1
        print(f"PASS: validated {len(Knowledge().intents)} answer intent(s); every selected rule/source is verified")
        return 0
    if not args.question:
        parser.error("a question is required")
    result = answer(args.question)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
