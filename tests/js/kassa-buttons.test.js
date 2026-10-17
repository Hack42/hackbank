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
      class: "account account-alice",
      display: "alice",
      fill: true,
      right: "-20.00",
      rightclass: "alice rood",
      text: "alice",
    },
  ]);
  assert.deepEqual(plain(helpers.accountsToButtons(accounts, ["alice"], ["bob"], "o")), [
    {
      class: "account account-bob",
      display: "bob",
      fill: true,
      right: "-2.00",
      rightclass: "bob orange",
      text: "bob",
    },
  ]);
  assert.deepEqual(plain(helpers.accountsToButtons(accounts, ["alice"], ["bob"], "x")), [
    {
      class: "account account-carol",
      display: "carol",
      fill: true,
      right: "3.50",
      rightclass: "carol",
      text: "carol",
    },
  ]);
});

test("account button classes are safe for CSS selectors", () => {
  const helpers = loadButtonHelpers();
  const accounts = {
    "alice@example": {amount: 1},
  };

  assert.equal(helpers.cssSafeClassName("alice@example"), "alice-example");
  assert.deepEqual(plain(helpers.accountsToButtons(
    accounts,
    ["alice@example"],
    [],
    "m",
  )), [
    {
      class: "account account-alice-example",
      display: "alice@example",
      fill: true,
      right: "1.00",
      rightclass: "alice@example",
      text: "alice@example",
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

test("retired sound controls are absent from command menus and search candidates", () => {
  const helpers = loadButtonHelpers();
  const commands = {
    deuroff: "Deur off", deuron: "Deur on", groovesalad: "Groove Salad",
    blues: "Jazz Radio Blues", killsounds: "Kill Music", louder: "Louder", quieter: "Quieter",
    sounds: "All sound commands", ns: "Ding Dong", kassaon: "Kassa on", kassaoff: "Kassa off",
    christmas: "christmas", vergaderen: "Vergaderen!",
  };
  const visible = helpers.commandsToButtons(commands);
  assert.deepEqual(plain(visible.map((button) => button.text)), [
    "christmas", "ns", "sounds", "vergaderen",
  ]);
  const matches = [];
  helpers.addMatchingButtons(matches, visible, "loud");
  assert.deepEqual(matches, []);
  assert.equal(commands.louder, "Louder");
  assert.equal(helpers.productGroupToButtons({
    blues: {description: "Blues beer", price: 2.5, group: "drinks"},
  }, {}, "drinks")[0].text, "blues");
});

test("account themes match names without changing account commands or balances", () => {
  const helpers = loadButtonHelpers();
  const accounts = {Jos: {amount: -20}, nino: {amount: 1}, Anus: {amount: 2}, Anux: {amount: 3}};
  const buttons = plain(helpers.accountsToButtons(accounts, Object.keys(accounts), [], "m"));
  const byName = Object.fromEntries(buttons.map((button) => [button.text, button]));
  assert.match(byName.Jos.class, /account-theme-lockpicker/);
  assert.match(byName.nino.class, /account-theme-ukraine/);
  assert.match(byName.Anus.class, /account-theme-plasma/);
  assert.doesNotMatch(byName.Anux.class, /account-theme/);
  assert.equal(byName.Jos.right, "-20.00");
  assert.equal(byName.Jos.rightclass, "Jos rood");
  assert.deepEqual(Object.keys(byName).sort(), ["Anus", "Anux", "Jos", "nino"]);
});

test("command sections preserve action ids, ordering and access through Manage members", () => {
  const helpers=loadButtonHelpers();
  const commands={abort:'Abort everything',addproduct:'Add new product',setprice:'Change the price of a product',
    addmember:'Add user to members',members:'Manage members',partymodeon:'Enable party mode',partymodeoff:'Disable party mode',
    market:'Market: Products',changemarket:'Market: Change Price',addmarket:'Market: Add alias'};
  const sections=plain(helpers.commandSections(commands));
  assert.deepEqual(sections.map((section)=>section.name),['Products','Users','Sales','Wholesale','Market','Misc']);
  assert.deepEqual(sections[0].buttons.map((button)=>[button.text,button.display]),[['addproduct','Add new'],['setprice','Change price']]);
  assert.deepEqual(sections[1].buttons.map((button)=>button.text),['members']);
  assert.deepEqual(sections[4].buttons.map((button)=>button.display),['Products','Pricing','Aliases']);
  assert.equal(commands.addmember,'Add user to members');
});

test("archives use purchase dates, keep unknown activity visible, and preserve selection commands", () => {
  const helpers=loadButtonHelpers();
  const accounts={Jos:{amount:10,lastupdate:'2026-10-16'},old:{amount:-2,lastupdate:'2020-01-01'},newuser:{amount:0,lastupdate:'2026-10-16'}};
  const candidates=helpers.accountsToButtons(accounts,Object.keys(accounts),[],'m');
  const activity={available:true,cutoff:'2025-10-17',last_purchase:{Jos:'2024-01-01'}};
  const split=plain(helpers.splitAccounts(candidates,accounts,activity));
  assert.deepEqual(split.active.map((button)=>button.text),['newuser']);
  assert.deepEqual(split.archive.map((button)=>button.text),['Jos','old']);
  assert(split.archive.every((button)=>button.class.includes('archived-account')));
  assert.equal(helpers.splitAccounts(candidates,accounts,{available:false}).active.length,3);
});
