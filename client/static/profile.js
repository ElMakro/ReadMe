(function() {
    const profileContainer = document.getElementById('profileContainer');
    if (!profileContainer) return;

    async function loadProfile() {
        profileContainer.innerHTML = '<div class="text-center">Загрузка...</div>';
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
            profileContainer.innerHTML = '<p class="text-danger">Не удалось загрузить профиль. Возможно, сервер недоступен.</p>';
        }
    }

    function getRoleName(role) {
        const roleMap = {
            'admin': 'администратор',
            'professor': 'преподаватель',
            'student': 'обучающийся'
        };
        return roleMap[role] || 'обучающийся';
    }

    function renderProfile(user) {
        profileContainer.innerHTML = `
            <div class="row mb-5">
                <div class="col-lg-8">
                    <h3 class="mb-4">Мои Данные</h3>
                    <div class="data-item d-flex align-items-center mb-3">
                        <span class="fw-bold me-2">Никнейм:</span> ${escapeHtml(user.nickname)}
                    </div>
                    <div class="data-item d-flex align-items-center mb-3">
                        <span class="fw-bold me-2">Почта:</span> ${escapeHtml(user.email || 'не указана')}
                    </div>
                    <div class="data-item d-flex align-items-center mb-3">
                        <span class="fw-bold me-2">Роль:</span> ${escapeHtml(getRoleName(user.role))}
                    </div>
                    <button class="btn btn-outline-accent" id="logoutBtn">Выход</button>
                    ${user.role === 'admin' ? `
                        <div class="mt-3">
                            <a href="/admin/applications" class="btn btn-outline-accent w-100">Управление заявками на преподавание</a>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                if (window.Auth && window.Auth.logout) {
                    window.Auth.logout();
                } else {
                    fetch(`${window.API_BASE_URL}auth/logout`, { credentials: 'include' })
                        .finally(() => window.location.href = '/');
                }
            });
        }
    }

    function renderNotLoggedIn() {
        profileContainer.innerHTML = `
            <div class="alert alert-warning">
                Вы не авторизованы. <a href="#" id="loginLink">Войдите</a>, чтобы увидеть профиль.
            </div>
        `;
        const loginLink = document.getElementById('loginLink');
        if (loginLink) {
            loginLink.addEventListener('click', (e) => {
                e.preventDefault();
                if (window.AuthModal) window.AuthModal.open();
            });
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadProfile();
})();