/* Checks every static/js/lessons/<algorithm>.js against the contract in
   static/js/lessons/README.md. Run directly with `node tests/validate_lessons.js`,
   or through pytest, which calls it from tests/test_lessons.py.

   Prints one line per problem and exits non zero if there were any. */
const fs = require('fs');
const path = require('path');

// LESSON_DIR can point elsewhere, so a test can prove a broken lesson fails.
const LESSON_DIR = process.env.LESSON_DIR || path.join(__dirname, '..', 'static', 'js', 'lessons');
const VARIANTS = require(path.join(__dirname, '..', 'static', 'js', 'variants.js'));

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
const GROWTH_KEYS = ['1', 'logn', 'sqrtn', 'n', 'nlogn', 'n2', 'n3', null];
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

function checkLesson(lesson, key, file) {

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

    // Sorting and searching lessons say what each input preset means for them.
    if (lesson.family === 'sorting' || lesson.family === 'searching') {
        const KINDS = ['random', 'sorted', 'reversed', 'equal', 'nearly'];
        const offered = lesson.presets || KINDS;
        offered.forEach(function (kind) {
            if (KINDS.indexOf(kind) === -1) complain(file, 'presets lists unknown preset ' + kind);
            const note = lesson.presetNotes && lesson.presetNotes[kind];
            if (typeof note !== 'string' || !note.trim()) complain(file, 'presetNotes.' + kind + ' is missing');
        });
    } else if ('presetNotes' in lesson) {
        complain(file, 'presetNotes belongs only to sorting and searching lessons');
    }

    const c = lesson.complexity;
    ['best', 'average', 'worst'].forEach(function (band) {
        const entry = c.time && c.time[band];
        if (!entry || !entry.value || !entry.reason) {
            complain(file, 'complexity.time.' + band + ' needs a value and a reason');
            return;
        }
        // Each case states its tight bound, and the O shown for the case is
        // that same bound, so the two can never disagree.
        if (BOUNDS.indexOf(entry.theta) === -1) {
            complain(file, 'complexity.time.' + band + '.theta must be one of: ' + BOUNDS.join(', '));
        } else if (entry.value !== 'O(' + entry.theta + ')') {
            complain(file, 'complexity.time.' + band + '.value is ' + entry.value +
                     ' but its theta says O(' + entry.theta + ')');
        }
    });
    checkOverall(lesson, file);
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
}

// Phase 11. The bounds a case or the overall line may state, written the
// way the rest of the lesson writes figures. `k times E` is Bellman-Ford's
// average, where k is its number of passes. Phase 19 adds jump search's
// square root and the two sorts that do not compare: counting sort's
// n plus k (k the largest key) and radix sort's d times (n plus b) (d digits,
// b buckets). Phase 20 adds Kahn's V plus E, Phase 21 A*'s V log V.
const BOUNDS = ['1', 'log n', 'square root of n', 'n', 'n log n', 'n squared',
                'V', 'E', 'V squared', 'V cubed', 'V times E', 'E log E', 'k times E',
                'n plus k', 'd times (n plus b)', 'V plus E', 'V log V'];

// Which growth curve a one variable worst case has. A bound missing here
// names two variables at once, so the lesson draws no curve for it.
const CURVE_OF = {
    '1': '1', 'log n': 'logn', 'square root of n': 'sqrtn', 'n': 'n', 'n log n': 'nlogn', 'n squared': 'n2',
    'V': 'n', 'E': 'n', 'V squared': 'n2', 'V cubed': 'n3', 'E log E': 'nlogn',
    'V log V': 'nlogn'
};

const FIXED_MISCONCEPTION =
    'Best, average and worst are cases: three kinds of input. O, Omega and Theta ' +
    'are bounds: a ceiling on the growth, a floor under it, and both at once. Every ' +
    'case has its own bounds, so reading O as the worst case, Omega as the best and ' +
    'Theta as the average mixes up two different ideas.';

function checkOverall(lesson, file) {
    const c = lesson.complexity;
    const t = c.time;
    const o = c.overall;
    if (!t || !t.best || !t.worst) return;
    if (!o || typeof o !== 'object') {
        complain(file, 'complexity.overall is missing');
        return;
    }
    ['O', 'Omega', 'Theta'].forEach(function (k) {
        if (!(k in o)) complain(file, 'complexity.overall is missing ' + k);
    });
    // Across every input, the growth is at most the worst case and at least
    // the best case. A single Theta exists only when those two agree.
    if (o.O !== t.worst.theta) {
        complain(file, 'overall.O is ' + o.O + ' but the worst case is ' + t.worst.theta);
    }
    if (o.Omega !== t.best.theta) {
        complain(file, 'overall.Omega is ' + o.Omega + ' but the best case is ' + t.best.theta);
    }
    const tight = t.best.theta === t.worst.theta ? t.best.theta : null;
    if (o.Theta !== tight) {
        complain(file, 'overall.Theta must be ' + (tight === null
            ? 'null, because the best and worst cases differ'
            : tight + ', because the best and worst cases agree'));
    }
    if (c.growth !== (CURVE_OF[t.worst.theta] || null)) {
        complain(file, 'growth is ' + c.growth + ' but the worst case ' + t.worst.theta +
                 ' has the curve ' + (CURVE_OF[t.worst.theta] || null));
    }
    if (c.misconception !== FIXED_MISCONCEPTION) {
        complain(file, 'complexity.misconception must use the shared wording');
    }
    // A graph's cases need saying which graphs they range over.
    if (lesson.family === 'graph') {
        if (typeof c.caseScope !== 'string' || !c.caseScope.trim()) {
            complain(file, 'a graph lesson says which graphs its cases range over in complexity.caseScope');
        }
    } else if ('caseScope' in c) {
        complain(file, 'caseScope belongs only to graph lessons');
    }
}

// The input shapes a claim can be measured on, and how it is compared.
const CLAIM_INPUTS = ['sorted', 'reversed', 'equal', 'random', 'nearly'];
const CLAIM_BOUNDS = ['exact', 'atMost', 'mean'];
// A formula is arithmetic in n with these helpers and nothing else, so the
// Python test can evaluate it without trusting the file.
const FORMULA = /^(?:[n0-9+\-*\/(). ]|log2|H|ceil|floor)+$/;

function textAt(lesson, where) {
    const parts = where.split('.');
    if (parts[0] === 'presetNotes') return (lesson.presetNotes || {})[parts[1]];
    if (parts[0] === 'time') {
        const entry = lesson.complexity.time[parts[1]];
        return entry && entry.reason;
    }
    return lesson.complexity[where];
}

function checkClaims(lesson, file) {
    const claims = lesson.complexity.claims;
    if (claims === undefined) return;
    if (!Array.isArray(claims) || !claims.length) {
        complain(file, 'complexity.claims must be a non empty list');
        return;
    }
    claims.forEach(function (claim, k) {
        const at = 'claims[' + k + ']';
        if (CLAIM_INPUTS.indexOf(claim.input) === -1) complain(file, at + ' has unknown input ' + claim.input);
        if ('sameAs' in claim) {
            if (CLAIM_INPUTS.indexOf(claim.sameAs) === -1) complain(file, at + ' sameAs names unknown input ' + claim.sameAs);
        } else {
            if (typeof claim.comparisons !== 'string' || !FORMULA.test(claim.comparisons)) {
                complain(file, at + ' comparisons must be a formula in n');
            }
            if (CLAIM_BOUNDS.indexOf(claim.bound) === -1) complain(file, at + ' bound must be one of ' + CLAIM_BOUNDS.join(', '));
        }
        // Every claim backs a sentence the learner reads.
        const text = typeof claim.where === 'string' ? textAt(lesson, claim.where) : null;
        if (typeof text !== 'string' || !text.trim()) {
            complain(file, at + ' where must name a text the lesson shows, got ' + claim.where);
        }
    });
}

function checkVariants(lesson, key, file) {
    const v = lesson.variants;
    if (v === undefined) return;
    if (lesson.family !== 'sorting') complain(file, 'variants belong only to sorting lessons for now');
    Object.keys(v).forEach(function (field) {
        if (['key', 'label', 'default', 'options'].indexOf(field) === -1) {
            complain(file, 'variants has an unknown field ' + field);
        }
    });
    if (typeof v.key !== 'string' || !v.key) complain(file, 'variants.key must name the switch');
    if (typeof v.label !== 'string' || !v.label) complain(file, 'variants.label is missing');
    const ids = Object.keys(v.options || {});
    if (ids.length < 2) complain(file, 'variants.options needs at least two options');
    if (ids.indexOf(v.default) === -1) complain(file, 'variants.default must be one of the options');
    if (!lesson.complexity.claims) complain(file, 'a lesson with variants must give complexity.claims');

    ids.forEach(function (id) {
        const option = v.options[id];
        const where = file + ' [' + v.key + '=' + id + ']';
        if (typeof option.label !== 'string' || !option.label.trim()) complain(where, 'option needs a label');
        if (typeof option.note !== 'string' || !option.note.trim()) complain(where, 'option needs a note');
        Object.keys(option).forEach(function (field) {
            if (field === 'label' || field === 'note') return;
            if (VARIANTS.OVERRIDABLE.indexOf(field) === -1) complain(where, 'an option cannot override ' + field);
            if (id === v.default) complain(where, 'the default option is the lesson as written, so it overrides nothing');
        });
        if (option.code && !(option.code.pseudocode && option.code.python)) {
            complain(where, 'an option that changes the code gives both listings');
        }
        const c = option.complexity || {};
        if ((c.time || c.worked) && !c.claims) {
            complain(where, 'an option that changes its complexity text gives its own claims');
        }
        // The variant, as the page will show it, must meet the whole contract.
        const resolved = VARIANTS.resolve(lesson, id);
        checkLesson(resolved, key, where);
        checkClaims(resolved, where);
    });
}

// Phase 12. The C, C++ and Java listings tools/extract_code.py writes to
// lessons/code/<algo>.js. Each language gives one listing per variant of the
// lesson ('default' when it has none), and each listing uses exactly the
// line ids of that variant's Python listing, so a step lights up the same
// line whichever language is shown.
const CODE_DIR = path.join(LESSON_DIR, 'code');
const CODE_LANGUAGES = ['c', 'cpp', 'java'];
global.window.LESSON_CODE = {};
if (fs.existsSync(CODE_DIR)) {
    fs.readdirSync(CODE_DIR).filter(function (n) { return n.endsWith('.js'); })
        .forEach(function (name) {
            try {
                eval(fs.readFileSync(path.join(CODE_DIR, name), 'utf8'));
            } catch (error) {
                complain('code/' + name, 'does not parse: ' + error.message);
            }
        });
}
const CODE = global.window.LESSON_CODE;

// The set of ids a listing uses. A language may use one id on two lines,
// as Prim pushes edges in two places, and both light up together.
function idsOf(listing) {
    return Array.from(new Set(listing.map(function (l) { return l.id; }).filter(Boolean))).sort();
}

function checkCode(lesson, key) {
    const file = 'code/' + key + '.js';
    const code = CODE[key];
    if (!code) {
        complain(file, 'is missing: run python tools/extract_code.py');
        return;
    }
    const variants = VARIANTS.optionIds(lesson);
    const wanted = variants.length ? variants : ['default'];
    CODE_LANGUAGES.forEach(function (language) {
        const entry = code[language];
        if (!entry || !entry.listings) {
            complain(file, 'has no ' + language + ' listings');
            return;
        }
        if (typeof entry.source !== 'string' || !entry.source.startsWith('reference_code/')) {
            complain(file, language + ' must name its source under reference_code/');
        }
        // Helpers sit behind "Show helpers": plain lines with no line id, so
        // turning them on never moves the highlight.
        if (!Array.isArray(entry.helpers)) {
            complain(file, language + ' must list its helpers, even if there are none');
        } else {
            entry.helpers.forEach(function (line) {
                if (typeof line.text !== 'string' || !line.text.trim()) complain(file, language + ' has a helper line with no text');
                if (typeof line.indent !== 'number' || line.indent < 0) complain(file, language + ' has a helper line with no indent');
                if (line.id !== null) complain(file, language + ' helper lines carry no line id');
            });
        }
        const have = Object.keys(entry.listings);
        if (have.join(' ') !== wanted.join(' ')) {
            complain(file, language + ' has listings for ' + have.join(', ') +
                     ' but the lesson has ' + wanted.join(', '));
        }
        wanted.forEach(function (variant) {
            const listing = entry.listings[variant] || [];
            const where = file + ' [' + language + ' ' + variant + ']';
            if (!listing.length) complain(where, 'is empty');
            listing.forEach(function (line) {
                if (typeof line.text !== 'string' || !line.text.trim()) complain(where, 'a line has no text');
                if (typeof line.indent !== 'number' || line.indent < 0) complain(where, 'a line has no indent');
                if (line.id !== null && typeof line.id !== 'string') complain(where, 'a line id must be text or null');
            });
            const python = VARIANTS.resolve(lesson, variants.length ? variant : null).code.python;
            const mine = idsOf(listing);
            const theirs = idsOf(python);
            if (mine.join(' ') !== theirs.join(' ')) {
                complain(where, 'line ids ' + mine.join(', ') + ' do not match the Python listing ' +
                         theirs.join(', '));
            }
        });
    });
}

Object.keys(CODE).forEach(function (key) {
    if (!lessons[key]) complain('code/' + key + '.js', 'has no lesson ' + key);
});

Object.keys(lessons).sort().forEach(function (key) {
    const lesson = lessons[key];
    const file = key + '.js';
    checkLesson(lesson, key, file);
    if (lesson.code) checkCode(lesson, key);
    if (!lesson.complexity) return;
    checkClaims(lesson, file);
    checkVariants(lesson, key, file);
});

if (problems.length) {
    problems.forEach(function (p) { console.log(p); });
    console.log(problems.length + ' problem(s)');
    process.exit(1);
}

console.log('ok: ' + Object.keys(lessons).length + ' lesson files match the contract');
