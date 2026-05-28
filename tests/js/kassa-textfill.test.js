const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadTextfill() {
  function jquery(selection) {
    return selection;
  }
  jquery.fn = {};

  const sandbox = {jQuery: jquery, window: {}};
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-textfill.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-textfill.js"});

  return {
    fillElement: sandbox.window.HackBankTextfill.fillElement,
    textfillPlugin: jquery.fn.textfill,
  };
}

function createElement(text) {
  const element = {
    currentFontSize: 0,
    parentElement: {
      offsetHeight: 50,
      offsetWidth: 50,
    },
    style: {},
    textContent: text,
    get offsetHeight() {
      return this.currentFontSize > 2 ? 120 : 10;
    },
    get offsetWidth() {
      return this.currentFontSize > 2 ? 120 : 10;
    },
  };
  Object.defineProperty(element.style, "fontSize", {
    get() {
      return this._fontSize;
    },
    set(value) {
      this._fontSize = value;
      element.currentFontSize = Number.parseFloat(value);
    },
  });

  return element;
}

test("textfill lowers font size until text fits and vertically centers it", () => {
  const {fillElement} = loadTextfill();
  const element = createElement("hello");

  const result = fillElement(element, {maxFontPixels: 5});

  assert.equal(result, element);
  assert.equal(element.style.fontSize, "1.4vh");
  assert.equal(element.style.top, "20px");
});

test("textfill reuses cached size for repeated text", () => {
  const {fillElement} = loadTextfill();
  const first = createElement("cached");
  const second = createElement("cached");

  fillElement(first, {maxFontPixels: 5});
  fillElement(second, {maxFontPixels: 5});

  assert.equal(second.style.fontSize, "1.4vh");
  assert.equal(second.style.top, "20px");
});

test("jQuery plugin remains available as a wrapper", () => {
  const {textfillPlugin} = loadTextfill();
  const element = createElement("wrapped");
  const selection = {
    filled: [],
    each(callback) {
      callback.call(element);
      this.filled.push(element);
      return this;
    },
  };

  const result = textfillPlugin.call(selection, {maxFontPixels: 5});

  assert.equal(result, selection);
  assert.equal(selection.filled[0], element);
  assert.equal(element.style.fontSize, "1.4vh");
});
