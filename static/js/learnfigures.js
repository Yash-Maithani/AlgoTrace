/* The complexity figures on /learn, read from the lesson files.
 *
 * Every card and every row of the suggested order carries
 * data-lesson="<id>" and data-figure="best", "worst" or "space"; this fills
 * them from window.LESSONS, the same lesson data the Complexity tab prints,
 * so /learn cannot say one thing while the lesson says another.
 *
 * The lessons write figures in words ('O(n squared)'); the page shows them
 * with symbols for the eye (n², V·E, √n) and keeps the words for a screen
 * reader, the way the Complexity tab does.
 */
(function (root) {
    'use strict';

    var SYMBOLS = [
        [/square root of n/g, '√n'],
        [/ squared/g, '²'],
        [/ cubed/g, '³'],
        [/ times \(([^)]*)\)/g, '($1)'],
        [/ times /g, '·'],
        [/ plus /g, ' + ']
    ];

    function symbols(value) {
        var out = value;
        SYMBOLS.forEach(function (rule) { out = out.replace(rule[0], rule[1]); });
        return out;
    }

    function figureOf(lesson, which) {
        var c = lesson && lesson.complexity;
        if (!c) return null;
        if (which === 'space') return c.space && c.space.value;
        return c.time && c.time[which] && c.time[which].value;
    }

    function fill(doc, lessons) {
        var missing = [];
        Array.prototype.forEach.call(doc.querySelectorAll('[data-lesson][data-figure]'), function (node) {
            var value = figureOf(lessons[node.getAttribute('data-lesson')], node.getAttribute('data-figure'));
            if (!value) {
                missing.push(node.getAttribute('data-lesson'));
                return;
            }
            node.textContent = '';
            var seen = doc.createElement('span');
            seen.setAttribute('aria-hidden', 'true');
            seen.textContent = symbols(value);
            var spoken = doc.createElement('span');
            spoken.className = 'sr-only';
            spoken.textContent = value.replace(/^O\((.*)\)$/, 'Big O of $1');
            node.appendChild(seen);
            node.appendChild(spoken);
        });
        return missing;
    }

    var api = { symbols: symbols, figureOf: figureOf, fill: fill };
    if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
    root.LearnFigures = api;
    fill(document, root.LESSONS || {});
})(typeof window !== 'undefined' ? window : this);
