/* Menu button for the narrow header.
 *
 * The open state is aria-expanded on the button and nothing else: CSS styles
 * the panel from that attribute, so there is no class to keep in step. With
 * JavaScript off the button never appears and the links show as they always
 * did, because the collapsed rule is scoped to the button being present and
 * closed.
 *
 * No animation. The menu is opened and closed often enough that a transition
 * would only put a delay between the tap and the list.
 */
(function () {
    'use strict';

    var toggle = document.getElementById('nav-toggle');
    var links = document.getElementById('nav-links');
    if (!toggle || !links) return;

    function isOpen() {
        return toggle.getAttribute('aria-expanded') === 'true';
    }

    function setOpen(open) {
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    function close(returnFocus) {
        if (!isOpen()) return;
        setOpen(false);
        if (returnFocus) toggle.focus();
    }

    toggle.addEventListener('click', function () {
        setOpen(!isOpen());
    });

    // Escape closes from anywhere in the header and puts focus back on the
    // button, so a keyboard user is never left with focus inside a hidden list.
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen()) close(true);
    });

    // Tabbing out of the menu closes it. Checked on the next tick because at
    // focusout time the new element is not focused yet.
    links.addEventListener('focusout', function () {
        window.setTimeout(function () {
            var inside = links.contains(document.activeElement) ||
                         document.activeElement === toggle;
            if (!inside) close(false);
        }, 0);
    });

    // A click outside the header closes it.
    document.addEventListener('click', function (event) {
        if (!isOpen()) return;
        if (toggle.contains(event.target) || links.contains(event.target)) return;
        close(false);
    });

    // Following a link navigates, but an in page jump would otherwise leave
    // the menu sitting open over the thing it jumped to.
    links.addEventListener('click', function (event) {
        if (event.target.closest('a')) close(false);
    });

    // Once the viewport is wide enough that the links are on the row again,
    // the button is hidden, so leave the attribute in its closed state rather
    // than hiding a list that is now visible.
    var wide = window.matchMedia('(min-width: 1024px)');
    if (wide.addEventListener) {
        wide.addEventListener('change', function (event) {
            if (event.matches) close(false);
        });
    }
})();
