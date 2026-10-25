/* Ambient scenes and local shader adaptations share one WebGL context. */
(function(window, document) {
  var WIDTH=320, HEIGHT=128, FRAME_MS=1000/24;
  var VERTEX='attribute vec2 position; varying vec2 uv; void main() { uv=position*.5+.5; gl_Position=vec4(position,0.,1.); }';
  var HEADER=`
    #ifdef GL_FRAGMENT_PRECISION_HIGH
    precision highp float;
    #else
    precision mediump float;
    #endif
    varying vec2 uv;
    uniform vec2 resolution;
    uniform float time, intensity;
    uniform vec3 color0, color1, color2;
    vec3 palette(float n) {
      return mix(mix(color0,color1,smoothstep(0.,.5,n)),color2,smoothstep(.5,1.,n));
    }
    float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
  `;
  var SCENES={
    'shader-lights':`
      vec3 scene() {
        vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.);
        vec3 light=color0*.12;
        for(int i=0;i<5;i++) {
          float n=float(i);
          vec2 center=vec2(sin(time*.19+n*1.7)*resolution.x/resolution.y*.34,cos(time*.23+n*2.1)*.28);
          vec2 delta=p-center;
          light+=palette(n*.25)*(.025/(dot(delta,delta)+.025))*.85;
        }
        return light;
      }
    `,
    'shader-snow':`
      vec3 scene() {
        vec3 sky=mix(color0,color1,uv.y*.65)*.55;
        float snow=0.;
        for(int i=0;i<4;i++) {
          float layer=float(i), scale=5.+layer*3.;
          vec2 p=uv*vec2(resolution.x/resolution.y,1.)*scale;
          p+=vec2(time*.11/(layer+1.),time*(.22+layer*.09));
          vec2 cell=floor(p);
          vec2 center=vec2(hash(cell+layer),hash(cell+layer+17.));
          vec2 flake=fract(p)-(.2+.6*center);
          flake.x+=sin(time*.3+center.y*6.283)*.1;
          snow+=(1.-smoothstep(.025,.07,length(flake)))*(.35+layer*.18);
        }
        return sky+color2*snow;
      }
    `,
    'shader-cubes':`
      vec3 scene() {
        vec2 p=uv*vec2(resolution.x/resolution.y,1.)*2.4;
        p.x+=mod(floor(p.y),2.)*.5;
        vec2 cell=floor(p), q=(fract(p)-.5)*1.8;
        // A quarter turn travels from the bottom left across successive cells.
        float phase=time*.22-cell.x*.15-cell.y*.19;
        float angle=(floor(phase)+smoothstep(.12,.84,fract(phase)))*1.570796;
        float c=cos(angle), s=sin(angle);
        mat3 rotation=mat3(c,0.,-s,0.,1.,0.,s,0.,c);
        vec3 camera=normalize(vec3(1.4,1.1,2.3));
        vec3 right=normalize(vec3(camera.z,0.,-camera.x)), up=cross(camera,right);
        vec3 origin=rotation*(camera*3.+right*q.x+up*q.y);
        vec3 ray=rotation*(-camera), inverse=1./(ray+vec3(.00001));
        vec3 a=(-.36-origin)*inverse, b=(.36-origin)*inverse;
        vec3 nearPlane=min(a,b), farPlane=max(a,b);
        float entry=max(nearPlane.x,max(nearPlane.y,nearPlane.z));
        float exit=min(farPlane.x,min(farPlane.y,farPlane.z));
        vec3 background=color0*.18;
        if(entry>exit) return background;
        vec3 hit=origin+ray*entry, extent=abs(hit), normal=vec3(0.);
        if(extent.x>extent.y && extent.x>extent.z) normal.x=sign(hit.x);
        else if(extent.y>extent.z) normal.y=sign(hit.y);
        else normal.z=sign(hit.z);
        vec3 face=mix(color0*.65+color1*.2,color1,abs(normal.x));
        face=mix(face,color2,abs(normal.y));
        float light=.55+.45*max(0.,dot(normal*rotation,normalize(vec3(-.4,.8,1.))));
        return mix(background,face*light,smoothstep(0.,.035,exit-entry));
      }
    `,
    'shader-synthwave':`
      float peak(vec2 cell) { return .25+hash(cell)*3.6; }
      float terrain(vec2 p) {
        vec2 grid=p*.65, cell=floor(grid), f=fract(grid);
        float a=peak(cell), b=peak(cell+vec2(1.,0.));
        float c=peak(cell+vec2(0.,1.)), d=peak(cell+vec2(1.,1.));
        float height=f.x+f.y<1. ? a+(b-a)*f.x+(c-a)*f.y : d+(c-d)*(1.-f.x)+(b-d)*(1.-f.y);
        return height*smoothstep(1.,3.8,abs(p.x))-.35;
      }
      vec3 scene() {
        float horizon=.48;
        vec3 sky=color0*.28+color1*exp(-abs(uv.y-horizon)*6.)*.32;
        vec2 sun=(uv-vec2(.72,.73))*vec2(resolution.x/resolution.y,1.);
        float disc=1.-smoothstep(.225,.235,length(sun));
        float stripes=smoothstep(.08,.18,fract(sun.y*22.));
        disc*=mix(stripes,1.,step(0.,sun.y));
        sky=mix(sky,mix(color1,color2,clamp((uv.y-.4)*2.8,0.,1.)),disc);
        vec3 camera=vec3(0.,1.1,time*2.2);
        vec3 ray=normalize(vec3((uv.x-.5)*resolution.x/resolution.y,(uv.y-horizon)*1.25,.95));
        float distance=.1;
        for(int i=0;i<36;i++) {
          vec3 point=camera+ray*distance;
          float gap=point.y-terrain(point.xz);
          if(gap<.025) {
            vec2 f=fract(point.xz*.65), lines=min(f,1.-f);
            float hills=smoothstep(1.,3.8,abs(point.x));
            float edge=min(lines.x,lines.y);
            edge=min(edge,mix(1.,abs(f.x+f.y-1.)*.707,hills));
            float width=.012+distance*.0008;
            float neon=1.-smoothstep(width,width*2.,edge);
            float roadEdge=1.-smoothstep(.025,.07,abs(abs(point.x)-1.15));
            vec3 ground=color0*.18+color1*(.12*hills+neon*.85)+color2*roadEdge*.45;
            return mix(sky,ground,exp(-distance*.038));
          }
          distance+=max(.055,gap*.45);
          if(distance>38.) break;
        }
        return sky+color1*exp(-abs(uv.y-horizon)*140.)*.5;
      }
    `,
  };
  Object.assign(SCENES,window.HackBankExtraButtonShaders || {});
  var FOOTER='void main() { gl_FragColor=vec4(clamp(mix(palette(uv.y*.6+uv.x*.4),scene(),intensity),0.,1.),1.); }';
  var source=null, gl=null, programs={}, state='idle';
  var targets=new Map(), observer=null, sizes=null, mutations=null, observing=false;
  var motion=null, timer=null, frame=null;

  function seedFor(user) {
    var hash=2166136261;
    for(var index=0;index<user.length;index++) hash=Math.imul(hash^user.charCodeAt(index),16777619);
    return (hash>>>0)/4294967296;
  }
  function palette(background) {
    var stops=background.gradient.stops.slice().sort(function(a,b) { return a.position-b.position; });
    return [stops[0],stops[Math.floor((stops.length-1)/2)],stops[stops.length-1]];
  }
  function announce(value) {
    state=value;
    document.dispatchEvent(new window.CustomEvent('buttonshaderstatus'));
  }
  function stop() {
    window.clearTimeout(timer); timer=null;
    if(frame !== null) window.cancelAnimationFrame(frame);
    frame=null;
  }
  function mark(target,value) { target.canvas.dataset.shaderState=value; }
  function fallback() {
    stop(); targets.forEach(function(target) { mark(target,'fallback'); });
  }
  function initialize() {
    if(state !== 'idle') return state === 'ready';
    try {
      if(!source) {
        source=document.createElement('canvas'); source.width=WIDTH; source.height=HEIGHT;
        source.addEventListener('webglcontextlost',function(event) {
          event.preventDefault(); announce('lost'); fallback();
        });
        source.addEventListener('webglcontextrestored',function() {
          programs={}; gl=null; state='idle';
          if(initialize()) schedule();
        });
      }
      // Keep the small shared buffer valid while Firefox copies it into each
      // button. Discarding it can expose empty frames on some GPU backends.
      gl=source.getContext('webgl',{alpha:false,depth:false,stencil:false,antialias:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
      if(!gl) throw new Error('WebGL unavailable');
      var buffer=gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
      announce('ready'); return true;
    } catch(_error) { announce('unavailable'); fallback(); return false; }
  }
  function program(kind) {
    if(Object.prototype.hasOwnProperty.call(programs,kind)) return programs[kind];
    var vertex=gl.createShader(gl.VERTEX_SHADER), fragment=gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(vertex,VERTEX); gl.compileShader(vertex);
    gl.shaderSource(fragment,HEADER+SCENES[kind]+FOOTER); gl.compileShader(fragment);
    var handle=gl.createProgram();
    gl.attachShader(handle,vertex); gl.attachShader(handle,fragment);
    gl.bindAttribLocation(handle,0,'position'); gl.linkProgram(handle);
    gl.deleteShader(vertex); gl.deleteShader(fragment);
    if(!gl.getProgramParameter(handle,gl.LINK_STATUS)) {
      console.warn('Ambient button shader unavailable:',kind,gl.getProgramInfoLog(handle));
      gl.deleteProgram(handle); programs[kind]=null;
      document.dispatchEvent(new window.CustomEvent('buttonshaderstatus'));
      return null;
    }
    var uniforms={};
    ['resolution','time','intensity','color0','color1','color2'].forEach(function(name) { uniforms[name]=gl.getUniformLocation(handle,name); });
    programs[kind]={handle:handle,uniforms:uniforms}; return programs[kind];
  }
  function measure(target,width,height) {
    if(width <= 0 || height <= 0) return;
    var scale=Math.min(1,WIDTH/width,HEIGHT/height);
    target.width=Math.max(1,Math.round(width*scale)); target.height=Math.max(1,Math.round(height*scale));
    if(target.canvas.width !== target.width) target.canvas.width=target.width;
    if(target.canvas.height !== target.height) target.canvas.height=target.height;
  }
  function visibleTargets() {
    var dialog=document.querySelector('dialog[open]');
    var quiet=document.body.classList.contains('button-styles-off');
    return Array.from(targets.values()).filter(function(target) {
      return target.canvas.isConnected && target.visible && target.width && target.height && (!dialog || dialog.contains(target.canvas))
        && (!quiet || !target.canvas.closest('.magic-button') || target.canvas.closest('.magic-preview'));
    });
  }
  function schedule() {
    if(frame !== null || timer !== null || document.hidden || state !== 'ready') return;
    frame=window.requestAnimationFrame(draw);
  }
  function draw(timestamp) {
    frame=null;
    if(document.hidden || state !== 'ready') return;
    var visible=visibleTargets();
    if(!visible.length) return;
    var groups=new Map();
    visible.forEach(function(target) {
      var key=target.key+':'+target.width+':'+target.height;
      if(!groups.has(key)) groups.set(key,[]);
      groups.get(key).push(target);
    });
    var rendered=false;
    try {
      groups.forEach(function(group) {
        var target=group[0], settings=target.settings, compiled=program(settings.kind);
        if(!compiled) { group.forEach(function(item) { mark(item,'fallback'); }); return; }
        rendered=true;
        gl.viewport(0,0,target.width,target.height); gl.useProgram(compiled.handle);
        var uniforms=compiled.uniforms;
        gl.uniform2f(uniforms.resolution,target.width,target.height);
        gl.uniform1f(uniforms.time,(motion.matches ? 12 : timestamp/1000*24/settings.speed)+target.seed*120);
        gl.uniform1f(uniforms.intensity,settings.intensity/100);
        target.colors.forEach(function(color,index) { gl.uniform3fv(uniforms['color'+index],color); });
        gl.drawArrays(gl.TRIANGLES,0,3);
        group.forEach(function(item) {
          item.context.drawImage(source,0,HEIGHT-item.height,item.width,item.height,0,0,item.width,item.height);
          mark(item,motion.matches ? 'still' : 'animated');
        });
      });
    } catch(_error) { announce('unavailable'); fallback(); return; }
    if(rendered && !motion.matches) timer=window.setTimeout(function() { timer=null; schedule(); },FRAME_MS);
  }
  function cleanup() {
    targets.forEach(function(target,canvas) {
      if(canvas.isConnected) return;
      if(observer) observer.unobserve(canvas);
      if(sizes) sizes.unobserve(canvas);
      targets.delete(canvas);
    });
    if(!targets.size) { stop(); mutations.disconnect(); observing=false; }
    else schedule();
  }
  function watch() {
    if(!motion) {
      motion=window.matchMedia('(prefers-reduced-motion: reduce)');
      motion.addEventListener('change',function() { stop(); schedule(); document.dispatchEvent(new window.CustomEvent('buttonshaderstatus')); });
      document.addEventListener('visibilitychange',function() { stop(); if(!document.hidden) schedule(); });
      document.addEventListener('buttonstyleschange',function() { stop(); schedule(); });
      if(window.IntersectionObserver) observer=new window.IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          var target=targets.get(entry.target);
          if(target) target.visible=entry.isIntersecting && entry.intersectionRect.width > 0 && entry.intersectionRect.height > 0;
        });
        schedule();
      });
      sizes=new window.ResizeObserver(function(entries) {
        entries.forEach(function(entry) {
          var target=targets.get(entry.target);
          if(target) measure(target,entry.contentRect.width,entry.contentRect.height);
        });
        schedule();
      });
      mutations=new window.MutationObserver(cleanup);
    }
    if(!observing) { mutations.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['open']}); observing=true; }
  }
  function attach(layer,background,user) {
    var canvas=layer.querySelector('.magic-shader-canvas');
    if(!Object.prototype.hasOwnProperty.call(SCENES,background.kind)) {
      if(canvas) canvas.remove();
      return;
    }
    var previous=canvas && targets.get(canvas);
    if(!canvas) {
      canvas=document.createElement('canvas'); canvas.className='magic-shader-canvas';
      canvas.setAttribute('aria-hidden','true'); canvas.dataset.shaderState='fallback';
      layer.appendChild(canvas);
    }
    var context=canvas.getContext('2d',{alpha:false});
    if(!context) return;
    watch();
    var settings=JSON.parse(JSON.stringify(background));
    var colors=palette(settings).map(function(stop) {
      return [1,3,5].map(function(offset) { return parseInt(stop.color.slice(offset,offset+2),16)/255; });
    });
    var seed=seedFor(String(user || ''));
    var target={canvas:canvas,context:context,settings:settings,colors:colors,seed:seed,key:JSON.stringify([settings.kind,colors,settings.speed,settings.intensity,seed]),visible:previous ? previous.visible : !observer,width:previous ? previous.width : 0,height:previous ? previous.height : 0};
    targets.set(canvas,target);
    var rect=layer.getBoundingClientRect(); measure(target,rect.width,rect.height);
    if(!previous) {
      if(observer) observer.observe(canvas);
      sizes.observe(canvas);
    }
    if(initialize()) schedule();
  }
  window.HackBankButtonShaders={attach:attach,palette:palette,status:function(kind) { return programs[kind] === null ? 'unavailable' : state; }};
})(window, document);
