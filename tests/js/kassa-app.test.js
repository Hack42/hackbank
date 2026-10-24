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
    showModal() {
      this.open = true;
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

function loadKassaApp({hash = "", pageCapacity = 25, accountCapacity = 42} = {}) {
  const elements = {};
  const documentListeners = {};
  const eventSources = [];
  const fetchCalls = [];
  const audioMountCalls = [];
  const soundSettingsMountCalls = [];
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
      return findFirst(body, `#${id}`) || elements[id] || null;
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
    HackBankAudio: {
      mount(container) {
        const mounted = {container, stopped: false};
        audioMountCalls.push(mounted);
        const panel=makeElement("section",register);
        panel.className="audio-controls";
        container.appendChild(panel);
        return {stop() { mounted.stopped = true; }};
      },
    },
    HackBankSoundSettings: {
      mount(container,options) {
        const mounted={container,options,stopped:false,updates:[],replies:[]};
        soundSettingsMountCalls.push(mounted);
        const panel=makeElement("section",register);
        panel.className="pos-sound-settings";
        container.appendChild(panel);
        return {stop(){mounted.stopped=true;},update(state){mounted.updates.push(state);},receive(reply){mounted.replies.push(reply);}};
      },
    },
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
    audioMountCalls,
    soundSettingsMountCalls,
    body,
    documentListeners,
    elements,
    eventSources,
    fetchCalls,
    textfillCalls,
    timers,
  };
}

test("deposit payment opens a modal with bank details and closes without confirming payment", () => {
  const {elements,eventSources,fetchCalls}=loadKassaApp();
  const send=(state) => eventSources[0].onmessage({data:JSON.stringify([
    'hack42bar/output/session/main/deposit_payment',JSON.stringify(state),
  ])});
  send({payments:[{name:'Hack42',iban:'NL43ABNA0136777643',amount:'25.50',reference:'test_user',qr:'data:image/png;base64,test'}]});
  const dialog=elements.DepositPayment;
  assert.equal(dialog.open,true);
  const image=findFirst(dialog,'.deposit-payment-qr');
  assert.equal(image.width,400);
  assert.match(image.alt,/test_user/);
  const values=findFirst(dialog,'.deposit-payment-details').children.map((child) => child.textContent);
  assert(values.includes('NL43ABNA0136777643'));
  assert(values.includes('EUR 25.50'));
  assert(values.includes('test_user'));
  findFirst(dialog,'.deposit-payment-close').eventListeners.click();
  assert.equal(dialog.parentElement,null);
  assert.equal(String(fetchCalls.at(-1).options.body),'topic=session%2Fmain%2Finput&msg=ok');
  send({});
  assert.equal(dialog.parentElement,null);
});

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
  assert.equal(findFirst(elements.LogoAbort,'.brand-name').textContent,'Lovelace Bar');
  assert.equal(findFirst(elements.LogoAbort,'.brand-caption').textContent,'Drinks @ Hack42');
  assert.equal(findFirst(elements.LeftButtons,'#abort').children[0].textContent,'Cancel');
  assert.equal(findFirst(elements.LeftButtons,'#otherusers').children[0].textContent,'Guests');
  assert.equal(findFirst(elements.Log.parentElement,'.activity-label').textContent,'HISTORY');
  assert.equal(findFirst(elements.Receipt2.parentElement,'.eyebrow'),null);
  assert.equal(findFirst(elements.Receipt2.parentElement,'.receipt-footer').children.at(-1).textContent,'Eat. Drink. Hack. Repeat.');
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

test("the entire Hack42 brand aborts once even with an unfinished command in the input", () => {
  const {elements, fetchCalls} = loadKassaApp({hash: "#bar"});
  elements.Zoek.value = "2* cola";
  elements.LogoAbort.eventListeners.click();

  assert.equal(elements.LogoAbort.tag, "button");
  assert.equal(elements.LogoAbort.type, "button");
  assert(findFirst(elements.LogoAbort, ".brand-name"));
  assert(findFirst(elements.LogoAbort, ".brand-caption"));
  assert.equal(fetchCalls.length, 2);
  assert.equal(String(fetchCalls[1].options.body), "topic=session%2Fbar%2Finput&msg=abort");
  assert.equal(elements.Zoek.value, "");
  assert.equal(elements.Zoek.focused, true);
});

test("custom sound menus include volume controls and omit the retired choices", () => {
  const {body, elements, eventSources, fetchCalls, audioMountCalls,soundSettingsMountCalls} = loadKassaApp();
  const names = ["abort", "ns", "deuron", "deuroff", "kassaon", "kassaoff", "killsounds", "groovesalad", "christmas", "blues", "quieter", "louder", "vergaderen", "vergaderenextreme", "throw", "yeet"];
  eventSources[0].onmessage({data: JSON.stringify([
    "hack42bar/output/session/main/buttons",
    JSON.stringify({special: "custom", custom: names.map((name) => ({text: name, display: name}))}),
  ])});
  assert.deepEqual(findAll(elements.MainButtons, ".Buttontext").map((el) => el.textContent), [
    "ns", "throw", "vergaderen", "vergaderenextreme", "yeet",
  ]);
  assert.equal(audioMountCalls.length, 1);
  assert.equal(audioMountCalls[0].container, findFirst(elements.MainButtons, ".sound-screen"));
  assert.deepEqual(findFirst(elements.MainButtons,".sound-screen").children.map((child)=>child.className),["section-title","sound-actions","audio-controls","pos-sound-settings"]);
  assert.equal(soundSettingsMountCalls.length,1);
  eventSources[0].onmessage({data:JSON.stringify(["hack42bar/output/settings/sounds",JSON.stringify({features:[]})])});
  eventSources[0].onmessage({data:JSON.stringify(["hack42bar/output/session/main/sound_settings",JSON.stringify({request:"sample-1",ok:true})])});
  assert.equal(soundSettingsMountCalls[0].updates.length,1);
  assert.equal(soundSettingsMountCalls[0].replies.length,1);
  assert(findFirst(elements.LeftButtons, "#sounds").classList.contains("activetop"));
  assert.equal(fetchCalls.length, 1);
  names.filter((name) => ["ns", "vergaderen", "vergaderenextreme", "throw", "yeet"].includes(name)).forEach((name) => {
    body.eventListeners.click({target: {closest(selector) {
      return selector === "div.normal" ? findFirst(elements.MainButtons, `#${name}`) : null;
    }}});
    assert.equal(String(fetchCalls.at(-1).options.body), `topic=session%2Fmain%2Finput&msg=${name}`);
    eventSources[0].onmessage({data: JSON.stringify(["hack42bar/output/session/main/buttons", "{}"])});
    assert(findFirst(elements.MainButtons, ".sound-screen"));
    assert.equal(audioMountCalls.length, 1);
    assert.equal(audioMountCalls[0].stopped, false);
  });
  body.eventListeners.click({target: {
    closest(selector) {
      return selector.startsWith("div.Knopje:not") ? findFirst(elements.LeftButtons, "#members") : null;
    },
  }});
  assert.equal(audioMountCalls[0].stopped, true);
  assert.equal(soundSettingsMountCalls[0].stopped,true);
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
  [18, 42].forEach((capacity) => {
    const {body, elements, eventSources, timers, fetchCalls} = loadKassaApp({accountCapacity: capacity});
    const names = Array.from({length: 191}, (_, i) => `user${String(i).padStart(3, "0")}`);
    const send = (topic, msg) => eventSources[0].onmessage({
      data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
    });
    names.forEach((name) => send(`accounts/${name}`, {amount: 12.50}));
    send("members", names.slice(0, 66));
    send("nonmembers", names.slice(66));
    send("buttons", {special: "accounts"});
    assert.equal(elements.TopButtons.children.at(-1).textContent, "Members Archive (0)");
    send("buttons", {special: "accountsamount"});

    assert.equal(findAll(elements.AccountList, ".account").length, 66);
    assert.equal(findAll(elements.Page1, ".account").length, capacity);
    assert.equal(findAll(elements.TopButtons, ".page").length, Math.ceil(66/capacity));
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
    assert.equal(elements.TopButtons.children.at(-1).textContent, "Guests Archive (0)");
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
  assert.equal(findAll(elements.Page1, ".account").length, 42);
  assert.equal(findAll(elements.Page2, ".account").length, 42);
  assert.equal(findAll(elements.Page3, ".account").length, 41);
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

test("the stitch account has no bundled character image and keeps its command", () => {
  const {body, elements, eventSources, fetchCalls} = loadKassaApp();
  const send = (topic, msg) => eventSources[0].onmessage({
    data: JSON.stringify([`hack42bar/output/session/main/${topic}`, JSON.stringify(msg)]),
  });
  send("accounts/stitch", {amount: 10});
  send("members", ["stitch"]);
  send("buttons", {special: "accounts"});
  const account = findFirst(elements.AccountList, "#stitch");
  assert.equal(account.children[0].textContent, "stitch");
  assert.equal(account.children.some((child) => child.tag === "img"), false);
  body.eventListeners.click({target: {
    closest(selector) {
      return selector === "div.normal" ? account : null;
    },
  }});
  assert.equal(fetchCalls.length, 2);
  assert.equal(String(fetchCalls[1].options.body), "topic=session%2Fmain%2Finput&msg=stitch");
});

test("Music and Home Assistant open their LAN frames and switch cleanly", () => {
  const {body, elements, fetchCalls} = loadKassaApp();
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
  assert.equal(elements.IRCwindow.children[0].src, "http://192.168.142.157:3000/");
  assert.equal(elements.IRCwindow.children[0].title, "Music");
  assert.equal(elements.IRCwindow.childElementCount, 1);
  clickMain("spacecon");
  assert.equal(elements.spacewindow.children[0].src, "http://hass.space.hack42.nl:8123/home/overview");
  assert.equal(elements.spacewindow.children[0].title, "Home Assistant");
  assert.equal(elements.spacewindow.childElementCount, 1);
  assert.equal(elements.IRCwindow.style.display, "none");
  clickMain("irc");
  assert.equal(elements.spacewindow.style.display, "none");
  assert.equal(elements.IRCwindow.childElementCount, 1);
  clickMain("members");
  assert.equal(elements.spacewindow.style.display, "none");
  assert.equal(elements.IRCwindow.style.display, "none");
  assert.equal(fetchCalls.length, 1);
});

test("profile membership actions send the existing command for the selected user", () => {
  const cases=[
    {members:["Jos"],profile:{is_member:true},label:"Promote to guest",command:"delmember Jos"},
    {members:[],profile:{is_member:false},label:"Promote to Member",command:"addmember Jos"},
    {members:["party"],profile:{is_member:true},label:"Promote to guest",command:"delmember Jos"},
    {members:["Jos"],profile:{is_member:false},label:"Promote to Member",command:"addmember Jos"},
    {members:["Jos"],profile:{},label:"Promote to guest",command:"delmember Jos"},
  ];
  cases.forEach((scenario) => {
    const {elements,eventSources,fetchCalls}=loadKassaApp();
    function send(topic,value) {
      eventSources[0].onmessage({data:JSON.stringify([`hack42bar/output/session/main/${topic}`,JSON.stringify(value)])});
    }
    send("members",scenario.members);
    send("infobox/account",{user:"Jos",amount:12,purchases:[],history_available:true,...scenario.profile});
    send("buttons",{special:"infobox"});
    const action=findFirst(elements.MainButtons,".membership-action");
    assert.equal(action.textContent,scenario.label);
    assert.equal(findAll(elements.MainButtons,".membership-action").length,1);
    assert.equal(findFirst(elements.MainButtons,".profile-actions").children.at(-1),action);
    action.eventListeners.click();
    assert.equal(fetchCalls.length,2);
    const params=new URLSearchParams(fetchCalls[1].options.body);
    assert.equal(params.get("topic"),"session/main/input");
    assert.equal(params.get("msg"),scenario.command);
  });
});

test("kassa app handles closed streams by scheduling one reconnect", () => {
  const {eventSources, timers} = loadKassaApp();

  eventSources[0].onmessage({data: "closed"});
  eventSources[0].onerror();

  assert.equal(eventSources[0].closeCalled, true);
  assert.equal(timers.length, 1);
  assert.equal(timers[0].delay, 1000);
});

test("late idle updates preserve Commands and selecting an action restores normal navigation", () => {
  const {body,elements,eventSources}=loadKassaApp();
  function send(topic,payload) {
    eventSources[0].onmessage({data:JSON.stringify([`hack42bar/output/session/main/${topic}`,JSON.stringify(payload)])});
  }
  send('accounts/Jos',{amount:10});
  send('members',['Jos']);
  send('commands',{deposit:'Deposit Money'});
  send('buttons',{});
  body.eventListeners.click({target:{closest(selector) {
    return selector.startsWith('div.Knopje:not') ? findFirst(elements.LeftButtons,'#commands') : null;
  }}});
  assert(findFirst(elements.MainButtons,'.command-sections'));
  send('buttons',{});
  assert(findFirst(elements.MainButtons,'.command-sections'));
  send('buttons',{special:'numbers'});
  assert(findFirst(elements.MainButtons,'.command-sections'));
  body.eventListeners.click({target:{closest(selector) {
    return selector === 'div.normal' ? findFirst(elements.MainButtons,'#deposit') : null;
  }}});
  send('buttons',{});
  assert(elements.MainButtons.children.some((element)=>element.id === 'AccountList'));
});

test("repeated user visits and checkout keep profile history alongside transaction controls", () => {
  const {elements,eventSources}=loadKassaApp();
  function send(topic,value) {
    eventSources[0].onmessage({data:JSON.stringify([`hack42bar/output/session/main/${topic}`,JSON.stringify(value)])});
  }
  const profile={user:"Jos",amount:12,purchases:[{count:1,description:"Cola",date:"2026-10-17_12:00:00",total:2}],history_available:true,undo_transaction:null};
  for(let visit=0;visit<3;visit++) {
    send("receipt",[]);
    send("buttons",{});
    send("infobox/account",profile);
    send("buttons",{special:"infobox"});
    assert(findFirst(elements.MainButtons,".user-profile"));
    assert.equal(findAll(elements.MainButtons,".purchase-row").length,1);
    ["ok","undo","restore","bon","kassala"].forEach((command)=>assert(findFirst(elements.TopButtons,`#${command}`)));
  }
  send("totals",[{user:"Jos",amount:-2}]);
  send("infobox/account",{...profile,amount:10,checkout:true});
  send("buttons",{special:"infobox"});
  assert(findFirst(elements.MainButtons,".infoboxes"));
  assert(findFirst(elements.MainButtons,".user-profile"));
  assert.equal(findAll(elements.MainButtons,".purchase-row").length,1);
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
