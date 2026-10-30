(function(window, document) {
  var COLORS=['#ffbf69','#f05c86','#55cdb6','#7dafff','#bc8dff','#ffe17a'];

  function create() {
    var canvas=null;
    var context=null;
    var particles=[];
    var frame=null;
    var previous=null;

    function resize() {
      var scale=Math.min(window.devicePixelRatio || 1,2);
      canvas.width=Math.round(window.innerWidth*scale);
      canvas.height=Math.round(window.innerHeight*scale);
      context.setTransform(scale,0,0,scale,0,0);
    }
    function clear() {
      if(frame !== null) window.cancelAnimationFrame(frame);
      window.removeEventListener('resize',resize);
      if(canvas) canvas.remove();
      canvas=null; context=null; particles=[]; frame=null; previous=null;
    }
    function draw(now) {
      var seconds=previous === null ? 0 : Math.min(.05,(now-previous)/1000);
      previous=now;
      context.clearRect(0,0,window.innerWidth,window.innerHeight);
      particles=particles.filter(function(particle) {
        var age=(now-particle.created)/1000;
        particle.x+=(particle.drift+Math.sin(age*3+particle.phase)*12)*seconds;
        particle.speed+=50*seconds;
        particle.y+=particle.speed*seconds;
        particle.rotation+=particle.spin*seconds;
        if(particle.y > window.innerHeight+20 || age > 14) return false;
        context.save();
        context.translate(particle.x,particle.y);
        context.rotate(particle.rotation);
        context.fillStyle=particle.color;
        context.globalAlpha=Math.min(1,Math.max(0,(window.innerHeight-particle.y)/80));
        var flutter=Math.max(.25,Math.abs(Math.cos(age*4+particle.phase)));
        context.fillRect(-particle.size/2,-particle.size/3,particle.size,particle.size*.65*flutter);
        context.restore();
        return true;
      });
      if(particles.length) frame=window.requestAnimationFrame(draw);
      else clear();
    }
    function burst(sale) {
      if(!canvas) {
        canvas=document.createElement('canvas');
        canvas.className='confetti-canvas';
        canvas.setAttribute('aria-hidden','true');
        context=canvas.getContext('2d');
        if(!context) { canvas=null; return; }
        resize();
        document.body.appendChild(canvas);
        window.addEventListener('resize',resize);
      }
      var count=sale ? 90 : 18;
      // Bound the work when barcode scans or commands arrive in quick succession.
      particles=particles.slice(-(360-count));
      for(var i=0; i<count; i++) {
        particles.push({
          x: Math.random()*window.innerWidth,
          y: -12-Math.random()*160,
          speed: 55+Math.random()*55,
          drift: (Math.random()-.5)*36,
          size: 4+Math.random()*4,
          rotation: Math.random()*Math.PI,
          spin: (Math.random()-.5)*5,
          phase: Math.random()*Math.PI*2,
          color: COLORS[Math.floor(Math.random()*COLORS.length)],
          created: window.performance.now(),
        });
      }
      if(frame === null) frame=window.requestAnimationFrame(draw);
    }
    return {burst: burst, clear: clear};
  }
  window.HackBankConfetti={create: create};
})(window, document);
