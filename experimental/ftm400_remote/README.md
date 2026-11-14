# FTM-400 Remote — four-variant, fail-closed UI prototype

This independent, **simulation-only** preview accepts exactly four model identities: FTM-400DR, FTM-400DE, FTM-400XDR and FTM-400XDE. Firmware families remain separate (DR/DE versus XDR/XDE). No firmware update procedure or hardware protocol is inferred.

**NOT YET A RADIO CONTROLLER:** No physical radio is connected. Microphone, loudspeaker, screen video, physical frequency/channel changes and RF PTT are unavailable. Frequency/channel/volume values are *local previews*, not hardware readback or transmit authorization. Analog FM is the intended initial integration; C4FM is deferred.

## Run locally (Python 3.12, standard library only)

From the repository root, in Windows PowerShell:

```powershell
$env:FTM400_REMOTE_TOKEN = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
python experimental/ftm400_remote/server.py
```

Open http://127.0.0.1:8765/ on the same computer. Paste the generated token into the password field and click Bağlan. The token is held only in the browser tab's JavaScript memory (no cookies or persistent storage). Stop with Ctrl+C and remove the environment variable after the session. Use a fresh random token for each session.

The server refuses any bind address other than 127.0.0.1 and any missing or short token. No direct Internet/VPN listener is provided. For future phone access, add a separately reviewed authenticated VPN/reverse-proxy layer; never expose this HTTP development server to the public Internet.

## API contract

- GET / — static, read-only HTML UI.
- GET /api/state — authenticated simulator state; hardware_connected=false and rf_transmit_enabled=false.
- POST /api/preview — authenticated exact-key JSON commands: select_model, preview_frequency, preview_channel, preview_volume. All are local-only previews.
- Any PTT, TX, audio, microphone or screen operation is denied (HTTP 423). No device, audio, GPIO, serial or CAT interface is implemented.

Security controls: constant-time Bearer token comparison, loopback binding, 1024-byte JSON body cap, duplicate JSON key refusal, strict typed/ranged parameters, unknown command denial, same-origin POST check, strict Content Security Policy, no token logging.

## Tests

```bash
python -m unittest discover -s tests -p 'test_ftm400_remote.py' -v
python -m unittest discover -s tests -p 'test_*.py' -v
```

Test coverage includes all four identities, family isolation, invalid/ambiguous models, strict parameter limits, duplicate JSON keys, disabled PTT, unauthorized client rejection, cross-origin denial, and oversized body denial. Passing these tests **does not prove physical radio support**.

## Hardware activation gates — unresolved

1. Independently verify Yaesu documentation, model/hardware variant and DATA/MIC pinouts.
2. Verify receive-only USB audio hardware against a physical unit, with evidence and independent readback.
3. Before any TX implementation: physical PTT hard-stop, watchdog, authentication, exclusive operator, loss-of-network and power-failure release, regulatory constraints, and hardware acceptance tests.
4. Frequency/channel control requires independent actual-device readback; simulated preview must never be treated as physical state.
5. Screen requires verified camera and controlled mechanical interface; do not pretend an undocumented screen mirroring or CAT protocol exists.
6. Confirm exact-head CI, independent security review, and user acceptance before releasing the hardware-connected program.

Existing source-grounded scripts, legal rules, firmware guard, and CI contracts are not modified. Rollback: remove experimental/ftm400_remote and tests/test_ftm400_remote.py on the feature branch.
