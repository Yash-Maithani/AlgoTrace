/* The growth chart, shared by the Learn panel's Complexity tab and /big-o.
 *
 * Plain SVG, no library. The reference curves sit behind the one being
 * talked about, and a table carries the same numbers for anyone who cannot
 * see the picture, because a chart on its own is not accessible.
 *
 *   Growth.CURVES          every curve this can draw, by key
 *   Growth.ORDER           the five reference curves, in the order drawn
 *   Growth.render(host, o) draw into host; o is
 *                          {n, highlight, label, basis, note, width, height, log, key}
 *
 * `key: true` is for the chart that is about the curves themselves (/big-o), where
 * no one curve is the subject: each gets its own colour and its own line style, and
 * a legend under the chart names them, so the picture never depends on colour alone.
 * Beside an algorithm's own Complexity tab the chart stays as it was: faint
 * references and the one curve that is the algorithm's, in the accent.
 *
 * Nothing here knows which algorithm is being described. The caller passes
 * the figure to show (`label`), which curve has that shape (`highlight`, or
 * null when none does), what the axis letter stands for when it is not n
 * (`basis`), and the sentence to use when no curve fits (`note`). Every one
 * of those comes from the algorithm's own lesson file, which is the single
 * source of truth for its complexity.
 */
(function () {
    'use strict';

    var CURVES = {
        '1': { label: 'O(1)', of: function () { return 1; } },
        'logn': { label: 'O(log n)', of: function (n) { return Math.log2(n + 1); } },
        'n': { label: 'O(n)', of: function (n) { return n; } },
        'nlogn': { label: 'O(n log n)', of: function (n) { return n * Math.log2(n + 1); } },
        'n2': { label: 'O(n squared)', of: function (n) { return n * n; } },
        /* Not a reference curve: /big-o teaches five, and this one is only
           drawn when an algorithm actually has that shape. Floyd-Warshall
           does. */
        'n3': { label: 'O(n cubed)', of: function (n) { return n * n * n; } },
        /* Not a reference curve either: jump search has this shape. */
        'sqrtn': { label: 'O(square root of n)', of: function (n) { return Math.sqrt(n); } }
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

    /* The curves to draw: the five references, plus the highlighted one when
       it is not already among them. */
    function drawn(highlight) {
        var keys = ORDER.slice();
        if (highlight && keys.indexOf(highlight) === -1) keys.push(highlight);
        return keys;
    }

    /* What the caption and the aria-label say. The figure always comes from
       the caller; this only decides how it relates to the curve drawn. */
    function describe(options, n) {
        var highlight = options.highlight;
        var curve = highlight ? CURVES[highlight] : null;
        var label = options.label || (curve ? curve.label : null);
        var upTo = ' for n up to ' + n + '.';

        if (!label) {
            return 'The five common growth curves,' + upTo;
        }
        if (!curve) {
            var note = options.note ||
                (label + ' is not one of the curves below.');
            return note + ' They are drawn for comparison,' + upTo;
        }
        if (label === curve.label) {
            return 'This algorithm is ' + label + '. The faint lines are the others,' + upTo;
        }
        /* Same shape, different letter: Dijkstra is O(V squared), which is the
           O(n squared) curve with n standing for the number of nodes. Saying
           so is the difference between a comparison and a wrong figure. */
        return 'This algorithm is ' + label + ', which is the ' + curve.label +
            ' curve with n standing for ' + (options.basis || 'the input size') +
            '. The faint lines are the others,' + upTo;
    }

    function render(host, options) {
        if (!host) return;
        options = options || {};
        var highlight = options.highlight && CURVES[options.highlight]
            ? options.highlight : null;
        var n = Math.max(options.n || 0, 10);
        var width = options.width || 260;
        var height = options.height || 160;
        var pad = 24;

        clear(host);

        /* On a linear axis a big n flattens the slower curves onto the
           floor, because the fastest growing one dwarfs them. True, but it
           hides exactly the comparison this chart is for, so the caller can
           ask for a log axis instead, which keeps every curve readable and
           still shows which one climbs fastest. */
        var log = !!options.log;
        var scale = log
            ? function (value) { return Math.log10(value + 1); }
            : function (value) { return value; };

        var keyed = !!options.key && !highlight;
        var keys = drawn(highlight);
        var highest = 0;
        keys.forEach(function (key) {
            highest = Math.max(highest, scale(CURVES[key].of(n)));
        });
        if (highest <= 0) highest = 1;

        var sentence = describe(options, n);
        var axisNote = log ? ' The vertical axis is logarithmic.' : '';

        var svg = document.createElementNS(SVG_NS, 'svg');
        svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
        svg.setAttribute('class', 'growth-chart');
        svg.setAttribute('role', 'img');
        svg.setAttribute('aria-label', sentence + axisNote);

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
            node.setAttribute('class', keyed ? 'growth-curve' : key === highlight ? 'growth-mine' : 'growth-ref');
            node.setAttribute('data-curve', key);
            return node;
        }

        /* One legend row: a short sample of the line, in the curve's own colour and
           dash, then its name. The sample is decoration; the name is the text. */
        function legendItem(key) {
            var item = el('li', 'growth-legend-item');
            var sample = document.createElementNS(SVG_NS, 'svg');
            sample.setAttribute('class', 'growth-key');
            sample.setAttribute('viewBox', '0 0 40 10');
            sample.setAttribute('width', '40');
            sample.setAttribute('height', '10');
            sample.setAttribute('aria-hidden', 'true');
            sample.setAttribute('focusable', 'false');
            var line = document.createElementNS(SVG_NS, 'line');
            line.setAttribute('x1', '3');
            line.setAttribute('x2', '37');
            line.setAttribute('y1', '5');
            line.setAttribute('y2', '5');
            line.setAttribute('class', 'growth-curve');
            line.setAttribute('data-curve', key);
            sample.appendChild(line);
            item.appendChild(sample);
            item.appendChild(el('span', null, CURVES[key].label));
            return item;
        }

        keys.forEach(function (key) { if (key !== highlight) svg.appendChild(path(key)); });
        if (highlight) svg.appendChild(path(highlight));
        host.appendChild(svg);

        if (keyed) {
            /* Slowest growth first, which is the order the curves leave the floor. */
            var legend = el('ul', 'growth-legend');
            legend.setAttribute('aria-label', 'Which line is which');
            keys.forEach(function (key) { legend.appendChild(legendItem(key)); });
            host.appendChild(legend);
        }

        var caption = el('p', 'growth-caption', sentence + axisNote);
        host.appendChild(caption);

        var details = el('details', 'growth-data');
        details.appendChild(el('summary', null, 'The same numbers as a table'));
        var table = el('table', 'var-table');
        var head = el('tr');
        head.appendChild(el('th', null, 'Curve'));
        head.appendChild(el('th', null, 'At n = ' + n));
        table.appendChild(head);
        keys.forEach(function (key) {
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
