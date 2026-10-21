/* The grid stage for A*: drawing the grid, editing it, and painting a run.
 *
 *   var grid = GridStage.create({ host, status, onEdit })
 *   grid.setSize(rows, cols)      rebuild, keeping what still fits
 *   grid.applyPreset(name)        'empty', 'gap', 'maze' or 'nopath'
 *   grid.state()                  {rows, cols, walls, start, goal} to post
 *   grid.showRun(steps, index)    paint the run as it stands after step index
 *   grid.clearRun()               back to the plain grid
 *
 * Editing, by pointer: press on a free cell and drag to draw walls, press on
 * a wall and drag to rub them out, press on S or G and drag to move it. By
 * keyboard, with the grid focused: the arrow keys move a cell cursor, Space
 * or Enter toggles a wall, S puts the start and G the goal under the cursor.
 * Every edit calls onEdit, because a run made on the old grid no longer
 * describes the one on screen.
 *
 * A run is painted from its steps alone (static/js/lessons/README.md and
 * algotrace/algorithms/grid/astar.py): `enqueue` and `relax` put a cell in the open set
 * with its g, h and f, `visit` expands it, `reject` is a stale entry, and
 * `done` carries the path. The cell a step is about is the current cell.
 *
 * The presets are pure functions of the size, and so is everything else
 * here that does not touch the page, so node can test them.
 */
(function (root) {
    'use strict';

    function key(r, c) { return r + ',' + c; }

    function clampCell(cell, rows, cols) {
        return [Math.max(0, Math.min(rows - 1, cell[0])), Math.max(0, Math.min(cols - 1, cell[1]))];
    }

    /* --- presets ------------------------------------------------------------- */

    var PRESETS = {
        /* Nothing in the way: the start on the left, the goal on the right. */
        empty: function (rows, cols) {
            var mid = Math.floor(rows / 2);
            return { walls: [], start: [mid, 1], goal: [mid, cols - 2] };
        },
        /* A wall down the middle with one gap at the top, so the search has
           to go round. */
        gap: function (rows, cols) {
            var mid = Math.floor(rows / 2), wallCol = Math.floor(cols / 2), walls = [];
            for (var r = 1; r < rows; r++) walls.push([r, wallCol]);
            return { walls: walls, start: [mid, Math.max(0, wallCol - 3)],
                     goal: [mid, Math.min(cols - 1, wallCol + 3)] };
        },
        /* Rows of wall with the gap at alternate ends, so the one path winds
           back and forth through every corridor. */
        maze: function (rows, cols) {
            var walls = [], lastGap = cols - 1;
            for (var r = 1; r < rows - 1; r += 2) {
                var gap = (r % 4 === 1) ? cols - 1 : 0;
                for (var c = 0; c < cols; c++) if (c !== gap) walls.push([r, c]);
                lastGap = gap;
            }
            // The goal at the far end of the last corridor from its way in.
            return { walls: walls, start: [0, 0], goal: [rows - 1, lastGap === 0 ? cols - 1 : 0] };
        },
        /* The goal boxed in by a ring of walls: no path can reach it. */
        nopath: function (rows, cols) {
            var mid = Math.floor(rows / 2), goal = [mid, cols - 3], walls = [];
            for (var dr = -1; dr <= 1; dr++) {
                for (var dc = -1; dc <= 1; dc++) {
                    var r = goal[0] + dr, c = goal[1] + dc;
                    if ((dr || dc) && r >= 0 && r < rows && c >= 0 && c < cols) walls.push([r, c]);
                }
            }
            return { walls: walls, start: [mid, 1], goal: goal };
        }
    };

    var PRESET_LABELS = { empty: 'Empty', gap: 'Wall with a gap', maze: 'Simple maze', nopath: 'No path' };

    /* What a run's steps say about every cell, after step `index`. */
    function runState(steps, index) {
        var cells = {}, current = null, path = [], outcome = null;
        for (var i = 0; i <= index && i < steps.length; i++) {
            var s = steps[i];
            var id = s.indices[0];
            current = null;
            if (s.action === 'enqueue' || s.action === 'relax') {
                cells[id] = { state: 'open', g: s.values[0], h: s.values[1], f: s.values[0] + s.values[1] };
                current = id;
            } else if (s.action === 'visit') {
                cells[id] = { state: 'closed', g: s.values[0], h: s.values[1], f: s.values[0] + s.values[1] };
                current = id;
            } else if (s.action === 'reject') {
                current = id;
            } else if (s.action === 'done') {
                path = s.line === 'path' ? s.indices.slice() : [];
                outcome = s.line === 'path' ? 'found' : 'missing';
            }
        }
        return { cells: cells, current: current, path: path, outcome: outcome };
    }

    var api = { PRESETS: PRESETS, PRESET_LABELS: PRESET_LABELS, runState: runState };
    if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }

    /* --- the stage (browser only) ---------------------------------------------- */

    function create(options) {
        var host = options.host;
        var status = options.status;
        var rows = 0, cols = 0;
        var walls = {};
        var start = [0, 0], goal = [0, 1];
        var cursor = [0, 0];
        var cells = [];          // cells[r][c] -> element
        var shown = null;        // the run state painted, or null
        var mode = null;         // pointer edit in progress

        host.setAttribute('role', 'grid');
        host.setAttribute('tabindex', '0');
        host.setAttribute('data-keys', 'own');

        function isWall(r, c) { return !!walls[key(r, c)]; }
        function same(a, b) { return a[0] === b[0] && a[1] === b[1]; }

        function kindOf(r, c) {
            if (same(start, [r, c])) return 'start';
            if (same(goal, [r, c])) return 'goal';
            return isWall(r, c) ? 'wall' : 'free';
        }

        function build() {
            host.innerHTML = '';
            cells = [];
            host.style.setProperty('--grid-cols', cols);
            host.style.setProperty('--grid-rows', rows);
            host.setAttribute('aria-rowcount', rows);
            host.setAttribute('aria-colcount', cols);
            for (var r = 0; r < rows; r++) {
                var row = document.createElement('div');
                row.className = 'grid-row';
                row.setAttribute('role', 'row');
                cells.push([]);
                for (var c = 0; c < cols; c++) {
                    var cell = document.createElement('div');
                    cell.className = 'grid-cell';
                    cell.id = 'cell-' + r + '-' + c;
                    cell.setAttribute('role', 'gridcell');
                    cell.setAttribute('data-r', r);
                    cell.setAttribute('data-c', c);
                    var mark = document.createElement('span');
                    mark.className = 'cell-mark';
                    mark.setAttribute('aria-hidden', 'true');
                    var f = document.createElement('span');
                    f.className = 'cell-f';
                    f.setAttribute('aria-hidden', 'true');
                    var gh = document.createElement('span');
                    gh.className = 'cell-gh';
                    gh.setAttribute('aria-hidden', 'true');
                    cell.appendChild(mark);
                    cell.appendChild(f);
                    cell.appendChild(gh);
                    row.appendChild(cell);
                    cells[r].push(cell);
                }
                host.appendChild(row);
            }
            fit();
            paint();
        }

        /* Cells as big as the stage allows, square, and the detail they can
           carry: g, h and f in a big cell, f alone in a middling one. */
        function fit() {
            var stage = host.parentElement;
            var width = stage ? stage.clientWidth - 24 : 600;
            var height = stage ? Math.max(stage.clientHeight - 24, 200) : 400;
            var size = Math.max(12, Math.floor(Math.min(width / cols, height / rows, 64)));
            host.style.setProperty('--cell', size + 'px');
            host.setAttribute('data-detail', size >= 46 ? 'full' : size >= 26 ? 'f' : 'none');
        }

        function describe(r, c, info, onPath, isCurrent) {
            var kind = kindOf(r, c);
            var text = 'Row ' + r + ', column ' + c + ': ' +
                ({ start: 'start', goal: 'goal', wall: 'wall', free: 'free' })[kind];
            if (info) {
                text += ', ' + (info.state === 'open' ? 'in the open set' : 'expanded') +
                    ', g ' + info.g + ', h ' + info.h + ', f ' + info.f;
            }
            if (onPath) text += ', on the path';
            if (isCurrent) text += ', current';
            return text;
        }

        function paint() {
            var onPath = {};
            if (shown) shown.path.forEach(function (id) { onPath[id] = true; });
            for (var r = 0; r < rows; r++) {
                for (var c = 0; c < cols; c++) {
                    var el = cells[r][c], id = key(r, c);
                    var info = shown ? shown.cells[id] : null;
                    var isCurrent = !!shown && shown.current === id;
                    el.setAttribute('data-kind', kindOf(r, c));
                    el.setAttribute('data-state', onPath[id] ? 'path' : (isCurrent ? 'current' : (info ? info.state : 'none')));
                    el.querySelector('.cell-mark').textContent =
                        kindOf(r, c) === 'start' ? 'S' : kindOf(r, c) === 'goal' ? 'G' : '';
                    el.querySelector('.cell-f').textContent = info ? info.f : '';
                    el.querySelector('.cell-gh').textContent = info ? info.g + ' ' + info.h : '';
                    el.setAttribute('aria-label', describe(r, c, info, onPath[id], isCurrent));
                    el.classList.toggle('is-cursor', cursor[0] === r && cursor[1] === c);
                }
            }
            host.setAttribute('aria-activedescendant', 'cell-' + cursor[0] + '-' + cursor[1]);
            host.setAttribute('aria-label', 'Grid, ' + rows + ' rows by ' + cols + ' columns. Start at row ' +
                start[0] + ', column ' + start[1] + '; goal at row ' + goal[0] + ', column ' + goal[1] +
                '; ' + Object.keys(walls).length + ' walls.');
        }

        function edited(message) {
            if (status && message) status.textContent = message;
            if (options.onEdit) options.onEdit();
        }

        function setWall(r, c, on) {
            if (kindOf(r, c) === 'start' || kindOf(r, c) === 'goal') return false;
            if (on === isWall(r, c)) return false;
            if (on) walls[key(r, c)] = true;
            else delete walls[key(r, c)];
            return true;
        }

        function place(which, r, c) {
            var other = which === 'start' ? goal : start;
            if (same(other, [r, c])) return false;
            delete walls[key(r, c)];
            if (which === 'start') start = [r, c];
            else goal = [r, c];
            return true;
        }

        /* --- pointer editing --- */

        function cellAt(event) {
            var target = document.elementFromPoint(event.clientX, event.clientY);
            var el = target && target.closest ? target.closest('.grid-cell') : null;
            if (!el || !host.contains(el)) return null;
            return [Number(el.getAttribute('data-r')), Number(el.getAttribute('data-c'))];
        }

        function applyMode(cell) {
            if (!cell) return false;
            if (mode === 'start' || mode === 'goal') return place(mode, cell[0], cell[1]);
            return setWall(cell[0], cell[1], mode === 'draw');
        }

        host.addEventListener('pointerdown', function (event) {
            var cell = cellAt(event);
            if (!cell || event.button > 0) return;
            event.preventDefault();
            host.focus({ preventScroll: true });
            cursor = cell;
            var kind = kindOf(cell[0], cell[1]);
            mode = kind === 'start' ? 'start' : kind === 'goal' ? 'goal' : kind === 'wall' ? 'erase' : 'draw';
            if (host.setPointerCapture) host.setPointerCapture(event.pointerId);
            var changed = applyMode(cell);
            paint();
            if (changed) edited();
        });

        host.addEventListener('pointermove', function (event) {
            if (!mode) return;
            if (applyMode(cellAt(event))) { paint(); edited(); }
        });

        function endPointer() { mode = null; }
        host.addEventListener('pointerup', endPointer);
        host.addEventListener('pointercancel', endPointer);

        /* --- keyboard editing --- */

        var STEP = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };

        host.addEventListener('keydown', function (event) {
            if (event.ctrlKey || event.metaKey || event.altKey) return;
            var k = event.key, r = cursor[0], c = cursor[1], said = null, changed = false;
            if (STEP[k]) {
                event.preventDefault();
                cursor = clampCell([r + STEP[k][0], c + STEP[k][1]], rows, cols);
                paint();
                if (status) status.textContent = cells[cursor[0]][cursor[1]].getAttribute('aria-label');
                return;
            }
            if (k === ' ' || k === 'Enter') {
                event.preventDefault();
                var kind = kindOf(r, c);
                if (kind === 'start' || kind === 'goal') {
                    said = 'The ' + kind + ' cannot be a wall. Move it first with ' + (kind === 'start' ? 'S' : 'G') + '.';
                } else {
                    changed = setWall(r, c, kind !== 'wall');
                    said = (kind === 'wall' ? 'Wall removed' : 'Wall added') + ' at row ' + r + ', column ' + c + '.';
                }
            } else if (k === 's' || k === 'S' || k === 'g' || k === 'G') {
                event.preventDefault();
                var which = (k === 's' || k === 'S') ? 'start' : 'goal';
                changed = place(which, r, c);
                said = changed ? 'The ' + which + ' is now at row ' + r + ', column ' + c + '.'
                               : 'The start and the goal must be different cells.';
            } else {
                return;
            }
            paint();
            if (changed) edited(said);
            else if (status) status.textContent = said;
        });

        window.addEventListener('resize', function () { if (rows) fit(); });

        return {
            setSize: function (r, c) {
                rows = r;
                cols = c;
                var kept = {};
                Object.keys(walls).forEach(function (id) {
                    var p = id.split(',').map(Number);
                    if (p[0] < rows && p[1] < cols) kept[id] = true;
                });
                walls = kept;
                start = clampCell(start, rows, cols);
                goal = clampCell(goal, rows, cols);
                if (same(start, goal)) goal = clampCell([start[0], start[1] + 1 < cols ? start[1] + 1 : start[1] - 1], rows, cols);
                delete walls[key(start[0], start[1])];
                delete walls[key(goal[0], goal[1])];
                cursor = clampCell(cursor, rows, cols);
                shown = null;
                build();
            },
            applyPreset: function (name) {
                var p = PRESETS[name](rows, cols);
                walls = {};
                p.walls.forEach(function (w) { walls[key(w[0], w[1])] = true; });
                start = p.start;
                goal = p.goal;
                delete walls[key(start[0], start[1])];
                delete walls[key(goal[0], goal[1])];
                shown = null;
                paint();
                edited(PRESET_LABELS[name] + ' grid loaded.');
            },
            state: function () {
                return {
                    rows: rows, cols: cols,
                    walls: Object.keys(walls).map(function (id) { return id.split(',').map(Number); }),
                    start: start.slice(), goal: goal.slice()
                };
            },
            showRun: function (steps, index) {
                shown = runState(steps, index);
                paint();
            },
            clearRun: function () {
                shown = null;
                paint();
            },
            fit: fit,
            edges: function () {
                var n = 0;
                for (var r = 0; r < rows; r++) {
                    for (var c = 0; c < cols; c++) {
                        if (isWall(r, c)) continue;
                        if (c + 1 < cols && !isWall(r, c + 1)) n++;
                        if (r + 1 < rows && !isWall(r + 1, c)) n++;
                    }
                }
                return n;
            }
        };
    }

    api.create = create;
    root.GridStage = api;
})(typeof window !== 'undefined' ? window : this);
