/* global dolog, runtext, showusers */
var cachepixels={};
var cachetop={};
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
        var mytop=(maxHeight-textHeight)/2;
        this.css('top',mytop);
        cachetop[this.text()]=mytop;
        return this;
    };
})(jQuery);

$(function() {
  var session='main';
  if (window.location.hash !== '') {
    session=window.location.hash.replace('#','');
  }
  var prods={};
  var stock={};
  var accounts={};
  var commands={};
  var groups={};
  var nobcgroup={};
  var members=[];
  var nonmembers=[];
  var history=[];
  var tabenable=0;
  var question="";
  var locked=0;

  function postmsg(topic,msg) {
    fetch("post.php", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        topic: 'session/'+session+'/'+topic,
        msg: msg,
      }),
    }).catch(function(error) {
      console.error("Post failed", error);
    });
  }
  function firstElement(selector) {
    return document.querySelector(selector);
  }
  function allElements(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }
  function showElement(selector) {
    var element=firstElement(selector);
    if(element) element.style.display='';
  }
  function hideElement(selector) {
    var element=firstElement(selector);
    if(element) element.style.display='none';
  }
  function hideElements(selector) {
    allElements(selector).forEach(function(element) {
      element.style.display='none';
    });
  }
  function clearElement(selector) {
    var element=firstElement(selector);
    if(element) element.textContent='';
  }
  function scrollToBottom(selector) {
    var element=firstElement(selector);
    if(element) element.scrollTop=element.scrollHeight;
  }
  function searchInput() {
    return document.getElementById('Zoek');
  }
  function searchValue() {
    var input=searchInput();
    return input ? input.value : "";
  }
  function setSearchValue(value) {
    var input=searchInput();
    if(input) input.value=value;
  }
  function appendSearchValue(value) {
    setSearchValue(searchValue()+value);
  }
  function fillVisibleText(selector) {
    $(selector).each(function() {
       $(this).textfill({maxFontPixels: 5});
    });
  }
  function topButton(className,id,text) {
    return $('<div>',{class: "Knopje Button "+className,id: id}).append($('<span>',{class: "Paginatext",text: text}));
  }
  function buttonElement(className,id,text) {
    return $('<div>',{class: className,id: id}).append($('<span>',{class: "Knopjetext",text: text}));
  }
  function prependCashButton() {
    $('#TopButtons').prepend(topButton("normal cash",'cash',"cash"));
    fillVisibleText(".Paginatext:visible");
  }
  function activateTopButton(id) {
    $('.topknop').removeClass('activetop');
    $('#'+id).addClass('activetop');
  }
  function showAccountButtons(activeButtonId, accountType, tabMode) {
    activateTopButton(activeButtonId);
    showElement('#Secondscreen');
    makepages('normal',accountstobuttons(accounts,accountType));
    prependCashButton();
    focus();
    tabenable=tabMode;
  }
  function build_receipt(msg) {
    var parts=JSON.parse(msg);
    clearElement('#Receipt');
    var counter=0;
    parts.forEach(function(stuff) {
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
    scrollToBottom('#Receipt');
    if(counter === 0) {
      $('#Receipt').append($('<div>',{class: 'welcome', html: "Welcome to Hack42 Bank HTML5 Interface"}));
    }
    clearElement('#Receipt2');
    $('.Itemline').clone().appendTo('#Receipt2');
    scrollToBottom('#Receipt2');
    if ($('#Receipt2').is(':empty')){
       $('#Receipt2').append($('<img>',{src: 'images/Hack42.png', width: '100%'}).css({'top': '12vh','position': 'absolute'}));
    }
  }
  function build_totals(msg) {
    var parts=JSON.parse(msg);
    clearElement('#Totals');
    var counter=0;
    parts.forEach(function(stuff) {
      counter++;
      $('#Totals').append(
        $('<div>',{class: 'Userline Total_'+stuff.user})
          .append($('<span>',{class: 'UserName', text: stuff.user ? stuff.user : '-$you-' }))
          .append($('<span>',{class: 'GainOrLose',text: (stuff.amount<0) ? 'LOSE' : 'GAIN'}))
          .append($('<span>',{class: 'TotalEuro'}))
          .append($('<span>',{class: 'Totalamount',text: (stuff.amount ? stuff.amount : 0-stuff.amount).toFixed(2) }))
      );
    });
    scrollToBottom('#Totals');
    if(counter === 0) {
      $('#Totals').append($('<div>',{class: 'welcome', html: "Scan a product or choose a button from below"}));
    }
  }
  function run_infobox(name,msg) {
    var json=JSON.parse(msg);
    var newsaldo=json.amount;
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
    stock[name]=msg;
  }
  function setupproducts(name,msg) {
    prods[name]=JSON.parse(msg);
    groups={};
    Object.keys(prods).forEach(function(idx) {
      var stuff=prods[idx];
      groups[stuff.group]=(groups[stuff.group] || 0) + 1;
      var barcode=0;
      stuff.aliases.forEach(function(stuff2) {
        if(stuff2 > 9999999) barcode=1;
      });
      if(barcode === 0) {
        nobcgroup[name]=prods[name];
      }
    });
  }
  function productstobuttons(products) {
    var buttons=[];
    Object.keys(products).sort().forEach(function(v) {
      buttons.push({'text': v,'display': v, class: v});
    });
    return buttons;
  }
  function commandstobuttons() {
    var buttons=[];
    Object.keys(commands).sort().forEach(function(v) {
      buttons.push({'text': v,'display': commands[v], class: v});
    });
    return buttons;
  }
  function mycomparator(a,b) {
    var alc = a.toLowerCase(), blc = b.toLowerCase();
    return alc > blc ? 1 : alc < blc ? -1 : 0;
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
  function accountstobuttons(accounts,type) {
    var buttons=[];
    Object.keys(accounts).sort(mycomparator).forEach(function(v) {
      var isMember = members.indexOf(v) !== -1;
      var isNonMember = nonmembers.indexOf(v) !== -1;
      if((isMember && type === 'm') || (isNonMember && type === 'o') || (!isMember && !isNonMember && type === 'x')) {
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
    Object.keys(prods).forEach(function(v) {
      var button={'text': v,'display': prods[v].description,'right': prods[v].price.toFixed(2), rightclass:"green", class: v, aliases: prods[v].aliases};
      if(stock[v] !== undefined && Number(stock[v]) !== 0) {
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
    Object.keys(prods).forEach(function(idx) {
      var stuff=prods[idx];
      if(stuff.group === group) thisprods[idx]=1;
    });
    Object.keys(thisprods).sort().forEach(function(v) {
      var button={'text': v,'display': prods[v].description,'right': prods[v].price.toFixed(2), rightclass:"green", class: v};
      if(stock[v] !== undefined && Number(stock[v]) !== 0) {
        button['left']=stock[v];
        button['leftclass']='orange';
      }
      buttons.push(button);
    });
    return buttons;
  }

  function makepage_infobox() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    $('#MainButtons').append($('<div>',{class: "infoboxes", id: "infoboxes"}));
    $('.Userline').clone().appendTo('#infoboxes');
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal ok",id: 'ok'}).append($('<span>',{class: "Knopjetext",text: "OK"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal undo",id: 'undo'}).append($('<span>',{class: "Knopjetext",text: "Undo"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal restore",id: 'restore'}).append($('<span>',{class: "Knopjetext",text: "Undo + Restore"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal bon",id: 'bon'}).append($('<span>',{class: "Knopjetext",text: "Bon"})));
    $('#TopButtons').append($('<div>',{class: "Knopje Button normal kassala",id: 'kassala'}).append($('<span>',{class: "Knopjetext",text: "Kassala"})));
    fillVisibleText("#TopButtons .Knopjetext:visible");
  }
  function dokeys(keys) {
    keys.forEach(function(val) {
      $('#keys').append($('<div>',{class: "Knopje Knop invoer small",id: val ,text: val}));
    });
  }
  function makepage_keyboard() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    $('#MainButtons').append($('<div>',{class: "keys", id: "keys"}));

    var keys=['!','@','#','$','%','^','&','*','(',')'];
    dokeys(keys);
    $('#keys').append($('<br>'));

    keys=['1','2','3','4','5','6','7','8','9','0'];
    dokeys(keys);
    $('#keys').append($('<br>'));

    keys=['q','w','e','r','t','y','u','i','o','p'];
    dokeys(keys);
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "backspace" ,text: "←"}));
    $('#keys').append($('<br>'));

    keys=['a','s','d','f','g','h','j','k','l'];
    dokeys(keys);
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "enter" ,text: "⏎"}));
    $('#keys').append($('<br>'));

    keys=['z','x','c','v','b','n','m'];
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    dokeys(keys);
    $('#keys').append($('<br>'));
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    $('#keys').append($('<div>',{class: "Knopje Knop invoer enter small",id: "space" ,text: " "}));
    $('#keys').append($('<br>'));

    keys=['-','=','+','_','`','~',',','.','/','<','>'];
    dokeys(keys);
    $('#keys').append($('<br>'));

    keys=["?",";","'",'\\',':','"','|','[',']','{','}'];
    dokeys(keys);
    $('#keys').append($('<br>'));
    showquestion();
    
  }
  function makepage_history() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    $('#MainButtons').append($('<div>',{class: "mylines", id: "mylines"}));
    history.forEach(function(val) {
       $('#mylines').append(val+"<br>");
    });
    $('#mylines').css({'position': 'relative','top': '-12vh','left': '0px','z-index': '100','background': 'lightgray','height': '76vh','overflow-wrap': 'break-word','overflow-y': 'scroll','width': '96vw'});
    scrollToBottom('#mylines');
    showquestion();
  }
  function makepage_numbers() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
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
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    $('#MainButtons').append($('<div>',{id: 'Page'+pagecount, class: 'Pagina'}));
    $('#TopButtons').append($('<div>',{class: "Knopje Button page",id: '1'}).append($('<span>',{class: "Paginatext",text: "Page 1"})));
    var counter=0;
    var donewpage=0;
    var first=1;
    var lastchar="";
    buttons.forEach(function(stuff) {
      if(donewpage === 1) {
        $('#'+pagecount+' .Paginatext').html($('#'+pagecount+' .Paginatext').html()+' - '+lastchar);
        pagecount++;
        $('#MainButtons').append($('<div>',{id: 'Page'+pagecount, class: 'Pagina', style: 'display: none;'}));
        $('#TopButtons').append($('<div>',{class: "Knopje Button page",id: pagecount}).append($('<span>',{class: "Paginatext",text: "Page "+pagecount})));
        counter=0;
        donewpage=0;
        first=1;
      }
      if(first === 1) {
        $('#'+pagecount+' .Paginatext').html($('#'+pagecount+' .Paginatext').html()+'<br>'+stuff.display.charAt(0).toUpperCase());
        first=0;
      }
      var txt=$('<span>',{class: "Buttontext ",text: stuff.display});
      var knopje=$('<div>',{class: "Knopje Knop "+stuff.text+" "+extraclass + " " + stuff.class,id: stuff.text }).append(txt);
      if(stuff.right) {
        var fullwidth='';
        if(!stuff.left && stuff.fill) {
          fullwidth=' fullwidthButton ';
        }
        knopje.append($('<span>',{class: "right extra "+fullwidth+stuff.rightclass,text: stuff.right}));
      }
      if(stuff.left) {
        knopje.append($('<span>',{class: "left extra "+stuff.leftclass,text: stuff.left}));
      }
      lastchar=stuff.display.charAt(0).toUpperCase();
      $('#Page'+pagecount).append(knopje);
      counter++;
      var w=5;
      var h=5;
      if(counter>=w*h) {
        donewpage=1;
      }
    });
    if(pagecount === 1) {
      $(".page").remove();
      fillVisibleText(".Buttontext:visible");
      showquestion();
    } else {
      $('#'+pagecount+' .Paginatext').html($('#'+pagecount+' .Paginatext').html()+' - '+lastchar);
      fillVisibleText(".Paginatext:visible");
      allElements(".Pagina").forEach(function(page) {
        hideElements('.Pagina');
        page.style.display='';
        fillVisibleText(".Buttontext:visible");
        hideElements('.Pagina');
        showElement('#Page1');
      });
    }
  }
  function dobuttons(msg) {
    var buttons=JSON.parse(msg);
    if(msg === '{}' && locked === 0) {
      showAccountButtons('members','m',1);
    } else if (buttons['special'] === 'custom') {
      activateTopButton('commands');
      showElement('#Secondscreen');
      if(buttons['sort'] === "text") {
        buttons['custom'].sort(compare_text_rev);
      } else {
        buttons['custom'].sort(compare_display);
      }
      makepages('normal',buttons['custom']);
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'accounts') {
      showAccountButtons('members','m',2);
    } else if (buttons['special'] === 'accountsamount') {
      activateTopButton('members');
      showElement('#Secondscreen');
      makepages('normal',accountstobuttons(accounts,'m'));
      $('#TopButtons').prepend(topButton("shownumbers",'shownumbers',"Enter amount"));
      prependCashButton();
      focus();
      tabenable=2;

    } else if (buttons['special'] === 'numbers') {
      $('.topknop').removeClass('activetop');
      showElement('#Secondscreen');
      makepage_numbers();
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'keyboard') {
      $('.topknop').removeClass('activetop');
      showElement('#Secondscreen');
      makepage_keyboard();
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'infobox') {
      $('.topknop').removeClass('activetop');
      showElement('#Secondscreen');
      makepage_infobox();
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'history') {
      activateTopButton('commands');
      showElement('#Secondscreen');
      makepage_history();
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'products') {
      activateTopButton('products');
      showElement('#Secondscreen');
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
       $('#TopButtons').append($('<div>',{class: "Question",id: 'Question', text: question}));
    }
  }

  function runsession(SID,action,msg,pathParts) {
     if(SID !== session) return;
     switch(action) {
         case 'message':
            if(searchInput()) searchInput().placeholder=msg;
            $('#Question').remove();
            question=msg;
            showquestion();
            $('#Log').append(  $('<div>',{class: 'lastlog Log',text: msg})  );
            scrollToBottom('#Log');
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
            scrollToBottom('#Log');
            break;
         case 'infobox':
            run_infobox(pathParts[6],msg);
            $("#MainButtons").css("background-color","#d7ffd7");
            break;
         case 'accounts':
            setupaccounts(pathParts[5],msg);
            break;
         case 'products':
            setupproducts(pathParts[5],msg);
            break;
         case 'stock':
            setupstock(pathParts[5],msg);
            break;
         case 'history':
            history=JSON.parse(msg);
            break;
         case 'buttons':
            dobuttons(msg);
            $("#MainButtons").css("background-color","");
            break;
         case 'sound':
            playsound(msg);
            break;
         case 'members':
            members=JSON.parse(msg);
            break;
         case 'nonmembers':
            nonmembers=JSON.parse(msg);
            break;
         case 'commands':
            setupcommands(msg);
            break;
     }
  }
  function runmsg(path,msg) {
    var elms=path.split("/");
    //console.log(elms);
    if(elms.length < 3) return;
    switch(elms[2]) {
      case 'session':
         if(elms.length < 5) return;
         var sessionID=elms[3];
         var action=elms[4];
         runsession(sessionID,action,msg,elms);
         break;
       case 'log':
         dolog(msg);
         break;
       default:
         break;
    }
  }
  var source = null;
  var streamReconnectTimer = null;
  var streamReconnectDelay = 1000;

  function scheduleStreamReconnect() {
    if(streamReconnectTimer) return;
    if(source) {
      source.close();
      source = null;
    }
    streamReconnectTimer = setTimeout(function() {
      streamReconnectTimer = null;
      connectStream();
    }, streamReconnectDelay);
    streamReconnectDelay = Math.min(streamReconnectDelay * 2, 30000);
  }

  function connectStream() {
    source = new EventSource('stream.php?session='+encodeURIComponent(session)+'&t='+(new Date()).getTime());
    source.onopen = function() {
      streamReconnectDelay = 1000;
    };
    source.onmessage = function(event) {
      if(event.data === "closed") {
        scheduleStreamReconnect();
        return;
      }
      var data;
      try {
        data=JSON.parse(event.data);
      } catch(error) {
        console.log("Invalid stream message", event.data, error);
        return;
      }
      var path=data[0];
      var msg=data[1];
      //if(path=="startup") postmsg('startup',1);
      runmsg(path,msg);
    };
    source.onerror = function() {
      scheduleStreamReconnect();
    };
  }

  function buttonMatches(button, query) {
    return button.text.toLowerCase().startsWith(query) || button.display.toLowerCase().startsWith(query);
  }
  function addMatchingButtons(matches, candidates, query) {
    candidates.forEach(function(candidate) {
       if(buttonMatches(candidate, query)) {
           matches.push(candidate);
       }
    });
  }
  function dotabfill(fill) {
    if(!tabenable) return;
    var dingen=searchValue().split(" ");
    var zoek=dingen[dingen.length-1].toLowerCase();
    if(zoek.length<2) {
        return;
    }
    var buttons=[];
    addMatchingButtons(buttons, accountstobuttons(accounts,'m'), zoek);
    addMatchingButtons(buttons, accountstobuttons(accounts,'o'), zoek);
    addMatchingButtons(buttons, accountstobuttons(accounts,'x'), zoek);
    if(tabenable === 1) {
      addMatchingButtons(buttons, commandstobuttons(), zoek);
      allproductstobuttons().forEach(function(v) {
         if(buttonMatches(v, zoek)) {
           buttons.push(v);
         } else {
           var done2=0;
           v.aliases.forEach(function(v2) {
             if(String(v2).toLowerCase().startsWith(zoek) && ! done2) {
               buttons.push(v);
               done2=1;
             }
           });
         }
      });
    }
    makepages('normal',buttons);
    if(buttons.length === 1 && fill) {
        dingen[dingen.length-1]=buttons[0].text+" ";
        setSearchValue(dingen.join(" "));
    }
  }

  function focus() {
    hideElement('#IRCwindow');
    hideElement('#spacewindow');
    if(searchInput()) searchInput().focus();
  }
  function verwerkinput() {
    postmsg('input',searchValue());
    setSearchValue("");
  }
  var delay = (function(){
    var timer = 0;
    return function(callback, ms){
      clearTimeout (timer);
      timer = setTimeout(callback, ms);
    };
  })();

  function handleShownumbersClick() {
    locked=1;
    showElement('#Secondscreen');
    makepage_numbers();
    focus();
    tabenable=0;
  }

  function handleNormalClick() {
    var dingen=searchValue().split(" ");
    dingen[dingen.length-1]=this.id;
    postmsg('input',dingen.join(" "));
    setSearchValue("");
    focus();
  }

  function handleInputClick() {
    if(this.id === "enter") {
      verwerkinput();
    } else if(this.id === "backspace") {
      setSearchValue(searchValue().substring(0, searchValue().length - 1));
    } else if(this.id === "leeg") {
      focus();
      return;
    } else if(this.id === "space") {
      appendSearchValue(" ");
    } else {
      appendSearchValue(this.id);
    }
    //postmsg('input',this.id);
    focus();
  }

  function handlePageClick() {
    hideElements('.Pagina');
    showElement('#Page'+this.id);
    fillVisibleText(".Buttontext:visible");
    focus();
  }

  function handleProductGroupClick() {
     makepages('normal',productgrouptobuttons(this.id).sort(compare_display));
     focus();
  }

  function handleMainButtonClick() {
    switch(this.id) {
      case 'members':
         locked=0;
         showAccountButtons(this.id,'m',tabenable);
         break;
      case 'otherusers':
         locked=0;
         showAccountButtons(this.id,'o',tabenable);
         break;
      case 'products':
         activateTopButton(this.id);
         locked=1;
         makepages('productgroups',productstobuttons(groups).sort(compare_display));
         focus();
         break;
      case 'commands':
         activateTopButton(this.id);
         locked=0;
         makepages('normal',commandstobuttons().sort(compare_display));
         focus();
         break;
      case 'back':
         activateTopButton(this.id);
         locked=0;
         hideElement('#Secondscreen');
         focus();
         break;
      case 'irc':
         activateTopButton(this.id);
         locked=0;
         showElement('#IRCwindow');
         if($('#IRCwindow').html() === "") {
           $("#IRCwindow").append($('<iframe>',{src: 'http://kleintje:4200/',frameborder: 0, scrolling: 'no', width: '100%', height: '100%'}));
         }
         break;
      case 'spacecon':
         activateTopButton(this.id);
         locked=0;
         showElement('#spacewindow');
         if($('#spacewindow').html() === "") {
           $("#spacewindow").append($('<iframe>',{src: '/spaceconsole/',frameborder: 0, scrolling: 'no', width: '100%', height: '100%'}));
         }
         break;
      case 'knopjes':
         activateTopButton(this.id);
         locked=0;
         showElement('#Secondscreen');
         hideElement('#IRCwindow');
         hideElement('#spacewindow');
         focus();
         break;
      default:
        appendSearchValue(this.id);
        verwerkinput();
        focus();
    }
  }

  function handleOkClick() {
    runtext(searchValue());
    setSearchValue("");
    showusers('');
    focus();
  }

  function bindButtonEvents() {
    $("body" ).on( "click",'div.shownumbers', handleShownumbersClick);
    $("body" ).on( "click",'div.normal', handleNormalClick);
    $("body" ).on( "click",'div.invoer', handleInputClick);
    $("body" ).on( "click", 'div.page' ,handlePageClick);
    $("body" ).on( "click", 'div.productgroups' ,handleProductGroupClick);
    $("body").on("click", 'div.Knopje:not(.normal):not(.shownumbers):not(.invoer):not(.page):not(.productgroups)', handleMainButtonClick);
    $("body").on("click", '.KnopjeOK', handleOkClick);
  }

  function buildLayout() {
    $('#body').append($('<div>',{id: 'Firstscreen'}));
    $('#body').append($('<div>',{id: 'Secondscreen'}));
    $('#body').append($('<div>',{id: 'IRCwindow'}));
    $('#body').append($('<div>',{id: 'spacewindow'}));

    $('#Firstscreen').append($('<div>',{id: 'Receipt', class: 'Receipt'}));
    $('#Firstscreen').append($('<div>',{id: 'Totals', class: 'Totals'}));
    $('#Firstscreen').append($('<div>',{id: 'Buttons', class: 'Buttons'}));
    $('#Firstscreen').append($('<div>',{id: 'Log'}));
    $('#Firstscreen').append($('<div>',{id: 'Invoer'}).append($('<input>',{id: 'Zoek',placeholder: "Starting network communication" }).attr('autocomplete','off')));
    $('#Secondscreen').append($('<div>',{id: 'LeftButtons', class: 'LeftButtons'}));
    $('#Secondscreen').append($('<div>',{id: 'MainButtons', class: 'MainButtons'}));
    $('#Secondscreen').append($('<div>',{id: 'TopButtons', class: 'RightButtons'}));
    $('#Secondscreen').append($('<div>',{id: 'Receipt2'}));
  }

  function buildLeftButtons() {
    var buttons=[
      ["Knopje Button topknop normal abort",'abort',"Abort"],
      ["Knopje Button topknop special",'members',"Members"],
      ["Knopje Button topknop special",'otherusers',"Other Users"],
      ["Knopje Button topknop special",'products',"Products"],
      ["Knopje Button topknop special",'commands',"Commands"],
      ["Knopje Button topknop sounds",'sounds',"Sounds"],
      ["Knopje Button topknop irc",'irc',"IRC"],
      ["Knopje Button topknop spacecon",'spacecon',"Lights"],
    ];
    buttons.forEach(function(button) {
      $('#LeftButtons').append(buttonElement(button[0],button[1],button[2]));
    });
  }

  function buildActionButtons() {
    var buttons=[
      ["Knopje abort",'abort',"Abort"],
      ["Knopje bon",'bon',"Bon"],
      ["Knopje remove",'remove'," Remove Item"],
      ["Knopje shame",'shame',"Shame"],
      ["Knopje undo",'undo',"Undo"],
      ["Knopje ok",'ok',"OK"],
      ["Knopje knopjes",'knopjes',"Show Buttons"],
    ];
    buttons.forEach(function(button) {
      $('#Buttons').append(buttonElement(button[0],button[1],button[2]));
    });
  }

  function bindSearchInput() {
    searchInput().addEventListener("keydown", function(data) {
      if(data.which === 9) {
        dotabfill(1);
        data.preventDefault();
      } else if(data.which === 13) {
        locked=0;
        postmsg('input',this.value);
        this.value="";
      } else {
        delay(function(){
          dotabfill(0);
        }, 200 );
      }
    });
  }

  connectStream();
  buildLayout();
  buildLeftButtons();
  buildActionButtons();
  fillVisibleText(".Knopjetext:visible");
  bindButtonEvents();
  bindSearchInput();
  focus();
  postmsg('input','');
});
