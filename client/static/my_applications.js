// static/my_applications.js
(function() {
    const API_BASE = (window.API_BASE_URL || 'http://localhost:8080/api/v1').replace(/\/$/, '');
    const PAGE_SIZE = 9;
    let currentPage = 1;
    let isLoading = false;

    const container = document.getElementById('applicationsList');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        try { return new Date(dateStr).toLocaleString('ru-RU'); } catch(e) { return dateStr; }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    function getStatusBadge(status) {
        const statusMap = {
            'pending': '<span class="badge bg-warning text-dark">На рассмотрении</span>',
            'approved': '<span class="badge bg-success">Одобрена</span>',
            'rejected': '<span class="badge bg-danger">Отклонена</span>'
        };
        return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    function updatePaginationButtons(page, hasNext) {
        if (prevPageBtn) prevPageBtn.disabled = (page <= 1);
        if (nextPageBtn) nextPageBtn.disabled = !hasNext;
    }

    async function loadPage(page) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>`;
        try {
            const url = `${API_BASE}/users/get-my-applications?page=${page}&size=${PAGE_SIZE}`;
            const response = await fetch(url, { credentials: 'include' });
            if (response.status === 401) {
                container.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <p class="text-danger">Вы не авторизованы. <a href="#" id="loginLink">Войдите</a>.</p>
                    </div>
                `;
                const loginLink = document.getElementById('loginLink');
                if (loginLink) {
                    loginLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        const loginBtn = document.getElementById('loginBtn');
                        if (loginBtn) loginBtn.click();
                    });
                }
                const paginationDiv = document.querySelector('.pagination');
                if (paginationDiv) paginationDiv.style.display = 'none';
                isLoading = false;
                return;
            }
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const applications = await response.json();
            if (!Array.isArray(applications)) throw new Error('Неверный формат ответа');
            renderApplications(applications);
            const hasNext = applications.length === PAGE_SIZE;
            updatePaginationButtons(page, hasNext);
            currentPage = page;
        } catch (err) {
            console.error(err);
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <p class="text-danger">Ошибка загрузки: ${err.message}</p>
                    <button class="btn btn-outline-accent" onclick="location.reload()">Повторить</button>
                </div>
            `;
            updatePaginationButtons(page, false);
        } finally {
            isLoading = false;
        }
    }

    function renderApplications(applications) {
        if (!applications.length) {
            container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-secondary">Вы ещё не подавали заявок на преподавание.</p></div>`;
            return;
        }
        container.innerHTML = '';
        applications.forEach(app => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-4';
            col.innerHTML = `
                <div class="card h-100" style="background: var(--bg-secondary); border-color: var(--border-color);">
                    <div class="card-body">
                        <h5 class="card-title">Заявка от ${formatDate(app.created_at)}</h5>
                        <p class="card-text text-secondary small">
                            <strong>ФИО:</strong> ${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}<br>
                            <strong>Статус:</strong> ${getStatusBadge(app.status)}<br>
                            ${app.admin_comment ? `<strong>Комментарий администратора:</strong> ${escapeHtml(app.admin_comment)}<br>` : ''}
                            <strong>Последнее обновление:</strong> ${formatDate(app.updated_at)}
                        </p>
                    </div>
                </div>
            `;
            container.appendChild(col);
        });
    }

    function goPrevPage() {
        if (currentPage > 1 && !isLoading) loadPage(currentPage - 1);
    }

    function goNextPage() {
        if (nextPageBtn && !nextPageBtn.disabled && !isLoading) loadPage(currentPage + 1);
    }

    if (prevPageBtn) prevPageBtn.addEventListener('click', (e) => { e.preventDefault(); goPrevPage(); });
    if (nextPageBtn) nextPageBtn.addEventListener('click', (e) => { e.preventDefault(); goNextPage(); });

    loadPage(1);
})();