// static/cookie-consent.js
(function () {
    const COOKIE_CONSENT_KEY = 'cookie_consent_accepted';
    const BANNER_HTML = `
        <div id="cookie-consent-banner" class="cookie-banner">
                Мы используем cookies для улучшения работы сайта.<br>
            <button id="cookie-consent-accept" class="btn btn-accent">Принять</button>
        </div>
    `;

    function hasConsent() {
        return localStorage.getItem(COOKIE_CONSENT_KEY) === 'true';
    }

    function setConsent() {
        localStorage.setItem(COOKIE_CONSENT_KEY, 'true');
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) banner.remove();
    }

    function init() {
        if (hasConsent()) return;
        document.body.insertAdjacentHTML('beforeend', BANNER_HTML);
        const acceptBtn = document.getElementById('cookie-consent-accept');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', setConsent);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();