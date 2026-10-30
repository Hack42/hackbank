const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadTextfill() {
  const sandbox = {window: {
    getComputedStyle() {
      return {fontSize: "22px", paddingTop: "10px", paddingBottom: "10px"};
    },
  }};
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-textfill.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-textfill.js"});

  return {
    fillElement: sandbox.window.HackBankTextfill.fillElement,
  };
}

function createElement(text, width = 50) {
  const element = {
    currentFontSize: 0,
    parentElement: {
      clientHeight: 50,
      clientWidth: width,
    },
    style: {},
    textContent: text,
    get clientWidth() {
      return this.parentElement.clientWidth;
    },
    get scrollHeight() {
      return this.currentFontSize * 1.2;
    },
    get scrollWidth() {
      return this.currentFontSize * text.length / 2;
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

test("textfill fits text into the current tile using readable pixel sizes", () => {
  const {fillElement} = loadTextfill();
  const element = createElement("hello");

  const result = fillElement(element, {maxFontPixels: 22, minFontPixels: 12});

  assert.equal(result, element);
  assert.equal(element.style.fontSize, "20px");
  assert(element.scrollWidth <= element.clientWidth);
  assert(element.scrollHeight <= 30);
});

test("repeated labels are sized independently for differently sized tiles", () => {
  const {fillElement} = loadTextfill();
  const first = createElement("cached");
  const second = createElement("cached", 100);

  fillElement(first, {maxFontPixels: 22});
  fillElement(second, {maxFontPixels: 22});

  assert.equal(first.style.fontSize, "16.5px");
  assert.equal(second.style.fontSize, "22px");
});

test("textfill grows labels again after resizing and respects the minimum", () => {
  const {fillElement} = loadTextfill();
  const element = createElement("hello", 20);
  fillElement(element, {maxFontPixels: 22, minFontPixels: 12});
  assert.equal(element.style.fontSize, "12px");
  element.parentElement.clientWidth = 100;
  fillElement(element, {maxFontPixels: 22, minFontPixels: 12});
  assert.equal(element.style.fontSize, "22px");
});

test("textfill leaves hidden labels untouched until their tile is visible", () => {
  const {fillElement} = loadTextfill();
  const element = createElement("hidden", 0);
  element.style.fontSize = "18px";
  fillElement(element, {maxFontPixels: 22});
  assert.equal(element.style.fontSize, "18px");
});

test("button studio font sizes survive the standard label-fitting pass", () => {
  const {fillElement}=loadTextfill();
  const element=createElement("custom",20);
  element.style.fontSize="38px";
  element.closest=(selector)=>selector === ".magic-button" ? element.parentElement : null;
  fillElement(element,{maxFontPixels:22,minFontPixels:12});
  assert.equal(element.style.fontSize,"38px");
});
