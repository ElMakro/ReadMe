// static/highlight.js
(function() {
    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function highlightElement(element, query) {
        if (!element || !query) return;
        const original = element.getAttribute('data-original-text');
        if (!original) {
            element.setAttribute('data-original-text', element.textContent);
        }
        const text = element.getAttribute('data-original-text') || element.textContent;
        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        const html = text.replace(regex, '<mark class="search-highlight">$1</mark>');
        element.innerHTML = html;
    }

    function clearHighlight(container) {
        const searchables = container.querySelectorAll('[data-searchable]');
        searchables.forEach(el => {
            const original = el.getAttribute('data-original-text');
            if (original) {
                el.textContent = original;
                el.removeAttribute('data-original-text');
            }
        });
    }

    function applyHighlight(container, query) {
        if (!container || !query) return;
        const searchables = container.querySelectorAll('[data-searchable]');
        searchables.forEach(el => {
            highlightElement(el, query);
        });
    }

    window.Highlight = {
        apply: applyHighlight,
        clear: clearHighlight
    };
})();