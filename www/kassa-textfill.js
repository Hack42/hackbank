var cachepixels = {};
var cachetop = {};

(function(window) {
    function textfillElement(element, options) {
        var fontSize = options.maxFontPixels;
        var parent = element.parentElement;
        var maxHeight = parent ? parent.offsetHeight : 0;
        var maxWidth = parent ? parent.offsetWidth : 0;
        var text = element.textContent;
        var textHeight;
        var textWidth;
        if(cachepixels[text] > 0) {
            element.style.fontSize = cachepixels[text] + 'vh';
            element.style.top = cachetop[text];
            return element;
        }
        do {
            element.style.fontSize = fontSize + 'vh';
            textHeight = element.offsetHeight;
            textWidth = element.offsetWidth;
            cachepixels[text] = fontSize;
            fontSize = fontSize - 0.9;
        } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 0.5);
        textHeight = element.offsetHeight;
        cachetop[text] = ((maxHeight - textHeight) / 2) + 'px';
        element.style.top = cachetop[text];
        return element;
    }

    window.HackBankTextfill = {
        fillElement: textfillElement,
    };
})(window);
