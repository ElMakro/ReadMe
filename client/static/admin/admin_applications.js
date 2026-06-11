// static/admin/admin_applications.js
(function () {
    const PAGE_SIZE = 9;
    let isLoading = false;
    let pagination = null;
    let currentPage = 1;

    const container = document.getElementById('applicationsList');
    const refreshBtn = document.getElementById('refreshBtn');

    // Модальное окно изменения статуса
    const modalElement = document.getElementById('statusModal');
    let statusModal;
    const confirmStatusBtn = document.getElementById('confirmStatusBtn');
    const actionTextSpan = document.getElementById('actionText');
    const userFullNameSpan = document.getElementById('userFullName');
    const adminCommentTextarea = document.getElementById('adminComment');
    const currentApplicationIdInput = document.getElementById('currentApplicationId');
    const currentUserIdInput = document.getElementById('currentUserId');
    const currentNewStatusInput = document.getElementById('currentNewStatus');

    function getStatusText(status) {
        const map = {
            'pending': 'На рассмотрении',
            'approved': 'Одобрена',
            'rejected': 'Отклонена'
        };
        return map[status] || status;
    }

    function getStatusBadgeClass(status) {
        if (status === 'pending') return 'bg-warning text-dark';
        if (status === 'approved') return 'bg-success';
        if (status === 'rejected') return 'bg-danger';
        return 'bg-secondary';
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        try {
            return new Date(dateStr).toLocaleString('ru-RU');
        } catch (e) {
            return dateStr;
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>]/g, function (m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    async function loadPage(page) {
        if (isLoading) return;
        isLoading = true;
        currentPage = page;
        container.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>`;
        try {
            const url = `${window.API_BASE_URL}users/get-active-applications?page=${page}&records_per_page=${PAGE_SIZE}`;
            const response = await fetch(url, { credentials: 'include' });
            if (response.status === 401 || response.status === 403) {
                window.showAccessDenied(container, 'Вы не авторизованы или недостаточно прав.', true, pagination);
                isLoading = false;
                return;
            }
            if (!response.ok) {
                if (response.status === 404) throw new Error('Ресурс не найден.');
                if (response.status === 422) throw new Error('Ошибка валидации параметров.');
                throw new Error(`HTTP ${response.status}`);
            }
            const applications = await response.json();
            if (!Array.isArray(applications)) throw new Error('Неверный формат ответа');
            renderApplications(applications);
            const hasNext = applications.length === PAGE_SIZE;
            const total = hasNext ? page + 1 : page;
            pagination.setTotalPages(total);
            pagination.setPage(page, true);
            if (refreshBtn) refreshBtn.disabled = false;
        } catch (err) {
            console.error(err);
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <p class="text-danger">Не удалось загрузить заявки: ${err.message}</p>
                    <button class="btn btn-outline-accent" onclick="location.reload()">Повторить</button>
                </div>
            `;
            pagination.hide();
        } finally {
            isLoading = false;
        }
    }

    function renderApplications(applications) {
        if (!applications.length) {
            container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-secondary">Нет активных заявок на преподавание.</p></div>`;
            return;
        }
        container.innerHTML = '';
        applications.forEach(app => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-4';
            const statusText = getStatusText(app.status);
            const statusClass = getStatusBadgeClass(app.status);
            col.innerHTML = `
                <div class="card h-100" style="background: var(--bg-secondary); border-color: var(--border-color);">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}</h5>
                        <p class="card-text text-secondary small">
                            <strong>Дата подачи:</strong> ${formatDate(app.created_at)}<br>
                            <strong>Статус:</strong> <span class="badge ${statusClass}">${statusText}</span>
                        </p>
                        <div class="d-flex gap-2 mt-3">
                            <button class="btn btn-sm btn-success approve-btn" data-id="${app.application_id}" data-user-id="${app.user_id}" data-name="${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}">Одобрить</button>
                            <button class="btn btn-sm btn-danger reject-btn" data-id="${app.application_id}" data-user-id="${app.user_id}" data-name="${escapeHtml(app.surname)} ${escapeHtml(app.name)} ${escapeHtml(app.patronymic || '')}">Отклонить</button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(col);
        });
        document.querySelectorAll('.approve-btn').forEach(btn =>
            btn.addEventListener('click', () => openStatusModal(btn.dataset.id, btn.dataset.userId, btn.dataset.name, 'approved'))
        );
        document.querySelectorAll('.reject-btn').forEach(btn =>
            btn.addEventListener('click', () => openStatusModal(btn.dataset.id, btn.dataset.userId, btn.dataset.name, 'rejected'))
        );
    }

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
            const response = await fetch(`${window.API_BASE_URL}users/change-application-status`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify(payload)
            });
            if (response.status === 204) {
                window.showToast(`Заявка успешно ${currentNewStatus === 'approved' ? 'одобрена' : 'отклонена'}.`);
                statusModal.hide();
                loadPage(currentPage);
            } else if (response.status === 401 || response.status === 403) {
                window.showAccessDenied(container);
                statusModal.hide();
            } else if (response.status === 404) {
                window.showToast('Заявка или пользователь не найдены.', 'danger');
                statusModal.hide();
            } else if (response.status === 409) {
                window.showToast('Несоответствие идентификатора заявки и пользователя.', 'danger');
                statusModal.hide();
            } else if (response.status === 422) {
                const errorData = await response.json().catch(() => ({}));
                window.showToast(errorData.detail || 'Ошибка валидации данных.', 'danger');
                statusModal.hide();
            } else {
                const errorData = await response.json().catch(() => ({}));
                window.showToast(errorData.detail || 'Ошибка при изменении статуса.', 'danger');
            }
        } catch (err) {
            console.error(err);
            window.showToast('Ошибка сети. Попробуйте позже.', 'danger');
        } finally {
            confirmStatusBtn.disabled = false;
            confirmStatusBtn.innerHTML = 'Подтвердить';
        }
    }

    function addSecretLinkControls() {
        const manageBtn = document.getElementById('manageSecretLinkBtn');
        if (!manageBtn) return;
        manageBtn.addEventListener('click', openSecretLinkModal);
    }

    function openSecretLinkModal() {
        let modal = document.getElementById('secretLinkModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'secretLinkModal';
            modal.className = 'modal fade';
            modal.tabIndex = -1;
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content" style="background: var(--bg-secondary);">
                        <div class="modal-header">
                            <h5 class="modal-title">Управление ссылкой для подачи заявок</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Выберите действие:</label>
                                <div class="d-flex flex-column gap-2">
                                    <button id="genRandomBtn" class="btn btn-accent">Сгенерировать случайную ссылку</button>
                                    <button id="setDefaultBtn" class="btn btn-outline-accent">Использовать ссылку по умолчанию</button>
                                    <hr>
                                    <div class="input-group">
                                        <input type="text" id="customLinkInput" class="form-control" placeholder="Введите свою ссылку (латиница, цифры, _, -, .)">
                                        <button id="setCustomBtn" class="btn btn-primary">Установить свою</button>
                                    </div>
                                </div>
                            </div>
                            <div id="secretLinkResult" class="alert" style="display: none;"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        const modalObj = new bootstrap.Modal(modal);
        const resultDiv = modal.querySelector('#secretLinkResult');
        const clearResult = () => {
            resultDiv.style.display = 'none';
            resultDiv.innerHTML = '';
        };

        const setLink = async (type, content = null) => {
            const payload = {type};
            if (content !== null) payload.content = content;
            try {
                const response = await fetch(`${window.API_BASE_URL}users/set-application-link`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    const data = await response.json();
                    const fullLink = `${window.location.origin}/submit_professor_application/${data.secret_part}`;
                    resultDiv.className = 'alert alert-success mt-3';
                    resultDiv.innerHTML = `
                        <strong>Ссылка установлена:</strong><br>
                        <div class="input-group mt-2">
                            <input type="text" id="copiedLinkInput" class="form-control" value="${escapeHtml(fullLink)}" readonly>
                            <button class="btn btn-outline-secondary" id="copyLinkBtn" type="button">Копировать</button>
                        </div>
                        <small class="text-muted mt-2 d-block">Секретная часть: ${escapeHtml(data.secret_part)}</small>
                    `;
                    resultDiv.style.display = 'block';
                    const copyBtn = document.getElementById('copyLinkBtn');
                    if (copyBtn) {
                        copyBtn.addEventListener('click', async () => {
                            const input = document.getElementById('copiedLinkInput');
                            if (input) {
                                await navigator.clipboard.writeText(input.value);
                                window.showToast('Ссылка скопирована в буфер обмена');
                            }
                        });
                    }
                    window.showToast('Ссылка для подачи заявок успешно обновлена');
                } else if (response.status === 401 || response.status === 403) {
                    window.showAccessDenied(container);
                    resultDiv.className = 'alert alert-danger mt-3';
                    resultDiv.innerHTML = 'Недостаточно прав для выполнения операции.';
                    resultDiv.style.display = 'block';
                } else if (response.status === 422) {
                    const err = await response.json().catch(() => ({}));
                    resultDiv.className = 'alert alert-danger mt-3';
                    resultDiv.innerHTML = `Ошибка: ${err.detail?.[0]?.msg || 'некорректный формат ссылки'}`;
                    resultDiv.style.display = 'block';
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (err) {
                resultDiv.className = 'alert alert-danger mt-3';
                resultDiv.innerHTML = `Ошибка: ${err.message}`;
                resultDiv.style.display = 'block';
            }
        };

        const randomBtn = modal.querySelector('#genRandomBtn');
        const defaultBtn = modal.querySelector('#setDefaultBtn');
        const customBtn = modal.querySelector('#setCustomBtn');
        const customInput = modal.querySelector('#customLinkInput');

        const generateRandomSecret = () => {
            const randomBytes = new Uint8Array(32);
            crypto.getRandomValues(randomBytes);
            return btoa(String.fromCharCode(...randomBytes)).replace(/[+/=]/g, '').slice(0, 43);
        };

        randomBtn.onclick = () => {
            const randomSecret = generateRandomSecret();
            setLink('random', randomSecret);
        };
        defaultBtn.onclick = () => setLink('default');
        customBtn.onclick = () => {
            const customValue = customInput.value.trim();
            if (!customValue) {
                window.showToast('Введите непустую ссылку', 'danger');
                return;
            }
            setLink('custom', customValue);
        };

        modalObj.show();
    }

    const paginationContainer = document.getElementById('paginationContainer');
    if (paginationContainer) {
        pagination = new Pagination(paginationContainer, (page) => loadPage(page), {
            pageSize: PAGE_SIZE,
            autoHide: true
        });
    }

    if (refreshBtn) refreshBtn.addEventListener('click', () => loadPage(pagination.currentPage));
    if (confirmStatusBtn) confirmStatusBtn.addEventListener('click', confirmStatusChange);

    document.addEventListener('DOMContentLoaded', addSecretLinkControls);
    loadPage(1);
})();