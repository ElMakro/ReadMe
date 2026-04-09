(function() {
    // Переключение темы (data-theme)
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

    // Демо-обработчики (нужно заменить на реальную логику)
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => alert('Форма входа (демо)'));
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

    // Поиск по курсам (фильтрация по названию)
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