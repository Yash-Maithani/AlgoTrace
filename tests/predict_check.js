/* Run by tests/test_phase16.py: builds every Predict question for each run in
   the JSON file named on the command line and prints them, so Python can
   check each one against the real steps without trusting this code. */
const fs = require('fs');
const path = require('path');

const Predict = require(path.join(__dirname, '..', 'static', 'js', 'predict.js'));
const runs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = {};
runs.forEach(function (run) {
    out[run.id] = Predict.questionsFor(run.family, run.metas);
});
process.stdout.write(JSON.stringify(out));
