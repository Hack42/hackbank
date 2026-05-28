const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function makeElement(id = "") {
  const element = {
    childrenBySelector: {},
    id,
    parentElement: {
      offsetHeight: 80,
      offsetWidth: 120,
    },
    style: {},
    textContent: "",
    value: "",
    closest() {
      return null;
    },
    matches() {
      return false;
    },
    querySelector(selector) {
      return this.childrenBySelector[selector] || null;
    },
  };

  Object.defineProperty(element, "offsetHeight", {
    get() {
      return 20;
    },
  });
  Object.defineProperty(element, "offsetWidth", {
    get() {
      return 40;
    },
  });

  return element;
}

function loadSpaceConsole({elements = {}, selectorMap = {}} = {}) {
  const bodyListeners = {};
  const documentListeners = {};
  const eventSources = [];
  const fetchCalls = [];
  const document = {
    body: {
      addEventListener(type, handler) {
        bodyListeners[type] = handler;
      },
    },
    addEventListener(type, handler) {
      documentListeners[type] = handler;
    },
    getElementById(id) {
      return elements[id] || null;
    },
    querySelectorAll(selector) {
      return selectorMap[selector] || [];
    },
  };

  function EventSource(url) {
    this.url = url;
    this.onmessage = null;
    eventSources.push(this);
  }

  const sandbox = {
    EventSource,
    URLSearchParams,
    console: {
      error() {},
      log() {},
    },
    document,
    fetch(url, options) {
      fetchCalls.push({url, options});
      return Promise.resolve();
    },
    window: {},
  };
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/spaceconsole/all.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "spaceconsole/all.js"});

  return {
    bodyListeners,
    documentListeners,
    eventSources,
    fetchCalls,
    spaceConsole: sandbox.window.SpaceConsole,
  };
}

test("spaceconsole index no longer loads jQuery", () => {
  const indexPath = path.join(__dirname, "../../www/spaceconsole/index.html");
  const html = fs.readFileSync(indexPath, "utf8");
  const scripts = Array.from(html.matchAll(/<script src="([^"]+)"><\/script>/g)).map(
    (match) => match[1],
  );

  assert.deepEqual(scripts, ["all.js"]);
});

test("runmsg updates power, lwt and telemetry status without jQuery", () => {
  const lamp = makeElement("lamp");
  const dot = makeElement();
  lamp.childrenBySelector["span.dot"] = dot;
  const {spaceConsole} = loadSpaceConsole({
    elements: {
      lamp,
    },
  });

  spaceConsole.runmsg("hack42/stat/lamp/POWER", "ON");
  assert.equal(lamp.style.backgroundColor, "red");

  spaceConsole.runmsg("hack42/stat/lamp/POWER", "OFF");
  assert.equal(lamp.style.backgroundColor, "green");

  spaceConsole.runmsg("hack42/stat/lamp/LWT", "Online");
  assert.equal(dot.style.display, "none");

  spaceConsole.runmsg("hack42/tele/lamp/status", "offline");
  assert.equal(dot.style.display, "");
});

test("runmsg updates sensor fields, valves and sound volume", () => {
  const volume = makeElement();
  const co = makeElement("loungeco");
  const humid = makeElement("loungehumid");
  const temp = makeElement("sensor1");
  const gebouw = makeElement("gebouw");
  const barakken = makeElement("barakken");
  const {spaceConsole} = loadSpaceConsole({
    elements: {
      barakken,
      gebouw,
      loungeco: co,
      loungehumid: humid,
      sensor1: temp,
    },
    selectorMap: {
      ".input-range": [volume],
    },
  });

  spaceConsole.runmsg("hack42/sound/volume", "[45]");
  assert.equal(volume.value, 4.5);

  spaceConsole.runmsg("hack42/sensors/dht11/lounge/co", "12");
  assert.equal(co.textContent, "12");

  spaceConsole.runmsg("hack42/sensors/dht11/lounge/humid", "53");
  assert.equal(humid.textContent, "53");

  spaceConsole.runmsg("hack42/sensors/1wire/sensor1", "19.5");
  assert.equal(temp.textContent, "19.5");

  spaceConsole.runmsg("hack42/stookkelder/hoofdgebouwvalve", "open");
  assert.equal(gebouw.style.backgroundColor, "red");

  spaceConsole.runmsg("hack42/stookkelder/barrakkenvalve", "closed");
  assert.equal(barakken.style.backgroundColor, "green");
});

test("bindEvents posts power toggles and volume changes", () => {
  const {bodyListeners, fetchCalls, spaceConsole} = loadSpaceConsole();

  spaceConsole.bindEvents();

  bodyListeners.click({
    target: {
      closest(selector) {
        assert.equal(selector, "div.powerswitch");
        return {id: "lamp"};
      },
    },
  });
  bodyListeners.input({
    target: {
      value: "7",
      matches(selector) {
        assert.equal(selector, ".input-range");
        return true;
      },
    },
  });

  assert.equal(fetchCalls.length, 2);
  assert.equal(fetchCalls[0].url, "cmd.php");
  assert.equal(fetchCalls[0].options.method, "POST");
  assert.equal(String(fetchCalls[0].options.body), "action=toggle&device=lamp");
  assert.equal(String(fetchCalls[1].options.body), "action=volume&value=7");
});

test("init textfills labels, binds events and consumes stream messages", () => {
  const label = makeElement();
  const lamp = makeElement("lamp");
  const {documentListeners, eventSources} = loadSpaceConsole({
    elements: {
      lamp,
    },
    selectorMap: {
      ".Knopjetext": [label],
    },
  });

  documentListeners.DOMContentLoaded();
  assert.equal(eventSources.length, 1);
  assert.equal(eventSources[0].url, "stream.php");

  eventSources[0].onmessage({
    data: JSON.stringify(["hack42/stat/lamp/POWER", "ON"]),
  });

  assert.equal(lamp.style.backgroundColor, "red");
  assert.equal(label.style.top, "30px");
});
