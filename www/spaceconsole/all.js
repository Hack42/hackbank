(function(window, document) {
  var cachepixels = {};
  var cachetop = {};

  function allElements(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function setDisplay(element, value) {
    if(element) element.style.display = value;
  }

  function setBackgroundColor(id, value) {
    var element = byId(id);
    if(element) element.style.backgroundColor = value;
  }

  function setText(id, value) {
    var element = byId(id);
    if(element) element.textContent = value;
  }

  function dotForDevice(device) {
    var element = byId(device);
    return element ? element.querySelector("span.dot") : null;
  }

  function textfillElement(element, options) {
    var fontSize = options.maxFontPixels;
    var parent = element.parentElement;
    var maxHeight = parent ? parent.offsetHeight : 0;
    var maxWidth = parent ? parent.offsetWidth : 0;
    var text = element.textContent;
    var textHeight;
    var textWidth;

    if(cachepixels[text] > 0) {
      element.style.fontSize = cachepixels[text] + 'vh';
      element.style.top = cachetop[text];
      return element;
    }

    do {
      element.style.fontSize = fontSize + 'vh';
      textHeight = element.offsetHeight;
      textWidth = element.offsetWidth;
      cachepixels[text] = fontSize;
      fontSize = fontSize - 0.9;
    } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 0.5);

    textHeight = element.offsetHeight;
    cachetop[text] = ((maxHeight - textHeight) / 2) + 'px';
    element.style.top = cachetop[text];
    return element;
  }

  function postCommand(data) {
    fetch("cmd.php", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(data),
    }).catch(function(error) {
      console.error("Command failed", error);
    });
  }

  function runmsg(path, msg) {
    var parts = path.split("/");

    if(path.endsWith("/POWER")) {
      setBackgroundColor(parts[2], msg === "ON" ? "red" : "green");
    }
    if(path.endsWith("/LWT")) {
      setDisplay(dotForDevice(parts[2]), msg === "Online" ? "none" : "");
    }
    if(path.endsWith("/status") && path.startsWith("hack42/tele/")) {
      console.log(path);
      setDisplay(dotForDevice(parts[2]), msg === "online" ? "none" : "");
    }
    if(path === "hack42/sound/volume") {
      var val = JSON.parse(msg)[0];
      allElements('.input-range').forEach(function(input) {
        input.value = val / 10;
      });
    }
    if(path.endsWith("/GBpower") || path.endsWith("/GBvolt")) {
      setText(parts[2], msg);
    }
    if(path.endsWith("/co")) {
      setText(parts[3] + "co", msg);
    }
    if(path.endsWith("/humid")) {
      setText(parts[3] + "humid", msg);
    }
    if(path.startsWith("hack42/sensors/1wire/")) {
      setText(parts[3], msg);
    }
    if(path === 'hack42/stookkelder/hoofdgebouwvalve' ) {
      setBackgroundColor("gebouw", msg !== "closed" ? "red" : "green");
    }
    if(path === 'hack42/stookkelder/barrakkenvalve' ) {
      setBackgroundColor("barakken", msg !== "closed" ? "red" : "green");
    }
  }

  function connectStream() {
    var source = new EventSource('stream.php');
    source.onmessage = function(event) {
      var data = JSON.parse(event.data);
      runmsg(data[0], data[1]);
    };
    return source;
  }

  function bindEvents() {
    document.body.addEventListener("click", function(event) {
      var button = event.target.closest && event.target.closest('div.powerswitch');
      if(!button) return;
      postCommand({
        action: "toggle",
        device: button.id,
      });
    });
    document.body.addEventListener("input", function(event) {
      if(!event.target.matches || !event.target.matches('.input-range')) return;
      postCommand({
        action: "volume",
        value: event.target.value,
      });
    });
  }

  function init() {
    allElements(".Knopjetext").forEach(function(element) {
      textfillElement(element, {maxFontPixels: 5});
    });
    connectStream();
    bindEvents();
  }

  window.SpaceConsole = {
    bindEvents: bindEvents,
    connectStream: connectStream,
    init: init,
    postCommand: postCommand,
    runmsg: runmsg,
    textfillElement: textfillElement,
  };

  document.addEventListener("DOMContentLoaded", init);
})(window, document);
