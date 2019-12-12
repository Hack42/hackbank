var cachepixels={};
var cachetop={};
;(function($) {
    $.fn.textfill = function(options) {
        var fontSize = options.maxFontPixels;
        var ourText = $('span:visible:first', this);
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
        var mytop=(maxHeight-textHeight)/2
        this.css('top',mytop);
        cachetop[this.text()]=mytop;
        return this;
    }
})(jQuery);

$( document ).ready(function() {
  function runmsg(path, msg) {
    if(path.endsWith("/POWER")) {
       device = path.split("/")[2];
       $("#"+device).css("background-color",msg == "ON" ? "red" : "green");
    }
    if(path.endsWith("/LWT")) {
       device = path.split("/")[2];
       msg == "Online" ?  $("#"+device+" > span.dot").hide() : $("#"+device+" > span.dot").show();
    }
    if(path.endsWith("/status") & path.startsWith("hack42/tele/")) {
       console.log(path);
       device = path.split("/")[2];
       msg == "online" ?  $("#"+device+" > span.dot").hide() : $("#"+device+" > span.dot").show();
    }
    if(path == "hack42/sound/volume") {
        val = JSON.parse(msg)[0];
        $('.input-range').val( val / 10);
    }
    if(path.endsWith("/GBpower") || path.endsWith("/GBvolt")) {
       device = path.split("/")[2];
       $("#"+device).text(msg);
    }
    if(path.endsWith("/co")) {
       device = path.split("/")[3];
       $("#"+device+"co").text(msg);
    }
    if(path.endsWith("/humid")) {
       device = path.split("/")[3];
       $("#"+device+"humid").text(msg);
    }
    if(path.startsWith("hack42/sensors/1wire/")) {
       device = path.split("/")[3];
       $("#"+device).text(msg);
    }
    if(path == 'hack42/stookkelder/hoofdgebouwvalve' ) {
       $("#gebouw").css("background-color",msg != "closed" ? "red" : "green");
    }
    if(path == 'hack42/stookkelder/barrakkenvalve' ) {
       $("#barakken").css("background-color",msg != "closed" ? "red" : "green");
    }
  }

  $( ".Knopjetext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
  });

  var source = new EventSource('stream.php');
  source.onmessage = function(event) {
    var msg=JSON.parse(event.data);
    var path=msg[0];
    var msg=msg[1];
    //if(path=="startup") postmsg('startup',1);
    runmsg(path,msg);
  }

  $("body" ).on( "click",'div.powerswitch', function() {
    $.ajax({
      type: "POST",
      url: "cmd.php",
      data: {"action": "toggle", "device": this.id},
      success: function(data) {
      }
    });
  });
  $('.input-range').on('input', function(){
    $.ajax({
      type: "POST",
      url: "cmd.php",
      data: {"action": "volume", "value": this.value},
      success: function(data) {
      }
    });
  }); 

});
