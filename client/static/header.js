(function() {
    const themeToggle = document.getElementById('themeToggle');
    const themeText = document.getElementById('themeText');
    const htmlElement = document.documentElement;

    function setTheme(newTheme) {
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        if (themeText) {
            themeText.textContent = newTheme === 'dark' ? 'Свет' : 'Тьма';
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

    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        const visiblePaths = ['/', '/admin/users'];
searchBox.style.display = visiblePaths.includes(window.location.pathname) ? 'flex' : 'none';
    }

    const loginBtn = document.getElementById('loginBtn');
    const profileBtn = document.getElementById('profileBtn');
    const myNotesBtn = document.getElementById('myNotesBtn');

    function updateAuthButtons() {
        if (!loginBtn || !profileBtn) return;
        const isLoggedIn = window.Auth && window.Auth.isAuthenticated();
        loginBtn.style.display = isLoggedIn ? 'none' : '';
        profileBtn.style.display = isLoggedIn ? '' : 'none';
        myNotesBtn.style.display = isLoggedIn ? '' : 'none';
    }

    if (window.Auth) {
        updateAuthButtons();
    } else {
        document.addEventListener('auth-loaded', updateAuthButtons);
    }

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                window.AuthModal.open();
            }
        });
    }

    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            window.location.href = '/me';
        });
    }

    if (myNotesBtn) {
        myNotesBtn.addEventListener('click', () => {
            window.location.href = '/my-notes';
        });
    }

    window.addEventListener('auth-changed', updateAuthButtons);
})();