# Resmî Kaynak Erişim Kayıtları

Ortam: Claude Code bulut oturumu (egress proxy). Erişim sonucu kaynağın kendisi hakkında değil, yalnız bu çalışma ortamı hakkında bilgi verir.

## 2026-09-28 probe

| DOMAIN | ACCESS | HTTP_STATUS | ERROR_CLASS | TESTED_AT |
|---|---|---|---|---|
| www.btk.gov.tr | BLOCKED | — (CONNECT 403) | EGRESS_POLICY (curl: CONNECT tunnel failed 403; WebFetch: EGRESS_BLOCKED) | 2026-09-28T19:03:28Z |
| www.mevzuat.gov.tr | BLOCKED | — (CONNECT 403) | EGRESS_POLICY (curl + WebFetch) | 2026-09-28T19:03:29Z |
| www.resmigazete.gov.tr | BLOCKED | — (CONNECT 403) | EGRESS_POLICY (curl + WebFetch) | 2026-09-28T19:03:29Z |
| resmigazete.gov.tr | BLOCKED | — (CONNECT 403) | EGRESS_POLICY (curl + WebFetch) | 2026-09-28T19:03:29Z |

Sonuç: P0 (BTK frekans tablosu), P1 (5809), P2 (FTM Yönetmeliği), P3 (KEGM Yönetmeliği) = `BLOCKED_BY_OFFICIAL_SOURCE_ACCESS`. Gayriresmî mirror kullanılmadı.


## 2026-09-28 trusted web-render follow-up

A separate trusted web-rendering path successfully opened the official BTK PDF at the canonical `btk.gov.tr` URL as `application/pdf`, reported **47 pages**, exposed the PDF text layer, and allowed visual verification of the amateur section and table pages.

This does **not** invalidate the earlier Claude Code egress result: that cloud execution environment was still blocked. It only means the official source content could be independently inspected through another trusted rendering path.

What is now available:

- official Article 22 text;
- visual/table transcription of all **33** amateur frequency rows on PDF pages 41-45/47;
- `Tablo 26-1` emission code/bandwidth reference on page 46/47.

What is still missing:

- raw PDF bytes in the code-execution runtime;
- artifact file size from a byte-for-byte download;
- SHA-256 digest.

Therefore P0 advances from **source-content blocked** to **raw transcription complete / semantic promotion HOLD**. `coverage_status` remains `partial`; no complete legal-permission verdict is enabled.

## ≈2026-09-28T20:30Z — candidate source domains (Claude Code environment)

| DOMAIN | ACCESS | ERROR_CLASS |
|---|---|---|
| www.btk.gov.tr, www.mevzuat.gov.tr, www.resmigazete.gov.tr, www.kiyiemniyeti.gov.tr, www.uab.gov.tr | BLOCKED | curl: CONNECT refused (HTTP 000); WebFetch EGRESS_BLOCKED (btk, mevzuat, resmigazete, kiyiemniyeti) |
| www.itu.int, www.cept.org, docdb.cept.org, efis.cept.org | BLOCKED | curl: CONNECT refused (HTTP 000); WebFetch EGRESS_BLOCKED (docdb.cept.org) |
| www.iaru-r1.org, www.iaru.org, trac.org.tr | BLOCKED | curl: CONNECT refused (HTTP 000); WebFetch EGRESS_BLOCKED (iaru-r1, trac) |
| github.com/arch-yunus/Amator-Telsiz- | NOT_FOUND_OR_PRIVATE | GitHub add_repo "not found or no access"; WebFetch HTTP 404 |

Result: no candidate in `data/source_candidates.json` could be verified; all remain `candidate_unverified` / `candidate_inaccessible`.


## 2026-09-28 — independent access recheck

| TARGET | ACCESS | EVIDENCE | CONSEQUENCE |
|---|---|---|---|
| BTK canonical Technical Criteria PDF | RENDER_REACHABLE | Canonical URL opened as a 47-page PDF; decision date `23.09.2022`, decision no. `2022/İK-SYD/245`; Article 22 and the amateur table are visible | Source-content reading is available, but this does **not** satisfy byte-level artifact verification |
| BTK canonical PDF raw bytes | UNAVAILABLE_IN_RUNTIME | Direct raw-byte download failed in the working runtime | `artifact.sha256` remains unknown; P0 artifact gate stays fail-closed |
| `github.com/arch-yunus/Amator-Telsiz-Rehberi` | REACHABLE | GitHub repository metadata, README, ROADMAP and root tree were read successfully; repository reports MIT license | Candidate status corrected from `candidate_inaccessible` to `candidate_unverified`; community content still cannot ground legal claims |

This recheck supersedes only the earlier access-state observation for the community repository. It does not retroactively verify any claim copied from that repository.


## 2026-09-28 — P1/P2/P3 canonical-text recheck

The current verification path can read several official BTK/KEGM web pages, but still cannot retrieve the canonical consolidated Mevzuat Bilgi Sistemi texts needed for exact-text legal promotion.

| PHASE | CANONICAL TARGET | CURRENT ACCESS | OFFICIAL CORROBORATION | RESULT |
|---|---|---|---|---|
| P1 — Law No. 5809 | `https://www.mevzuat.gov.tr/Metin1.Aspx?MevzuatIliski=0&MevzuatKod=1.5.5809&No=5809&Tertip=5&Tur=1` | inaccessible in current web path; PDF variant timed out | BTK's current FTM page quotes Article 37(3) and references Articles 36/37; other current BTK pages also attribute provisions to Law No. 5809 | `VERIFY_REQUIRED`; no promotion from secondary quotation alone |
| P2 — FTM Regulation | `https://www.mevzuat.gov.tr/Metin.Aspx?MevzuatIliski=0&MevzuatKod=7.5.29010&sourceXmlSearch=frekans` | inaccessible in current web path | BTK's current FTM page identifies the regulation as published 27.11.2018 / RG 30608 and quotes Article 6(1) | `VERIFY_REQUIRED`; consolidated exact text still missing |
| P3 — KEGM amateur exam/certification regulation | `https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=13769&MevzuatTur=7&MevzuatTertip=5` | inaccessible in current web path | KEGM's current Regulations page maps the title to MevzuatNo 13769; KEGM FAQ/2026 exam notice quote selected provisions | `VERIFY_REQUIRED`; selected official quotations do not replace the consolidated regulation |

Fail-closed interpretation:

- official institutional quotations are useful corroboration and provenance;
- they do not replace the current consolidated legal text for rule promotion;
- P1/P2/P3 remain on HOLD for exact-text verification;
- work may proceed on source-independent engineering features without weakening these legal gates.


## 2026-09-29 — AFAD current regulation recheck

Current-law discovery corrected the prior P8 target.

| TARGET | RESULT | EVIDENCE / CONSEQUENCE |
|---|---|---|
| AFAD TAMP page | REACHABLE | Still states 2022 TAMP publication and 24.02.2022/31760 legal basis; this legal-basis metadata is stale after the 2025 replacement |
| UAB current emergency-law index | REACHABLE | Lists 31.12.2025 / 10809 Afet ve Acil Durum Müdahale Hizmetleri Yönetmeliği as current emergency legislation |
| Exact Official Gazette origin URL | RESOLVED | `https://www.resmigazete.gov.tr/eskiler/2025/12/20251231M5-15.pdf` |
| Exact Official Gazette PDF body/raw bytes | INACCESSIBLE_IN_CURRENT_VERIFICATION_PATH | Web fetch returned origin failure and raw download also failed; no byte hash or origin screenshot could be produced |
| 2022/5211 historical full text | REACHABLE_OFFICIAL_ARCHIVE | Official Aile ve Sosyal Hizmetler Bakanlığı PDF is readable; retained as historical/repealed only |
| Current 10809 consolidated text | CORROBORATED_ONLY | Independent consolidated copies report Article 37 repeal of 5211, Geçici Madde 1 TAMP transition, and current 31.12.2025 effectiveness; not promoted as origin legal authority |

Fail-closed result:

```text
CURRENT_INSTRUMENT=10809
CURRENT_EFFECTIVE_DATE=2025-12-31
OLD_INSTRUMENT=5211
OLD_STATUS=REPEALED
TAMP_PAGE_2022_LEGAL_BASIS_METADATA=STALE
CURRENT_ORIGIN_EXACT_TEXT=PENDING
LEGAL_RULE_PROMOTION=HOLD
```

The current-law metadata correction is accepted; exact legal-text promotion is not.


## 2026-09-29 — autonomous closure source-access recheck

Probe path: trusted web renderer plus existing exact-head GitHub Actions artifact evidence. A domain result describes this access path only; it is not a statement that the public service is globally unavailable.

| DOMAIN | ACCESS | HTTP_STATUS | ERROR_CLASS | TESTED_AT |
|---|---|---|---|---|
| www.btk.gov.tr | PASS | response status not exposed by renderer | NONE | 2026-09-29T21:10:00+03:00 |
| www.mevzuat.gov.tr | BLOCKED | origin status not observed | TIMEOUT_FETCHING | 2026-09-29T21:10:00+03:00 |
| www.resmigazete.gov.tr | BLOCKED | origin status not observed | TIMEOUT_FETCHING | 2026-09-29T21:10:00+03:00 |
| resmigazete.gov.tr | BLOCKED | origin status not observed | TIMEOUT_FETCHING | 2026-09-29T21:10:00+03:00 |

Canonical P0 PDF target:

```text
URL=https://www.btk.gov.tr/uploads/pages/ftm-teknik-olcutler-ek-5.pdf
ACCESS=PASS
CONTENT_TYPE=application/pdf
PDF_PAGE_COUNT=47
ARTICLE=MADDE 22
VISIBLE_TABLE_HEADING=Tablo 25
ARTICLE_REFERENCE=Tablo-26
EMISSION_REFERENCE=Tablo 26-1
```

The current GitHub artifact registry already carries byte-level evidence from run `36559259435` / job `109375881365`:

```text
FETCHED_AT=2026-09-29T11:02:27Z
SIZE_BYTES=508766
SHA256=eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0
CONTENT_TYPE=application/pdf
FINAL_URL=https://www.btk.gov.tr/uploads/pages/ftm-teknik-olcutler-ek-5.pdf
ARTIFACT_STATUS=verified_bytes
CHANGE_STATUS=UNCHANGED
```

The old log statements saying that P0 still lacked raw bytes/hash are superseded by the byte-binding checkpoint. P0 is no longer blocked by artifact access; it remains partial because of structured semantic-model gaps and explicit source conflicts.

P1/P2/P3 remain fail-closed: current consolidated texts on `www.mevzuat.gov.tr` were not retrievable in this recheck, and direct root probes for both Resmî Gazete hosts timed out. Search-index visibility of some Resmî Gazete pages is not treated as consolidated exact-text access.


## 2026-09-29 — P1/P2/P3 fail-closed artifact acquisition gates

The pending official legal sources are now registered in `data/artifacts.json` without fabricated byte evidence:

| SOURCE_ID | EXPECTED_MIME | ARTIFACT_STATUS | HASH | REVERIFY |
|---|---|---|---|---|
| `TR.BTK.EHK.5809` | `text/html` | `awaiting_bytes` | null | true |
| `TR.BTK.FTM.REGULATION.2018` | `text/html` | `awaiting_bytes` | null | true |
| `TR.KEGM.AMATEUR.EXAM.REGULATION` | `text/html` | `awaiting_bytes` | null | true |

No pending record may carry `fetched_at`, `size_bytes`, or `sha256` before a successful official fetch and provenance review. `change_status` remains `UNKNOWN`.

The observation client now derives its temporary file suffix from `expected_mime_type`, not from URL path syntax. This is required for Mevzuat URLs ending in `.Aspx` or without a file extension: valid `text/html` responses must be inspected as HTML rather than misclassified from a temporary `.Aspx`/`.bin` filename.

The generalized workflow `.github/workflows/official-artifact-observation.yml` can observe P0, P1, P2 or P3 by `source_id`. It enforces:

- exact-head checkout and nonblank runner identity;
- clean worktree before/after observation;
- tracked Python-cache hygiene;
- artifact-registry validation;
- HTTPS canonical URL and same-origin final URL;
- HTTP 200;
- exact expected Content-Type;
- bounded nonzero byte stream;
- SHA-256 observation and change classification;
- review-only binding: no automatic source hash mutation.

A failed fetch, wrong MIME, non-200 response, cross-origin redirect, size violation, zero-byte result or `SOURCE_CHANGED` cannot be reported as PASS.

Current legal-content state is unchanged:

```text
TR.BTK.EHK.5809=PENDING / BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
TR.BTK.FTM.REGULATION.2018=PENDING / BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
TR.KEGM.AMATEUR.EXAM.REGULATION=PENDING / BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
RULE_PROMOTION=PROHIBITED_UNTIL_EXACT_OFFICIAL_TEXT_VERIFIED
```
