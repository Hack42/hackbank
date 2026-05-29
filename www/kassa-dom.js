(function(window, document) {
  function firstElement(selector) {
    return document.querySelector(selector);
  }

  function allElements(selector) {
    if(selector.indexOf(':visible') === -1) {
      return Array.prototype.slice.call(document.querySelectorAll(selector));
    }
    return Array.prototype.slice.call(
      document.querySelectorAll(selector.replace(/:visible/g, ''))
    ).filter(function(element) {
      if(element.offsetWidth || element.offsetHeight) return true;
      if(element.getClientRects) return element.getClientRects().length > 0;
      return true;
    });
  }

  function showElement(selector) {
    var element = firstElement(selector);
    if(element) element.style.display = '';
  }

  function hideElement(selector) {
    var element = firstElement(selector);
    if(element) element.style.display = 'none';
  }

  function hideElements(selector) {
    allElements(selector).forEach(function(element) {
      element.style.display = 'none';
    });
  }

  function clearElement(selector) {
    var element = firstElement(selector);
    if(element) element.textContent = '';
  }

  function scrollToBottom(selector) {
    var element = firstElement(selector);
    if(element) element.scrollTop = element.scrollHeight;
  }

  function searchInput() {
    return document.getElementById('Zoek');
  }

  function searchValue() {
    var input = searchInput();
    return input ? input.value : "";
  }

  function setSearchValue(value) {
    var input = searchInput();
    if(input) input.value = value;
  }

  function appendSearchValue(value) {
    setSearchValue(searchValue() + value);
  }

  function fillVisibleText(selector) {
    allElements(selector).forEach(function(element) {
      window.HackBankTextfill.fillElement(element, {maxFontPixels: 5});
    });
  }

  function topButton(className, id, text) {
    return elementWithText("div", "Knopje Button " + className, id, "Paginatext", text);
  }

  function buttonElement(className, id, text) {
    return elementWithText("div", className, id, "Knopjetext", text);
  }

  function elementWithText(tagName, className, id, textClassName, text) {
    var element = document.createElement(tagName);
    var label = document.createElement("span");

    element.className = className;
    element.id = id;
    label.className = textClassName;
    label.textContent = text;
    element.appendChild(label);

    return element;
  }

  window.HackBankDom = {
    allElements: allElements,
    appendSearchValue: appendSearchValue,
    buttonElement: buttonElement,
    clearElement: clearElement,
    fillVisibleText: fillVisibleText,
    firstElement: firstElement,
    hideElement: hideElement,
    hideElements: hideElements,
    scrollToBottom: scrollToBottom,
    searchInput: searchInput,
    searchValue: searchValue,
    setSearchValue: setSearchValue,
    showElement: showElement,
    topButton: topButton,
  };
})(window, document);
