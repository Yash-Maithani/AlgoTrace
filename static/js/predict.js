/* Predict mode: ask the learner what the next step will do, then play it.
 *
 * Two halves, kept apart on purpose.
 *
 *  1. Question builders, one per family (sorting, searching, graph). Each
 *     reads the REAL step meta (README section 1 and 4 of the lessons
 *     contract) and returns a question or null. The correct answer is read
 *     off the step that actually follows; options are taken from the run's own
 *     data (the live queue, the stack, the unvisited set), never invented.
 *     This half touches no DOM, so node runs it in the unit tests.
 *
 *  2. The session, mount(): the toggle, the score, and the gate the shared
 *     workspace asks before it plays a step. It renders nothing family
 *     specific; the Learn panel draws whatever question object it is given.
 *
 * A question is asked BEFORE its step, about the step after it:
 *
 *   sorting    the next step compares two values. "Will these two swap?"
 *              The answer is whether the step after that swaps exactly them.
 *   searching  the next step compares the target with one value. "Found it,
 *              go left, or go right?" (linear search: "found, or keep
 *              looking?"). The answer is the step after that.
 *   graph      the next step visits (or, in Prim, joins) a node. "Which node
 *              is visited next?" Options are the frontier now.
 *
 * Question object:
 *   { step, kind, prompt, options: [{id, label}], answer, explain }
 * `step` is the index being asked about, `explain` the real one line reason
 * shown after the answer.
 */
(function (root) {
    'use strict';

    function sameSet(a, b) {
        if (!a || !b || a.length !== b.length) return false;
        return a.every(function (v) { return b.indexOf(v) !== -1; });
    }

    function unique(list) {
        var seen = {};
        return list.filter(function (v) {
            var key = String(v);
            if (seen[key]) return false;
            seen[key] = true;
            return true;
        });
    }

    function option(id, label) { return { id: String(id), label: label }; }

    /* --- sorting -------------------------------------------------------------- */

    /* Only a run in which a comparison is sometimes followed by a swap of the
       same two cells is asked about: that is the thing "will these two swap?"
       can truthfully mean. Selection, insertion, merge and quick sort never do
       that (they select, shift, write or swap a different pair), so asking
       would invent an answer. */
    function sortingHasPairSwaps(ctx) {
        if (ctx.cache.pairSwaps !== undefined) return ctx.cache.pairSwaps;
        var found = false;
        for (var i = 0; i + 1 < ctx.length && !found; i++) {
            var a = ctx.meta(i), b = ctx.meta(i + 1);
            found = !!a && !!b && a.action === 'compare' && a.indices.length === 2 &&
                b.action === 'swap' && sameSet(a.indices, b.indices);
        }
        ctx.cache.pairSwaps = found;
        return found;
    }

    function buildSorting(ctx) {
        var asked = ctx.meta(ctx.next);
        var after = ctx.meta(ctx.next + 1);
        if (!asked || !after || asked.action !== 'compare' || asked.indices.length !== 2) return null;
        if (asked.values.length !== 2 || !sortingHasPairSwaps(ctx)) return null;

        var swaps = after.action === 'swap' && sameSet(after.indices, asked.indices);
        var a = asked.values[0], b = asked.values[1];
        return {
            step: ctx.next,
            kind: 'sorting-swap',
            prompt: 'Next the sort compares ' + a + ' and ' + b + ' (positions ' +
                asked.indices[0] + ' and ' + asked.indices[1] + '). Will these two swap?',
            options: [option('yes', 'Yes, they swap'), option('no', 'No, they stay')],
            answer: swaps ? 'yes' : 'no',
            // What really happened next, in the run's own words.
            explain: swaps
                ? after.explain.beginner
                : 'They stay where they are. What the sort does next: ' + after.explain.beginner
        };
    }

    /* --- searching ------------------------------------------------------------ */

    function searchHasDiscards(ctx) {
        if (ctx.cache.discards !== undefined) return ctx.cache.discards;
        var found = false;
        for (var i = 0; i < ctx.length && !found; i++) {
            var m = ctx.meta(i);
            found = !!m && m.action === 'discard';
        }
        ctx.cache.discards = found;
        return found;
    }

    function buildSearching(ctx) {
        var asked = ctx.meta(ctx.next);
        var after = ctx.meta(ctx.next + 1);
        if (!asked || !after || asked.action !== 'compare' || !asked.indices.length) return null;

        var halves = searchHasDiscards(ctx);
        var where = asked.indices[0];
        var value = asked.values[0];
        var target = asked.vars && asked.vars.target;

        var answer, explain;
        if (after.action === 'found') {
            answer = 'found';
            explain = after.explain.beginner;
        } else if (after.action === 'discard') {
            answer = after.line === 'go-left' ? 'left' : 'right';
            explain = after.explain.beginner;
        } else if (after.action === 'compare' || after.action === 'missing') {
            answer = 'onward';
            explain = value + ' is not ' + target + ', so the search moves on. ' +
                (after.action === 'missing' ? after.explain.beginner : '');
            explain = explain.trim();
        } else {
            return null;
        }
        // The answer has to be one of the options this run can ever offer.
        if (!halves && answer !== 'found' && answer !== 'onward') return null;
        if (halves && answer === 'onward') return null;

        return {
            step: ctx.next,
            kind: halves ? 'search-halves' : 'search-scan',
            prompt: (halves
                ? 'Next the search looks at position ' + where + ', the middle of the live range. It holds ' + value
                : 'Next the search checks position ' + where + ', which holds ' + value) +
                '. The target is ' + target + '. ' +
                (halves ? 'Found it, go left, or go right?' : 'Found it, or keep looking?'),
            options: halves
                ? [option('found', 'Found it'), option('left', 'Go left'), option('right', 'Go right')]
                : [option('found', 'Found it'), option('onward', 'Keep looking')],
            answer: answer,
            explain: explain
        };
    }

    /* --- graph ---------------------------------------------------------------- */

    /* The nodes waiting right now, named by the structure that holds them. */
    function frontier(ctx, now) {
        var vars = now.vars || {};
        var key = ['queue', 'stack', 'unvisited'].filter(function (k) { return Array.isArray(vars[k]); })[0];
        if (key) return { key: key, nodes: unique(vars[key].map(String)) };

        // Prim keeps its frontier in a heap of edges. The nodes those edges
        // reach are the ones every `enqueue` step so far announced, less the
        // ones the tree has since taken in.
        if (Array.isArray(vars.visited)) {
            var visited = vars.visited.map(String), reached = [];
            for (var i = 0; i <= ctx.at; i++) {
                var m = ctx.meta(i);
                if (m && m.action === 'enqueue') reached = reached.concat(m.indices.map(String));
            }
            return { key: 'frontier', nodes: unique(reached).filter(function (n) { return visited.indexOf(n) === -1; }) };
        }
        return null;
    }

    var FRONTIER_LABEL = {
        queue: 'The queue, front first: ',
        stack: 'The stack, top last: ',
        unvisited: 'Not yet settled: ',
        frontier: 'Waiting to join the tree: '
    };

    function buildGraph(ctx) {
        var now = ctx.meta(ctx.at);
        var next = ctx.meta(ctx.next);
        if (!now || !next) return null;

        var joins = next.action === 'consider' && next.indices.length === 2;
        var visits = next.action === 'visit' && next.indices.length === 1;
        if (!joins && !visits) return null;

        var answer = String(joins ? next.indices[1] : next.indices[0]);
        var held = frontier(ctx, now);
        if (!held || held.nodes.length < 2 || held.nodes.indexOf(answer) === -1) return null;

        return {
            step: ctx.next,
            kind: joins ? 'graph-join' : 'graph-visit',
            prompt: FRONTIER_LABEL[held.key] + held.nodes.join(', ') + '. ' +
                (joins ? 'Which node joins the tree next?' : 'Which node is visited next?'),
            options: held.nodes.map(function (n) { return option(n, n); }),
            answer: answer,
            explain: next.explain.beginner
        };
    }

    var builders = { sorting: buildSorting, searching: buildSearching, graph: buildGraph };

    /* --- the module's pure API ------------------------------------------------ */

    /* The question to ask before step `next`, or null. `ctx` carries the run:
       meta(i), length, and a cache shared by the run's questions. */
    function makeContext(metas, cache) {
        return {
            length: metas.length,
            meta: function (i) { return i >= 0 && i < metas.length ? metas[i] : null; },
            cache: cache || {}
        };
    }

    function build(family, ctx, at) {
        var builder = builders[family];
        if (!builder || at < 0 || at + 1 >= ctx.length) return null;
        ctx.at = at;
        ctx.next = at + 1;
        var q = builder(ctx);
        if (!q) return null;
        // Never ship a question that cannot be answered.
        var ids = q.options.map(function (o) { return o.id; });
        if (!ids.length || unique(ids).length !== ids.length || ids.indexOf(q.answer) === -1) return null;
        return q;
    }

    /* Every question a whole run holds, in order. For tests and for the
       "n questions in this run" note. */
    function questionsFor(family, metas) {
        var ctx = makeContext(metas);
        var out = [];
        for (var at = 0; at + 1 < metas.length; at++) {
            var q = build(family, ctx, at);
            if (q) out.push(q);
        }
        return out;
    }

    var api = { builders: builders, build: build, questionsFor: questionsFor, makeContext: makeContext };
    if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
    if (typeof document === 'undefined') { root.Predict = api; return; }

    /* --- the session (browser only) ------------------------------------------- */

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    /* Attach Predict mode to a workspace. The workspace calls the returned
       gate before it plays a step forward (intercept), after any move
       (onGo) and when a run starts or is thrown away (reset). */
    function mount(ws, options) {
        var family = options.family;
        var panel = ws.panel;
        var bar = document.querySelector('.control-bar');
        if (!panel || !bar || !builders[family]) return null;

        var state;
        function fresh() {
            return { answered: {}, correct: 0, total: 0, skipped: 0, pending: null, cache: {} };
        }
        state = fresh();
        var on = false;

        /* --- the toggle, the score and the note in the control bar --- */
        var box = el('div', 'predict-control');
        var label = el('label', 'predict-toggle');
        var input = document.createElement('input');
        input.type = 'checkbox';
        input.id = 'predict-toggle';
        label.appendChild(input);
        label.appendChild(el('span', null, 'Predict'));
        var score = el('span', 'predict-score');
        score.hidden = true;
        var note = el('span', 'predict-note');
        note.hidden = true;
        box.appendChild(label);
        box.appendChild(score);
        box.appendChild(note);
        var anchor = bar.querySelector('.step-counter');
        bar.insertBefore(box, anchor || null);

        function context() { return makeContext(metas(), state.cache); }

        function metas() {
            var out = [];
            for (var i = 0; i < ws.steps.length; i++) out.push(ws.metaAt(i));
            return out;
        }

        function syncUi() {
            score.hidden = !on || state.total + state.skipped === 0;
            var text = state.correct + ' of ' + state.total + ' correct';
            if (state.skipped) text += ', ' + state.skipped + ' skipped';
            score.textContent = text;

            note.hidden = !on || !ws.steps.length;
            if (on && ws.steps.length) {
                var count = questionsFor(family, metas()).length;
                note.textContent = count
                    ? count + (count === 1 ? ' question' : ' questions') + ' in this run'
                    : 'This algorithm has nothing to predict yet';
            }
        }

        function dismiss() {
            state.pending = null;
            panel.clearQuestion();
        }

        function clearAll() {
            dismiss();
            panel.clearResult();
        }

        function finish(q, auto) {
            state.pending = null;
            syncUi();
            ws.resume(q.step, auto);
            // Leave the learner on the control that carries on.
            var next = ws.forward && !ws.forward.disabled ? ws.forward : ws.playPause;
            if (next && !next.disabled) next.focus();
        }

        function answer(id) {
            var p = state.pending;
            if (!p) return;
            var q = p.question;
            var right = id === q.answer;
            var correct = q.options.filter(function (o) { return o.id === q.answer; })[0];
            state.total++;
            if (right) state.correct++;
            state.answered[q.step] = true;
            var detail = right
                ? q.explain
                : 'The answer was “' + correct.label + '”. ' + q.explain;
            panel.clearQuestion();
            panel.showResult({ right: right, text: detail });
            panel.announce((right ? 'Correct. ' : 'Not quite. ') + detail);
            finish(q, p.auto);
        }

        function skip() {
            var p = state.pending;
            if (!p) return;
            state.answered[p.question.step] = true;
            state.skipped++;
            panel.clearQuestion();
            panel.clearResult();
            panel.announce('Skipped.');
            finish(p.question, p.auto);
        }

        var gate = {
            get pending() { return !!state.pending; },
            get on() { return on; },

            /* About to play step `next`. True means a question took over and
               the step must wait; the answer or Skip plays it. */
            intercept: function (next, auto) {
                if (!on) return false;
                if (state.pending) {
                    // Pressing Step or Play with a question open is not an answer.
                    gate.nudge();
                    return true;
                }
                if (state.answered[next]) return false;
                var q = build(family, context(), next - 1);
                if (!q) return false;
                state.pending = { question: q, auto: !!auto };
                panel.clearResult();
                panel.showQuestion(q, Object.keys(state.answered).length + 1, { answer: answer, skip: skip });
                return true;
            },

            nudge: function () {
                panel.announce('Answer the question, or skip it, to carry on.');
                panel.focusQuestion();
            },

            /* Any move. Going back, or to the start, leaves a question
               unanswered rather than answering it, so it is asked again on
               the way forward; an answered one never is. */
            onGo: function (index, previous) {
                if (ws.gateStepping || index >= previous) return;
                clearAll();
            },

            reset: function () {
                state = fresh();
                clearAll();
                syncUi();
            }
        };

        input.addEventListener('change', function () {
            on = input.checked;
            if (!on) clearAll();
            syncUi();
            panel.announce(on ? 'Predict mode on. Before some steps you will be asked what happens next.'
                              : 'Predict mode off.');
        });

        syncUi();
        return gate;
    }

    api.mount = mount;
    root.Predict = api;
})(typeof window !== 'undefined' ? window : this);
