(function(window, document) {
  var IDLE_MS=60000;
  var EVENTS=['pointerdown','pointerup','pointermove','click','keydown','input','change','wheel','touchstart','touchmove'];

  function watch(options) {
    var lastActivity=Date.now();
    var timer=null;
    var stopped=false;
    var checking=false;
    function activity() { lastActivity=Date.now(); }
    function schedule(delay) {
      window.clearTimeout(timer);
      timer=window.setTimeout(check,delay);
    }
    function check() {
      if(stopped || checking) return;
      checking=true;
      try {
        var remaining=IDLE_MS-(Date.now()-lastActivity);
        if(remaining > 0) { schedule(remaining); return; }
        var active=document.activeElement;
        var blocked=document.hidden || !document.hasFocus() ||
          (options.isPaused && options.isPaused()) ||
          (active && active.tagName === 'IFRAME') || document.querySelector('dialog[open]');
        if(blocked) { schedule(1000); return; }
        var input=options.getInput();
        if(input && active !== input) input.focus({preventScroll:true});
        schedule(IDLE_MS);
      } finally {
        checking=false;
      }
    }
    EVENTS.forEach(function(event) { document.addEventListener(event,activity,{capture:true,passive:true}); });
    window.addEventListener('blur',activity);
    window.addEventListener('focus',check);
    document.addEventListener('visibilitychange',check);
    schedule(IDLE_MS);
    return {
      stop:function() {
        stopped=true; window.clearTimeout(timer);
        EVENTS.forEach(function(event) { document.removeEventListener(event,activity,true); });
        window.removeEventListener('blur',activity);
        window.removeEventListener('focus',check);
        document.removeEventListener('visibilitychange',check);
      },
    };
  }
  window.HackBankIdleFocus={watch:watch};
})(window, document);
