(function(window) {
    function textfillElement(element, options) {
        if(element.closest && element.closest('.magic-button')) return element;
        var parent = element.parentElement;
        if(!parent || !parent.clientWidth || !parent.clientHeight) return element;

        // Labels can appear in different sized tiles. Measure their current
        // space each time instead of caching one size for every repeated name.
        element.style.fontSize = '';
        var labelStyle = window.getComputedStyle(element);
        var parentStyle = window.getComputedStyle(parent);
        var fontSize = Math.min(parseFloat(labelStyle.fontSize), options.maxFontPixels);
        var minFontSize = options.minFontPixels || 12;
        var maxWidth = element.clientWidth;
        var maxHeight = parent.clientHeight - parseFloat(parentStyle.paddingTop) - parseFloat(parentStyle.paddingBottom);

        element.style.fontSize = fontSize + 'px';
        while(fontSize > minFontSize && (element.scrollWidth > maxWidth || element.scrollHeight > maxHeight)) {
            fontSize = Math.max(minFontSize, fontSize - 0.5);
            element.style.fontSize = fontSize + 'px';
        }
        return element;
    }

    window.HackBankTextfill = {
        fillElement: textfillElement,
    };
})(window);
