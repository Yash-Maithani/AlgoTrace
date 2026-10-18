/* The workspace shell: algorithm picker, run button, transport, Learn panel.
 *
 * Shared by every workspace. Nothing here knows about searching, sorting or
 * graphs. The page supplies the parts that differ as callbacks, and this file
 * owns everything that does not: fetching, playback, the step counter, the
 * enabled state of the transport, and wiring the Learn panel to the step.
 *
 *   Workspace.start({
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
 *   })
 *
 * The template must provide these ids: run-button, play-pause, step-back,
 * step-forward, reset, speed, step-counter. An algo-picker list and a
 * learn-panel are optional; with a picker, its links carry data-algorithm,
 * and without a panel the Learn tabs are simply not built.
 *
 * Playback is a plain interval. The transport is pressed often, so none of
 * its buttons animates anything beyond the press feedback in CSS.
 */
(function () {
    'use strict';

    function byId(id) { return document.getElementById(id); }

    function Workspace(options) {
        this.options = options;
        this.steps = [];
        this.index = 0;
        this.timer = null;
        this.payload = null;
        this.resultShown = false;

        this.picker = byId('algo-picker');
        this.runButton = byId('run-button');
        this.playPause = byId('play-pause');
        this.back = byId('step-back');
        this.forward = byId('step-forward');
        this.resetButton = byId('reset');
        this.speed = byId('speed');
        this.counter = byId('step-counter');

        // A page whose picker is a set of links to other pages, rather than an
        // in place switch, names the algorithm it is showing instead.
        this.algorithm = options.algorithm || this.firstAlgorithm();

        // The Learn panel is optional: a page without a #learn-panel element
        // gets the shell and the transport and nothing else.
        var panelHost = byId('learn-panel');
        this.panel = panelHost && window.Teacher
            ? window.Teacher.mount({
                panel: panelHost,
                lesson: (options.lessons || {})[this.algorithm]
            })
            : null;

        this.bind();
        this.bindShortcuts();
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
        if (this.playPause) {
            this.playPause.addEventListener('click', function () { self.togglePlay(); });
        }
        if (this.back) {
            this.back.addEventListener('click', function () { self.pause(); self.go(self.index - 1); });
        }
        if (this.forward) {
            this.forward.addEventListener('click', function () { self.pause(); self.go(self.index + 1); });
        }
        if (this.resetButton) {
            this.resetButton.addEventListener('click', function () { self.pause(); self.go(0); });
        }
        if (this.speed) {
            this.speed.addEventListener('input', function () {
                if (self.timer) { self.pause(); self.play(); }
            });
        }
    };

    /* Space plays or pauses, Left and Right step, R resets. One listener for
       every workspace, because they all have this transport. */
    Workspace.prototype.bindShortcuts = function () {
        var self = this;
        [[this.playPause, 'Space'], [this.back, 'ArrowLeft'],
         [this.forward, 'ArrowRight'], [this.resetButton, 'R']]
            .forEach(function (pair) {
                if (pair[0]) pair[0].setAttribute('aria-keyshortcuts', pair[1]);
            });

        var bar = document.querySelector('.control-bar');
        if (bar && !bar.querySelector('.shortcuts')) bar.appendChild(shortcutsDisclosure());

        document.addEventListener('keydown', function (event) {
            if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
            var target = event.target;
            var tag = target && target.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' ||
                (target && target.isContentEditable)) return;
            // The Learn tabs use the arrow keys to move between themselves.
            if (target && target.closest && target.closest('[role="tablist"], dialog')) return;

            var key = event.key;
            if (key === ' ') {
                // On a button or link Space already means "press it".
                if (tag === 'BUTTON' || tag === 'A' || tag === 'SUMMARY') return;
                event.preventDefault();
                self.togglePlay();
            } else if (key === 'ArrowLeft') {
                event.preventDefault();
                self.pause();
                self.go(self.index - 1);
            } else if (key === 'ArrowRight') {
                event.preventDefault();
                self.pause();
                self.go(self.index + 1);
            } else if (key === 'r' || key === 'R') {
                event.preventDefault();
                self.pause();
                self.go(0);
            }
        });
    };

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
            document.querySelectorAll('.field-error'),
            function (node) { node.textContent = ''; });
    };

    Workspace.prototype.showError = function (field, message) {
        var box = byId(field) || document.querySelector('.field-error');
        if (!box) return;
        box.textContent = message;
    };

    Workspace.prototype.run = function () {
        var self = this;
        this.clearErrors();
        var banner = byId('run-banner');
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
        if (this.options.clearResult) this.options.clearResult();
        if (this.options.onLoad) this.options.onLoad(payload);
        this.go(0);
        this.syncTransport();
    };

    Workspace.prototype.go = function (index) {
        if (!this.steps.length) return;
        this.index = Math.max(0, Math.min(index, this.steps.length - 1));
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
        var atStart = this.index <= 0;
        var atEnd = this.index >= this.steps.length - 1;

        if (this.playPause) {
            this.playPause.disabled = !has || (atEnd && !this.timer);
            var playing = !!this.timer;
            this.playPause.setAttribute('data-playing', playing ? 'true' : 'false');
            this.playPause.setAttribute('aria-label', playing ? 'Pause' : 'Play');
        }
        if (this.back) this.back.disabled = !has || atStart;
        if (this.forward) this.forward.disabled = !has || atEnd;
        if (this.resetButton) this.resetButton.disabled = !has || atStart;
        if (this.counter) {
            this.counter.textContent = has
                ? 'Step ' + (this.index + 1) + ' of ' + this.steps.length
                : 'Step 0 of 0';
        }
    };

    /* How long to wait between frames, read from the speed slider. A page
       whose slider has a different range, or a different feel, supplies its
       own delayFor(value); the default suits a 1 to 10 slider. */
    Workspace.prototype.delay = function () {
        var value = this.speed ? Number(this.speed.value) : 5;
        if (this.options.delayFor) return this.options.delayFor(value);
        // 1 is slowest, 10 is fastest.
        return 1100 - (value * 100);
    };

    Workspace.prototype.play = function () {
        var self = this;
        if (this.timer || !this.steps.length) return;
        if (this.index >= this.steps.length - 1) this.go(0);
        this.timer = window.setInterval(function () {
            if (self.index >= self.steps.length - 1) { self.pause(); return; }
            self.go(self.index + 1);
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
        if (this.timer) this.pause();
        else this.play();
    };

    window.Workspace = {
        start: function (options) {
            var instance = new Workspace(options);
            window.Workspace.current = instance;
            return instance;
        }
    };
})();
