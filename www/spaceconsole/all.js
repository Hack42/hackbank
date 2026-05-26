var cachepixels = {};
var cachetop = {};
(function($) {
    $.fn.textfill = function(options) {
        var fontSize = options.maxFontPixels;
        var maxHeight = $(this).parent().height();
        var maxWidth = $(this).parent().width();
        var textHeight;
        var textWidth;
        if(cachepixels[this.text()]>0) {
            this.css('font-size', cachepixels[this.text()]+'vh');
            this.css('top',cachetop[this.text()]);
            return this;
        }
        do {
            this.css('font-size', fontSize+'vh');
            textHeight = this.height();
            textWidth = this.width();
            cachepixels[this.text()]=fontSize;
            fontSize = fontSize - 0.9;
        } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 0.5);
        textHeight = this.height();
        var mytop = (maxHeight - textHeight) / 2;
        this.css('top',mytop);
        cachetop[this.text()]=mytop;
        return this;
    }
})(jQuery);

$( document ).ready(function() {
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
    if(path.endsWith("/POWER")) {
       var device = path.split("/")[2];
       $("#"+device).css("background-color",msg === "ON" ? "red" : "green");
    }
    if(path.endsWith("/LWT")) {
       var lwtDevice = path.split("/")[2];
       msg === "Online" ?  $("#"+lwtDevice+" > span.dot").hide() : $("#"+lwtDevice+" > span.dot").show();
    }
    if(path.endsWith("/status") && path.startsWith("hack42/tele/")) {
       console.log(path);
       var statusDevice = path.split("/")[2];
       msg === "online" ?  $("#"+statusDevice+" > span.dot").hide() : $("#"+statusDevice+" > span.dot").show();
    }
    if(path === "hack42/sound/volume") {
        var val = JSON.parse(msg)[0];
        $('.input-range').val(val / 10);
    }
    if(path.endsWith("/GBpower") || path.endsWith("/GBvolt")) {
       var gbDevice = path.split("/")[2];
       $("#"+gbDevice).text(msg);
    }
    if(path.endsWith("/co")) {
       var coDevice = path.split("/")[3];
       $("#"+coDevice+"co").text(msg);
    }
    if(path.endsWith("/humid")) {
       var humidDevice = path.split("/")[3];
       $("#"+humidDevice+"humid").text(msg);
    }
    if(path.startsWith("hack42/sensors/1wire/")) {
       var sensorDevice = path.split("/")[3];
       $("#"+sensorDevice).text(msg);
    }
    if(path === 'hack42/stookkelder/hoofdgebouwvalve' ) {
       $("#gebouw").css("background-color",msg !== "closed" ? "red" : "green");
    }
    if(path === 'hack42/stookkelder/barrakkenvalve' ) {
       $("#barakken").css("background-color",msg !== "closed" ? "red" : "green");
    }
  }

  $( ".Knopjetext:visible" ).each(function() {
         $(this).textfill({maxFontPixels: 5});
  });

  var source = new EventSource('stream.php');
  source.onmessage = function(event) {
    var data = JSON.parse(event.data);
    var path = data[0];
    var msg = data[1];
    //if(path=="startup") postmsg('startup',1);
    runmsg(path,msg);
  }

  $("body" ).on( "click",'div.powerswitch', function() {
    postCommand({
      "action": "toggle",
      "device": this.id,
    });
  });
  $('.input-range').on('input', function(){
    postCommand({
      "action": "volume",
      "value": this.value,
    });
  }); 

});
