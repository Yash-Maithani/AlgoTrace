/* The first-visit tour of a workspace: five short steps, each lighting up a real
 * control and saying what it is for.
 *
 * Plain DOM, no library. One script tag per workspace page names its workspace:
 *
 *   <script src=".../tour.js" data-workspace="sorting"></script>
 *
 * The names are sorting, searching, graph (every graph algorithm page shares it)
 * and astar. The first time a workspace is opened the tour starts by itself and
 * that workspace is remembered in localStorage under one key, as a comma list of
 * names ("sorting,graph"). A "Take the tour" button in the control bar plays it
 * again. If storage is blocked nothing is remembered, so the tour never starts
 * by itself and the button is the only way in.
 *
 * What it promises:
 *   - the tour is a modal dialog. Focus moves into it, Tab stays inside it, Esc,
 *     Skip and Done close it, and focus goes back to where it was
 *   - each step is announced: the card is a polite live region
 *   - it only ever dims the page and lights one element; nothing is clicked for
 *     the learner, so the workspace is left exactly as it was found
 *   - on a phone or tablet (one column, under 1024px) the card is a sheet at the top or bottom edge of the screen,
 *     whichever is farther from the lit element, and the page is scrolled so the
 *     two never overlap
 *   - under prefers-reduced-motion nothing animates
 *   - the keys it handles (arrows, Esc) are its own: the card carries data-keys="own",
 *     which workspace.js already leaves alone
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'pbl2.tourSeen';
    var script = document.currentScript;
    var NAME = script && script.getAttribute('data-workspace');
    if (!NAME) return;

    /* ------------------------------------------------------------------ */
    /* What each step lights up. A target is a selector, a function that    */
    /* returns an element, or a list of those tried in order; the first one */
    /* that is on screen wins, so a page missing a part loses that spotlight*/
    /* and keeps the words.                                                  */
    /* ------------------------------------------------------------------ */

    function nth(selector, index) {
        return function () { return document.querySelectorAll(selector)[index] || null; };
    }

    var TARGETS = {
        picker: ['#algo-picker'],
        input: {
            sorting: ['.setup-grid > div:last-child'],
            searching: ['.setup-grid > div:last-child'],
            graph: [nth('.workspace-setup > .panel', 1)],
            astar: [nth('.workspace-setup > .panel', 1)]
        },
        transport: ['.control-bar'],
        learn: ['#learn-panel .learn-tabs', '#learn-panel'],
        predict: ['.predict-control', '.control-bar']
    };

    /* ------------------------------------------------------------------ */
    /* The words. Plain language, written for someone who has not met the   */
    /* algorithm yet, and specific to the workspace.                        */
    /* ------------------------------------------------------------------ */

    var TRANSPORT = 'Press Space to play or pause, the left and right arrow keys to step back and forward, and R to go back to the start.';
    var LEARN = 'Explain says in plain words what the step just did. Code shows the line that is running, and its language tabs switch between pseudocode, Python, C, C++ and Java. Complexity shows how much work the algorithm does as the input grows.';

    var COPY = {
        sorting: [
            ['Pick a sort', 'Each card is a sorting algorithm, from bubble sort to radix sort. Click one to switch to it. Some have a choice of their own, such as which value quick sort uses as its pivot.'],
            ['Choose your numbers', 'Type your own list or let the site make a random one. The shape buttons give you a list that is already sorted, reversed or nearly sorted, which is the fastest way to see a best case and a worst case. Then press Run the sort.'],
            ['Play it one step at a time', 'Once you run, the bars move one step at a time. Use play and pause, or step forward and back at your own pace. ' + TRANSPORT],
            ['Read the Learn panel', LEARN],
            ['Try Predict', 'Switch Predict on and the run stops before some steps to ask what happens next, for example whether two bars will swap. Guessing first is the best way to learn a sort. You can replay this tour any time with the Take the tour button.']
        ],
        searching: [
            ['Pick a search', 'Each card is a way of finding a value in a list: linear, binary or jump search. Click one to switch to it.'],
            ['Set up the list and the target', 'Type a list and the number to look for, or press Random array. Binary and jump search need a sorted list, so Sort it fixes that. The target buttons pick a value that is in the list, or one that is not, so you can see both endings. Then press Run the search.'],
            ['Play it one step at a time', 'Once you run, each cell the search looks at is marked as it goes. Use play and pause, or step forward and back at your own pace. ' + TRANSPORT],
            ['Read the Learn panel', LEARN],
            ['Try Predict', 'Switch Predict on and the run stops to ask what the search does next, for example whether it finds the target, goes left or goes right. Guessing first is the best way to learn a search. You can replay this tour any time with the Take the tour button.']
        ],
        graph: [
            ['Pick a graph algorithm', 'Each card is a graph algorithm: breadth-first and depth-first search, Dijkstra, Prim, Kruskal, Floyd-Warshall, Bellman-Ford and topological sort. A* is here too, on a grid of its own. Click one to open it.'],
            ['Describe your graph', 'A graph is typed as one edge per line. The format guide above the box shows the shape, and the demo buttons load a ready made graph. You can also make a random one. Then press Run the algorithm.'],
            ['Play it one step at a time', 'Once you run, the nodes and edges change colour step by step. Use play and pause, or step forward and back at your own pace. ' + TRANSPORT],
            ['Read the Learn panel', LEARN],
            ['Try Predict', 'Switch Predict on and the run stops to ask what happens next, for example which node is visited next. Guessing first is the best way to learn a graph algorithm. You can replay this tour any time with the Take the tour button.']
        ],
        astar: [
            ['Pick a graph algorithm', 'A* is one of the Graphs algorithms. This list switches between all of them, so you can compare how each one finds its way.'],
            ['Draw your own maze', 'Click or drag on the grid to place walls, and drag S and G to move the start and the goal. Or start from a ready made grid. Then press Run A*, or Run Dijkstra on the same grid to compare how many cells each one has to look at.'],
            ['Play it one step at a time', 'Once you run, the cells are marked as A* looks at them. Use play and pause, or step forward and back at your own pace. ' + TRANSPORT],
            ['Read the Learn panel', LEARN],
            ['Try Predict', 'Switch Predict on and the run stops to ask which cell A* looks at next. Guessing first is the best way to see why it heads for the goal. You can replay this tour any time with the Take the tour button.']
        ]
    };

    function buildSteps() {
        var words = COPY[NAME];
        if (!words) return [];
        var targets = [TARGETS.picker, TARGETS.input[NAME], TARGETS.transport, TARGETS.learn, TARGETS.predict];
        return words.map(function (pair, i) {
            return { title: pair[0], body: pair[1], target: targets[i] };
        });
    }

    /* ------------------------------------------------------------------ */
    /* Storage: one key, a comma list, every access guarded                  */
    /* ------------------------------------------------------------------ */

    /* The names already toured, or null when storage cannot be used. */
    function readSeen() {
        try {
            var raw = window.localStorage.getItem(STORAGE_KEY);
            return raw ? raw.split(',') : [];
        } catch (error) {
            return null;
        }
    }

    function markSeen() {
        var seen = readSeen();
        if (seen === null || seen.indexOf(NAME) !== -1) return;
        seen.push(NAME);
        try { window.localStorage.setItem(STORAGE_KEY, seen.join(',')); } catch (error) { /* not remembered */ }
    }

    /* ------------------------------------------------------------------ */
    /* Small DOM helpers                                                     */
    /* ------------------------------------------------------------------ */

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function isVisible(node) {
        if (!node) return false;
        var box = node.getBoundingClientRect();
        return box.width > 0 && box.height > 0 && getComputedStyle(node).visibility !== 'hidden';
    }

    function resolve(list) {
        for (var i = 0; i < list.length; i++) {
            var found = typeof list[i] === 'string' ? document.querySelector(list[i]) : list[i]();
            if (isVisible(found)) return found;
        }
        return null;
    }

    function headerHeight() {
        var header = document.getElementById('header');
        return header ? header.getBoundingClientRect().height : 56;
    }

    function clamp(value, low, high) {
        return Math.max(low, Math.min(high, value));
    }

    function scrollPage(delta) {
        if (Math.abs(delta) < 1) return;
        window.scrollBy({ top: delta, left: 0, behavior: 'instant' });
    }

    /* ------------------------------------------------------------------ */
    /* The tour                                                              */
    /* ------------------------------------------------------------------ */

    var steps = buildSteps();
    var replayButton = null;
    var tour = null;                          // the open tour, or null

    var GAP = 16;                             // between the lit element and the card
    var EDGE = 8;                             // from the card to the screen's edge
    var NARROW = 1024;                        // below this the card is a sheet: the layout is one column

    function open(opener) {
        if (tour || !steps.length) return;
        markSeen();

        var root = el('div', 'tour');
        root.style.setProperty('--header-height', Math.round(headerHeight()) + 'px');
        root.setAttribute('data-keys', 'own');
        var spot = el('div', 'tour-spot');
        spot.setAttribute('aria-hidden', 'true');

        var card = el('section', 'tour-card');
        card.setAttribute('role', 'dialog');
        card.setAttribute('aria-modal', 'true');
        card.setAttribute('aria-labelledby', 'tour-title');
        card.setAttribute('aria-describedby', 'tour-body');
        card.tabIndex = -1;

        var content = el('div', 'tour-content');
        content.setAttribute('aria-live', 'polite');
        content.setAttribute('aria-atomic', 'true');
        var count = el('p', 'tour-count');
        var title = el('h2', 'tour-title');
        title.id = 'tour-title';
        var body = el('p', 'tour-body');
        body.id = 'tour-body';
        content.appendChild(count);
        content.appendChild(title);
        content.appendChild(body);

        var actions = el('div', 'tour-actions');
        var skip = el('button', 'btn btn-secondary tour-skip', 'Skip tour');
        var back = el('button', 'btn btn-secondary tour-back', 'Back');
        var next = el('button', 'btn btn-primary tour-next', 'Next');
        [skip, back, next].forEach(function (button) { button.type = 'button'; });
        actions.appendChild(skip);
        actions.appendChild(back);
        actions.appendChild(next);

        card.appendChild(content);
        card.appendChild(actions);
        root.appendChild(spot);
        root.appendChild(card);
        document.body.appendChild(root);

        var state = { index: 0, frame: 0, edge: 'bottom' };
        tour = { root: root };

        /* --- placing the lit element and the card ---------------------- */

        function target() { return resolve(steps[state.index].target); }

        /* Bring the target into the part of the screen the card does not cover. */
        function reveal() {
            var node = target();
            if (!node) return;
            var vh = window.innerHeight;
            var top = headerHeight() + EDGE;
            var box = node.getBoundingClientRect();

            if (window.innerWidth >= NARROW) {
                if (box.height > vh - top - EDGE) scrollPage(box.top - top);
                else if (box.top < top || box.bottom > vh - EDGE) scrollPage(box.top + box.height / 2 - (vh + top) / 2);
                return;
            }

            /* A phone. Centre the target, then put the card on the edge that is
               farther from it and move the page until the two do not overlap. */
            scrollPage(box.top + box.height / 2 - vh / 2);
            box = node.getBoundingClientRect();
            var cardHeight = card.getBoundingClientRect().height;
            state.edge = box.top + box.height / 2 > vh / 2 ? 'top' : 'bottom';
            if (state.edge === 'top') {
                var floor = top + cardHeight + GAP;
                if (box.top < floor) scrollPage(box.top - floor);
            } else {
                var ceiling = vh - EDGE - cardHeight - GAP;
                if (box.bottom > ceiling) scrollPage(Math.min(box.bottom - ceiling, box.top - top));
            }
        }

        function position() {
            var node = target();
            var vw = window.innerWidth;
            var vh = window.innerHeight;
            var narrow = vw < NARROW;
            card.removeAttribute('data-edge');
            card.style.left = '';
            card.style.top = '';

            if (!node) {
                spot.hidden = true;
                root.classList.add('is-bare');
                if (!narrow) {
                    var plain = card.getBoundingClientRect();
                    card.style.left = Math.round((vw - plain.width) / 2) + 'px';
                    card.style.top = Math.round((vh - plain.height) / 3) + 'px';
                }
                return;
            }
            spot.hidden = false;
            root.classList.remove('is-bare');

            /* The lit box: the element plus a margin, kept on screen. */
            var box = node.getBoundingClientRect();
            var left = clamp(box.left - 6, 0, vw);
            var top = clamp(box.top - 6, 0, vh);
            var right = clamp(box.right + 6, 0, vw);
            var bottom = clamp(box.bottom + 6, 0, vh);
            spot.style.left = left + 'px';
            spot.style.top = top + 'px';
            spot.style.width = Math.max(right - left, 0) + 'px';
            spot.style.height = Math.max(bottom - top, 0) + 'px';

            if (narrow) {
                card.setAttribute('data-edge', state.edge);
                return;
            }

            var size = card.getBoundingClientRect();
            var wide = (right - left) > vw * 0.55;
            var places = {
                right: { x: right + GAP, y: clamp(top, EDGE, vh - size.height - EDGE) },
                left: { x: left - GAP - size.width, y: clamp(top, EDGE, vh - size.height - EDGE) },
                bottom: { x: clamp(left, EDGE, vw - size.width - EDGE), y: bottom + GAP },
                above: { x: clamp(left, EDGE, vw - size.width - EDGE), y: top - GAP - size.height }
            };
            var order = wide ? ['bottom', 'above', 'right', 'left'] : ['right', 'left', 'bottom', 'above'];
            var chosen = null;
            order.forEach(function (name) {
                var p = places[name];
                if (!chosen && p.x >= EDGE && p.y >= EDGE &&
                    p.x + size.width <= vw - EDGE && p.y + size.height <= vh - EDGE) chosen = p;
            });
            /* Nothing fits beside it (a tall element on a short screen): the corner. */
            if (!chosen) chosen = { x: vw - size.width - GAP, y: vh - size.height - GAP };
            card.style.left = Math.round(chosen.x) + 'px';
            card.style.top = Math.round(chosen.y) + 'px';
        }

        function schedule() {
            if (state.frame) return;
            state.frame = window.requestAnimationFrame(function () {
                state.frame = 0;
                position();
            });
        }

        /* --- the step on show ------------------------------------------ */

        function show(index) {
            state.index = index;
            var step = steps[index];
            count.textContent = 'Step ' + (index + 1) + ' of ' + steps.length;
            title.textContent = step.title;
            body.textContent = step.body;
            back.disabled = index === 0;
            next.textContent = index === steps.length - 1 ? 'Done' : 'Next';
            if (document.activeElement === back && back.disabled) next.focus();
            reveal();
            position();
        }

        function close() {
            window.cancelAnimationFrame(state.frame);
            document.removeEventListener('keydown', onKey, true);
            document.removeEventListener('focusin', onFocusIn, true);
            window.removeEventListener('resize', onResize);
            window.removeEventListener('scroll', onMove, true);
            root.remove();
            tour = null;
            var returnTo = opener && document.contains(opener) && opener !== document.body ? opener : replayButton;
            if (returnTo) returnTo.focus({ preventScroll: true });
        }

        function advance() {
            if (state.index === steps.length - 1) close();
            else show(state.index + 1);
        }

        function retreat() {
            if (state.index > 0) show(state.index - 1);
        }

        /* --- keyboard and focus ---------------------------------------- */

        function onKey(event) {
            if (event.key === 'Escape') {
                event.preventDefault();
                event.stopPropagation();
                close();
            } else if (event.key === 'Tab') {
                var stops = [skip, back, next].filter(function (button) { return !button.disabled; });
                var first = stops[0];
                var last = stops[stops.length - 1];
                var active = document.activeElement;
                if (event.shiftKey && (active === first || active === card)) {
                    event.preventDefault();
                    last.focus();
                } else if (!event.shiftKey && active === last) {
                    event.preventDefault();
                    first.focus();
                } else if (stops.indexOf(active) === -1) {
                    event.preventDefault();
                    (event.shiftKey ? last : first).focus();
                }
            } else if (event.key === 'ArrowRight' && !event.altKey && !event.ctrlKey && !event.metaKey) {
                event.preventDefault();
                advance();
            } else if (event.key === 'ArrowLeft' && !event.altKey && !event.ctrlKey && !event.metaKey) {
                event.preventDefault();
                retreat();
            }
        }

        /* A click on the dimmed page, or anything else that takes focus out. */
        function onFocusIn(event) {
            if (!root.contains(event.target)) card.focus({ preventScroll: true });
        }

        function onMove() { schedule(); }
        function onResize() { reveal(); schedule(); }

        skip.addEventListener('click', close);
        back.addEventListener('click', retreat);
        next.addEventListener('click', advance);
        document.addEventListener('keydown', onKey, true);
        document.addEventListener('focusin', onFocusIn, true);
        window.addEventListener('resize', onResize);
        window.addEventListener('scroll', onMove, true);

        show(0);
        card.focus({ preventScroll: true });
        window.requestAnimationFrame(function () { root.classList.add('is-open'); });
    }

    /* "Take the tour": next to the keyboard shortcuts, at the foot of the control bar. */
    function addReplayButton() {
        var bar = document.querySelector('.control-bar');
        if (!bar || bar.querySelector('.tour-replay')) return;
        var foot = bar.querySelector('.control-bar-foot');
        if (!foot) {
            foot = el('div', 'control-bar-foot');
            var shortcuts = bar.querySelector('.shortcuts');
            if (shortcuts) foot.appendChild(shortcuts);
            bar.appendChild(foot);
        }
        replayButton = el('button', 'btn btn-secondary btn-sm tour-replay', 'Take the tour');
        replayButton.type = 'button';
        replayButton.addEventListener('click', function () { open(replayButton); });
        foot.appendChild(replayButton);
    }

    function init() {
        addReplayButton();
        var seen = readSeen();
        if (seen !== null && seen.indexOf(NAME) === -1) window.setTimeout(function () { open(null); }, 300);
    }

    if (document.readyState === 'complete') init();
    else window.addEventListener('load', init);

    window.Tour = { open: function () { open(replayButton); }, workspace: NAME };
})();
