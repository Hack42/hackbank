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
            fontSize = fontSize - 0.5;
        } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 0.5);
        textHeight = this.height();
        var mytop=(maxHeight-textHeight)/2
        this.css('top',mytop);
        cachetop[this.text()]=mytop;
        return this;
    }
})(jQuery);

$( document ).ready(function() {
  var session='main';
  if (window.location.hash!='') {
    session=window.location.hash.replace('#','');
  }
  var prods={};
  var stock={};
  var accounts={};
  var commands={};
  var groups={};
  var nobcgroup={};
  var members=[];
  var history=[];
  var tabenable=0;
  var question="";
  var locked=0;

  function postmsg(topic,msg) {
    $.post( "post.php", { topic: 'session/'+session+'/'+topic, msg: msg } );
  }
  function build_receipt(msg) {
    var parts=JSON.parse(msg);
    $('#Receipt').empty();
    var counter=0;
    $.each(parts, function(idx,stuff) {
      counter++;
      $('#Receipt').append(
                    $('<div>',{class: 'Itemline'})
		      .append($('<span>',{class: 'Product', text: stuff.description}))
		      .append($('<span>',{class: 'Times', text: stuff.count}))
		      .append($('<span>',{class: 'LoseOrGain', text: stuff.Lose ? "LOSE" : "GAIN"}))
		      .append($('<span>',{class: 'ItemEuro'}))
		      .append($('<div>',{class: 'ItemAmount', text: stuff.total.toFixed(2)}))
		    );
    });
    $('#Receipt').scrollTop($('#Receipt')[0].scrollHeight);
    if(counter==0) {
      $('#Receipt').append($('<div>',{class: 'welcome', html: "Welcome to Hack42 Bank HTML5 Interface"}));
    }
    $('#Receipt2').empty();
    $('.Itemline').clone().appendTo('#Receipt2');
    $('#Receipt2').scrollTop($('#Receipt2')[0].scrollHeight);
    if ($('#Receipt2').is(':empty')){
       $('#Receipt2').append($('<img>',{src: 'images/Hack42.png', width: '100%'}).css({'top': '12vh','position': 'absolute'}))
    }
  }
  function build_totals(msg) {
    var parts=JSON.parse(msg);
    $('#Totals').empty();
    var counter=0;
    $.each(parts, function(idx,stuff) {
      counter++;
      $('#Totals').append(
                    $('<div>',{class: 'Userline Total_'+stuff.user})
		      .append($('<span>',{class: 'UserName', text: stuff.user ? stuff.user : '-$you-' }))
		      .append($('<span>',{class: 'GainOrLose',text: (stuff.amount<0) ? 'LOSE' : 'GAIN'}))
		      .append($('<span>',{class: 'TotalEuro'}))
		      .append($('<span>',{class: 'Totalamount',text: (stuff.amount ? stuff.amount : 0-stuff.amount).toFixed(2) }))
		    );
    });
    $('#Totals').scrollTop($('#Totals')[0].scrollHeight);
    if(counter==0) {
      $('#Totals').append($('<div>',{class: 'welcome', html: "Scan a product or choose a button from below"}));
    }
  }
  function run_infobox(name,msg) {
    json=JSON.parse(msg);
    newsaldo=json.amount;
    $('.infoboxes .Total_'+name).append($('<span>',{class: 'NowHas',text: "Now Has"}));
    $('.infoboxes .Total_'+name).append($('<span>',{class: 'NewSaldo',text: newsaldo.toFixed(2)}));
  }
  function setupaccounts(name,msg) {
    accounts[name]=JSON.parse(msg);
  }
  function setupcommands(msg) {
    commands=JSON.parse(msg);
  }
  function setupstock(name,msg) {
    stock[name]=msg
  }
  function setupproducts(name,msg) {
    prods[name]=JSON.parse(msg);
    groups={};
    $.each(prods, function(idx,stuff) {
      groups[stuff.group]++;
      barcode=0;
      $.each(stuff.aliases, function(idx2,stuff2) {
        if(stuff2>9999999) barcode=1;
      })
      if(barcode==0) {
        nobcgroup[name]=prods[name];
      }
    });
  }
  function productstobuttons(products) {
    var buttons=[];
    Object.keys(products).sort().forEach(function(v, i) {
      buttons.push({'text': v,'display': v, class: v});
    });
    return buttons;
  }
  function commandstobuttons() {
    var buttons=[];
    Object.keys(commands).sort().forEach(function(v, i) {
      buttons.push({'text': v,'display': commands[v], class: v});
    });
    return buttons;
  }
  function mycomparator(a,b) {
    var alc = a.toLowerCase(), blc = b.toLowerCase();
    return alc > blc ? 1 : alc < blc ? -1 : 0;
  }
  function compare_text(a,b) {
    if (a.text < b.text)
      return -1;
    else if (a.text > b.text)
      return 1;
    else 
      return 0;
  }
  function compare_text_rev(a,b) {
    if (a.text > b.text)
      return -1;
    else if (a.text < b.text)
      return 1;
    else 
      return 0;
  }
  function compare_display(a,b) {
    if (a.display < b.display)
      return -1;
    else if (a.display > b.display)
      return 1;
    else 
      return 0;
  }
  function compare_display_rev(a,b) {
    if (a.display > b.display)
      return -1;
    else if (a.display < b.display)
      return 1;
    else 
      return 0;
  }
  function accountstobuttons(accounts,type) {
    var buttons=[];
    Object.keys(accounts).sort(mycomparator).forEach(function(v, i) {
      if($.inArray(v,members)!=-1 & type=='m' || ( $.inArray(v,members)==-1 & type=='o')) {
        var extraclass=v;
        if(accounts[v].amount < -13.37) {
          extraclass=v+" rood";
        } else if(accounts[v].amount < 0) {
          extraclass=v+" orange";
        }
        buttons.push({'text': v,'display': v, rightclass: extraclass, right: accounts[v].amount.toFixed(2), 'fill': true});
      }
    });
    //console.log(buttons);
    return buttons;
  }
  function allproductstobuttons() {
    var buttons=[];
    $.each(prods,function(v,i) {
      button={'text': v,'display': prods[v].description,'right': prods[v].price.toFixed(2), rightclass:"green", class: v, aliases: prods[v].aliases}
      if(stock[v]!=undefined) {
        button['left']=stock[v];
        button['leftclass']='orange';
      }
      buttons.push(button);
    });
    return buttons;
  }
  function productgrouptobuttons(group) {
    var buttons=[];
    var thisprods={};
    $.each(prods, function(idx,stuff) {
      if(stuff.group==group) thisprods[idx]=1;
    });
    Object.keys(thisprods).sort().forEach(function(v,i) {
      button={'text': v,'display': prods[v].description,'right': prods[v].price.toFixed(2), rightclass:"green", class: v}
      if(stock[v]!=undefined) {
        button['left']=stock[v];
        button['leftclass']='orange';
      }
      buttons.push(button);
    });
    return buttons;
  }

  function makepage_infobox() {
    $('#MainButtons').empty();
    $('#TopButtons').empty();
    $('#MainButtons').append($('<div>',{class: "infoboxes", id: "infoboxes"}));
    $('.Userline').clone().appendTo('#infoboxes');
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal ok",id: 'ok'}).append($('<span>',{class: "Knopjetext",text: "OK"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal undo",id: 'undo'}).append($('<span>',{class: "Knopjetext",text: "Undo"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal restore",id: 'restore'}).append($('<span>',{class: "Knopjetext",text: "Undo + Restore"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal bon",id: 'bon'}).append($('<span>',{class: "Knopjetext",text: "Bon"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal kassala",id: 'kassala'}).append($('<span>',{class: "Knopjetext",text: "Kassala"})));
    $( "#TopButtons .Knopjetext:visible" ).each(function( index, element ) {
       $(this).textfill({maxFontPixels: 5});
    });
  }
  function dokeys(keys) {
    $.each(keys, function(idx,val) {
      $('#keys')    .append($('<div>',{class: "Knopje Knop invoer small",id: val ,text: val}));
    });
  }
  function makepage_keyboard() {
    $('#MainButtons').empty();
    $('#TopButtons').empty();
    $('#MainButtons').append($('<div>',{class: "keys", id: "keys"}));

    keys=['!','@','#','$','%','^','&','*','(',')'];
    dokeys(keys);
    $('#keys').append($('<br>'))

    keys=['1','2','3','4','5','6','7','8','9','0'];
    dokeys(keys);
    $('#keys').append($('<br>'))

    keys=['q','w','e','r','t','y','u','i','o','p'];
    dokeys(keys);
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "backspace" ,text: "←"}));
    $('#keys').append($('<br>'))

    keys=['a','s','d','f','g','h','j','k','l'];
    dokeys(keys);
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "enter" ,text: "⏎"}));
    $('#keys').append($('<br>'))

    keys=['z','x','c','v','b','n','m'];
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    dokeys(keys);
    $('#keys').append($('<br>'))
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "space" ,text: " "}))
    $('#keys').append($('<br>'))

    keys=['-','=','+','_','`','~',',','.','/','<','>'];
    dokeys(keys);
    $('#keys').append($('<br>'))

    keys=["?",";","'",'\\',':','"','|','[',']','{','}'];
    dokeys(keys);
    $('#keys').append($('<br>'))
    showquestion();
    
  }
  function makepage_history() {
    $('#MainButtons').empty();
    $('#TopButtons').empty();
    $('#MainButtons').append($('<div>',{class: "lines", id: "lines"}));
    $.each(history,function(idx,val) {
       $('#lines').append($('<div>',{class: 'Outputline',id: idx, text: val}));
    });
    $('#lines').scrollTop($('#lines')[0].scrollHeight);
    showquestion();
  }
  function makepage_numbers() {
    $('#MainButtons').empty();
    $('#TopButtons').empty();
    $('#MainButtons').append($('<div>',{class: "numbers", id: "numbers"}));
    $('#numbers')    .append($('<div>',{class: "Knopje Knop invoer",id: 1 ,text: 1}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 2 ,text: 2}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 3 ,text: 3}))
                     .append($('<br>'))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 4 ,text: 4}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 5 ,text: 5}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 6 ,text: 6}))
                     .append($('<br>'))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 7 ,text: 7}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 8 ,text: 8}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 9 ,text: 9}))
                     .append($('<br>'))
                     .append($('<div>',{class: "Knopje Knop invoer",id: "." ,text: "."}))
                     .append($('<div>',{class: "Knopje Knop invoer",id: 0 ,text: 0}))
                     .append($('<div>',{class: "Knopje Knop invoer enter",id: "enter" ,text: "⏎"}));
    showquestion();
  }
  function makepages(extraclass,buttons) {
    var pagecount=1;
    $('#MainButtons').empty();
    $('#TopButtons').empty();
    $('#MainButtons').append($('<div>',{id: 'Page'+pagecount, class: 'Pagina'}));
    $('#TopButtons').append($('<div>',{class: "Knopje Button page",id: '1'}).append($('<span>',{class: "Paginatext",text: "Page 1"})));
    var counter=0;
    var donewpage=0;
    var first=1;
    var lastchar="";
    $.each(buttons, function(idx, stuff) {
      if(donewpage==1) {
        $('#'+pagecount+' .Paginatext').html($('#'+pagecount+' .Paginatext').html()+' - '+lastchar)
        pagecount++;
        $('#MainButtons').append($('<div>',{id: 'Page'+pagecount, class: 'Pagina'}).hide());
        $('#TopButtons').append($('<div>',{class: "Knopje Button page",id: pagecount}).append($('<span>',{class: "Paginatext",text: "Page "+pagecount})));
        counter=0;
        donewpage=0;
        first=1;
      }
      if(first==1) {
        $('#'+pagecount+' .Paginatext').html($('#'+pagecount+' .Paginatext').html()+'<br>'+stuff.display.charAt(0).toUpperCase())
        first=0;
      }
      txt=$('<span>',{class: "Buttontext ",text: stuff.display})
      knopje=$('<div>',{class: "Knopje Knop "+stuff.text+" "+extraclass + " " + stuff.class,id: stuff.text }).append(txt);
      if(stuff.right) {
        fullwidth=''
        if(!stuff.left && stuff.fill) {
          fullwidth=' fullwidthButton ';
        }
        knopje.append($('<span>',{class: "right extra "+fullwidth+stuff.rightclass,text: stuff.right}));
      }
      if(stuff.left) {
        knopje.append($('<span>',{class: "left extra "+stuff.leftclass,text: stuff.left}));
      }
      lastchar=stuff.display.charAt(0).toUpperCase();
      $('#Page'+pagecount).append(knopje)
      counter++;
      w=5;
      h=5;
      if(counter>=w*h) {
        donewpage=1;
      }
    });
    if(pagecount==1) {
      $(".page").remove();
      $( ".Buttontext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
      });
      showquestion();
    } else {
      $('#'+pagecount+' .Paginatext').html($('#'+pagecount+' .Paginatext').html()+' - '+lastchar)
      $( ".Paginatext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
      });
      $(".Pagina").each(function(index,element) {
        $('.Pagina').hide();
        $(this).show();
        $( ".Buttontext:visible" ).each(function( index, element ) {
           $(this).textfill({maxFontPixels: 5});
        });
        $('.Pagina').hide();
        $('#Page1').show();
      });
    }
  }
  function dobuttons(msg) {
    buttons=JSON.parse(msg);
    if(msg=='{}' && locked==0) {
      $('#Secondscreen').show();
      makepages('normal',accountstobuttons(accounts,'m'));
      $('#TopButtons').prepend($('<div>',{class: "Knopje Button normal cash",id: 'cash'}).append($('<span>',{class: "Paginatext",text: "cash"})));
      $( ".Paginatext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
      });
      focus();
      tabenable=1;
    } else if (buttons['special']=='custom') {
      $('#Secondscreen').show();
      if(buttons['sort']=="text") {
        buttons['custom'].sort(compare_text_rev);
      } else {
        buttons['custom'].sort(compare_display);
      }
      makepages('normal',buttons['custom']);
      focus();
      tabenable=0;
    } else if (buttons['special']=='accounts') {
      $('#Secondscreen').show();
      makepages('normal',accountstobuttons(accounts,'m'));
      $('#TopButtons').prepend($('<div>',{class: "Knopje Button normal cash",id: 'cash'}).append($('<span>',{class: "Paginatext",text: "cash"})));
      $( ".Paginatext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
      });
      focus();
      tabenable=2;
    } else if (buttons['special']=='accountsamount') {
      $('#Secondscreen').show();
      makepages('normal',accountstobuttons(accounts,'m'));
      $('#TopButtons').prepend($('<div>',{class: "Knopje Button shownumbers",id: 'shownumbers'}).append($('<span>',{class: "Paginatext",text: "Enter amount"})));
      $('#TopButtons').prepend($('<div>',{class: "Knopje Button normal cash",id: 'cash'}).append($('<span>',{class: "Paginatext",text: "cash"})));
      $( ".Paginatext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
      });
      focus();
      tabenable=2;

    } else if (buttons['special']=='numbers') {
      $('#Secondscreen').show();
      makepage_numbers();
      focus();
      tabenable=0;
    } else if (buttons['special']=='keyboard') {
      $('#Secondscreen').show();
      makepage_keyboard();
      focus();
      tabenable=0;
    } else if (buttons['special']=='infobox') {
      $('#Secondscreen').show();
      makepage_infobox();
      focus();
      tabenable=0;
    } else if (buttons['special']=='history') {
      $('#Secondscreen').show();
      makepage_history();
      focus();
      tabenable=0;
    } else if (buttons['special']=='products') {
      $('#Secondscreen').show();
      makepages('productgroups',productstobuttons(groups).sort(compare_display));
      focus();
      tabenable=1;
    }
  }
  function playsound(sound) {
    var audioElement = document.createElement('audio');
    audioElement.setAttribute('src', 'sounds/'+sound);
    audioElement.setAttribute('autoplay', 'autoplay');
    audioElement.load();
    audioElement.addEventListener("load", function() {
    audioElement.play();
    },true);
  }

  function showquestion() {
    if ($('#TopButtons').is(':empty')){
       $('#TopButtons').append($('<div>',{class: "Question",id: 'Question', text: question}))
    }
  }

  function runsession(SID,action,msg) {
     if(SID!=session) return;
     switch(action) {
         case 'message':
            $("#Zoek")[0].placeholder=msg;
            $('#Question').remove();
            question=msg;
            showquestion();
            $('#Log').append(  $('<div>',{class: 'lastlog Log',text: msg})  );
            $('#Log').scrollTop($('#Log')[0].scrollHeight);
            break;
         case 'receipt':
            build_receipt(msg);
            break;
         case 'totals':
            build_totals(msg);
            break;
         case 'log':
            $('.lastlog').remove();
            $('#Log').append(  $('<div>',{class: 'Log',text: msg})  );
            $('#Log').scrollTop($('#Log')[0].scrollHeight);
            break;
         case 'infobox':
            run_infobox(elms[6],msg);
            break;
         case 'accounts':
            setupaccounts(elms[5],msg);
            break;
         case 'products':
            setupproducts(elms[5],msg);
            break;
         case 'stock':
            setupstock(elms[5],msg);
            break;
         case 'history':
            history=JSON.parse(msg);
            break;
         case 'buttons':
            dobuttons(msg);
            break;
         case 'sound':
            playsound(msg);
            break;
         case 'members':
            members=JSON.parse(msg);
            break;
         case 'commands':
            setupcommands(msg);
            break;
     }
  }
  function runmsg(path,msg) {
    elms=path.split("/");
    //console.log(elms);
    if(elms.length<3) return;
    switch(elms[2]) {
      case 'session':
         if(elms.length<5) return;
         sessionID=elms[3];
         action=elms[4];
         runsession(sessionID,action,msg);
         break;
       case 'log':
         dolog(msg);
         break;
       default:
         break;
    }
  }
  var source = new EventSource('stream.php?session='+session);
  source.onmessage = function(event) {
    var msg=JSON.parse(event.data);
    var path=msg[0];
    var msg=msg[1];
    //if(path=="startup") postmsg('startup',1);
    runmsg(path,msg);
  } 

  $('#body').append($('<div>',{id: 'Firstscreen'}));
  $('#body').append($('<div>',{id: 'Secondscreen'}));

  $('#Firstscreen').append(  $('<div>',{id: 'Receipt', class: 'Receipt'}) );
  $('#Firstscreen').append(  $('<div>',{id: 'Totals', class: 'Totals'}) );
  $('#Firstscreen').append(  $('<div>',{id: 'Buttons', class: 'Buttons'}) );
  $('#Firstscreen').append(  $('<div>',{id: 'Log'}) );
  $('#Firstscreen').append(  $('<div>',{id: 'Invoer'}).append($('<input>',{id: 'Zoek',placeholder: "Starting network communication" }).attr('autocomplete','off')))
  $('#Secondscreen').append(  $('<div>',{id: 'LeftButtons', class: 'LeftButtons'}) );
  $('#Secondscreen').append(  $('<div>',{id: 'MainButtons', class: 'MainButtons'}) );
  $('#Secondscreen').append(  $('<div>',{id: 'TopButtons', class: 'RightButtons'}) );
  $('#Secondscreen').append(  $('<div>',{id: 'Receipt2'}) );
  $('#LeftButtons').append($('<div>',{class: "Knopje Button normal abort",id: 'abort'}).append($('<span>',{class: "Knopjetext",text: "Abort"})));
  $('#LeftButtons').append($('<div>',{class: "Knopje Button special",id: 'members'}).append($('<span>',{class: "Knopjetext",text: "Members"})));
  $('#LeftButtons').append($('<div>',{class: "Knopje Button special",id: 'otherusers'}).append($('<span>',{class: "Knopjetext",text: "Other Users"})));
  $('#LeftButtons').append($('<div>',{class: "Knopje Button special",id: 'products'}).append($('<span>',{class: "Knopjetext",text: "Products"})));
  $('#LeftButtons').append($('<div>',{class: "Knopje Button special",id: 'commands'}).append($('<span>',{class: "Knopjetext",text: "Commands"})));
  $('#LeftButtons').append($('<div>',{class: "Knopje Button sounds",id: 'sounds'}).append($('<span>',{class: "Knopjetext",text: "Sounds"})));
  $('#LeftButtons').append($('<div>',{class: "Knopje Button irc",id: 'irc'}).append($('<span>',{class: "Knopjetext",text: "IRC"})));
  //$('#LeftButtons').append($('<div>',{class: "Knopje Button back",id: 'back'}).append($('<span>',{class: "Knopjetext",text: "Back"})));
  $('#Buttons').append($('<div>',{class: "Knopje abort",id: 'abort'}).append($('<span>',{class: "Knopjetext",text: "Abort"})));
  $('#Buttons').append($('<div>',{class: "Knopje bon",id: 'bon'}).append($('<span>',{class: "Knopjetext",text: "Bon"})));
  $('#Buttons').append($('<div>',{class: "Knopje remove",id: 'remove'}).append($('<span>',{class: "Knopjetext",text: " Remove Item"})));
  $('#Buttons').append($('<div>',{class: "Knopje shame",id: 'shame'}).append($('<span>',{class: "Knopjetext",text: "Shame"})));
  $('#Buttons').append($('<div>',{class: "Knopje undo",id: 'undo'}).append($('<span>',{class: "Knopjetext",text: "Undo"})));
  $('#Buttons').append($('<div>',{class: "Knopje ok",id: 'ok'}).append($('<span>',{class: "Knopjetext",text: "OK"})));
  $('#Buttons').append($('<div>',{class: "Knopje knopjes",id: 'knopjes'}).append($('<span>',{class: "Knopjetext",text: "Show Buttons"})));
  $( ".Knopjetext:visible" ).each(function( index, element ) {
         $(this).textfill({maxFontPixels: 5});
  });

  function dotabfill(fill) {
    if(!tabenable) return;
    var dingen=$('#Zoek')[0].value.split(" ");
    var zoek=dingen[dingen.length-1].toLowerCase();
    if(zoek.length<2) {
        return;
    }
    var buttons=[];
    $.each(accountstobuttons(accounts,'m'),function(i,v) {
       if(v.text.toLowerCase().startsWith(zoek) || v.display.toLowerCase().startsWith(zoek)) {
           buttons.push(v);
       }
    });
    $.each(accountstobuttons(accounts,'o'),function(i,v) {
       if(v.text.toLowerCase().startsWith(zoek) || v.display.toLowerCase().startsWith(zoek)) {
           buttons.push(v);
       }
    });
    if(tabenable==1) {
      $.each(commandstobuttons(),function(i,v) {
         if(v.text.toLowerCase().startsWith(zoek) || v.display.toLowerCase().startsWith(zoek)) {
             buttons.push(v);
         }
      });
      $.each(allproductstobuttons(),function(i,v) {
         if(v.text.toLowerCase().startsWith(zoek) || v.display.toLowerCase().startsWith(zoek)) {
           buttons.push(v);
         } else {
           var done2=0;
           $.each(v.aliases,function(i2,v2) {
             if(v2.toLowerCase().startsWith(zoek) && ! done2) {
               buttons.push(v);
               done2=1;
             }
           });
         }
      });
    }
    makepages('normal',buttons);
    if(buttons.length==1 && fill) {
        dingen[dingen.length-1]=buttons[0].text+" ";
        $('#Zoek')[0].value=dingen.join(" ");
    }
  }

  function focus() {
    $('#Zoek')[0].focus();
  }
  function verwerkinput() {
    postmsg('input',$('#Zoek')[0].value);
    $('#Zoek')[0].value="";
  }
  $("body" ).on( "click",'div.shownumbers', function() {
    locked=1;
    $('#Secondscreen').show();
    makepage_numbers();
    focus();
    tabenable=0;
  });
  $("body" ).on( "click",'div.normal', function() {
    postmsg('input',this.id);
    focus();
  });
  $("body" ).on( "click",'div.invoer', function() {
    if(this.id=="enter") {
      verwerkinput();
    } else if(this.id=="backspace") {
      $('#Zoek')[0].value=$('#Zoek')[0].value.substring(0, $('#Zoek')[0].value.length - 1);
    } else if(this.id=="leeg") {
    } else if(this.id=="space") {
      $('#Zoek')[0].value=$('#Zoek')[0].value+" ";
    } else {
      $('#Zoek')[0].value=$('#Zoek')[0].value+this.id;
    }
    //postmsg('input',this.id);
    focus();
  });
  $("body" ).on( "click", 'div.page' ,function() {
    $('.Pagina').hide();
    $('#Page'+this.id).show();
    $( ".Buttontext:visible" ).each(function( index, element ) {
       $(this).textfill({maxFontPixels: 5});
    });
  });
  $("body" ).on( "click", 'div.productgroups' ,function() {
     makepages('normal',productgrouptobuttons(this.id).sort(compare_display))
     focus();
  });
  $('.Knopje').click(function() {
    switch(this.id) {
      case 'members':
         locked=0
         makepages('normal',accountstobuttons(accounts,'m'));
         $('#TopButtons').prepend($('<div>',{class: "Knopje Button normal cash",id: 'cash'}).append($('<span>',{class: "Paginatext",text: "cash"})));
         $( ".Paginatext:visible" ).each(function( index, element ) {
           $(this).textfill({maxFontPixels: 5});
         });
         focus();
         break;
      case 'otherusers':
         locked=0
         makepages('normal',accountstobuttons(accounts,'o'));
         $('#TopButtons').prepend($('<div>',{class: "Knopje Button normal cash",id: 'cash'}).append($('<span>',{class: "Paginatext",text: "cash"})));
         $( ".Paginatext:visible" ).each(function( index, element ) {
           $(this).textfill({maxFontPixels: 5});
         });
         focus();
         break;
      case 'products':
         locked=1;
         makepages('productgroups',productstobuttons(groups).sort(compare_display));
         focus();
         break;
      case 'commands':
         locked=0;
         makepages('normal',commandstobuttons().sort(compare_display));
         focus();
         break;
      case 'back':
         locked=0;
         $('#Secondscreen').hide();
         focus();
         break;
      case 'irc':
         locked=0;
         $('#Secondscreen').show();
         makepage_infobox();
         focus();
         break;
      case 'knopjes':
         locked=0;
         $('#Secondscreen').show();
         focus();
         break;
      default:
        $('#Zoek')[0].value=$('#Zoek')[0].value+''+this.id;
        verwerkinput();
        focus();
    }
  });
  $('.KnopjeOK').click(function() {
      runtext($('#Zoek')[0].value);
      $('#Zoek')[0].value="";
      showusers('');
      focus();
  });
  var delay = (function(){
    var timer = 0;
    return function(callback, ms){
      clearTimeout (timer);
      timer = setTimeout(callback, ms);
    };
  })();

  $( "#Zoek" ).keydown(function(data,res) {
    if(data.which==9) {
      dotabfill(1);
      data.preventDefault();
    } else if(data.which==13) {
      locked=0;
      postmsg('input',this.value);
      this.value="";
    } else {
      delay(function(){
        dotabfill(0);
      }, 200 );
    }
  });
  $('#Firstscreen').resize(function(){
    console.log('resize');
  });
  focus();
  postmsg('input','');
});
