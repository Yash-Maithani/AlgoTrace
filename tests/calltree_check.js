/* Run by tests/test_phase18.py: builds the call tree for each run in the JSON
   file named on the command line and prints it, with the state of every box
   at every step, so Python can hold it to the real recursion. */
const fs = require('fs');
const path = require('path');

const CallTree = require(path.join(__dirname, '..', 'static', 'js', 'calltree.js'));
const runs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const LETTER = { pending: 'p', waiting: 'w', active: 'a', finished: 'f' };

const out = {};
runs.forEach(function (run) {
    const tree = CallTree.build(run.steps, run.array);
    if (!tree) { out[run.id] = null; return; }
    const layout = CallTree.layout(tree);
    out[run.id] = {
        nodes: tree.nodes.map(function (n) {
            return { id: n.id, depth: n.depth, lo: n.lo, hi: n.hi, leaf: n.leaf, parent: n.parent,
                     start: n.start, finish: n.finish, own: n.own, pivot: n.pivot };
        }),
        calls: tree.calls, leaves: tree.leaves, depth: tree.depth, quick: tree.quick,
        boxes: tree.nodes.map(function (n) { const b = layout.boxes[n.id]; return [b.x, b.y, b.w, b.h]; }),
        width: layout.width, height: layout.height,
        states: run.steps.map(function (s, i) {
            const st = CallTree.stateAt(tree, i);
            return {
                active: st.active, done: st.done,
                letters: st.boxes.map(function (b) { return LETTER[b.state]; }).join(''),
                results: st.boxes.map(function (b) { return b.result ? b.values : null; }),
                text: st.active === null ? null : CallTree.describe(tree, st.active)
            };
        })
    };
});
process.stdout.write(JSON.stringify(out));
