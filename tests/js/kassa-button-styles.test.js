const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

function load(window={},document={}) {
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../www/kassa-button-styles.js'),'utf8'),{window,document});
  return window.HackBankButtonStyles;
}
test('gradient percentages sort stably and sharp edges preserve both stops',()=>{
  const styles=load();
  const gradient={angle:180,stops:[{color:'#ffd700',position:100},{color:'#0057b7',position:0},{color:'#0057b7',position:50},{color:'#ffd700',position:50}]};
  const before=JSON.stringify(gradient);
  assert.equal(styles.cssGradient(gradient),'linear-gradient(180deg, #0057b7 0%, #0057b7 50%, #ffd700 50%, #ffd700 100%)');
  assert.equal(JSON.stringify(gradient),before);
});

function appearance(storage) {
  const classes=new Set(), nodes=[], events=[], handlers={};
  const document={
    body:{classList:{toggle(name,on) { if(on) classes.add(name); else classes.delete(name); }}},
    createElement() {
      const node={attributes:{},listeners:{},setAttribute(key,value) {this.attributes[key]=value;},addEventListener(key,handler){this.listeners[key]=handler;}};
      nodes.push(node);return node;
    },
    querySelectorAll(){return nodes;},
    addEventListener(name,handler){handlers[name]=handler;},
    dispatchEvent(event){events.push(event.type);},
  };
  const window={localStorage:storage,CustomEvent:function(type){this.type=type;},addEventListener(name,handler){handlers[name]=handler;}};
  const styles=load(window,document);
  handlers.DOMContentLoaded();
  return {styles,classes,events,handlers};
}

test('sunglasses persist the terminal preference and update rebuilt toggles without changing themes',()=>{
  const values=new Map(), storage={getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)};
  const first=appearance(storage);
  const before=JSON.stringify(first.styles.defaults('BugBlue'));
  const button=first.styles.toggleButton();
  assert.equal(button.attributes['aria-pressed'],'true');
  assert.equal(button.textContent,'😎');
  button.listeners.click();
  assert.equal(first.styles.enabled(),false);
  assert(first.classes.has('button-styles-off'));
  assert.equal(button.title,'Show button styles');
  assert.equal(button.attributes['aria-pressed'],'false');
  assert.equal(button.textContent,'🙂');
  assert.equal(JSON.stringify(first.styles.defaults('BugBlue')),before);
  assert.deepEqual(first.events,['buttonstyleschange']);
  const reloaded=appearance(storage);
  assert.equal(reloaded.styles.enabled(),false);
  assert(reloaded.classes.has('button-styles-off'));
  const rebuilt=reloaded.styles.toggleButton();
  assert.equal(rebuilt.attributes['aria-pressed'],'false');
  rebuilt.listeners.click();
  assert.equal(reloaded.styles.enabled(),true);
  assert(!reloaded.classes.has('button-styles-off'));
});

test('appearance toggles work with blocked storage and follow other tabs without writing back',()=>{
  const blocked=appearance({getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}});
  blocked.styles.toggleButton().listeners.click();
  assert.equal(blocked.styles.enabled(),false);
  const following=appearance({getItem(){return 'on';},setItem(){throw Error('should not write');}});
  following.handlers.storage({key:'unrelated',newValue:'off'});
  assert.equal(following.styles.enabled(),true);
  following.handlers.storage({key:'hackbank-button-styles',newValue:'off'});
  assert.equal(following.styles.enabled(),false);
  assert(following.classes.has('button-styles-off'));
  following.handlers.storage({key:null,newValue:null});
  assert.equal(following.styles.enabled(),true);
});
test('each user gets an independent editable copy of their existing theme',()=>{
  const styles=load();
  const first=styles.defaults('BugBlue');
  first.background.gradient.stops[0].color='#000000';
  assert.equal(styles.defaults('bugblue').background.kind,'glitter');
  assert.equal(styles.defaults('BugBlue').background.gradient.stops[0].color,'#102b65');
  assert.equal(styles.defaults('Anus').background.kind,'plasma');
  assert.equal(styles.defaults('Anus').text.backdrop.color,'#100c3d');
  assert.equal(styles.defaults('Jos').icon.kind,'key');
  assert.equal(styles.defaults('nino').background.gradient.stops[1].position,50);
  assert.equal(styles.defaults('nino').text.backdrop.color,'#fffdf3');
});
test('stitch keeps blue paint and bold white text with no bundled icon',()=>{
  const theme=load().defaults('stitch');
  assert.equal(theme.background.color,'#6088b0');
  assert.equal(theme.text.color,'#ffffff');
  assert.equal(theme.icon.kind,'none');
  assert.equal(theme.icon.image,'');
  assert.equal(fs.existsSync(path.join(__dirname,'../../www/images/users/stitch.png')),false);
});
