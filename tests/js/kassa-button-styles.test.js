const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

function load() {
  const window={};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../www/kassa-button-styles.js'),'utf8'),{window,document:{}});
  return window.HackBankButtonStyles;
}
test('gradient percentages sort stably and sharp edges preserve both stops',()=>{
  const styles=load();
  const gradient={angle:180,stops:[{color:'#ffd700',position:100},{color:'#0057b7',position:0},{color:'#0057b7',position:50},{color:'#ffd700',position:50}]};
  const before=JSON.stringify(gradient);
  assert.equal(styles.cssGradient(gradient),'linear-gradient(180deg, #0057b7 0%, #0057b7 50%, #ffd700 50%, #ffd700 100%)');
  assert.equal(JSON.stringify(gradient),before);
});
test('each user gets an independent editable copy of their existing theme',()=>{
  const styles=load();
  const first=styles.defaults('BugBlue');
  first.background.gradient.stops[0].color='#000000';
  assert.equal(styles.defaults('bugblue').background.kind,'glitter');
  assert.equal(styles.defaults('BugBlue').background.gradient.stops[0].color,'#102b65');
  assert.equal(styles.defaults('Anus').background.kind,'plasma');
  assert.equal(styles.defaults('Jos').icon.kind,'key');
  assert.equal(styles.defaults('nino').background.gradient.stops[1].position,50);
});
test('stitch keeps blue paint and bold white text with no bundled icon',()=>{
  const theme=load().defaults('stitch');
  assert.equal(theme.background.color,'#6088b0');
  assert.equal(theme.text.color,'#ffffff');
  assert.equal(theme.icon.kind,'none');
  assert.equal(theme.icon.image,'');
  assert.equal(fs.existsSync(path.join(__dirname,'../../www/images/users/stitch.png')),false);
});
