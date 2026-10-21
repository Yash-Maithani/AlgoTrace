/* The Home player: "One step, read three ways".
 *
 * Plays one real run of bubble sort (the steps /run_sort would send, embedded
 * by the server as #player-data) across four cards at once: the stage, the
 * Explain sentence, the Code lines and the Cost count. Nothing is invented
 * here; the page only walks the list of steps.
 *
 * Behaviour:
 *  - Starts when the section scrolls into view and pauses when it leaves,
 *    and when the tab is hidden. Pressing Pause or Step is the visitor's
 *    choice and is kept: scrolling away and back does not undo it.
 *  - Play/Pause and Step are real buttons. The Explain sentence is a polite
 *    live region, so a screen reader is told what each step does.
 *  - A swapped pair slides past each other by transform only.
 *  - Under prefers-reduced-motion nothing plays or slides: the section keeps
 *    the frozen step it was served on and the Step button still advances it.
 *
 * The Code card is static/js/home_code.js, which follows the saved language;
 * this file only tells it which line id is active.
 */
(function () {
    'use strict';

    var dataNode = document.getElementById('player-data');
    var section = document.getElementById('player');
    var stage = document.getElementById('player-stage');
    var track = document.getElementById('player-track');
    var controlsHost = document.getElementById('player-controls');
    if (!dataNode || !section || !stage || !track || !controlsHost) return;

    var data;
    try { data = JSON.parse(dataNode.textContent); } catch (error) { return; }
    var steps = data.steps || [];
    if (!steps.length) return;

    var explain = document.getElementById('player-explain');
    var why = document.getElementById('player-why');
    var count = document.getElementById('player-count');
    var swapsNode = document.getElementById('player-swaps');

    var STEP_MS = 1400;
    var HOLD_MS = 2600;           // how long the finished run is shown before it starts over
    var LIFT_MS = 170;            // the pair rises, then settles, while it crosses

    var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
    var index = reduce.matches ? data.frozen : 0;
    var timer = null;
    var userPaused = false;
    var inView = false;
    var liftTimer = null;

    /* One cell per starting position. A cell keeps its identity for the whole
       run, and a step says where each one now stands (`origins`), so a swap
       moves two cells instead of repainting two numbers. */
    var cells = data.start.map(function (value, origin) {
        var cell = document.createElement('span');
        cell.className = 'band-cell';
        cell.textContent = value;
        cell.setAttribute('data-origin', origin);
        return cell;
    });

    function build() {
        while (track.firstChild) track.removeChild(track.firstChild);
        cells.forEach(function (cell) { track.appendChild(cell); });
    }

    /* --- controls ----------------------------------------------------------- */

    function button(label, className) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'btn btn-secondary btn-sm ' + (className || '');
        b.textContent = label;
        return b;
    }

    var playButton = button('Play', 'player-play');
    var stepButton = button('Step', 'player-step');
    var status = document.createElement('span');
    status.className = 'player-status';

    controlsHost.appendChild(playButton);
    controlsHost.appendChild(stepButton);
    controlsHost.appendChild(status);

    function syncControls() {
        var playing = !!timer;
        playButton.textContent = playing ? 'Pause' : 'Play';
        playButton.setAttribute('aria-label', playing ? 'Pause the bubble sort' : 'Play the bubble sort');
        playButton.hidden = reduce.matches;
        stepButton.setAttribute('aria-label', 'Step forward one step');
        status.textContent = 'Step ' + (index + 1) + ' of ' + steps.length;
    }

    /* --- drawing one step ------------------------------------------------------ */

    function positions(step) {
        var at = {};
        step.origins.forEach(function (origin, position) { at[origin] = position; });
        return at;
    }

    function render(next, previous) {
        var step = steps[next];
        var now = positions(step);
        var before = previous === null ? null : positions(steps[previous]);
        var sorted = step.action === 'done';
        var moving = !reduce.matches && before !== null;

        window.clearTimeout(liftTimer);
        cells.forEach(function (cell, origin) {
            var position = now[origin];
            cell.style.setProperty('--pos', position);
            cell.classList.toggle('is-comparing', step.action === 'compare' && step.indices.indexOf(position) !== -1);
            cell.classList.toggle('is-swapped', step.action === 'swap' && step.indices.indexOf(position) !== -1);
            cell.classList.toggle('is-sorted', sorted);
            // The cell going right rises and the one going left dips, so the
            // pair passes instead of overlapping. Both settle again halfway.
            var lift = 0;
            if (moving && before[origin] !== position) lift = position > before[origin] ? -14 : 14;
            cell.style.setProperty('--lift', lift + 'px');
        });
        if (moving && step.action === 'swap') {
            liftTimer = window.setTimeout(function () {
                cells.forEach(function (cell) { cell.style.setProperty('--lift', '0px'); });
            }, LIFT_MS);
        }

        explain.textContent = step.explain.beginner;
        why.textContent = step.explain.why;
        count.textContent = step.comparisons;
        swapsNode.textContent = step.swaps;
        if (window.HomeCode) window.HomeCode.light(step.line);
        syncControls();
    }

    function go(next) {
        var previous = index;
        index = (next + steps.length) % steps.length;
        // Starting over is a reset, not a move: put the cells back at once
        // rather than sliding all five across the stage.
        var restart = index < previous;
        if (restart) stage.classList.add('no-motion');
        render(index, index === previous || restart ? null : previous);
        if (restart) settle();
    }

    function settle() {
        window.requestAnimationFrame(function () {
            window.requestAnimationFrame(function () { stage.classList.remove('no-motion'); });
        });
    }

    /* --- playback ---------------------------------------------------------------- */

    function schedule() {
        window.clearTimeout(timer);
        var last = index === steps.length - 1;
        timer = window.setTimeout(function () {
            if (!timer) return;
            go(index + 1);              // after the last step this wraps to the first
            schedule();
        }, last ? HOLD_MS : STEP_MS);
        syncControls();
    }

    function play() {
        if (timer || reduce.matches) return;
        schedule();
    }

    function pause() {
        if (timer) { window.clearTimeout(timer); timer = null; }
        syncControls();
    }

    playButton.addEventListener('click', function () {
        if (timer) {
            userPaused = true;
            pause();
        } else {
            userPaused = false;
            play();
        }
    });

    stepButton.addEventListener('click', function () {
        userPaused = true;
        pause();
        go(index + 1);
    });

    function sync() {
        if (inView && !userPaused && !document.hidden && !reduce.matches) play();
        else pause();
    }

    if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
            inView = entries[entries.length - 1].isIntersecting;
            sync();
        }, { threshold: 0.4 }).observe(section);
    }
    document.addEventListener('visibilitychange', sync);

    /* Changing the setting while the page is open is honoured at once. */
    function motionChanged() {
        if (reduce.matches) {
            pause();
            index = data.frozen;
            render(index, null);
        } else {
            sync();
        }
    }
    if (reduce.addEventListener) reduce.addEventListener('change', motionChanged);

    /* --- start ------------------------------------------------------------------- */

    build();
    stage.classList.add('is-live');
    // Place the cells where the first step says without sliding them there.
    stage.classList.add('no-motion');
    render(index, null);
    controlsHost.hidden = false;
    settle();
})();
