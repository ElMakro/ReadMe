// static/access-denied.js
(function() {
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Отображает сообщение об отказе в доступе и предлагает войти или вернуться на главную.
     * @param {HTMLElement} container - DOM-элемент, содержимое которого будет заменено.
     * @param {string} message - Текст сообщения.
     * @param {boolean} showLoginLink - Показывать ли кнопку "Войти".
     * @param {boolean} hidePagination - Скрывать ли пагинацию (по умолчанию true).
     */
    window.showAccessDenied = function(container, message = 'Доступ запрещён.', showLoginLink = true, hidePagination = true) {
        if (!container) return;

        if (hidePagination) {
            const paginationDiv = document.querySelector('.pagination');
            if (paginationDiv) paginationDiv.style.display = 'none';
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn) refreshBtn.disabled = true;
            const prevPageBtn = document.getElementById('prevPageBtn');
            if (prevPageBtn) prevPageBtn.disabled = true;
            const nextPageBtn = document.getElementById('nextPageBtn');
            if (nextPageBtn) nextPageBtn.disabled = true;
        }

        container.innerHTML = `
            <div class="text-center py-5">
                <p class="text-danger">${escapeHtml(message)}</p>
                ${showLoginLink ? '<button class="btn btn-accent" id="accessDeniedLoginBtn">Войти</button>' : ''}
                <button class="btn btn-outline-accent ms-2" onclick="window.location.href='/'">На главную</button>
            </div>
        `;

        if (showLoginLink) {
            const loginBtn = document.getElementById('accessDeniedLoginBtn');
            if (loginBtn) {
                loginBtn.addEventListener('click', () => {
                    if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                        window.AuthModal.open();
                    } else {
                        window.location.href = '/';
                    }
                });
            }
        }
    };
})();