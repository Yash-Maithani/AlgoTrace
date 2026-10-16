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
 *     renderStep(step, ctx),    draw one step on the stage
 *     renderResult(payload),    optional, the closing banner
 *     onError(payload, ui),     optional, return true if the page handled it
 *     delayFor(sliderValue)     optional, milliseconds between frames
 *   })
 *
 * The template must provide these ids: run-button, play-pause, step-back,
 * step-forward, reset, speed, step-counter, learn-panel. An algo-picker list
 * is optional; with one, its links carry data-algorithm.
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

        this.picker = byId('algo-picker');
        this.runButton = byId('run-button');
        this.playPause = byId('play-pause');
        this.back = byId('step-back');
        this.forward = byId('step-forward');
        this.resetButton = byId('reset');
        this.speed = byId('speed');
        this.counter = byId('step-counter');

        this.algorithm = this.firstAlgorithm();
        this.panel = window.Teacher.mount({
            panel: byId('learn-panel'),
            lesson: options.lessons[this.algorithm]
        });

        this.bind();
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

    Workspace.prototype.selectAlgorithm = function (name) {
        if (!name || name === this.algorithm) return;
        this.algorithm = name;
        Array.prototype.forEach.call(
            this.picker.querySelectorAll('[data-algorithm]'),
            function (link) {
                link.setAttribute('aria-current',
                    link.getAttribute('data-algorithm') === name ? 'true' : 'false');
            });
        this.panel.setLesson(this.options.lessons[name]);
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

        var request = this.options.readRequest({ algorithm: this.algorithm });
        if (request && request.message) {
            this.showError(request.field, request.message);
            return;
        }

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
                if (!result.ok || result.body.error) {
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

    Workspace.prototype.load = function (payload) {
        this.pause();
        this.payload = payload;
        this.steps = payload.steps || [];
        this.index = 0;
        if (this.options.renderResult) this.options.renderResult(payload);
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
        this.panel.showStep(step, this.lastStats);
        this.syncTransport();
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
