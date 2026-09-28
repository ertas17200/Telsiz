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
