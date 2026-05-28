(function(window, document, $) {
  function firstElement(selector) {
    return document.querySelector(selector);
  }

  function allElements(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
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
    $(selector).each(function() {
      $(this).textfill({maxFontPixels: 5});
    });
  }

  function topButton(className, id, text) {
    return $('<div>', {class: "Knopje Button " + className, id: id})
      .append($('<span>', {class: "Paginatext", text: text}));
  }

  function buttonElement(className, id, text) {
    return $('<div>', {class: className, id: id})
      .append($('<span>', {class: "Knopjetext", text: text}));
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
})(window, document, jQuery);
