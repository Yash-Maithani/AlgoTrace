/* The growth chart, shared by the Learn panel's Complexity tab and /big-o.
 *
 * Plain SVG, no library. The reference curves sit behind the one being
 * talked about, and a table carries the same numbers for anyone who cannot
 * see the picture, because a chart on its own is not accessible.
 *
 *   Growth.CURVES          the five curves, by key
 *   Growth.ORDER           the order they are drawn and listed in
 *   Growth.render(host, o) draw into host; o is
 *                          {n, highlight, width, height, log}
 *
 * Nothing here knows which algorithm is being described. The caller says
 * which curve to highlight and for what input size.
 */
(function () {
    'use strict';

    var CURVES = {
        '1': { label: 'O(1)', of: function () { return 1; } },
        'logn': { label: 'O(log n)', of: function (n) { return Math.log2(n + 1); } },
        'n': { label: 'O(n)', of: function (n) { return n; } },
        'nlogn': { label: 'O(n log n)', of: function (n) { return n * Math.log2(n + 1); } },
        'n2': { label: 'O(n squared)', of: function (n) { return n * n; } }
    };

    var ORDER = ['1', 'logn', 'n', 'nlogn', 'n2'];

    var SVG_NS = 'http://www.w3.org/2000/svg';

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function clear(node) {
        while (node.firstChild) node.removeChild(node.firstChild);
    }

    function round(value) {
        return Math.round(value * 10) / 10;
    }

    function render(host, options) {
        if (!host) return;
        options = options || {};
        var highlight = options.highlight;
        var n = Math.max(options.n || 0, 10);
        var width = options.width || 260;
        var height = options.height || 160;
        var pad = 24;

        clear(host);

        /* On a linear axis a big n flattens the four slower curves onto the
           floor, because n squared dwarfs them. True, but it hides exactly
           the comparison this chart is for, so the caller can ask for a log
           axis instead, which keeps every curve readable and still shows
           which one climbs fastest. */
        var log = !!options.log;
        var scale = log
            ? function (value) { return Math.log10(value + 1); }
            : function (value) { return value; };

        var highest = 0;
        ORDER.forEach(function (key) {
            highest = Math.max(highest, scale(CURVES[key].of(n)));
        });
        if (highest <= 0) highest = 1;

        var svg = document.createElementNS(SVG_NS, 'svg');
        svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
        svg.setAttribute('class', 'growth-chart');
        svg.setAttribute('role', 'img');
        var axisNote = log ? ' The vertical axis is logarithmic.' : '';
        svg.setAttribute('aria-label', highlight
            ? 'Growth of ' + CURVES[highlight].label + ' compared with the other '
              + 'common curves, for inputs up to ' + n + '.' + axisNote
            : 'The five common growth curves, for inputs up to ' + n + '.' + axisNote);

        function path(key) {
            var points = [];
            for (var x = 1; x <= n; x++) {
                var px = pad + ((x - 1) / Math.max(n - 1, 1)) * (width - pad * 2);
                var py = height - pad - (scale(CURVES[key].of(x)) / highest) * (height - pad * 2);
                points.push((x === 1 ? 'M' : 'L') + px.toFixed(1) + ' ' + py.toFixed(1));
            }
            var node = document.createElementNS(SVG_NS, 'path');
            node.setAttribute('d', points.join(' '));
            node.setAttribute('fill', 'none');
            node.setAttribute('class', key === highlight ? 'growth-mine' : 'growth-ref');
            node.setAttribute('data-curve', key);
            return node;
        }

        ORDER.forEach(function (key) { if (key !== highlight) svg.appendChild(path(key)); });
        if (highlight) svg.appendChild(path(highlight));
        host.appendChild(svg);

        var caption = el('p', 'growth-caption');
        if (highlight) {
            caption.appendChild(document.createTextNode('This algorithm is '));
            caption.appendChild(el('strong', null, CURVES[highlight].label));
            caption.appendChild(document.createTextNode(
                '. The faint lines are the others, for n up to ' + n + '.'));
        } else {
            caption.textContent = 'All five curves, for n up to ' + n +
                '. The steeper the line, the worse it scales.' + axisNote;
        }
        host.appendChild(caption);

        var details = el('details', 'growth-data');
        details.appendChild(el('summary', null, 'The same numbers as a table'));
        var table = el('table', 'var-table');
        var head = el('tr');
        head.appendChild(el('th', null, 'Curve'));
        head.appendChild(el('th', null, 'At n = ' + n));
        table.appendChild(head);
        ORDER.forEach(function (key) {
            var row = el('tr');
            row.appendChild(el('td', null,
                CURVES[key].label + (key === highlight ? ' (this one)' : '')));
            row.appendChild(el('td', null, String(round(CURVES[key].of(n)))));
            table.appendChild(row);
        });
        details.appendChild(table);
        host.appendChild(details);
    }

    window.Growth = { CURVES: CURVES, ORDER: ORDER, render: render };
})();
