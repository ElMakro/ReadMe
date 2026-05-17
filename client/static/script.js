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
    let totalItems = 0;
    const limit = 6;  // records_per_page

    function updateButtonsByAuth() {
        const isLoggedIn = window.Auth && window.Auth.isAuthenticated();
        if (myCoursesBtn) myCoursesBtn.style.display = isLoggedIn ? '' : 'none';
        if (manageCoursesBtn) manageCoursesBtn.style.display = isLoggedIn ? '' : 'none';
    }

    async function fetchCourses(page = 1, search = '') {
        // Для поиска используем эндпоинт search. Если search пустой, передаём пробел (или договориться с бэком)
        let searchTerm = search.trim();
        if (searchTerm === '') searchTerm = ' '; // костыль, если бэкенд не принимает пустую строку
        const url = `${window.API_BASE_URL}courses/search/${encodeURIComponent(searchTerm)}?page=${page}&records_per_page=${limit}`;
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) throw new Error('Ошибка загрузки курсов');
            const data = await response.json();
            // Ожидаем: { courses: [...], total: number }
            totalItems = data.total || 0;
            renderCourses(data.courses || []);
            updatePagination(page, totalItems);
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

    function updatePagination(page, total) {
        const totalPages = Math.ceil(total / limit) || 1;
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= totalPages;
        if (pageInfo) {
            pageInfo.textContent = `Страница ${page} из ${totalPages}`;
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
            const totalPages = Math.ceil(totalItems / limit);
            if (currentPage < totalPages) fetchCourses(currentPage + 1, currentSearch);
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

    window.addEventListener('auth-changed', updateButtonsByAuth);

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