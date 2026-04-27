(function() {
    // ========== Т Е М А ==========
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

    // ========== К Н О П К А   В Х О Д А ==========
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

    // ========== Д Е М О - К Н О П К И ==========
    function showFiltersAlert() { alert('Фильтры курсов (демо)'); }
    function showPrevPageAlert() { alert('Предыдущая страница (демо)'); }
    function showNextPageAlert() { alert('Следующая страница (демо)'); }

    const filtersBtn = document.getElementById('filtersBtn');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (filtersBtn) filtersBtn.addEventListener('click', showFiltersAlert);
    if (prevBtn) prevBtn.addEventListener('click', showPrevPageAlert);
    if (nextBtn) nextBtn.addEventListener('click', showNextPageAlert);

    // ========== П О И С К ==========
    const searchInput = document.getElementById('searchInput');
    const courseCards = document.querySelectorAll('.course-card');

    function filterCourses(query) {
        courseCards.forEach(function(card) {
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
    }

    if (searchInput) {
        searchInput.addEventListener('input', function(event) {
            const query = event.target.value.toLowerCase().trim();
            filterCourses(query);
        });
    }
})();