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

    // Установка сохранённой темы
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // ========== КНОПКА ВХОДА ==========
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                window.AuthModal.open();
            } else {
                console.error('AuthModal не готов');
            }
        });
    }
})();