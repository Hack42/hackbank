var cachepixels = {};
var cachetop = {};

(function($) {
    $.fn.textfill = function(options) {
        var fontSize = options.maxFontPixels;
        var maxHeight = $(this).parent().height();
        var maxWidth = $(this).parent().width();
        var textHeight;
        var textWidth;
        if(cachepixels[this.text()] > 0) {
            this.css('font-size', cachepixels[this.text()] + 'vh');
            this.css('top', cachetop[this.text()]);
            return this;
        }
        do {
            this.css('font-size', fontSize + 'vh');
            textHeight = this.height();
            textWidth = this.width();
            cachepixels[this.text()] = fontSize;
            fontSize = fontSize - 0.9;
        } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 0.5);
        textHeight = this.height();
        var mytop = (maxHeight - textHeight) / 2;
        this.css('top', mytop);
        cachetop[this.text()] = mytop;
        return this;
    };
})(jQuery);
