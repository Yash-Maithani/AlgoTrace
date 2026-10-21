// Run by tests/unit/test_theta_measured.py. Loads the real static/js/workspace.js against
// a small stand-in DOM and checks that choosing another algorithm throws the
// loaded run away: steps, stage, banner, counter and Learn panel.
const assert = require('assert');
const fs = require('fs');
const path = require('path');

function element(id) {
    return {
        id: id, disabled: false, textContent: '', hidden: false, attrs: {},
        listeners: {},
        setAttribute: function (k, v) { this.attrs[k] = String(v); },
        getAttribute: function (k) { return k in this.attrs ? this.attrs[k] : null; },
        removeAttribute: function (k) { delete this.attrs[k]; },
        addEventListener: function (type, fn) { this.listeners[type] = fn; },
        querySelector: function () { return null; },
        querySelectorAll: function () { return []; },
        appendChild: function () {}
    };
}

const byId = {};
['run-button', 'play-pause', 'step-back', 'step-forward', 'reset', 'speed',
 'step-counter', 'run-banner', 'learn-panel'].forEach(function (id) { byId[id] = element(id); });
byId.speed.value = '5';

const picks = ['Bubble Sort', 'Merge Sort'].map(function (name) {
    const b = element(null);
    b.attrs['data-algorithm'] = name;
    b.attrs['aria-current'] = name === 'Bubble Sort' ? 'true' : 'false';
    return b;
});
const picker = element('algo-picker');
picker.querySelectorAll = function () { return picks; };
picker.querySelector = function (sel) {
    return sel.indexOf('aria-current') !== -1 ? picks[0] : picks[0];
};
byId['algo-picker'] = picker;

global.document = {
    getElementById: function (id) { return byId[id] || null; },
    querySelector: function () { return null; },
    querySelectorAll: function () { return []; },
    addEventListener: function () {},
    createElement: function () { return element(null); }
};

const panelCalls = [];
global.window = {
    setInterval: setInterval, clearInterval: clearInterval,
    Teacher: {
        mount: function () {
            return {
                setLesson: function (l) { panelCalls.push('setLesson:' + (l && l.id)); },
                clearStep: function () { panelCalls.push('clearStep'); },
                showStep: function () { panelCalls.push('showStep'); }
            };
        }
    }
};

let pendingFetch = null;
global.fetch = function () {
    return new Promise(function (resolve) { pendingFetch = resolve; });
};

eval(fs.readFileSync(path.join(__dirname, '..', '..', 'algotrace', 'static', 'js', 'workspace.js'), 'utf8'));

const calls = [];
const ws = window.Workspace.start({
    endpoint: '/run_sort',
    lessons: { 'Bubble Sort': { id: 'bubble_sort' }, 'Merge Sort': { id: 'merge_sort' } },
    readRequest: function (ui) { return { algorithm: ui.algorithm }; },
    renderStep: function (step, ctx) { calls.push('render'); ctx.stats({ n: 3 }); },
    renderResult: function () { calls.push('result'); },
    clearResult: function () { calls.push('clearResult'); },
    clearStage: function () { calls.push('clearStage'); }
});

const run = { algorithm: 'Bubble Sort', steps: [{ action: 'compare' }, { action: 'done' }] };
ws.load(run);
ws.go(1);
assert.strictEqual(byId['step-counter'].textContent, 'Step 2 of 2');
assert.ok(calls.indexOf('result') !== -1, 'the banner showed on the last step');

calls.length = 0;
panelCalls.length = 0;
ws.selectAlgorithm('Merge Sort');

assert.strictEqual(ws.payload, null, 'the run is gone');
assert.deepStrictEqual(ws.steps, [], 'its steps are gone');
assert.ok(calls.indexOf('clearStage') !== -1, 'the stage was cleared');
assert.ok(calls.indexOf('clearResult') !== -1, 'the banner was cleared');
assert.strictEqual(byId['step-counter'].textContent, 'Step 0 of 0');
assert.ok(byId['play-pause'].disabled && byId['step-forward'].disabled, 'the transport is off');
assert.deepStrictEqual(panelCalls, ['clearStep', 'setLesson:merge_sort'],
    'the Learn panel forgot the run, then took the new lesson');

// Picking the algorithm already chosen changes nothing.
ws.load(Object.assign({}, run, { algorithm: 'Merge Sort' }));
ws.selectAlgorithm('Merge Sort');
assert.ok(ws.payload, 'reselecting the same algorithm keeps the run');

// A reply that lands after a switch is for a page no longer showing.
ws.discard();
ws.run();
ws.selectAlgorithm('Bubble Sort');
pendingFetch({ ok: true, json: function () { return Promise.resolve(run); } });
setTimeout(function () {
    assert.strictEqual(ws.payload, null, 'a late reply did not load');
    console.log('ok');
}, 20);
