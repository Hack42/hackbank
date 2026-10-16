document.addEventListener("DOMContentLoaded", function() {
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
  var pagedButtons=null;
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
      } else if(name === "html") {
        element.innerHTML=attrs[name];
      } else if(name === "style") {
        Object.keys(attrs[name]).forEach(function(styleName) {
          element.style[styleName]=attrs[name][styleName];
        });
      } else {
        element.setAttribute(name, attrs[name]);
      }
    });
    return element;
  }
  function first(selector) {
    return document.querySelector(selector);
  }
  function appendTo(selector, child) {
    var parent=first(selector);
    if(parent) parent.appendChild(child);
  }
  function appendChildren(parent, children) {
    children.forEach(function(child) {
      parent.appendChild(child);
    });
    return parent;
  }
  function appendToElement(parent, child) {
    if(parent) parent.appendChild(child);
    return child;
  }
  function removeElement(selector) {
    var element=first(selector);
    if(element) element.remove();
  }
  function removeElements(selector) {
    allElements(selector).forEach(function(element) {
      element.remove();
    });
  }
  function cloneElementsTo(selector, targetSelector) {
    var target=first(targetSelector);
    if(!target) return;
    allElements(selector).forEach(function(element) {
      target.appendChild(element.cloneNode(true));
    });
  }
  function setElementStyle(selector, styles) {
    var element=first(selector);
    if(!element) return;
    Object.keys(styles).forEach(function(name) {
      element.style[name]=styles[name];
    });
  }
  function appendBreak(parent) {
    appendToElement(parent, document.createElement('br'));
  }
  function setMainButtonsBackground(value) {
    var mainButtons=document.getElementById("MainButtons");
    if(mainButtons) mainButtons.style.backgroundColor=value;
  }
  function pageLabel(pagecount) {
    var pageButton=document.getElementById(String(pagecount));
    return pageButton ? pageButton.querySelector('.Paginatext') : null;
  }
  function appendToPageLabel(pagecount, html) {
    var label=pageLabel(pagecount);
    if(label) label.innerHTML=label.innerHTML + html;
  }
  function removeActiveTopButtons() {
    allElements('.topknop').forEach(function(button) {
      button.classList.remove('activetop');
    });
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
    makeAccountList(buttons.accountsToButtons(accounts,members,nonmembers,accountType));
    prependCashButton();
    focus();
    tabenable=tabMode;
  }
  function build_receipt(msg) {
    var parts=JSON.parse(msg);
    var receipt=first('#Receipt');
    var receipt2=first('#Receipt2');
    clearElement('#Receipt');
    var counter=0;
    parts.forEach(function(stuff) {
      counter++;
      appendToElement(receipt, appendChildren(createElement('div',{class: 'Itemline'}), [
        createElement('span',{class: 'Product', text: stuff.description}),
        createElement('span',{class: 'Times', text: stuff.count}),
        createElement('span',{class: 'LoseOrGain', text: stuff.Lose ? "LOSE" : "GAIN"}),
        createElement('span',{class: 'ItemEuro'}),
        createElement('div',{class: 'ItemAmount', text: stuff.total.toFixed(2)}),
      ]));
    });
    scrollToBottom('#Receipt');
    if(counter === 0) {
      appendToElement(receipt, createElement('div',{class: 'welcome', text: "Your next round starts here. Scan a product or choose a button."}));
    }
    clearElement('#Receipt2');
    cloneElementsTo('.Itemline', '#Receipt2');
    scrollToBottom('#Receipt2');
    if (receipt2 && receipt2.childElementCount === 0){
      appendToElement(receipt2, appendChildren(createElement('div',{class: 'receipt-empty'}), [
        createElement('span',{class: 'empty-symbol', text: '+', 'aria-hidden': 'true'}),
        createElement('strong',{text: 'Nothing on the tab yet'}),
        createElement('span',{text: 'Scan a product to get started.'}),
      ]));
    }
  }
  function build_totals(msg) {
    var parts=JSON.parse(msg);
    var totals=first('#Totals');
    clearElement('#Totals');
    var counter=0;
    parts.forEach(function(stuff) {
      counter++;
      appendToElement(totals, appendChildren(createElement('div',{class: 'Userline Total_'+stuff.user}), [
        createElement('span',{class: 'UserName', text: stuff.user ? stuff.user : '-$you-' }),
        createElement('span',{class: 'GainOrLose',text: (stuff.amount<0) ? 'LOSE' : 'GAIN'}),
        createElement('span',{class: 'TotalEuro'}),
        createElement('span',{class: 'Totalamount',text: (stuff.amount ? stuff.amount : 0-stuff.amount).toFixed(2) }),
      ]));
    });
    scrollToBottom('#Totals');
    if(counter === 0) {
      appendToElement(totals, createElement('div',{class: 'welcome', text: "Scan a product or choose a button from below"}));
    }
  }
  function run_infobox(name,msg) {
    var json=JSON.parse(msg);
    var newsaldo=json.amount;
    var infobox=first('.infoboxes .Total_'+name);
    appendToElement(infobox, createElement('span',{class: 'NowHas',text: "Now Has"}));
    appendToElement(infobox, createElement('span',{class: 'NewSaldo',text: newsaldo.toFixed(2)}));
  }
  function setupaccounts(name,msg) {
    if(msg === "") {
      delete accounts[name];
      return;
    }
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
    appendTo('#MainButtons', createElement('div',{class: "infoboxes", id: "infoboxes"}));
    cloneElementsTo('.Userline', '#infoboxes');
    appendTo('#TopButtons', buttonElement("Knopje Button normal ok",'ok',"OK"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal undo",'undo',"Undo"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal restore",'restore',"Undo + Restore"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal bon",'bon',"Bon"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal kassala",'kassala',"Kassala"));
    fillVisibleText("#TopButtons .Knopjetext:visible");
  }
  function dokeys(keys) {
    var keysElement=document.getElementById('keys');
    keys.forEach(function(val) {
      appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer small",id: val ,text: val}));
    });
  }
  function makepage_keyboard() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    appendTo('#MainButtons', createElement('div',{class: "keys", id: "keys"}));
    var keysElement=document.getElementById('keys');

    var keys=['!','@','#','$','%','^','&','*','(',')'];
    dokeys(keys);
    appendBreak(keysElement);

    keys=['1','2','3','4','5','6','7','8','9','0'];
    dokeys(keys);
    appendBreak(keysElement);

    keys=['q','w','e','r','t','y','u','i','o','p'];
    dokeys(keys);
    appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer enter small",id: "backspace" ,text: "←"}));
    appendBreak(keysElement);

    keys=['a','s','d','f','g','h','j','k','l'];
    dokeys(keys);
    appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer enter small",id: "enter" ,text: "⏎"}));
    appendBreak(keysElement);

    keys=['z','x','c','v','b','n','m'];
    appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    dokeys(keys);
    appendBreak(keysElement);
    appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer enter small",id: "leeg" ,text: " "}));
    appendToElement(keysElement, createElement('div',{class: "Knopje Knop invoer enter small",id: "space" ,text: " "}));
    appendBreak(keysElement);

    keys=['-','=','+','_','`','~',',','.','/','<','>'];
    dokeys(keys);
    appendBreak(keysElement);

    keys=["?",";","'",'\\',':','"','|','[',']','{','}'];
    dokeys(keys);
    appendBreak(keysElement);
    showquestion();
    
  }
  function makepage_history() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    appendTo('#MainButtons', createElement('div',{class: "mylines", id: "mylines"}));
    var mylines=document.getElementById('mylines');
    history.forEach(function(val) {
      appendToElement(mylines, document.createTextNode(val));
      appendBreak(mylines);
    });
    setElementStyle('#mylines', {overflowWrap: 'break-word', overflowY: 'auto'});
    scrollToBottom('#mylines');
    showquestion();
  }
  function makepage_numbers() {
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    appendTo('#MainButtons', createElement('div',{class: "numbers", id: "numbers"}));
    var numbers=document.getElementById('numbers');
    [["1","1"],["2","2"],["3","3"],["br"],["4","4"],["5","5"],["6","6"],["br"],["7","7"],["8","8"],["9","9"],["br"],[".","."],["0","0"],["enter","⏎"]].forEach(function(item) {
      if(item[0] === "br") {
        appendBreak(numbers);
      } else {
        appendToElement(numbers, createElement('div',{class: "Knopje Knop invoer" + (item[0] === "enter" ? " enter" : ""), id: item[0], text: item[1]}));
      }
    });
    showquestion();
  }
  function buttonsPerPage() {
    var mainButtons=first('#MainButtons');
    if(!mainButtons || !window.getComputedStyle) return 25;
    return parseInt(window.getComputedStyle(mainButtons).getPropertyValue('--buttons-per-page'), 10) || 25;
  }
  function selectButtonPage(id) {
    allElements('#TopButtons .page').forEach(function(button) {
      button.classList.remove('currentpage');
      if(button.id === String(id)) button.classList.add('currentpage');
    });
    hideElements('.Pagina');
    showElement('#Page'+id);
    fillVisibleText('.Buttontext:visible');
  }
  function reflowButtonPages() {
    if(!pagedButtons || !first('#MainButtons .Pagina')) return;
    var capacity=buttonsPerPage();
    if(capacity === pagedButtons.capacity) return;
    var activePage=first('#TopButtons .currentpage');
    var firstIndex=(activePage ? Number(activePage.id)-1 : 0)*pagedButtons.capacity;
    var extraButtons=allElements('#TopButtons .Knopje').filter(function(button) {
      return !button.classList.contains('page');
    });
    var previous=pagedButtons;
    makepages(previous.className,previous.buttons);
    selectButtonPage(Math.floor(firstIndex/capacity)+1);
    extraButtons.reverse().forEach(function(button) {
      first('#TopButtons').prepend(button);
    });
  }
  function commandButton(extraclass,stuff) {
    var knopje=appendChildren(createElement('div',{class: "Knopje Knop "+stuff.text+" "+extraclass + " " + stuff.class,id: stuff.text, role: 'button', tabindex: '0', title: stuff.display }), [
      createElement('span',{class: "Buttontext ",text: stuff.display}),
    ]);
    if(stuff.right) {
      var fullwidth='';
      if(!stuff.left && stuff.fill) fullwidth=' fullwidthButton ';
      appendToElement(knopje, createElement('span',{class: "right extra "+fullwidth+stuff.rightclass,text: stuff.right}));
    }
    if(stuff.left) {
      appendToElement(knopje, createElement('span',{class: "left extra "+stuff.leftclass,text: stuff.left}));
    }
    return knopje;
  }
  function makeAccountList(accountButtons) {
    pagedButtons=null;
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    var list=createElement('div',{id: 'AccountList', class: 'account-list', role: 'group', 'aria-label': 'Accounts'});
    accountButtons.forEach(function(button) {
      list.appendChild(commandButton('normal',button));
    });
    appendTo('#MainButtons',list);
    first('#MainButtons').scrollTop=0;
    fillVisibleText('.Buttontext:visible');
    showquestion();
  }
  function makepages(extraclass,buttons) {
    var capacity=buttonsPerPage();
    pagedButtons={className: extraclass, buttons: buttons, capacity: capacity};
    var pagecount=1;
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    appendTo('#MainButtons', createElement('div',{id: 'Page'+pagecount, class: 'Pagina'}));
    appendTo('#TopButtons', topButton("page currentpage",'1',"Page 1"));
    var counter=0;
    var donewpage=0;
    var first=1;
    var lastchar="";
    buttons.forEach(function(stuff) {
      if(donewpage === 1) {
        appendToPageLabel(pagecount, ' - '+lastchar);
        pagecount++;
        appendTo('#MainButtons', createElement('div',{id: 'Page'+pagecount, class: 'Pagina', style: {display: 'none'}}));
        appendTo('#TopButtons', topButton("page",String(pagecount),"Page "+pagecount));
        counter=0;
        donewpage=0;
        first=1;
      }
      if(first === 1) {
        appendToPageLabel(pagecount, '<br>'+stuff.display.charAt(0).toUpperCase());
        first=0;
      }
      lastchar=stuff.display.charAt(0).toUpperCase();
      appendTo('#Page'+pagecount, commandButton(extraclass,stuff));
      counter++;
      if(counter>=capacity) {
        donewpage=1;
      }
    });
    if(pagecount === 1) {
      removeElements(".page");
      fillVisibleText(".Buttontext:visible");
      showquestion();
    } else {
      appendToPageLabel(pagecount, ' - '+lastchar);
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
      makeAccountList(window.HackBankButtons.accountsToButtons(accounts,members,nonmembers,'m'));
      document.getElementById('TopButtons').prepend(topButton("shownumbers",'shownumbers',"Enter amount"));
      prependCashButton();
      focus();
      tabenable=2;

    } else if (buttons['special'] === 'numbers') {
      removeActiveTopButtons();
      showElement('#Secondscreen');
      makepage_numbers();
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'keyboard') {
      removeActiveTopButtons();
      showElement('#Secondscreen');
      makepage_keyboard();
      focus();
      tabenable=0;
    } else if (buttons['special'] === 'infobox') {
      removeActiveTopButtons();
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
            removeElement('#Question');
            question=msg;
            showquestion();
            appendTo('#Log', createElement('div',{class: 'lastlog Log',text: msg}));
            scrollToBottom('#Log');
            break;
         case 'receipt':
            build_receipt(msg);
            break;
         case 'totals':
            build_totals(msg);
            break;
         case 'log':
            removeElements('.lastlog');
            appendTo('#Log', createElement('div',{class: 'Log',text: msg}));
            scrollToBottom('#Log');
            break;
         case 'infobox':
            run_infobox(pathParts[6],msg);
            setMainButtonsBackground("#e8f3ec");
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
            setMainButtonsBackground("");
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
    if(tabenable === 2 || (buttons.length > 0 && buttons.every(function(button) {
      return button.class && button.class.indexOf('account ') === 0;
    }))) {
      makeAccountList(buttons);
    } else {
      makepages('normal',buttons);
    }
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
  function submitCommand() {
    locked=0;
    verwerkinput();
    focus();
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
    selectButtonPage(this.id);
    focus();
  }

  function handleProductGroupClick() {
     makepages('normal',window.HackBankButtons.productGroupToButtons(prods, stock, this.id).sort(window.HackBankButtons.compareDisplay));
     focus();
  }

  function showEmbeddedScreen(selector,title,url,hint) {
    hideElement('#IRCwindow');
    hideElement('#spacewindow');
    showElement(selector);
    var screen=first(selector);
    if(screen.childElementCount !== 0) return;
    var toolbar=createElement('div',{class: 'embed-toolbar'});
    toolbar.appendChild(createElement('strong',{text: title}));
    if(hint) toolbar.appendChild(createElement('span',{class: 'embed-note', text: hint}));
    toolbar.appendChild(createElement('a',{href: url, target: '_blank', rel: 'noopener noreferrer', text: 'Open '+title+' ↗'}));
    screen.appendChild(toolbar);
    screen.appendChild(createElement('iframe',{src: url, title: title, allow: 'autoplay; encrypted-media; picture-in-picture; fullscreen', allowfullscreen: ''}));
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
         showEmbeddedScreen('#IRCwindow','YouTube','https://www.youtube.com/','If the page cannot be displayed here, open it in a new tab.');
         break;
      case 'spacecon':
         activateTopButton(this.id);
         locked=0;
         showEmbeddedScreen('#spacewindow','Home Assistant','http://hass.space.hack42.nl:8123/home/overview');
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
    var header=createElement('header',{class: 'app-header row'});
    header.appendChild(appendChildren(createElement('div',{class: 'brand col-auto'}), [
      createElement('img',{class: 'brand-logo', src: 'images/Hack42.png', alt: 'Hack42 · Hackerspace Arnhem', width: '84', height: '56'}),
      appendChildren(createElement('div'), [
        createElement('span',{class: 'brand-name', text: 'hackbank'}),
        createElement('span',{class: 'brand-caption', text: 'HACK42 · BAR & DRINKS'}),
      ]),
    ]));
    header.appendChild(createElement('nav',{id: 'LeftButtons', class: 'LeftButtons col', 'aria-label': 'Register sections'}));
    appendTo('#body', header);

    var workspace=createElement('main',{class: 'workspace row'});
    var leftColumn=createElement('section',{class: 'workspace-main col', 'aria-label': 'Register'});
    var screens=createElement('div',{class: 'screens'});
    var overview=createElement('div',{id: 'Firstscreen', class: 'overview-screen'});
    overview.appendChild(createElement('h1',{class: 'section-title', text: 'Current sale'}));
    overview.appendChild(createElement('div',{id: 'Receipt', class: 'Receipt'}));
    overview.appendChild(createElement('div',{id: 'Buttons', class: 'Buttons'}));
    screens.appendChild(overview);

    var selection=createElement('div',{id: 'Secondscreen', class: 'selection-screen'});
    selection.appendChild(createElement('div',{id: 'TopButtons', class: 'RightButtons', 'aria-label': 'Current options'}));
    selection.appendChild(createElement('div',{id: 'MainButtons', class: 'MainButtons'}));
    screens.appendChild(selection);
    screens.appendChild(createElement('div',{id: 'IRCwindow', class: 'embedded-screen'}));
    screens.appendChild(createElement('div',{id: 'spacewindow', class: 'embedded-screen'}));
    leftColumn.appendChild(screens);
    leftColumn.appendChild(appendChildren(createElement('section',{class: 'activity', 'aria-label': 'Register activity'}), [
      createElement('span',{class: 'activity-label', text: 'ACTIVITY'}),
      createElement('div',{id: 'Log', role: 'log', 'aria-live': 'polite'}),
    ]));
    workspace.appendChild(leftColumn);

    var receiptPanel=createElement('aside',{class: 'receipt-panel col-auto', 'aria-label': 'Sale receipt'});
    receiptPanel.appendChild(appendChildren(createElement('div',{class: 'receipt-heading'}), [
      createElement('span',{class: 'eyebrow', text: 'THE HACK42 BAR'}),
      createElement('h2',{text: 'On the tab'}),
      createElement('span',{class: 'receipt-currency', text: 'EUR'}),
    ]));
    receiptPanel.appendChild(appendChildren(createElement('div',{class: 'receipt-columns', 'aria-hidden': 'true'}), [
      createElement('span',{text: 'ITEM'}),
      createElement('span',{text: 'QTY'}),
      createElement('span',{text: 'AMOUNT'}),
    ]));
    receiptPanel.appendChild(createElement('div',{id: 'Receipt2'}));
    receiptPanel.appendChild(createElement('div',{id: 'Totals', class: 'Totals', 'aria-label': 'Account totals', 'aria-live': 'polite'}));
    receiptPanel.appendChild(appendChildren(createElement('div',{class: 'receipt-footer'}), [
      createElement('span',{class: 'receipt-barcode', 'aria-hidden': 'true'}),
      createElement('span',{text: 'HACK42 · HACK. SIP. REPEAT.'}),
    ]));
    workspace.appendChild(receiptPanel);
    appendTo('#body', workspace);

    var inputWrapper=createElement('footer',{id: 'Invoer'});
    inputWrapper.appendChild(appendChildren(createElement('div',{class: 'command-caption'}), [
      createElement('label',{'for': 'Zoek', text: 'COMMAND LINE'}),
      createElement('span',{class: 'command-help', text: 'Scan a barcode · Type a command · Tab to complete'}),
    ]));
    inputWrapper.appendChild(appendChildren(createElement('div',{class: 'command-input'}), [
      createElement('span',{class: 'command-prompt', text: '›_', 'aria-hidden': 'true'}),
      createElement('input',{id: 'Zoek', placeholder: "Starting network communication", autocomplete: 'off', spellcheck: 'false', autocapitalize: 'off', 'aria-label': 'Product, command or username'}),
      createElement('button',{id: 'CommandEnter', type: 'button', class: 'enter-hint', text: 'ENTER ↵', 'aria-label': 'Submit command'}),
    ]));
    appendTo('#body', inputWrapper);
  }

  function buildLeftButtons() {
    var icons={
      abort: '<path d="m8 8 8 8M16 8l-8 8"/><circle cx="12" cy="12" r="9"/>',
      members: '<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 5"/>',
      otherusers: '<circle cx="12" cy="8" r="3"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/>',
      products: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
      commands: '<path d="m4 6 6 6-6 6M13 18h7"/>',
      sounds: '<path d="m11 4-6 5H2v6h3l6 5zM16 8a6 6 0 0 1 0 8M19 5a10 10 0 0 1 0 14"/>',
      irc: '<path d="M9 18V5l12-2v13M9 8l12-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="18" cy="16" rx="3" ry="2"/>',
      spacecon: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/><path d="M9 21v-9h6v9"/>',
    };
    var buttons=[
      ["Knopje Button topknop normal abort",'abort',"Abort"],
      ["Knopje Button topknop special",'members',"Members"],
      ["Knopje Button topknop special",'otherusers',"Other Users"],
      ["Knopje Button topknop special",'products',"Products"],
      ["Knopje Button topknop special",'commands',"Commands"],
      ["Knopje Button topknop sounds",'sounds',"Sounds"],
      ["Knopje Button topknop irc",'irc',"Music"],
      ["Knopje Button topknop spacecon",'spacecon',"Home Assistant"],
    ];
    buttons.forEach(function(button) {
      var element=buttonElement(button[0],button[1],button[2]);
      element.appendChild(createElement('span',{class: 'nav-icon', 'aria-hidden': 'true', html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'+icons[button[1]]+'</svg>'}));
      appendTo('#LeftButtons', element);
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
    document.getElementById('CommandEnter').addEventListener('click',submitCommand);
    searchInput().addEventListener("keydown", function(data) {
      if(data.which === 9) {
        dotabfill(1);
        data.preventDefault();
      } else if(data.which === 13) {
        submitCommand();
      } else {
        delay(function(){
          dotabfill(0);
        }, 200 );
      }
    });
  }

  window.HackBankStream.createSessionStream({
    session: session,
    onMessage: runmsg,
    onInvalidMessage: function(data, error) {
      console.log("Invalid stream message", data, error);
    },
  });
  buildLayout();
  buildLeftButtons();
  buildActionButtons();
  fillVisibleText(".Knopjetext:visible");
  bindButtonEvents();
  bindSearchInput();
  document.body.addEventListener('keydown', function(event) {
    if(event.target.id === 'Zoek' || (event.key !== 'Enter' && event.key !== ' ')) return;
    var button=event.target.closest && event.target.closest('.Knopje');
    if(button) {
      event.preventDefault();
      button.click();
    }
  });
  if(window.ResizeObserver) {
    var textObserver=new window.ResizeObserver(function() {
      reflowButtonPages();
      fillVisibleText('.Buttontext:visible');
      fillVisibleText('.Knopjetext:visible');
      fillVisibleText('.Paginatext:visible');
    });
    textObserver.observe(document.getElementById('MainButtons'));
    textObserver.observe(document.getElementById('LeftButtons'));
  }
  focus();
  postmsg('input','');
});
