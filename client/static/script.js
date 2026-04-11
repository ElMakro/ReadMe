(function() {
    // === ТЕМА (светлая/тёмная) ===
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    const htmlElement = document.documentElement;

    function updateThemeButton(theme) {
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Свет';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Тьма';
        }
    }

    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeButton(newTheme);
        });
    }

    // === МОДАЛЬНОЕ ОКНО: открытие и закрытие ===
    const loginBtn = document.getElementById('loginBtn');
    const modal = document.getElementById('authModal');
    const closeBtn = document.querySelector('.modal-close');

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            modal.classList.add('active');
        });
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
    }

    // === ПЕРЕКЛЮЧЕНИЕ МЕЖДУ ВХОДОМ И РЕГИСТРАЦИЕЙ ===
    const showLoginBtn = document.getElementById('showLoginBtn');
    const showRegBtn = document.getElementById('showRegBtn');
    const loginFields = document.getElementById('loginFields');
    const regFields = document.getElementById('regFields');
    const modalTitle = document.getElementById('modalTitle');
    const submitBtn = document.getElementById('submitBtn');
    let currentMode = 'login';

    function switchToLogin() {
        loginFields.style.display = 'block';
        regFields.style.display = 'none';

        // Это очень важно, иначе появится ошибка и не отработает отправка формы
        // Добавляем required полям входа
        document.getElementById('loginNickname').setAttribute('required', '');
        document.getElementById('loginPassword').setAttribute('required', '');

        // Убираем required с полей регистрации
        document.getElementById('regNickname').removeAttribute('required');
        document.getElementById('regPassword').removeAttribute('required');
        document.getElementById('regConfirm').removeAttribute('required');

        modalTitle.textContent = 'Вход';
        submitBtn.textContent = 'Войти';
        currentMode = 'login';
    }
    function switchToReg() {
        loginFields.style.display = 'none';
        regFields.style.display = 'block';

        // Это очень важно, иначе появится ошибка и не отработает отправка формы
        // Убираем required с полей входа
        document.getElementById('loginNickname').removeAttribute('required');
        document.getElementById('loginPassword').removeAttribute('required');

        // Добавляем required полям регистрации
        document.getElementById('regNickname').setAttribute('required', '');
        document.getElementById('regPassword').setAttribute('required', '');
        document.getElementById('regConfirm').setAttribute('required', '');

        modalTitle.textContent = 'Регистрация';
        submitBtn.textContent = 'Зарегистрироваться';
        currentMode = 'reg';
    }

    if (showLoginBtn) showLoginBtn.addEventListener('click', switchToLogin);
    if (showRegBtn) showRegBtn.addEventListener('click', switchToReg);

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            switchToLogin();
            modal.classList.add('active');
        });
    }

    // === ОБРАБОТКА ОТПРАВКИ ФОРМЫ  ===
    const authForm = document.getElementById('authForm');
    if (authForm) {
        authForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (currentMode === "login") {
                // Вход
                const nickname = document.getElementById('loginNickname').value;
                alert(`Привет, ${nickname}!`);
            } else {
                // Регистрация
                const nickname = document.getElementById('regNickname').value;
                const password = document.getElementById('regPassword').value;
                const confirm = document.getElementById('regConfirm').value;
                if (password !== confirm) {
                    alert('Пароли не совпадают!');
                    return;
                }
                alert(`Пользователь ${nickname} создан!`);
            }
            modal.classList.remove('active');
            authForm.reset();
        });
    }

    const filtersBtn = document.getElementById('filtersBtn');
    if (filtersBtn) {
        filtersBtn.addEventListener('click', () => alert('Фильтры курсов (демо)'));
    }

    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => alert('Предыдущая страница (демо)'));
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => alert('Следующая страница (демо)'));
    }

    const searchInput = document.getElementById('searchInput');
    const courseCards = document.querySelectorAll('.course-card');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            courseCards.forEach(card => {
                const titleElem = card.querySelector('.course-number');
                if (titleElem) {
                    const title = titleElem.textContent.toLowerCase();
                    const parentCol = card.closest('.col');
                    if (query === '' || title.includes(query)) {
                        parentCol.style.display = '';
                    } else {
                        parentCol.style.display = 'none';
                    }
                }
            });
        });
    }
})();