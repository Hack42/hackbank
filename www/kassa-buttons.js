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

  function commandsToButtons(commands) {
    var buttons = [];
    Object.keys(commands).sort().forEach(function(command) {
      buttons.push({text: command, display: commands[command], class: command});
    });
    return buttons;
  }

  function accountsToButtons(accounts, members, nonmembers, type) {
    var buttons = [];
    Object.keys(accounts).sort(sortText).forEach(function(user) {
      var isMember = members.indexOf(user) !== -1;
      var isNonMember = nonmembers.indexOf(user) !== -1;
      var amount = accounts[user].amount;
      var extraclass = user;

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
    compareDisplay: compareDisplay,
    compareTextReverse: compareTextReverse,
    productGroupToButtons: productGroupToButtons,
    productsToButtons: productsToButtons,
    rebuildProductIndexes: rebuildProductIndexes,
  };
})(window);
