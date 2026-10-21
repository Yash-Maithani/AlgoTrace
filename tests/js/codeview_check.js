/* Run by tests/unit/test_code_panel.py. Loads the real lessons, the generated
   listings and static/js/codeview.js, and prints what the Code panel would
   show for every lesson, variant and language, so the Python tests can hold
   it to the steps the endpoints emit. */
const fs = require('fs');
const path = require('path');

const JS = path.join(__dirname, '..', '..', 'algotrace', 'static', 'js');
const VARIANTS = require(path.join(JS, 'variants.js'));

function load(storage) {
    global.window = { localStorage: storage };
    global.window.LESSONS = {};
    ['lessons', path.join('lessons', 'code')].forEach(function (dir) {
        fs.readdirSync(path.join(JS, dir)).filter(n => n.endsWith('.js')).forEach(function (n) {
            eval(fs.readFileSync(path.join(JS, dir, n), 'utf8'));
        });
    });
    delete require.cache[require.resolve(path.join(JS, 'codeview.js'))];
    const saved = global.window;
    // codeview.js takes its root from `this` when it is not in a browser.
    const api = new Function('window', 'module', fs.readFileSync(path.join(JS, 'codeview.js'), 'utf8')
        .replace('})(typeof window !== \'undefined\' ? window : this);', '})(window);') +
        '\nreturn window.CodeView;')(saved, undefined);
    return api;
}

function memory(initial) {
    const data = Object.assign({}, initial || {});
    return {
        getItem: k => (k in data ? data[k] : null),
        setItem: (k, v) => { data[k] = String(v); },
        data: data
    };
}

const mode = process.argv[2];

if (mode === 'listings') {
    const CV = load(memory());
    const out = {};
    Object.keys(window.LESSONS).forEach(function (key) {
        const lesson = window.LESSONS[key];
        const ids = VARIANTS.optionIds(lesson);
        (ids.length ? ids : [null]).forEach(function (id) {
            const resolved = VARIANTS.resolve(lesson, id);
            const name = key + '/' + (id || 'default');
            out[name] = {};
            CV.LANGUAGES.forEach(function (lang) {
                const data = CV.listing(resolved, lang.id);
                out[name][lang.id] = data && {
                    ids: Array.from(new Set(data.lines.map(l => l.id).filter(Boolean))).sort(),
                    lines: data.lines.map(l => l.text),
                    helpers: data.helpers
                };
            });
        });
    });
    process.stdout.write(JSON.stringify(out));
} else if (mode === 'storage') {
    const assert = require('assert');
    // 1. Nothing saved: Python.
    let CV = load(memory());
    assert.strictEqual(CV.getLanguage(), 'python');
    // 2. A saved language comes back.
    CV = load(memory({ 'pbl2.codeLanguage': 'java' }));
    assert.strictEqual(CV.getLanguage(), 'java');
    // 3. A saved value that is not a language is ignored.
    CV = load(memory({ 'pbl2.codeLanguage': 'cobol' }));
    assert.strictEqual(CV.getLanguage(), 'python');
    // 4. Choosing saves, and listeners hear about it once.
    const store = memory();
    CV = load(store);
    let heard = [];
    CV.onChange(l => heard.push(l));
    CV.setLanguage('cpp');
    CV.setLanguage('cpp');
    CV.setLanguage('nonsense');
    assert.deepStrictEqual(heard, ['cpp']);
    assert.strictEqual(store.data['pbl2.codeLanguage'], 'cpp');
    // 5. Storage that throws (a private window) changes nothing but the saving.
    const broken = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
    CV = load(broken);
    assert.strictEqual(CV.getLanguage(), 'python');
    CV.setLanguage('c');
    assert.strictEqual(CV.getLanguage(), 'c');
    // 6. No localStorage at all.
    CV = load(undefined);
    assert.strictEqual(CV.getLanguage(), 'python');
    console.log('ok');
}
