(function(window, document) {
  var serial=0;
  function create(options) {
    var styles=window.HackBankButtonStyles;
    var dialog=null, profile=null, draft=null, current=null, pending=null, timeout=null;
    var editor, currentSlot, newSlot, status, save, retry, tabs, controls, returnFocus, shaderNote;
    var selectedTab='Background', ready=false, processing=false, dirty=false, generation=0;

    function el(tag,className,text) {
      var node=document.createElement(tag); node.className=className;
      if(text !== undefined) node.textContent=text;
      return node;
    }
    function button(text,className,callback) {
      var node=el('button',className,text); node.type='button';
      node.addEventListener('click',callback); return node;
    }
    function hint(text) { return el('p','studio-hint',text); }
    function message(text) { if(status) status.textContent=text; }
    function shaderStatus() {
      if(!shaderNote) return;
      var renderer=window.HackBankButtonShaders, state=renderer ? renderer.status(draft.background.kind) : 'unavailable';
      shaderNote.hidden=!['unavailable','lost'].includes(state) && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      shaderNote.textContent=['unavailable','lost'].includes(state)
        ? 'Animation is unavailable here. Your colour gradient is still shown, and you can keep designing.'
        : (window.matchMedia('(prefers-reduced-motion: reduce)').matches
          ? 'Reduced motion is on. These scenes keep a still preview.'
          : '');
      shaderNote.classList.toggle('studio-shader-fallback',['unavailable','lost'].includes(state));
    }
    function refreshButtons() {
      save.disabled=!ready || !!pending || processing;
      controls.disabled=!!pending || processing;
      retry.hidden=ready || !!pending;
    }
    function preview() {
      var design=!dirty && !options.getTheme(profile.user) ? null : draft;
      var button=newSlot.querySelector('.magic-preview');
      if(button) styles.apply(button,profile.user,design);
      else newSlot.appendChild(styles.preview(profile.user,profile.amount,design));
    }
    function changed() {
      dirty=true; preview(); message('Looking magical. Save when you’re happy!');
    }
    function inputField(parent,title,type,value,attributes,onInput) {
      var label=el('label','studio-field');
      label.appendChild(el('span','studio-field-name',title));
      var input=el('input','studio-input'); input.type=type; input.value=value;
      input.id='Studio-field-'+(++serial);
      Object.keys(attributes || {}).forEach(function(key) { input.setAttribute(key,attributes[key]); });
      input.addEventListener('input',function() { onInput(input.value,input); });
      label.appendChild(input); parent.appendChild(label); return input;
    }
    function range(parent,title,value,min,max,unit,onInput) {
      var field=el('div','studio-field studio-range');
      var label=el('label','studio-field-name',title);
      var row=el('div','studio-range-row');
      var input=el('input',''); input.type='range'; input.min=min; input.max=max; input.step=1; input.value=value;
      input.id='Studio-range-'+(++serial); label.htmlFor=input.id;
      var numeric=el('input','studio-number'); numeric.type='number'; numeric.min=min; numeric.max=max; numeric.step=1; numeric.value=value;
      numeric.setAttribute('aria-label',title+' value');
      function update(source,other) {
        if(!source.checkValidity() || source.value === '') return;
        other.value=source.value; onInput(Number(source.value)); changed();
      }
      input.addEventListener('input',function() { update(input,numeric); });
      numeric.addEventListener('input',function() { update(numeric,input); });
      row.appendChild(input); row.appendChild(numeric); row.appendChild(el('span','studio-unit',unit));
      field.appendChild(label); field.appendChild(row); parent.appendChild(field);
    }
    function select(parent,title,value,choices,onChange) {
      var field=el('div','studio-field');
      var label=el('label','studio-field-name',title);
      var input=el('select','studio-input');
      input.id='Studio-select-'+(++serial); label.htmlFor=input.id;
      Object.keys(choices).forEach(function(key) { var option=el('option','',choices[key]); option.value=key; input.appendChild(option); });
      input.value=value;
      input.addEventListener('change',function() { onChange(input.value); changed(); });
      field.appendChild(label); field.appendChild(input); parent.appendChild(field); return input;
    }
    function color(parent,title,value,onInput) {
      var field=el('div','studio-field studio-color');
      field.appendChild(el('span','studio-field-name',title));
      var row=el('div','studio-color-row');
      var picker=el('input','studio-color-picker'); picker.type='color'; picker.value=value;
      picker.setAttribute('aria-label',title+' colour picker');
      var hex=el('input','studio-input studio-hex'); hex.value=value; hex.spellcheck=false; hex.maxLength=7;
      hex.setAttribute('aria-label',title+' hex'); hex.pattern='#[A-Fa-f0-9]{6}'; hex.required=true;
      picker.addEventListener('input',function() { hex.value=picker.value; onInput(picker.value); changed(); });
      hex.addEventListener('input',function() { if(hex.checkValidity()) { picker.value=hex.value; onInput(hex.value); changed(); } });
      row.appendChild(picker); row.appendChild(hex); field.appendChild(row); parent.appendChild(field);
    }
    function gradient(parent,value,title) {
      var section=el('section','studio-gradient'); section.setAttribute('aria-label',title);
      section.appendChild(el('h3','',title));
      var track=el('div','studio-gradient-track');
      function repaint() { track.style.background=styles.cssGradient(value); }
      repaint(); section.appendChild(track);
      range(section,title+' angle',value.angle,0,360,'°',function(angle) { value.angle=angle; repaint(); });
      value.stops.forEach(function(stop,index) {
        var row=el('div','studio-stop');
        color(row,'Stop '+(index+1),stop.color,function(newColor) { stop.color=newColor; repaint(); });
        var position=inputField(row,'Position %','number',stop.position,{min:0,max:100,step:1,required:''},function(next,input) {
          if(input.checkValidity() && next !== '') { stop.position=Number(next); repaint(); changed(); }
        });
        position.setAttribute('aria-label',title+' stop '+(index+1)+' position');
        var remove=button('×','studio-stop-remove',function() { value.stops.splice(index,1); renderEditor(); changed(); });
        remove.disabled=value.stops.length <= 2;
        remove.setAttribute('aria-label','Remove '+title.toLowerCase()+' stop '+(index+1));
        row.appendChild(remove); section.appendChild(row);
      });
      var add=button('+ Add colour stop','studio-small-button',function() {
        value.stops.push({color:'#ffffff',position:50}); renderEditor(); changed();
      });
      add.disabled=value.stops.length >= 6; section.appendChild(add);
      section.appendChild(hint('Stops are sorted by percentage. Put two stops at the same % for a sharp edge.'));
      parent.appendChild(section);
    }
    function backgroundPanel() {
      var settings=editor.querySelector('.studio-background-settings');
      if(!settings) {
        editor.appendChild(el('h2','','Pick your kind of magic'));
        var presets=el('div','studio-presets');
        presets.setAttribute('aria-label','Background presets');
        styles.presets.forEach(function(preset,index) {
          var shader=preset.kind.startsWith('shader-');
          var tile=button('', 'studio-preset',function() {
            var next=styles.preset(index); draft.background=next.background; draft.text.color=next.text.color;
            if(shader && !draft.text.backdrop) draft.text.backdrop=next.text.backdrop;
            renderEditor(); changed();
          });
          tile.dataset.preset=index;
          var swatch=el('span','studio-swatch',shader ? '' : preset.emoji);
          swatch.setAttribute('aria-hidden','true');
          var design=styles.preset(index);
          swatch.style.background=design.background.kind === 'solid' ? design.background.color : styles.cssGradient(design.background.gradient);
          if(shader && window.HackBankButtonShaders) window.HackBankButtonShaders.attach(swatch,design.background,profile.user);
          tile.appendChild(swatch); tile.appendChild(el('span','',preset.name)); presets.appendChild(tile);
        });
        editor.appendChild(presets);
        shaderNote=hint(''); shaderNote.setAttribute('role','status'); editor.appendChild(shaderNote);
        settings=el('div','studio-background-settings'); editor.appendChild(settings);
      }
      settings.textContent='';
      editor.querySelectorAll('.studio-preset').forEach(function(tile) {
        var background=styles.preset(Number(tile.dataset.preset)).background;
        tile.setAttribute('aria-pressed',String(background.kind === draft.background.kind && JSON.stringify(background.gradient) === JSON.stringify(draft.background.gradient) && background.color === draft.background.color));
      });
      shaderStatus();
      var choices={solid:'Solid paint',gradient:'Colour gradient',glitter:'Glitter ✨',plasma:'Plasma 🪐'};
      styles.presets.forEach(function(preset) { if(preset.kind.startsWith('shader-')) choices[preset.kind]=preset.name; });
      select(settings,'Background style',draft.background.kind,choices,function(kind) {
        draft.background.kind=kind; renderEditor();
      });
      var shader=draft.background.kind.startsWith('shader-');
      if(draft.background.kind === 'solid') color(settings,'Background',draft.background.color,function(value) { draft.background.color=value; });
      else if(shader && window.HackBankButtonShaders) {
        var palette=el('section','studio-gradient'); palette.appendChild(el('h3','','Scene colours'));
        window.HackBankButtonShaders.palette(draft.background).filter(function(stop,index,all) { return all.indexOf(stop) === index; }).forEach(function(stop,index) {
          color(palette,'Scene colour '+(index+1),stop.color,function(value) { stop.color=value; });
        });
        palette.appendChild(hint('Your palette also becomes the still background when animation is unavailable.'));
        settings.appendChild(palette);
      }
      else gradient(settings,draft.background.gradient,'Background gradient');
      if(shader || ['glitter','plasma'].includes(draft.background.kind)) {
        var row=el('div','studio-field-grid');
        range(row,'Effect cycle',draft.background.speed,2,60,'sec',function(value) { draft.background.speed=value; });
        range(row,'Magic intensity',draft.background.intensity,0,100,'%',function(value) { draft.background.intensity=value; });
        settings.appendChild(row); settings.appendChild(hint('Longer cycles move more slowly. All the sparkles stay inside your button.'));
      }
    }
    function textPanel() {
      editor.appendChild(el('h2','','Give your name some personality'));
      var row=el('div','studio-field-grid');
      select(row,'Font',draft.text.font,{system:'Clean & friendly',rounded:'Round & bouncy',comic:'Comic time',mono:'Terminal hacker',serif:'Storybook',condensed:'Big & bold',cyber:'Cyber'},function(value) { draft.text.font=value; });
      select(row,'Weight',String(draft.text.weight),{'400':'Regular','600':'Semibold','700':'Bold','900':'Extra bold'},function(value) { draft.text.weight=Number(value); });
      editor.appendChild(row);
      select(editor,'Name case',draft.text.case || 'original',styles.cases,function(value) { draft.text.case=value; });
      range(editor,'Font size',draft.text.size,10,48,'px',function(value) { draft.text.size=value; });
      range(editor,'Text angle',draft.text.angle,0,360,'°',function(value) { draft.text.angle=value; });
      range(editor,'Text rotation',draft.text.rotation,0,60,'sec',function(value) { draft.text.rotation=value; });
      editor.appendChild(hint('Rotation: 0 is still. A higher number means a slower full turn.'));
      select(editor,'Text paint',draft.text.gradient ? 'gradient' : 'solid',{solid:'One colour',gradient:'Rainbow letters'},function(value) {
        draft.text.gradient=value === 'gradient' ? styles.gradient(['#fff3a6','#ff9bdb','#a7edff'],90) : null;
        renderEditor();
      });
      if(draft.text.gradient) gradient(editor,draft.text.gradient,'Text gradient');
      else color(editor,'Text',draft.text.color,function(value) { draft.text.color=value; });
      var backdrop=el('section','studio-gradient');
      backdrop.appendChild(el('h3','','A little contrast for your letters'));
      select(backdrop,'Label backdrop',draft.text.backdrop ? 'on' : 'off',{off:'No backdrop',on:'Colour backdrop'},function(value) {
        draft.text.backdrop=value === 'on' ? {color:'#100c3d',opacity:75,padding:5,radius:5} : null;
        renderEditor();
      });
      if(draft.text.backdrop) {
        color(backdrop,'Backdrop colour',draft.text.backdrop.color,function(value) { draft.text.backdrop.color=value; });
        range(backdrop,'Backdrop opacity',draft.text.backdrop.opacity,0,100,'%',function(value) { draft.text.backdrop.opacity=value; });
        var backdropShape=el('div','studio-field-grid');
        range(backdropShape,'Backdrop padding',draft.text.backdrop.padding,0,12,'px',function(value) { draft.text.backdrop.padding=value; });
        range(backdropShape,'Backdrop rounding',draft.text.backdrop.radius,0,20,'px',function(value) { draft.text.backdrop.radius=value; });
        backdrop.appendChild(backdropShape);
      }
      editor.appendChild(backdrop);
    }
    function loadImage(file) {
      if(!file || !/^image\/(png|jpeg|gif|webp)$/.test(file.type)) { message('Choose a PNG, JPEG, GIF or WebP image.'); return; }
      if(file.size > 8*1024*1024) { message('That image is a little big. Choose one under 8 MB.'); return; }
      var ticket=++generation;
      processing=true; refreshButtons(); message('Making your image button-sized…');
      var url=window.URL.createObjectURL(file);
      var image=new window.Image();
      function finished() { window.URL.revokeObjectURL(url); if(ticket === generation) { processing=false; refreshButtons(); } }
      image.onload=function() {
        if(ticket !== generation || !dialog) { finished(); return; }
        try {
          if(!image.naturalWidth || !image.naturalHeight || image.naturalWidth > 16000 || image.naturalHeight > 16000) throw new Error('Image too large');
          var canvas=document.createElement('canvas'); canvas.width=144; canvas.height=144;
          var size=Math.min(image.naturalWidth,image.naturalHeight);
          canvas.getContext('2d').drawImage(image,(image.naturalWidth-size)/2,(image.naturalHeight-size)/2,size,size,0,0,144,144);
          var png=canvas.toDataURL('image/png');
          if(png.length > 128*1024) throw new Error('Image too large');
          draft.icon.image=png; draft.icon.kind='image';
          finished(); renderEditor(); changed(); message('Image ready! Save to keep it with your button.');
        } catch(_error) { finished(); message('This image could not be resized. Please try another one.'); }
      };
      image.onerror=function() { finished(); if(ticket === generation) message('This image could not be opened. Please try another one.'); };
      image.src=url;
    }
    function iconPanel() {
      editor.appendChild(el('h2','','A tiny picture. A big entrance.'));
      select(editor,'Icon',draft.icon.kind,{none:'No icon',image:'My own image',key:'🔑 Key',star:'★ Star',bolt:'ϟ Lightning',heart:'♥ Heart',smile:'☺ Happy face'},function(value) {
        draft.icon.kind=value;
        if(value === 'image' && !draft.icon.image) message('Choose or paste an image to finish your icon.');
        renderEditor();
      });
      var drop=el('div','studio-drop'); drop.tabIndex=0; drop.setAttribute('aria-label','Paste or drop an icon image');
      drop.appendChild(el('span','studio-drop-star','🖼️'));
      drop.appendChild(el('strong','','Your image goes here'));
      drop.appendChild(hint('Drop an image, or focus here and paste with Ctrl+V (⌘V on a Mac).'));
      var file=el('input','studio-file'); file.type='file'; file.accept='image/png,image/jpeg,image/webp,image/gif';
      file.setAttribute('aria-label','Upload icon image');
      file.addEventListener('change',function() { loadImage(file.files[0]); });
      drop.appendChild(button('Choose image…','studio-small-button',function() { file.click(); })); drop.appendChild(file);
      drop.addEventListener('dragover',function(event) { event.preventDefault(); drop.classList.add('drag-over'); });
      drop.addEventListener('dragleave',function() { drop.classList.remove('drag-over'); });
      drop.addEventListener('drop',function(event) { event.preventDefault(); drop.classList.remove('drag-over'); loadImage(event.dataTransfer.files[0]); });
      editor.appendChild(drop);
      if(draft.icon.image) editor.appendChild(button('Remove my image','studio-small-button',function() { draft.icon.image=''; draft.icon.kind='none'; renderEditor(); changed(); }));
      editor.appendChild(hint('Images are cropped to a square and fitted with cover. Animated images become a still icon. The original file is not kept.'));
      range(editor,'Icon size',draft.icon.size,20,64,'px',function(value) { draft.icon.size=value; });
      range(editor,'Icon rotation',draft.icon.rotation,0,60,'sec',function(value) { draft.icon.rotation=value; });
      editor.appendChild(hint('Rotation: 0 is still. Larger numbers give a slower spin.'));
    }
    function renderEditor() {
      if(selectedTab !== 'Background' || !editor.querySelector('.studio-background-settings')) {
        shaderNote=null;
        editor.textContent=''; editor.scrollTop=0;
      }
      tabs.forEach(function(tab) { tab.setAttribute('aria-selected',String(tab.dataset.tab === selectedTab)); });
      editor.setAttribute('aria-labelledby','Studio-tab-'+selectedTab);
      if(selectedTab === 'Background') backgroundPanel();
      else if(selectedTab === 'Lettering') textPanel();
      else iconPanel();
    }
    function close() {
      if(pending && pending.action === 'save') { message('Saving your magic. Just a moment…'); return; }
      ++generation; processing=false;
      window.clearTimeout(timeout); pending=null;
      document.removeEventListener('buttonshaderstatus',shaderStatus); shaderNote=null;
      var previous=dialog; dialog=null;
      previous.close(); previous.remove();
      if(returnFocus && returnFocus.isConnected) returnFocus.focus();
    }
    function fail(id,text) {
      if(!dialog || !pending || pending.id !== id) return;
      window.clearTimeout(timeout); pending=null; refreshButtons(); message(text);
    }
    function request(theme) {
      if(!dialog || pending) return;
      var id='studio-'+Date.now()+'-'+(++serial);
      var payload={request:id,user:profile.user};
      if(theme) payload.theme=theme;
      pending={id:id,action:theme ? 'save' : 'read'};
      refreshButtons(); message(theme ? 'Saving your new button…' : 'Opening your paint box…');
      timeout=window.setTimeout(function() { fail(id,'No reply from the bar. Your changes are still here; please try again.'); },10000);
      window.fetch('post.php',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams({topic:'session/'+options.session+'/button_studio',msg:JSON.stringify(payload)})
      }).then(function(response) { if(!response.ok) throw new Error('Could not save'); return response.json(); })
        .then(function(reply) { if(reply.done !== 1) throw new Error('Could not save'); })
        .catch(function() { fail(id,'Could not reach the bar. Your changes are still here; please try again.'); });
    }
    function receive(reply) {
      if(!dialog || !pending || !reply || reply.request !== pending.id) return;
      if(!reply.ok) { fail(pending.id,reply.error || 'Your button could not be saved.'); return; }
      if(reply.user !== profile.user) { fail(pending.id,'The bar replied for a different user. Please reopen the studio.'); return; }
      var action=pending.action;
      window.clearTimeout(timeout); pending=null; ready=true;
      current=styles.copy(reply.theme || styles.defaults(profile.user));
      if(action === 'read' && !dirty) { draft=styles.copy(current); renderEditor(); preview(); }
      currentSlot.textContent=''; currentSlot.appendChild(styles.preview(profile.user,profile.amount,reply.theme));
      refreshButtons();
      if(action === 'save') {
        if(options.onSaved) options.onSaved(reply.user,reply.theme);
        dialog.classList.add('studio-saved'); message('Ta-da! Your new button is saved.');
        var savedDialog=dialog;
        window.setTimeout(function() { if(dialog === savedDialog) close(); },800);
      } else message('Your paint box is ready. Have fun!');
    }
    function open(userProfile) {
      if(dialog) return;
      document.addEventListener('buttonshaderstatus',shaderStatus);
      profile=userProfile; selectedTab='Background'; dirty=false; ready=false;
      returnFocus=document.activeElement;
      current=styles.copy(options.getTheme(profile.user) || styles.defaults(profile.user)); draft=styles.copy(current);
      dialog=el('dialog','button-studio'); dialog.setAttribute('aria-labelledby','Studio-title');
      var header=el('header','studio-header');
      header.appendChild(el('span','studio-badge','✦'));
      var title=el('div',''); title.appendChild(el('span','studio-eyebrow','THE BUTTON MAKEOVER MACHINE'));
      var h1=el('h1','','Hack42 Magic Button Studio (tm)'); h1.id='Studio-title'; title.appendChild(h1);
      title.appendChild(hint('A tiny button. A very big imagination.')); header.appendChild(title);
      var dismiss=button('×','studio-close',close); dismiss.setAttribute('aria-label','Close button studio'); header.appendChild(dismiss);
      dialog.appendChild(header);
      var main=el('div','studio-main');
      var workbench=el('aside','studio-workbench');
      workbench.appendChild(el('div','studio-owner','✂  Made by '+profile.user));
      workbench.appendChild(el('h2','','Your current button'));
      currentSlot=el('div','studio-current studio-preview-slot'); currentSlot.appendChild(styles.preview(profile.user,profile.amount,options.getTheme(profile.user))); workbench.appendChild(currentSlot);
      workbench.appendChild(el('div','studio-magic-arrow','↓ a little magic ↓'));
      workbench.appendChild(el('h2','','Your new button'));
      newSlot=el('div','studio-new studio-preview-slot'); workbench.appendChild(newSlot);
      workbench.appendChild(el('span','studio-live','● LIVE PREVIEW'));
      workbench.appendChild(hint('Same name. Same balance. All your personality.'));
      var resets=el('div','studio-draft-actions');
      resets.appendChild(button('↶ Revert changes','studio-small-button',function() { draft=styles.copy(current); renderEditor(); changed(); }));
      resets.appendChild(button('Start fresh','studio-small-button',function() { draft=styles.defaults(profile.user); renderEditor(); changed(); }));
      workbench.appendChild(resets);
      workbench.appendChild(el('div','studio-sticker','100% YOU\n0% BORING'));
      main.appendChild(workbench);
      var editing=el('section','studio-editing');
      var tablist=el('div','studio-tabs'); tablist.setAttribute('role','tablist'); tablist.setAttribute('aria-label','Button design tools');
      tabs=['Background','Lettering','Icon'].map(function(name,index) {
        var tab=button(['🎨  Background','🔤  Lettering','🖼️  Icon'][index],'studio-tab',function() { selectedTab=name; renderEditor(); });
        tab.id='Studio-tab-'+name; tab.dataset.tab=name; tab.setAttribute('role','tab'); tab.setAttribute('aria-controls','Studio-editor');
        tab.addEventListener('keydown',function(event) {
          if(!['ArrowRight','ArrowLeft','Home','End'].includes(event.key)) return;
          event.preventDefault();
          var next=event.key === 'Home' ? 0 : (event.key === 'End' ? 2 : (index+(event.key === 'ArrowRight' ? 1 : 2))%3);
          tabs[next].click(); tabs[next].focus();
        });
        tablist.appendChild(tab); return tab;
      });
      editing.appendChild(tablist);
      controls=el('fieldset','studio-controls');
      editor=el('div','studio-editor'); editor.id='Studio-editor'; editor.setAttribute('role','tabpanel');
      controls.appendChild(editor); editing.appendChild(controls);
      var scrollTools=el('div','studio-scroll-tools');
      scrollTools.appendChild(hint('More room for more magic'));
      scrollTools.appendChild(button('↑ Scroll up','studio-small-button',function() { editor.scrollBy({top:-editor.clientHeight*.75,behavior:'smooth'}); }));
      scrollTools.appendChild(button('Scroll down ↓','studio-small-button',function() { editor.scrollBy({top:editor.clientHeight*.75,behavior:'smooth'}); }));
      editing.appendChild(scrollTools); main.appendChild(editing); dialog.appendChild(main);
      var footer=el('footer','studio-footer');
      var notes=el('div','studio-save-note'); status=el('p','studio-status'); status.setAttribute('role','status'); notes.appendChild(status);
      notes.appendChild(hint('Saved on this bar, shared with its terminals. Images stay in the bar’s private data.'));
      retry=button('Try loading again','studio-small-button',function() { request(); }); notes.appendChild(retry);
      footer.appendChild(notes); footer.appendChild(button('Cancel','studio-cancel',close));
      save=button('✦ Use my new button','studio-save',function() {
        var invalid=Array.from(editor.querySelectorAll('input')).find(function(input) { return !input.checkValidity(); });
        if(invalid) { invalid.reportValidity(); return; }
        if(draft.icon.kind === 'image' && !draft.icon.image) { selectedTab='Icon'; renderEditor(); message('Choose an image, or select “No icon”, before saving.'); return; }
        request(draft);
      });
      footer.appendChild(save); dialog.appendChild(footer);
      dialog.addEventListener('click',function(event) { event.stopPropagation(); });
      dialog.addEventListener('keydown',function(event) { event.stopPropagation(); });
      dialog.addEventListener('cancel',function(event) { event.preventDefault(); close(); });
      dialog.addEventListener('paste',function(event) {
        var item=Array.from(event.clipboardData.items).find(function(part) { return part.kind === 'file' && part.type.startsWith('image/'); });
        if(item) { event.preventDefault(); loadImage(item.getAsFile()); }
      });
      document.body.appendChild(dialog); renderEditor(); preview(); refreshButtons(); dialog.showModal(); request();
    }
    return {open:open,receive:receive,isOpen:function() { return !!dialog; }};
  }
  window.HackBankButtonStudio={create:create};
})(window, document);
