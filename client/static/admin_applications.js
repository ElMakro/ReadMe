(function() {
    // ---------- Конфигурация ----------
    const API_BASE = (window.API_BASE_URL || 'http://localhost:8080/api/v1').replace(/\/$/, '');
    const PAGE_SIZE = 10;
    let currentPage = 1;
    let isLoading = false;

    // DOM-элементы
    const container = document.getElementById('applicationsList');
    const paginationNav = document.getElementById('paginationNav');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');
    const refreshBtn = document.getElementById('refreshBtn');

    // Модальное окно
    const modalElement = document.getElementById('statusModal');
    let statusModal;
    const confirmStatusBtn = document.getElementById('confirmStatusBtn');
    const actionTextSpan = document.getElementById('actionText');
    const userFullNameSpan = document.getElementById('userFullName');
    const adminCommentTextarea = document.getElementById('adminComment');
    const currentApplicationIdInput = document.getElementById('currentApplicationId');
    const currentUserIdInput = document.getElementById('currentUserId');
    const currentNewStatusInput = document.getElementById('currentNewStatus');

    // Toast
    const toastEl = document.getElementById('liveToast');
    let toast;

    function showToast(message, type = 'success') {
        if (!toast) toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
        const toastBody = toastEl.querySelector('.toast-body');
        toastBody.innerHTML = message;
        toastEl.classList.remove('bg-success', 'bg-danger', 'bg-warning');
        if (type === 'success') toastEl.classList.add('bg-success', 'text-white');
        else if (type === 'danger') toastEl.classList.add('bg-danger', 'text-white');
        else if (type === 'warning') toastEl.classList.add('bg-warning');
        toast.show();
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        try { return new Date(dateStr).toLocaleString('ru-RU'); }
        catch(e) { return dateStr; }
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

    // Показать сообщение об ошибке доступа
    function showAccessDenied(message = 'Доступ запрещён.') {
    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <p class="text-danger">${message}</p>
            <button class="btn btn-accent" id="accessDeniedLoginBtn">Войти</button>
            <button class="btn btn-outline-accent ms-2" onclick="window.location.href='/'">На главную</button>
        </div>
    `;
    paginationNav.classList.add('d-none');
    const loginBtn = document.getElementById('accessDeniedLoginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            const headerLoginBtn = document.getElementById('loginBtn');
            if (headerLoginBtn) headerLoginBtn.click();
            else window.location.href = '/';
        });
        }
    }

    // Загрузка страницы
    async function loadPage(page) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"><span class="visually-hidden">Загрузка...</span></div></div>`;
        try {
            const url = `${API_BASE}/users/get-active-applications?page=${page}&size=${PAGE_SIZE}`;
            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });

            // Обработка 401 и 403
            if (response.status === 401) {
                showAccessDenied('Вы не авторизованы. Пожалуйста, войдите в аккаунт.');
                isLoading = false;
                return;
            }
            if (response.status === 403) {
                showAccessDenied('У вас недостаточно прав для просмотра этой страницы. Только для администраторов.');
                isLoading = false;
                return;
            }
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const applications = await response.json();
            if (!Array.isArray(applications)) throw new Error('Неверный формат ответа');
            renderApplications(applications);
            const hasMore = applications.length === PAGE_SIZE;
            updatePaginationButtons(page, hasMore);
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-danger">Не удалось загрузить заявки: ${err.message}</p><button class="btn btn-outline-accent" onclick="location.reload()">Повторить</button></div>`;
            paginationNav.classList.add('d-none');
        } finally {
            isLoading = false;
        }
    }

    function renderApplications(applications) {
        if (!applications.length) {
            container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-secondary">Нет активных заявок на преподавание.</p></div>`;
            paginationNav.classList.add('d-none');
            return;
        }
        container.innerHTML = '';
        applications.forEach(app => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-4';
            col.innerHTML = `
                <div class="card h-100" style="background: var(--bg-secondary); border-color: var(--border-color);">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}</h5>
                        <p class="card-text text-secondary small">
                            <strong>Заявка ID:</strong> ${app.application_id}<br>
                            <strong>Пользователь ID:</strong> ${app.user_id}<br>
                            <strong>Дата подачи:</strong> ${formatDate(app.created_at)}<br>
                            <strong>Статус:</strong> <span class="badge bg-warning text-dark">${app.status}</span>
                        </p>
                        <div class="d-flex gap-2 mt-3">
                            <button class="btn btn-sm btn-success approve-btn"
                                data-id="${app.application_id}"
                                data-user-id="${app.user_id}"
                                data-name="${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}">
                                Одобрить
                            </button>
                            <button class="btn btn-sm btn-danger reject-btn"
                                data-id="${app.application_id}"
                                data-user-id="${app.user_id}"
                                data-name="${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}">
                                Отклонить
                            </button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(col);
        });

        document.querySelectorAll('.approve-btn').forEach(btn => {
            btn.addEventListener('click', () => openStatusModal(btn.dataset.id, btn.dataset.userId, btn.dataset.name, 'approved'));
        });
        document.querySelectorAll('.reject-btn').forEach(btn => {
            btn.addEventListener('click', () => openStatusModal(btn.dataset.id, btn.dataset.userId, btn.dataset.name, 'rejected'));
        });
    }

    function updatePaginationButtons(page, hasNext) {
        paginationNav.classList.remove('d-none');
        pageInfoSpan.innerText = `Страница ${page}`;
        prevPageBtn.classList.toggle('disabled', page <= 1);
        nextPageBtn.classList.toggle('disabled', !hasNext);
    }

    function goPrevPage() {
        if (currentPage <= 1) return;
        currentPage--;
        loadPage(currentPage);
    }

    function goNextPage() {
        if (nextPageBtn.classList.contains('disabled')) return;
        currentPage++;
        loadPage(currentPage);
    }

    // Модальное окно изменения статуса
    let currentAppId, currentUserId, currentNewStatus, currentUserName;

    function openStatusModal(appId, userId, userName, newStatus) {
        currentAppId = appId;
        currentUserId = userId;
        currentNewStatus = newStatus;
        currentUserName = userName;

        actionTextSpan.innerText = newStatus === 'approved' ? 'одобрить' : 'отклонить';
        userFullNameSpan.innerText = userName;
        adminCommentTextarea.value = '';
        currentApplicationIdInput.value = appId;
        currentUserIdInput.value = userId;
        currentNewStatusInput.value = newStatus;

        if (!statusModal) statusModal = new bootstrap.Modal(modalElement);
        statusModal.show();
    }

    async function confirmStatusChange() {
        const comment = adminCommentTextarea.value.trim() || null;
        const payload = {
            application_id: currentAppId,
            user_id: currentUserId,
            status: currentNewStatus,
            admin_comment: comment
        };

        confirmStatusBtn.disabled = true;
        confirmStatusBtn.innerHTML = 'Отправка...';

        try {
            const response = await fetch(`${API_BASE}/users/change-application-status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload)
            });

            if (response.status === 204) {
                showToast(`Заявка успешно ${currentNewStatus === 'approved' ? 'одобрена' : 'отклонена'}.`, 'success');
                statusModal.hide();
                loadPage(currentPage);
            } else if (response.status === 401 || response.status === 403) {
                showToast('Недостаточно прав для изменения статуса.', 'danger');
                statusModal.hide();
                // обновим страницу, чтобы показать сообщение о доступе
                loadPage(currentPage);
            } else if (response.status === 409) {
                const errorData = await response.json().catch(() => ({}));
                showToast(errorData.detail || 'Данные заявки не соответствуют.', 'danger');
            } else {
                const errorData = await response.json().catch(() => ({}));
                showToast(errorData.detail || 'Ошибка при изменении статуса.', 'danger');
            }
        } catch (err) {
            console.error(err);
            showToast('Ошибка сети. Попробуйте позже.', 'danger');
        } finally {
            confirmStatusBtn.disabled = false;
            confirmStatusBtn.innerHTML = 'Подтвердить';
        }
    }

    // События
    if (prevPageBtn) prevPageBtn.addEventListener('click', (e) => { e.preventDefault(); goPrevPage(); });
    if (nextPageBtn) nextPageBtn.addEventListener('click', (e) => { e.preventDefault(); goNextPage(); });
    if (refreshBtn) refreshBtn.addEventListener('click', () => loadPage(currentPage));
    if (confirmStatusBtn) confirmStatusBtn.addEventListener('click', confirmStatusChange);

    loadPage(1);
})();