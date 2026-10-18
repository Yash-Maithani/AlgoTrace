/* Variant switches: one lesson, read as the version the learner chose.
 *
 * A lesson with a switch carries a `variants` block (contract in
 * static/js/lessons/README.md). Its default option is the lesson exactly as
 * written; every other option lists only what it changes. resolve() lays
 * those changes over the lesson and returns a new object, so the Learn
 * panel renders a variant with the same code it renders any lesson with.
 *
 * The node validator loads this file too, so the page and the check apply a
 * variant the same way.
 */
(function (root) {
    'use strict';

    /* What an option may replace. Anything else stays the lesson's. */
    var OVERRIDABLE = ['idea', 'stable', 'presetNotes', 'code', 'complexity'];

    function assign(target) {
        for (var i = 1; i < arguments.length; i++) {
            var source = arguments[i] || {};
            Object.keys(source).forEach(function (key) { target[key] = source[key]; });
        }
        return target;
    }

    function defaultOf(lesson) {
        return lesson && lesson.variants ? lesson.variants.default : null;
    }

    function optionIds(lesson) {
        return lesson && lesson.variants ? Object.keys(lesson.variants.options) : [];
    }

    function resolve(lesson, id) {
        if (!lesson || !lesson.variants) return lesson;
        var chosen = id && lesson.variants.options[id] ? id : lesson.variants.default;
        var option = lesson.variants.options[chosen] || {};
        var out = assign({}, lesson);

        if ('idea' in option) out.idea = option.idea;
        if ('stable' in option) out.stable = option.stable;
        if (option.presetNotes) out.presetNotes = assign({}, lesson.presetNotes, option.presetNotes);
        // A listing is replaced whole, never spliced, so its line ids stay
        // the ones the variant's steps actually emit.
        if (option.code) out.code = assign({}, lesson.code, option.code);
        if (option.complexity) {
            out.complexity = assign({}, lesson.complexity, option.complexity);
            out.complexity.time = assign({}, lesson.complexity.time,
                                         option.complexity.time);
        }

        out.variant = chosen;
        out.variantLabel = option.label;
        out.variantNote = option.note;
        return out;
    }

    var api = { resolve: resolve, defaultOf: defaultOf, optionIds: optionIds,
                OVERRIDABLE: OVERRIDABLE };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.Variants = api;
})(typeof window !== 'undefined' ? window : this);
