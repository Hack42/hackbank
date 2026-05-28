const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadStreamHelpers() {
  const eventSources = [];
  const timers = [];
  function EventSource(url) {
    this.url = url;
    this.closeCalled = false;
    this.close = () => {
      this.closeCalled = true;
    };
    eventSources.push(this);
  }
  const sandbox = {
    Date,
    EventSource,
    clearTimeout() {},
    setTimeout(callback, delay) {
      timers.push({callback, delay});
      return timers.length;
    },
    window: {},
  };
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-stream.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-stream.js"});

  return {
    eventSources,
    helpers: sandbox.window.HackBankStream,
    timers,
  };
}

test("stream helper opens a session stream and dispatches messages", () => {
  const messages = [];
  const {eventSources, helpers} = loadStreamHelpers();

  helpers.createSessionStream({
    session: "main",
    onMessage(path, msg) {
      messages.push({path, msg});
    },
  });
  eventSources[0].onmessage({
    data: JSON.stringify(["hack42bar/output/session/main/message", "ok"]),
  });

  assert.match(eventSources[0].url, /^stream\.php\?session=main&t=/);
  assert.deepEqual(messages, [
    {
      msg: "ok",
      path: "hack42bar/output/session/main/message",
    },
  ]);
});

test("stream helper reconnects once for closed/error states", () => {
  const {eventSources, helpers, timers} = loadStreamHelpers();

  helpers.createSessionStream({
    session: "main",
    onMessage() {},
  });
  eventSources[0].onmessage({data: "closed"});
  eventSources[0].onerror();

  assert.equal(eventSources[0].closeCalled, true);
  assert.equal(timers.length, 1);
  assert.equal(timers[0].delay, 1000);
});

test("stream helper reports invalid JSON without dispatching", () => {
  const invalid = [];
  const messages = [];
  const {eventSources, helpers} = loadStreamHelpers();

  helpers.createSessionStream({
    session: "main",
    onInvalidMessage(data) {
      invalid.push(data);
    },
    onMessage(path, msg) {
      messages.push({path, msg});
    },
  });
  eventSources[0].onmessage({data: "no-json"});

  assert.deepEqual(invalid, ["no-json"]);
  assert.deepEqual(messages, []);
});
