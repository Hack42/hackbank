(function(window, document) {
  var MODES={dark: 'Dark mode', banana: 'Banana mode', dank: 'Dank Hit mode', party: 'Party mode'};
  var COMMANDS={darkmodeon: ['dark',true], darkmodeoff: ['dark',false],
    bananamodeon: ['banana',true], bananamodeoff: ['banana',false],
    dankmodeon: ['dank',true], dankmodeoff: ['dank',false]};

  function create(options) {
    var bananaLifetime=5*60*1000;
    var saved={};
    try { saved=JSON.parse(window.localStorage.getItem('hackbank-appearance') || '{}') || {}; } catch(_error) { /* Storage can be disabled. */ }
    var states={party: null, dark: saved.dark === true, banana: saved.banana === true || Number(saved.bananaUntil) > Date.now(), dank: saved.dank === true};
    var switches={};
    var bananas=[];

    function persist() {
      try {
        window.localStorage.setItem('hackbank-appearance',JSON.stringify({dark: states.dark, dank: states.dank, banana: states.banana,
          bananas: bananas.map(function(banana) { return banana.position; })}));
      } catch(_error) { /* Preferences still work without storage. */ }
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
    function removeBananas() {
      bananas.forEach(function(banana) {
        window.clearTimeout(banana.fadeTimer);
        window.clearTimeout(banana.expireTimer);
        banana.element.remove();
      });
      bananas=[];
    }
    function addBanana(position) {
      if(!states.banana) return;
      position=position || {left: Math.random(), top: Math.random(), until: Date.now()+bananaLifetime};
      var remaining=Math.min(bananaLifetime,Number(position.until)-Date.now());
      if(!Number.isFinite(remaining) || remaining <= 0) return;
      position={left: Math.min(1,Math.max(0,Number(position.left) || 0)), top: Math.min(1,Math.max(0,Number(position.top) || 0)), until: Date.now()+remaining};
      var element=document.createElement('img');
      element.className='dancing-banana';
      element.src='images/effects/banana/banana-peanut-butter-jelly-time.gif';
      element.alt='';
      element.setAttribute('aria-hidden','true');
      element.style.left=(12+position.left*Math.max(0,window.innerWidth-64))+'px';
      element.style.top=(12+position.top*Math.max(0,window.innerHeight-68))+'px';
      document.body.appendChild(element);
      var banana={element: element, position: position};
      bananas.push(banana);
      banana.fadeTimer=window.setTimeout(function() { element.classList.add('fading'); },Math.max(0,remaining-2000));
      banana.expireTimer=window.setTimeout(function() {
        element.remove();
        bananas=bananas.filter(function(item) { return item !== banana; });
        persist();
      },remaining);
    }
    function handleCommand(command) {
      var change=COMMANDS[command.trim()];
      if(!change) return false;
      states[change[0]]=change[1];
      if(change[0] === 'banana' && !change[1]) removeBananas();
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
      if(states.banana) { addBanana(); persist(); }
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
      window.setTimeout(function() { marker.remove(); },100);
    });
    if(Array.isArray(saved.bananas)) saved.bananas.forEach(function(position) { if(position) addBanana(position); });
    update(); persist();
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
