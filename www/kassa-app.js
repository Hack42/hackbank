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
  var filterRestore=null;
  var filtering=false;
  var audioControl=null;
  var currentView='accounts';
  var commandCategory='All commands';
  var soundButtons=[];
  var activity=null;
  var accountProfile=null;
  var accountType='m';
  var archivedAccounts=false;
  var accountSections=null;
  var filterReturnView=null;
  var preferences=window.HackBankPreferences ? window.HackBankPreferences.create({
    sendCommand: function(command) {
      postmsg('input',command);
    },
    playSound: playsound,
  }) : null;
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
    if(topic === 'input' && preferences && preferences.handleCommand(msg)) {
      preferences.command();
      if(currentView === 'commands') locked=1;
      if(filterReturnView === 'commands') { filterReturnView=null; makeCommandScreen(commandCategory); }
      else if(filterRestore) { restoreSelection(filterRestore); filterRestore=null; }
      return;
    }
    if(topic === 'input') filterReturnView=null;
    if(topic === 'input' && msg.trim() && preferences) preferences.command();
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
    stopAudio();
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
    stopAudio();
    allElements('.topknop').forEach(function(button) {
      button.classList.remove('activetop');
    });
    var button=document.getElementById(id);
    if(button) button.classList.add('activetop');
  }
  function stopAudio() {
    if(audioControl) audioControl.stop();
    audioControl=null;
  }
  function showAccountButtons(activeButtonId, accountType, tabMode) {
    activateTopButton(activeButtonId);
    showElement('#Secondscreen');
    currentView='accounts';
    makeAccountSections(accountType,false);
    prependCashButton();
    focus();
    tabenable=tabMode;
  }
  function makeAccountSections(type, archive) {
    accountType=type;
    archivedAccounts=archive;
    var candidates=buttons.accountsToButtons(accounts,members,nonmembers,type);
    if(type === 'o') candidates=candidates.concat(buttons.accountsToButtons(accounts,members,nonmembers,'x')).sort(function(a,b) { return a.display.toLowerCase().localeCompare(b.display.toLowerCase()); });
    accountSections=buttons.splitAccounts(candidates,accounts,activity);
    makeAccountList(archive ? accountSections.archive : accountSections.active);
    addArchiveTabs();
  }
  function addArchiveTabs() {
    if(!accountSections) return;
    var top=document.getElementById('TopButtons');
    var name=accountType === 'm' ? 'Members' : 'Other users';
    [[false,name],[true,name+' Archive']].forEach(function(item) {
      var tab=createElement('button',{type:'button',class:'archive-tab'+(archivedAccounts === item[0] ? ' selected' : ''),text:item[1]+' ('+accountSections[item[0] ? 'archive' : 'active'].length+')', 'aria-pressed':String(archivedAccounts === item[0])});
      if(item[0] && (!activity || !activity.available)) { tab.disabled=true; tab.title='Archive unavailable until purchase history can be checked'; }
      tab.addEventListener('click',function() { makeAccountSections(accountType,item[0]); prependCashButton(); focus(); });
      if(item[0]) top.appendChild(tab);
      else top.prepend(tab);
    });
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
    if(json.user) {
      accountProfile=json;
      return;
    }
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
    if(preferences) Object.assign(commands,preferences.commands);
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
    if(!accountProfile || accountProfile.checkout) {
      appendTo('#MainButtons', createElement('div',{class: "infoboxes", id: "infoboxes"}));
      cloneElementsTo('#Totals .Userline', '#infoboxes');
    }
    if(accountProfile) {
      makeUserProfile(accountProfile);
    }
    appendTo('#TopButtons', buttonElement("Knopje Button normal ok",'ok',"OK"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal undo",'undo',"Undo last transaction"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal restore",'restore',"Undo + Restore"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal bon",'bon',"Print receipt"));
    appendTo('#TopButtons', buttonElement("Knopje Button normal kassala",'kassala',"Open cash drawer"));
    fillVisibleText("#TopButtons .Knopjetext:visible");
  }
  function actionButton(label, command, className) {
    var button=createElement('button',{type:'button',class:className || 'profile-action',text:label});
    button.addEventListener('click',function() {
      locked=0;
      currentView='action';
      postmsg('input',command);
      setSearchValue(''); focus();
    });
    return button;
  }
  function makeUserProfile(profile) {
    currentView='profile';
    var screen=createElement('section',{class:'user-profile'});
    var heading=createElement('div',{class:'profile-heading'});
    heading.appendChild(createElement('h1',{text:profile.user}));
    var balanceClass=profile.amount < -13.37 ? ' rood' : (profile.amount < 0 ? ' orange' : '');
    heading.appendChild(createElement('span',{class:'profile-balance'+balanceClass,text:'Balance €'+profile.amount.toFixed(2)}));
    screen.appendChild(heading);
    var actions=createElement('div',{class:'profile-actions'});
    actions.appendChild(actionButton('Full user history','history '+profile.user));
    if(profile.undo_transaction !== null && profile.undo_transaction !== undefined) {
      actions.appendChild(actionButton('Undo latest transaction','undouserlatest '+profile.undo_transaction+':'+profile.user,'profile-action undo-user-transaction'));
    }
    screen.appendChild(actions);
    screen.appendChild(createElement('h2',{text:'Last 10 purchases'}));
    screen.appendChild(createElement('p',{class:'profile-hint',text:'Add again uses the current price and adds to the current sale.'}));
    if(profile.history_available && profile.history_complete === false) screen.appendChild(createElement('p',{class:'profile-hint',text:'Recent history is limited; open full user history for older purchases.'}));
    var rows=createElement('div',{class:'purchase-list'});
    (profile.purchases || []).forEach(function(purchase) {
      var row=createElement('div',{class:'purchase-row'});
      var details=createElement('div');
      details.appendChild(createElement('strong',{text:purchase.count+' × '+purchase.description}));
      details.appendChild(createElement('span',{class:'purchase-date',text:purchase.date.replace('_',' ')+' · paid €'+purchase.total.toFixed(2)}));
      row.appendChild(details);
      if(purchase.product && prods[purchase.product] && purchase.count > 0 && purchase.count < 100) {
        var command=purchase.count === 1 ? purchase.product : purchase.count+'* '+purchase.product;
        row.appendChild(actionButton('Add again · €'+(prods[purchase.product].price*purchase.count).toFixed(2),command,'profile-action reorder-purchase'));
      }
      rows.appendChild(row);
    });
    if(!rows.childElementCount) rows.appendChild(createElement('p',{class:'profile-hint',text:profile.history_available ? 'No purchases found.' : 'Purchase history is unavailable.'}));
    screen.appendChild(rows);
    appendTo('#MainButtons',screen);
    appendTo('#TopButtons',actionButton('Back to members','abort','profile-action'));
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
  function buttonsPerPage(accountList) {
    var mainButtons=first('#MainButtons');
    if(!mainButtons || !window.getComputedStyle) return 25;
    var style=window.getComputedStyle(mainButtons);
    if(accountList) {
      var width=mainButtons.clientWidth-(parseFloat(style.paddingLeft) || 0)-(parseFloat(style.paddingRight) || 0);
      var height=mainButtons.clientHeight-(parseFloat(style.paddingTop) || 0)-(parseFloat(style.paddingBottom) || 0);
      var rowHeight=parseFloat(style.getPropertyValue('--account-row-height')) || 84;
      if(width > 0 && height > 0) {
        var columns=Math.max(1,Math.floor((width+8)/(240+8)));
        var rows=Math.max(1,Math.floor((height+8)/(rowHeight+8)));
        mainButtons.style.setProperty('--account-columns',columns);
        mainButtons.style.setProperty('--account-rows',rows);
        return columns*rows;
      }
      return parseInt(style.getPropertyValue('--accounts-per-page'), 10) || 42;
    }
    return parseInt(style.getPropertyValue('--buttons-per-page'), 10) || 25;
  }
  function selectButtonPage(id) {
    allElements('#TopButtons .page').forEach(function(button) {
      button.classList.remove('currentpage');
      if(button.id === String(id)) button.classList.add('currentpage');
    });
    hideElements('.Pagina');
    showElement('#Page'+id);
    first('#MainButtons').scrollTop=0;
    fillVisibleText('.Buttontext:visible');
  }
  function selectionSnapshot() {
    if(!pagedButtons || !allElements('#MainButtons .Pagina').length) return null;
    var activePage=allElements('#TopButtons .currentpage')[0];
    return {
      view: pagedButtons,
      firstIndex: (activePage ? Number(activePage.id)-1 : 0)*pagedButtons.capacity,
      extras: allElements('#TopButtons .Knopje').filter(function(button) {
        return !button.classList.contains('page');
      }),
    };
  }
  function restoreExtraButtons(snapshot) {
    snapshot.extras.slice().reverse().forEach(function(button) {
      first('#TopButtons').prepend(button);
    });
  }
  function restoreSelection(snapshot) {
    if(!snapshot) return;
    makepages(snapshot.view.className,snapshot.view.buttons,snapshot.view.accountList);
    selectButtonPage(Math.floor(snapshot.firstIndex/pagedButtons.capacity)+1);
    restoreExtraButtons(snapshot);
    if(currentView === 'accounts') addArchiveTabs();
  }
  function reflowButtonPages() {
    if(!pagedButtons || !allElements('#MainButtons .Pagina').length) return;
    var capacity=buttonsPerPage(pagedButtons.accountList);
    if(capacity === pagedButtons.capacity) return;
    var previousFilter=filterRestore;
    restoreSelection(selectionSnapshot());
    filterRestore=previousFilter;
  }
  function commandButton(extraclass,stuff) {
    var knopje=appendChildren(createElement('div',{class: "Knopje Knop "+stuff.text+" "+extraclass + " " + stuff.class,id: stuff.text, role: 'button', tabindex: '0', title: stuff.display }), [
      createElement('span',{class: "Buttontext ",text: stuff.display}),
    ]);
    if(stuff.hint) knopje.appendChild(createElement('small',{class:'command-hint',text:stuff.hint}));
    if(stuff.text === 'stitch' && stuff.class && stuff.class.indexOf('account ') === 0) {
      knopje.prepend(createElement('img',{class: 'account-icon', src: 'images/users/stitch.png', width: '32', height: '32', alt: '', 'aria-hidden': 'true'}));
    }
    if(stuff.class && stuff.class.indexOf('account-theme-lockpicker') !== -1) {
      knopje.prepend(createElement('span',{class: 'account-icon key-icon', 'aria-hidden': 'true', html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="5"/><path d="m11.5 11.5 9 9M16 16l3-3M19 19l3-3"/></svg>'}));
    }
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
    makepages('normal',accountButtons,true);
  }
  function makepages(extraclass,buttons,accountList) {
    stopAudio();
    if(!filtering) filterRestore=null;
    var capacity=buttonsPerPage(accountList);
    pagedButtons={className: extraclass, buttons: buttons, capacity: capacity, accountList: !!accountList};
    var pagecount=1;
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    first('#MainButtons').scrollTop=0;
    var container='#MainButtons';
    var pageClass='Pagina';
    if(accountList) {
      appendTo(container,createElement('div',{id: 'AccountList', role: 'group', 'aria-label': 'Accounts'}));
      container='#AccountList';
      pageClass+=' account-list';
    }
    appendTo(container, createElement('div',{id: 'Page'+pagecount, class: pageClass}));
    appendTo('#TopButtons', topButton("page currentpage",'1',"Page 1"));
    var counter=0;
    var donewpage=0;
    var firstOnPage=1;
    var lastchar="";
    buttons.forEach(function(stuff) {
      if(donewpage === 1) {
        appendToPageLabel(pagecount, ' - '+lastchar);
        pagecount++;
        appendTo(container, createElement('div',{id: 'Page'+pagecount, class: pageClass, style: {display: 'none'}}));
        appendTo('#TopButtons', topButton("page",String(pagecount),"Page "+pagecount));
        counter=0;
        donewpage=0;
        firstOnPage=1;
      }
      if(firstOnPage === 1) {
        appendToPageLabel(pagecount, '<br>'+stuff.display.charAt(0).toUpperCase());
        firstOnPage=0;
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
  function makeSoundScreen(soundButtons) {
    activateTopButton('sounds');
    currentView='sounds';
    pagedButtons=null;
    filterRestore=null;
    clearElement('#MainButtons');
    clearElement('#TopButtons');
    showElement('#Secondscreen');
    var screen=createElement('div',{class: 'sound-screen'});
    screen.appendChild(createElement('h1',{class: 'section-title', text: 'Sounds'}));
    appendTo('#MainButtons',screen);
    audioControl=window.HackBankAudio.mount(screen);
    var actions=createElement('div',{class: 'sound-actions', 'aria-label': 'Sound commands'});
    soundButtons.forEach(function(button) { actions.appendChild(commandButton('normal',button)); });
    screen.appendChild(actions);
    showquestion();
    fillVisibleText('.Buttontext:visible');
  }
  function makeCommandScreen(category) {
    commandCategory=category || 'All commands';
    locked=1;
    activateTopButton('commands');
    currentView='commands';
    pagedButtons=null; filterRestore=null;
    clearElement('#MainButtons'); clearElement('#TopButtons');
    showElement('#Secondscreen');
    appendTo('#TopButtons',actionButton('Abort everything','abort','profile-action abort-all'));
    var sections=buttons.commandSections(commands);
    var icons={'All commands':'📋',Products:'📦',Users:'👥',Sales:'🧾',Wholesale:'🏬',Market:'🏷️',Misc:'🛠️',Settings:'⚙️'};
    function categoryIcon(element,name) {
      element.prepend(createElement('span',{class:'category-icon','aria-hidden':'true',text:icons[name]}));
      return element;
    }
    ['All commands'].concat(sections.map(function(section) { return section.name; }),['Settings']).forEach(function(name) {
      var tab=categoryIcon(createElement('button',{type:'button',class:'command-tab'+((category || 'All commands') === name ? ' selected' : ''),text:name,'aria-label':name}),name);
      tab.addEventListener('click',function() { makeCommandScreen(name); focus(); });
      appendTo('#TopButtons',tab);
    });
    var grid=createElement('div',{class:'command-sections'+(category && category !== 'All commands' ? ' single-section' : '')});
    sections.forEach(function(section) {
      if(category && category !== 'All commands' && category !== section.name) return;
      if(!section.buttons.length) return;
      var card=createElement('section',{class:'command-section section-'+section.name.toLowerCase()});
      card.appendChild(categoryIcon(createElement('h2',{text:section.name}),section.name));
      var commandsGrid=createElement('div',{class:'command-group-buttons'});
      section.buttons.forEach(function(button) { commandsGrid.appendChild(commandButton('normal',button)); });
      card.appendChild(commandsGrid); grid.appendChild(card);
    });
    if(preferences && (!category || category === 'All commands' || category === 'Settings')) {
      var settings=createElement('section',{class:'command-section section-settings'});
      settings.appendChild(categoryIcon(createElement('h2',{text:'Settings'}),'Settings'));
      var settingsGrid=createElement('div',{class:'settings-grid'});
      ['party','dark','banana','dank','confetti'].forEach(function(key) { settingsGrid.appendChild(preferences.toggle(key)); });
      settings.appendChild(settingsGrid); grid.appendChild(settings);
    }
    appendTo('#MainButtons',grid);
    focus(); tabenable=1;
  }
  function dobuttons(msg) {
    if(currentView === 'commands' && locked === 1) return;
    var buttons=JSON.parse(msg);
    if(msg === '{}' && locked === 0) {
      if(currentView === 'sounds') return;
      showAccountButtons('members','m',1);
    } else if (buttons['special'] === 'custom') {
      showElement('#Secondscreen');
      var customButtons=window.HackBankButtons.visibleCommandButtons(buttons['custom']);
      if(buttons['sort'] === "text") {
        customButtons.sort(window.HackBankButtons.compareTextReverse);
      } else {
        customButtons.sort(window.HackBankButtons.compareDisplay);
      }
      var soundMenu=buttons['custom'].some(function(button) { return button.text === 'ns'; })
        && buttons['custom'].some(function(button) { return button.text === 'vergaderen'; });
      if(soundMenu) {
        soundButtons=window.HackBankButtons.visibleSoundButtons(customButtons);
        makeSoundScreen(soundButtons);
      }
      else {
        currentView='action';
        activateTopButton('commands');
        makepages('normal',customButtons);
      }
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
    var playback=audioElement.play();
    if(playback && playback.catch) playback.catch(function(error) { console.log('Audio playback unavailable',error); });
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
            accountProfile=null;
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
         case 'effects':
            if(preferences && JSON.parse(msg).type === 'sale') preferences.sale();
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
         case 'activity':
            activity=JSON.parse(msg);
            if(currentView === 'accounts' && !searchValue()) {
              makeAccountSections(accountType,archivedAccounts); prependCashButton();
            }
            if(currentView === 'profile') {
              // A fresh backend check still guards the actual undo command.
              allElements('.undo-user-transaction').forEach(function(button) { button.remove(); });
            }
            break;
         case 'settings':
            if(preferences && pathParts[5] === 'party') preferences.setParty(JSON.parse(msg));
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
    if(!zoek.length) {
      if(filterReturnView === 'commands') { filterReturnView=null; makeCommandScreen(commandCategory); return; }
      restoreSelection(filterRestore);
      return;
    }
    if(fill && zoek.length<2) return;
    if(!filterReturnView && currentView === 'commands') filterReturnView='commands';
    if(!filterRestore) filterRestore=selectionSnapshot();
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
    filtering=true;
    try {
      var accountList=filterRestore ? filterRestore.view.accountList : (tabenable === 2 || (buttons.length > 0 && buttons.every(function(button) {
        return button.class && button.class.indexOf('account ') === 0;
      })));
      makepages('normal',buttons,accountList);
      if(filterRestore) restoreExtraButtons(filterRestore);
    } finally {
      filtering=false;
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
    var command=searchValue().trim();
    if(currentView === 'sounds' && !['ns','vergaderen','vergaderenextreme','vergaderen_extreme','throw','yeet','sounds'].includes(command) && !/^(dark|banana|dank|confetti)mode(on|off)$/.test(command)) currentView='action';
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
    if(currentView === 'commands') locked=0;
    if(currentView !== 'sounds' || !['ns','vergaderen','vergaderenextreme','throw','yeet'].includes(String(this.id))) currentView='action';
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
    filterReturnView=null;
    if(this.id !== 'sounds') currentView='action';
    switch(this.id) {
      case 'members':
         locked=0;
         showAccountButtons(this.id,'m',tabenable || 1);
         break;
      case 'otherusers':
         locked=0;
         showAccountButtons(this.id,'o',tabenable || 1);
         break;
      case 'products':
         activateTopButton(this.id);
         locked=1;
         makepages('productgroups',window.HackBankButtons.productsToButtons(groups).sort(window.HackBankButtons.compareDisplay));
         focus();
         break;
      case 'commands':
         locked=0;
         makeCommandScreen();
         break;
      case 'sounds':
         locked=0;
         postmsg('input','sounds');
         setSearchValue('');
         focus();
         break;
      case 'back':
         currentView='overview';
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
         currentView='embedded';
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
    var logoAbort=createElement('button',{id: 'LogoAbort', class: 'brand brand-abort col-auto', type: 'button', title: 'Reset current sale', 'aria-label': 'Hack42 HackBank — Reset current sale'});
    appendChildren(logoAbort,[
      createElement('img',{class: 'brand-logo', src: 'images/Hack42.png', alt: 'Hack42 · Hackerspace Arnhem', width: '84', height: '56'}),
      appendChildren(createElement('span'), [
        createElement('span',{class: 'brand-name', text: 'hackbank'}),
        createElement('span',{class: 'brand-caption', text: 'HACK42 · BAR & DRINKS'}),
      ]),
    ]);
    logoAbort.addEventListener('click',function() {
      currentView='action';
      stopAudio();
      setSearchValue('abort');
      submitCommand();
    });
    header.appendChild(logoAbort);
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
      }
    });
    searchInput().addEventListener('input',function() {
      delay(function() {
        dotabfill(0);
      },200);
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
