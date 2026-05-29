const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
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

function runChromium(command, url) {
  return spawnSync(command, [
    "--headless",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--allow-file-access-from-files",
    "--dump-dom",
    "--virtual-time-budget=3000",
    url,
  ], {
    encoding: "utf8",
    timeout: 20000,
  });
}

function skipIfChromiumSandboxed(t, result) {
  if(result.status !== 0 && /crashpad|Operation not permitted/.test(result.stderr)) {
    t.skip("Chromium cannot run in this sandbox");
    return true;
  }
  return false;
}

function scriptTag(scriptName) {
  return `<script src="file://${path.resolve(__dirname, "../../www", scriptName)}"></script>`;
}

function writeKassaFixture(bodyScript) {
  const fixturePath = path.join(os.tmpdir(), `kassa-browser-smoke-${process.pid}-${Date.now()}.html`);
  fs.writeFileSync(fixturePath, `<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <script>
      window.__fetchCalls = [];
      window.fetch = function(url, options) {
        window.__fetchCalls.push({url: url, body: String(options.body)});
        return Promise.resolve({ok: true});
      };
      window.EventSource = function(url) {
        this.url = url;
        this.close = function() {};
        window.__eventSourceUrl = url;
      };
    </script>
    ${scriptTag("kassa-textfill.js")}
    ${scriptTag("kassa-dom.js")}
    ${scriptTag("kassa-buttons.js")}
    ${scriptTag("kassa-stream.js")}
    ${scriptTag("kassa-app.js")}
    <script>${bodyScript}</script>
  </head>
  <body id="body"></body>
</html>`);
  return fixturePath;
}

test("kassa index boots in a real browser", (t) => {
  const command = chromiumCommand();
  if(!command) {
    t.skip("Chromium is not available");
    return;
  }

  const fixturePath = writeKassaFixture(`
    window.addEventListener("DOMContentLoaded", function() {
      setTimeout(function() {
        var output = document.createElement("pre");
        output.id = "smoke-result";
        output.textContent = JSON.stringify({
          hasFirstscreen: !!document.getElementById("Firstscreen"),
          hasZoek: !!document.getElementById("Zoek"),
          hasLeftButtons: !!document.getElementById("LeftButtons"),
          eventSourceUrl: window.__eventSourceUrl
        });
        document.body.appendChild(output);
      }, 0);
    });
  `);
  const result = runChromium(command, `file://${fixturePath}`);
  fs.unlinkSync(fixturePath);
  if(skipIfChromiumSandboxed(t, result)) return;

  assert.equal(result.status, 0, result.stderr);
  const match = result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
  assert(match, result.stdout);
  const data = JSON.parse(match[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&"));

  assert.equal(data.hasFirstscreen, true);
  assert.equal(data.hasZoek, true);
  assert.equal(data.hasLeftButtons, true);
  assert.match(data.eventSourceUrl, /^stream\.php\?session=main&t=/);
});

test("kassa frontend posts keyboard and button input in a browser", (t) => {
  const command = chromiumCommand();
  if(!command) {
    t.skip("Chromium is not available");
    return;
  }

  const fixturePath = writeKassaFixture(`
      window.addEventListener("DOMContentLoaded", function() {
        setTimeout(function() {
          var input = document.getElementById("Zoek");
          input.value = "abort";
          var keydown = new Event("keydown", {bubbles: true});
          Object.defineProperty(keydown, "which", {value: 13});
          input.dispatchEvent(keydown);
          document.getElementById("bon").click();

          var output = document.createElement("pre");
          output.id = "smoke-result";
          output.textContent = JSON.stringify({
            fetchCalls: window.__fetchCalls,
            eventSourceUrl: window.__eventSourceUrl,
            activeElement: document.activeElement && document.activeElement.id,
            hasButtons: !!document.getElementById("Buttons")
          });
          document.body.appendChild(output);
        }, 0);
      });
  `);

  const result = runChromium(command, `file://${fixturePath}`);
  fs.unlinkSync(fixturePath);
  if(skipIfChromiumSandboxed(t, result)) return;

  assert.equal(result.status, 0, result.stderr);
  const match = result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
  assert(match, result.stdout);
  const data = JSON.parse(match[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&"));

  assert.match(data.eventSourceUrl, /^stream\.php\?session=main&t=/);
  assert.equal(data.hasButtons, true);
  assert.deepEqual(data.fetchCalls.map((call) => call.body), [
    "topic=session%2Fmain%2Finput&msg=",
    "topic=session%2Fmain%2Finput&msg=abort",
    "topic=session%2Fmain%2Finput&msg=bon",
  ]);
});

test("the checked-in jQuery vendor file is gone", () => {
  assert.equal(fs.existsSync(path.resolve(__dirname, "../../www/jquery.min.js")), false);
});
