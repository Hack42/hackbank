(function(window) {
  function sortText(a, b) {
    var alc = a.toLowerCase();
    var blc = b.toLowerCase();
    return alc > blc ? 1 : alc < blc ? -1 : 0;
  }

  function compareTextReverse(a, b) {
    if(a.text > b.text) return -1;
    if(a.text < b.text) return 1;
    return 0;
  }

  function compareDisplay(a, b) {
    if(a.display < b.display) return -1;
    if(a.display > b.display) return 1;
    return 0;
  }

  function cssSafeClassName(value) {
    return String(value).replace(/[^A-Za-z0-9_-]/g, "-");
  }

  function rebuildProductIndexes(products, groups, productsWithoutBarcode) {
    Object.keys(groups).forEach(function(group) {
      delete groups[group];
    });
    Object.keys(productsWithoutBarcode).forEach(function(product) {
      delete productsWithoutBarcode[product];
    });

    Object.keys(products).forEach(function(productName) {
      var product = products[productName];
      var barcode = false;

      groups[product.group] = (groups[product.group] || 0) + 1;
      product.aliases.forEach(function(alias) {
        if(alias > 9999999) barcode = true;
      });
      if(!barcode) {
        productsWithoutBarcode[productName] = product;
      }
    });
  }

  function productsToButtons(products) {
    var buttons = [];
    Object.keys(products).sort().forEach(function(productName) {
      buttons.push({text: productName, display: productName, class: productName});
    });
    return buttons;
  }

  function visibleCommandButtons(buttons) {
    var hiddenSoundCommands=['deuroff', 'deuron', 'groovesalad', 'blues', 'killsounds', 'louder', 'quieter', 'kassaoff', 'kassaon'];
    return buttons.filter(function(button) {
      return hiddenSoundCommands.indexOf(button.text) === -1;
    });
  }

  function commandsToButtons(commands) {
    var buttons = [];
    Object.keys(commands).sort().forEach(function(command) {
      buttons.push({text: command, display: commands[command], class: command});
    });
    return visibleCommandButtons(buttons);
  }

  function commandSections(commands) {
    var definitions=[
      ['Products', [['addproduct','Add new'], ['aliasproduct','Add alias'], ['setprice','Change price'], ['voorraad','Set stock']]],
      ['Users', [['deposit','Deposit Money'], ['give','Give Money'], ['take','Take Money'], ['adduseralias','Add user key alias'], ['members','Manage members']]],
      ['Sales', [['bon','Print Receipt'], ['kassala','Open cash drawer'], ['undolist','Undo a transaction'], ['undo','Undo last transaction'], ['history','User History']]],
      ['Wholesale', [['declaratie','Declaration'], ['printstock','Print stock overview'], ['bons','Receipts to print'], ['remove','Remove item'], ['afroom','Remove cash money'], ['delmember','Remove user from members'], ['inkoop','Report buying'], ['verkoop','Report sales'], ['restore','Restore a transaction'], ['pfand','Return deposit']]],
      ['Market', [['market','Products'], ['changemarket','Pricing'], ['addmarket','Aliases'], ['delmarket','Remove product']]],
      ['Misc', [['sounds','Sounds'], ['stickers','Stickers'], ['dooropen','Door open']]],
    ];
    var hidden=['abort','addmember','partymodeon','partymodeoff','darkmodeon','darkmodeoff','bananamodeon','bananamodeoff','dankmodeon','dankmodeoff','confettimodeon','confettimodeoff','undouserlatest'];
    var used=new Set(hidden);
    var sections=definitions.map(function(definition) {
      return {name: definition[0], buttons: definition[1].filter(function(item) {
        used.add(item[0]);
        return Object.prototype.hasOwnProperty.call(commands,item[0]);
      }).map(function(item) {
        return {text: item[0], display: item[1], class: item[0], hint: item[0] === 'remove' ? 'Current, unbilled sale' : ''};
      })};
    });
    var extra=commandsToButtons(commands).filter(function(button) { return !used.has(button.text); });
    sections[sections.length-1].buttons=sections[sections.length-1].buttons.concat(extra);
    return sections;
  }

  function visibleSoundButtons(buttons) {
    return visibleCommandButtons(buttons).filter(function(button) {
      return button.text !== 'abort' && button.text !== 'christmas';
    });
  }

  function splitAccounts(candidates, accounts, activity) {
    var active=[], archive=[];
    candidates.forEach(function(button) {
      var last=activity && activity.last_purchase && activity.last_purchase[button.text];
      if(!last) last=accounts[button.text].lastupdate;
      var old=activity && activity.available && /^\d{4}-\d{2}-\d{2}/.test(last || '') && last < activity.cutoff;
      if(old) {
        button.class+=' archived-account';
        archive.push(button);
      } else active.push(button);
    });
    return {active: active, archive: archive};
  }

  function accountsToButtons(accounts, members, nonmembers, type) {
    var buttons = [];
    Object.keys(accounts).sort(sortText).forEach(function(user) {
      var isMember = members.indexOf(user) !== -1;
      var isNonMember = nonmembers.indexOf(user) !== -1;
      var amount = accounts[user].amount;
      var extraclass = user;
      var theme = {jos: 'lockpicker', nino: 'ukraine', anus: 'plasma'}[user.toLowerCase()];

      if(
        !((isMember && type === 'm') ||
          (isNonMember && type === 'o') ||
          (!isMember && !isNonMember && type === 'x'))
      ) {
        return;
      }

      if(amount < -13.37) {
        extraclass = user + " rood";
      } else if(amount < 0) {
        extraclass = user + " orange";
      }
      buttons.push({
        text: user,
        display: user,
        class: "account account-" + cssSafeClassName(user) + (theme ? " account-theme-" + theme : ""),
        rightclass: extraclass,
        right: amount.toFixed(2),
        fill: true,
      });
    });
    return buttons;
  }

  function pricedProductButton(products, stock, productName) {
    var button = {
      text: productName,
      display: products[productName].description,
      right: products[productName].price.toFixed(2),
      rightclass: "green",
      class: productName,
    };

    if(stock[productName] !== undefined && Number(stock[productName]) !== 0) {
      button.left = stock[productName];
      button.leftclass = 'orange';
    }
    return button;
  }

  function allProductsToButtons(products, stock) {
    var buttons = [];
    Object.keys(products).forEach(function(productName) {
      var button = pricedProductButton(products, stock, productName);
      button.aliases = products[productName].aliases;
      buttons.push(button);
    });
    return buttons;
  }

  function productGroupToButtons(products, stock, group) {
    var buttons = [];
    Object.keys(products).sort().forEach(function(productName) {
      if(products[productName].group === group) {
        buttons.push(pricedProductButton(products, stock, productName));
      }
    });
    return buttons;
  }

  function buttonMatches(button, query) {
    return button.text.toLowerCase().startsWith(query) ||
      button.display.toLowerCase().startsWith(query);
  }

  function addMatchingButtons(matches, candidates, query) {
    candidates.forEach(function(candidate) {
      if(buttonMatches(candidate, query)) {
        matches.push(candidate);
      }
    });
  }

  window.HackBankButtons = {
    accountsToButtons: accountsToButtons,
    addMatchingButtons: addMatchingButtons,
    allProductsToButtons: allProductsToButtons,
    buttonMatches: buttonMatches,
    commandsToButtons: commandsToButtons,
    commandSections: commandSections,
    visibleSoundButtons: visibleSoundButtons,
    splitAccounts: splitAccounts,
    compareDisplay: compareDisplay,
    compareTextReverse: compareTextReverse,
    cssSafeClassName: cssSafeClassName,
    productGroupToButtons: productGroupToButtons,
    productsToButtons: productsToButtons,
    rebuildProductIndexes: rebuildProductIndexes,
    visibleCommandButtons: visibleCommandButtons,
  };
})(window);
