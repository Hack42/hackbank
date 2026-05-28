const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

test("main index loads split kassa scripts in dependency order", () => {
  const indexPath = path.join(__dirname, "../../www/index.html");
  const html = fs.readFileSync(indexPath, "utf8");
  const scripts = Array.from(html.matchAll(/<script src="([^"]+)"><\/script>/g)).map(
    (match) => match[1],
  );

  assert.deepEqual(scripts, [
    "kassa-textfill.js",
    "kassa-dom.js",
    "kassa-buttons.js",
    "kassa-app.js",
  ]);
  assert(!html.includes('src="all.js"'));
});
