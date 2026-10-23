const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

function setup() {
  let now=0;
  let sequence=0;
  const frames=new Map();
  const listeners=new Set();
  const canvases=[];
  const drawn=[];
  const context={setTransform(){},clearRect(){drawn.length=0;},save(){},restore(){},rotate(){},
    translate(x,y){drawn.push({x,y});},fillRect(){}};
  const window={innerWidth:1920,innerHeight:1080,devicePixelRatio:1,performance:{now:()=>now},
    requestAnimationFrame(callback){frames.set(++sequence,callback);return sequence;},
    cancelAnimationFrame(id){frames.delete(id);},
    addEventListener(type,callback){listeners.add(callback);},
    removeEventListener(type,callback){listeners.delete(callback);}};
  const document={body:{appendChild(canvas){canvases.push(canvas);}},createElement(){
    return {setAttribute(){},getContext(){return context;},remove(){canvases.splice(canvases.indexOf(this),1);}};
  }};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../www/kassa-confetti.js'),'utf8'),{window,document});
  const confetti=window.HackBankConfetti.create();
  function advance(milliseconds) {
    const until=now+milliseconds;
    while(now<until) {
      now=Math.min(until,now+16);
      const pending=Array.from(frames.values());
      frames.clear();
      pending.forEach((callback)=>callback(now));
    }
  }
  return {confetti,advance,canvases,drawn,frames,listeners};
}

test('confetti enters at the top, falls down, and removes its canvas when finished',()=>{
  const {confetti,advance,canvases,drawn,frames,listeners}=setup();
  assert.equal(canvases.length,0);
  confetti.burst(false);
  advance(16);
  assert.equal(drawn.length,18);
  assert(drawn.every(({y})=>y<0));
  advance(2000);
  assert(drawn.every(({y})=>y>0));
  advance(14000);
  assert.equal(canvases.length,0);
  assert.equal(frames.size,0);
  assert.equal(listeners.size,0);
});

test('completed sales get more confetti, with bounded work and one animation loop',()=>{
  const {confetti,advance,drawn,frames,canvases}=setup();
  confetti.burst(true);
  advance(16);
  assert.equal(drawn.length,90);
  for(let i=0;i<100;i++) confetti.burst(false);
  assert.equal(frames.size,1);
  assert.equal(canvases.length,1);
  advance(16);
  assert.equal(drawn.length,360);
});

test('switching confetti off cancels the animation and allows a fresh start',()=>{
  const {confetti,advance,frames,canvases,listeners}=setup();
  confetti.burst(false);
  confetti.clear();
  advance(1000);
  assert.equal(frames.size,0);
  assert.equal(canvases.length,0);
  assert.equal(listeners.size,0);
  confetti.burst(false);
  assert.equal(canvases.length,1);
  assert.equal(frames.size,1);
});
