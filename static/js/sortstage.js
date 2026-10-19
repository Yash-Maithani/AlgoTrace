/* The sorting stage: one row of bars, painted from a step.
 *
 * Shared by /sorting and by both sides of /compare, so the bars look and
 * move the same wherever they appear. This is the code the sorting page has
 * always run, moved here unchanged: the same height formula, the same state
 * classes, the same letter tags for equal values.
 *
 *   var stage = SortStage.create(container, emptyMessage)
 *   stage.render(step, payload)    draw one step
 *   stage.clear()                  blank the stage, show the empty message
 *
 * Which bar class each action paints, read from the step itself:
 *   compare            -> comparing
 *   swap, place        -> swapping
 *   select             -> pivot
 *   count, bucket      -> pivot (a value read into the count list or a bucket)
 *   overwrite          -> swapping when a pair moved, else pivot
 *   done               -> every bar sorted
 */
(function () {
    'use strict';

    function classFor(step) {
        switch (step.action) {
            case 'compare': return 'comparing';
            case 'swap':
            case 'place': return 'swapping';
            case 'select':
            case 'count':
            case 'bucket': return 'pivot';
            case 'overwrite':
                return (step.compared || []).length >= 2 ? 'swapping' : 'pivot';
            default: return null;
        }
    }

    /* Letter tags for equal values: the first 5 in the input is 5a, the next
       5b, and so on, so a learner can see whether a sort kept equal values in
       their starting order. A value that occurs once gets no tag. Indexed by
       starting position. */
    function letters(k) {
        var out = '';
        k += 1;
        while (k > 0) {
            k -= 1;
            out = String.fromCharCode(97 + (k % 26)) + out;
            k = Math.floor(k / 26);
        }
        return out;
    }

    function tagsFor(input) {
        var count = {}, seen = {}, tags = [];
        input.forEach(function (v) { count[v] = (count[v] || 0) + 1; });
        input.forEach(function (v, origin) {
            if (count[v] < 2) { tags[origin] = ''; return; }
            seen[v] = seen[v] || 0;
            tags[origin] = letters(seen[v]);
            seen[v] += 1;
        });
        return tags;
    }

    function create(container, empty) {
        var tags = [];
        var lastTagged = null;

        function render(step, payload) {
            var data = step.array;
            payload = payload || {};
            if (payload !== lastTagged) {
                lastTagged = payload;
                tags = tagsFor(payload.array || data);
            }
            var origins = step.origins || [];

            if (container.childElementCount !== data.length) {
                container.innerHTML = '';
                data.forEach(function (value) {
                    var bar = document.createElement('div');
                    bar.className = 'bar';
                    var label = document.createElement('span');
                    label.className = 'bar-value';
                    label.textContent = value;
                    bar.appendChild(label);
                    container.appendChild(bar);
                });
            }

            var painted = classFor(step);
            var marked = step.compared || [];
            var finished = step.action === 'done';

            Array.prototype.forEach.call(container.children, function (bar, i) {
                // Same height formula and the same transition as before.
                bar.style.height = Math.max(data[i] * 3, 5) + 'px';
                bar.classList.remove('comparing', 'swapping', 'pivot', 'sorted');
                if (finished) {
                    bar.classList.add('sorted');
                } else if (painted && marked.indexOf(i) !== -1) {
                    bar.classList.add(painted);
                }
                var tag = tags[origins[i]] || '';
                var label = bar.querySelector('.bar-value');
                label.textContent = data[i];
                if (tag) {
                    var mark = document.createElement('span');
                    mark.className = 'bar-tag';
                    mark.textContent = tag;
                    label.appendChild(mark);
                }
            });

            /* Narrow screens hide the bar values, because at 30 bars they
               overlap. At this many they fit, and the Explain text refers to
               them by value. */
            container.classList.toggle('shows-values', data.length <= 12);

            if (empty) empty.hidden = true;
            container.hidden = false;
        }

        function clear() {
            container.innerHTML = '';
            container.hidden = true;
            if (empty) empty.hidden = false;
            lastTagged = null;
        }

        return { render: render, clear: clear };
    }

    window.SortStage = { create: create, classFor: classFor, tagsFor: tagsFor };
})();
