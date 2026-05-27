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

    function updateButtonsByAuthAndRole() {
        const isLoggedIn = window.Auth && window.Auth.isAuthenticated();

        // Мои курсы – всем авторизованным
        if (myCoursesBtn) myCoursesBtn.style.display = isLoggedIn ? '' : 'none';

        // Мастерская курсов – только преподавателям и админам
        let showManage = false;
        if (isLoggedIn && window.Auth.getUser) {
            const user = window.Auth.getUser();
            if (user && (user.role === 'professor' || user.role === 'admin')) {
                showManage = true;
            }
        }
        if (manageCoursesBtn) manageCoursesBtn.style.display = showManage ? '' : 'none';
    }

    async function fetchCourses(page = 1, search = '') {
        const searchTerm = search.trim();
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('records_per_page', limit);
        if (searchTerm !== '') {
            params.append('criteria', 'name_prefix');
            params.append('value', searchTerm);
        } else {
            params.append('criteria', 'name_prefix');
            params.append('value', '');
        }

        const url = `${window.API_BASE_URL}courses/search?${params.toString()}`;

        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) {
                if (response.status === 401) {
                    if (window.Auth && window.Auth.check) await window.Auth.check();
                    else window.location.reload();
                    return;
                }
                throw new Error('Ошибка загрузки курсов');
            }
            const data = await response.json();
            // Ожидаем массив CourseSearchResponse
            const courses = Array.isArray(data) ? data : (data.courses || []);
            renderCourses(courses);
            // Пагинация: если вернулось меньше limit, значит это последняя страница
            updatePagination(page, null, courses.length);
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
            let stateText = '';
            if (course.state === 'enrolled') stateText = '<span class="badge bg-success">Записан</span>';
            else if (course.state === 'controlled') stateText = '<span class="badge bg-primary">Преподаю</span>';
            else if (course.state === 'enrollable') stateText = '<span class="badge bg-secondary">Можно записаться</span>';

            // Добавляем описание курса
            const description = course.description || 'Описание отсутствует';
            const shortDesc = description.length > 100 ? description.substring(0, 100) + '…' : description;

            col.innerHTML = `
                <div class="course-card position-relative">
                    <a href="/course/${course.id}" class="stretched-link text-decoration-none">
                        <h5 class="course-title">${escapeHtml(course.name)}</h5>
                        <div class="course-state mb-2">${stateText}</div>
                        <p class="course-description">${escapeHtml(shortDesc)}</p>
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
        updateButtonsByAuthAndRole();
        // Сбросить поиск и загрузить первую страницу заново
        currentSearch = '';
        if (searchInput) searchInput.value = '';
        fetchCourses(1, '');
    });

    function init() {
        if (window.Auth && window.Auth.isAuthenticated !== undefined) {
            updateButtonsByAuthAndRole();
        } else {
            document.addEventListener('auth-loaded', updateButtonsByAuth);
        }
        fetchCourses(1);
    }

    init();
})();