/* The call tree: the recursion of Merge Sort and Quick Sort, drawn from the
 * steps of a run.
 *
 * Every step of those two sorts carries `depth` (how many calls deep it is,
 * the first call being 0) and `range` ([lo, hi], the positions that call
 * works on). That is all this reads. Nothing about the run is recomputed, so
 * the tree cannot disagree with the stage, and a variant (merge with < or <=,
 * quick with the last, middle or a random pivot) needs no special case.
 *
 *   CallTree.build(steps, initial)  -> tree, or null for a sort with no recursion
 *   CallTree.stateAt(tree, i)       -> what the tree looks like at step i
 *   CallTree.layout(tree, options)  -> x, y, width, height of every box
 *   CallTree.mount({root})          -> the panel on the sorting page
 *
 * The tree is a pure function of the step index, so stepping back, Predict
 * mode and the keyboard shortcuts need nothing of their own: whatever step the
 * workspace shows is the step this draws.
 *
 * What is a call. A call of two or more values does work, so it has steps of
 * its own and is a node. A call of one value does nothing and has no steps; it
 * is a leaf, found as the positions of its parent that no child node covers.
 * Quick sort's pivot is not a call: it is the position its partition fixed.
 *
 * When a call starts. Merge sort calls start top down but only merge on the
 * way back up, so a call appears with the first step anywhere beneath it.
 * Quick sort partitions first and recurses after, so a call appears with its
 * own first step. A leaf appears when the step after its earlier siblings
 * finish is shown.
 */
(function (root) {
    'use strict';

    /* --- the model ------------------------------------------------------------- */

    function key(depth, lo, hi) { return depth + ':' + lo + ':' + hi; }

    function build(steps, initial) {
        if (!steps || !steps.length || steps[0].depth === undefined) return null;
        var n = steps[0].array.length;
        var last = steps.length - 1;

        var quick = steps.some(function (s) { return s.line === 'place-pivot'; });
        var byKey = {};
        var nodes = [];

        function make(depth, lo, hi, leaf) {
            var node = { id: nodes.length, depth: depth, lo: lo, hi: hi, leaf: !!leaf, parent: null,
                         children: [], own: [], start: 0, finish: 0, pivot: null };
            nodes.push(node);
            return node;
        }

        steps.forEach(function (s, i) {
            if (s.action === 'done') return;                 // the closing frame belongs to no call
            var k = key(s.depth, s.range[0], s.range[1]);
            var node = byKey[k];
            if (!node) node = byKey[k] = make(s.depth, s.range[0], s.range[1], false);
            node.own.push(i);
            if (s.line === 'place-pivot') node.pivot = s.indices[0];
        });

        // A run of one value makes one call and no steps.
        if (!nodes.length) {
            var only = make(0, 0, n - 1, true);
            only.start = 0;
            only.finish = 0;
            return finish({ n: n, nodes: nodes, root: only.id, quick: quick, last: last, steps: steps, initial: initial });
        }

        // Nesting: a call's parent is the call one level up whose range holds it.
        var real = nodes.slice();
        real.forEach(function (node) {
            if (node.depth === 0) return;
            var parent = real.filter(function (p) {
                return p.depth === node.depth - 1 && p.lo <= node.lo && node.hi <= p.hi;
            })[0];
            if (parent) { node.parent = parent.id; parent.children.push(node.id); }
        });

        // Leaves: the positions a call's children do not cover, bar the pivot.
        real.forEach(function (node) {
            var covered = {};
            node.children.forEach(function (id) {
                for (var p = nodes[id].lo; p <= nodes[id].hi; p++) covered[p] = true;
            });
            for (var p = node.lo; p <= node.hi; p++) {
                if (covered[p] || p === node.pivot) continue;
                var leaf = make(node.depth + 1, p, p, true);
                leaf.parent = node.id;
                node.children.push(leaf.id);
            }
            node.children.sort(function (a, b) { return nodes[a].lo - nodes[b].lo; });
        });

        var rootNode = real.filter(function (nd) { return nd.depth === 0; })[0];
        return finish({ n: n, nodes: nodes, root: rootNode.id, quick: quick, last: last, steps: steps, initial: initial });
    }

    /* Start and finish of every call, from where its steps fall.
       Walk the calls in the order they really ran, keeping a cursor: the index
       of the next step to be drawn. A call starts at the cursor. Quick sort
       spends its own steps first and then recurses; merge sort recurses first
       and merges after. Every step belongs to exactly one call, so the cursor
       always lands on the true index. */
    function finish(tree) {
        var nodes = tree.nodes, last = tree.last;
        var cursor = 0;

        function visit(id) {
            var node = nodes[id];
            node.start = Math.min(cursor, last);
            if (node.leaf) {
                node.finish = node.start;                    // a one value call ends as it begins
                return;
            }
            var own = node.own;
            if (tree.quick) {
                cursor = own[own.length - 1] + 1;
                node.children.forEach(visit);
                // Done when its partition and every call beneath it with steps are.
                node.finish = own[own.length - 1];
                node.children.forEach(function (c) {
                    if (!nodes[c].leaf) node.finish = Math.max(node.finish, nodes[c].finish);
                });
            } else {
                node.children.forEach(visit);
                cursor = own[own.length - 1] + 1;
                node.finish = own[own.length - 1];
            }
        }
        visit(tree.root);

        var depth = 0;
        nodes.forEach(function (nd) { depth = Math.max(depth, nd.depth); });
        tree.depth = depth;
        tree.calls = nodes.filter(function (nd) { return !nd.leaf; }).length;
        tree.leaves = nodes.length - tree.calls;
        return tree;
    }

    function slice(tree, index, lo, hi) {
        var arr = index < 0 ? (tree.initial || tree.steps[0].array) : tree.steps[index].array;
        return arr.slice(lo, hi + 1);
    }

    /* What the tree looks like at one step. */
    function stateAt(tree, i) {
        var done = tree.steps[i].action === 'done';
        var active = null;
        var boxes = tree.nodes.map(function (node) {
            var appeared = done || i >= node.start;
            var isActive = !done && node.own.indexOf(i) !== -1;
            if (isActive) active = node.id;
            // Dimmed once the step after its last has been reached. A call
            // whose last step is the one on show is still the one at work.
            var finished = appeared && !isActive && (done || i > node.finish);
            var state = !appeared ? 'pending' : isActive ? 'active' : finished ? 'finished' : 'waiting';
            // What the box shows: the values it was handed and, as soon as its
            // last step has been drawn, the same positions as that call left
            // them. Read at the call's own last step, not later: an enclosing
            // merge changes these positions again.
            var complete = !node.leaf && appeared && (done || i >= node.finish);
            var values;
            if (node.leaf) values = slice(tree, node.start - 1, node.lo, node.hi);
            else if (complete) values = slice(tree, node.finish, node.lo, node.hi);
            else values = slice(tree, node.start - 1, node.lo, node.hi);
            return { id: node.id, state: state, values: values, result: complete };
        });
        return { boxes: boxes, active: active, done: done };
    }

    /* The words for a call, for a screen reader and the live region. */
    function describe(tree, id) {
        var node = tree.nodes[id];
        var where = node.lo === node.hi ? 'position ' + node.lo : 'positions ' + node.lo + ' to ' + node.hi;
        return 'Sorting ' + where + ', depth ' + node.depth;
    }

    /* --- layout ---------------------------------------------------------------- */

    var GEOMETRY = { rowHeight: 58, boxHeight: 40, leafHeight: 28, pad: 12 };

    /* Boxes sit on rows by depth. Leaves take one slot each, left to right, and a
       call sits over the middle of its children, so the tree is as wide as the
       number of single value calls and never overlaps itself. */
    function layout(tree) {
        var nodes = tree.nodes;
        var slot = tree.n > 24 ? 44 : 64;
        var cursor = 0;
        var boxes = {};

        function place(id) {
            var node = nodes[id];
            if (node.leaf || !node.children.length) {
                boxes[id] = { x: cursor * slot + slot / 2, slots: 1 };
                cursor++;
                return;
            }
            node.children.forEach(place);
            var firstChild = boxes[node.children[0]], lastChild = boxes[node.children[node.children.length - 1]];
            boxes[id] = { x: (firstChild.x + lastChild.x) / 2, slots: 0 };
            // The slots its subtree owns, which bound how wide its box may be.
            var total = 0;
            node.children.forEach(function (c) { total += boxes[c].slots; });
            boxes[id].slots = total;
        }
        place(tree.root);

        nodes.forEach(function (node) {
            var b = boxes[node.id];
            b.y = GEOMETRY.pad + node.depth * GEOMETRY.rowHeight;
            if (node.leaf) {
                b.w = Math.min(slot - 8, 40);
                b.h = GEOMETRY.leafHeight;
            } else {
                b.w = Math.max(52, Math.min(b.slots * slot - 8, 150));
                b.h = GEOMETRY.boxHeight;
            }
            b.x -= b.w / 2;
        });
        return {
            boxes: boxes,
            width: Math.max(cursor * slot, slot),
            height: GEOMETRY.pad * 2 + (tree.depth + 1) * GEOMETRY.rowHeight - (GEOMETRY.rowHeight - GEOMETRY.boxHeight)
        };
    }

    /* Whether a list of values fits a box of this width at 10px mono. */
    function fits(values, width) {
        return values.join(' ').length * 6.3 + 10 <= width;
    }

    function label(node) {
        return node.lo === node.hi ? String(node.lo) : node.lo + '-' + node.hi;
    }

    var api = { build: build, stateAt: stateAt, layout: layout, describe: describe, fits: fits, label: label };
    if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
    root.CallTree = api;
    if (typeof document === 'undefined') return;

    /* --- the panel (browser only) -------------------------------------------------- */

    var SVG = 'http://www.w3.org/2000/svg';

    function svgEl(tag, attrs, text) {
        var node = document.createElementNS(SVG, tag);
        Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, attrs[k]); });
        if (text !== undefined) node.textContent = text;
        return node;
    }

    /* The panel under the stage. The page calls load() when a run arrives,
       show(i) for every step, clear() when the run is thrown away and
       select() when the chosen algorithm changes, and never looks inside. */
    function mount(options) {
        var rootEl = options.root;
        var toggle = rootEl.querySelector('.call-tree-toggle');
        var body = rootEl.querySelector('.call-tree-body');
        var scroller = rootEl.querySelector('.call-tree-scroll');
        var live = rootEl.querySelector('.call-tree-live');
        var empty = rootEl.querySelector('.call-tree-empty');
        var canvas = rootEl.querySelector('.call-tree-canvas');

        var wide = window.matchMedia ? window.matchMedia('(min-width: 900px)') : { matches: true };
        var open = wide.matches;                 // open on a desktop, closed on a phone
        var tree = null, geometry = null, nodeEls = [], edgeEls = [], shown = [];
        var selectedRecursive = false;
        var lastActive = null;

        function syncOpen() {
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.textContent = open ? 'Hide call tree' : 'Show call tree';
            body.hidden = !open;
        }

        function syncVisible() {
            rootEl.hidden = !(tree || selectedRecursive);
            empty.hidden = !!tree;
            scroller.hidden = !tree;
        }

        toggle.addEventListener('click', function () {
            open = !open;
            syncOpen();
        });

        function draw() {
            while (canvas.firstChild) canvas.removeChild(canvas.firstChild);
            nodeEls = []; edgeEls = []; shown = [];
            geometry = layout(tree);
            var svg = svgEl('svg', {
                'class': 'ct-svg', width: geometry.width, height: geometry.height,
                viewBox: '0 0 ' + geometry.width + ' ' + geometry.height, 'aria-hidden': 'true', focusable: 'false'
            });
            var edges = svgEl('g', { 'class': 'ct-edges' });
            var boxes = svgEl('g', { 'class': 'ct-boxes' });
            tree.nodes.forEach(function (node) {
                var b = geometry.boxes[node.id];
                if (node.parent !== null) {
                    var p = geometry.boxes[node.parent];
                    var edge = svgEl('path', {
                        'class': 'ct-edge', 'data-state': 'pending',
                        d: 'M' + (p.x + p.w / 2) + ' ' + (p.y + p.h) + ' L' + (b.x + b.w / 2) + ' ' + b.y
                    });
                    edges.appendChild(edge);
                    edgeEls[node.id] = edge;
                }
                var g = svgEl('g', { 'class': 'ct-node', 'data-state': 'pending', 'data-leaf': node.leaf ? 'true' : 'false',
                                     'data-id': node.id, transform: 'translate(' + b.x + ' ' + b.y + ')' });
                g.appendChild(svgEl('rect', { width: b.w, height: b.h, rx: 6 }));
                var name = svgEl('text', { 'class': 'ct-label', x: b.w / 2, y: node.leaf ? b.h / 2 + 4 : 15, 'text-anchor': 'middle' }, node.leaf ? '' : label(node));
                var vals = svgEl('text', { 'class': 'ct-values', x: b.w / 2, y: node.leaf ? b.h / 2 + 4 : 31, 'text-anchor': 'middle' });
                g.appendChild(name);
                g.appendChild(vals);
                boxes.appendChild(g);
                nodeEls[node.id] = { g: g, values: vals };
            });
            svg.appendChild(edges);
            svg.appendChild(boxes);
            canvas.appendChild(svg);
            scroller.setAttribute('aria-label', 'Call tree: ' + tree.calls + ' calls, ' + (tree.depth + 1) +
                ' levels deep. Scrolls inside this box.');
        }

        function keepInView(id) {
            var b = geometry.boxes[id];
            var left = scroller.scrollLeft, top = scroller.scrollTop;
            var w = scroller.clientWidth, h = scroller.clientHeight;
            var next = {};
            if (b.x < left + 8 || b.x + b.w > left + w - 8) next.left = Math.max(0, b.x + b.w / 2 - w / 2);
            if (b.y < top + 4 || b.y + b.h > top + h - 4) next.top = Math.max(0, b.y + b.h / 2 - h / 2);
            if (next.left !== undefined || next.top !== undefined) {
                // Instant: a scroll that animates under every autoplay step would never settle.
                scroller.scrollTo({ left: next.left === undefined ? left : next.left,
                                    top: next.top === undefined ? top : next.top, behavior: 'auto' });
            }
        }

        function valuesText(node, box, b) {
            if (node.leaf) return box.values.join(' ');
            return CallTree.fits(box.values, b.w) ? box.values.join(' ') : '';
        }

        return {
            load: function (payload) {
                var steps = payload && payload.steps;
                tree = build(steps, payload && payload.array);
                lastActive = null;
                if (tree) draw();
                syncVisible();
                syncOpen();
            },

            show: function (i) {
                if (!tree || !geometry) return;
                var st = stateAt(tree, i);
                st.boxes.forEach(function (box) {
                    var node = tree.nodes[box.id], el = nodeEls[box.id], b = geometry.boxes[box.id];
                    var text = box.state === 'pending' ? '' : valuesText(node, box, b);
                    if (shown[box.id] !== box.state + '|' + text + '|' + box.result) {
                        shown[box.id] = box.state + '|' + text + '|' + box.result;
                        el.g.setAttribute('data-state', box.state);
                        el.g.setAttribute('data-result', box.result ? 'true' : 'false');
                        el.values.textContent = text;
                        if (node.leaf) el.g.querySelector('.ct-values').textContent = text;
                        if (edgeEls[box.id]) edgeEls[box.id].setAttribute('data-state', box.state);
                    }
                });
                if (st.active !== null) keepInView(st.active);
                if (st.active !== lastActive) {
                    lastActive = st.active;
                    if (open) {
                        live.textContent = st.active !== null ? describe(tree, st.active)
                                         : st.done ? 'Every call has finished' : '';
                    }
                }
            },

            clear: function () {
                tree = null; geometry = null; lastActive = null;
                while (canvas.firstChild) canvas.removeChild(canvas.firstChild);
                live.textContent = '';
                syncVisible();
            },

            /* Before a run, the panel follows the algorithm picked. */
            select: function (recursive) {
                selectedRecursive = !!recursive;
                syncVisible();
            },

            get tree() { return tree; }
        };
    }

    api.mount = mount;
})(typeof window !== 'undefined' ? window : this);
