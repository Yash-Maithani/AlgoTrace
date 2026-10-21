/* Input presets for the Sorting and Searching setup columns.
 *
 * The generators are pure functions of a seed, so a preset can be reproduced
 * from the number shown next to it. mount() wires the buttons and the one
 * line of explanation under them; the line comes from the lesson's
 * presetNotes, so what a preset means for an algorithm is lesson data.
 *
 *   Presets.mount({
 *     host,            element to build the buttons in
 *     getLesson(),     the lesson of the chosen algorithm
 *     getSize(),       how many values to generate
 *     apply(values),   put the values into the page's input
 *   })
 */
(function (root) {
    'use strict';

    var ORDER = ['random', 'sorted', 'reversed', 'equal', 'nearly'];
    var LABELS = {
        random: 'Random',
        sorted: 'Already sorted',
        reversed: 'Reversed',
        equal: 'All equal',
        nearly: 'Nearly sorted'
    };

    /* mulberry32: small, fast and the same in every browser. */
    function rng(seed) {
        var a = seed >>> 0;
        return function () {
            a = (a + 0x6D2B79F5) >>> 0;
            var t = a;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    /* Every random value on the site is a whole number from 1 to
       RANDOM_MAX, the same range the server uses (algotrace/routes/sorting.py), inside the 0 to 99 that
       Counting and Radix Sort accept. */
    var RANDOM_MAX = 99;

    function randomValues(n, next) {
        var out = [];
        for (var i = 0; i < n; i++) out.push(1 + Math.floor(next() * RANDOM_MAX));
        return out;
    }

    function ascending(a, b) { return a - b; }

    function generate(kind, n, seed) {
        var next = rng(seed);
        var values = randomValues(n, next);
        switch (kind) {
            case 'sorted':
                return values.sort(ascending);
            case 'reversed':
                return values.sort(ascending).reverse();
            case 'equal':
                return values.map(function () { return values[0]; });
            case 'nearly':
                values.sort(ascending);
                // About one adjacent pair in ten is swapped, never the same
                // pair twice, so the list stays close to sorted.
                var swaps = Math.max(1, Math.round(n / 10));
                var used = {};
                var done = 0;
                var guard = 0;
                while (done < swaps && guard++ < 1000) {
                    var i = Math.floor(next() * (n - 1));
                    if (used[i] || used[i + 1] || used[i - 1]) continue;
                    used[i] = used[i + 1] = true;
                    var t = values[i]; values[i] = values[i + 1]; values[i + 1] = t;
                    done++;
                }
                return values;
            default:
                return values;
        }
    }

    function offered(lesson) {
        var list = lesson && lesson.presets;
        return list && list.length ? list : ORDER;
    }

    function newSeed() { return 1 + Math.floor(Math.random() * 99999); }

    function mount(options) {
        var host = options.host;
        var chosen = null;
        var seed = null;
        var buttons = {};

        var group = document.createElement('div');
        group.className = 'setup-row preset-row';
        group.setAttribute('role', 'group');
        group.setAttribute('aria-label', 'Input presets');
        var note = document.createElement('p');
        note.className = 'setup-hint preset-note';
        note.setAttribute('role', 'status');

        ORDER.forEach(function (kind) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'btn btn-secondary btn-sm';
            b.textContent = LABELS[kind];
            b.setAttribute('data-preset', kind);
            b.setAttribute('aria-pressed', 'false');
            b.addEventListener('click', function () {
                chosen = kind;
                seed = newSeed();
                options.apply(generate(kind, options.getSize(), seed));
                refresh();
            });
            buttons[kind] = b;
            group.appendChild(b);
        });
        host.appendChild(group);
        host.appendChild(note);

        function refresh() {
            var lesson = options.getLesson();
            var allowed = offered(lesson);
            ORDER.forEach(function (kind) {
                var ok = allowed.indexOf(kind) !== -1;
                buttons[kind].hidden = !ok;
                buttons[kind].setAttribute('aria-pressed', kind === chosen ? 'true' : 'false');
            });
            if (!chosen || allowed.indexOf(chosen) === -1) {
                note.textContent = '';
                return;
            }
            var notes = (lesson && lesson.presetNotes) || {};
            var text = LABELS[chosen] + '. ' + (notes[chosen] || '');
            if (chosen === 'random' || chosen === 'nearly') text += ' Seed ' + seed + '.';
            note.textContent = text;
        }

        refresh();
        return { refresh: refresh };
    }

    var api = { RANDOM_MAX: RANDOM_MAX, generate: generate, rng: rng, offered: offered, ORDER: ORDER, LABELS: LABELS, mount: mount };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.Presets = api;
})(typeof window !== 'undefined' ? window : this);
