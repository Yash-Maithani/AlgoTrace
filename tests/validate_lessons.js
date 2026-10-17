/* Checks every static/js/lessons/<algorithm>.js against the contract in
   static/js/lessons/README.md. Run directly with `node tests/validate_lessons.js`,
   or through pytest, which calls it from tests/test_lessons.py.

   Prints one line per problem and exits non zero if there were any. */
const fs = require('fs');
const path = require('path');

const LESSON_DIR = path.join(__dirname, '..', 'static', 'js', 'lessons');

const FIXED_AUXILIARY =
    'Auxiliary space is the memory the algorithm needs on top of the input array itself.';
const FIXED_THIS_RUN =
    'Big O describes how work grows as the input grows and ignores constants. ' +
    'The counter shows the exact work for this one input.';

// A graph run shows its sizes and its figure, and no counted work: the
// seven do not count one shared unit, and making one up would be a
// metric the page does not measure.
const FIXED_THIS_RUN_GRAPH =
    'Big O describes how work grows as the input grows and ignores constants. ' +
    'The sizes above are this one graph; the figure is how the work would grow ' +
    'if the graph got bigger.';

// null is allowed: a figure in two variables, such as O(V times E), is
// not any single curve, and claiming one would be a different figure.
const GROWTH_KEYS = ['1', 'logn', 'n', 'nlogn', 'n2', 'n3', null];
const FAMILIES = ['sorting', 'searching', 'graph'];

global.window = {};
const problems = [];

function complain(file, message) {
    problems.push(file + ': ' + message);
}

const files = fs.readdirSync(LESSON_DIR).filter(function (name) {
    return name.endsWith('.js');
});

if (!files.length) {
    console.log('no lesson files found in ' + LESSON_DIR);
    process.exit(1);
}

files.forEach(function (name) {
    const source = fs.readFileSync(path.join(LESSON_DIR, name), 'utf8');
    try {
        eval(source);
    } catch (error) {
        complain(name, 'does not parse: ' + error.message);
    }
});

const lessons = global.window.LESSONS || {};

Object.keys(lessons).sort().forEach(function (key) {
    const lesson = lessons[key];
    const file = key + '.js';

    ['id', 'name', 'family', 'idea', 'analogy', 'whenToUse', 'code', 'complexity']
        .forEach(function (field) {
            if (!(field in lesson)) complain(file, 'missing ' + field);
        });
    if (!lesson.code || !lesson.complexity) return;

    if (lesson.id !== key) complain(file, 'id is ' + lesson.id + ' but registered as ' + key);
    if (FAMILIES.indexOf(lesson.family) === -1) complain(file, 'unknown family ' + lesson.family);
    if (!Array.isArray(lesson.idea) || lesson.idea.length !== 3) {
        complain(file, 'idea must be exactly 3 sentences');
    }

    // Both listings must offer the same set of highlightable ids, so one step
    // can light up either view.
    const pseudo = new Set(lesson.code.pseudocode.map(function (l) { return l.id; }).filter(Boolean));
    const python = new Set(lesson.code.python.map(function (l) { return l.id; }).filter(Boolean));
    pseudo.forEach(function (id) {
        if (!python.has(id)) complain(file, 'line id "' + id + '" is in pseudocode but not python');
    });
    python.forEach(function (id) {
        if (!pseudo.has(id)) complain(file, 'line id "' + id + '" is in python but not pseudocode');
    });
    lesson.code.pseudocode.concat(lesson.code.python).forEach(function (line) {
        if (typeof line.text !== 'string' || !line.text.trim()) complain(file, 'a code line has no text');
        if (typeof line.indent !== 'number') complain(file, 'a code line has no indent');
    });

    const c = lesson.complexity;
    ['best', 'average', 'worst'].forEach(function (band) {
        const entry = c.time && c.time[band];
        if (!entry || !entry.value || !entry.reason) {
            complain(file, 'complexity.time.' + band + ' needs a value and a reason');
        }
    });
    ['worked', 'space', 'auxiliaryNote', 'thisRun', 'growth',
     'growthBasis', 'growthNote'].forEach(function (field) {
        if (!(field in c)) complain(file, 'complexity is missing ' + field);
    });
    if (c.worked && typeof c.worked.comparisons !== 'number') {
        complain(file, 'complexity.worked.comparisons must be a number');
    }
    if (c.space && !c.space.what) {
        complain(file, 'complexity.space must name what the memory is');
    }
    if (GROWTH_KEYS.indexOf(c.growth) === -1) complain(file, 'growth must be one of ' + GROWTH_KEYS.join(', '));
    if (c.growth === null && !c.growthNote) {
        complain(file, 'growth is null, so growthNote must say why no curve fits');
    }
    if (c.growth !== null && c.growthNote) {
        complain(file, 'growthNote belongs only on a lesson with no curve');
    }
    if ('countLabel' in lesson && typeof lesson.countLabel !== 'string') {
        complain(file, 'countLabel must be a string');
    }
    if ('countLabel' in lesson && !c.countsNote) {
        complain(file, 'a renamed counter must be explained in complexity.countsNote');
    }
    if (c.auxiliaryNote !== FIXED_AUXILIARY) complain(file, 'auxiliaryNote must use the shared wording');
    const wanted = lesson.family === 'graph' ? FIXED_THIS_RUN_GRAPH : FIXED_THIS_RUN;
    if (c.thisRun !== wanted) {
        complain(file, 'thisRun must use the shared wording for its family');
    }
});

if (problems.length) {
    problems.forEach(function (p) { console.log(p); });
    console.log(problems.length + ' problem(s)');
    process.exit(1);
}

console.log('ok: ' + Object.keys(lessons).length + ' lesson files match the contract');
