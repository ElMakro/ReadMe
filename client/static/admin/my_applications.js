// static/my_applications.js
(function() {
    const PAGE_SIZE = 9;
    let currentPage = 1;
    let isLoading = false;
    let totalPages = 1;

    const container = document.getElementById('applicationsList');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');

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

    function updatePagination(page, total) {
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= total;
        if (pageInfoSpan) pageInfoSpan.textContent = `Страница ${page} из ${total}`;
        currentPage = page;
        totalPages = total;
    }

    async function loadPage(page) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>`;
        try {
            const url = `${window.API_BASE_URL}users/get-my-applications?page=${page}&size=${PAGE_SIZE}`;
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
            const total = hasNext ? page + 1 : page;
            updatePagination(page, total);
        } catch (err) {
            console.error(err);
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <p class="text-danger">Ошибка загрузки: ${err.message}</p>
                    <button class="btn btn-outline-accent" onclick="location.reload()">Повторить</button>
                </div>
            `;
            updatePagination(page, page);
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
        if (currentPage < totalPages && !isLoading) loadPage(currentPage + 1);
    }

    if (prevBtn) prevBtn.addEventListener('click', (e) => { e.preventDefault(); goPrevPage(); });
    if (nextBtn) nextBtn.addEventListener('click', (e) => { e.preventDefault(); goNextPage(); });

    loadPage(1);
})();