// static/my_courses.js
(function() {
    const grid = document.getElementById('myCoursesGrid');
    let pagination = null;
    let isLoading = false;
    const limit = 9;

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function fetchMyCourses(page) {
        if (isLoading) return;
        isLoading = true;
        grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>';
        const params = new URLSearchParams({ page, records_per_page: limit });
        try {
            const response = await fetch(`${window.API_BASE_URL}courses/followed-courses?${params}`, { credentials: 'include' });
            if (response.status === 401 || response.status === 403) {
                window.showAccessDenied(grid, 'Вы не авторизованы или доступ запрещён.', true, pagination);
                isLoading = false;
                return;
            }
            if (!response.ok) {
                if (response.status === 422) throw new Error('Ошибка валидации параметров');
                throw new Error('Ошибка загрузки курсов');
            }
            const data = await response.json();
            const courses = Array.isArray(data) ? data : (data.courses || []);
            renderCourses(courses);
            const hasNext = courses.length === limit;
            const total = hasNext ? page + 1 : page;
            if (pagination) {
                pagination.setTotalPages(total);
                pagination.setPage(page, true);
            }
        } catch (error) {
            grid.innerHTML = `<div class="col-12 text-center text-danger">${error.message}</div>`;
            if (pagination) pagination.hide();
        } finally {
            isLoading = false;
        }
    }

    function renderCourses(courses) {
        if (!courses.length) {
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
                <div class="course-card position-relative d-flex flex-column h-100">
                    <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                         class="course-icon"
                         alt="Иконка курса">
                    <a href="/course/${course.id}" class="stretched-link text-decoration-none">
                        <h5 class="course-title mt-2">${escapeHtml(title)}</h5>
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

    function init() {
        const paginationContainer = document.getElementById('paginationContainer');
        if (paginationContainer) {
            pagination = new Pagination(paginationContainer, (page) => fetchMyCourses(page), { pageSize: limit });
        }
        fetchMyCourses(1);
    }
    init();
})();