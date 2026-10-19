/* The workspace shell: algorithm picker, run button, transport, Learn panel.
 *
 * Shared by every workspace. Nothing here knows about searching, sorting or
 * graphs. The page supplies the parts that differ as callbacks, and this file
 * owns everything that does not: fetching, playback, the step counter, the
 * enabled state of the transport, and wiring the Learn panel to the step.
 *
 *   Workspace.start({
 *     root,                     optional, the element this workspace lives in.
 *                               Omitted, it is the whole document (see below)
 *     endpoint,                 where to POST the run
 *     lessons,                  window.LESSONS, keyed by algorithm id
 *     readRequest(ui),          build the POST body, or return {field, message}
 *     onRun(ui),                optional, take the run over and call load()
 *     algorithm,                optional, the id shown when the picker navigates
 *     metaFor(step, i, body),   optional, where the teacher payload lives when
 *                               it is not the step itself
 *     renderStep(step, ctx),    draw one step on the stage
 *     renderResult(payload),    optional, the closing banner. Called when the
 *                               run reaches its last step, not when it loads,
 *                               so it does not give the answer away
 *     clearResult(),            optional, undo renderResult when the viewer
 *                               steps back off the last step
 *     clearStage(),             optional, blank the stage when a run is
 *                               refused, so nothing of the last one is left
 *     onLoad(payload),          optional, called once when a run arrives,
 *                               before its first step is drawn
 *     onError(payload, ui),     optional, return true if the page handled it
 *     delayFor(sliderValue)     optional, milliseconds between frames
 *     shortcuts                 optional, false to leave the keyboard alone,
 *                               as a workspace inside a group does
 *     predict                   optional, {family}. Turns on Predict mode
 *                               (static/js/predict.js), which asks a question
 *                               before some forward steps. The shell only
 *                               asks the gate whether a step may play; it
 *                               knows nothing about what is asked
 *   })
 *
 * Finding the parts. With no root, the page has one workspace and the parts
 * are these ids, the contract the three workspace templates were built on:
 * run-button, play-pause, step-back, step-forward, reset, speed,
 * step-counter, and optionally algo-picker, learn-panel and run-banner.
 * Inside a root, the same names are given as data-part="play-pause" and so
 * on, so two workspaces on one page never share an id. A part a workspace
 * lacks is simply not wired: a workspace inside a group has no transport of
 * its own.
 *
 *   Workspace.group([a, b], { root, delayFor, onTick })
 *
 * One transport for several workspaces, as /compare has. The group keeps one
 * tick: each member shows its own step at that tick, or its last step once
 * it has run out, so a member that finishes first waits while the others
 * carry on. Step back, step forward, reset, play and the keyboard all move
 * the tick.
 *
 * Playback is a plain interval. The transport is pressed often, so none of
 * its buttons animates anything beyond the press feedback in CSS.
 */
(function () {
    'use strict';

    var PARTS = ['algo-picker', 'run-button', 'play-pause', 'step-back',
                 'step-forward', 'reset', 'speed', 'step-counter',
                 'learn-panel', 'run-banner'];

    /* One part of a workspace: an id on a page with one workspace, a
       data-part inside a root. */
    function partOf(root, name) {
        if (!root || root === document) return document.getElementById(name);
        return root.querySelector('[data-part="' + name + '"]');
    }

    function within(root, selector) {
        return (root || document).querySelector(selector);
    }

    function withinAll(root, selector) {
        return (root || document).querySelectorAll(selector);
    }

    /* The transport buttons and the keyboard, shared by a lone workspace and
       a group. The owner provides togglePlay, stepBack, stepForward, toStart,
       restartTimer, and the parts it found. */
    function wireTransport(owner) {
        var p = owner.parts;
        if (p['play-pause']) p['play-pause'].addEventListener('click', function () { owner.togglePlay(); });
        if (p['step-back']) p['step-back'].addEventListener('click', function () { owner.stepBack(); });
        if (p['step-forward']) p['step-forward'].addEventListener('click', function () { owner.stepForward(); });
        if (p.reset) p.reset.addEventListener('click', function () { owner.toStart(); });
        if (p.speed) p.speed.addEventListener('input', function () { owner.restartTimer(); });
    }

    /* Space plays or pauses, Left and Right step, R resets. */
    function wireShortcuts(owner) {
        var p = owner.parts;
        [[p['play-pause'], 'Space'], [p['step-back'], 'ArrowLeft'],
         [p['step-forward'], 'ArrowRight'], [p.reset, 'R']]
            .forEach(function (pair) {
                if (pair[0]) pair[0].setAttribute('aria-keyshortcuts', pair[1]);
            });

        var bar = owner.controlBar;
        if (bar && !bar.querySelector('.shortcuts')) bar.appendChild(shortcutsDisclosure());

        document.addEventListener('keydown', function (event) {
            if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
            var target = event.target;
            var tag = target && target.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
                (target && target.isContentEditable)) return;
            // The Learn tabs use the arrow keys to move between themselves.
            if (target && target.closest && target.closest('[role="tablist"], dialog, [data-keys="own"]')) return;

            var key = event.key;
            if (key === ' ') {
                // On a button or link Space already means "press it".
                if (tag === 'BUTTON' || tag === 'A' || tag === 'SUMMARY') return;
                event.preventDefault();
                owner.togglePlay();
            } else if (key === 'ArrowLeft') {
                event.preventDefault();
                owner.stepBack();
            } else if (key === 'ArrowRight') {
                event.preventDefault();
                owner.stepForward();
            } else if (key === 'r' || key === 'R') {
                event.preventDefault();
                owner.toStart();
            }
        });
    }

    function shortcutsDisclosure() {
        var box = document.createElement('details');
        box.className = 'shortcuts';
        var summary = document.createElement('summary');
        summary.textContent = 'Keyboard shortcuts';
        box.appendChild(summary);
        var list = document.createElement('dl');
        [['Space', 'Play or pause'], ['Left arrow', 'Step back'],
         ['Right arrow', 'Step forward'], ['R', 'Back to the first step']]
            .forEach(function (row) {
                var dt = document.createElement('dt');
                var kbd = document.createElement('kbd');
                kbd.textContent = row[0];
                dt.appendChild(kbd);
                var dd = document.createElement('dd');
                dd.textContent = row[1];
                list.appendChild(dt);
                list.appendChild(dd);
            });
        box.appendChild(list);
        return box;
    }

    /* Enable, disable and label the transport for a position in a run. */
    function syncButtons(parts, has, atStart, atEnd, playing, label) {
        if (parts['play-pause']) {
            parts['play-pause'].disabled = !has || (atEnd && !playing);
            parts['play-pause'].setAttribute('data-playing', playing ? 'true' : 'false');
            parts['play-pause'].setAttribute('aria-label', playing ? 'Pause' : 'Play');
        }
        if (parts['step-back']) parts['step-back'].disabled = !has || atStart;
        if (parts['step-forward']) parts['step-forward'].disabled = !has || atEnd;
        if (parts.reset) parts.reset.disabled = !has || atStart;
        if (parts['step-counter']) parts['step-counter'].textContent = label;
    }

    /* Milliseconds between frames for a slider. A page whose slider has a
       different range, or a different feel, supplies delayFor(value); the
       default suits a 1 to 10 slider. */
    function delayFrom(speed, delayFor) {
        var value = speed ? Number(speed.value) : 5;
        if (delayFor) return delayFor(value);
        // 1 is slowest, 10 is fastest.
        return 1100 - (value * 100);
    }

    function Workspace(options) {
        var self = this;
        this.options = options;
        this.root = options.root || document;
        this.steps = [];
        this.index = 0;
        this.timer = null;
        this.payload = null;
        this.resultShown = false;

        this.parts = {};
        PARTS.forEach(function (name) { self.parts[name] = partOf(self.root, name); });
        this.controlBar = within(this.root, '.control-bar');

        // The names the rest of the code and the other scripts already use.
        this.picker = this.parts['algo-picker'];
        this.runButton = this.parts['run-button'];
        this.playPause = this.parts['play-pause'];
        this.back = this.parts['step-back'];
        this.forward = this.parts['step-forward'];
        this.resetButton = this.parts.reset;
        this.speed = this.parts.speed;
        this.counter = this.parts['step-counter'];

        // A page whose picker is a set of links to other pages, rather than an
        // in place switch, names the algorithm it is showing instead.
        this.algorithm = options.algorithm || this.firstAlgorithm();

        // The Learn panel is optional: a page without a learn-panel gets the
        // shell and the transport and nothing else.
        var panelHost = this.parts['learn-panel'];
        this.panel = panelHost && window.Teacher
            ? window.Teacher.mount({
                panel: panelHost,
                lesson: (options.lessons || {})[this.algorithm]
            })
            : null;

        // Predict mode is a gate in front of every forward step.
        this.gate = options.predict && window.Predict && this.panel
            ? window.Predict.mount(this, options.predict)
            : null;
        this.gateStepping = false;

        this.bind();
        if (options.shortcuts !== false) wireShortcuts(this);
        this.syncTransport();
    }

    Workspace.prototype.firstAlgorithm = function () {
        if (!this.picker) return null;
        var current = this.picker.querySelector('[aria-current="true"]');
        var first = current || this.picker.querySelector('[data-algorithm]');
        return first ? first.getAttribute('data-algorithm') : null;
    };

    Workspace.prototype.bind = function () {
        var self = this;

        if (this.picker) {
            this.picker.addEventListener('click', function (event) {
                var link = event.target.closest('[data-algorithm]');
                if (!link) return;
                event.preventDefault();
                self.selectAlgorithm(link.getAttribute('data-algorithm'));
            });
        }

        if (this.runButton) {
            this.runButton.addEventListener('click', function () { self.run(); });
        }
        wireTransport(this);
    };

    Workspace.prototype.stepBack = function () { this.pause(); this.go(this.index - 1); };
    Workspace.prototype.stepForward = function () { this.pause(); this.advance(false); };
    Workspace.prototype.toStart = function () { this.pause(); this.go(0); };
    Workspace.prototype.restartTimer = function () {
        if (this.timer) { this.pause(); this.play(); }
    };

    Workspace.prototype.selectAlgorithm = function (name) {
        if (!name || name === this.algorithm) return;
        this.algorithm = name;
        Array.prototype.forEach.call(
            this.picker.querySelectorAll('[data-algorithm]'),
            function (link) {
                link.setAttribute('aria-current',
                    link.getAttribute('data-algorithm') === name ? 'true' : 'false');
            });
        /* The loaded run belongs to the algorithm just left. Kept, its steps
           would play under the new algorithm's name, code and counters, so
           it goes, exactly as a refused run does. */
        if (this.payload) this.discard();
        if (this.panel) this.panel.setLesson((this.options.lessons || {})[name]);
        if (this.options.onAlgorithmChange) this.options.onAlgorithmChange(name);
    };

    Workspace.prototype.clearErrors = function () {
        Array.prototype.forEach.call(
            withinAll(this.root, '.field-error'),
            function (node) { node.textContent = ''; });
    };

    Workspace.prototype.showError = function (field, message) {
        var box = (field && partOf(this.root, field)) || within(this.root, '.field-error');
        if (!box) return;
        box.textContent = message;
    };

    Workspace.prototype.run = function () {
        var self = this;
        this.clearErrors();
        var banner = this.parts['run-banner'];
        if (banner) { banner.textContent = ''; banner.removeAttribute('data-outcome'); }

        // A page that has to do more than post one body, because it builds a
        // canvas first or picks an endpoint per algorithm, takes the run over
        // and calls load() when it has the steps.
        if (this.options.onRun) {
            this.options.onRun({ algorithm: this.algorithm });
            return;
        }

        var request = this.options.readRequest({ algorithm: this.algorithm });
        if (request && request.message) {
            this.showError(request.field, request.message);
            return;
        }

        var askedFor = this.algorithm;
        fetch(this.options.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        })
            .then(function (response) {
                return response.json().then(function (body) {
                    return { ok: response.ok, body: body };
                });
            })
            .then(function (result) {
                // The learner switched algorithm while this was in flight,
                // so the answer is for a page that is no longer showing.
                if (self.algorithm !== askedFor) return;
                if (!result.ok || result.body.error) {
                    /* There is no run now. Anything still on screen belongs
                       to the last one and would be read as this one. */
                    self.discard();
                    var handled = self.options.onError &&
                        self.options.onError(result.body, { algorithm: self.algorithm });
                    if (!handled) self.showError(null, result.body.error || 'The run failed.');
                    return;
                }
                self.load(result.body);
            })
            .catch(function (error) {
                console.error('Workspace request failed:', error);
                self.showError(null, 'Could not reach the server. Try again.');
            });
    };

    /* Throw the loaded run away: no steps, no stage, no narration, no
       banner, and a transport that cannot be pressed. */
    Workspace.prototype.discard = function () {
        this.pause();
        if (this.gate) this.gate.reset();
        this.payload = null;
        this.steps = [];
        this.index = 0;
        this.lastStats = null;
        this.resultShown = false;
        if (this.options.clearResult) this.options.clearResult();
        if (this.options.clearStage) this.options.clearStage();
        if (this.panel) this.panel.clearStep();
        this.syncTransport();
    };

    Workspace.prototype.load = function (payload) {
        this.pause();
        this.payload = payload;
        this.steps = payload.steps || [];
        this.index = 0;
        this.resultShown = false;
        if (this.gate) this.gate.reset();
        if (this.options.clearResult) this.options.clearResult();
        if (this.options.onLoad) this.options.onLoad(payload);
        this.go(0);
        this.syncTransport();
    };

    /* The teacher payload of step i: the step itself, or where the page keeps
       it (graphs send it in a parallel list). */
    Workspace.prototype.metaAt = function (i) {
        var step = this.steps[i];
        return this.options.metaFor ? this.options.metaFor(step, i, this.payload) : step;
    };

    /* Play the next step, unless the gate holds it back for a question. The
       gate plays it itself, through resume(), once the question is answered or
       skipped. `auto` says the step was due from playback, which should carry
       on afterwards. */
    Workspace.prototype.advance = function (auto) {
        var next = this.index + 1;
        if (next >= this.steps.length) return false;
        if (this.gate && this.gate.intercept(next, !!auto)) {
            this.pause();
            return false;
        }
        this.go(next);
        return true;
    };

    Workspace.prototype.resume = function (index, auto) {
        this.gateStepping = true;
        this.go(index);
        this.gateStepping = false;
        if (auto) this.play();
    };

    Workspace.prototype.go = function (index) {
        if (!this.steps.length) return;
        var previous = this.index;
        this.index = Math.max(0, Math.min(index, this.steps.length - 1));
        if (this.gate) this.gate.onGo(this.index, previous);
        var step = this.steps[this.index];
        var self = this;
        this.options.renderStep(step, {
            index: this.index,
            total: this.steps.length,
            payload: this.payload,
            stats: function (stats) { self.lastStats = stats; }
        });
        if (this.panel) {
            var meta = this.options.metaFor
                ? this.options.metaFor(step, this.index, this.payload)
                : step;
            this.panel.showStep(meta, this.lastStats);
        }
        this.showResultIfFinished();
        this.syncTransport();
    };

    /* The banner belongs to the last step, so it arrives with it and leaves
       again on the way back. */
    Workspace.prototype.showResultIfFinished = function () {
        var finished = this.steps.length > 0 &&
            this.index === this.steps.length - 1;
        if (finished === this.resultShown) return;
        this.resultShown = finished;
        if (finished) {
            if (this.options.renderResult) this.options.renderResult(this.payload);
        } else if (this.options.clearResult) {
            this.options.clearResult();
        }
    };

    Workspace.prototype.syncTransport = function () {
        var has = this.steps.length > 0;
        syncButtons(this.parts, has, this.index <= 0, this.index >= this.steps.length - 1,
                    !!this.timer,
                    has ? 'Step ' + (this.index + 1) + ' of ' + this.steps.length : 'Step 0 of 0');
    };

    Workspace.prototype.delay = function () {
        return delayFrom(this.speed, this.options.delayFor);
    };

    Workspace.prototype.play = function () {
        var self = this;
        if (this.timer || !this.steps.length) return;
        if (this.index >= this.steps.length - 1) this.go(0);
        this.timer = window.setInterval(function () {
            if (self.index >= self.steps.length - 1) { self.pause(); return; }
            self.advance(true);
        }, this.delay());
        this.syncTransport();
    };

    Workspace.prototype.pause = function () {
        if (this.timer) {
            window.clearInterval(this.timer);
            this.timer = null;
        }
        this.syncTransport();
    };

    Workspace.prototype.togglePlay = function () {
        // A question is waiting: Play and Space are not an answer.
        if (this.gate && this.gate.pending) { this.gate.nudge(); return; }
        if (this.timer) this.pause();
        else this.play();
    };

    /* ---------------------------------------------------------------------
       A group: one transport driving several workspaces in step.
       --------------------------------------------------------------------- */

    function Group(members, options) {
        var self = this;
        this.members = members;
        this.options = options || {};
        this.root = this.options.root || document;
        this.tick = 0;
        this.timer = null;
        this.parts = {};
        PARTS.forEach(function (name) { self.parts[name] = partOf(self.root, name); });
        this.controlBar = within(this.root, '.control-bar');
        wireTransport(this);
        if (this.options.shortcuts !== false) wireShortcuts(this);
        this.sync();
    }

    /* How many ticks the longest loaded run needs. */
    Group.prototype.length = function () {
        return this.members.reduce(function (most, ws) {
            return Math.max(most, ws.steps.length);
        }, 0);
    };

    Group.prototype.ready = function () {
        return this.members.length > 0 && this.members.every(function (ws) {
            return ws.steps.length > 0;
        });
    };

    /* Every member to the tick, each stopping at its own last step. */
    Group.prototype.go = function (tick) {
        var length = this.length();
        if (!length) return;
        this.tick = Math.max(0, Math.min(tick, length - 1));
        var self = this;
        this.members.forEach(function (ws) {
            if (!ws.steps.length) return;
            var want = Math.min(self.tick, ws.steps.length - 1);
            if (want !== ws.index || self.tick === 0) ws.go(want);
        });
        if (this.options.onTick) this.options.onTick(this.tick, length);
        this.sync();
    };

    /* After the members have loaded new runs: back to the start. */
    Group.prototype.restart = function () {
        this.pause();
        this.tick = 0;
        this.go(0);
        this.sync();
    };

    Group.prototype.sync = function () {
        var length = this.length();
        var has = this.ready();
        syncButtons(this.parts, has, this.tick <= 0, this.tick >= length - 1, !!this.timer,
                    has ? 'Step ' + (this.tick + 1) + ' of ' + length : 'Step 0 of 0');
    };

    Group.prototype.stepBack = function () { this.pause(); this.go(this.tick - 1); };
    Group.prototype.stepForward = function () { this.pause(); this.go(this.tick + 1); };
    Group.prototype.toStart = function () { this.pause(); this.go(0); };
    Group.prototype.restartTimer = function () {
        if (this.timer) { this.pause(); this.play(); }
    };

    Group.prototype.play = function () {
        var self = this;
        if (this.timer || !this.ready()) return;
        if (this.tick >= this.length() - 1) this.go(0);
        this.timer = window.setInterval(function () {
            if (self.tick >= self.length() - 1) { self.pause(); return; }
            self.go(self.tick + 1);
        }, delayFrom(this.parts.speed, this.options.delayFor));
        this.sync();
    };

    Group.prototype.pause = function () {
        if (this.timer) {
            window.clearInterval(this.timer);
            this.timer = null;
        }
        this.sync();
    };

    Group.prototype.togglePlay = function () {
        if (this.timer) this.pause();
        else this.play();
    };

    window.Workspace = {
        /* The one workspace of a page. Workspace.current is it. */
        start: function (options) {
            var instance = new Workspace(options);
            window.Workspace.current = instance;
            return instance;
        },
        /* A workspace that shares its page with others, as /compare's two
           sides do. Give it a root. */
        create: function (options) {
            return new Workspace(options);
        },
        group: function (members, options) {
            return new Group(members, options);
        }
    };
})();
