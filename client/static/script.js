// static/script.js
(function() {
    const coursesGrid = document.getElementById('coursesGrid');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const searchInput = document.getElementById('searchInput');
    const filtersBtn = document.getElementById('filtersBtn');
    const pageInfoSpan = document.getElementById('pageInfo');
    const myCoursesBtn = document.getElementById('myCoursesBtn');
    const manageCoursesBtn = document.getElementById('manageCoursesBtn');

    let currentPage = 1;
    let currentSearch = '';
    const limit = 9;
    let isLoading = false;
    let totalPages = 1;

    function updateButtonsByAuthAndRole() {
        const isLoggedIn = window.Auth && window.Auth.isAuthenticated();
        if (myCoursesBtn) myCoursesBtn.style.display = isLoggedIn ? '' : 'none';
        let showManage = false;
        if (isLoggedIn && window.Auth.getUser) {
            const user = window.Auth.getUser();
            if (user && (user.role === 'professor' || user.role === 'admin')) showManage = true;
        }
        if (manageCoursesBtn) manageCoursesBtn.style.display = showManage ? '' : 'none';
    }

    async function fetchCourses(page = 1, search = '') {
        if (isLoading) return;
        isLoading = true;
        coursesGrid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>';

        const searchTerm = search.trim();
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('records_per_page', limit);
        params.append('criteria', 'name_prefix');
        params.append('value', searchTerm);

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
            const courses = await response.json();
            const fetchedCount = courses.length;

            if (fetchedCount === 0 && page > 1) {
                currentPage = page - 1;
                renderCourses([]);
                updatePagination(currentPage, false);
                return;
            }
            renderCourses(courses);
            const hasNext = fetchedCount === limit;
            const total = hasNext ? page + 1 : page;
            updatePagination(page, total);
            currentPage = page;
            totalPages = total;
        } catch (error) {
            console.error(error);
            coursesGrid.innerHTML = '<p class="text-center text-danger">Не удалось загрузить курсы.</p>';
            updatePagination(page, page);
        } finally {
            isLoading = false;
        }
    }

    function renderCourses(courses) {
        if (!coursesGrid) return;
        if (courses.length === 0) {
            coursesGrid.innerHTML = '<p class="text-center">Курсы не найдены.</p>';
            return;
        }
        coursesGrid.innerHTML = '';
        courses.forEach(course => {
            const col = document.createElement('div');
            col.className = 'col';
            let stateText = '';
            if (course.state === 'enrolled') stateText = '<span class="badge bg-success">Записан</span>';
            else if (course.state === 'controlled') stateText = '<span class="badge bg-accent-dark">Преподаю</span>';
            else stateText = '<span class="badge bg-secondary">Можно записаться</span>';
            const description = course.description || 'Описание отсутствует';
            const shortDesc = description.length > 100 ? description.substring(0, 100) + '…' : description;

            col.innerHTML = `
                <div class="course-card position-relative d-flex flex-column h-100">
                    <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                         class="course-icon"
                         alt="Иконка курса">
                    <a href="/course/${course.id}" class="stretched-link text-decoration-none">
                        <h5 class="course-title mt-2">${escapeHtml(course.name)}</h5>
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

    function updatePagination(page, total) {
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= total;
        if (pageInfoSpan) pageInfoSpan.textContent = `Страница ${page} из ${total}`;
    }

    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1 && !isLoading) fetchCourses(currentPage - 1, currentSearch); });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (currentPage < totalPages && !isLoading) fetchCourses(currentPage + 1, currentSearch); });

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

    if (filtersBtn) filtersBtn.addEventListener('click', () => window.showToast('Фильтры курсов (демо)', 'warning'));
    if (myCoursesBtn) myCoursesBtn.addEventListener('click', () => window.location.href = '/my-courses');
    if (manageCoursesBtn) manageCoursesBtn.addEventListener('click', () => window.location.href = '/created-courses');

    window.addEventListener('auth-changed', () => {
        updateButtonsByAuthAndRole();
        currentSearch = '';
        if (searchInput) searchInput.value = '';
        fetchCourses(1, '');
    });

    function init() {
        if (window.Auth && window.Auth.isAuthenticated !== undefined) updateButtonsByAuthAndRole();
        else document.addEventListener('auth-loaded', updateButtonsByAuthAndRole);
        fetchCourses(1, '');
    }
    init();
})();