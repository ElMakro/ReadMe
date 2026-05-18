(function() {
    const coursesGrid = document.getElementById('coursesGrid');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const searchInput = document.getElementById('searchInput');
    const filtersBtn = document.getElementById('filtersBtn');
    const pageInfo = document.getElementById('pageInfo');
    const myCoursesBtn = document.getElementById('myCoursesBtn');
    const manageCoursesBtn = document.getElementById('manageCoursesBtn');

    let currentPage = 1;
    let currentSearch = '';
    let totalItems = null;        // null = неизвестно общее количество
    const limit = 10;            // records_per_page

    function updateButtonsByAuth() {
        const isLoggedIn = window.Auth && window.Auth.isAuthenticated();
        if (myCoursesBtn) myCoursesBtn.style.display = isLoggedIn ? '' : 'none';
        if (manageCoursesBtn) manageCoursesBtn.style.display = isLoggedIn ? '' : 'none';
    }

    async function fetchCourses(page = 1, search = '') {
        const searchTerm = search.trim();
        const isLoggedIn = window.Auth && window.Auth.isAuthenticated();
        const basePath = isLoggedIn ? 'courses/authorized-search' : 'courses/search';

        const params = new URLSearchParams();
        params.append('page', page);
        params.append('records_per_page', limit);
        if (searchTerm !== '') {
            params.append('course_name_prefix', searchTerm);
        }

        const url = `${window.API_BASE_URL}${basePath}?${params.toString()}`;

        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) {
                // Если 401 при попытке использовать authorized-search (например, сессия истекла)
                if (response.status === 401 && isLoggedIn) {
                    // Можно вызвать перепроверку авторизации
                    if (window.Auth && window.Auth.check) await window.Auth.check();
                    // Или просто перезагрузить страницу
                    window.location.reload();
                    return;
                }
                throw new Error('Ошибка загрузки курсов');
            }
            const data = await response.json();
            // Поддержка двух форматов
            let courses, total;
            if (Array.isArray(data)) {
                courses = data;
                total = null;
            } else {
                courses = data.courses || [];
                total = data.total !== undefined ? data.total : null;
            }
            totalItems = total;
            renderCourses(courses);
            updatePagination(page, totalItems, courses.length);
        } catch (error) {
            console.error(error);
            coursesGrid.innerHTML = '<p class="text-center text-danger">Не удалось загрузить курсы.</p>';
        }
    }

    function renderCourses(courses) {
        if (!coursesGrid) return;
        coursesGrid.innerHTML = '';
        if (courses.length === 0) {
            coursesGrid.innerHTML = '<p class="text-center">Курсы не найдены.</p>';
            return;
        }
        courses.forEach(course => {
            const col = document.createElement('div');
            col.className = 'col';
            col.innerHTML = `
                <div class="course-card position-relative">
                    <a href="/course/${course.id}" class="stretched-link text-decoration-none">
                        <h5 class="course-title">${escapeHtml(course.name)}</h5>
                        <p class="course-instructor">${escapeHtml(course.professor_id || 'Преподаватель')}</p>
                        <p class="course-description">${escapeHtml(course.description || '')}</p>
                    </a>
                </div>
            `;
            coursesGrid.appendChild(col);
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function updatePagination(page, total, fetchedCount) {
        let totalPages = null;

        if (total !== null && total !== undefined) {
            totalPages = Math.ceil(total / limit) || 1;
        }

        // Кнопка "Назад"
        if (prevBtn) prevBtn.disabled = page <= 1;

        // Кнопка "Вперёд"
        let nextDisabled = false;
        if (totalPages !== null) {
            nextDisabled = page >= totalPages;
        } else {
            // Если общее количество неизвестно, следующая страница есть только если получили ровно limit записей
            nextDisabled = fetchedCount < limit;
        }
        if (nextBtn) nextBtn.disabled = nextDisabled;

        // Отображение информации о странице
        if (pageInfo) {
            if (totalPages !== null) {
                pageInfo.textContent = `Страница ${page} из ${totalPages}`;
            } else {
                pageInfo.textContent = `Страница ${page}`;
            }
        }

        currentPage = page;
    }

    // Обработчики
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) fetchCourses(currentPage - 1, currentSearch);
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            fetchCourses(currentPage + 1, currentSearch);
        });
    }

    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            searchTimeout = setTimeout(() => {
                currentSearch = query;
                fetchCourses(1, currentSearch);
            }, 400);
        });
    }

    if (filtersBtn) {
        filtersBtn.addEventListener('click', () => alert('Фильтры курсов (демо)'));
    }
    if (myCoursesBtn) {
        myCoursesBtn.addEventListener('click', () => window.location.href = '/my-courses');
    }
    if (manageCoursesBtn) {
        manageCoursesBtn.addEventListener('click', () => window.location.href = '/created-courses');
    }

    window.addEventListener('auth-changed', () => {
        updateButtonsByAuth();
        // Сбросить поиск и загрузить первую страницу заново
        currentSearch = '';
        if (searchInput) searchInput.value = '';
        fetchCourses(1, '');
    });

    function init() {
        if (window.Auth && window.Auth.isAuthenticated !== undefined) {
            updateButtonsByAuth();
        } else {
            document.addEventListener('auth-loaded', updateButtonsByAuth);
        }
        fetchCourses(1);
    }

    init();
})();