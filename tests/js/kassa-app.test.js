const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function makeElement(tag, register) {
  const element = {
    attributes: {},
    childElementCount: 0,
    children: [],
    className: "",
    eventListeners: {},
    id: "",
    innerHTML: "",
    parentElement: null,
    scrollHeight: 0,
    scrollTop: 0,
    style: {},
    tag,
    _textContent: "",
    value: "",
    get textContent() {
      return this._textContent;
    },
    set textContent(value) {
      this._textContent = String(value);
      if(value === "") {
        this.children = [];
        this.childElementCount = 0;
      }
    },
    appendChild(child) {
      child.parentElement = this;
      this.children.push(child);
      this.childElementCount = this.children.length;
      return child;
    },
    addEventListener(type, handler) {
      this.eventListeners[type] = handler;
    },
    classList: {
      add(className) {
        const classes = new Set(element.className.split(/\s+/).filter(Boolean));
        classes.add(className);
        element.className = Array.from(classes).join(" ");
      },
      remove(className) {
        element.className = element.className
          .split(/\s+/)
          .filter((item) => item && item !== className)
          .join(" ");
      },
    },
    focus() {
      this.focused = true;
    },
    cloneNode(deep) {
      const clone = makeElement(this.tag, register);
      clone.attributes = {...this.attributes};
      clone.className = this.className;
      clone.id = this.id;
      clone.innerHTML = this.innerHTML;
      clone.scrollHeight = this.scrollHeight;
      clone.style = {...this.style};
      clone.textContent = this.textContent;
      clone.value = this.value;
      if(deep) {
        this.children.forEach((child) => {
          clone.appendChild(child.cloneNode ? child.cloneNode(true) : {...child});
        });
      }
      return clone;
    },
    prepend(child) {
      child.parentElement = this;
      this.children.unshift(child);
      this.childElementCount = this.children.length;
      return child;
    },
    querySelector(selector) {
      return findFirst(this, selector);
    },
    remove() {
      if(!this.parentElement) return;
      this.parentElement.children = this.parentElement.children.filter(
        (child) => child !== this,
      );
      this.parentElement.childElementCount = this.parentElement.children.length;
      this.parentElement = null;
    },
    setAttribute(name, value) {
      this.attributes[name] = value;
      this[name] = value;
      if(name === "id") {
        this.id = value;
        register(value, this);
      }
    },
  };
  return element;
}

function matchesSelector(element, selector) {
  if(!element.className) return false;
  const cleanSelector = selector.replace(":visible", "");
  if(cleanSelector.startsWith("#")) return element.id === cleanSelector.slice(1);
  if(cleanSelector.startsWith(".")) {
    return element.className.split(/\s+/).includes(cleanSelector.slice(1));
  }
  return element.tag === cleanSelector;
}

function findAll(root, selector, results = []) {
  if(selector.includes(" ")) {
    const parts = selector.split(/\s+/);
    const parents = findAll(root, parts[0]);
    parents.forEach((parent) => findAll(parent, parts.slice(1).join(" "), results));
    return results;
  }
  root.children.forEach((child) => {
    if(matchesSelector(child, selector)) results.push(child);
    if(child.children) findAll(child, selector, results);
  });
  return results;
}

function findFirst(root, selector) {
  return findAll(root, selector)[0] || null;
}

function loadScript(sandbox, scriptName) {
  const script = fs.readFileSync(
    path.join(__dirname, "../../www", scriptName),
    "utf8",
  );
  vm.runInNewContext(script, sandbox, {filename: scriptName});
}

function loadKassaApp({hash = ""} = {}) {
  const elements = {};
  const documentListeners = {};
  const eventSources = [];
  const fetchCalls = [];
  const textfillCalls = [];
  const timers = [];
  const register = (id, element) => {
    elements[id] = element;
  };
  const body = makeElement("body", register);
  body.id = "body";
  register("body", body);

  const document = {
    body,
    addEventListener(type, handler) {
      documentListeners[type] = handler;
    },
    createElement(tag) {
      return makeElement(tag, register);
    },
    createTextNode(text) {
      return {
        nodeType: 3,
        parentElement: null,
        textContent: text,
        cloneNode() {
          return {...this};
        },
      };
    },
    getElementById(id) {
      return elements[id] || null;
    },
    querySelector(selector) {
      if(selector === "#body") return body;
      if(selector.startsWith("#")) return elements[selector.slice(1)] || null;
      return findFirst(body, selector);
    },
    querySelectorAll(selector) {
      return findAll(body, selector);
    },
  };

  function EventSource(url) {
    this.url = url;
    this.closeCalled = false;
    this.close = () => {
      this.closeCalled = true;
    };
    eventSources.push(this);
  }

  const window = {
    HackBankTextfill: {
      fillElement(element, options) {
        textfillCalls.push({element, options});
      },
    },
    location: {
      hash,
    },
  };
  const sandbox = {
    Date,
    EventSource,
    URLSearchParams,
    clearTimeout() {},
    console: {
      error() {},
      log() {},
    },
    document,
    fetch(url, options) {
      fetchCalls.push({url, options});
      return Promise.resolve();
    },
    setTimeout(callback, delay) {
      timers.push({callback, delay});
      return timers.length;
    },
    window,
  };

  loadScript(sandbox, "kassa-dom.js");
  loadScript(sandbox, "kassa-buttons.js");
  loadScript(sandbox, "kassa-stream.js");
  loadScript(sandbox, "kassa-app.js");
  documentListeners.DOMContentLoaded();

  return {
    body,
    documentListeners,
    elements,
    eventSources,
    fetchCalls,
    textfillCalls,
    timers,
  };
}

test("kassa app builds the startup layout and opens a session stream", () => {
  const {elements, eventSources, fetchCalls, textfillCalls} = loadKassaApp({
    hash: "#bar",
  });

  [
    "Firstscreen",
    "Secondscreen",
    "Receipt",
    "Totals",
    "Buttons",
    "Log",
    "Zoek",
    "LeftButtons",
    "MainButtons",
    "TopButtons",
    "Receipt2",
  ].forEach((id) => assert(elements[id], `${id} should exist`));

  assert.match(eventSources[0].url, /^stream\.php\?session=bar&t=/);
  assert.equal(fetchCalls[0].url, "post.php");
  assert.equal(String(fetchCalls[0].options.body), "topic=session%2Fbar%2Finput&msg=");
  assert.equal(elements.Zoek.placeholder, "Starting network communication");
  assert(textfillCalls.length > 0);
});

test("kassa app wires Enter in the search input to post input and clear it", () => {
  const {elements, fetchCalls} = loadKassaApp();
  const input = elements.Zoek;

  input.value = "abort";
  input.eventListeners.keydown.call(input, {
    which: 13,
  });

  assert.equal(fetchCalls.length, 2);
  assert.equal(String(fetchCalls[1].options.body), "topic=session%2Fmain%2Finput&msg=abort");
  assert.equal(input.value, "");
});

test("kassa app handles closed streams by scheduling one reconnect", () => {
  const {eventSources, timers} = loadKassaApp();

  eventSources[0].onmessage({data: "closed"});
  eventSources[0].onerror();

  assert.equal(eventSources[0].closeCalled, true);
  assert.equal(timers.length, 1);
  assert.equal(timers[0].delay, 1000);
});

test("kassa app removes accounts when retained account messages are cleared", () => {
  const {elements, eventSources} = loadKassaApp();
  const sendStreamMessage = (topic, msg) => {
    eventSources[0].onmessage({data: JSON.stringify([topic, msg])});
  };
  const accountButtonTexts = () => (
    findAll(elements.MainButtons, ".Buttontext").map((element) => element.textContent)
  );

  sendStreamMessage(
    "hack42bar/output/session/main/accounts/user1",
    '{"amount": 1, "lastupdate": "now"}',
  );
  sendStreamMessage(
    "hack42bar/output/session/main/accounts/stale",
    '{"amount": 2, "lastupdate": "now"}',
  );
  sendStreamMessage("hack42bar/output/session/main/members", '["user1", "stale"]');
  sendStreamMessage("hack42bar/output/session/main/buttons", '{"special": "accounts"}');

  assert.deepEqual(accountButtonTexts(), ["stale", "user1"]);

  sendStreamMessage("hack42bar/output/session/main/accounts/stale", "");
  sendStreamMessage("hack42bar/output/session/main/buttons", '{"special": "accounts"}');

  assert.deepEqual(accountButtonTexts(), ["user1"]);
});
