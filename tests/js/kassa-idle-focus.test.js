const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

function load() {
  let now=0, sequence=0, paused=false, focused=true, dialog=false;
  const timers=new Map(), documentEvents=new Map(), windowEvents=new Map();
  const document={
    hidden:false,activeElement:{tagName:'BUTTON'},
    hasFocus:()=>focused,
    querySelector:()=>dialog ? {} : null,
    addEventListener:(name,callback)=>documentEvents.set(name,callback),
    removeEventListener:(name)=>documentEvents.delete(name),
  };
  const input={value:'2* clubmate',focusCalls:0,focus(options){this.focusCalls++;this.focusOptions=options;document.activeElement=this;}};
  const window={
    setTimeout(callback,delay){const id=++sequence;timers.set(id,{callback,due:now+delay});return id;},
    clearTimeout:(id)=>timers.delete(id),
    addEventListener:(name,callback)=>windowEvents.set(name,callback),
    removeEventListener:(name)=>windowEvents.delete(name),
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../www/kassa-idle-focus.js'),'utf8'),{window,document,Date:{now:()=>now}});
  const controller=window.HackBankIdleFocus.watch({getInput:()=>input,isPaused:()=>paused});
  function advance(ms) {
    const until=now+ms;
    for(;;) {
      const next=Array.from(timers).filter(([,timer])=>timer.due<=until).sort((a,b)=>a[1].due-b[1].due)[0];
      if(!next) break;
      now=next[1].due;timers.delete(next[0]);next[1].callback();
    }
    now=until;
  }
  return {document,input,controller,timers,advance,
    activity:(name)=>documentEvents.get(name)(),
    windowEvent:(name)=>windowEvents.get(name)(),
    pause:(value)=>{paused=value;},modal:(value)=>{dialog=value;},windowFocus:(value)=>{focused=value;},
    listenerCount:()=>documentEvents.size+windowEvents.size};
}

test('one minute of inactivity focuses the command line without changing its text',()=>{
  const app=load();
  app.advance(59999);assert.equal(app.input.focusCalls,0);
  app.advance(1);assert.equal(app.input.focusCalls,1);
  assert.equal(app.input.focusOptions.preventScroll,true);
  assert.equal(app.input.value,'2* clubmate');
  app.advance(120000);assert.equal(app.input.focusCalls,1);
});

test('keyboard, mouse, touch and form activity each restart the minute',()=>{
  for(const event of ['keydown','input','pointerdown','pointermove','click','wheel','change','touchmove']) {
    const app=load();
    app.advance(59000);app.activity(event);
    app.advance(59999);assert.equal(app.input.focusCalls,0,event);
    app.advance(1);assert.equal(app.input.focusCalls,1,event);
  }
});

test('embedded pages retain focus until the user returns to the bar',()=>{
  const app=load();app.pause(true);
  app.advance(180000);assert.equal(app.input.focusCalls,0);
  app.pause(false);app.activity('pointerdown');
  app.advance(59999);assert.equal(app.input.focusCalls,0);
  app.advance(1);assert.equal(app.input.focusCalls,1);
});

test('iframe focus and open dialogs are left alone',()=>{
  const app=load();app.document.activeElement={tagName:'IFRAME'};
  app.advance(60000);assert.equal(app.input.focusCalls,0);
  app.document.activeElement={tagName:'BUTTON'};app.modal(true);
  app.advance(60000);assert.equal(app.input.focusCalls,0);
  app.modal(false);app.advance(1000);assert.equal(app.input.focusCalls,1);
});

test('hidden or unfocused windows do not reclaim focus, and recover when returning',()=>{
  const app=load();app.document.hidden=true;
  app.advance(60000);assert.equal(app.input.focusCalls,0);
  app.document.hidden=false;app.windowFocus(false);
  app.advance(60000);assert.equal(app.input.focusCalls,0);
  app.windowFocus(true);app.windowEvent('focus');
  assert.equal(app.input.focusCalls,1);
});

test('stopping clears the timer and all activity listeners',()=>{
  const app=load();app.controller.stop();
  assert.equal(app.timers.size,0);assert.equal(app.listenerCount(),0);
  app.advance(120000);assert.equal(app.input.focusCalls,0);
});
