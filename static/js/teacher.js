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
        this.codeView = 'pseudocode';
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

    Panel.prototype.renderCode = function () {
        var self = this;
        var body = this.bodies.code;
        var lesson = this.lesson;
        clear(body);
        if (!lesson) return;

        var toggle = el('div', 'code-toggle');
        toggle.setAttribute('role', 'group');
        toggle.setAttribute('aria-label', 'Code view');
        ['pseudocode', 'python'].forEach(function (view) {
            var button = el('button', 'code-toggle-btn',
                view === 'pseudocode' ? 'Pseudocode' : 'Python');
            button.type = 'button';
            button.setAttribute('aria-pressed', self.codeView === view ? 'true' : 'false');
            button.addEventListener('click', function () {
                self.codeView = view;
                self.renderCode();
                self.highlight(self.currentLine);
            });
            toggle.appendChild(button);
        });
        body.appendChild(toggle);

        // The listing scrolls sideways in a narrow panel, so it is a focus
        // stop: a scroll box no one can reach from the keyboard hides its own
        // right hand side. Named, because an unexplained stop is worse.
        var listing = el('ol', 'code-listing');
        listing.tabIndex = 0;
        listing.setAttribute('aria-label',
            (self.codeView === 'python' ? 'Python' : 'Pseudocode') + ' listing');
        lesson.code[this.codeView].forEach(function (line) {
            var item = el('li', 'code-line');
            if (line.id) item.setAttribute('data-line', line.id);
            item.style.setProperty('--indent', line.indent || 0);
            item.appendChild(el('code', null, line.text));
            listing.appendChild(item);
        });
        body.appendChild(listing);

        body.appendChild(el('h3', 'vars-heading', 'Live values'));
        this.codeVars = el('dl', 'var-table');
        body.appendChild(this.codeVars);
    };

    Panel.prototype.renderComplexity = function () {
        var body = this.bodies.complexity;
        var lesson = this.lesson;
        clear(body);
        if (!lesson) return;
        var c = lesson.complexity;

        body.appendChild(el('h3', null, 'Time'));
        var table = el('dl', 'complexity-table');
        [['Best', c.time.best], ['Average', c.time.average], ['Worst', c.time.worst]]
            .forEach(function (pair) {
                var dt = el('dt', null, pair[0]);
                var dd = el('dd');
                dd.appendChild(el('span', 'complexity-value', pair[1].value));
                dd.appendChild(el('span', 'complexity-reason', pair[1].reason));
                table.appendChild(dt);
                table.appendChild(dd);
            });
        body.appendChild(table);

        body.appendChild(el('h3', null, 'A worked example'));
        var worked = el('p', 'worked');
        worked.appendChild(el('code', null, c.worked.input));
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
        row('Input size', stats.n);
        if (stats.comparisons !== undefined) row('Comparisons counted', stats.comparisons);
        if (stats.swaps !== undefined) row('Swaps counted', stats.swaps);

        var curve = CURVES[this.lesson.complexity.growth];
        if (curve) {
            row(curve.label + ' at n = ' + stats.n,
                Math.round(curve.of(stats.n) * 10) / 10);
        }
        this.thisRunBox.appendChild(table);
        this.renderGrowth(stats.n);
    };

    Panel.prototype.renderGrowth = function (n) {
        if (!this.growthBox || !this.lesson) return;
        window.Growth.render(this.growthBox, {
            n: n,
            highlight: this.lesson.complexity.growth
        });
    };

    Panel.prototype.highlight = function (lineId) {
        this.currentLine = lineId;
        var lines = this.bodies.code.querySelectorAll('.code-line');
        Array.prototype.forEach.call(lines, function (line) {
            var on = !!lineId && line.getAttribute('data-line') === lineId;
            line.classList.toggle('is-current', on);
            if (on) line.setAttribute('aria-current', 'step');
            else line.removeAttribute('aria-current');
        });
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

    Panel.prototype.showStep = function (step, stats) {
        if (!step) return;
        if (this.explainAction) {
            this.explainAction.textContent = step.action || '';
            this.explainAction.setAttribute('data-action', step.action || '');
        }
        if (this.explainText) this.explainText.textContent = step.explain.beginner;
        if (this.explainWhy) this.explainWhy.textContent = step.explain.why;
        fillVars(this.explainVars, step.vars);
        fillVars(this.codeVars, step.vars);
        this.highlight(step.line);
        if (stats) this.renderThisRun(stats);
    };

    window.Teacher = {
        mount: function (options) { return new Panel(options); }
    };
})();
