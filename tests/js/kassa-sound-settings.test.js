const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

const DEFAULTS={command:'KDE_Beep_ClassicBeep.wav',deposit:'itsgone.wav',insufficient_funds:'sinterklaas.wav',sale:'katsjing.wav',error:'KDE_Beep_Beep.wav'};
const ALTERNATIVES={command:'KDE_Beep_Beep.wav',deposit:'money.wav',insufficient_funds:'insufficient_funds.wav',sale:'cash_tycoon.wav',error:'KDE_Beep_Beep.wav'};
function state(selected={}) {
  return {features:Object.keys(DEFAULTS).map((id)=>({id,label:id,default:DEFAULTS[id],
    selected:selected[id] || DEFAULTS[id],choices:[DEFAULTS[id],ALTERNATIVES[id]]}))};
}
function node(tag) {
  return {tag,children:[],attributes:{},listeners:{},_text:'',value:'',
    get textContent(){return this._text;},set textContent(text){this._text=text;this.children=[];},
    setAttribute(name,value){this.attributes[name]=value;},appendChild(child){this.children.push(child);},
    addEventListener(event,handler){this.listeners[event]=handler;}};
}
function fixture() {
  const requests=[];
  const timers=new Map();
  let sequence=0;
  const window={fetch(url,options){return new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));},
    setTimeout(callback){timers.set(++sequence,callback);return sequence;},clearTimeout(id){timers.delete(id);}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../www/kassa-sound-settings.js'),'utf8'),{window,document:{createElement:node},URLSearchParams});
  const container=node('main');
  const controller=window.HackBankSoundSettings.mount(container,{session:'bar',initialState:state()});
  const panel=container.children[0];
  const fields=Object.fromEntries(panel.children[1].children.map((card)=>[card.children[1].id.slice(6),{select:card.children[1],preview:card.children[2].children[0],reset:card.children[2].children[1]}]));
  function payload(index){return JSON.parse(requests[index].options.body.get('msg'));}
  return {requests,timers,controller,fields,payload,status:panel.children[2],resetAll:panel.children[0].children[1],
    async respond(index,current=state()) {
      requests[index].resolve({ok:true,json:()=>Promise.resolve({done:1})});
      await new Promise((resolve)=>setImmediate(resolve));
      controller.receive({request:payload(index).request,ok:true,settings:current});
    },
    change(id,sound) {fields[id].select.value=sound;fields[id].select.listeners.change();},
  };
}

test('feature dropdowns load saved choices and keep each feature’s own options',async()=>{
  const ui=fixture();
  assert.equal(ui.requests[0].options.body.get('topic'),'session/bar/sound_settings');
  await ui.respond(0,state({deposit:'money.wav'}));
  assert.equal(ui.fields.deposit.select.value,'money.wav');
  assert.deepEqual(ui.fields.sale.select.children.map((option)=>option.value),['katsjing.wav','cash_tycoon.wav']);
  assert.equal(ui.fields.command.select.disabled,false);
  assert.equal(ui.fields.command.reset.disabled,true);
  assert.equal(ui.fields.deposit.reset.disabled,false);
});

test('a changed choice saves immediately without consuming POS command input',async()=>{
  const ui=fixture();
  await ui.respond(0);
  ui.change('sale','cash_tycoon.wav');
  const request=ui.payload(1);
  assert.equal(request.feature,'sale');
  assert.equal(request.sound,'cash_tycoon.wav');
  assert.equal(ui.requests[1].options.body.get('topic'),'session/bar/sound_settings');
  assert.equal(ui.fields.sale.select.disabled,true);
  ui.controller.update(state()); // An older broadcast must not replace the pending selection.
  assert.equal(ui.fields.sale.select.value,'cash_tycoon.wav');
  await ui.respond(1,state({sale:'cash_tycoon.wav'}));
  assert.equal(ui.fields.sale.select.value,'cash_tycoon.wav');
  assert.equal(ui.status.textContent,'Sound settings saved.');
  assert.equal(ui.timers.size,0);
});

test('failed saves and timeouts restore the confirmed choice and allow retry',async()=>{
  const ui=fixture();
  await ui.respond(0);
  ui.change('deposit','money.wav');
  ui.controller.receive({request:ui.payload(1).request,ok:false,error:'Could not save sound.'});
  assert.equal(ui.fields.deposit.select.value,'itsgone.wav');
  assert.equal(ui.fields.deposit.select.disabled,false);
  assert.equal(ui.status.textContent,'Could not save sound.');
  ui.change('deposit','money.wav');
  Array.from(ui.timers.values()).forEach((callback)=>callback());
  assert.equal(ui.fields.deposit.select.value,'itsgone.wav');
  assert.match(ui.status.textContent,/could not be confirmed/);
});

test('per-feature and all-default resets use the settings route',async()=>{
  const ui=fixture();
  await ui.respond(0,state({deposit:'money.wav',sale:'cash_tycoon.wav'}));
  ui.fields.deposit.reset.listeners.click();
  assert.equal(ui.payload(1).reset,'deposit');
  await ui.respond(1,state({sale:'cash_tycoon.wav'}));
  assert.equal(ui.fields.deposit.select.value,'itsgone.wav');
  assert.equal(ui.fields.sale.select.value,'cash_tycoon.wav');
  ui.resetAll.listeners.click();
  assert.equal(ui.payload(2).reset,'all');
  await ui.respond(2);
  assert.equal(ui.fields.sale.select.value,'katsjing.wav');
});

test('leaving the page cancels waiting state and ignores late responses',async()=>{
  const ui=fixture();
  await ui.respond(0);
  ui.change('sale','cash_tycoon.wav');
  ui.controller.stop();
  assert.equal(ui.timers.size,0);
  const before=ui.status.textContent;
  await ui.respond(1,state({sale:'cash_tycoon.wav'}));
  assert.equal(ui.status.textContent,before);
});

test('settings from another browser update without sending a new write',async()=>{
  const ui=fixture();
  await ui.respond(0);
  ui.controller.update(state({command:'KDE_Beep_Beep.wav'}));
  assert.equal(ui.fields.command.select.value,'KDE_Beep_Beep.wav');
  assert.equal(ui.requests.length,1);
});

test('a feature with only its default sound can still be previewed without changing it',async()=>{
  const ui=fixture();
  await ui.respond(0);
  ui.fields.error.preview.listeners.click();
  assert.equal(ui.payload(1).preview,'error');
  assert.equal(ui.status.textContent,'Playing preview…');
  await ui.respond(1);
  assert.equal(ui.fields.error.select.value,'KDE_Beep_Beep.wav');
  assert.equal(ui.status.textContent,'Preview requested.');
});
