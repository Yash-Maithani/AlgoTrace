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
 * A question is asked BEFORE its step, about what that step does:
 *
 *   bubble sort     "Will these two swap?"
 *   selection sort  "Is this the new smallest value?"
 *   insertion sort  "Will this value shift right?"
 *   merge sort      "Which value is written next: the left half's or the right's?"
 *   quick sort      "Is this smaller than the pivot, so it moves to the left side?"
 *   heap sort       "Will the parent move down?"
 *   searching       "Found it, go left, or go right?" (linear: "or keep looking?")
 *   BFS, DFS, Dijkstra, Prim   "Which node is visited next?" (joins the tree)
 *   Kruskal         "Will this edge be added, or would it make a cycle?"
 *   Bellman-Ford    "Will this edge shorten the distance?"
 *   Floyd-Warshall  "Is the path through k shorter?"
 *
 * The answer is read off the step that follows (or, for merge sort, a fact the
 * compare step records) and the explanation is that step's own text. A step
 * is never asked about unless it has a step before it to ask from.
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

    /* Each sort has its own natural question, and the step meta says which sort
       this is: the line id of the comparison, and the variables it carries
       (a selection sort has min_idx, an insertion sort a held key, a quick sort
       a pivot). Every answer is read off the steps that follow, or off a fact
       the compare step itself records. */
    function sortingKind(step) {
        if (step.action !== 'compare') return null;
        var vars = step.vars || {};
        if (step.line === 'cmp-left') return 'heap';
        if (step.line === 'merge-compare') return 'merge';
        if (step.line !== 'compare') return null;
        if (vars.min_idx !== undefined) return 'selection';
        if (vars.key !== undefined) return 'insertion';
        if (vars.pivot !== undefined) return 'quick';
        return 'bubble';
    }

    var SORTING = {};

    /* Bubble: two neighbours are compared and either swap or do not. */
    SORTING.bubble = function (ctx, asked, after) {
        if (asked.indices.length !== 2 || asked.values.length !== 2) return null;
        var swaps = after.action === 'swap' && sameSet(after.indices, asked.indices);
        var a = asked.values[0], b = asked.values[1];
        return {
            kind: 'sorting-swap',
            prompt: 'Next the sort compares ' + a + ' and ' + b + ' (positions ' +
                asked.indices[0] + ' and ' + asked.indices[1] + '). Will these two swap?',
            options: [option('yes', 'Yes, they swap'), option('no', 'No, they stay')],
            answer: swaps ? 'yes' : 'no',
            explain: swaps
                ? after.explain.beginner
                : 'They stay where they are. What the sort does next: ' + after.explain.beginner
        };
    };

    /* Selection: a candidate is compared with the smallest value so far, and
       either becomes the new smallest (a `select` step) or does not. */
    SORTING.selection = function (ctx, asked, after) {
        if (asked.values.length !== 2) return null;
        var smallest = asked.values[0], candidate = asked.values[1];
        var yes = after.action === 'select' && after.line === 'update-min';
        return {
            kind: 'selection-min',
            prompt: 'Next the sort compares ' + candidate + ' (position ' + asked.indices[1] +
                ') with the smallest value so far, ' + smallest + '. Is ' + candidate +
                ' the new smallest value?',
            options: [option('yes', 'Yes, new smallest'), option('no', 'No, ' + smallest + ' stays')],
            answer: yes ? 'yes' : 'no',
            explain: yes
                ? after.explain.beginner
                : candidate + ' is not smaller than ' + smallest + ', so ' + smallest + ' stays the smallest so far.'
        };
    };

    /* Insertion: the held value meets a value to its left, which either
       shifts one place right (a `shift` write) or stops the held value. */
    SORTING.insertion = function (ctx, asked, after) {
        if (asked.values.length !== 1 || asked.vars.key === undefined) return null;
        var key = asked.vars.key, value = asked.values[0];
        var yes = after.action === 'overwrite' && after.line === 'shift';
        if (!yes && !(after.action === 'overwrite' && after.line === 'place')) return null;
        return {
            kind: 'insertion-shift',
            prompt: 'Next the held value ' + key + ' is compared with ' + value + ' (position ' +
                asked.indices[0] + '). Will ' + value + ' shift one place right?',
            options: [option('yes', 'Yes, it shifts'), option('no', 'No, it stays')],
            answer: yes ? 'yes' : 'no',
            explain: yes ? after.explain.beginner : value + ' stays. ' + after.explain.beginner
        };
    };

    /* Merge: the front values of the two halves are compared, and one is taken.
       The compare step records which (`taken`); it is not shown on the stage. */
    SORTING.merge = function (ctx, asked) {
        if (asked.values.length !== 2 || (asked.taken !== 'left' && asked.taken !== 'right')) return null;
        var l = asked.values[0], r = asked.values[1];
        var reason;
        if (l < r) reason = l + ' is smaller than ' + r + ', so the left half’s ' + l + ' goes next.';
        else if (r < l) reason = r + ' is smaller than ' + l + ', so the right half’s ' + r + ' goes next.';
        else {
            var tie = /They are equal.*$/.exec(asked.explain.beginner);
            reason = (tie ? tie[0] : 'They are equal, so the tie rule decides.') + ' The ' +
                asked.taken + ' half’s ' + (asked.taken === 'left' ? l : r) + ' goes next.';
        }
        return {
            kind: 'merge-take',
            prompt: 'Next the merge compares the left half’s ' + l + ' with the right half’s ' + r +
                '. Which value is written next: the left half’s or the right half’s?',
            options: [option('left', 'The left half’s ' + l), option('right', 'The right half’s ' + r)],
            answer: asked.taken,
            explain: reason
        };
    };

    /* Quick: a value is compared with the pivot and is swapped to the left
       side if it is smaller. The pivot is whichever the run chose (the last
       value, the middle or a seeded random one), read from the step. */
    SORTING.quick = function (ctx, asked, after) {
        if (asked.values.length !== 2) return null;
        var value = asked.values[0], pivot = asked.vars.pivot;
        var yes = after.action === 'swap';
        return {
            kind: 'quick-left',
            prompt: 'Next the sort compares ' + value + ' (position ' + asked.indices[0] + ') with the pivot, ' +
                pivot + '. Is ' + value + ' smaller than the pivot, so it moves to the left side?',
            options: [option('yes', 'Yes, to the left'), option('no', 'No, it stays')],
            answer: yes ? 'yes' : 'no',
            explain: yes
                ? after.explain.beginner
                : value + ' is not smaller than the pivot, ' + pivot + ', so it stays where it is.'
        };
    };

    /* Heap: a parent is compared with its children, one or two comparisons
       in all, and then either swaps with the larger child (`swap-down`) or
       stays. Asked at the first comparison; answered by what follows the last. */
    SORTING.heap = function (ctx, asked) {
        var parent = asked.vars.i;
        var at = ctx.next + 1;
        var m = ctx.meta(at);
        while (m && m.action === 'compare' && m.line === 'cmp-right' && m.vars.i === parent) m = ctx.meta(++at);
        if (!m) return null;
        var moves = m.action === 'swap' && m.line === 'swap-down' && m.vars.i === parent;
        var value = asked.values[1];
        return {
            kind: 'heap-down',
            prompt: 'Next the heap compares position ' + parent + ' (value ' + value + ') with its children. ' +
                'Will the parent move down?',
            options: [option('yes', 'Yes, it moves down'), option('no', 'No, it stays')],
            answer: moves ? 'yes' : 'no',
            explain: moves
                ? m.explain.beginner
                : value + ' stays where it is. What the sort does next: ' + m.explain.beginner
        };
    };

    function buildSorting(ctx) {
        var asked = ctx.meta(ctx.next);
        var after = ctx.meta(ctx.next + 1);
        if (!asked || !after) return null;
        var kind = sortingKind(asked);
        if (!kind) return null;
        var q = SORTING[kind](ctx, asked, after);
        if (!q) return null;
        q.step = ctx.next;
        return q;
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

    var GRAPH = {};

    /* Traversals and Dijkstra: which waiting node comes off next. */
    GRAPH.visit = function (ctx, now, next) {
        var answer = String(next.indices[0]);
        var held = frontier(ctx, now);
        if (!held || held.nodes.length < 2 || held.nodes.indexOf(answer) === -1) return null;
        return {
            kind: 'graph-visit',
            prompt: FRONTIER_LABEL[held.key] + held.nodes.join(', ') + '. Which node is visited next?',
            options: held.nodes.map(function (n) { return option(n, n); }),
            answer: answer,
            explain: next.explain.beginner
        };
    };

    /* Prim: which waiting node the cheapest edge brings into the tree. */
    GRAPH.join = function (ctx, now, next) {
        var answer = String(next.indices[1]);
        var held = frontier(ctx, now);
        if (!held || held.nodes.length < 2 || held.nodes.indexOf(answer) === -1) return null;
        return {
            kind: 'graph-join',
            prompt: FRONTIER_LABEL[held.key] + held.nodes.join(', ') + '. Which node joins the tree next?',
            options: held.nodes.map(function (n) { return option(n, n); }),
            answer: answer,
            explain: next.explain.beginner
        };
    };

    /* Kruskal: the next cheapest edge either joins two separate groups or
       closes a loop. The step after it says which. */
    GRAPH.edge = function (ctx, now, next, after) {
        if (!after || (after.action !== 'include' && after.action !== 'reject')) return null;
        var add = after.action === 'include';
        return {
            kind: 'kruskal-edge',
            prompt: 'Next the cheapest edge left, ' + next.indices[0] + ' to ' + next.indices[1] +
                ' (weight ' + next.values[0] + '), is considered. The forest holds ' +
                (now.vars.tree_edges || 0) + ' of ' + now.vars.needed + ' edges. Will it be added, or would it make a cycle?',
            options: [option('add', 'Added to the forest'), option('cycle', 'Makes a cycle, skipped')],
            answer: add ? 'add' : 'cycle',
            explain: after.explain.beginner
        };
    };

    /* Bellman-Ford: an edge is checked against the distances on record, and
       either shortens the far end's distance (a `relax` step) or does not. */
    GRAPH.relax = function (ctx, now, next, after) {
        if (!after || (after.action !== 'relax' && after.action !== 'reject')) return null;
        var from = next.indices[0], to = next.indices[1], w = next.values[0];
        var yes = after.action === 'relax';
        return {
            kind: 'bellman-relax',
            prompt: 'Next the edge ' + from + ' to ' + to + ' (weight ' + w + ') is checked. ' + from +
                ' is at distance ' + next.vars.from + ' now and ' + to + ' at ' + next.vars.to +
                '. Will this edge shorten the distance to ' + to + '?',
            options: [option('yes', 'Yes, it shortens it'), option('no', 'No, it does not')],
            answer: yes ? 'yes' : 'no',
            explain: after.explain.beginner
        };
    };

    /* Floyd-Warshall: the direct distance i to j is weighed against going
       through k. The numbers are the three pieces; adding two of them is the
       prediction. */
    GRAPH.through = function (ctx, now, next, after) {
        if (!after || (after.action !== 'relax' && after.action !== 'reject') || next.values.length < 3) return null;
        var i = next.indices[0], j = next.indices[1], k = next.indices[2];
        var yes = after.action === 'relax';
        return {
            kind: 'floyd-through',
            prompt: 'Next ' + i + ' to ' + j + ' (' + next.values[0] + ' now) is tested against the path through ' + k +
                ': ' + i + ' to ' + k + ' is ' + next.values[1] + ' and ' + k + ' to ' + j + ' is ' + next.values[2] +
                '. Is the path through ' + k + ' shorter?',
            options: [option('yes', 'Yes, shorter'), option('no', 'No, keep ' + next.values[0])],
            answer: yes ? 'yes' : 'no',
            explain: after.explain.beginner
        };
    };

    /* Which question a step asks is told by what the step is: its action and
       the line id it carries. */
    function graphKind(next) {
        if (next.action === 'visit' && next.indices.length === 1) return 'visit';
        if (next.action === 'consider') {
            if (next.line === 'pop-min' && next.indices.length === 2) return 'join';
            if (next.line === 'take-next' && next.indices.length === 2) return 'edge';
            if (next.line === 'edge-loop' && next.indices.length === 2) return 'relax';
            if (next.line === 'compare' && next.indices.length === 3) return 'through';
        }
        return null;
    }

    function buildGraph(ctx) {
        var now = ctx.meta(ctx.at);
        var next = ctx.meta(ctx.next);
        if (!now || !next) return null;
        var kind = graphKind(next);
        if (!kind) return null;
        var q = GRAPH[kind](ctx, now, next, ctx.meta(ctx.next + 1));
        if (!q) return null;
        q.step = ctx.next;
        return q;
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
                    : 'No step in this run can be predicted';
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
