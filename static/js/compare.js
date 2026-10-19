/* /compare: two sorts, one input, one transport.
 *
 * Each side is a workspace of its own (Workspace.create with a root), with
 * its own stage (static/js/sortstage.js, the bars /sorting draws), its own
 * counters and its own variant and seed. Both are driven by one
 * Workspace.group, so the transport steps them together and a side that
 * finishes first waits on its last step while the other carries on.
 *
 * Both sides run through /run_sort with the same values, so every count here
 * is the count /sorting shows for that input and variant. No Learn panel and
 * no Predict: the point of this page is the side by side.
 */
(function () {
    'use strict';

    var config = JSON.parse(document.getElementById('compare-config').textContent);
    var LESSON_FOR = config.lessonIds;

    function byId(id) { return document.getElementById(id); }

    function plural(count, noun) {
        return count + ' ' + (count === 1 ? noun.replace(/s$/, '') : noun);
    }

    /* The counter /sorting labels the second count with. */
    function countNoun(lesson) {
        return (lesson && lesson.countLabel) || 'swaps';
    }

    function capital(text) { return text.charAt(0).toUpperCase() + text.slice(1); }

    /* /sorting's speed curve, so a slider position plays at the same pace. */
    function delayFor(value) {
        var delay;
        if (value <= 100) {
            delay = 1200 - (value * 10);
        } else {
            var extra = value - 100;
            delay = 200 - (Math.pow(extra / 100, 1.5) * 190);
        }
        return Math.max(delay, 10);
    }

    /* ---------------------------------------------------------------------
       One side
       --------------------------------------------------------------------- */

    function Side(name, onChange) {
        var self = this;
        this.name = name;
        this.root = byId('compare-' + name);
        this.pick = document.querySelector('.compare-pick[data-side="' + name + '"]');
        this.select = this.pick.querySelector('[data-role="algorithm"]');
        this.seedRow = this.pick.querySelector('[data-role="seed-row"]');
        this.seedInput = this.pick.querySelector('[data-role="seed"]');
        this.note = this.pick.querySelector('[data-role="variant-note"]');
        this.chosen = {};
        this.onChange = onChange;

        this.view = {};
        ['title', 'open', 'comparisons', 'second', 'second-label', 'status',
         'seed-shown', 'seed-value'].forEach(function (role) {
            self.view[role] = self.root.querySelector('[data-role="' + role + '"]');
        });

        Array.prototype.forEach.call(this.pick.querySelectorAll('[data-variant-for]'), function (box) {
            var display = box.getAttribute('data-variant-for');
            self.chosen[display] = box.querySelector('input[type="radio"]:checked').value;
            box.addEventListener('change', function (event) {
                if (!event.target.matches('input[type="radio"]')) return;
                self.chosen[display] = event.target.value;
                self.changed();
            });
        });
        this.select.addEventListener('change', function () { self.changed(); });
        this.pick.querySelector('[data-role="new-seed"]').addEventListener('click', function () {
            self.seedInput.value = 1 + Math.floor(Math.random() * 99999);
            self.seedInput.focus();
        });

        this.stage = SortStage.create(this.root.querySelector('[data-part="bars"]'),
                                      this.root.querySelector('[data-part="empty"]'));
        this.ws = Workspace.create({
            root: this.root,
            shortcuts: false,
            renderStep: function (step, context) {
                self.stage.render(step, context.payload);
                self.showCounts(step.vars.comparisons, step.vars.swaps);
            },
            clearStage: function () {
                self.stage.clear();
                self.showCounts(0, 0);
                self.view.status.textContent = '';
            }
        });
        this.sync();
    }

    Side.prototype.algorithm = function () { return this.select.value; };

    Side.prototype.variant = function () { return this.chosen[this.algorithm()]; };

    Side.prototype.lesson = function () {
        var base = window.LESSONS[LESSON_FOR[this.algorithm()]];
        return Variants.resolve(base, this.variant());
    };

    /* "Quick Sort (Pivot: Middle)", or just "Heap Sort" without a switch. */
    Side.prototype.label = function () {
        var lesson = this.lesson();
        if (!lesson.variants) return this.algorithm();
        return this.algorithm() + ' (' + lesson.variants.label + ': ' + lesson.variantLabel + ')';
    };

    Side.prototype.isRandomPivot = function () {
        return this.algorithm() === 'Quick Sort' && this.variant() === 'random';
    };

    Side.prototype.showCounts = function (comparisons, second) {
        this.view.comparisons.textContent = comparisons;
        this.view.second.textContent = second;
    };

    /* Show this algorithm's switch, its note, the seed when it needs one,
       the title, the counter's name and the link to its own page. */
    Side.prototype.sync = function () {
        var algorithm = this.algorithm();
        Array.prototype.forEach.call(this.pick.querySelectorAll('[data-variant-for]'), function (box) {
            box.hidden = box.getAttribute('data-variant-for') !== algorithm;
        });
        var lesson = this.lesson();
        this.seedRow.hidden = !this.isRandomPivot();
        this.note.textContent = lesson.variantNote || '';
        this.view.title.textContent = this.label();
        this.view['second-label'].textContent = capital(countNoun(lesson));
        this.view.open.href = '/sorting?algorithm=' + encodeURIComponent(algorithm);
        this.view.open.setAttribute('aria-label', 'Open ' + algorithm + ' in Sorting');
        if (!this.isRandomPivot()) this.view['seed-shown'].hidden = true;
    };

    Side.prototype.changed = function () {
        this.sync();
        this.onChange();
    };

    Side.prototype.request = function (values) {
        var body = { algorithm: this.algorithm(), values: values };
        if (this.variant()) body.variant = this.variant();
        if (this.isRandomPivot() && this.seedInput.value.trim() !== '') {
            body.seed = this.seedInput.value.trim();
        }
        return body;
    };

    /* The run records its seed: it goes back into the field, so running
       again replays it, and it shows beside the counters. */
    Side.prototype.load = function (payload) {
        var seeded = payload.seed !== null && payload.seed !== undefined;
        if (seeded) this.seedInput.value = payload.seed;
        this.view['seed-shown'].hidden = !seeded;
        this.view['seed-value'].textContent = seeded ? payload.seed : '';
        this.ws.load(payload);
    };

    /* Where this side is at the shared tick. */
    Side.prototype.showStatus = function (tick, length) {
        var steps = this.ws.steps.length;
        if (!steps) { this.view.status.textContent = ''; return; }
        if (tick >= steps - 1) {
            this.view.status.textContent = 'Finished in ' + plural(steps, 'steps') +
                (tick < length - 1 ? '. Waiting for the other side.' : '.');
        } else {
            this.view.status.textContent = 'Step ' + (tick + 1) + ' of ' + steps;
        }
    };

    /* ---------------------------------------------------------------------
       The page
       --------------------------------------------------------------------- */

    var banner = byId('run-banner');
    var errorBox = byId('setup-error');
    var methodRandom = byId('random-input');
    var methodManual = byId('manual-input-choice');
    var presetUi = null;
    var group = null;

    function clearBanner() {
        banner.textContent = '';
        banner.removeAttribute('data-outcome');
    }

    /* A side changed algorithm, variant or seed: the loaded comparison no
       longer describes what is on screen, so both runs go. */
    function stale() {
        left.ws.discard();
        right.ws.discard();
        if (group) group.restart();
        clearBanner();
        if (presetUi) presetUi.refresh();
    }

    var left = new Side('left', stale);
    var right = new Side('right', stale);

    function finishText() {
        var a = left.ws.payload.result;
        var b = right.ws.payload.result;
        var nameA = left.label();
        var nameB = right.label();
        if (nameA === nameB) {
            nameA = 'Left, ' + nameA;
            nameB = 'Right, ' + nameB;
        }
        /* Counting Sort and Radix Sort never compare two values, so 0 against
           anything says nothing about who did less work. When either side
           made no comparisons the banner compares the steps each side drew
           instead, and says so. */
        var measure = 'comparisons';
        var x = a.comparisons, y = b.comparisons;
        var text = '';
        if (x === 0 || y === 0) {
            measure = 'steps';
            x = left.ws.payload.steps.length;
            y = right.ws.payload.steps.length;
            var zero = a.comparisons === 0 && b.comparisons === 0
                ? 'Neither side compares two values, '
                : (a.comparisons === 0 ? nameA : nameB) + ' never compares two values, ';
            text = zero + 'so comparisons cannot say which did less. This compares the total ' +
                'steps each side showed instead. ';
        }
        if (x === y) {
            text += 'Both used ' + plural(x, measure) + '.';
        } else {
            var leftWins = x < y;
            var few = leftWins ? x : y;
            var many = leftWins ? y : x;
            text += (leftWins ? nameA : nameB) + ' used ' +
                plural(many - few, measure).replace(/^(\d+) /, '$1 fewer ') +
                ' than ' + (leftWins ? nameB : nameA) + ': ' + few + ' against ' + many + '.';
        }
        if (measure === 'steps') {
            text += ' ' + nameA + ' made ' + plural(a.comparisons, 'comparisons') + ', ' +
                nameB + ' made ' + plural(b.comparisons, 'comparisons') + '.';
        }
        text += ' ' + nameA + ' made ' + plural(a.swaps, countNoun(left.lesson())) + ', ' +
            nameB + ' made ' + plural(b.swaps, countNoun(right.lesson())) + '.';
        text += ' These counts are for this one input of ' + plural(a.n, 'values') +
            ': a different input can change them, and even which side does less.';
        return text;
    }

    group = Workspace.group([left.ws, right.ws], {
        delayFor: delayFor,
        onTick: function (tick, length) {
            left.showStatus(tick, length);
            right.showStatus(tick, length);
            if (tick >= length - 1 && left.ws.payload && right.ws.payload) {
                banner.setAttribute('data-outcome', 'found');
                banner.textContent = finishText();
            } else {
                clearBanner();
            }
        }
    });

    function syncInputMethod() {
        var manual = methodManual.checked;
        byId('size-field').hidden = manual;
        byId('values-field').hidden = !manual;
    }
    methodRandom.addEventListener('change', syncInputMethod);
    methodManual.addEventListener('change', syncInputMethod);
    syncInputMethod();

    function arraySize() {
        var n = parseInt(byId('array-size').value, 10);
        return isNaN(n) ? null : n;
    }

    /* The values both sides will sort. A random array is drawn here, not on
       the server, so both get the same one, and it goes into the values box
       so the run can be replayed. */
    function readValues() {
        if (methodManual.checked) {
            var typed = byId('manual-input').value;
            if (!typed.trim()) return { error: 'Enter some numbers, separated by commas.' };
            return { values: typed };
        }
        var n = arraySize();
        if (n === null || n < 5 || n > config.maxSize) {
            return { error: 'Array size must be between 5 and ' + config.maxSize + '.' };
        }
        var values = Presets.generate('random', n, 1 + Math.floor(Math.random() * 99999));
        byId('manual-input').value = values.join(', ');
        return { values: values };
    }

    function post(body) {
        return fetch('/run_sort', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(function (response) {
            return response.json().then(function (data) { return { ok: response.ok, body: data }; });
        });
    }

    var runs = 0;

    function run() {
        errorBox.textContent = '';
        clearBanner();
        var input = readValues();
        if (input.error) {
            errorBox.textContent = input.error;
            return Promise.resolve();
        }
        var mine = ++runs;
        return Promise.all([post(left.request(input.values)), post(right.request(input.values))])
            .then(function (results) {
                if (mine !== runs) return;             // a newer run is on its way
                var problems = [];
                results.forEach(function (result, k) {
                    if (!result.ok || result.body.error) {
                        problems.push((k ? 'Right: ' : 'Left: ') + (result.body.error || 'the run failed.'));
                    }
                });
                if (problems.length) {
                    left.ws.discard();
                    right.ws.discard();
                    group.restart();
                    errorBox.textContent = problems.join(' ');
                    return;
                }
                left.load(results[0].body);
                right.load(results[1].body);
                group.restart();
            })
            .catch(function () {
                errorBox.textContent = 'Could not reach the server. Try again.';
            });
    }

    byId('run-button').addEventListener('click', run);

    /* The same presets as /sorting. The line under them says what the shape
       means for each side. */
    presetUi = Presets.mount({
        host: byId('preset-host'),
        getLesson: function () {
            var notes = {};
            Presets.ORDER.forEach(function (kind) {
                notes[kind] = [left, right].map(function (side, k) {
                    var said = (side.lesson().presetNotes || {})[kind] || '';
                    return (k ? 'Right, ' : 'Left, ') + side.label() + ': ' + said;
                }).join(' ');
            });
            return { presetNotes: notes };
        },
        getSize: function () {
            var n = arraySize();
            return Math.min(config.maxSize, Math.max(5, n === null ? 20 : n));
        },
        apply: function (list) {
            byId('manual-input').value = list.join(', ');
            methodManual.checked = true;
            syncInputMethod();
            errorBox.textContent = '';
        }
    });

    /* "What to try": set both sides and the input, then run. */
    function setSide(side, algorithm, variant) {
        side.select.value = algorithm;
        if (variant) {
            var key = side.pick.querySelector('[data-variant-for="' + algorithm + '"]')
                .getAttribute('data-variant-key');
            byId(side.name + '-variant-' + key + '-' + variant).checked = true;
            side.chosen[algorithm] = variant;
        }
        side.seedInput.value = '';
        side.sync();
    }

    Array.prototype.forEach.call(document.querySelectorAll('[data-try]'), function (button) {
        button.addEventListener('click', function () {
            var t = config.tries[Number(button.getAttribute('data-try'))];
            setSide(left, t.left, t.left_variant);
            setSide(right, t.right, t.right_variant);
            stale();
            byId('array-size').value = t.size;
            document.querySelector('#preset-host [data-preset="' + t.preset + '"]').click();
            run().then(function () {
                byId('compare-left').scrollIntoView({ block: 'nearest' });
            });
        });
    });

    // For the browser tests and the console: the two sides and the group.
    window.Compare = { left: left, right: right, group: group, run: run };
})();
