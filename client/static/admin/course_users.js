// static/admin/course_users.js
(function() {
    const courseId = window.COURSE_ID;
    const notEnrolledContainer = document.getElementById('notEnrolledList');
    const enrolledContainer = document.getElementById('enrolledList');
    const enrollSelectedBtn = document.getElementById('enrollSelectedBtn');
    const unenrollSelectedBtn = document.getElementById('unenrollSelectedBtn');
    const backBtn = document.getElementById('backBtn');
    const courseNameSpan = document.getElementById('courseName');
    const professorInfoSpan = document.getElementById('professorInfo');

    // Элементы пагинации для левого списка
    const notEnrolledPrev = document.getElementById('notEnrolledPrevBtn');
    const notEnrolledNext = document.getElementById('notEnrolledNextBtn');
    const notEnrolledPageInfo = document.getElementById('notEnrolledPageInfo');
    // Для правого списка
    const enrolledPrev = document.getElementById('enrolledPrevBtn');
    const enrolledNext = document.getElementById('enrolledNextBtn');
    const enrolledPageInfo = document.getElementById('enrolledPageInfo');

    const PAGE_SIZE = 9;

    let allUsers = [];
    let enrolledUsers = [];
    let notEnrolledUsers = [];
    let courseProfessorId = null;
    let courseProfessorName = '';

    let notEnrolledPage = 1;
    let enrolledPage = 1;
    let notEnrolledTotalPages = 1;
    let enrolledTotalPages = 1;

    let isLoading = false;

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Загрузка информации о курсе (название и преподаватель)
    async function loadCourseInfo() {
        try {
            const resp = await fetch(`${window.API_BASE_URL}courses/${courseId}`, { credentials: 'include' });
            if (resp.ok) {
                const course = await resp.json();
                courseNameSpan.textContent = course.name;
                courseProfessorId = course.professor_id;
                const professorFullName = `${course.professor_surname} ${course.professor_name} ${course.professor_patronymic || ''}`.trim();
                courseProfessorName = professorFullName || course.professor_id;
                professorInfoSpan.innerHTML = `<small>Преподаватель курса: <strong>${escapeHtml(courseProfessorName)}</strong></small>`;
            } else {
                courseNameSpan.textContent = 'Курс';
                professorInfoSpan.innerHTML = '<small class="text-danger">Не удалось загрузить информацию о преподавателе</small>';
            }
        } catch(e) {
            console.error(e);
            courseNameSpan.textContent = 'Курс';
        }
    }

    // Загрузка всех пользователей (кроме преподавателя курса)
    async function loadAllUsers() {
        try {
            const resp = await fetch(`${window.API_BASE_URL}users/all?page=1&records_per_page=30`, {
                credentials: 'include'
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            let users = await resp.json();
            users = Array.isArray(users) ? users : [];
            // Исключаем преподавателя курса из общего списка (чтобы он не попал в "Не записаны")
            if (courseProfessorId) {
                users = users.filter(u => u.id !== courseProfessorId);
            }
            allUsers = users;
        } catch (err) {
            console.error('Ошибка загрузки пользователей:', err);
            allUsers = [];
            notEnrolledContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки пользователей: ${err.message}</div>`;
        }
    }

    // Загрузка списка записанных на курс пользователей (исключая преподавателя)
    async function loadEnrolledUsers() {
        try {
            const resp = await fetch(`${window.API_BASE_URL}users/enrolled-users/${courseId}`, {
                credentials: 'include'
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            let users = await resp.json();
            users = Array.isArray(users) ? users : [];
            // Исключаем преподавателя из списка записанных (он там не должен быть, но на всякий случай)
            if (courseProfessorId) {
                users = users.filter(u => u.id !== courseProfessorId);
            }
            enrolledUsers = users;
        } catch (err) {
            console.error('Ошибка загрузки записанных пользователей:', err);
            enrolledUsers = [];
            enrolledContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки записанных: ${err.message}</div>`;
        }
    }

    // Вычисление разности: все пользователи (исключая преподавателя) минус записанные
    function computeNotEnrolled() {
        const enrolledIds = new Set(enrolledUsers.map(u => u.id));
        notEnrolledUsers = allUsers.filter(user => !enrolledIds.has(user.id));
        notEnrolledTotalPages = Math.ceil(notEnrolledUsers.length / PAGE_SIZE) || 1;
        if (notEnrolledPage > notEnrolledTotalPages) notEnrolledPage = notEnrolledTotalPages;
        renderNotEnrolledList();
        updateNotEnrolledPagination();
    }

    function renderNotEnrolledList() {
        if (!notEnrolledContainer) return;
        const start = (notEnrolledPage - 1) * PAGE_SIZE;
        const pageUsers = notEnrolledUsers.slice(start, start + PAGE_SIZE);

        if (pageUsers.length === 0 && notEnrolledUsers.length === 0) {
            notEnrolledContainer.innerHTML = '<div class="text-muted p-3">Нет пользователей для записи</div>';
            return;
        }
        if (pageUsers.length === 0 && notEnrolledUsers.length > 0) {
            if (notEnrolledPage > 1) notEnrolledPage--;
            renderNotEnrolledList();
            return;
        }

        notEnrolledContainer.innerHTML = '';
        pageUsers.forEach(user => {
            const div = document.createElement('div');
            div.className = 'list-group-item d-flex justify-content-between align-items-center';
            div.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input user-checkbox" type="checkbox" value="${user.id}" data-list="not-enrolled">
                    <label class="form-check-label">${escapeHtml(user.nickname)} (${escapeHtml(user.email || 'нет email')})</label>
                </div>
                <button class="btn btn-sm btn-success single-action-btn" data-user-id="${user.id}" data-action="enroll">Записать</button>
            `;
            const btn = div.querySelector('.single-action-btn');
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                await performAction(user.id, 'enroll');
            });
            notEnrolledContainer.appendChild(div);
        });
    }

    function renderEnrolledList() {
        if (!enrolledContainer) return;
        const start = (enrolledPage - 1) * PAGE_SIZE;
        const pageUsers = enrolledUsers.slice(start, start + PAGE_SIZE);

        if (pageUsers.length === 0 && enrolledUsers.length === 0) {
            enrolledContainer.innerHTML = '<div class="text-muted p-3">Нет записанных пользователей</div>';
            return;
        }
        if (pageUsers.length === 0 && enrolledUsers.length > 0) {
            if (enrolledPage > 1) enrolledPage--;
            renderEnrolledList();
            return;
        }

        enrolledContainer.innerHTML = '';
        pageUsers.forEach(user => {
            const div = document.createElement('div');
            div.className = 'list-group-item d-flex justify-content-between align-items-center';
            div.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input user-checkbox" type="checkbox" value="${user.id}" data-list="enrolled">
                    <label class="form-check-label">${escapeHtml(user.nickname)} (${escapeHtml(user.email || 'нет email')})</label>
                </div>
                <button class="btn btn-sm btn-danger single-action-btn" data-user-id="${user.id}" data-action="unenroll">Отписать</button>
            `;
            const btn = div.querySelector('.single-action-btn');
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                await performAction(user.id, 'unenroll');
            });
            enrolledContainer.appendChild(div);
        });
    }

    function updateNotEnrolledPagination() {
        if (notEnrolledPrev) notEnrolledPrev.disabled = notEnrolledPage <= 1;
        if (notEnrolledNext) notEnrolledNext.disabled = notEnrolledPage >= notEnrolledTotalPages;
        if (notEnrolledPageInfo) {
            notEnrolledPageInfo.textContent = `Страница ${notEnrolledPage} из ${notEnrolledTotalPages}`;
        }
    }

    function updateEnrolledPagination() {
        if (enrolledPrev) enrolledPrev.disabled = enrolledPage <= 1;
        if (enrolledNext) enrolledNext.disabled = enrolledPage >= enrolledTotalPages;
        if (enrolledPageInfo) {
            enrolledPageInfo.textContent = `Страница ${enrolledPage} из ${enrolledTotalPages}`;
        }
    }

    function goNotEnrolledPrev() {
        if (notEnrolledPage > 1) {
            notEnrolledPage--;
            renderNotEnrolledList();
            updateNotEnrolledPagination();
        }
    }
    function goNotEnrolledNext() {
        if (notEnrolledPage < notEnrolledTotalPages) {
            notEnrolledPage++;
            renderNotEnrolledList();
            updateNotEnrolledPagination();
        }
    }
    function goEnrolledPrev() {
        if (enrolledPage > 1) {
            enrolledPage--;
            renderEnrolledList();
            updateEnrolledPagination();
        }
    }
    function goEnrolledNext() {
        if (enrolledPage < enrolledTotalPages) {
            enrolledPage++;
            renderEnrolledList();
            updateEnrolledPagination();
        }
    }

    async function performAction(userId, action) {
        const isEnroll = action === 'enroll';
        const url = isEnroll
            ? `${window.API_BASE_URL}users/enroll?user_id=${userId}&course_id=${courseId}`
            : `${window.API_BASE_URL}users/unenroll?user_id=${userId}&course_id=${courseId}`;
        const method = isEnroll ? 'POST' : 'DELETE';

        try {
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            if (res.ok) {
                window.showToast(isEnroll ? 'Пользователь записан' : 'Пользователь отписан');
                await loadDataAndRender();
            } else if (res.status === 409) {
                window.showToast(isEnroll ? 'Пользователь уже записан на курс' : 'Пользователь не был записан', 'warning');
            } else {
                const text = await res.text();
                window.showToast(`Ошибка: ${text}`, 'danger');
            }
        } catch (err) {
            console.error(err);
            window.showToast(`Ошибка сети: ${err.message}`, 'danger');
        }
    }

    async function performBulk(action) {
        const listType = action === 'enroll' ? 'not-enrolled' : 'enrolled';
        const checkboxes = document.querySelectorAll(`.user-checkbox[data-list="${listType}"]:checked`);
        const userIds = Array.from(checkboxes).map(cb => cb.value);
        if (!userIds.length) {
            window.showToast('Выберите хотя бы одного пользователя', 'warning');
            return;
        }
        const isEnroll = action === 'enroll';
        let successCount = 0;
        for (const userId of userIds) {
            const url = isEnroll
                ? `${window.API_BASE_URL}users/enroll?user_id=${userId}&course_id=${courseId}`
                : `${window.API_BASE_URL}users/unenroll?user_id=${userId}&course_id=${courseId}`;
            const method = isEnroll ? 'POST' : 'DELETE';
            try {
                const res = await fetch(url, { method, credentials: 'include' });
                if (res.ok) successCount++;
                else if (res.status !== 409) console.warn(`Failed for ${userId}`);
            } catch(e) { console.warn(e); }
        }
        window.showToast(`Выполнено: ${successCount} из ${userIds.length}`, successCount === userIds.length ? 'success' : 'warning');
        if (successCount > 0) {
            await loadDataAndRender();
        }
    }

    async function loadDataAndRender() {
        if (isLoading) return;
        isLoading = true;
        try {
            await Promise.all([loadAllUsers(), loadEnrolledUsers()]);
            computeNotEnrolled();
            enrolledTotalPages = Math.ceil(enrolledUsers.length / PAGE_SIZE) || 1;
            if (enrolledPage > enrolledTotalPages) enrolledPage = enrolledTotalPages;
            renderEnrolledList();
            updateEnrolledPagination();
        } catch (err) {
            console.error(err);
        } finally {
            isLoading = false;
        }
    }

    function bindEvents() {
        if (notEnrolledPrev) notEnrolledPrev.addEventListener('click', goNotEnrolledPrev);
        if (notEnrolledNext) notEnrolledNext.addEventListener('click', goNotEnrolledNext);
        if (enrolledPrev) enrolledPrev.addEventListener('click', goEnrolledPrev);
        if (enrolledNext) enrolledNext.addEventListener('click', goEnrolledNext);
        if (enrollSelectedBtn) enrollSelectedBtn.addEventListener('click', () => performBulk('enroll'));
        if (unenrollSelectedBtn) unenrollSelectedBtn.addEventListener('click', () => performBulk('unenroll'));
        if (backBtn) backBtn.addEventListener('click', () => window.location.href = '/admin/courses');
    }

    async function init() {
        bindEvents();
        await loadCourseInfo();
        await loadDataAndRender();
    }

    init();
})();