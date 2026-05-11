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

    // Видимость кнопок зависит только от loggedIn
    function updateAuthButtons() {
        if (!loginBtn || !profileBtn) return;
        const isLoggedIn = localStorage.getItem('loggedIn') === 'true';
        loginBtn.style.display = isLoggedIn ? 'none' : '';
        profileBtn.style.display = isLoggedIn ? '' : 'none';
    }

    updateAuthButtons();

    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                window.AuthModal.open();
            } else {
                console.error('AuthModal не готов');
            }
        });
    }

    // При клике на «Профиль» просто переходим на /me
    if (profileBtn) {
        profileBtn.addEventListener('click', function() {
            window.location.href = '/me';
        });
    }

    // Событие после успешного входа
    window.addEventListener('auth-changed', function(e) {
        if (e.detail && e.detail.loggedIn) {
            localStorage.setItem('loggedIn', 'true');
            updateAuthButtons();
        }
    });
})();