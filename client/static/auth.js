// static/auth.js
(function() {
    window.AppState = window.AppState || {};
    window.AppState.currentUser = null;

    let authCheckPending = false;
    let pendingActions = [];

    async function checkAuth() {
        if (authCheckPending) return null;
        authCheckPending = true;
        try {
            const response = await fetch(`${window.API_BASE_URL}users/profile`, {
                credentials: 'include'
            });
            if (response.ok) {
                const user = await response.json();
                window.AppState.currentUser = user;
                return user;
            } else if (response.status === 401) {
                window.AppState.currentUser = null;
                return null;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('checkAuth error:', error);
            window.AppState.currentUser = null;
            return null;
        } finally {
            authCheckPending = false;
        }
    }

    async function logout() {
        try {
            await fetch(`${window.API_BASE_URL}auth/logout`, {
                method: 'GET',
                credentials: 'include'
            });
        } catch (e) {
            console.warn('Logout request failed', e);
        } finally {
            window.AppState.currentUser = null;
            window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: null } }));
            window.location.href = '/';
        }
    }

    function isAuthenticated() {
        return window.AppState.currentUser !== null;
    }

    function getUser() {
        return window.AppState.currentUser;
    }

    /**
     * Выполняет действие после успешного входа.
     * Если пользователь уже авторизован, действие выполняется немедленно.
     * Если нет – открывается модальное окно входа, и действие сохраняется в очередь.
     * @param {Function} action - асинхронная функция, которую нужно выполнить после входа.
     * @param {boolean} showModalImmediately - сразу показать модалку, если не авторизован.
     */
    function retryAfterLogin(action, showModalImmediately = true) {
        if (isAuthenticated()) {
            action();
            return;
        }
        pendingActions.push(action);
        if (showModalImmediately && window.AuthModal && typeof window.AuthModal.open === 'function') {
            window.AuthModal.open();
        }
    }

    function onAuthChanged(event) {
        const user = event.detail?.user;
        if (user && pendingActions.length) {
            const actions = [...pendingActions];
            pendingActions = [];
            actions.forEach(action => {
                try {
                    action();
                } catch (err) {
                    console.error('Error in retry action:', err);
                }
            });
        }
    }

    window.Auth = {
        check: checkAuth,
        logout: logout,
        isAuthenticated: isAuthenticated,
        getUser: getUser,
        retryAfterLogin: retryAfterLogin
    };

    window.handleUnauthorized = function(message = 'Сессия истекла. Пожалуйста, войдите снова.') {
        window.AppState.currentUser = null;
        window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: null } }));
        if (window.AuthModal && typeof window.AuthModal.open === 'function') {
            window.AuthModal.open();
            setTimeout(() => {
                const errorDiv = document.querySelector('#auth-modal-error');
                if (errorDiv) errorDiv.textContent = message;
            }, 100);
        } else {
            alert(message);
        }
    };

    window.handleForbidden = function(message = 'У вас недостаточно прав для выполнения этого действия.') {
        if (window.showToast) {
            window.showToast(message, 'danger');
        } else {
            alert(message);
        }
    };

    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(async response => {
            if (response.status === 401) {
                const url = typeof args[0] === 'string' ? args[0] : args[0].url;
                if (!url.includes('/auth/login') && !url.includes('/auth/reg') && !url.includes('/users/profile')) {
                    window.handleUnauthorized('Сессия истекла. Пожалуйста, войдите снова.');
                }
            } else if (response.status === 403) {
                const url = typeof args[0] === 'string' ? args[0] : args[0].url;
                if (!url.includes('/client_healthcheck') && !url.includes('/static/')) {
                    window.handleForbidden();
                }
            }
            return response;
        });
    };

    document.addEventListener('DOMContentLoaded', () => {
        window.Auth.check().then(user => {
            if (user) {
                window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user } }));
            }
            document.dispatchEvent(new CustomEvent('auth-loaded'));
        });
    });

    window.addEventListener('auth-changed', onAuthChanged);
})();