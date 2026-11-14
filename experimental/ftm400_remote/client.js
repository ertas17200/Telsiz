"use strict";
let token = "";
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
el("set-frequency").addEventListener("click", () => execute("preview_frequency", "frequency_mhz", Number(el("frequency").value)));
el("set-channel").addEventListener("click", () => execute("preview_channel", "channel", Number(el("channel").value)));
el("set-volume").addEventListener("click", () => execute("preview_volume", "volume", Number(el("volume").value)));
