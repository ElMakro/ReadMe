// static/admin/my_applications.js
(function() {
    const container = document.getElementById('applicationsList');
    let pagination = null;
    let isLoading = false;
    const PAGE_SIZE = 9;

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

    async function loadPage(page) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>`;
        try {
            const url = `${window.API_BASE_URL}users/get-my-applications?page=${page}&records_per_page=${PAGE_SIZE}`;
            const response = await fetch(url, { credentials: 'include' });
            if (response.status === 401 || response.status === 403) {
                window.showAccessDenied(container, 'Вы не авторизованы или недостаточно прав.', true, pagination);
                isLoading = false;
                return;
            }
            if (!response.ok) {
                if (response.status === 422) throw new Error('Ошибка валидации параметров');
                throw new Error(`HTTP ${response.status}`);
            }
            const applications = await response.json();
            if (!Array.isArray(applications)) throw new Error('Неверный формат ответа');
            renderApplications(applications);
            const hasNext = applications.length === PAGE_SIZE;
            const total = hasNext ? page + 1 : page;
            if (pagination) {
                pagination.setTotalPages(total);
                pagination.setPage(page, true);
            }
        } catch (err) {
            console.error(err);
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <p class="text-danger">Ошибка загрузки: ${err.message}</p>
                    <button class="btn btn-outline-accent" onclick="location.reload()">Повторить</button>
                </div>
            `;
            if (pagination) pagination.hide();
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

    const paginationContainer = document.getElementById('paginationContainer');
    if (paginationContainer) {
        pagination = new Pagination(paginationContainer, (page) => loadPage(page), {
            pageSize: PAGE_SIZE,
            autoHide: true
        });
    }
    loadPage(1);
})();