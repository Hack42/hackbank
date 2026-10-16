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
      contains(className) {
        return element.className.split(/\s+/).includes(className);
      },
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

function loadKassaApp({hash = "", pageCapacity = 25, accountCapacity = 66} = {}) {
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
    getComputedStyle() {
      return {getPropertyValue: (name) => String(name === "--accounts-per-page" ? accountCapacity : pageCapacity)};
    },
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

test("the command Enter button submits once, clears the input and restores focus", () => {
  const {elements, fetchCalls} = loadKassaApp({hash: "#bar"});
  const input = elements.Zoek;
  input.value = "2* clubmate";
  elements.CommandEnter.eventListeners.click();

  assert.equal(elements.CommandEnter.tag, "button");
  assert.equal(elements.CommandEnter.type, "button");
  assert.equal(fetchCalls.length, 2);
  assert.equal(String(fetchCalls[1].options.body), "topic=session%2Fbar%2Finput&msg=2*+clubmate");
  assert.equal(input.value, "");
  assert.equal(input.focused, true);
});

test("pagination uses the grid capacity for large and smaller screens", () => {
  [25, 56].forEach((capacity) => {
    const {elements, eventSources} = loadKassaApp({pageCapacity: capacity});
    const names = Array.from({length: capacity + 1}, (_, i) => `member${String(i).padStart(3, "0")}`);
    const send = (topic, msg) => eventSources[0].onmessage({
      data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
    });
    send("buttons", {special: "custom", custom: names.map((name) => ({text: name, display: name}))});

    assert.equal(findAll(elements.Page1, ".Buttontext").length, capacity);
    assert.equal(findAll(elements.Page2, ".Buttontext").length, 1);
    assert.deepEqual(findAll(elements.MainButtons, ".Buttontext").map((el) => el.textContent), names);
  });
});

test("account pages use their own capacity and retain cash and amount controls", () => {
  [21, 66].forEach((capacity) => {
    const {body, elements, eventSources, timers, fetchCalls} = loadKassaApp({accountCapacity: capacity});
    const names = Array.from({length: 191}, (_, i) => `user${String(i).padStart(3, "0")}`);
    const send = (topic, msg) => eventSources[0].onmessage({
      data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
    });
    names.forEach((name) => send(`accounts/${name}`, {amount: 12.50}));
    send("members", names.slice(0, 66));
    send("nonmembers", names.slice(66));
    send("buttons", {special: "accountsamount"});

    assert.equal(findAll(elements.AccountList, ".account").length, 66);
    assert.equal(findAll(elements.Page1, ".account").length, capacity);
    assert.equal(findAll(elements.TopButtons, ".page").length, capacity === 66 ? 0 : 4);
    assert(findFirst(elements.TopButtons, "#cash"));
    assert(findFirst(elements.TopButtons, "#shownumbers"));

    elements.Zoek.value = "user";
    elements.Zoek.eventListeners.input();
    timers[timers.length - 1].callback();
    assert.equal(findAll(elements.AccountList, ".account").length, 191);
    assert.equal(findAll(elements.TopButtons, ".page").length, Math.ceil(191/capacity));
    assert(findFirst(elements.TopButtons, "#cash"));
    assert(findFirst(elements.TopButtons, "#shownumbers"));
    assert.equal(fetchCalls.length, 1);

    body.eventListeners.click({target: {
      closest(selector) {
        return selector.startsWith("div.Knopje:not") ? findFirst(elements.LeftButtons, "#otherusers") : null;
      },
    }});
    assert.deepEqual(findAll(elements.AccountList, ".Buttontext").map((el) => el.textContent), names.slice(66));
    assert.equal(findAll(elements.TopButtons, ".page").length, Math.ceil(125/capacity));
  });
});

test("backspacing a user filter expands results and clearing restores the selection", () => {
  const {elements, eventSources, timers, fetchCalls} = loadKassaApp();
  const send = (topic, msg) => eventSources[0].onmessage({
    data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
  });
  const members = ["Jan", "Johan", "Jos", "Josef", "stitch", "BugBlue"];
  [...members, "John", "Visitor"].forEach((name) => send(`accounts/${name}`, {amount: 12.50}));
  send("members", members);
  send("nonmembers", ["John", "Visitor"]);
  send("buttons", {special: "accountsamount"});
  function filter(value) {
    elements.Zoek.value = value;
    elements.Zoek.eventListeners.input();
    timers[timers.length - 1].callback();
    return findAll(elements.MainButtons, ".Buttontext").map((el) => el.textContent);
  }

  assert.deepEqual(filter("Jos"), ["Jos", "Josef"]);
  assert.deepEqual(filter("Jo"), ["Johan", "Jos", "Josef", "John"]);
  assert.deepEqual(filter("J"), ["Jan", "Johan", "Jos", "Josef", "John"]);
  assert.deepEqual(filter(""), ["BugBlue", "Jan", "Johan", "Jos", "Josef", "stitch"]);
  assert(findFirst(elements.TopButtons, "#cash"));
  assert(findFirst(elements.TopButtons, "#shownumbers"));
  assert.equal(fetchCalls.length, 1);
});

test("clearing a filter restores the original user tab after no matches", () => {
  const {body, elements, eventSources, timers, fetchCalls} = loadKassaApp();
  const send = (topic, msg) => eventSources[0].onmessage({
    data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
  });
  const names = Array.from({length: 125}, (_, i) => `visitor${String(i).padStart(3, "0")}`);
  names.forEach((name) => send(`accounts/${name}`, {amount: 0}));
  send("nonmembers", names);
  send("buttons", {});
  body.eventListeners.click({target: {
    closest(selector) {
      return selector.startsWith("div.Knopje:not") ? findFirst(elements.LeftButtons, "#otherusers") : null;
    },
  }});
  body.eventListeners.click({target: {
    closest(selector) {
      return selector === "div.page" ? findFirst(elements.TopButtons, "#2") : null;
    },
  }});
  assert.equal(elements.Page2.style.display, "");

  elements.Zoek.value = "no-matching-user";
  elements.Zoek.eventListeners.input();
  timers[timers.length - 1].callback();
  assert.equal(findAll(elements.MainButtons, ".Buttontext").length, 0);
  elements.Zoek.value = "";
  elements.Zoek.eventListeners.input();
  timers[timers.length - 1].callback();
  assert.equal(findAll(elements.Page1, ".account").length, 66);
  assert.equal(findAll(elements.Page2, ".account").length, 59);
  assert.equal(elements.Page1.style.display, "none");
  assert.equal(elements.Page2.style.display, "");
  assert.equal(findFirst(elements.TopButtons, "#2").classList.contains("currentpage"), true);
  assert.equal(fetchCalls.length, 1);
});

test("mixed search results retain the layout of the selected section", () => {
  const {body, elements, eventSources, timers} = loadKassaApp();
  const send = (topic, msg) => eventSources[0].onmessage({
    data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
  });
  send("accounts/Jos", {amount: 10});
  send("members", ["Jos"]);
  send("products/jos-soda", {description: "Jos Soda", group: "drinks", price: 1.5, aliases: []});
  send("buttons", {});
  function filter(value) {
    elements.Zoek.value = value;
    elements.Zoek.eventListeners.input();
    timers[timers.length - 1].callback();
  }
  filter("Jos");
  assert.equal(findAll(elements.MainButtons, ".Buttontext").length, 2);
  assert.equal(elements.Page1.classList.contains("account-list"), true);
  filter("");
  body.eventListeners.click({target: {
    closest(selector) {
      return selector.startsWith("div.Knopje:not") ? findFirst(elements.LeftButtons, "#products") : null;
    },
  }});
  filter("Jos");
  assert.equal(findAll(elements.MainButtons, ".Buttontext").length, 2);
  assert.equal(elements.Page1.classList.contains("account-list"), false);
  filter("");
  assert.deepEqual(findAll(elements.MainButtons, ".Buttontext").map((el) => el.textContent), ["drinks"]);
});

test("clearing a product filter restores the selected product group", () => {
  const {body, elements, eventSources, timers, fetchCalls} = loadKassaApp();
  const send = (topic, msg) => eventSources[0].onmessage({
    data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
  });
  ["cola", "coffee", "water", "whisky"].forEach((name) => send(`products/${name}`, {
    description: name, group: "drinks", price: 1.5, aliases: [],
  }));
  send("buttons", {special: "products"});
  body.eventListeners.click({target: {
    closest(selector) {
      return selector === "div.productgroups" ? findFirst(elements.MainButtons, "#drinks") : null;
    },
  }});
  function filter(value) {
    elements.Zoek.value = value;
    elements.Zoek.eventListeners.input();
    timers[timers.length - 1].callback();
    return findAll(elements.MainButtons, ".Buttontext").map((el) => el.textContent);
  }
  assert.deepEqual(filter("co"), ["cola", "coffee"]);
  assert.deepEqual(filter("col"), ["cola"]);
  assert.deepEqual(filter("c"), ["cola", "coffee"]);
  assert.deepEqual(filter(""), ["coffee", "cola", "water", "whisky"]);
  assert.equal(fetchCalls.length, 1);
});

test("the Stitch icon belongs to the user button and preserves its command", () => {
  const {body, elements, eventSources, fetchCalls} = loadKassaApp();
  const send = (topic, msg) => eventSources[0].onmessage({
    data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
  });
  send("accounts/stitch", {amount: 10});
  send("members", ["stitch"]);
  send("buttons", {special: "accounts"});
  const account = findFirst(elements.AccountList, "#stitch");
  assert.equal(account.children[0].tag, "img");
  assert.equal(account.children[0].src, "images/users/stitch.png");
  assert.equal(account.children[0].alt, "");
  body.eventListeners.click({target: {
    closest(selector) {
      return selector === "div.normal" ? account : null;
    },
  }});
  assert.equal(fetchCalls.length, 2);
  assert.equal(String(fetchCalls[1].options.body), "topic=session%2Fmain%2Finput&msg=stitch");
});

test("Music and Home Assistant open the requested frames and switch cleanly", () => {
  const {body, elements} = loadKassaApp();
  function clickMain(id) {
    body.eventListeners.click({
      target: {
        closest(selector) {
          return selector.startsWith("div.Knopje:not") ? findFirst(elements.LeftButtons, `#${id}`) : null;
        },
      },
    });
  }

  assert.equal(findFirst(elements.LeftButtons, "#irc").children[0].textContent, "Music");
  assert.equal(findFirst(elements.LeftButtons, "#spacecon").children[0].textContent, "Home Assistant");
  clickMain("irc");
  assert.equal(elements.IRCwindow.children[1].src, "https://www.youtube.com/");
  assert.equal(elements.IRCwindow.children[1].title, "YouTube");
  assert.equal(elements.IRCwindow.children[0].children[2].href, "https://www.youtube.com/");
  assert.equal(elements.IRCwindow.style.display, "");
  assert.equal(elements.spacewindow.style.display, "none");
  clickMain("spacecon");
  assert.equal(elements.spacewindow.children[1].src, "http://hass.space.hack42.nl:8123/home/overview");
  assert.equal(elements.spacewindow.children[1].title, "Home Assistant");
  assert.equal(findAll(elements.spacewindow, ".embed-note").length, 0);
  assert.equal(elements.IRCwindow.style.display, "none");
  clickMain("irc");
  assert.equal(elements.spacewindow.style.display, "none");
  assert.equal(elements.IRCwindow.childElementCount, 2);
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
