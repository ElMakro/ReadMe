(function() {
    const coursesGrid = document.getElementById('coursesGrid');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const searchInput = document.getElementById('searchInput');
    const filtersBtn = document.getElementById('filtersBtn');
    const pageInfo = document.getElementById('pageInfo');

    let currentPage = 1;
    let currentSearch = '';
    let totalPages = 1;
    const limit = 8;

    // Определяет, какой эндпоинт использовать для получения курсов
    function getApiUrl() {
        // Пока всегда один эндпоинт; при авторизации можно будет переключить на /courses/my-courses
        return '/courses';
    }

    // Загрузка курсов с сервера
    async function fetchCourses(page = 1, search = '') {
        const apiUrl = getApiUrl();
        try {
            const params = new URLSearchParams({ page, limit });
            if (search) params.append('search', search);

            const response = await fetch(`${apiUrl}?${params}`);
            if (!response.ok) throw new Error('Ошибка загрузки курсов');

            const data = await response.json();
            currentPage = data.page;
            totalPages = data.total_pages;
            renderCourses(data.courses);
            updatePagination();
        } catch (error) {
            console.error(error);
            coursesGrid.innerHTML = '<p class="text-center text-danger">Не удалось загрузить курсы.</p>';
        }
    }

    // Отрисовка карточек
    function renderCourses(courses) {
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
                        <h5 class="course-title">${escapeHtml(course.title)}</h5>
                        <p class="course-instructor">${escapeHtml(course.instructor)}</p>
                        <p class="course-description">${escapeHtml(course.description)}</p>
                    </a>
                </div>
            `;
            coursesGrid.appendChild(col);
        });
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Пагинация
    function updatePagination() {
        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled = currentPage >= totalPages;
        if (pageInfo) {
            pageInfo.textContent = `Страница ${currentPage} из ${totalPages}`;
        }
    }

    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            fetchCourses(currentPage - 1, currentSearch);
        }
    });

    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            fetchCourses(currentPage + 1, currentSearch);
        }
    });

    // Поиск
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            searchTimeout = setTimeout(() => {
                currentSearch = query;
                fetchCourses(1, currentSearch);
            }, 400);
        });
    }

    // Фильтры (демо)
    if (filtersBtn) {
        filtersBtn.addEventListener('click', () => alert('Фильтры курсов (демо)'));
    }

    // Реакция на авторизацию (можно оставить)
    window.addEventListener('auth-changed', function(e) {
        console.log('auth-changed, обновляем список курсов');
        fetchCourses(currentPage, currentSearch);
    });

    // Первоначальная загрузка
    fetchCourses(1);
})();