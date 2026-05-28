const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadTextfillPlugin() {
  function jquery(selection) {
    return selection;
  }
  jquery.fn = {};

  const sandbox = {jQuery: jquery};
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-textfill.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-textfill.js"});

  return jquery.fn.textfill;
}

function createSelection(text) {
  const selection = {
    currentFontSize: 0,
    styles: {},
    css(name, value) {
      this.styles[name] = value;
      if(name === "font-size") {
        this.currentFontSize = Number.parseFloat(value);
      }
      return this;
    },
    height() {
      return this.currentFontSize > 2 ? 120 : 10;
    },
    parent() {
      return {
        height: () => 50,
        width: () => 50,
      };
    },
    text() {
      return text;
    },
    width() {
      return this.currentFontSize > 2 ? 120 : 10;
    },
  };

  return selection;
}

test("textfill lowers font size until text fits and vertically centers it", () => {
  const textfill = loadTextfillPlugin();
  const selection = createSelection("hello");

  const result = textfill.call(selection, {maxFontPixels: 5});

  assert.equal(result, selection);
  assert.equal(selection.styles["font-size"], "1.4vh");
  assert.equal(selection.styles.top, 20);
});

test("textfill reuses cached size for repeated text", () => {
  const textfill = loadTextfillPlugin();
  const first = createSelection("cached");
  const second = createSelection("cached");

  textfill.call(first, {maxFontPixels: 5});
  textfill.call(second, {maxFontPixels: 5});

  assert.equal(second.styles["font-size"], "1.4vh");
  assert.equal(second.styles.top, 20);
});
