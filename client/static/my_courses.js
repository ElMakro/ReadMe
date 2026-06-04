// static/my_courses.js
(function() {
    const grid = document.getElementById('myCoursesGrid');
    let currentPage = 1;
    const limit = 9;
    let isLoading = false;

    // Создаём пагинацию внутри header-контейнера
    function createPagination() {
        const container = document.getElementById('paginationControls');
        if (!container || container.children.length > 0) return;
        container.innerHTML = `
            <button class="pagination-btn" id="prevPageBtn" disabled>← Предыдущий</button>
            <span id="pageInfo" class="text-muted">Страница 1</span>
            <button class="pagination-btn" id="nextPageBtn">Следующий →</button>
        `;
    }

    async function fetchMyCourses(page = 1) {
        if (isLoading) return;
        isLoading = true;
        grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>';

        const params = new URLSearchParams();
        params.append('page', page);
        params.append('records_per_page', limit);

        try {
            const response = await fetch(`${window.API_BASE_URL}courses/followed-courses?${params.toString()}`, {
                credentials: 'include'
            });
            if (!response.ok) {
                if (response.status === 401) {
                    grid.innerHTML = '<div class="col-12 text-center">Вы не авторизованы. <a href="#" id="loginLink">Войдите</a></div>';
                    const loginLink = document.getElementById('loginLink');
                    if (loginLink) loginLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        if (window.AuthModal) window.AuthModal.open();
                    });
                    return;
                }
                throw new Error('Ошибка загрузки курсов');
            }
            const data = await response.json();
            const courses = Array.isArray(data) ? data : (data.courses || []);
            const hasNext = courses.length === limit;
            renderCourses(courses);
            updatePagination(page, hasNext);
            currentPage = page;
        } catch (error) {
            console.error(error);
            grid.innerHTML = '<div class="col-12 text-center text-danger">Не удалось загрузить курсы</div>';
            updatePagination(1, false);
        } finally {
            isLoading = false;
        }
    }

    function renderCourses(courses) {
        if (!courses.length) {
            // Текст строго в одну строку без переноса (даже на мобилках)
            grid.innerHTML = `
                <div class="col-12 text-center py-4">
                    <div class="empty-message">
                        <span>Вы пока не записаны ни на один курс.</span>
                    </div>
                </div>
            `;
            return;
        }

        grid.innerHTML = '';
        courses.forEach(course => {
            const col = document.createElement('div');
            col.className = 'col';
            const title = course.name || 'Без названия';
            const description = course.description || 'Описание отсутствует';
            const shortDesc = description.length > 100 ? description.substring(0, 100) + '…' : description;

            col.innerHTML = `
                <div class="course-card position-relative">
                    <a href="/course/${course.id}" class="stretched-link text-decoration-none">
                        <h5 class="course-title">${escapeHtml(title)}</h5>
                        <div class="course-state mb-2">
                            <span class="badge bg-success">Записан</span>
                        </div>
                        <p class="course-description">${escapeHtml(shortDesc)}</p>
                    </a>
                </div>
            `;
            grid.appendChild(col);
        });
    }

    function updatePagination(page, hasNext) {
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const pageInfo = document.getElementById('pageInfo');
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = !hasNext;
        if (pageInfo) pageInfo.textContent = `Страница ${page}`;
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function init() {
        createPagination();
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1 && !isLoading) fetchMyCourses(currentPage - 1); });
        if (nextBtn) nextBtn.addEventListener('click', () => { if (!nextBtn.disabled && !isLoading) fetchMyCourses(currentPage + 1); });
        fetchMyCourses(1);
    }

    init();
})();