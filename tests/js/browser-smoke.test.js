const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {spawnSync} = require("node:child_process");
const test = require("node:test");

function chromiumCommand() {
  const candidates = [
    process.env.CHROMIUM_BIN,
    "chromium",
    "chromium-browser",
    "google-chrome",
  ].filter(Boolean);

  return candidates.find((command) => {
    const result = spawnSync(command, ["--version"], {encoding: "utf8"});
    return result.status === 0;
  });
}

test("kassa index boots in a real browser", (t) => {
  const command = chromiumCommand();
  if(!command) {
    t.skip("Chromium is not available");
    return;
  }

  const indexPath = path.resolve(__dirname, "../../www/index.html");
  const result = spawnSync(command, [
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--dump-dom",
    `file://${indexPath}`,
  ], {
    encoding: "utf8",
    timeout: 10000,
  });

  if(result.status !== 0 && /crashpad|Operation not permitted/.test(result.stderr)) {
    t.skip("Chromium cannot run in this sandbox");
    return;
  }

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /id="Firstscreen"/);
  assert.match(result.stdout, /id="Zoek"/);
  assert.match(result.stdout, /id="LeftButtons"/);
});

test("the checked-in jQuery vendor file is gone", () => {
  assert.equal(fs.existsSync(path.resolve(__dirname, "../../www/jquery.min.js")), false);
});
