# FTM-400 Remote — four-variant, fail-closed UI prototype

This independent, **simulation-only** preview accepts exactly four model identities: FTM-400DR, FTM-400DE, FTM-400XDR and FTM-400XDE. Firmware families remain separate (DR/DE versus XDR/XDE). No firmware update procedure or hardware protocol is inferred.

**NOT YET A RADIO CONTROLLER:** No physical radio is connected or verified. Transmit microphone, loudspeaker output, screen video, physical frequency/channel changes and RF PTT are unavailable. An opt-in receive-only PC input capture is available, but it does not prove a radio is attached. Frequency/channel/volume values are *local previews*, not hardware readback or transmit authorization. Analog FM is the intended initial integration; C4FM is deferred.

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
- Any PTT, TX, microphone-transmit or screen operation is denied (HTTP 423). No GPIO, serial, DATA, CAT or RF interface is implemented.
- GET /api/rx/sample — optional, authenticated Windows PC sound-input RX-only 2-second audio clip. Not a radio-control API.

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

## Optional Windows RX-only two-second audio capture (experimental)

Requires Windows, an intentionally selected local PC USB audio **input** connected to a verified safe receiver audio output, and FFmpeg installed on PATH. This is not a remote radio TX adapter and does not control Yaesu hardware. FFmpeg DirectShow device enumeration: https://ffmpeg.org/ffmpeg-devices.html#dshow

```powershell
ffmpeg -list_devices true -f dshow -i dummy
# Inspect the exact audio device name and independently verify safe audio levels.
$env:FTM400_RX_AUDIO_DEVICE = 'Your exact receive-only USB line-in input name'
python experimental/ftm400_remote/server.py
```

After local authentication, click **2 saniye alıcı sesi al**, then click Play in the browser audio control. The program requests up to two seconds of 16 kHz mono PCM WAV from the configured Windows DirectShow input; the clip is returned in memory, is not saved by the server and is never sent to an external network listener. One capture at a time; timeout and maximum size are enforced. The browser retains the last temporary audio Blob URL only until replaced or the tab closes.

**Security and hardware gate:** The optional input may capture unrelated audio if the wrong Windows device is selected. Only configure a dedicated receiver input with the operator's consent. Verify the radio's output is safe for the USB audio adapter; do not wire unknown microphone/DATA pins. Do not expose the service to the public Internet. FFmpeg missing, wrong device, unsupported OS, authentication failure, capture timeout and invalid output all deny audio rather than simulating success. No permanent audio recording, raw audio upload, hardware readback, PTT or TX is implemented. Green CI uses only simulated PCM WAV bytes and does not prove real radio audio capture.

- `GET /api/rx/sample`: Bearer-authenticated, origin- and Host-checked 2-second WAV; HTTP 409 when busy and HTTP 503 when input unavailable/invalid.
- `GET /api/state`: `rx_capture_configured` reports configuration only, `rx_capture_verified` remains false until physical evidence is separately verified.

Run Windows/hardware acceptance separately and record exact device/input and actual RX recording evidence only after testing with a physical device. Keep hardware Issue #63 OPEN until then.
