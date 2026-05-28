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
  var buttons=window.HackBankButtons;
  var dom=window.HackBankDom;
  var allElements=dom.allElements;
  var appendSearchValue=dom.appendSearchValue;
  var buttonElement=dom.buttonElement;
  var clearElement=dom.clearElement;
  var fillVisibleText=dom.fillVisibleText;
  var hideElement=dom.hideElement;
  var hideElements=dom.hideElements;
  var scrollToBottom=dom.scrollToBottom;
  var searchInput=dom.searchInput;
  var searchValue=dom.searchValue;
  var setSearchValue=dom.setSearchValue;
  var showElement=dom.showElement;
  var topButton=dom.topButton;

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
  function createElement(tagName, attrs) {
    var element=document.createElement(tagName);
    Object.keys(attrs || {}).forEach(function(name) {
      if(name === "class") {
        element.className=attrs[name];
      } else if(name === "text") {
        element.textContent=attrs[name];
      } else {
        element.setAttribute(name, attrs[name]);
      }
    });
    return element;
  }
  function appendTo(selector, child) {
    var parent=document.querySelector(selector);
    if(parent) parent.appendChild(child);
  }
  function prependCashButton() {
    var topButtons=document.getElementById('TopButtons');
    if(topButtons) topButtons.prepend(topButton("normal cash",'cash',"cash"));
    fillVisibleText(".Paginatext:visible");
  }
  function activateTopButton(id) {
    allElements('.topknop').forEach(function(button) {
      button.classList.remove('activetop');
    });
    var button=document.getElementById(id);
    if(button) button.classList.add('activetop');
  }
  function showAccountButtons(activeButtonId, accountType, tabMode) {
    activateTopButton(activeButtonId);
    showElement('#Secondscreen');
    makepages('normal',buttons.accountsToButtons(accounts,members,nonmembers,accountType));
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
    buttons.rebuildProductIndexes(prods, groups, nobcgroup);
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
        buttons['custom'].sort(window.HackBankButtons.compareTextReverse);
      } else {
        buttons['custom'].sort(window.HackBankButtons.compareDisplay);
      }
      makepages('normal',buttons['custom']);
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'accounts') {
      showAccountButtons('members','m',2);
    } else if (buttons['special'] === 'accountsamount') {
      activateTopButton('members');
      showElement('#Secondscreen');
      makepages('normal',window.HackBankButtons.accountsToButtons(accounts,members,nonmembers,'m'));
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
      makepages('productgroups',window.HackBankButtons.productsToButtons(groups).sort(window.HackBankButtons.compareDisplay));
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
    var topButtons=document.getElementById('TopButtons');
    if (topButtons && topButtons.childElementCount === 0){
       topButtons.appendChild(createElement('div',{class: "Question",id: 'Question', text: question}));
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

  function dotabfill(fill) {
    if(!tabenable) return;
    var dingen=searchValue().split(" ");
    var zoek=dingen[dingen.length-1].toLowerCase();
    if(zoek.length<2) {
        return;
    }
    var buttons=[];
    window.HackBankButtons.addMatchingButtons(buttons, window.HackBankButtons.accountsToButtons(accounts,members,nonmembers,'m'), zoek);
    window.HackBankButtons.addMatchingButtons(buttons, window.HackBankButtons.accountsToButtons(accounts,members,nonmembers,'o'), zoek);
    window.HackBankButtons.addMatchingButtons(buttons, window.HackBankButtons.accountsToButtons(accounts,members,nonmembers,'x'), zoek);
    if(tabenable === 1) {
      window.HackBankButtons.addMatchingButtons(buttons, window.HackBankButtons.commandsToButtons(commands), zoek);
      window.HackBankButtons.allProductsToButtons(prods, stock).forEach(function(v) {
         if(window.HackBankButtons.buttonMatches(v, zoek)) {
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
     makepages('normal',window.HackBankButtons.productGroupToButtons(prods, stock, this.id).sort(window.HackBankButtons.compareDisplay));
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
         makepages('productgroups',window.HackBankButtons.productsToButtons(groups).sort(window.HackBankButtons.compareDisplay));
         focus();
         break;
      case 'commands':
         activateTopButton(this.id);
         locked=0;
         makepages('normal',window.HackBankButtons.commandsToButtons(commands).sort(window.HackBankButtons.compareDisplay));
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
    document.body.addEventListener("click", function(event) {
      var target=event.target;
      var button;

      if(!target.closest) return null;

      button=target.closest('div.shownumbers');
      if(button) return handleShownumbersClick.call(button, event);

      button=target.closest('div.normal');
      if(button) return handleNormalClick.call(button, event);

      button=target.closest('div.invoer');
      if(button) return handleInputClick.call(button, event);

      button=target.closest('div.page');
      if(button) return handlePageClick.call(button, event);

      button=target.closest('div.productgroups');
      if(button) return handleProductGroupClick.call(button, event);

      button=target.closest('.KnopjeOK');
      if(button) return handleOkClick.call(button, event);

      button=target.closest('div.Knopje:not(.normal):not(.shownumbers):not(.invoer):not(.page):not(.productgroups)');
      if(button) return handleMainButtonClick.call(button, event);
    });
  }

  function buildLayout() {
    appendTo('#body', createElement('div',{id: 'Firstscreen'}));
    appendTo('#body', createElement('div',{id: 'Secondscreen'}));
    appendTo('#body', createElement('div',{id: 'IRCwindow'}));
    appendTo('#body', createElement('div',{id: 'spacewindow'}));

    appendTo('#Firstscreen', createElement('div',{id: 'Receipt', class: 'Receipt'}));
    appendTo('#Firstscreen', createElement('div',{id: 'Totals', class: 'Totals'}));
    appendTo('#Firstscreen', createElement('div',{id: 'Buttons', class: 'Buttons'}));
    appendTo('#Firstscreen', createElement('div',{id: 'Log'}));

    var inputWrapper=createElement('div',{id: 'Invoer'});
    inputWrapper.appendChild(createElement('input',{id: 'Zoek', placeholder: "Starting network communication", autocomplete: 'off'}));
    appendTo('#Firstscreen', inputWrapper);

    appendTo('#Secondscreen', createElement('div',{id: 'LeftButtons', class: 'LeftButtons'}));
    appendTo('#Secondscreen', createElement('div',{id: 'MainButtons', class: 'MainButtons'}));
    appendTo('#Secondscreen', createElement('div',{id: 'TopButtons', class: 'RightButtons'}));
    appendTo('#Secondscreen', createElement('div',{id: 'Receipt2'}));
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
      appendTo('#LeftButtons', buttonElement(button[0],button[1],button[2]));
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
      appendTo('#Buttons', buttonElement(button[0],button[1],button[2]));
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
