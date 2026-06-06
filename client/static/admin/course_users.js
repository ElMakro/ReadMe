// static/admin/course_users.js
(function() {
    const courseId = window.COURSE_ID;
    const notEnrolledContainer = document.getElementById('notEnrolledList');
    const enrolledContainer = document.getElementById('enrolledList');
    const enrollSelectedBtn = document.getElementById('enrollSelectedBtn');
    const unenrollSelectedBtn = document.getElementById('unenrollSelectedBtn');
    const backBtn = document.getElementById('backBtn');
    const courseNameSpan = document.getElementById('courseName');

    let allUsers = [];

    async function loadCourseName() {
        try {
            const resp = await fetch(`${window.API_BASE_URL}courses/${courseId}`, { credentials: 'include' });
            if (resp.ok) {
                const course = await resp.json();
                courseNameSpan.textContent = course.name;
            } else {
                courseNameSpan.textContent = 'Курс';
            }
        } catch(e) {
            console.error(e);
        }
    }

    async function loadAllUsers() {
        try {
            const resp = await fetch(`${window.API_BASE_URL}users/all`, { credentials: 'include' });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const users = await resp.json();
            allUsers = Array.isArray(users) ? users : [];
            renderLists();
        } catch (err) {
            console.error(err);
            notEnrolledContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки пользователей: ${err.message}</div>`;
            enrolledContainer.innerHTML = '';
        }
    }

    function renderLists() {
        notEnrolledContainer.innerHTML = '';
        enrolledContainer.innerHTML = '';

        if (!allUsers.length) {
            notEnrolledContainer.innerHTML = '<div class="text-muted p-3">Нет пользователей</div>';
            enrolledContainer.innerHTML = '<div class="text-muted p-3">Нет пользователей</div>';
            return;
        }

        allUsers.forEach(user => {
            // Блок "Не записаны" – показываем всех
            const notEnrolledItem = createUserItem(user, 'not-enrolled');
            notEnrolledContainer.appendChild(notEnrolledItem);

            // Блок "Записаны" – тоже всех (заглушка)
            const enrolledItem = createUserItem(user, 'enrolled');
            enrolledContainer.appendChild(enrolledItem);
        });
    }

    function createUserItem(user, listType) {
        const div = document.createElement('div');
        div.className = 'list-group-item d-flex justify-content-between align-items-center';
        div.innerHTML = `
            <div class="form-check">
                <input class="form-check-input user-checkbox" type="checkbox" value="${user.id}" data-list="${listType}">
                <label class="form-check-label">${escapeHtml(user.nickname)} (${escapeHtml(user.email || 'нет email')})</label>
            </div>
            <button class="btn btn-sm ${listType === 'not-enrolled' ? 'btn-success' : 'btn-danger'} single-action-btn" data-user-id="${user.id}" data-action="${listType === 'not-enrolled' ? 'enroll' : 'unenroll'}">
                ${listType === 'not-enrolled' ? 'Записать' : 'Отписать'}
            </button>
        `;
        const btn = div.querySelector('.single-action-btn');
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const action = btn.dataset.action;
            const userId = btn.dataset.userId;
            await performAction(userId, action);
        });
        return div;
    }

    async function performAction(userId, action) {
        const url = action === 'enroll'
            ? `${window.API_BASE_URL}users/enroll`
            : `${window.API_BASE_URL}users/unenroll`;

        // Пробуем два варианта тела запроса (student_id или user_id)
        const bodyVariants = [
            { student_id: userId, course_id: courseId },
            { user_id: userId, course_id: courseId },
            { id: userId, course_id: courseId }
        ];

        let lastError = null;
        for (const body of bodyVariants) {
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(body)
                });
                if (res.ok) {
                    window.showToast(action === 'enroll' ? 'Пользователь записан' : 'Пользователь отписан');
                    // Перезагружаем страницу, чтобы сбросить состояние (временное решение)
                    setTimeout(() => location.reload(), 1000);
                    return;
                } else {
                    const errorText = await res.text();
                    lastError = `HTTP ${res.status}: ${errorText}`;
                    console.warn(`Попытка с телом ${JSON.stringify(body)} не удалась:`, errorText);
                }
            } catch (err) {
                lastError = err.message;
            }
        }
        window.showToast(`Не удалось ${action === 'enroll' ? 'записать' : 'отписать'}: ${lastError}`, 'danger');
    }

    async function performBulk(action) {
        const listType = action === 'enroll' ? 'not-enrolled' : 'enrolled';
        const checkboxes = document.querySelectorAll(`.user-checkbox[data-list="${listType}"]:checked`);
        const userIds = Array.from(checkboxes).map(cb => cb.value);
        if (!userIds.length) {
            window.showToast('Выберите хотя бы одного пользователя', 'warning');
            return;
        }
        const url = action === 'enroll'
            ? `${window.API_BASE_URL}users/enroll`
            : `${window.API_BASE_URL}users/unenroll`;

        let successCount = 0;
        for (const userId of userIds) {
            // Пробуем тот же перебор вариантов тела
            let ok = false;
            for (const body of [{ student_id: userId, course_id: courseId }, { user_id: userId, course_id: courseId }, { id: userId, course_id: courseId }]) {
                try {
                    const res = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify(body)
                    });
                    if (res.ok) {
                        ok = true;
                        break;
                    }
                } catch(e) {}
            }
            if (ok) successCount++;
        }
        window.showToast(`Выполнено: ${successCount} из ${userIds.length}`, successCount === userIds.length ? 'success' : 'warning');
        if (successCount > 0) setTimeout(() => location.reload(), 1500);
    }

    enrollSelectedBtn.addEventListener('click', () => performBulk('enroll'));
    unenrollSelectedBtn.addEventListener('click', () => performBulk('unenroll'));
    backBtn.addEventListener('click', () => window.location.href = '/admin/courses');

    loadCourseName();
    loadAllUsers();

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
})();