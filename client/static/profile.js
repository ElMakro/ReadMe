(function() {
    const profileContainer = document.getElementById('profileContainer');
    if (!profileContainer) return;

    // ---- Вспомогательные функции ----
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function getRoleName(role) {
        const roleMap = {
            'admin': 'Администратор',
            'professor': 'Преподаватель',
            'student': 'Студент'
        };
        return roleMap[role] || 'Студент';
    }

    function getInitials(nickname) {
        return nickname ? nickname.charAt(0).toUpperCase() : '?';
    }

    function showMessage(text, isError = false) {
        const toast = document.createElement('div');
        toast.textContent = text;
        toast.style.cssText = `
            position: fixed; bottom: 20px; right: 20px; z-index: 9999;
            padding: 12px 20px; border-radius: 8px; background: ${isError ? '#dc3545' : '#198754'};
            color: white; box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: opacity 0.3s;
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ---- Загрузка профиля ----
    async function loadProfile() {
        profileContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-accent" role="status"></div>
                <p class="mt-2 text-secondary">Загрузка профиля...</p>
            </div>`;
        try {
            const response = await fetch(`${window.API_BASE_URL}users/profile`, {
                credentials: 'include'
            });
            if (response.ok) {
                const user = await response.json();
                renderProfile(user);
            } else if (response.status === 401) {
                renderNotLoggedIn();
            } else {
                throw new Error('Ошибка загрузки профиля');
            }
        } catch (err) {
            console.error(err);
            profileContainer.innerHTML = '<div class="alert alert-danger">Не удалось загрузить профиль. Попробуйте позже.</div>';
        }
    }

    // ---- Отображение профиля (карточка + аватар) ----
    function renderProfile(user) {
        const initials = getInitials(user.nickname);
        profileContainer.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card border-0 shadow-sm" style="background: var(--bg-secondary);">
                        <div class="card-body p-4">
                            <div class="d-flex flex-column flex-md-row align-items-center gap-4 mb-4">
                                <!-- Аватар с инициалами -->
                                <div class="rounded-circle d-flex align-items-center justify-content-center" 
                                     style="width: 90px; height: 90px; background: var(--accent);">
                                    <span style="font-size: 2.2rem; font-weight: bold; color: var(--bg-primary);">
                                        ${escapeHtml(initials)}
                                    </span>
                                </div>
                                <div class="text-center text-md-start">
                                    <h3 class="mb-1">${escapeHtml(user.nickname)}</h3>
                                    <p class="text-secondary mb-0">${escapeHtml(getRoleName(user.role))}</p>
                                </div>
                            </div>

                            <div class="row g-3 mb-4">
                                <div class="col-md-6">
                                    <div class="p-3 rounded-3" style="background: rgba(var(--bs-primary-rgb), 0.1);">
                                        <small class="text-secondary text-uppercase d-block">Никнейм</small>
                                        <span class="fs-5 fw-semibold">${escapeHtml(user.nickname)}</span>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-3 rounded-3" style="background: rgba(var(--bs-primary-rgb), 0.1);">
                                        <small class="text-secondary text-uppercase d-block">Email</small>
                                        <span class="fs-5 fw-semibold">${escapeHtml(user.email || '—')}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="d-flex flex-wrap gap-2 mt-3">
                                <button class="btn btn-accent" id="editProfileBtn">Редактировать профиль</button>
                                <button class="btn btn-outline-accent" id="logoutBtn">Выход</button>
                                <a href="/my-applications" class="btn btn-outline-accent">Мои заявки</a>
                            </div>

                            ${user.role === 'admin' ? `
                                <hr class="my-4">
                                <div class="d-flex flex-wrap gap-2">
                                    <a href="/admin/applications" class="btn btn-outline-accent">Управление заявками</a>
                                    <a href="/admin/users" class="btn btn-outline-accent">Управление пользователями</a>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('logoutBtn').addEventListener('click', () => {
            if (window.Auth && window.Auth.logout) {
                window.Auth.logout();
            } else {
                fetch(`${window.API_BASE_URL}auth/logout`, { credentials: 'include' })
                    .finally(() => window.location.href = '/');
            }
        });

        const editBtn = document.getElementById('editProfileBtn');
        if (editBtn) editBtn.addEventListener('click', () => enterEditMode(user));
    }

    // ---- Режим редактирования (две колонки, email опционален) ----
    function enterEditMode(user) {
        profileContainer.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card border-0 shadow-sm" style="background: var(--bg-secondary);">
                        <div class="card-body p-4">
                            <h3 class="card-title mb-4">Редактирование профиля</h3>
                            <form id="editProfileForm">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold">Никнейм <span class="text-danger">*</span></label>
                                        <input type="text" class="form-control" id="editNickname" 
                                               value="${escapeHtml(user.nickname)}" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold">Email</label>
                                        <input type="email" class="form-control" id="editEmail" 
                                               value="${escapeHtml(user.email || '')}" placeholder="example@domain.com">
                                    </div>
                                </div>
                                <div class="d-flex gap-2 mt-4">
                                    <button type="submit" class="btn btn-accent">Сохранить</button>
                                    <button type="button" class="btn btn-outline-secondary" id="cancelEditBtn">Отмена</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const form = document.getElementById('editProfileForm');
        const cancelBtn = document.getElementById('cancelEditBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newNickname = document.getElementById('editNickname').value.trim();
            const newEmail = document.getElementById('editEmail').value.trim() || null;

            if (!newNickname) {
                showMessage('Никнейм не может быть пустым', true);
                return;
            }

            const payload = { nickname: newNickname };
            if (newEmail !== null) payload.email = newEmail;

            try {
                const response = await fetch(`${window.API_BASE_URL}users/profile`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const updatedUser = await response.json();
                    showMessage('Профиль успешно обновлён');
                    renderProfile(updatedUser);
                } else if (response.status === 409) {
                    const error = await response.json().catch(() => ({}));
                    showMessage(error.detail || 'Никнейм или email уже заняты', true);
                } else {
                    throw new Error('Ошибка обновления');
                }
            } catch (err) {
                console.error(err);
                showMessage('Не удалось обновить профиль', true);
            }
        });

        cancelBtn.addEventListener('click', () => loadProfile());
    }

    function renderNotLoggedIn() {
        profileContainer.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card border-0 shadow-sm text-center p-4" style="background: var(--bg-secondary);">
                        <p class="mb-3">Вы не авторизованы.</p>
                        <button class="btn btn-accent" id="loginFromProfileBtn">Войти</button>
                    </div>
                </div>
            </div>
        `;
        const loginBtn = document.getElementById('loginFromProfileBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                    window.AuthModal.open();
                }
            });
        }
    }

    loadProfile();
})();