const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function fakeElement(tag) {
  return {
    children: [],
    className: "",
    id: "",
    tag,
    textContent: "",
    appendChild(child) {
      this.children.push(child);
      return child;
    },
  };
}

function loadDomHelpers({elements = {}, selectorMap = {}} = {}) {
  const textfillCalls = [];
  const document = {
    createElement(tag) {
      return fakeElement(tag);
    },
    getElementById(id) {
      return elements[id] || null;
    },
    querySelector(selector) {
      return elements[selector] || null;
    },
    querySelectorAll(selector) {
      return selectorMap[selector] || [];
    },
  };
  const sandbox = {
    document,
    window: {
      HackBankTextfill: {
        fillElement(element, options) {
          textfillCalls.push({element, options});
        },
      },
    },
  };
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-dom.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-dom.js"});

  return {
    helpers: sandbox.window.HackBankDom,
    textfillCalls,
  };
}

test("DOM helpers show, hide, clear and scroll existing elements", () => {
  const panel = {style: {display: "block"}};
  const log = {scrollHeight: 42, scrollTop: 0};
  const message = {textContent: "old"};
  const {helpers} = loadDomHelpers({
    elements: {
      "#panel": panel,
      "#log": log,
      "#message": message,
    },
  });

  helpers.hideElement("#panel");
  assert.equal(panel.style.display, "none");

  helpers.showElement("#panel");
  assert.equal(panel.style.display, "");

  helpers.clearElement("#message");
  assert.equal(message.textContent, "");

  helpers.scrollToBottom("#log");
  assert.equal(log.scrollTop, 42);
});

test("search helpers read, set and append the Zoek input", () => {
  const input = {value: "ab"};
  const {helpers} = loadDomHelpers({elements: {Zoek: input}});

  assert.equal(helpers.searchInput(), input);
  assert.equal(helpers.searchValue(), "ab");

  helpers.setSearchValue("cd");
  helpers.appendSearchValue("ef");

  assert.equal(input.value, "cdef");
});

test("button helpers build native elements and fill visible text", () => {
  const label = {};
  const {helpers, textfillCalls} = loadDomHelpers({
    selectorMap: {".Buttontext": [label]},
  });

  const button = helpers.buttonElement("Knopje normal", "ok", "OK");
  assert.equal(button.tag, "div");
  assert.equal(button.className, "Knopje normal");
  assert.equal(button.id, "ok");
  assert.equal(button.children[0].tag, "span");
  assert.equal(button.children[0].className, "Knopjetext");
  assert.equal(button.children[0].textContent, "OK");

  helpers.fillVisibleText(".Buttontext:visible");
  assert.equal(textfillCalls.length, 1);
  assert.equal(textfillCalls[0].element, label);
  assert.equal(textfillCalls[0].options.maxFontPixels, 5);
});

test("allElements supports legacy visible selectors", () => {
  const visible = {offsetWidth: 10, offsetHeight: 0};
  const hidden = {offsetWidth: 0, offsetHeight: 0, getClientRects: () => []};
  const rectVisible = {offsetWidth: 0, offsetHeight: 0, getClientRects: () => [1]};
  const {helpers} = loadDomHelpers({
    selectorMap: {".Buttontext": [visible, hidden, rectVisible]},
  });

  const result = helpers.allElements(".Buttontext:visible");
  assert.equal(result.length, 2);
  assert.equal(result[0], visible);
  assert.equal(result[1], rectVisible);
});

test("topButton builds a native pagination button", () => {
  const {helpers} = loadDomHelpers();
  const button = helpers.topButton("normal cash", "cash", "cash");

  assert.equal(button.className, "Knopje Button normal cash");
  assert.equal(button.id, "cash");
  assert.equal(button.children[0].className, "Paginatext");
  assert.equal(button.children[0].textContent, "cash");
});
