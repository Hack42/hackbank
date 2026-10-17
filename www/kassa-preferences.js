(function(window, document) {
  var MODES={dark: 'Dark mode', banana: 'Banana mode', dank: 'Dank Hit mode', party: 'Party mode'};
  var COMMANDS={darkmodeon: ['dark',true], darkmodeoff: ['dark',false],
    bananamodeon: ['banana',true], bananamodeoff: ['banana',false],
    dankmodeon: ['dank',true], dankmodeoff: ['dank',false]};

  function create(options) {
    var saved={};
    try { saved=JSON.parse(window.localStorage.getItem('hackbank-appearance') || '{}') || {}; } catch(_error) { /* Storage can be disabled. */ }
    var until=Math.min(Number(saved.bananaUntil) || 0,Date.now()+3600000);
    var states={party: null, dark: saved.dark === true, banana: until > Date.now(), dank: saved.dank === true};
    var switches={};
    var banana=null;
    var fadeTimer=null;
    var expireTimer=null;

    function persist() {
      try { window.localStorage.setItem('hackbank-appearance',JSON.stringify({dark: states.dark, dank: states.dank, bananaUntil: until})); } catch(_error) { /* Preferences still work without storage. */ }
    }
    function update() {
      Object.keys(switches).forEach(function(key) {
        var button=switches[key];
        button.disabled=states[key] === null;
        button.setAttribute('aria-checked',String(states[key] === true));
        button.querySelector('.setting-state').textContent=states[key] === null ? 'Reading…' : (states[key] ? 'Enabled' : 'Disabled');
      });
      document.body.classList[states.dark ? 'add' : 'remove']('dark-mode');
    }
    function removeBanana() {
      window.clearTimeout(fadeTimer);
      window.clearTimeout(expireTimer);
      if(banana) banana.remove();
      banana=null;
    }
    function renderBanana() {
      removeBanana();
      if(!states.banana) return;
      banana=document.createElement('img');
      banana.className='dancing-banana';
      banana.src='images/effects/banana/banana-peanut-butter-jelly-time.gif';
      banana.alt='';
      banana.setAttribute('aria-hidden','true');
      banana.style.left=(12+Math.random()*Math.max(0,window.innerWidth-124))+'px';
      banana.style.top=(90+Math.random()*Math.max(0,window.innerHeight-290))+'px';
      document.body.appendChild(banana);
      var remaining=Math.max(0,until-Date.now());
      fadeTimer=window.setTimeout(function() { if(banana) banana.classList.add('fading'); },Math.max(0,remaining-2000));
      expireTimer=window.setTimeout(function() {
        states.banana=false; until=0; removeBanana(); persist(); update();
      },remaining);
    }
    function handleCommand(command) {
      var change=COMMANDS[command.trim()];
      if(!change) return false;
      states[change[0]]=change[1];
      if(change[0] === 'banana') {
        until=change[1] ? Date.now()+3600000 : 0;
        renderBanana();
      }
      persist(); update();
      return true;
    }
    function toggle(key) {
      var button=document.createElement('button');
      button.type='button';
      button.className='setting-toggle';
      button.id='Setting-'+key;
      button.setAttribute('role','switch');
      var label=document.createElement('span');
      label.className='setting-name'; label.textContent=MODES[key];
      var state=document.createElement('span');
      state.className='setting-state';
      button.appendChild(label); button.appendChild(state);
      button.addEventListener('click',function() {
        var prefix=key === 'party' ? 'partymode' : key+'mode';
        options.sendCommand(prefix+(states[key] ? 'off' : 'on'));
      });
      switches[key]=button;
      update();
      return button;
    }
    document.addEventListener('click',function(event) {
      if(!states.dank) return;
      var marker=document.createElement('img');
      marker.className='click-hitmarker';
      marker.src='images/effects/mlg/hitmarker.gif';
      marker.alt=''; marker.setAttribute('aria-hidden','true');
      var rect=event.target.getBoundingClientRect ? event.target.getBoundingClientRect() : {left:0,top:0,width:0,height:0};
      marker.style.left=(event.detail ? event.clientX : rect.left+rect.width/2)+'px';
      marker.style.top=(event.detail ? event.clientY : rect.top+rect.height/2)+'px';
      document.body.appendChild(marker);
      options.playSound('../images/effects/mlg/hitmarker.wav');
      window.setTimeout(function() { marker.remove(); },300);
    });
    update(); renderBanana();
    return {
      handleCommand: handleCommand,
      toggle: toggle,
      setParty: function(state) { states.party=state.enabled === true; update(); },
      commands: Object.keys(COMMANDS).reduce(function(result, command) {
        var change=COMMANDS[command]; result[command]=(change[1] ? 'Enable ' : 'Disable ')+MODES[change[0]]; return result;
      },{}),
    };
  }
  window.HackBankPreferences={create: create};
})(window, document);
