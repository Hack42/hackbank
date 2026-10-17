(function(window, document) {
  var FEATURES={command:'Command',deposit:'Deposit',insufficient_funds:'Insufficient funds',sale:'Sale',error:'Error'};
  var sequence=0;

  function element(tag, className, text) {
    var node=document.createElement(tag);
    node.className=className;
    if(text) node.textContent=text;
    return node;
  }
  function mount(container, options) {
    var stopped=false;
    var confirmed=null;
    var pending=null;
    var timeout=null;
    var fields={};
    var panel=element('section','pos-sound-settings');
    panel.setAttribute('aria-label','POS sounds');
    var heading=element('div','pos-sound-settings-heading');
    var title=element('div','');
    title.appendChild(element('h2','','POS sounds'));
    title.appendChild(element('p','profile-hint','Selections save and preview automatically.'));
    var resetAll=element('button','sound-reset','Reset all to defaults');
    resetAll.type='button';
    resetAll.addEventListener('click',function() { send({reset:'all'}); });
    heading.appendChild(title); heading.appendChild(resetAll);
    panel.appendChild(heading);
    var grid=element('div','pos-sound-grid');
    var status=element('p','pos-sound-status','Reading POS sounds…');
    status.setAttribute('role','status');
    panel.appendChild(grid); panel.appendChild(status);
    container.appendChild(panel);

    function render() {
      Object.keys(fields).forEach(function(id) {
        var field=fields[id];
        var feature=confirmed && confirmed.features.find(function(item) { return item.id === id; });
        field.select.disabled=!!pending || !feature;
        field.preview.disabled=!!pending || !feature;
        field.reset.disabled=!!pending || !feature || feature.selected === feature.default;
        if(!feature || pending) return;
        var choices=JSON.stringify(feature.choices);
        if(field.choices !== choices) {
          field.select.textContent='';
          feature.choices.forEach(function(sound) {
            var option=element('option','',sound+(sound === feature.default ? ' (default)' : ''));
            option.value=sound;
            field.select.appendChild(option);
          });
          field.choices=choices;
        }
        field.select.value=feature.selected;
        field.select.title=feature.selected;
      });
      resetAll.disabled=!!pending;
    }
    function update(state) {
      if(stopped || !state || !Array.isArray(state.features)) return false;
      if(!Object.keys(FEATURES).every(function(id) {
        return state.features.some(function(item) { return item.id === id && Array.isArray(item.choices) && item.choices.includes(item.selected); });
      })) return false;
      confirmed=state;
      render();
      return true;
    }
    function failed(id, message) {
      if(stopped || !pending || pending.id !== id) return;
      window.clearTimeout(timeout);
      pending=null;
      render();
      status.textContent=message;
    }
    function send(change) {
      if(stopped || pending) return;
      var id=Date.now()+'-'+(++sequence)+'-'+Math.random().toString(36).slice(2,8);
      pending={id:id,action:change.preview ? 'preview' : (Object.keys(change).length ? 'save' : 'read')};
      render();
      status.textContent={save:'Saving sound…',preview:'Playing preview…',read:'Reading POS sounds…'}[pending.action];
      timeout=window.setTimeout(function() { failed(id,'No reply from the bar. Your sound choice could not be confirmed.'); },8000);
      window.fetch('post.php',{
        method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams({topic:'session/'+options.session+'/sound_settings',msg:JSON.stringify(Object.assign({request:id},change))}),
      }).then(function(response) {
        if(!response.ok) throw new Error('Sound request failed');
        return response.json();
      }).then(function(reply) {
        if(reply.done !== 1) throw new Error('Sound request failed');
      }).catch(function() { failed(id,'Could not reach the bar. Please try again.'); });
    }
    function receive(reply) {
      if(stopped || !pending || !reply || reply.request !== pending.id) return;
      if(!reply.ok) { failed(pending.id,reply.error || 'Sound settings could not be saved.'); return; }
      var action=pending.action;
      window.clearTimeout(timeout); pending=null;
      if(!update(reply.settings)) {
        render(); status.textContent='POS sound settings are unavailable. Please try again.'; return;
      }
      status.textContent={save:'Sound settings saved.',preview:'Preview requested.',read:'Sound settings are up to date.'}[action];
    }

    Object.keys(FEATURES).forEach(function(id) {
      var card=element('div','pos-sound-card');
      var label=element('label','pos-sound-label',FEATURES[id]);
      label.setAttribute('for','Sound-'+id);
      var select=element('select','pos-sound-select');
      select.id='Sound-'+id;
      select.disabled=true;
      select.addEventListener('change',function() { send({feature:id,sound:select.value}); });
      var actions=element('div','pos-sound-actions');
      var preview=element('button','sound-reset','Preview');
      preview.type='button'; preview.disabled=true;
      preview.setAttribute('aria-label','Preview '+FEATURES[id].toLowerCase()+' sound');
      preview.addEventListener('click',function() { send({preview:id}); });
      var reset=element('button','sound-reset','Reset');
      reset.type='button'; reset.disabled=true;
      reset.setAttribute('aria-label','Reset '+FEATURES[id].toLowerCase()+' sound to default');
      reset.addEventListener('click',function() { send({reset:id}); });
      actions.appendChild(preview); actions.appendChild(reset);
      card.appendChild(label); card.appendChild(select); card.appendChild(actions);
      grid.appendChild(card);
      fields[id]={select:select,reset:reset,preview:preview,choices:null};
    });
    update(options.initialState);
    send({});
    return {
      update:update,
      receive:receive,
      stop:function() { stopped=true; pending=null; window.clearTimeout(timeout); },
    };
  }
  window.HackBankSoundSettings={mount:mount};
})(window, document);
