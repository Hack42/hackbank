(function(window, document) {
  function element(tag, className, text) {
    var node=document.createElement(tag);
    node.className=className;
    if(text) node.textContent=text;
    return node;
  }

  function mount(container) {
    var stopped=false;
    var readInFlight=false;
    var writeChannel=null;
    var revision=0;
    var sendTimer=null;
    var pending={pos: null, space: null};
    var dragging={pos: false, space: false};
    var controls={};
    var panel=element('section','audio-controls');
    panel.setAttribute('aria-label','Audio volumes');
    var cards=element('div','audio-volume-grid');
    var status=element('p','audio-status','Reading audio levels…');
    status.setAttribute('role','status');
    panel.appendChild(cards);
    panel.appendChild(status);
    container.appendChild(panel);

    function message(text) {
      if(status.textContent !== text) status.textContent=text;
    }
    function showLevel(control, value, muted) {
      control.input.value=String(Math.min(100,value));
      control.output.textContent=muted ? 'Muted' : value+'%';
      control.input.setAttribute('aria-valuetext',muted ? 'Muted, '+value+' percent' : value+' percent');
      control.input.style.setProperty('--volume-fill',Math.min(100,value)+'%');
    }
    function apply(state, confirmed) {
      if(stopped) return;
      if(!state || !state.channels) throw new Error('Invalid audio state');
      var available=0;
      Object.keys(controls).forEach(function(id) {
        var channel=state.channels[id];
        var control=controls[id];
        if(!channel || !channel.available || !Number.isFinite(channel.volume)) {
          control.input.disabled=true;
          control.output.textContent='Unavailable';
          control.input.setAttribute('aria-valuetext','Unavailable');
          return;
        }
        available++;
        control.input.disabled=false;
        if(dragging[id] || pending[id] !== null || (writeChannel === id && confirmed !== id)) return;
        showLevel(control,channel.volume,channel.muted);
      });
      message(available === 2 ? 'Volumes are up to date.' : (available ? 'One audio output is unavailable.' : 'Audio controls are unavailable.'));
    }
    function unavailable() {
      if(stopped) return;
      Object.keys(controls).forEach(function(id) {
        controls[id].input.disabled=true;
        controls[id].output.textContent='Unavailable';
        controls[id].input.setAttribute('aria-valuetext','Unavailable');
      });
      message('Audio controls are unavailable.');
    }
    function json(response) {
      if(!response.ok) throw new Error('Audio request failed');
      return response.json();
    }
    function hasPending() {
      return Object.keys(pending).some(function(id) { return pending[id] !== null; });
    }
    function refresh() {
      if(stopped || readInFlight || writeChannel || hasPending()) return;
      var requestedRevision=revision;
      readInFlight=true;
      window.fetch('audio.php',{cache: 'no-store'}).then(json).then(function(state) {
        if(requestedRevision === revision) apply(state);
      }).catch(function() {
        if(requestedRevision === revision) unavailable();
      }).finally(function() { readInFlight=false; });
    }
    function sendNext() {
      if(stopped || writeChannel) return;
      var id=Object.keys(pending).find(function(key) { return pending[key] !== null; });
      if(!id) return;
      var value=pending[id];
      pending[id]=null;
      writeChannel=id;
      message('Saving volume…');
      window.fetch('audio.php',{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({channel: id, volume: value}),
      }).then(json).then(function(state) {
        apply(state,id);
      }).catch(function() {
        pending[id]=null;
        unavailable();
      }).finally(function() {
        writeChannel=null;
        if(!stopped) {
          if(hasPending()) sendNext();
          else refresh();
        }
      });
    }
    function queue(id, immediate) {
      var control=controls[id];
      if(control.input.disabled || stopped) return;
      var value=Number(control.input.value);
      pending[id]=value;
      revision++;
      showLevel(control,value,false);
      window.clearTimeout(sendTimer);
      if(immediate) sendNext();
      else sendTimer=window.setTimeout(sendNext,120);
    }

    [{id: 'pos', label: 'HackBank POS effects', hint: 'Scans, confirmations and alerts'},
      {id: 'space', label: 'Space audio', hint: 'Building sound system'}].forEach(function(channel) {
      var card=element('div','audio-volume-card');
      var heading=element('div','audio-volume-heading');
      var label=element('label','audio-volume-label',channel.label);
      label.setAttribute('for','Volume-'+channel.id);
      var output=element('output','audio-volume-value','…');
      output.setAttribute('for','Volume-'+channel.id);
      heading.appendChild(label);
      heading.appendChild(output);
      var input=element('input','audio-slider');
      input.type='range';
      input.id='Volume-'+channel.id;
      input.min='0';
      input.max='100';
      input.step='1';
      input.value='0';
      input.disabled=true;
      controls[channel.id]={input: input, output: output};
      input.addEventListener('input',function() { queue(channel.id,false); });
      input.addEventListener('change',function() { queue(channel.id,true); });
      input.addEventListener('pointerdown',function() { dragging[channel.id]=true; });
      ['pointerup','pointercancel','blur'].forEach(function(event) {
        input.addEventListener(event,function() { dragging[channel.id]=false; });
      });
      card.appendChild(heading);
      card.appendChild(element('p','audio-volume-hint',channel.hint));
      card.appendChild(input);
      var scale=element('div','audio-volume-scale');
      scale.appendChild(element('span','','Silent'));
      scale.appendChild(element('span','','100%'));
      card.appendChild(scale);
      cards.appendChild(card);
    });
    refresh();
    var pollTimer=window.setInterval(refresh,2000);
    return {
      stop: function() {
        stopped=true;
        window.clearInterval(pollTimer);
        window.clearTimeout(sendTimer);
      },
    };
  }

  window.HackBankAudio={mount: mount};
})(window, document);
