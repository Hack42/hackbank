const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function node(tag) {
  return {
    tag,
    children: [],
    attributes: {},
    listeners: {},
    style: {setProperty() {}},
    appendChild(child) { this.children.push(child); },
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(event, handler) { this.listeners[event] = handler; },
  };
}

function state(pos, space, {posMuted = false, posAvailable = true} = {}) {
  return {channels: {
    pos: {available: posAvailable, volume: pos, muted: posMuted},
    space: {available: true, volume: space, muted: false},
  }};
}

function audioFixture() {
  const requests = [];
  const timeouts = new Map();
  const intervals = new Map();
  let timer = 0;
  const window = {
    fetch(url, options) {
      return new Promise((resolve, reject) => requests.push({url, options, resolve, reject}));
    },
    setTimeout(callback) { timeouts.set(++timer, callback); return timer; },
    clearTimeout(id) { timeouts.delete(id); },
    setInterval(callback) { intervals.set(++timer, callback); return timer; },
    clearInterval(id) { intervals.delete(id); },
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../../www/kassa-audio.js"), "utf8"), {
    window, document: {createElement: node},
  });
  const container = node("main");
  const controller = window.HackBankAudio.mount(container);
  const panel = container.children[0];
  const controls = Object.fromEntries(panel.children[0].children.map((card) => {
    const input = card.children.find((child) => child.tag === "input");
    return [input.id.replace("Volume-", ""), {input, output: card.children[0].children[1]}];
  }));
  const flush = () => new Promise((resolve) => setImmediate(resolve));
  return {
    requests, controls, controller, timeouts, intervals, status: panel.children[1],
    async reply(index, payload, ok = true) {
      requests[index].resolve({ok, json: () => Promise.resolve(payload)});
      await flush();
    },
    poll() { intervals.forEach((callback) => callback()); },
    change(channel, value, immediate = true) {
      const input = controls[channel].input;
      input.value = String(value);
      input.listeners.input();
      if(immediate) input.listeners.change();
    },
  };
}

test("audio sliders read actual state and reflect external changes and missing devices", async () => {
  const audio = audioFixture();
  assert.equal(audio.controls.pos.input.disabled, true);
  await audio.reply(0, state(50, 92));
  assert.equal(audio.controls.pos.input.value, "50");
  assert.equal(audio.controls.space.input.value, "92");
  assert.equal(audio.controls.pos.input.disabled, false);
  audio.poll();
  await audio.reply(1, state(15, 60, {posMuted: true}));
  assert.equal(audio.controls.pos.input.value, "15");
  assert.equal(audio.controls.pos.output.textContent, "Muted");
  assert.equal(audio.controls.space.output.textContent, "60%");
  audio.poll();
  await audio.reply(2, state(null, 60, {posAvailable: false}));
  assert.equal(audio.controls.pos.input.disabled, true);
  assert.equal(audio.controls.space.input.disabled, false);
  assert.equal(audio.status.textContent, "One audio output is unavailable.");
});

test("rapid volume edits keep the latest intent and ignore stale reads", async () => {
  const audio = audioFixture();
  await audio.reply(0, state(35, 70));
  audio.poll(); // A read starts before the user moves the sliders.
  audio.change("pos", 64);
  audio.change("pos", 10);
  audio.change("space", 66);
  assert.equal(audio.requests.length, 3); // Only one write is in flight.
  await audio.reply(1, state(35, 70));
  assert.equal(audio.controls.pos.input.value, "10");
  assert.equal(audio.controls.space.input.value, "66");
  await audio.reply(2, state(64, 70));
  assert.equal(audio.controls.pos.input.value, "10");
  await audio.reply(3, state(10, 70));
  await audio.reply(4, state(10, 66));
  await audio.reply(5, state(10, 66));
  assert.deepEqual(audio.requests.filter((request) => request.options.method === "POST")
    .map((request) => JSON.parse(request.options.body)), [
    {channel: "pos", volume: 64}, {channel: "pos", volume: 10}, {channel: "space", volume: 66},
  ]);
  assert.equal(audio.controls.pos.input.value, "10");
  assert.equal(audio.controls.space.input.value, "66");
});

test("audio failures disable controls and a later poll recovers the real state", async () => {
  const audio = audioFixture();
  await audio.reply(0, {error: "unavailable"}, false);
  assert.equal(audio.controls.pos.input.disabled, true);
  assert.equal(audio.status.textContent, "Audio controls are unavailable.");
  audio.poll();
  await audio.reply(1, state(30, 80));
  assert.equal(audio.controls.pos.input.disabled, false);
  assert.equal(audio.controls.space.input.value, "80");
  audio.poll();
  await audio.reply(2, {unexpected: true});
  assert.equal(audio.controls.pos.input.disabled, true);
  assert.equal(audio.status.textContent, "Audio controls are unavailable.");
});

test("leaving Sounds cancels queued volume edits and ignores late replies", async () => {
  const audio = audioFixture();
  await audio.reply(0, state(35, 70));
  audio.poll();
  audio.change("pos", 60, false);
  assert.equal(audio.timeouts.size, 1);
  audio.controller.stop();
  assert.equal(audio.timeouts.size, 0);
  assert.equal(audio.intervals.size, 0);
  await audio.reply(1, state(10, 20));
  assert.equal(audio.controls.pos.input.value, "60");
  assert.equal(audio.controls.space.input.value, "70");
  assert.equal(audio.requests.length, 2);
});
