// static/script.js
(function () {
    const coursesGrid = document.getElementById('coursesGrid');
    const searchInput = document.getElementById('searchInput');
    const filtersBtn = document.getElementById('filtersBtn');
    const myCoursesBtn = document.getElementById('myCoursesBtn');
    const manageCoursesBtn = document.getElementById('manageCoursesBtn');

    let currentPage = 1;
    let currentSearch = '';
    let currentFilterMode = 'all';
    let currentTagFilter = '';
    let currentProfessorFilter = '';
    let currentLimit = 9;
    let isLoading = false;
    let pagination = null;
    let allCoursesCache = [];

    // --- Управление видимостью кнопок ---
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

    // --- СОЗДАНИЕ ВЫПАДАЮЩЕГО ОКНА ФИЛЬТРОВ ---
    let filtersDropdown = null;
    let filtersWrapper = null;

    function createFiltersDropdown() {
        if (filtersDropdown) return;

        // Оборачиваем кнопку в относительный контейнер
        filtersWrapper = document.createElement('div');
        filtersWrapper.className = 'filters-wrapper';
        filtersWrapper.style.position = 'relative';
        filtersBtn.parentNode.insertBefore(filtersWrapper, filtersBtn);
        filtersWrapper.appendChild(filtersBtn);

        const dropdown = document.createElement('div');
        dropdown.className = 'filters-dropdown';
        dropdown.style.display = 'none'; // изначально скрыто
        dropdown.innerHTML = `
            <div class="filter-group mb-3">
                <label class="form-label fw-bold">Статус участия</label>
                <select id="filterStatusSelect" class="form-select form-select-sm">
                    <option value="all">Все курсы</option>
                    <option value="enrolled">Только записанные</option>
                    <option value="controlled">Только преподаваемые</option>
                    <option value="enrollable">Только можно записаться</option>
                </select>
            </div>
            <div class="filter-group mb-3">
                <label class="form-label fw-bold">Тег (точное совпадение)</label>
                <input type="text" id="filterTagInput" class="form-control form-control-sm" placeholder="например: программирование">
            </div>
            <div class="filter-group mb-3">
                <label class="form-label fw-bold">Преподаватель</label>
                <select id="filterProfessorSelect" class="form-select form-select-sm">
                    <option value="">Все преподаватели</option>
                </select>
            </div>
            <div class="filter-group mb-3">
                <label class="form-label fw-bold">Курсов на странице</label>
                <select id="filterLimitSelect" class="form-select form-select-sm">
                    <option value="6">6</option>
                    <option value="9" selected>9</option>
                    <option value="15">15</option>
                    <option value="30">30</option>
                </select>
            </div>
            <div class="d-flex justify-content-between gap-2 mt-2">
                <button id="resetFiltersBtn" class="btn btn-sm btn-outline-secondary">Сбросить</button>
                <button id="applyFiltersBtn" class="btn btn-sm btn-primary">Применить</button>
            </div>
        `;
        filtersWrapper.appendChild(dropdown);
        filtersDropdown = dropdown;

        // Закрытие при клике вне
        document.addEventListener('click', (e) => {
            if (!filtersWrapper.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Открытие/закрытие по кнопке
        filtersBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = dropdown.style.display === 'block';
            dropdown.style.display = isVisible ? 'none' : 'block';
            if (!isVisible) {
                updateProfessorFilterList();
                document.getElementById('filterStatusSelect').value = currentFilterMode;
                document.getElementById('filterTagInput').value = currentTagFilter;
                document.getElementById('filterLimitSelect').value = currentLimit;
            }
        });

        document.getElementById('resetFiltersBtn').addEventListener('click', () => {
            document.getElementById('filterStatusSelect').value = 'all';
            document.getElementById('filterTagInput').value = '';
            document.getElementById('filterProfessorSelect').value = '';
            document.getElementById('filterLimitSelect').value = '9';
            applyFiltersAndFetch();
        });
        document.getElementById('applyFiltersBtn').addEventListener('click', applyFiltersAndFetch);
    }

    function updateProfessorFilterList() {
        const select = document.getElementById('filterProfessorSelect');
        if (!select) return;
        const professors = new Map();
        if (Array.isArray(allCoursesCache)) {
            allCoursesCache.forEach(course => {
                if (course.professor_id && course.professor_surname) {
                    const fullName = `${course.professor_surname} ${course.professor_name} ${course.professor_patronymic || ''}`.trim();
                    professors.set(course.professor_id, fullName);
                }
            });
        }
        const currentVal = select.value;
        select.innerHTML = '<option value="">Все преподаватели</option>';
        for (let [id, name] of professors) {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = name;
            if (id === currentVal) option.selected = true;
            select.appendChild(option);
        }
    }

    function applyFiltersAndFetch() {
        currentFilterMode = document.getElementById('filterStatusSelect').value;
        currentTagFilter = document.getElementById('filterTagInput').value.trim();
        currentProfessorFilter = document.getElementById('filterProfessorSelect').value;
        const newLimit = parseInt(document.getElementById('filterLimitSelect').value, 10);

        if (currentFilterMode !== 'enrollable') {
            if (newLimit !== currentLimit) {
                currentLimit = newLimit;
                if (pagination) pagination.destroy();
                if (paginationContainer && window.Pagination) {
                    pagination = new window.Pagination(paginationContainer, (page) => fetchCourses(page), {pageSize: currentLimit});
                }
            }
        }
        if (searchInput) searchInput.value = '';
        currentSearch = '';
        fetchCourses(1);
        filtersDropdown.style.display = 'none';
    }

    // --- Загрузка всех страниц для режима "Только можно записаться" ---
    async function fetchAllEnrollableCourses() {
        let allCourses = [];
        let page = 1;
        const perPage = 30;
        let hasMore = true;
        while (hasMore) {
            const url = `${window.API_BASE_URL}courses/search?page=${page}&records_per_page=${perPage}&criteria=name_prefix&value=`;
            try {
                const response = await fetch(url, {credentials: 'include'});
                if (!response.ok) break;
                const coursesChunk = await response.json();
                const chunkArray = Array.isArray(coursesChunk) ? coursesChunk : [];
                allCourses = allCourses.concat(chunkArray);
                hasMore = chunkArray.length === perPage;
                page++;
                if (page > 10) break;
            } catch (err) {
                console.warn('Ошибка при загрузке страницы курсов', err);
                break;
            }
        }
        return allCourses.filter(c => c.state === 'enrollable');
    }

    // --- ОСНОВНАЯ ФУНКЦИЯ ЗАГРУЗКИ КУРСОВ ---
    async function fetchCourses(page = 1) {
        if (isLoading) return;
        isLoading = true;
        coursesGrid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-accent" role="status"></div></div>';

        try {
            let courses = [];
            let hasNext = false;

            if (currentFilterMode === 'enrolled') {
                const response = await fetch(`${window.API_BASE_URL}courses/followed-courses?page=${page}&records_per_page=${currentLimit}`, {credentials: 'include'});
                if (response.status === 401 || response.status === 403) {
                    window.showAccessDenied(coursesGrid, 'Вы не авторизованы или доступ запрещён.', true, pagination);
                    isLoading = false;
                    return;
                }
                if (!response.ok) throw new Error('Ошибка загрузки записанных курсов');
                const data = await response.json();
                courses = Array.isArray(data) ? data : [];
                hasNext = courses.length === currentLimit;
                if (pagination) pagination.show();
            } else if (currentFilterMode === 'controlled') {
                const response = await fetch(`${window.API_BASE_URL}courses/controlled-courses?page=${page}&records_per_page=${currentLimit}`, {credentials: 'include'});
                if (response.status === 401 || response.status === 403) {
                    window.showAccessDenied(coursesGrid, 'Вы не авторизованы или доступ запрещён.', true, pagination);
                    isLoading = false;
                    return;
                }
                if (!response.ok) throw new Error('Ошибка загрузки преподаваемых курсов');
                const data = await response.json();
                courses = Array.isArray(data) ? data : [];
                hasNext = courses.length === currentLimit;
                if (pagination) pagination.show();
            } else if (currentFilterMode === 'enrollable') {
                courses = await fetchAllEnrollableCourses();
                if (pagination) pagination.hide();
            } else { // Режим 'all'
                let url;
                if (currentTagFilter) {
                    url = `${window.API_BASE_URL}courses/search?page=${page}&records_per_page=${currentLimit}&criteria=tag&value=${encodeURIComponent(currentTagFilter)}`;
                } else {
                    url = `${window.API_BASE_URL}courses/search?page=${page}&records_per_page=${currentLimit}&criteria=name_prefix&value=${encodeURIComponent(currentSearch)}`;
                }
                const response = await fetch(url, {credentials: 'include'});
                if (!response.ok) {
                    // Для неавторизованных или при ошибке бэкенда показываем пустой список
                    if (response.status === 401 || response.status === 403) {
                        console.warn('Доступ к поиску курсов ограничен, показываем пустой список');
                        courses = [];
                        hasNext = false;
                    } else {
                        throw new Error(`Ошибка загрузки курсов: ${response.status}`);
                    }
                } else {
                    const data = await response.json();
                    courses = Array.isArray(data) ? data : [];
                    hasNext = courses.length === currentLimit;
                }
                if (pagination) pagination.show();
            }

            allCoursesCache = courses;
            if (currentProfessorFilter && currentFilterMode !== 'enrollable') {
                courses = courses.filter(c => c.professor_id === currentProfessorFilter);
            }

            renderCourses(courses);

            if (currentFilterMode !== 'enrollable') {
                const total = hasNext ? page + 1 : page;
                if (pagination) {
                    pagination.setTotalPages(total);
                    pagination.setPage(page, true);
                }
                currentPage = page;
            } else {
                currentPage = 1;
            }
        } catch (error) {
            console.error(error);
            coursesGrid.innerHTML = `<p class="text-center text-danger">${error.message}</p>`;
            if (pagination) pagination.hide();
        } finally {
            isLoading = false;
        }
    }

    function formatProfessorFullName(course) {
        const parts = [course.professor_surname, course.professor_name, course.professor_patronymic].filter(p => p);
        return parts.join(' ') || '—';
    }

    function renderCourses(courses) {
        if (!coursesGrid) return;
        if (!Array.isArray(courses) || courses.length === 0) {
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
            const professorFullName = formatProfessorFullName(course);

            col.innerHTML = `
                <div class="course-card position-relative d-flex flex-column h-100">
                    <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                         class="course-icon"
                         alt="Иконка курса">
                    <a href="/course/${course.id}" class="stretched-link text-decoration-none">
                        <h5 class="course-title mt-2">${escapeHtml(course.name)}</h5>
                        <div class="course-instructor small text-secondary mb-1">Преподаватель: ${escapeHtml(professorFullName)}</div>
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

    // --- ПАГИНАЦИЯ ---
    const paginationContainer = document.getElementById('paginationContainer');
    if (paginationContainer && window.Pagination) {
        pagination = new window.Pagination(paginationContainer, (page) => fetchCourses(page), {pageSize: currentLimit});
    }

    // --- ПОИСК ПО НАЗВАНИЮ ---
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            searchTimeout = setTimeout(() => {
                currentFilterMode = 'all';
                currentTagFilter = '';
                currentProfessorFilter = '';
                currentSearch = query;
                if (filtersDropdown) {
                    const statusSelect = document.getElementById('filterStatusSelect');
                    if (statusSelect) statusSelect.value = 'all';
                    const tagInput = document.getElementById('filterTagInput');
                    if (tagInput) tagInput.value = '';
                    const profSelect = document.getElementById('filterProfessorSelect');
                    if (profSelect) profSelect.value = '';
                }
                if (pagination) pagination.show();
                fetchCourses(1);
            }, 400);
        });
    }

    // --- КНОПКИ ---
    if (myCoursesBtn) myCoursesBtn.addEventListener('click', () => window.location.href = '/my-courses');
    if (manageCoursesBtn) manageCoursesBtn.addEventListener('click', () => window.location.href = '/created-courses');

    // --- ПОДПИСКА НА ИЗМЕНЕНИЕ АВТОРИЗАЦИИ ---
    window.addEventListener('auth-changed', () => {
        updateButtonsByAuthAndRole();
        currentFilterMode = 'all';
        currentTagFilter = '';
        currentProfessorFilter = '';
        currentSearch = '';
        if (searchInput) searchInput.value = '';
        if (pagination) pagination.show();
        fetchCourses(1);
    });

    // --- ИНИЦИАЛИЗАЦИЯ ---
    function init() {
        createFiltersDropdown();
        if (window.Auth && window.Auth.isAuthenticated !== undefined) updateButtonsByAuthAndRole();
        else document.addEventListener('auth-loaded', updateButtonsByAuthAndRole);
        fetchCourses(1);
    }

    init();
})();