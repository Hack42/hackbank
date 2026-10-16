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
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "kassa-chromium-"));
  try {
    return spawnSync(command, [
      `--user-data-dir=${profile}`,
      "--no-first-run",
      "--no-default-browser-check",
      "--headless",
      "--window-size=1920,1080",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--allow-file-access-from-files",
      "--dump-dom",
      "--virtual-time-budget=3000",
      url,
    ], {
      encoding: "utf8",
      timeout: 40000,
    });
  } finally {
    fs.rmSync(profile, {recursive: true, force: true});
  }
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
    <link rel="stylesheet" href="file://${path.resolve(__dirname, "../../www/stom.css")}">
    <script>
      window.__fetchCalls = [];
      window.fetch = function(url, options) {
        window.__fetchCalls.push({url: url, body: String(options.body)});
        return Promise.resolve({ok: true});
      };
      window.EventSource = function(url) {
        this.url = url;
        this.close = function() {};
        window.__eventSource = this;
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

  assert.ifError(result.error);
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
          input.value = "clubmate";
          document.getElementById("CommandEnter").click();

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

  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  const match = result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
  assert(match, result.stdout);
  const data = JSON.parse(match[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&"));

  assert.match(data.eventSourceUrl, /^stream\.php\?session=main&t=/);
  assert.equal(data.hasButtons, true);
  assert.equal(data.activeElement, "Zoek");
  assert.deepEqual(data.fetchCalls.map((call) => call.body), [
    "topic=session%2Fmain%2Finput&msg=",
    "topic=session%2Fmain%2Finput&msg=abort",
    "topic=session%2Fmain%2Finput&msg=bon",
    "topic=session%2Fmain%2Finput&msg=clubmate",
  ]);
});

test("filtering keeps account cell sizes and backspace restores the previous view", (t) => {
  const command = chromiumCommand();
  if(!command) {
    t.skip("Chromium is not available");
    return;
  }
  const fixturePath = writeKassaFixture(`
    window.addEventListener("DOMContentLoaded", function() {
      setTimeout(function() {
        function send(topic, payload) {
          window.__eventSource.onmessage({data: JSON.stringify([
            'hack42bar/output/session/main/' + topic, JSON.stringify(payload)
          ])});
        }
        var members = ['BugBlue', 'Jan', 'Johan', 'Jos', 'Josef', 'stitch'];
        members.concat(['John']).forEach(function(name) { send('accounts/' + name, {amount: 12.5}); });
        send('members', members);
        send('nonmembers', ['John']);
        send('buttons', {});
        var before = document.querySelector('#AccountList #Jos').getBoundingClientRect();
        var input = document.getElementById('Zoek');
        var counts = [];
        function filter(value) {
          input.value = value;
          input.dispatchEvent(new Event('input', {bubbles: true}));
        }
        filter('Jos');
        setTimeout(function() {
          counts.push(document.querySelectorAll('#AccountList .account').length);
          var after = document.querySelector('#AccountList #Jos').getBoundingClientRect();
          filter('Jo');
          setTimeout(function() {
            counts.push(document.querySelectorAll('#AccountList .account').length);
            filter('J');
            setTimeout(function() {
              counts.push(document.querySelectorAll('#AccountList .account').length);
              filter('');
              setTimeout(function() {
                counts.push(document.querySelectorAll('#AccountList .account').length);
                var output = document.createElement('pre');
                output.id = 'smoke-result';
                output.textContent = JSON.stringify({
                  beforeWidth: before.width, afterWidth: after.width,
                  beforeHeight: before.height, afterHeight: after.height,
                  counts: counts, fetchCount: window.__fetchCalls.length,
                  hasCash: !!document.querySelector('#TopButtons #cash')
                });
                document.body.appendChild(output);
              }, 250);
            }, 250);
          }, 250);
        }, 250);
      }, 0);
    });
  `);
  const result = runChromium(command, `file://${fixturePath}`);
  fs.unlinkSync(fixturePath);
  if(skipIfChromiumSandboxed(t, result)) return;
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  const match = result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
  assert(match, result.stdout);
  const data = JSON.parse(match[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&"));
  assert(data.beforeWidth > 0);
  assert(Math.abs(data.beforeWidth - data.afterWidth) < 0.5, JSON.stringify(data));
  assert(Math.abs(data.beforeHeight - data.afterHeight) < 0.5, JSON.stringify(data));
  assert.deepEqual(data.counts, [2, 4, 5, 6]);
  assert.equal(data.fetchCount, 1);
  assert.equal(data.hasCash, true);
});

test("the checked-in jQuery vendor file is gone", () => {
  assert.equal(fs.existsSync(path.resolve(__dirname, "../../www/jquery.min.js")), false);
});
