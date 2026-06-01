(function() {
    const API_BASE = (window.API_BASE_URL || 'http://localhost:8080/api/v1').replace(/\/$/, '');
    const PAGE_SIZE = 9;
    let currentPage = 1;
    let isLoading = false;

    const container = document.getElementById('usersList');
    const paginationNav = document.getElementById('paginationNav');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');
    const refreshBtn = document.getElementById('refreshBtn');

    const roleModalEl = document.getElementById('roleModal');
    let roleModal;
    const roleUserNameSpan = document.getElementById('roleUserName');
    const newRoleSelect = document.getElementById('newRoleSelect');
    const currentUserIdInput = document.getElementById('currentUserId');
    const confirmRoleBtn = document.getElementById('confirmRoleBtn');

    const deleteModalEl = document.getElementById('deleteModal');
    let deleteModal;
    const deleteUserNameSpan = document.getElementById('deleteUserName');
    const deleteUserIdInput = document.getElementById('deleteUserId');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

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

    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    async function loadUsers(page = 1) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"><span class="visually-hidden">Загрузка...</span></div></div>`;
        try {
            const url = `${API_BASE}/users/all?page=${page}&size=${PAGE_SIZE}`;
            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.status === 401 || response.status === 403) {
                container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-danger">Доступ запрещён. Только для администраторов.</p><button class="btn btn-primary" onclick="window.location.href='/'">На главную</button></div>`;
                paginationNav.classList.add('d-none');
                isLoading = false;
                return;
            }
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const users = await response.json();
            if (!Array.isArray(users)) throw new Error('Неверный формат ответа');
            renderUsers(users);
            const hasMore = users.length === PAGE_SIZE;
            updatePaginationButtons(page, hasMore);
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-danger">Ошибка загрузки: ${err.message}</p><button class="btn btn-outline-accent" onclick="location.reload()">Повторить</button></div>`;
            paginationNav.classList.add('d-none');
        } finally {
            isLoading = false;
        }
    }

    function renderUsers(users) {
        if (!users.length) {
            container.innerHTML = `<div class="col-12 text-center py-5"><p class="text-secondary">Пользователи не найдены.</p></div>`;
            return;
        }
        container.innerHTML = '';
        users.forEach(user => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-4';
            col.innerHTML = `
                <div class="card h-100" style="background: var(--bg-secondary); border-color: var(--border-color);">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(user.nickname)}</h5>
                        <p class="card-text text-secondary small">
                            <strong>ID:</strong> ${user.id}<br>
                            <strong>Email:</strong> ${escapeHtml(user.email || '—')}<br>
                            <strong>Роль:</strong> <span class="badge ${getRoleBadgeClass(user.role)}">${getRoleName(user.role)}</span>
                        </p>
                        <div class="d-flex gap-2 mt-3">
                            <button class="btn btn-sm btn-outline-accent change-role-btn" data-id="${user.id}" data-name="${escapeHtml(user.nickname)}" data-role="${user.role}">Изменить роль</button>
                            <button class="btn btn-sm btn-danger delete-btn" data-id="${user.id}" data-name="${escapeHtml(user.nickname)}">Удалить</button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(col);
        });
        document.querySelectorAll('.change-role-btn').forEach(btn => {
            btn.addEventListener('click', () => openRoleModal(btn.dataset.id, btn.dataset.name, btn.dataset.role));
        });
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => openDeleteModal(btn.dataset.id, btn.dataset.name));
        });
    }

    function getRoleName(role) {
        const map = { 'student': 'Студент', 'professor': 'Преподаватель', 'admin': 'Администратор' };
        return map[role] || role;
    }
    function getRoleBadgeClass(role) {
        if (role === 'admin') return 'bg-danger';
        if (role === 'professor') return 'bg-success';
        return 'bg-secondary';
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
        loadUsers(currentPage);
    }
    function goNextPage() {
        if (nextPageBtn.classList.contains('disabled')) return;
        currentPage++;
        loadUsers(currentPage);
    }

    let selectedUserId, selectedUserName, currentRole;

    function openRoleModal(userId, userName, role) {
        selectedUserId = userId;
        selectedUserName = userName;
        currentRole = role;
        roleUserNameSpan.innerText = userName;
        for (let i = 0; i < newRoleSelect.options.length; i++) {
            if (newRoleSelect.options[i].value === role) {
                newRoleSelect.selectedIndex = i;
                break;
            }
        }
        currentUserIdInput.value = userId;
        if (!roleModal) roleModal = new bootstrap.Modal(roleModalEl);
        roleModal.show();
    }

    async function confirmRoleChange() {
        const newRole = newRoleSelect.value;
        if (newRole === currentRole) {
            showToast('Роль не изменена (выбрана текущая).', 'warning');
            if (roleModal) roleModal.hide();
            return;
        }
        confirmRoleBtn.disabled = true;
        confirmRoleBtn.innerHTML = 'Сохранение...';
        try {
            const payload = { id: selectedUserId, role: newRole };
            const response = await fetch(`${API_BASE}/users/change-role`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload)
            });
            if (response.status === 204) {
                showToast(`Роль пользователя ${selectedUserName} изменена на ${getRoleName(newRole)}.`, 'success');
                loadUsers(currentPage);
            } else if (response.status === 409) {
                const errorData = await response.json().catch(() => ({}));
                let msg = errorData.detail || 'Невозможно изменить роль.';
                if (msg.includes('преподавателя') || msg.includes('professors')) {
                    msg = 'Нельзя назначить роль "Преподаватель": пользователь не зарегистрирован как преподаватель. Сначала одобрите заявку.';
                } else if (msg.includes('свою')) {
                    msg = 'Нельзя изменить собственную роль.';
                }
                showToast(msg, 'danger');
            } else if (response.status === 404) {
                showToast('Пользователь не найден.', 'danger');
            } else if (response.status === 403) {
                showToast('Доступ запрещён.', 'danger');
            } else {
                showToast('Ошибка при изменении роли.', 'danger');
            }
        } catch (err) {
            console.error(err);
            showToast('Ошибка сети. Попробуйте позже.', 'danger');
        } finally {
            confirmRoleBtn.disabled = false;
            confirmRoleBtn.innerHTML = 'Сохранить';
            if (roleModal) roleModal.hide();
        }
    }

    function openDeleteModal(userId, userName) {
        deleteUserIdInput.value = userId;
        deleteUserNameSpan.innerText = userName;
        if (!deleteModal) deleteModal = new bootstrap.Modal(deleteModalEl);
        deleteModal.show();
    }

    async function confirmDelete() {
        const userId = deleteUserIdInput.value;
        const userName = deleteUserNameSpan.innerText;
        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.innerHTML = 'Удаление...';
        try {
            const response = await fetch(`${API_BASE}/users/delete-user/${userId}`, {
                method: 'DELETE',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.status === 204) {
                showToast(`Пользователь ${userName} удалён.`, 'success');
                loadUsers(currentPage);
            } else if (response.status === 409) {
                const errorData = await response.json().catch(() => ({}));
                showToast(errorData.detail || 'Нельзя удалить собственный профиль.', 'danger');
            } else if (response.status === 404) {
                showToast('Пользователь не найден.', 'danger');
            } else {
                showToast('Ошибка при удалении.', 'danger');
            }
        } catch (err) {
            console.error(err);
            showToast('Ошибка сети.', 'danger');
        } finally {
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.innerHTML = 'Удалить';
            if (deleteModal) deleteModal.hide();
        }
    }

    if (prevPageBtn) prevPageBtn.addEventListener('click', (e) => { e.preventDefault(); goPrevPage(); });
    if (nextPageBtn) nextPageBtn.addEventListener('click', (e) => { e.preventDefault(); goNextPage(); });
    if (refreshBtn) refreshBtn.addEventListener('click', () => loadUsers(currentPage));
    if (confirmRoleBtn) confirmRoleBtn.addEventListener('click', confirmRoleChange);
    if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', confirmDelete);

    loadUsers(1);
})();