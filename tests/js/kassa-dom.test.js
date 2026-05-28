const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function fakeJQueryFactory(selectorMap) {
  function createElement(tagWithBrackets, attrs) {
    return {
      attrs: attrs || {},
      children: [],
      tag: tagWithBrackets.replace(/[<>]/g, ""),
      append(child) {
        this.children.push(child);
        return this;
      },
    };
  }

  return function jquery(selector, attrs) {
    if(typeof selector === "object") {
      return selector;
    }
    if(typeof selector === "string" && selector.startsWith("<")) {
      return createElement(selector, attrs);
    }
    const elements = selectorMap[selector] || [];
    return {
      each(callback) {
        elements.forEach((element, index) => callback.call(element, index, element));
        return this;
      },
    };
  };
}

function loadDomHelpers({elements = {}, selectorMap = {}} = {}) {
  const document = {
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
    jQuery: fakeJQueryFactory(selectorMap),
    window: {},
  };
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-dom.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-dom.js"});

  return sandbox.window.HackBankDom;
}

test("DOM helpers show, hide, clear and scroll existing elements", () => {
  const panel = {style: {display: "block"}};
  const log = {scrollHeight: 42, scrollTop: 0};
  const message = {textContent: "old"};
  const helpers = loadDomHelpers({
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
  const helpers = loadDomHelpers({elements: {Zoek: input}});

  assert.equal(helpers.searchInput(), input);
  assert.equal(helpers.searchValue(), "ab");

  helpers.setSearchValue("cd");
  helpers.appendSearchValue("ef");

  assert.equal(input.value, "cdef");
});

test("button helpers build jQuery elements and fill visible text", () => {
  const label = {
    textfillOptions: null,
    textfill(options) {
      this.textfillOptions = options;
    },
  };
  const helpers = loadDomHelpers({selectorMap: {".Buttontext:visible": [label]}});

  const button = helpers.buttonElement("Knopje normal", "ok", "OK");
  assert.equal(button.tag, "div");
  assert.equal(button.attrs.class, "Knopje normal");
  assert.equal(button.attrs.id, "ok");
  assert.equal(button.children[0].tag, "span");
  assert.equal(button.children[0].attrs.class, "Knopjetext");
  assert.equal(button.children[0].attrs.text, "OK");

  helpers.fillVisibleText(".Buttontext:visible");
  assert.equal(label.textfillOptions.maxFontPixels, 5);
});
