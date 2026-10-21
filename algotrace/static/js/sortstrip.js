/* The strip under the bars for the two sorts that do not compare.
 *
 * Counting Sort carries `counts` (the count list) and `cells` ([lo, hi], the
 * slots a step is about) on every step; Radix Sort carries `buckets` (ten
 * lists of values), `bucket` (the one a step is about) and `place` (1 for the
 * ones digit, 10 for the tens). This draws whichever the step has, and
 * nothing at all for a step that has neither, so it can be told about every
 * run and stays hidden for the other sorts.
 *
 *   var strip = SortStrip.create(host, stage)
 *   strip.render(step)    draw one step, or hide for a step without strip data
 *   strip.clear()         hide and empty
 *
 * The count list is drawn as a hundred square: row r, column c is slot
 * 10r + c, so the slot of 47 is row 4, column 7. Every slot is drawn,
 * empty or not, because the sort reads every one of them.
 */
(function () {
    'use strict';

    var PLACE = { 1: 'ones', 10: 'tens', 100: 'hundreds' };

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function create(host, stage) {
        var title = host.querySelector('[data-part="strip-title"]');
        var caption = host.querySelector('[data-part="strip-caption"]');
        var body = host.querySelector('[data-part="strip-body"]');
        var kind = null;
        var cells = [];
        var columns = [];

        function show(on) {
            host.hidden = !on;
            if (stage) stage.classList.toggle('has-strip', on);
        }

        function buildCounts(size) {
            kind = 'counts';
            body.innerHTML = '';
            cells = [];
            var grid = el('div', 'count-grid');
            grid.setAttribute('role', 'list');
            grid.setAttribute('aria-label', 'Count list, one slot for each value from 0 to ' + (size - 1));
            var rows = Math.ceil(size / 10);
            grid.appendChild(el('span', 'count-corner'));
            for (var c = 0; c < 10; c++) {
                var head = el('span', 'count-head', String(c));
                head.setAttribute('aria-hidden', 'true');
                grid.appendChild(head);
            }
            for (var r = 0; r < rows; r++) {
                var side = el('span', 'count-head', String(r * 10));
                side.setAttribute('aria-hidden', 'true');
                grid.appendChild(side);
                for (var k = 0; k < 10; k++) {
                    var v = r * 10 + k;
                    var cell = el('span', 'count-cell');
                    cell.setAttribute('role', 'listitem');
                    if (v >= size) {
                        cell.hidden = true;
                    }
                    var label = el('span', 'sr-only', 'count of ' + v + ': ');
                    var value = el('span', 'count-value', '0');
                    cell.appendChild(label);
                    cell.appendChild(value);
                    grid.appendChild(cell);
                    cells.push(cell);
                }
            }
            body.appendChild(grid);
        }

        function buildBuckets() {
            kind = 'buckets';
            body.innerHTML = '';
            columns = [];
            var row = el('div', 'bucket-row');
            row.setAttribute('role', 'list');
            row.setAttribute('aria-label', 'Ten buckets, 0 to 9');
            for (var d = 0; d < 10; d++) {
                var col = el('div', 'bucket');
                col.setAttribute('role', 'listitem');
                col.appendChild(el('span', 'bucket-head', String(d)));
                var list = el('span', 'bucket-values');
                col.appendChild(list);
                row.appendChild(col);
                columns.push(col);
            }
            body.appendChild(row);
        }

        function renderCounts(step) {
            var counts = step.counts;
            if (kind !== 'counts' || cells.length < counts.length) buildCounts(counts.length);
            var lo = step.cells && step.cells.length ? step.cells[0] : -1;
            var hi = step.cells && step.cells.length ? step.cells[1] : -1;
            var scanning = step.line === 'scan' || step.line === 'write';
            var finished = step.action === 'done';
            title.textContent = 'Count list';
            caption.textContent = finished
                ? 'Every slot has been read, from 0 to ' + (counts.length - 1) + '.'
                : scanning
                    ? 'Reading the slots from 0 upwards. Each value is written back as many times as its slot says.'
                    : 'One slot for each value from 0 to ' + (counts.length - 1) + '. Each value read adds one to its slot.';
            counts.forEach(function (count, v) {
                var cell = cells[v];
                cell.querySelector('.count-value').textContent = count;
                var state = count ? 'counted' : 'empty';
                if (scanning && v < lo) state = 'read';
                if (finished) state = 'read';
                if (v >= lo && v <= hi) state = 'active';
                cell.setAttribute('data-state', state);
            });
        }

        function renderBuckets(step) {
            if (kind !== 'buckets') buildBuckets();
            var place = PLACE[step.place];
            title.textContent = place ? 'Buckets, by the ' + place + ' digit' : 'Buckets';
            caption.textContent = step.action === 'done'
                ? 'Every pass is done and the buckets are empty.'
                : step.action === 'bucket'
                    ? 'Each value goes to the back of the bucket for its ' + place + ' digit.'
                    : 'The buckets are emptied from 0 to 9, each from the front.';
            step.buckets.forEach(function (values, d) {
                var col = columns[d];
                var list = col.querySelector('.bucket-values');
                list.innerHTML = '';
                values.forEach(function (v) { list.appendChild(el('span', 'bucket-chip', String(v))); });
                col.setAttribute('data-state', d === step.bucket ? 'active' : (values.length ? 'filled' : 'empty'));
                col.setAttribute('aria-label', 'Bucket ' + d + ': ' +
                    (values.length ? values.join(', ') : 'empty'));
            });
        }

        /* Keep the slot or bucket a step is about inside the strip's own
           scroll box, without moving the page. */
        function reveal(node) {
            if (!node || host.scrollHeight <= host.clientHeight) return;
            var top = node.offsetTop - host.offsetTop;
            if (top < host.scrollTop || top + node.offsetHeight > host.scrollTop + host.clientHeight) {
                host.scrollTop = Math.max(0, top - 8);
            }
        }

        function render(step) {
            if (step && Array.isArray(step.counts)) {
                renderCounts(step);
                show(true);
                if (step.cells && step.cells.length) reveal(cells[step.cells[0]]);
            } else if (step && Array.isArray(step.buckets)) {
                renderBuckets(step);
                show(true);
                if (typeof step.bucket === 'number') reveal(columns[step.bucket]);
            } else {
                show(false);
            }
        }

        function clear() {
            body.innerHTML = '';
            kind = null;
            cells = [];
            columns = [];
            show(false);
        }

        return { render: render, clear: clear };
    }

    window.SortStrip = { create: create };
})();
