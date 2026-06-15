// static/profile.js
(function() {
    const profileContainer = document.getElementById('profileContainer');
    if (!profileContainer) return;

    let selectedAvatarFile = null;

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
                window.showAccessDenied(profileContainer, 'Вы не авторизованы.', true);
            } else if (response.status === 403) {
                window.showAccessDenied(profileContainer, 'Доступ запрещён.', true);
            } else {
                throw new Error('Ошибка загрузки профиля');
            }
        } catch (err) {
            console.error(err);
            profileContainer.innerHTML = '<div class="alert alert-danger">Не удалось загрузить профиль. Попробуйте позже.</div>';
        }
    }

    function renderProfile(user) {
        const initials = getInitials(user.nickname);
        const iconUrl = `${window.API_BASE_URL}users/${user.id}/icon?t=${Date.now()}`;
        profileContainer.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card border-0 shadow-sm" style="background: var(--bg-secondary);">
                        <div class="card-body p-4">
                            <div class="d-flex flex-column flex-md-row align-items-center gap-4 mb-4">
                                <div class="rounded-circle d-flex align-items-center justify-content-center overflow-hidden" 
                                     style="width: 90px; height: 90px; background: var(--accent);">
                                    <img src="${escapeHtml(iconUrl)}"
                                         alt="Avatar"
                                         style="width: 100%; height: 100%; object-fit: cover;"
                                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                    <span class="initials-fallback" style="font-size: 2.2rem; font-weight: bold; color: var(--bg-primary); display: none;">
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
                                    <a href="/admin/courses" class="btn btn-outline-accent">Управление записью</a>
                                </div>
                            ` : (user.role === 'professor' ? `
                                <hr class="my-4">
                                <div class="d-flex flex-wrap gap-2">
                                    <a href="/admin/courses" class="btn btn-outline-accent">Управление курсами</a>
                                </div>
                            ` : '')}
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

    function enterEditMode(user) {
        selectedAvatarFile = null;
        const iconUrl = `${window.API_BASE_URL}users/${user.id}/icon?t=${Date.now()}`;
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

                                <div class="mb-3 mt-3">
                                    <label class="form-label fw-bold">Фото профиля</label>
                                    <div class="d-flex align-items-center gap-3">
                                        <img src="${escapeHtml(iconUrl)}"
                                             class="current-user-icon"
                                             width="64" height="64"
                                             style="object-fit: cover;">
                                        <div>
                                            <button type="button" class="btn btn-outline-accent select-avatar-btn">Выбрать файл</button>
                                            <span class="ms-2 text-muted avatar-filename"></span>
                                        </div>
                                        <input type="file" class="d-none" id="avatarFileInput" accept="image/*">
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
        const selectBtn = form.querySelector('.select-avatar-btn');
        const fileInput = document.getElementById('avatarFileInput');
        const filenameSpan = form.querySelector('.avatar-filename');

        selectBtn.addEventListener('click', () => {
            fileInput.click();
        });
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                selectedAvatarFile = fileInput.files[0];
                filenameSpan.textContent = selectedAvatarFile.name;
                const reader = new FileReader();
                reader.onload = (e) => {
                    const previewImg = form.querySelector('.current-user-icon');
                    if (previewImg) {
                        previewImg.src = e.target.result;
                    }
                };
                reader.readAsDataURL(selectedAvatarFile);
            } else {
                selectedAvatarFile = null;
                filenameSpan.textContent = '';
            }
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newNickname = document.getElementById('editNickname').value.trim();
            const newEmail = document.getElementById('editEmail').value.trim() || null;

            if (!newNickname) {
                window.showToast('Никнейм не может быть пустым', 'danger');
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

                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) throw new Error('Доступ запрещён');
                    if (response.status === 404) throw new Error('Пользователь не найден');
                    if (response.status === 409) {
                        const error = await response.json().catch(() => ({}));
                        throw new Error(error.detail || 'Никнейм или email уже заняты');
                    }
                    if (response.status === 422) throw new Error('Ошибка валидации данных');
                    throw new Error('Ошибка обновления профиля');
                }

                if (selectedAvatarFile) {
                    const formData = new FormData();
                    formData.append('icon_file', selectedAvatarFile);
                    const iconRes = await fetch(`${window.API_BASE_URL}users/icon`, {
                        method: 'POST',
                        credentials: 'include',
                        body: formData
                    });
                    if (!iconRes.ok) {
                        if (iconRes.status === 401 || iconRes.status === 403) throw new Error('Доступ запрещён');
                        if (iconRes.status === 415) throw new Error('Некорректный тип файла');
                        throw new Error('Не удалось загрузить фото профиля');
                    }
                }

                window.showToast('Профиль успешно обновлён');
                loadProfile();
            } catch (err) {
                console.error(err);
                window.showToast(err.message, 'danger');
            }
        });

        cancelBtn.addEventListener('click', () => loadProfile());
    }

    loadProfile();
})();