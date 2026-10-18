/* The Learn panel: Explain, Code, Complexity, About.
 *
 * Shared by every workspace. Nothing in this file knows about searching,
 * sorting or graphs. It is given a lesson object from window.LESSONS and a
 * step, and it renders what the contract in static/js/lessons/README.md says
 * those contain:
 *
 *   Teacher.mount({ panel, lesson })        build the tabs and static tabs
 *   Teacher.showStep(step, stats)           update Explain, Code and This run
 *   Teacher.setLesson(lesson)               switch algorithm without remounting
 *
 * `step` is any object with action, line, vars and explain. A sorting or
 * searching step is one directly; for graphs, pass the meta entry that runs
 * parallel to the step array.
 *
 * Tabs are a real tablist: arrow keys move, Home and End jump to the ends,
 * and only the selected tab is in the tab order (DESIGN section 7).
 *
 * Requires static/js/growth.js, which draws the Complexity tab's chart and
 * the one on /big-o from the same code.
 */
(function () {
    'use strict';

    var TABS = [
        { id: 'explain', label: 'Explain' },
        { id: 'code', label: 'Code' },
        { id: 'complexity', label: 'Complexity' },
        { id: 'about', label: 'About' }
    ];

    /* The curves and the chart live in static/js/growth.js, because /big-o
       draws the same picture with a slider on it. */
    var CURVES = window.Growth.CURVES;

    /* What the counted-moves row is called. Most sorts swap pairs; merge
       sort copies a merged run back over the array, so every element is
       written whether or not it moved. Counting those as swaps made the one
       sort that never swaps look like the most swap heavy on the site. */
    function countLabel(lesson) {
        var label = lesson && lesson.countLabel ? lesson.countLabel : 'swaps';
        return label.charAt(0).toUpperCase() + label.slice(1);
    }

    /* Which of the reported sizes the lesson's figure is written in. */
    function axisLetter(complexity) {
        var basis = complexity.growthBasis;
        return basis ? basis.split(',')[0] : 'n';
    }

    function axisSize(complexity, stats) {
        if (axisLetter(complexity) === 'E') return stats.edges;
        return stats.n;
    }

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function clear(node) {
        while (node.firstChild) node.removeChild(node.firstChild);
    }

    function Panel(options) {
        this.root = options.panel;
        this.lesson = options.lesson || null;
        this.codeView = null;
        this.active = 'explain';
        this.build();
        if (this.lesson) this.renderStatic();
    }

    Panel.prototype.build = function () {
        var self = this;
        clear(this.root);

        var strip = el('div', 'learn-tabs');
        strip.setAttribute('role', 'tablist');
        strip.setAttribute('aria-label', 'Learn panel');
        this.tabs = {};
        this.bodies = {};

        TABS.forEach(function (tab) {
            var button = el('button', 'learn-tab', tab.label);
            button.type = 'button';
            button.id = 'learn-tab-' + tab.id;
            button.setAttribute('role', 'tab');
            button.setAttribute('aria-controls', 'learn-body-' + tab.id);
            button.setAttribute('aria-selected', tab.id === self.active ? 'true' : 'false');
            button.tabIndex = tab.id === self.active ? 0 : -1;
            button.addEventListener('click', function () { self.select(tab.id, true); });
            strip.appendChild(button);
            self.tabs[tab.id] = button;
        });

        strip.addEventListener('keydown', function (event) {
            var ids = TABS.map(function (t) { return t.id; });
            var at = ids.indexOf(self.active);
            var next = null;
            if (event.key === 'ArrowRight') next = ids[(at + 1) % ids.length];
            else if (event.key === 'ArrowLeft') next = ids[(at - 1 + ids.length) % ids.length];
            else if (event.key === 'Home') next = ids[0];
            else if (event.key === 'End') next = ids[ids.length - 1];
            if (!next) return;
            event.preventDefault();
            self.select(next, true);
        });

        this.root.appendChild(strip);

        TABS.forEach(function (tab) {
            var body = el('div', 'learn-body');
            body.id = 'learn-body-' + tab.id;
            body.setAttribute('role', 'tabpanel');
            body.setAttribute('aria-labelledby', 'learn-tab-' + tab.id);
            body.hidden = tab.id !== self.active;
            if (tab.id !== self.active) body.setAttribute('tabindex', '-1');
            self.root.appendChild(body);
            self.bodies[tab.id] = body;
        });
    };

    Panel.prototype.select = function (id, focus) {
        var self = this;
        this.active = id;
        TABS.forEach(function (tab) {
            var chosen = tab.id === id;
            self.tabs[tab.id].setAttribute('aria-selected', chosen ? 'true' : 'false');
            self.tabs[tab.id].tabIndex = chosen ? 0 : -1;
            self.bodies[tab.id].hidden = !chosen;
        });
        if (focus) this.tabs[id].focus();
    };

    Panel.prototype.setLesson = function (lesson) {
        this.lesson = lesson;
        this.renderStatic();
    };

    /* About and Complexity do not change as the run plays, so they are built
       once per algorithm rather than on every step. */
    Panel.prototype.renderStatic = function () {
        this.renderAbout();
        this.renderComplexity();
        this.renderCode();
        this.renderExplainShell();
    };

    Panel.prototype.renderExplainShell = function () {
        var body = this.bodies.explain;
        clear(body);
        // Two lines are reserved so a one line and a two line explanation do
        // not move the tabs (DESIGN section 7).
        this.explainText = el('p', 'explain-text');
        this.explainWhy = el('p', 'explain-why');
        this.explainAction = el('span', 'explain-action');
        var head = el('div', 'explain-head');
        head.appendChild(this.explainAction);
        body.appendChild(head);
        body.appendChild(this.explainText);
        body.appendChild(this.explainWhy);
        this.explainVars = el('dl', 'var-table');
        body.appendChild(this.explainVars);
    };

    Panel.prototype.renderAbout = function () {
        var body = this.bodies.about;
        var lesson = this.lesson;
        clear(body);
        if (!lesson) return;

        body.appendChild(el('h3', null, 'The idea'));
        var list = el('ul', 'idea-list');
        lesson.idea.forEach(function (sentence) {
            list.appendChild(el('li', null, sentence));
        });
        body.appendChild(list);

        body.appendChild(el('h3', null, 'An everyday version'));
        body.appendChild(el('p', null, lesson.analogy));

        body.appendChild(el('h3', null, 'When to use it'));
        body.appendChild(el('p', null, lesson.whenToUse));

        if (lesson.stable !== null && lesson.stable !== undefined) {
            body.appendChild(el('h3', null, 'Stable'));
            body.appendChild(el('p', null, lesson.stable
                ? 'Yes. Equal values keep the order they started in.'
                : 'No. Equal values can come out in the opposite order.'));
        }
    };

    /* A lesson resolved through static/js/variants.js says which version
       of the algorithm it describes. The Code and Complexity tabs name it,
       because both change with the switch. */
    function variantLine(lesson) {
        if (!lesson.variants || !lesson.variantLabel) return null;
        return el('p', 'variant-line',
            'Showing: ' + lesson.variants.label + ', ' + lesson.variantLabel);
    }

    Panel.prototype.renderCode = function () {
        var self = this;
        var body = this.bodies.code;
        var lesson = this.lesson;
        clear(body);
        if (!lesson) return;
        var shown = variantLine(lesson);
        if (shown) body.appendChild(shown);

        // Language tabs, the listing, helpers and Expand all live in
        // static/js/codeview.js, shared with the Home code card.
        if (this.codeView) this.codeView.destroy();
        var holder = el('div', 'code-holder');
        body.appendChild(holder);
        this.codeView = window.CodeView.mount({ host: holder, lesson: lesson });
        this.codeView.highlight(this.currentLine);

        body.appendChild(el('h3', 'vars-heading', 'Live values'));
        this.codeVars = el('dl', 'var-table');
        body.appendChild(this.codeVars);
        this.codeVarsEmpty = el('p', 'vars-empty', EMPTY_VARS);
        body.appendChild(this.codeVarsEmpty);
        this.syncCodeVars();
    };

    /* O, Omega and Theta, written with their symbols for the eye and in words
       for a screen reader, which would otherwise read "O" as a letter and
       skip the figure's meaning. The lesson stores the figure in words
       ('n squared'); this is the only place that turns it into symbols. */
    var SYMBOL = { O: 'O', Omega: 'Ω', Theta: 'Θ' };
    var SPOKEN = { O: 'Big O', Omega: 'Omega', Theta: 'Theta' };
    var FIGURE = {
        'n squared': ['n²', 'n squared'],
        'V squared': ['V²', 'V squared'],
        'V cubed': ['V³', 'V cubed'],
        'V times E': ['V·E', 'V times E'],
        'k times E': ['k·E', 'k times E']
    };

    function figure(token) {
        return FIGURE[token] || [token, token];
    }

    /* The bare symbol, with its name in words. */
    function symbol(kind) {
        var node = el('span', 'notation');
        node.appendChild(el('span', null, SYMBOL[kind]));
        node.firstChild.setAttribute('aria-hidden', 'true');
        node.appendChild(el('span', 'sr-only', SPOKEN[kind]));
        return node;
    }

    function notation(kind, token) {
        var f = figure(token);
        var node = el('span', 'notation');
        node.appendChild(el('span', null, SYMBOL[kind] + '(' + f[0] + ')'));
        node.firstChild.setAttribute('aria-hidden', 'true');
        node.appendChild(el('span', 'sr-only', SPOKEN[kind] + ' of ' + f[1]));
        return node;
    }

    /* Case, tight bound, reason. Each case has its own Theta, and the lesson
       says why, so the table is the lesson's data and nothing more. */
    function thetaTable(c) {
        var table = el('table', 'theta-table');
        table.appendChild(el('caption', 'sr-only',
            'Time by case, with the tight bound for each'));
        var head = el('tr');
        [['Case', null], ['Tight bound ', 'Theta'], ['Why', null]].forEach(function (col) {
            var th = el('th');
            th.scope = 'col';
            if (col[1]) {
                th.appendChild(document.createTextNode(col[0]));
                th.appendChild(symbol(col[1]));
            } else {
                th.textContent = col[0];
            }
            head.appendChild(th);
        });
        var thead = el('thead');
        thead.appendChild(head);
        table.appendChild(thead);
        var tbody = el('tbody');
        [['Best', c.time.best], ['Average', c.time.average], ['Worst', c.time.worst]]
            .forEach(function (pair) {
                var row = el('tr');
                var th = el('th', null, pair[0]);
                th.scope = 'row';
                row.appendChild(th);
                var cell = el('td', 'theta-cell');
                cell.appendChild(notation('Theta', pair[1].theta));
                row.appendChild(cell);
                row.appendChild(el('td', 'complexity-reason', pair[1].reason));
                tbody.appendChild(row);
            });
        table.appendChild(tbody);
        return table;
    }

    /* Across every input: the ceiling (O), the floor (Omega) and, only when
       the two meet, the tight bound. */
    function overallLine(c) {
        var o = c.overall;
        var line = el('p', 'overall-line');
        line.appendChild(el('strong', null, 'Overall: '));
        line.appendChild(notation('O', o.O));
        line.appendChild(document.createTextNode(' at most, '));
        line.appendChild(notation('Omega', o.Omega));
        line.appendChild(document.createTextNode(' at least, '));
        if (o.Theta) {
            line.appendChild(notation('Theta', o.Theta));
            line.appendChild(document.createTextNode(
                ': the ceiling and the floor are the same function, so it is tight for every input.'));
        } else {
            line.appendChild(document.createTextNode('and no single '));
            line.appendChild(symbol('Theta'));
            line.appendChild(document.createTextNode('. The best case is '));
            line.appendChild(notation('Theta', c.time.best.theta));
            line.appendChild(document.createTextNode(' and the worst is '));
            line.appendChild(notation('Theta', c.time.worst.theta));
            line.appendChild(document.createTextNode(
                ', so no one function fits every input.'));
            line.setAttribute('data-no-theta', 'true');
        }
        return line;
    }

    Panel.prototype.renderComplexity = function () {
        var body = this.bodies.complexity;
        var lesson = this.lesson;
        clear(body);
        if (!lesson) return;
        var c = lesson.complexity;
        var shown = variantLine(lesson);
        if (shown) body.appendChild(shown);

        body.appendChild(el('h3', null, 'Time'));
        body.appendChild(thetaTable(c));
        body.appendChild(overallLine(c));
        if (c.misconception) {
            var mix = el('p', 'misconception');
            mix.appendChild(el('strong', null, 'A common mix-up. '));
            mix.appendChild(document.createTextNode(c.misconception));
            body.appendChild(mix);
        }

        body.appendChild(el('h3', null, 'A worked example'));
        var worked = el('p', 'worked');
        worked.appendChild(el('code', null, c.worked.input));
        // A random pivot's count depends on its seed, so the seed is part of
        // the example.
        if (c.worked.seed !== undefined) {
            worked.appendChild(document.createTextNode(' with seed ' + c.worked.seed));
        }
        worked.appendChild(document.createTextNode(' costs '));
        worked.appendChild(el('strong', null, String(c.worked.comparisons)));
        worked.appendChild(document.createTextNode(' comparisons.'));
        body.appendChild(worked);
        body.appendChild(el('p', 'worked-note', c.worked.note));

        body.appendChild(el('h3', null, 'Auxiliary space'));
        var space = el('p', 'space-line');
        space.appendChild(el('strong', null, c.space.value));
        space.appendChild(document.createTextNode(': ' + c.space.what + '.'));
        body.appendChild(space);
        body.appendChild(el('p', 'aux-note', c.auxiliaryNote));

        body.appendChild(el('h3', null, 'This run'));
        this.thisRunBox = el('div', 'this-run');
        body.appendChild(this.thisRunBox);
        body.appendChild(el('p', 'aux-note', c.thisRun));
        /* Where a counter needs explaining, the lesson says so beside it. */
        if (c.countsNote) body.appendChild(el('p', 'aux-note', c.countsNote));

        body.appendChild(el('h3', null, 'How the work grows'));
        this.growthBox = el('div', 'growth');
        body.appendChild(this.growthBox);

        if (c.divergence) {
            body.appendChild(el('h3', null, 'Against the textbook'));
            body.appendChild(el('p', 'divergence', c.divergence));
        }

        /* The longer explanation of what these figures mean lives on one
           page rather than being repeated in fifteen lessons. */
        var more = el('p', 'complexity-more');
        var link = el('a', null, 'How complexity works');
        link.href = '/big-o';
        more.appendChild(link);
        more.appendChild(document.createTextNode(
            ' explains counting, the three cases and auxiliary space.'));
        body.appendChild(more);

        this.renderThisRun(null);
    };

    /* The "this run" box and the growth chart both depend on the size of the
       input, so they are redrawn whenever the caller reports new stats. */
    Panel.prototype.renderThisRun = function (stats) {
        if (!this.thisRunBox || !this.lesson) return;
        clear(this.thisRunBox);

        if (!stats || !stats.n) {
            this.thisRunBox.appendChild(
                el('p', 'this-run-empty', 'Run the algorithm to see its counted work here.'));
            this.renderGrowth(0);
            return;
        }

        var table = el('dl', 'var-table');
        function row(term, value) {
            table.appendChild(el('dt', null, term));
            table.appendChild(el('dd', null, String(value)));
        }
        /* A graph reports both of its sizes, because its figure may be
           written in either. Anything else has one. */
        if (stats.edges === undefined) {
            row('Input size', stats.n);
        } else {
            row('Nodes', stats.n);
            row('Edges', stats.edges);
        }
        if (stats.comparisons !== undefined) row('Comparisons counted', stats.comparisons);
        if (stats.swaps !== undefined) {
            row(countLabel(this.lesson) + ' counted', stats.swaps);
        }

        /* The figure is the lesson's own worst case. The curve only says
           what shape that figure has, and some figures have no single
           curve, in which case there is no row to show. */
        var c = this.lesson.complexity;
        var curve = CURVES[c.growth];
        var size = axisSize(c, stats);
        if (curve && size) {
            row(c.time.worst.value + ' at ' + axisLetter(c) + ' = ' + size,
                Math.round(curve.of(size) * 10) / 10);
        }
        this.thisRunBox.appendChild(table);
        this.renderGrowth(size || stats.n);
    };

    Panel.prototype.renderGrowth = function (n) {
        if (!this.growthBox || !this.lesson) return;
        var c = this.lesson.complexity;
        window.Growth.render(this.growthBox, {
            n: n,
            highlight: c.growth,
            label: c.time.worst.value,
            basis: c.growthBasis,
            note: c.growthNote
        });
    };

    Panel.prototype.highlight = function (lineId) {
        this.currentLine = lineId;
        if (this.codeView) this.codeView.highlight(lineId);
    };

    var EMPTY_VARS = 'Run the algorithm to see values change';

    /* Before a run there are no values to list, and an empty heading reads as
       a broken panel. Say what to do instead. Re-rendering the listing in the
       middle of a run keeps the values of the step on screen. */
    Panel.prototype.syncCodeVars = function () {
        fillVars(this.codeVars, this.currentVars);
        if (this.codeVarsEmpty) {
            this.codeVarsEmpty.hidden = Object.keys(this.currentVars || {}).length > 0;
        }
    };

    function fillVars(list, vars) {
        if (!list) return;
        clear(list);
        Object.keys(vars || {}).forEach(function (key) {
            var value = vars[key];
            list.appendChild(el('dt', null, key));
            list.appendChild(el('dd', null,
                typeof value === 'object' ? JSON.stringify(value) : String(value)));
        });
    }

    /* No step to describe. The tabs stay, because the lesson is still the
       right lesson; what goes is everything that described a run. */
    Panel.prototype.clearStep = function () {
        if (this.explainAction) {
            this.explainAction.textContent = '';
            this.explainAction.removeAttribute('data-action');
        }
        if (this.explainText) this.explainText.textContent = '';
        if (this.explainWhy) this.explainWhy.textContent = '';
        fillVars(this.explainVars, {});
        this.currentVars = null;
        this.syncCodeVars();
        this.highlight(null);
        this.renderThisRun(null);
    };

    Panel.prototype.showStep = function (step, stats) {
        if (!step) return;
        if (this.explainAction) {
            this.explainAction.textContent = step.action || '';
            this.explainAction.setAttribute('data-action', step.action || '');
        }
        if (this.explainText) this.explainText.textContent = step.explain.beginner;
        if (this.explainWhy) this.explainWhy.textContent = step.explain.why;
        fillVars(this.explainVars, step.vars);
        this.currentVars = step.vars;
        this.syncCodeVars();
        this.highlight(step.line);
        if (stats) this.renderThisRun(stats);
    };

    window.Teacher = {
        mount: function (options) { return new Panel(options); }
    };
})();
