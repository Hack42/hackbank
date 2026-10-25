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

function runChromium(command, url, extraArgs=[]) {
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
      ...extraArgs,
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

for(const disabled of [false,true]) {
  test(disabled ? 'shader buttons keep their gradient and labels when WebGL is unavailable' : 'ambient presets render distinct scenes through one shared WebGL context', (t)=>{
    const command=chromiumCommand();
    if(!command) { t.skip('Chromium is not available'); return; }
    const url='file://'+path.resolve(__dirname,'../fixtures/button-shaders.html')+'?report'+(disabled ? '&disabled' : '');
    const result=runChromium(command,url,['--enable-unsafe-swiftshader','--use-angle=swiftshader']);
    if(skipIfChromiumSandboxed(t,result)) return;
    assert.ifError(result.error);
    assert.equal(result.status,0,result.stderr);
    const match=result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
    assert(match,result.stdout);
    const data=JSON.parse(match[1].replaceAll('&quot;','"').replaceAll('&amp;','&'));
    assert.equal(data.contexts,1);
    assert.equal(data.sceneCount,9);
    assert.equal(data.canvases,22);
    assert.equal(data.labels,22);
    assert.equal(data.fallback,true);
    if(disabled) {
      assert.equal(data.status,'unavailable');
      assert(data.samples.every(sample=>sample.state==='fallback'));
    } else {
      assert.equal(data.status,'ready',result.stderr);
      assert(data.samples.every(sample=>sample.state==='animated' && sample.bright>1000 && sample.width<=320 && sample.height<=128),JSON.stringify(data));
      assert.equal(new Set(data.samples.map(sample=>sample.hash)).size,9);
      assert.equal(new Set(data.seedSamples.slice(0,12).map(sample=>sample.hash)).size,12);
      assert.equal(data.seedSamples.at(-1).hash,data.samples[0].hash);
      assert.equal(data.preserved,true);
    }
  });
}

function writeKassaFixture(bodyScript) {
  const fixturePath = path.join(os.tmpdir(), `kassa-browser-smoke-${process.pid}-${Date.now()}.html`);
  fs.writeFileSync(fixturePath, `<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="file://${path.resolve(__dirname, "../../www/stom.css")}">
    <link rel="stylesheet" href="file://${path.resolve(__dirname, "../../www/kassa-button-studio.css")}">
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
    ${scriptTag("kassa-audio.js")}
    ${scriptTag("kassa-sound-settings.js")}
    ${scriptTag("shaders/wonderful.js")}
    ${scriptTag("shaders/heartfelt.js")}
    ${scriptTag("shaders/star-nest.js")}
    ${scriptTag("shaders/clouds.js")}
    ${scriptTag("shaders/universe-within.js")}
    ${scriptTag("kassa-button-shaders.js")}
    ${scriptTag("kassa-button-styles.js")}
    ${scriptTag("kassa-button-studio.js")}
    ${scriptTag("kassa-confetti.js")}
    ${scriptTag("kassa-preferences.js")}
    ${scriptTag("kassa-idle-focus.js")}
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
  assert.equal(data.beforeHeight, 84);
  assert(Math.abs(data.beforeWidth - data.afterWidth) < 0.5, JSON.stringify(data));
  assert(Math.abs(data.beforeHeight - data.afterHeight) < 0.5, JSON.stringify(data));
  assert.deepEqual(data.counts, [2, 4, 5, 6]);
  assert.equal(data.fetchCount, 1);
  assert.equal(data.hasCash, true);
});

test('sunglasses quiet both account lists without sending a command or changing saved styles', (t)=>{
  const command=chromiumCommand();
  if(!command){t.skip('Chromium is not available');return;}
  const fixture=writeKassaFixture(`
    window.addEventListener('DOMContentLoaded',function(){setTimeout(function(){
      var result={};
      try{
        function send(topic,value){window.__eventSource.onmessage({data:JSON.stringify(['hack42bar/output/session/main/'+topic,JSON.stringify(value)])});}
        send('accounts/BugBlue',{amount:-20});send('accounts/stitch',{amount:42});send('accounts/guest',{amount:1});
        send('members',['BugBlue','stitch']);send('nonmembers',['guest']);send('buttons',{});
        var account=document.querySelector('#AccountList #BugBlue'), before=account.getBoundingClientRect();
        var original=account.innerHTML, input=document.getElementById('Zoek');input.value='unfinished command';
        var posts=window.__fetchCalls.length;
        var toggle=document.querySelector('.button-styles-toggle');
        result.archiveThenToggle=toggle.previousElementSibling.classList.contains('archive');
        toggle.click();
        result.off=toggle.getAttribute('aria-pressed')==='false' && document.body.classList.contains('button-styles-off');
        result.plain=getComputedStyle(account.querySelector('.magic-layer')).display==='none' && getComputedStyle(account.querySelector('.Buttontext')).fontSize==='17px';
        result.draftKept=input.value==='unfinished command';
        result.focus=input===document.activeElement;
        var after=account.getBoundingClientRect();
        result.sameSize=before.width===after.width && before.height===after.height;
        result.balance=account.querySelector('.extra').textContent==='-20.00' && account.querySelector('.extra').classList.contains('rood');
        document.body.classList.add('dark-mode');
        result.darkInk=getComputedStyle(account.querySelector('.Buttontext')).color==='rgb(225, 234, 243)';
        var preview=HackBankButtonStyles.preview('preview',42,HackBankButtonStyles.preset(0));
        document.body.appendChild(preview);
        result.studioShowsDesign=getComputedStyle(preview.querySelector('.magic-layer')).display!=='none';preview.remove();
        document.getElementById('otherusers').click();
        toggle=document.querySelector('.button-styles-toggle');
        result.guestsOff=toggle.getAttribute('aria-pressed')==='false' && toggle.previousElementSibling.classList.contains('archive');
        document.getElementById('members').click();
        document.querySelector('.button-styles-toggle').click();
        result.restored=!document.body.classList.contains('button-styles-off') && document.querySelector('#AccountList #BugBlue').innerHTML===original;
        result.noCommand=window.__fetchCalls.length===posts;
      }catch(error){result.error=String(error.stack);}
      var output=document.createElement('pre');output.id='smoke-result';output.textContent=JSON.stringify(result);document.body.appendChild(output);
    },0);});
  `);
  const result=runChromium(command,'file://'+fixture);
  fs.unlinkSync(fixture);
  if(skipIfChromiumSandboxed(t,result))return;
  assert.ifError(result.error);assert.equal(result.status,0,result.stderr);
  const match=result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);assert(match,result.stdout);
  const data=JSON.parse(match[1].replaceAll('&quot;','"').replaceAll('&amp;','&'));
  assert.equal(data.error,undefined,JSON.stringify(data));
  Object.keys(data).forEach(key=>assert.equal(data[key],true,key+': '+JSON.stringify(data)));
});

test("button studio previews locally, saves one user's design and cancels without a POS command", (t) => {
  const command=chromiumCommand();
  if(!command) { t.skip("Chromium is not available"); return; }
  const fixturePath=writeKassaFixture(`
    window.addEventListener('DOMContentLoaded',function() {
      setTimeout(async function() {
        var result={};
        function send(topic,payload) {
          window.__eventSource.onmessage({data:JSON.stringify(['hack42bar/output/session/main/'+topic,JSON.stringify(payload)])});
        }
        function wait(ms) { return new Promise(function(resolve) { setTimeout(resolve,ms); }); }
        var saved=null, requests=[];
        window.fetch=function(url,options) {
          var params=new URLSearchParams(options.body);
          var topic=params.get('topic'); requests.push(topic);
          if(topic.endsWith('/button_studio')) {
            var change=JSON.parse(params.get('msg'));
            if(change.theme) saved=change.theme;
            setTimeout(function() { send('button_studio',{request:change.request,ok:true,user:change.user,theme:saved}); },10);
          }
          return Promise.resolve({ok:true,json:function() { return Promise.resolve({done:1}); }});
        };
        try {
          send('accounts/stitch',{amount:10}); send('accounts/BugBlue',{amount:-20});
          send('members',['stitch','BugBlue']); send('buttons',{});
          var other=document.querySelector('#BugBlue').innerHTML;
          send('infobox/account',{user:'stitch',amount:10,purchases:[],history_available:true,undo_transaction:null});
          send('buttons',{special:'infobox'});
          document.querySelector('.studio-launch').click(); await wait(30);
          var dialog=document.querySelector('.button-studio');
          var current=dialog.querySelector('.studio-current').innerHTML;
          var presets=Array.from(dialog.querySelectorAll('.studio-presets .studio-preset'));
          result.allPresetsTogether=presets.length===15 && !dialog.querySelector('.studio-ambient');
          presets[6].click();
          var previewCanvas=dialog.querySelector('.studio-new .magic-shader-canvas');
          presets[7].click(); presets[8].click(); presets[9].click();
          result.previewCanvasPreserved=previewCanvas===dialog.querySelector('.studio-new .magic-shader-canvas');
          result.presetCanvasesPreserved=presets.every(function(tile,index) { return tile===dialog.querySelectorAll('.studio-presets .studio-preset')[index]; });
          dialog.querySelectorAll('.studio-preset')[0].click();
          var style=dialog.querySelector('select'); style.value='plasma'; style.dispatchEvent(new Event('change'));
          document.querySelector('#Studio-tab-Lettering').click();
          var size=Array.from(dialog.querySelectorAll('input')).find(function(el) { return el.getAttribute('aria-label')==='Font size value'; });
          size.value='30'; size.dispatchEvent(new Event('input'));
          var backdrop=Array.from(dialog.querySelectorAll('select')).find(function(el) { return el.labels[0].textContent==='Label backdrop'; });
          backdrop.value='on'; backdrop.dispatchEvent(new Event('change'));
          result.currentUnchanged=current===dialog.querySelector('.studio-current').innerHTML;
          result.livePlasma=!!dialog.querySelector('.studio-new .magic-plasma');
          result.liveBackdrop=!!dialog.querySelector('.studio-new .has-label-backdrop');
          result.previewSize=getComputedStyle(dialog.querySelector('.studio-new .Buttontext')).fontSize;
          var postsBefore=requests.length;
          dialog.querySelector('.studio-save').click(); await wait(900);
          result.savedExactlyOnce=requests.length===postsBefore+1;
          document.querySelector('#members').click();
          result.savedFontSize=getComputedStyle(document.querySelector('#stitch .Buttontext')).fontSize;
          result.savedBackdrop=!!document.querySelector('#stitch .has-label-backdrop');
          result.otherUnchanged=other===document.querySelector('#BugBlue').innerHTML;
          result.bounded=getComputedStyle(document.querySelector('#stitch')).overflow==='hidden';
          send('infobox/account',{user:'stitch',amount:10,purchases:[],history_available:true,undo_transaction:null});
          send('buttons',{special:'infobox'}); document.querySelector('.studio-launch').click(); await wait(30);
          dialog=document.querySelector('.button-studio');
          dialog.querySelectorAll('.studio-preset')[2].click();
          postsBefore=requests.length; dialog.querySelector('.studio-cancel').click();
          result.cancelSilent=requests.length===postsBefore;
          result.noFinancialCommands=requests.every(function(topic) { return topic.endsWith('/button_studio'); });
        } catch(error) { result.error=String(error.stack); }
        var output=document.createElement('pre'); output.id='smoke-result'; output.textContent=JSON.stringify(result); document.body.appendChild(output);
      },0);
    });
  `);
  const result=runChromium(command,`file://${fixturePath}`);
  fs.unlinkSync(fixturePath);
  if(skipIfChromiumSandboxed(t,result)) return;
  assert.ifError(result.error);
  assert.equal(result.status,0,result.stderr);
  const match=result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
  assert(match,result.stdout);
  const data=JSON.parse(match[1].replaceAll('&quot;','"').replaceAll('&amp;','&'));
  assert.equal(data.error,undefined,JSON.stringify(data));
  assert.equal(data.currentUnchanged,true);
  assert.equal(data.allPresetsTogether,true);
  assert.equal(data.previewCanvasPreserved,true);
  assert.equal(data.presetCanvasesPreserved,true);
  assert.equal(data.livePlasma,true);
  assert.equal(data.liveBackdrop,true);
  assert.equal(data.previewSize,'30px');
  assert.equal(data.savedFontSize,'30px');
  assert.equal(data.savedBackdrop,true);
  assert.equal(data.savedExactlyOnce,true);
  assert.equal(data.otherUnchanged,true);
  assert.equal(data.bounded,true);
  assert.equal(data.cancelSilent,true);
  assert.equal(data.noFinancialCommands,true);
});

test("a completed deposit displays a native payment dialog and dismisses through OK", (t) => {
  const command=chromiumCommand();
  if(!command) { t.skip('Chromium is not available'); return; }
  const repo=path.resolve(__dirname,'../..');
  const payment=spawnSync(path.join(repo,'.venv/bin/python'),[
    '-c','import json; from epc_payment import create_payment; print(json.dumps(create_payment("test_user", "25.50")))',
  ],{cwd:repo,encoding:'utf8'});
  assert.equal(payment.status,0,payment.stderr);
  const fixture=writeKassaFixture(`
    window.addEventListener('DOMContentLoaded',function() {
      setTimeout(function() {
        var result={};
        try {
          window.__eventSource.onmessage({data:JSON.stringify([
            'hack42bar/output/session/main/deposit_payment',JSON.stringify({payments:[${payment.stdout.trim()}]})
          ])});
          var dialog=document.getElementById('DepositPayment');
          var image=dialog.querySelector('img');
          result.modal=dialog.open && dialog.matches(':modal');
          result.qrWidth=image.getBoundingClientRect().width;
          result.details=dialog.textContent;
          dialog.querySelector('button').click();
          result.closed=!document.getElementById('DepositPayment');
          result.lastPost=window.__fetchCalls.at(-1).body;
        } catch(error) { result.error=String(error.stack); }
        var output=document.createElement('pre'); output.id='smoke-result';
        output.textContent=JSON.stringify(result); document.body.appendChild(output);
      },100);
    });
  `);
  const result=runChromium(command,`file://${fixture}`);
  fs.unlinkSync(fixture);
  if(skipIfChromiumSandboxed(t,result)) return;
  assert.ifError(result.error);
  assert.equal(result.status,0,result.stderr);
  const match=result.stdout.match(/<pre id="smoke-result">([^<]+)<\/pre>/);
  assert(match,result.stdout);
  const data=JSON.parse(match[1].replaceAll('&quot;','"').replaceAll('&amp;','&'));
  assert.equal(data.error,undefined,JSON.stringify(data));
  assert.equal(data.modal,true);
  assert(data.qrWidth>=300);
  assert.match(data.details,/NL43ABNA0136777643/);
  assert.match(data.details,/25.50/);
  assert.match(data.details,/test_user/);
  assert.equal(data.closed,true);
  assert.equal(data.lastPost,'topic=session%2Fmain%2Finput&msg=ok');
});

test("the checked-in jQuery vendor file is gone", () => {
  assert.equal(fs.existsSync(path.resolve(__dirname, "../../www/jquery.min.js")), false);
});
