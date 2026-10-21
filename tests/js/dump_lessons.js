/* Prints every lesson as JSON, each variant already resolved the way the
   page resolves it, so the Python tests can check the figures in them
   against the code. Run by tests/unit/test_variants.py and tests/unit/test_theta_measured.py.
   A lesson with no switch appears under the single option ''. */
const fs = require('fs');
const path = require('path');

const LESSON_DIR = path.join(__dirname, '..', '..', 'algotrace', 'static', 'js', 'lessons');
const VARIANTS = require(path.join(__dirname, '..', '..', 'algotrace', 'static', 'js', 'variants.js'));

global.window = {};
fs.readdirSync(LESSON_DIR).filter(function (n) { return n.endsWith('.js'); })
    .forEach(function (name) {
        eval(fs.readFileSync(path.join(LESSON_DIR, name), 'utf8'));
    });

const out = {};
Object.keys(window.LESSONS).forEach(function (key) {
    const lesson = window.LESSONS[key];
    const ids = VARIANTS.optionIds(lesson);
    out[key] = {
        default: VARIANTS.defaultOf(lesson),
        variantKey: lesson.variants ? lesson.variants.key : null,
        resolved: {}
    };
    (ids.length ? ids : [null]).forEach(function (id) {
        out[key].resolved[id === null ? '' : id] = VARIANTS.resolve(lesson, id);
    });
});
process.stdout.write(JSON.stringify(out));
