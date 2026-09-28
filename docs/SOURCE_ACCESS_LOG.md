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
