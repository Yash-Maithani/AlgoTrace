// Run by tests/unit/test_presets_and_shortcuts.py. Checks the preset generators without a browser.
const assert = require('assert');
const P = require('../../algotrace/static/js/presets.js');

function sortedAsc(a) { return a.every((v, i) => i === 0 || a[i - 1] <= v); }

[5, 12, 30, 100].forEach(function (n) {
    P.ORDER.forEach(function (kind) {
        const a = P.generate(kind, n, 42);
        assert.strictEqual(a.length, n, kind + ' length');
        assert.ok(a.every(v => Number.isInteger(v) && v >= 1 && v <= 99), kind + ' range');
        // the same seed gives the same list: a run can be reproduced
        assert.deepStrictEqual(a, P.generate(kind, n, 42), kind + ' is seeded');
    });
    assert.ok(sortedAsc(P.generate('sorted', n, 7)));
    const rev = P.generate('reversed', n, 7);
    assert.ok(sortedAsc(rev.slice().reverse()));
    assert.strictEqual(new Set(P.generate('equal', n, 7)).size, 1);

    const near = P.generate('nearly', n, 7);
    const base = P.generate('sorted', n, 7);
    assert.deepStrictEqual(near.slice().sort((a, b) => a - b), base, 'nearly is a permutation of sorted');
    let off = 0;
    near.forEach((v, i) => { if (v !== base[i]) off++; });
    assert.ok(off <= 2 * Math.max(1, Math.round(n / 10)), 'nearly moves about 10 percent of pairs');
});
assert.notDeepStrictEqual(P.generate('random', 30, 1), P.generate('random', 30, 2));
console.log('ok');
