/* Theme toggle.
 *
 * The <head> of each page runs a tiny inline script that resolves the theme
 * and sets data-theme on <html> before the first paint, so there is no flash
 * of the wrong colours. This file only wires up the button and keeps the
 * choice in step with the system setting.
 *
 * Nothing here needs to repaint the visualisations. Every colour the d3 code
 * writes is a var(--token) reference rather than a resolved value, so the
 * browser re-resolves it against the new data-theme by itself. A themechange
 * event is dispatched regardless, for anything that later needs to know.
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'theme';
    var root = document.documentElement;

    function stored() {
        try {
            var v = localStorage.getItem(STORAGE_KEY);
            return v === 'dark' || v === 'light' ? v : null;
        } catch (e) {
            // Private mode, blocked storage, or a browser that throws on access.
            return null;
        }
    }

    function store(theme) {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {
            // Not fatal. The toggle still works for this page view.
        }
    }

    function current() {
        return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    }

    function label(theme) {
        return theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    }

    function apply(theme, source) {
        root.setAttribute('data-theme', theme);
        root.setAttribute('data-theme-source', source);

        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.setAttribute('aria-label', label(theme));
            btn.setAttribute('title', label(theme));
            btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
        }

        document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme } }));
    }

    function init() {
        var btn = document.getElementById('theme-toggle');
        if (btn) {
            var theme = current();
            btn.setAttribute('aria-label', label(theme));
            btn.setAttribute('title', label(theme));
            btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');

            btn.addEventListener('click', function () {
                var next = current() === 'dark' ? 'light' : 'dark';
                // Suppress the cross-fade for anyone who asked for less motion.
                var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                if (!reduce) {
                    root.classList.add('theme-switching');
                    window.setTimeout(function () {
                        root.classList.remove('theme-switching');
                    }, 240);
                }
                store(next);
                apply(next, 'user');
            });
        }

        // Follow the system only while the visitor has not chosen for themselves.
        var mq = window.matchMedia('(prefers-color-scheme: dark)');
        var onSystemChange = function (e) {
            if (stored()) return;
            apply(e.matches ? 'dark' : 'light', 'system');
        };
        if (mq.addEventListener) {
            mq.addEventListener('change', onSystemChange);
        } else if (mq.addListener) {
            mq.addListener(onSystemChange);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
