(function(window, document) {
  var STORAGE_KEY='hackbank-button-styles', enabled=true;
  try { enabled=window.localStorage.getItem(STORAGE_KEY) !== 'off'; } catch(_error) { /* The toggle still works without storage. */ }
  function updateToggle(button) {
    button.textContent=enabled ? '😎' : '🙂';
    button.setAttribute('aria-pressed',String(enabled));
    button.title=enabled ? 'Hide button styles' : 'Show button styles';
  }
  function updateAppearance() {
    if(document.body) document.body.classList.toggle('button-styles-off',!enabled);
    if(document.querySelectorAll) {
      document.querySelectorAll('.button-styles-toggle').forEach(updateToggle);
      document.querySelectorAll('.magic-button').forEach(updateName);
    }
  }
  function announceAppearance() {
    updateAppearance();
    document.dispatchEvent(new window.CustomEvent('buttonstyleschange'));
  }
  function setEnabled(value) {
    enabled=value !== false;
    try { window.localStorage.setItem(STORAGE_KEY,enabled ? 'on' : 'off'); } catch(_error) { /* Keep the in-memory preference. */ }
    announceAppearance();
  }
  function toggleButton() {
    var button=node('button','archive-tab button-styles-toggle');
    button.type='button';
    button.setAttribute('aria-label','Button styles'); updateToggle(button);
    button.addEventListener('click',function() { setEnabled(!enabled); });
    return button;
  }
  if(document.addEventListener) document.addEventListener('DOMContentLoaded',updateAppearance);
  if(window.addEventListener) window.addEventListener('storage',function(event) {
    if(event.key !== STORAGE_KEY && event.key !== null) return;
    enabled=event.newValue !== 'off'; announceAppearance();
  });
  var FONTS={system:'system-ui, sans-serif',rounded:'"Arial Rounded MT Bold", "Trebuchet MS", sans-serif',
    comic:'"Comic Sans MS", "Comic Sans", cursive',mono:'ui-monospace, "Courier New", monospace',
    serif:'Georgia, "Times New Roman", serif',condensed:'Impact, "Arial Narrow", sans-serif',
    cyber:'"HackBank Cyber", ui-monospace, "Courier New", monospace'};
  var CASES={original:'Original',uppercase:'UPPERCASE',lowercase:'lowercase',capitalize:'Capitalized Words',
    camel:'camelCase',pascal:'PascalCase',snake:'snake_case',kebab:'kebab-case'};
  var SYMBOLS={key:'🔑',star:'★',bolt:'ϟ',heart:'♥',smile:'☺'};
  function formatName(user,mode) {
    if(mode === 'uppercase') return user.toUpperCase();
    if(mode === 'lowercase') return user.toLowerCase();
    if(!['capitalize','camel','pascal','snake','kebab'].includes(mode)) return user;
    var words=user.replace(/(\p{Lu})(\p{Lu}\p{Ll})/gu,'$1 $2')
      .replace(/(\p{Ll}\p{M}*|\p{Nd})(\p{Lu})/gu,'$1 $2').split(/[\s_-]+/u).filter(Boolean);
    if(!words.length) return user;
    words=words.map(function(word) { return word.toLowerCase(); });
    if(mode === 'snake') return words.join('_');
    if(mode === 'kebab') return words.join('-');
    return words.map(function(word,index) {
      if(mode === 'camel' && index === 0) return word;
      var characters=Array.from(word);
      return characters.shift().toUpperCase()+characters.join('');
    }).join(mode === 'capitalize' ? ' ' : '');
  }
  function updateName(button) {
    var label=button.querySelector('.Buttontext');
    if(!label) return;
    var mode=enabled || button.classList.contains('magic-preview') ? button.getAttribute('data-button-case') : 'original';
    label.textContent=formatName(button.getAttribute('data-button-user'),mode);
  }
  function copy(value) { return JSON.parse(JSON.stringify(value)); }
  function gradient(colors,angle) {
    return {angle:angle,stops:colors.map(function(color,index) { return {color:color,position:index*100/(colors.length-1)}; })};
  }
  function base() {
    return {version:1,background:{kind:'solid',color:'#e7edf3',gradient:gradient(['#7760db','#f080b5'],135),speed:24,intensity:65},
      text:{color:'#263e52',gradient:null,size:17,font:'system',weight:700,angle:0,rotation:0,backdrop:null,case:'original'},
      icon:{kind:'none',image:'',size:36,rotation:0}};
  }
  var PRESETS=[
    {name:'Blue glitter',emoji:'✨',kind:'glitter',colors:['#102b65','#285c9d','#142e6b'],text:'#ffffff'},
    {name:'Cosmic plasma',emoji:'🪐',kind:'plasma',colors:['#251055','#fa228c','#04d9d2'],text:'#ffffff'},
    {name:'Candy shop',emoji:'🍬',kind:'gradient',colors:['#fdc5de','#c9b5ff','#a5e4f2'],text:'#38254e'},
    {name:'Sunset',emoji:'🌅',kind:'gradient',colors:['#fead63','#ee6f98','#7c5bd4'],text:'#ffffff'},
    {name:'Blue & yellow',emoji:'💙',kind:'gradient',colors:['#0057b7','#0057b7','#ffd700','#ffd700'],text:'#ffffff'},
    {name:'Fresh paint',emoji:'🎨',kind:'solid',colors:['#6088b0','#9bb9d7'],text:'#ffffff'},
    {name:'Five lights',emoji:'💡',kind:'shader-lights',colors:['#18183c','#ed548a','#6fddd5'],text:'#ffffff',speed:40},
    {name:'Snow',emoji:'❄️',kind:'shader-snow',colors:['#102d48','#416c9b','#e9f6ff'],text:'#ffffff',speed:32},
    {name:'Cubes',emoji:'🧊',kind:'shader-cubes',colors:['#182742','#448eab','#a9d5e2'],text:'#ffffff',speed:44},
    {name:'Synthwave',emoji:'🌴',kind:'shader-synthwave',colors:['#201136','#d749a1','#ffc07b'],text:'#ffffff',speed:40},
    {name:'Wonderful',emoji:'🔮',kind:'shader-wonderful',colors:['#c95bd8','#56e5d1','#ffb36c'],text:'#ffffff',speed:48},
    {name:'Heartfelt',emoji:'💜',kind:'shader-heartfelt',colors:['#171c3b','#415d91','#ffc6a1'],text:'#ffffff',speed:48},
    {name:'Star Nest',emoji:'🌌',kind:'shader-star-nest',colors:['#ff0000','#00ff00','#0000ff'],text:'#ffffff',speed:40},
    {name:'2D Clouds',emoji:'☁️',kind:'shader-clouds',colors:['#336699','#66b3ff','#ffffe6'],text:'#ffffff',speed:36},
    {name:'Universe Within',emoji:'🌠',kind:'shader-universe',colors:['#552d91','#6ccdee','#dfbdf2'],text:'#ffffff',speed:48},
    {name:'Matrix',emoji:'💻',kind:'shader-matrix',colors:['#000804','#008f3b','#b6ffd1'],text:'#ffffff',speed:24},
  ];
  function preset(index) {
    var definition=PRESETS[index];
    var theme=base();
    theme.background.kind=definition.kind;
    theme.background.color=definition.colors[0];
    theme.background.gradient=gradient(definition.colors,135);
    theme.text.color=definition.text;
    if(definition.kind.startsWith('shader-')) {
      theme.background.speed=definition.speed; theme.background.intensity=90;
      theme.text.backdrop={color:definition.kind === 'shader-matrix' ? '#001208' : '#100c26',opacity:65,padding:5,radius:5};
    }
    if(index === 1) theme.text.backdrop={color:'#100c3d',opacity:80,padding:5,radius:5};
    if(index === 4) {
      theme.background.gradient={angle:180,stops:[{color:'#0057b7',position:0},{color:'#0057b7',position:50},{color:'#ffd700',position:50},{color:'#ffd700',position:100}]};
      theme.text.color='#102d48';
      theme.text.backdrop={color:'#fffdf3',opacity:95,padding:5,radius:5};
    }
    return theme;
  }
  function defaults(user) {
    switch(user.toLowerCase()) {
      case 'stitch': return preset(5);
      case 'bugblue': return preset(0);
      case 'anus': return preset(1);
      case 'nino': return preset(4);
      case 'jos': {
        var theme=base();
        theme.background.kind='gradient';
        theme.background.gradient=gradient(['#263649','#182533'],120);
        theme.text.color='#fff8e7';
        theme.icon.kind='key';
        return theme;
      }
      default: return base();
    }
  }
  function cssGradient(value) {
    return 'linear-gradient('+value.angle+'deg, '+value.stops.slice().sort(function(a,b) { return a.position-b.position; }).map(function(stop) {
      return stop.color+' '+stop.position+'%';
    }).join(', ')+')';
  }
  function node(tag,className) {
    var element=document.createElement(tag);
    element.className=className;
    return element;
  }
  function apply(button,user,design) {
    var theme=design || defaults(user);
    var label=button.querySelector('.Buttontext');
    if(!label) return;
    button.appendChild(label);
    button.querySelectorAll('.magic-label, .magic-icon').forEach(function(element) { element.remove(); });
    button.classList.add('magic-button');
    button.classList.toggle('magic-neutral',!design && !['stitch','bugblue','anus','nino','jos'].includes(user.toLowerCase()));
    button.setAttribute('data-button-user',user);
    button.setAttribute('data-button-case',theme.text.case || 'original');
    updateName(button);
    var background=theme.background;
    var layer=button.querySelector('.magic-layer') || node('span','magic-layer');
    layer.className='magic-layer magic-'+background.kind;
    layer.setAttribute('aria-hidden','true');
    layer.style.background=background.kind === 'solid' ? background.color : cssGradient(background.gradient);
    layer.style.setProperty('--magic-speed',background.speed+'s');
    layer.style.setProperty('--magic-power',background.intensity/100);
    background.gradient.stops.slice(0,3).forEach(function(stop,index) { layer.style.setProperty('--magic-color-'+index,stop.color); });
    if(background.gradient.stops.length < 3) layer.style.setProperty('--magic-color-2',background.gradient.stops[0].color);
    button.prepend(layer);
    if(window.HackBankButtonShaders) window.HackBankButtonShaders.attach(layer,background,user);
    button.style.setProperty('--magic-ink',theme.text.color);
    button.style.setProperty('--magic-font',FONTS[theme.text.font] || FONTS.system);
    button.style.setProperty('--magic-synthesis',theme.text.font === 'cyber' ? 'weight' : 'none');
    button.style.setProperty('--magic-size',theme.text.size+'px');
    button.style.setProperty('--magic-weight',theme.text.weight);
    if(theme.icon.kind !== 'none') {
      var icon=node('span','magic-icon');
      icon.setAttribute('aria-hidden','true');
      icon.style.width=theme.icon.size+'px';
      icon.style.height=theme.icon.size+'px';
      icon.style.flexBasis=theme.icon.size+'px';
      var picture;
      if(theme.icon.kind === 'image') {
        picture=node('img','magic-icon-image');
        picture.src=theme.icon.image; picture.alt='';
      } else {
        picture=node('span','magic-symbol');
        picture.textContent=SYMBOLS[theme.icon.kind] || '';
        picture.style.fontSize=theme.icon.size+'px';
      }
      if(theme.icon.rotation) { picture.classList.add('magic-spin'); picture.style.animationDuration=theme.icon.rotation+'s'; }
      icon.appendChild(picture);
      button.appendChild(icon);
    }
    var frame=node('span','magic-label');
    var angle=node('span','magic-angle');
    angle.style.transform='rotate('+theme.text.angle+'deg)';
    var name=node('span','magic-name');
    var backdrop=theme.text.backdrop;
    if(backdrop) {
      name.classList.add('has-label-backdrop');
      name.style.setProperty('--label-backdrop-color',backdrop.color);
      name.style.setProperty('--label-backdrop-opacity',backdrop.opacity/100);
      name.style.setProperty('--label-backdrop-padding',backdrop.padding+'px');
      name.style.setProperty('--label-backdrop-radius',backdrop.radius+'px');
    }
    label.style.fontSize='';
    label.classList.remove('magic-spin');
    label.style.animationDuration='';
    if(theme.text.rotation) { name.classList.add('magic-spin'); name.style.animationDuration=theme.text.rotation+'s'; }
    label.classList.toggle('magic-text-gradient',!!theme.text.gradient);
    label.style.backgroundImage=theme.text.gradient ? cssGradient(theme.text.gradient) : '';
    name.appendChild(label); angle.appendChild(name); frame.appendChild(angle); button.appendChild(frame);
    var balance=button.querySelector('.extra');
    if(balance) button.appendChild(balance);
  }
  function preview(user,amount,theme) {
    var button=node('div','Knopje Knop account magic-preview');
    button.setAttribute('role','img');
    button.setAttribute('aria-label',user+' button preview');
    var label=node('span','Buttontext'); label.textContent=user;
    var balance=node('span','extra'+(amount < -13.37 ? ' rood' : (amount < 0 ? ' orange' : '')));
    balance.textContent=Number(amount).toFixed(2);
    button.appendChild(label); button.appendChild(balance);
    apply(button,user,theme);
    return button;
  }
  window.HackBankButtonStyles={apply:apply,preview:preview,defaults:defaults,copy:copy,gradient:gradient,cssGradient:cssGradient,preset:preset,presets:PRESETS,fonts:FONTS,cases:CASES,formatName:formatName,
    enabled:function() { return enabled; },setEnabled:setEnabled,toggleButton:toggleButton};
})(window, document);
