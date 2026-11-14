'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

(async function run() {
  const handlers = {};
  const elements = new Map();
  for (const id of ['token', 'connect', 'message', 'model', 'family', 'readback', 'frequency', 'set-frequency', 'channel', 'set-channel', 'volume', 'set-volume', 'set-model']) {
    elements.set(id, {value: '', textContent: '', addEventListener: (_event, cb) => {handlers[id] = cb;}});
  }
  const requests = [];
  const context = {
    document: {getElementById: id => {assert.ok(elements.has(id), 'unexpected DOM id ' + id); return elements.get(id);}},
    fetch: async (route, options) => {
      requests.push({route, options});
      return {ok: true, json: async () => ({model: 'FTM-400DR', firmware_family: 'DR/DE',
        frequency_preview_mhz: null, channel_preview: null, volume_preview: 0, ptt: 'HARDWARE_LOCKED', status: 'SIMULATION_ONLY'})};
    },
  };
  const script = fs.readFileSync(path.join(__dirname, '..', 'experimental', 'ftm400_remote', 'client.js'), 'utf8');
  vm.runInNewContext(script, context, {filename: 'client.js', timeout: 2000});

  // Unauthorized browser UI action with an empty numeric input must not be coerced to zero.
  elements.get('volume').value = '';
  await handlers['set-volume']();
  assert.equal(requests.length, 0, 'empty volume must never cause an API request');
  assert.match(elements.get('message').textContent, /HOLD:/);

  elements.get('volume').value = '  ';
  await handlers['set-volume']();
  assert.equal(requests.length, 0, 'whitespace volume must never cause an API request');

  // Explicit zero is valid and must survive as an integer.
  elements.get('volume').value = '0';
  await handlers['set-volume']();
  assert.equal(requests.length, 1);
  assert.equal(JSON.parse(requests[0].options.body).volume, 0);

  // Incomplete/non-finite/out-of-range values are rejected before any request.
  for (const value of ['0x10', 'Infinity', 'NaN', '-1', '101', '1.5']) {
    elements.get('volume').value = value;
    await handlers['set-volume']();
  }
  assert.equal(requests.length, 1, 'malformed volume values should not call API');

  elements.get('channel').value = '';
  await handlers['set-channel']();
  assert.equal(requests.length, 1);
  elements.get('frequency').value = '';
  await handlers['set-frequency']();
  assert.equal(requests.length, 1);

  elements.get('channel').value = '15';
  await handlers['set-channel']();
  assert.equal(JSON.parse(requests[1].options.body).channel, 15);
  elements.get('frequency').value = '145.500';
  await handlers['set-frequency']();
  assert.equal(JSON.parse(requests[2].options.body).frequency_mhz, 145.5);

  console.log('FTM400_JS_UI_NUMERIC_VALIDATION=PASS scenarios=14');
})().catch(e => {console.error(e); process.exitCode = 1;});
