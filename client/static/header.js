(function() {
    // ========== ПЕРЕКЛЮЧЕНИЕ ТЕМЫ ==========
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    const htmlElement = document.documentElement;

    function setTheme(newTheme) {
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeButton(newTheme);
    }

    function updateThemeButton(theme) {
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Свет';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Тьма';
        }
    }

    function toggleTheme() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }

    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // ========== КНОПКИ ВХОДА И ПРОФИЛЯ ==========
    const loginBtn = document.getElementById('loginBtn');
    const profileBtn = document.getElementById('profileBtn');

//    // Функция обновления видимости кнопок
//    function updateAuthButtons() {
//        if (!loginBtn || !profileBtn) return;
//        const isLoggedIn = localStorage.getItem('loggedIn') === 'true';
//        if (isLoggedIn) {
//            loginBtn.style.display = 'none';
//            profileBtn.style.display = '';
//        } else {
//            loginBtn.style.display = '';
//            profileBtn.style.display = 'none';
//        }
//    }
    // ВРЕМЕННО!!!
    function updateAuthButtons() {
        if (!loginBtn || !profileBtn) return;
        const isLoggedIn = localStorage.getItem('loggedIn') === 'true';
        // Показываем профиль, если залогинены и есть хоть какой-то идентификатор
        if (isLoggedIn && (localStorage.getItem('user_id') || localStorage.getItem('nickname'))) {
            loginBtn.style.display = 'none';
            profileBtn.style.display = '';
        } else {
            loginBtn.style.display = '';
            profileBtn.style.display = 'none';
        }
    }

    // Начальное состояние
    updateAuthButtons();

    // Обработчик клика по кнопке «Вход»
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                window.AuthModal.open();
            } else {
                console.error('AuthModal не готов');
            }
        });
    }

//    // Обработчик клика по кнопке «Профиль»
//    if (profileBtn) {
//        profileBtn.addEventListener('click', function() {
//            const userId = localStorage.getItem('user_id');
//            if (userId) {
//                window.location.href = `/me/${userId}`;
//            } else {
//                window.location.href = '/';
//            }
//        });
//    }
    // ВРЕМЕННО!!!
    if (profileBtn) {
    profileBtn.addEventListener('click', function() {
        const userId = localStorage.getItem('user_id');
        const nickname = localStorage.getItem('nickname');
        const id = userId || nickname;
        if (id) {
            window.location.href = `/me/${encodeURIComponent(id)}`;
        } else {
            window.location.href = '/';
        }
    });
}

//    // Слушатель успешной авторизации
//    window.addEventListener('auth-changed', function(e) {
//        console.log('Получено событие auth-changed', e.detail);
//        if (e.detail && e.detail.loggedIn) {
//            localStorage.setItem('loggedIn', 'true');
//            const userId = e.detail.user?.id || e.detail.user?.user_id;
//            if (userId) localStorage.setItem('user_id', userId);
//            updateAuthButtons();
//        }
//    });
    // ВРЕМЕННО!!!
    window.addEventListener('auth-changed', function(e) {
        console.log('Получено событие auth-changed', e.detail);
        if (e.detail && e.detail.loggedIn) {
            localStorage.setItem('loggedIn', 'true');
            const userId = e.detail.user?.id || e.detail.user?.user_id;
            const nickname = e.detail.user?.nickname;
            if (userId) localStorage.setItem('user_id', userId);
            if (nickname) localStorage.setItem('nickname', nickname);
            updateAuthButtons();
        }
    });
})();