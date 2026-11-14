"use strict";
let token = "";
let rxObjectUrl = null;
const el = id => document.getElementById(id);
function message(text) { el("message").textContent = text; }
async function call(path, data) {
  const headers = {Authorization: "Bearer " + token};
  const opts = {method: data ? "POST" : "GET", headers};
  if (data) { headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(data); }
  const res = await fetch(path, opts);
  const json = await res.json();
  if (!res.ok) throw Error(json.error || "request failed");
  return json;
}
function show(state) {
  el("model").value = state.model;
  el("rx-button").disabled = !state.rx_capture_configured;
  el("rx-status").textContent = state.rx_capture_configured ? "RX giriş ayarı var, gerçek donanım henüz doğrulanmadı." : "RX girişi: yapılandırılmadı";
  el("family").textContent = "Firmware ailesi: " + state.firmware_family;
  el("readback").textContent = "Yalnız önizleme: " + (state.frequency_preview_mhz ?? "—") + " MHz / Kanal " + (state.channel_preview ?? "—") + " / Ses " + (state.volume_preview ?? "—") + " | PTT: " + state.ptt;
  message("Bağlandı: " + state.status + " — gerçek cihaz bağlı değil.");
}
async function execute(action, valueName, value) {
  try { show(await call("/api/preview", {action, [valueName]: value})); }
  catch (e) { message("HOLD: " + e.message); }
}
el("connect").addEventListener("click", async () => {
  token = el("token").value;
  el("token").value = "";
  try { show(await call("/api/state")); } catch(e) { token = ""; message("HOLD: " + e.message); }
});
el("set-model").addEventListener("click", () => execute("select_model", "model", el("model").value));
function parseNumberInput(raw, min, max, integer) {
  // Number("") and Number(" ") both become 0, which is a valid volume value.
  // Require an explicit decimal value before allowing any command to be sent.
  if (typeof raw !== "string" || !/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(raw.trim())) {
    throw Error("Sayısal değer girilmeli (boş veya geçersiz giriş reddedildi)");
  }
  const value = Number(raw);
  if (!Number.isFinite(value) || value < min || value > max || (integer && !Number.isInteger(value))) {
    throw Error("Değer izin verilen aralıkta olmalı");
  }
  return value;
}
function executeNumber(action, inputId, key, min, max, integer) {
  try {
    return execute(action, key, parseNumberInput(el(inputId).value, min, max, integer));
  } catch (e) {
    message("HOLD: " + e.message);
    return Promise.resolve();
  }
}
el("set-frequency").addEventListener("click", () => executeNumber("preview_frequency", "frequency", "frequency_mhz", 1, 1000, false));
el("set-channel").addEventListener("click", () => executeNumber("preview_channel", "channel", "channel", 1, 999, true));
el("set-volume").addEventListener("click", () => executeNumber("preview_volume", "volume", "volume", 0, 100, true));

// Explicitly authenticated one-shot RX clip; no token in URLs and no auto-play.
el("rx-button").addEventListener("click", async () => {
  const button = el("rx-button");
  button.disabled = true;
  try {
    if (!token) throw Error("önce bağlanılmalı");
    const response = await fetch("/api/rx/sample", {headers: {Authorization: "Bearer " + token}, cache: "no-store"});
    if (!response.ok) {
      const failure = await response.json();
      throw Error(failure.error || "alıcı ses kaydı alınamadı");
    }
    if (!response.headers.get("Content-Type")?.startsWith("audio/wav")) throw Error("beklenmeyen ses formatı");
    const blob = await response.blob();
    if (!blob.size || blob.size > 131072) throw Error("geçersiz ses boyutu");
    const player = el("rx-player");
    if (rxObjectUrl) URL.revokeObjectURL(rxObjectUrl);
    rxObjectUrl = URL.createObjectURL(blob);
    player.src = rxObjectUrl;
    player.load();
    message("İki saniyelik RX kaydı hazır. Dinlemek için oynat düğmesine basın.");
  } catch (error) {
    message("HOLD: " + error.message);
  } finally {
    // Do not turn on the capability if there has been no successful configuration readback.
    button.disabled = !token || el("rx-status").textContent.startsWith("RX girişi: yapılandırılmadı");
  }
});
