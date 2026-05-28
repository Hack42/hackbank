const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadButtonHelpers() {
  const sandbox = {
    window: {},
  };
  const script = fs.readFileSync(
    path.join(__dirname, "../../www/kassa-buttons.js"),
    "utf8",
  );

  vm.runInNewContext(script, sandbox, {filename: "kassa-buttons.js"});
  return sandbox.window.HackBankButtons;
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

test("rebuildProductIndexes resets groups and barcode-free products", () => {
  const helpers = loadButtonHelpers();
  const groups = {old: 9};
  const productsWithoutBarcode = {stale: {}};
  const products = {
    ClubMate: {
      aliases: ["mate", "12345678"],
      group: "drinks",
    },
    Tosti: {
      aliases: ["tosti"],
      group: "food",
    },
  };

  helpers.rebuildProductIndexes(products, groups, productsWithoutBarcode);

  assert.deepEqual(groups, {
    drinks: 1,
    food: 1,
  });
  assert.deepEqual(Object.keys(productsWithoutBarcode), ["Tosti"]);
});

test("accountsToButtons filters member types and marks negative balances", () => {
  const helpers = loadButtonHelpers();
  const accounts = {
    alice: {amount: -20},
    bob: {amount: -2},
    carol: {amount: 3.5},
  };

  assert.deepEqual(plain(helpers.accountsToButtons(accounts, ["alice"], ["bob"], "m")), [
    {
      display: "alice",
      fill: true,
      right: "-20.00",
      rightclass: "alice rood",
      text: "alice",
    },
  ]);
  assert.deepEqual(plain(helpers.accountsToButtons(accounts, ["alice"], ["bob"], "o")), [
    {
      display: "bob",
      fill: true,
      right: "-2.00",
      rightclass: "bob orange",
      text: "bob",
    },
  ]);
  assert.deepEqual(plain(helpers.accountsToButtons(accounts, ["alice"], ["bob"], "x")), [
    {
      display: "carol",
      fill: true,
      right: "3.50",
      rightclass: "carol",
      text: "carol",
    },
  ]);
});

test("product button helpers include prices, stock and aliases for app pages", () => {
  const helpers = loadButtonHelpers();
  const products = {
    Cola: {
      aliases: ["cola", "123"],
      description: "Cold cola",
      group: "drinks",
      price: 1.25,
    },
    Tosti: {
      aliases: ["tosti"],
      description: "Cheese tosti",
      group: "food",
      price: 2.5,
    },
  };
  const stock = {
    Cola: 4,
    Tosti: 0,
  };

  assert.deepEqual(plain(helpers.productGroupToButtons(products, stock, "drinks")), [
    {
      class: "Cola",
      display: "Cold cola",
      left: 4,
      leftclass: "orange",
      right: "1.25",
      rightclass: "green",
      text: "Cola",
    },
  ]);
  assert.deepEqual(helpers.allProductsToButtons(products, stock)[0].aliases, [
    "cola",
    "123",
  ]);
});
