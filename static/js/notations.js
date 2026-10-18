/* The "tight bound" explorer on /big-o: f(n) between c1*g(n) and c2*g(n)
 * from n0 on. Plain SVG, no animation, nothing hidden under reduced motion.
 *
 * The model (what counts as a bound) is separate from the drawing so a test
 * can run it under node. Needs the ids used in templates/big_o.html.
 */
(function (root) {
    'use strict';

    /* f is real work counted on this site, plus one invented function with
       the lower order terms Big O is meant to ignore. */
    var FUNCTIONS = {
        bubble: function (n) { return n * (n - 1) / 2; },
        insertion: function (n) { return n - 1; },
        example: function (n) { return 3 * n * n + 20 * n + 50; }
    };

    var SHAPES = {
        n2: { value: function (n) { return n * n; }, spoken: 'n squared', text: 'n²' },
        nlogn: { value: function (n) { return n * Math.log2(n); }, spoken: 'n log n', text: 'n log n' },
        n: { value: function (n) { return n; }, spoken: 'n', text: 'n' }
    };

    /* Sizes the check looks at: every integer from n0 to 2000, then a few far
       larger ones, because a ceiling that holds to 2000 can still lose later. */
    var FAR = [1e4, 1e5, 1e6, 1e7];
    var EPS = 1e-9;

    /* Does the ceiling (f <= c2 g) and the floor (f >= c1 g) hold from n0 on?
       Returns whether each holds and the first size where it does not. */
    function check(f, g, c1, c2, n0) {
        var upper = { holds: true, at: null };
        var lower = { holds: true, at: null };
        function look(n) {
            var fv = f(n), gv = g(n);
            if (upper.holds && fv > c2 * gv + EPS) { upper.holds = false; upper.at = n; }
            if (lower.holds && fv < c1 * gv - EPS) { lower.holds = false; lower.at = n; }
        }
        for (var n = Math.max(1, n0); n <= 2000; n++) look(n);
        FAR.forEach(look);
        return { upper: upper, lower: lower, tight: upper.holds && lower.holds };
    }

    var api = { FUNCTIONS: FUNCTIONS, SHAPES: SHAPES, check: check };
    if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
    root.Notations = api;

    var chartHost = document.getElementById('nt-chart');
    if (!chartHost) return;

    var SVG = 'http://www.w3.org/2000/svg';
    var $ = function (id) { return document.getElementById(id); };
    var controls = { f: $('nt-f'), g: $('nt-g'), c1: $('nt-c1'), c2: $('nt-c2'), n0: $('nt-n0') };
    var verdict = $('nt-verdict');

    var W = 560, H = 300, PAD = { l: 44, r: 12, t: 12, b: 34 };
    var N_MAX = 60;

    function svg(tag, attrs, text) {
        var node = document.createElementNS(SVG, tag);
        Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, attrs[k]); });
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function html(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    /* A symbol seen as itself and heard as its name. */
    function symbol(shown, spoken) {
        var node = html('span', 'notation');
        var visible = html('span', null, shown);
        visible.setAttribute('aria-hidden', 'true');
        node.appendChild(visible);
        node.appendChild(html('span', 'sr-only', spoken));
        return node;
    }

    function say(parts) {
        while (verdict.firstChild) verdict.removeChild(verdict.firstChild);
        parts.forEach(function (part) {
            verdict.appendChild(typeof part === 'string' ? document.createTextNode(part) : part);
        });
    }

    function draw() {
        var f = FUNCTIONS[controls.f.value];
        var shape = SHAPES[controls.g.value];
        var g = shape.value;
        var c1 = Number(controls.c1.value);
        var c2 = Number(controls.c2.value);
        var n0 = Number(controls.n0.value);
        $('nt-c1-out').textContent = 'c1 = ' + c1;
        $('nt-c2-out').textContent = 'c2 = ' + c2;
        $('nt-n0-out').textContent = 'n0 = ' + n0;

        var top = Math.max(f(N_MAX), c1 * g(N_MAX), 1) * 1.2;
        var plotW = W - PAD.l - PAD.r, plotH = H - PAD.t - PAD.b;
        function x(n) { return PAD.l + (n - 1) / (N_MAX - 1) * plotW; }
        function y(v) { return PAD.t + plotH - Math.min(v, top * 1.5) / top * plotH; }
        function path(fn) {
            var d = [];
            for (var n = 1; n <= N_MAX; n++) d.push((n === 1 ? 'M' : 'L') + x(n).toFixed(1) + ' ' + y(fn(n)).toFixed(1));
            return d.join(' ');
        }

        var chart = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'class': 'nt-svg' });
        var clip = svg('clipPath', { id: 'nt-clip' });
        clip.appendChild(svg('rect', { x: PAD.l, y: PAD.t, width: plotW, height: plotH }));
        chart.appendChild(svg('defs')).appendChild(clip);

        // From n0 on is where the claim is made.
        chart.appendChild(svg('rect', {
            'class': 'nt-from', x: x(n0), y: PAD.t, width: Math.max(0, PAD.l + plotW - x(n0)), height: plotH
        }));
        chart.appendChild(svg('line', { 'class': 'nt-axis', x1: PAD.l, y1: PAD.t + plotH, x2: PAD.l + plotW, y2: PAD.t + plotH }));
        chart.appendChild(svg('line', { 'class': 'nt-axis', x1: PAD.l, y1: PAD.t, x2: PAD.l, y2: PAD.t + plotH }));
        chart.appendChild(svg('line', { 'class': 'nt-n0', x1: x(n0), y1: PAD.t, x2: x(n0), y2: PAD.t + plotH }));
        chart.appendChild(svg('text', { 'class': 'nt-label', x: x(n0) + 4, y: PAD.t + 12 }, 'n0'));
        chart.appendChild(svg('text', { 'class': 'nt-label', x: PAD.l + plotW / 2, y: H - 8, 'text-anchor': 'middle' }, 'n, the size of the input'));
        chart.appendChild(svg('text', { 'class': 'nt-label', x: 12, y: PAD.t + plotH / 2, 'text-anchor': 'middle',
            transform: 'rotate(-90 12 ' + (PAD.t + plotH / 2) + ')' }, 'work'));

        var curves = svg('g', { 'clip-path': 'url(#nt-clip)' });
        curves.appendChild(svg('path', { 'class': 'nt-curve nt-hi', d: path(function (n) { return c2 * g(n); }) }));
        curves.appendChild(svg('path', { 'class': 'nt-curve nt-lo', d: path(function (n) { return c1 * g(n); }) }));
        curves.appendChild(svg('path', { 'class': 'nt-curve nt-f', d: path(f) }));
        chart.appendChild(curves);

        var result = check(f, g, c1, c2, n0);
        var gName = shape.spoken, gShown = shape.text;
        var summary = result.tight
            ? 'From n0 = ' + n0 + ', f stays between c1 times g and c2 times g: theta of ' + gName + '.'
            : 'From n0 = ' + n0 + ', f does not stay between c1 times g and c2 times g.';
        chart.setAttribute('aria-label', 'Chart of f(n), c1 times g(n) and c2 times g(n) for n from 1 to ' +
            N_MAX + '. ' + summary);
        while (chartHost.firstChild) chartHost.removeChild(chartHost.firstChild);
        chartHost.appendChild(chart);

        var key = html('ul', 'nt-key');
        [['nt-f', 'f(n), the work'], ['nt-lo', 'c1 × g(n), the floor'], ['nt-hi', 'c2 × g(n), the ceiling']]
            .forEach(function (item) {
                var li = html('li');
                var sw = html('span', 'nt-swatch ' + item[0]);
                sw.setAttribute('aria-hidden', 'true');
                li.appendChild(sw);
                li.appendChild(document.createTextNode(item[1]));
                key.appendChild(li);
            });
        chartHost.appendChild(key);

        var O = symbol('O(' + gShown + ')', 'Big O of ' + gName);
        var Om = symbol('Ω(' + gShown + ')', 'Omega of ' + gName);
        var Th = symbol('Θ(' + gShown + ')', 'Theta of ' + gName);
        if (result.tight) {
            say(['Both halves hold from n0 = ' + n0 + ' on, so with these constants f is ', Th,
                 ': the ceiling gives ', O, ' and the floor gives ', Om, '.']);
        } else if (result.upper.holds) {
            say(['The ceiling holds, so f is ', O, ', but the floor fails at n = ' + result.lower.at +
                 ': f grows more slowly than g, so it is not ', Om, ' and not tight. Lower c1, or pick a smaller g.']);
        } else if (result.lower.holds) {
            say(['The floor holds, so f is ', Om, ', but the ceiling fails at n = ' + result.upper.at +
                 ': f outgrows c2 times g, so it is not ', O, ' and not tight. Raise c2, or pick a bigger g.']);
        } else {
            say(['Neither half holds from n0 = ' + n0 + ': the ceiling fails at n = ' + result.upper.at +
                 ' and the floor at n = ' + result.lower.at + '. Move the constants or n0, or pick another g.']);
        }
    }

    Object.keys(controls).forEach(function (k) {
        controls[k].addEventListener('input', draw);
        controls[k].addEventListener('change', draw);
    });
    draw();
})(typeof window !== 'undefined' ? window : this);
