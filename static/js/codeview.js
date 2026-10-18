/* The code view: language tabs, the listing, helpers, and the Expand dialog.
 *
 * Shared by the Learn panel on every workspace and by the Home code card, so
 * a language chosen anywhere is the language everywhere. The choice is kept
 * in localStorage under one key. Storage can be missing or throw (private
 * windows, blocked site data), so every access is wrapped and the page works
 * without it.
 *
 *   CodeView.mount({ host, lesson, expandable })  -> view
 *   view.setLesson(lesson)    new algorithm or variant, lines keep their ids
 *   view.highlight(lineId)    light every line with this id, in any language
 *   view.destroy()
 *
 *   CodeView.listing(lesson, language) -> { lines, helpers } or null
 *   CodeView.control(onPick)           -> { el, set(language) }, the tabs and
 *                                         the narrow-screen select
 *   CodeView.getLanguage(), CodeView.setLanguage(id), CodeView.onChange(fn)
 *
 * Listings come from the lesson (pseudocode, python) and from the generated
 * window.LESSON_CODE (c, cpp, java; see tools/extract_code.py). Every
 * language uses the same line ids, which is what lets a step light the same
 * line after the language changes.
 */
(function (root) {
    'use strict';

    var LANGUAGES = [
        { id: 'pseudocode', label: 'Pseudocode' },
        { id: 'python', label: 'Python' },
        { id: 'c', label: 'C' },
        { id: 'cpp', label: 'C++' },
        { id: 'java', label: 'Java' }
    ];
    var DEFAULT_LANGUAGE = 'python';
    var STORAGE_KEY = 'pbl2.codeLanguage';
    /* The half of the crossfade spent fading out; the other half fades in. */
    var FADE_MS = 60;

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function clear(node) {
        while (node.firstChild) node.removeChild(node.firstChild);
    }

    function isLanguage(id) {
        return LANGUAGES.some(function (l) { return l.id === id; });
    }

    function reducedMotion() {
        return !!(root.matchMedia &&
                  root.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }

    /* --- the saved choice -------------------------------------------------- */

    var listeners = [];
    var current = DEFAULT_LANGUAGE;

    function readStored() {
        try {
            var saved = root.localStorage.getItem(STORAGE_KEY);
            if (isLanguage(saved)) return saved;
        } catch (error) { /* storage unavailable: keep the default */ }
        return DEFAULT_LANGUAGE;
    }

    function notify() {
        listeners.slice().forEach(function (fn) { fn(current); });
    }

    function setLanguage(id) {
        if (!isLanguage(id) || id === current) return;
        current = id;
        try { root.localStorage.setItem(STORAGE_KEY, id); } catch (error) { /* ignore */ }
        notify();
    }

    function onChange(fn) {
        listeners.push(fn);
        return function () {
            var at = listeners.indexOf(fn);
            if (at !== -1) listeners.splice(at, 1);
        };
    }

    current = readStored();

    // Another tab of this site chose a language.
    if (root.addEventListener) {
        root.addEventListener('storage', function (event) {
            if (event.key !== STORAGE_KEY) return;
            var next = readStored();
            if (next === current) return;
            current = next;
            notify();
        });
    }

    /* --- listings ----------------------------------------------------------- */

    /* The listing key a lesson's variant uses in the generated files. */
    function variantKey(lesson) {
        if (lesson.variant) return lesson.variant;
        if (lesson.variants && lesson.variants.default) return lesson.variants.default;
        return 'default';
    }

    function listing(lesson, language) {
        if (!lesson) return null;
        if (language === 'pseudocode' || language === 'python') {
            var lines = lesson.code && lesson.code[language];
            return lines ? { lines: lines, helpers: [] } : null;
        }
        var all = root.LESSON_CODE && root.LESSON_CODE[lesson.id];
        var entry = all && all[language];
        if (!entry) return null;
        var key = variantKey(lesson);
        var lines2 = entry.listings[key] || entry.listings['default'] ||
            entry.listings[Object.keys(entry.listings)[0]];
        return { lines: lines2, helpers: entry.helpers || [] };
    }

    function languageLabel(id) {
        var found = LANGUAGES.filter(function (l) { return l.id === id; })[0];
        return found ? found.label : id;
    }

    /* --- the language control ------------------------------------------------ */

    var controlCount = 0;

    function control(onPick) {
        var uid = ++controlCount;
        var wrap = el('div', 'lang-control');

        var tabs = el('div', 'lang-tabs');
        tabs.setAttribute('role', 'tablist');
        tabs.setAttribute('aria-label', 'Language');
        // The selected tab's background. It moves by transform only.
        var thumb = el('span', 'lang-thumb');
        thumb.setAttribute('aria-hidden', 'true');
        tabs.appendChild(thumb);

        var buttons = {};
        LANGUAGES.forEach(function (lang) {
            var b = el('button', 'lang-tab', lang.label);
            b.type = 'button';
            b.id = 'lang-tab-' + uid + '-' + lang.id;
            b.setAttribute('role', 'tab');
            b.setAttribute('data-language', lang.id);
            b.addEventListener('click', function () { onPick(lang.id); });
            buttons[lang.id] = b;
            tabs.appendChild(b);
        });

        tabs.addEventListener('keydown', function (event) {
            var ids = LANGUAGES.map(function (l) { return l.id; });
            var at = ids.indexOf(chosen);
            var next = null;
            if (event.key === 'ArrowRight') next = ids[(at + 1) % ids.length];
            else if (event.key === 'ArrowLeft') next = ids[(at - 1 + ids.length) % ids.length];
            else if (event.key === 'Home') next = ids[0];
            else if (event.key === 'End') next = ids[ids.length - 1];
            if (!next) return;
            event.preventDefault();
            onPick(next);
            buttons[next].focus();
        });

        var select = el('select', 'lang-select');
        select.setAttribute('aria-label', 'Language');
        LANGUAGES.forEach(function (lang) {
            var o = el('option', null, lang.label);
            o.value = lang.id;
            select.appendChild(o);
        });
        select.addEventListener('change', function () { onPick(select.value); });

        wrap.appendChild(tabs);
        wrap.appendChild(select);

        var chosen = null;
        var placed = false;

        /* The thumb is a fixed 100px box scaled to the tab: translate and
           scale are the only properties that animate. */
        function place(animate) {
            var b = buttons[chosen];
            if (!b || !b.offsetWidth) return false;
            thumb.classList.toggle('is-instant', !animate || reducedMotion());
            thumb.style.transform = 'translateX(' + b.offsetLeft + 'px) scaleX(' +
                (b.offsetWidth / 100) + ')';
            thumb.style.height = b.offsetHeight + 'px';
            placed = true;
            return true;
        }

        function set(id) {
            var first = chosen === null;
            chosen = id;
            LANGUAGES.forEach(function (lang) {
                var on = lang.id === id;
                buttons[lang.id].setAttribute('aria-selected', on ? 'true' : 'false');
                buttons[lang.id].tabIndex = on ? 0 : -1;
            });
            select.value = id;
            place(!first && placed);
        }

        // The control may be built hidden (a closed dialog, a narrow screen),
        // where nothing has a width. Place the thumb when it gets one.
        if (root.ResizeObserver) {
            new root.ResizeObserver(function () { place(false); }).observe(tabs);
        } else if (root.addEventListener) {
            root.addEventListener('resize', function () { place(false); });
        }

        return {
            el: wrap,
            set: set,
            labelTabs: function (panelId) {
                LANGUAGES.forEach(function (lang) {
                    buttons[lang.id].setAttribute('aria-controls', panelId);
                });
            },
            place: function () { place(false); }
        };
    }

    /* --- the listing ---------------------------------------------------------- */

    function fillLines(ol, lines) {
        clear(ol);
        lines.forEach(function (line) {
            var item = el('li', 'code-line');
            if (line.id) item.setAttribute('data-line', line.id);
            item.style.setProperty('--indent', line.indent || 0);
            item.appendChild(el('code', null, line.text));
            ol.appendChild(item);
        });
    }

    function mark(scope, lineId) {
        Array.prototype.forEach.call(scope.querySelectorAll('.code-line'), function (line) {
            var on = !!lineId && line.getAttribute('data-line') === lineId;
            line.classList.toggle('is-current', on);
            if (on) line.setAttribute('aria-current', 'step');
            else line.removeAttribute('aria-current');
        });
    }

    /* One rendered listing plus its helpers. The main view and the dialog
       each own one. */
    function Body(options) {
        this.expanded = !!options.helpersOpen;
        this.root = el('div', 'code-body');
        this.stage = el('div', 'code-stage');
        this.list = el('ol', 'code-listing');
        this.helperHeading = el('p', 'code-helpers-heading', 'Helpers');
        this.helpers = el('ol', 'code-listing code-helpers');
        this.stage.appendChild(this.list);
        this.stage.appendChild(this.helperHeading);
        this.stage.appendChild(this.helpers);
        this.root.appendChild(this.stage);
        this.alwaysOpen = !!options.helpersOpen;
    }

    Body.prototype.fill = function (data, language, lessonName) {
        this.hasHelpers = !!(data && data.helpers && data.helpers.length);
        this.list.setAttribute('aria-label', languageLabel(language) + ' listing' +
            (lessonName ? ' for ' + lessonName : ''));
        if (!data) {
            clear(this.list);
            var item = el('li', 'code-missing',
                'No ' + languageLabel(language) + ' listing is loaded for this algorithm.');
            this.list.appendChild(item);
            this.hasHelpers = false;
        } else {
            fillLines(this.list, data.lines);
            fillLines(this.helpers, data.helpers || []);
        }
        this.showHelpers(this.expanded);
    };

    Body.prototype.showHelpers = function (open) {
        this.expanded = open;
        var visible = this.hasHelpers && (open || this.alwaysOpen);
        this.helpers.hidden = !visible;
        this.helperHeading.hidden = !visible;
    };

    /* --- the view --------------------------------------------------------------- */

    var viewCount = 0;

    function View(options) {
        var self = this;
        this.uid = ++viewCount;
        this.host = options.host;
        this.lesson = options.lesson || null;
        this.expandable = options.expandable !== false;
        this.currentLine = null;
        this.fadeTimer = null;
        this.language = current;

        this.root = el('div', 'code-view');
        this.control = control(function (id) { setLanguage(id); });
        this.root.appendChild(this.control.el);

        this.body = new Body({});
        this.body.root.id = 'code-body-' + this.uid;
        this.control.labelTabs(this.body.root.id);
        this.root.appendChild(this.body.root);

        var actions = el('div', 'code-actions');
        this.helperButton = el('button', 'code-action', 'Show helpers');
        this.helperButton.type = 'button';
        this.helperButton.setAttribute('aria-expanded', 'false');
        this.helperButton.setAttribute('aria-controls', this.body.root.id);
        this.helperButton.addEventListener('click', function () {
            self.body.showHelpers(!self.body.expanded);
            self.syncHelperButton();
        });
        actions.appendChild(this.helperButton);

        if (this.expandable) {
            this.expandButton = el('button', 'code-action', 'Expand code');
            this.expandButton.type = 'button';
            this.expandButton.setAttribute('aria-haspopup', 'dialog');
            this.expandButton.addEventListener('click', function () { self.expand(); });
            actions.appendChild(this.expandButton);
        }
        this.root.appendChild(actions);
        this.host.appendChild(this.root);

        this.unsubscribe = onChange(function () { self.languageChanged(); });
        this.control.set(this.language);
        this.render();
    }

    View.prototype.data = function () {
        return listing(this.lesson, this.language);
    };

    View.prototype.name = function () {
        return this.lesson ? this.lesson.name : '';
    };

    View.prototype.syncHelperButton = function () {
        var has = this.body.hasHelpers;
        this.helperButton.hidden = !has;
        this.helperButton.textContent = this.body.expanded ? 'Hide helpers' : 'Show helpers';
        this.helperButton.setAttribute('aria-expanded', this.body.expanded ? 'true' : 'false');
    };

    View.prototype.render = function () {
        this.body.fill(this.data(), this.language, this.name());
        this.syncHelperButton();
        mark(this.root, this.currentLine);
    };

    /* Fade the old listing out, swap, fade the new one in: about 120ms in
       all. The highlighted line is re-applied by id before it fades in, so
       it is on the same line of the new listing the moment it appears. */
    View.prototype.languageChanged = function () {
        var self = this;
        if (current === this.language) return;
        this.language = current;
        this.control.set(this.language);
        if (this.dialog) this.dialog.sync();

        window.clearTimeout(this.fadeTimer);
        var stage = this.body.stage;
        if (reducedMotion() || !this.root.offsetParent) {
            stage.classList.remove('is-swapping');
            this.render();
            this.refreshDialog();
            return;
        }
        stage.classList.add('is-swapping');
        this.fadeTimer = window.setTimeout(function () {
            self.render();
            self.refreshDialog();
            stage.classList.remove('is-swapping');
        }, FADE_MS);
    };

    View.prototype.setLesson = function (lesson) {
        this.lesson = lesson || null;
        this.body.expanded = false;
        this.render();
        this.refreshDialog();
    };

    View.prototype.highlight = function (lineId) {
        this.currentLine = lineId || null;
        mark(this.root, this.currentLine);
        if (this.dialog) this.dialog.highlight(this.currentLine);
    };

    View.prototype.refreshDialog = function () {
        if (this.dialog) this.dialog.render();
    };

    View.prototype.expand = function () {
        if (!this.dialog) this.dialog = new Dialog(this);
        this.dialog.open();
    };

    View.prototype.destroy = function () {
        window.clearTimeout(this.fadeTimer);
        if (this.unsubscribe) this.unsubscribe();
        if (this.dialog) this.dialog.destroy();
        if (this.root.parentNode) this.root.parentNode.removeChild(this.root);
    };

    /* --- the Expand dialog --------------------------------------------------------- */

    /* A native modal <dialog>: the browser traps focus inside it, closes it on
       Esc and gives focus back to the button that opened it. It carries its
       own language control, because the page behind a modal cannot be used,
       and its own highlight, which follows the run while it is open. */
    function Dialog(view) {
        var self = this;
        this.view = view;
        this.node = document.createElement('dialog');
        this.node.className = 'code-dialog';
        var titleId = 'code-dialog-title-' + view.uid;
        this.node.setAttribute('aria-labelledby', titleId);

        var head = el('div', 'code-dialog-head');
        this.title = el('h2', 'code-dialog-title');
        this.title.id = titleId;
        head.appendChild(this.title);
        var close = el('button', 'code-action', 'Close');
        close.type = 'button';
        close.addEventListener('click', function () { self.node.close(); });
        head.appendChild(close);
        this.node.appendChild(head);

        this.control = control(function (id) { setLanguage(id); });
        this.node.appendChild(this.control.el);

        // The full listing: helpers are shown, not folded away.
        this.body = new Body({ helpersOpen: true });
        this.body.root.tabIndex = 0;
        this.body.root.classList.add('code-dialog-body');
        this.node.appendChild(this.body.root);

        // A click on the backdrop is a click on the dialog element itself.
        this.node.addEventListener('click', function (event) {
            if (event.target === self.node) self.node.close();
        });
        document.body.appendChild(this.node);
    }

    Dialog.prototype.render = function () {
        var view = this.view;
        this.title.textContent = (view.name() ? view.name() + ': ' : '') +
            languageLabel(view.language);
        this.body.fill(view.data(), view.language, view.name());
        this.control.set(view.language);
        this.highlight(view.currentLine);
    };

    Dialog.prototype.sync = function () {
        this.control.set(this.view.language);
    };

    Dialog.prototype.highlight = function (lineId) {
        mark(this.node, lineId);
        if (!lineId || !this.node.open) return;
        var line = this.node.querySelector('.code-line.is-current');
        if (line && line.scrollIntoView) line.scrollIntoView({ block: 'nearest' });
    };

    Dialog.prototype.open = function () {
        this.render();
        if (!this.node.open) this.node.showModal();
        this.control.place();
        this.highlight(this.view.currentLine);
    };

    Dialog.prototype.destroy = function () {
        if (this.node.open) this.node.close();
        if (this.node.parentNode) this.node.parentNode.removeChild(this.node);
    };

    var api = {
        LANGUAGES: LANGUAGES,
        DEFAULT_LANGUAGE: DEFAULT_LANGUAGE,
        STORAGE_KEY: STORAGE_KEY,
        mount: function (options) { return new View(options); },
        listing: listing,
        control: control,
        label: languageLabel,
        getLanguage: function () { return current; },
        setLanguage: setLanguage,
        onChange: onChange
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.CodeView = api;
})(typeof window !== 'undefined' ? window : this);
