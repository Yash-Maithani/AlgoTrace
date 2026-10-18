/* The Home code card. It shows the three lines of bubble sort that the hero
 * animation is working on, in the language the visitor chose anywhere on the
 * site. Without JavaScript the card keeps the Python it was served with.
 *
 * Needs codeview.js, lessons/bubble_sort.js and lessons/code/bubble_sort.js.
 */
(function () {
    'use strict';

    var pre = document.querySelector('.band-code');
    var host = document.getElementById('home-code-lang');
    if (!pre || !host || !window.CodeView || !window.LESSONS ||
        !window.LESSONS.bubble_sort) return;

    var lesson = window.LESSONS.bubble_sort;
    // The three lines in view, and the one the card points at.
    var SHOWN = ['walk', 'compare', 'swap'];
    var MARKED = 'compare';

    var picker = CodeView.control(function (id) { CodeView.setLanguage(id); });
    host.appendChild(picker.el);

    function draw() {
        var language = CodeView.getLanguage();
        picker.set(language);
        var data = CodeView.listing(lesson, language);
        if (!data) return;
        // The lines in view, plus the lines that finish a statement the
        // last of them starts: Java's swap is three lines under one id.
        var lines = [];
        var tail = null;
        data.lines.forEach(function (l) {
            if (SHOWN.indexOf(l.id) !== -1) {
                lines.push(l);
                tail = l.id === SHOWN[SHOWN.length - 1] ? l.indent || 0 : null;
            } else if (tail !== null && !l.id && (l.indent || 0) >= tail) {
                lines.push(l);
            } else {
                tail = null;
            }
        });
        if (!lines.length) return;
        var base = Math.min.apply(null, lines.map(function (l) { return l.indent || 0; }));

        var code = document.createElement('code');
        lines.forEach(function (line, i) {
            var pad = new Array(((line.indent || 0) - base) * 4 + 1).join(' ');
            var text = pad + line.text;
            var newline = i < lines.length - 1 ? '\n' : '';
            if (line.id === MARKED) {
                var mark = document.createElement('mark');
                mark.textContent = text;
                // The mark is a block and ends its own line: a newline after
                // it would leave an empty one.
                code.appendChild(mark);
            } else {
                code.appendChild(document.createTextNode(text + newline));
            }
        });
        while (pre.firstChild) pre.removeChild(pre.firstChild);
        pre.appendChild(code);
        pre.setAttribute('aria-label', CodeView.label(language) + ' code for the comparison');
    }

    CodeView.onChange(draw);
    draw();
})();
