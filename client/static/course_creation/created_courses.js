// static/course_creation/created_courses.js
(function() {
    const container = document.getElementById('coursesList');
    const addBtn = document.getElementById('addCourseBtn');

    let courses = [];
    let originalCourses = [];

    function showMessage(text, isError = false) {
        let msgDiv = document.getElementById('toastMessage');
        if (!msgDiv) {
            msgDiv = document.createElement('div');
            msgDiv.id = 'toastMessage';
            msgDiv.style.position = 'fixed';
            msgDiv.style.bottom = '20px';
            msgDiv.style.right = '20px';
            msgDiv.style.zIndex = '9999';
            msgDiv.style.padding = '12px 20px';
            msgDiv.style.borderRadius = '8px';
            msgDiv.style.backgroundColor = isError ? '#dc3545' : '#198754';
            msgDiv.style.color = 'white';
            msgDiv.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
            document.body.appendChild(msgDiv);
        }
        msgDiv.textContent = text;
        msgDiv.style.backgroundColor = isError ? '#dc3545' : '#198754';
        msgDiv.style.opacity = '1';
        setTimeout(() => {
            msgDiv.style.opacity = '0';
            setTimeout(() => msgDiv.remove(), 300);
        }, 2000);
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function truncateWords(text, wordLimit) {
        if (!text) return '';
        const words = text.trim().split(/\s+/);
        if (words.length <= wordLimit) return text;
        return words.slice(0, wordLimit).join(' ') + '…';
    }

    async function loadCourses() {
        try {
            const res = await fetch(`${window.API_BASE_URL}courses/controlled-courses?page=1&records_per_page=30`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            let coursesArray = Array.isArray(data) ? data : (data.items || []);
            courses = coursesArray.map(c => ({
                id: c.id,
                name: c.name,
                description: c.description || '',
                tags: c.tags || [],
                is_public: c.is_public !== undefined ? c.is_public : true,
                is_content_public: c.is_content_public !== undefined ? c.is_content_public : true
            }));
            originalCourses = JSON.parse(JSON.stringify(courses));
            renderCourses();
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="text-danger">Ошибка загрузки курсов: ${err.message}</div>`;
            courses = [];
            originalCourses = [];
            renderCourses();
        }
    }

    function renderCourses() {
        container.innerHTML = '';
        courses.forEach((course) => {
            const card = document.createElement('div');
            card.className = 'list-group-item list-group-item-action border mb-2 rounded';
            card.style.cursor = 'pointer';
            card.setAttribute('data-course-id', course.id);

            const shortDescription = truncateWords(course.description, 15);

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <strong>${escapeHtml(course.name)}</strong>
                        ${shortDescription ? `<div class="text-secondary small mt-1">${escapeHtml(shortDescription)}</div>` : ''}
                        ${course.tags && course.tags.length ? `<div class="small text-muted mt-1">Теги: ${course.tags.map(t => escapeHtml(t)).join(' ')}</div>` : ''}
                        <div class="small text-muted mt-1">
                            ${course.is_public ? 'Публичный' : 'Закрытый'} |
                            ${course.is_content_public ? 'Контент открыт' : 'Контент скрыт'}
                        </div>
                    </div>
                    <span class="text-secondary edit-course-trigger" style="cursor: pointer;">✎ редактировать</span>
                </div>
            `;

            const editTrigger = card.querySelector('.edit-course-trigger');
            editTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                openEditMode(course);
            });

            card.addEventListener('click', (e) => {
                if (card.querySelector('.save-course-edit, .cancel-edit, .delete-course')) {
                    e.stopPropagation();
                    return;
                }
                window.location.href = `/course/${course.id}/sections`;
            });

            container.appendChild(card);
        });
    }

    function openEditMode(course) {
        const card = container.querySelector(`.list-group-item[data-course-id="${course.id}"]`);
        if (!card) return;

        card.style.cursor = 'default';
        card.innerHTML = `
            <div class="p-2">
                <div class="mb-3">
                    <label class="form-label">Название курса</label>
                    <input type="text" class="form-control course-name-edit" value="${escapeHtml(course.name)}">
                </div>
                <div class="mb-3">
                    <label class="form-label">Описание</label>
                    <textarea class="form-control course-description-edit" rows="3">${escapeHtml(course.description || '')}</textarea>
                </div>

                <div class="mb-3">
                    <label class="form-label">Видимость курса</label>
                    <select class="form-select course-is-public-edit">
                        <option value="true" ${course.is_public ? 'selected' : ''}>Публичный (виден всем)</option>
                        <option value="false" ${!course.is_public ? 'selected' : ''}>Закрытый (только записанные)</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Видимость контента</label>
                    <select class="form-select course-is-content-public-edit">
                        <option value="true" ${course.is_content_public ? 'selected' : ''}>Открытый (доступен всем)</option>
                        <option value="false" ${!course.is_content_public ? 'selected' : ''}>Скрытый (только записанные)</option>
                    </select>
                </div>

                <div class="mb-3">
                    <label class="form-label">Теги</label>
                    <div id="tagsManagerPlaceholder-${course.id || 'new'}"></div>
                </div>

                <div class="d-flex justify-content-between align-items-center mt-3">
                    <button class="btn btn-danger delete-course">Удалить курс</button>
                    <div>
                        <button class="btn btn-outline-secondary cancel-edit me-2">Отмена</button>
                        <button class="btn btn-accent save-course-edit">Сохранить</button>
                    </div>
                </div>
            </div>
        `;

        const placeholderId = `tagsManagerPlaceholder-${course.id || 'new'}`;
        const placeholder = card.querySelector(`#${placeholderId}`);
        if (placeholder) {
            window.initTagManager(placeholder, course.tags);
        }

        const nameInput = card.querySelector('.course-name-edit');
        const descInput = card.querySelector('.course-description-edit');
        const isPublicSelect = card.querySelector('.course-is-public-edit');
        const isContentPublicSelect = card.querySelector('.course-is-content-public-edit');
        const saveBtn = card.querySelector('.save-course-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-course');

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            if (!newName) {
                showMessage('Название курса не может быть пустым', true);
                return;
            }
            const newDesc = descInput.value.trim();
            const newIsPublic = isPublicSelect.value === 'true';
            const newIsContentPublic = isContentPublicSelect.value === 'true';
            const newTags = [...course.tags];

            if (course.id) {
                try {
                    const res = await fetch(`${window.API_BASE_URL}courses/${course.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            name: newName,
                            description: newDesc,
                            tags: newTags,
                            is_public: newIsPublic,
                            is_content_public: newIsContentPublic
                        })
                    });
                    if (!res.ok) throw new Error('Ошибка обновления');
                    course.name = newName;
                    course.description = newDesc;
                    course.tags = newTags;
                    course.is_public = newIsPublic;
                    course.is_content_public = newIsContentPublic;
                    const orig = originalCourses.find(c => c.id === course.id);
                    if (orig) Object.assign(orig, course);
                    renderCourses();
                    showMessage('Курс обновлён');
                } catch (err) {
                    showMessage(err.message, true);
                }
            } else {
                try {
                    const res = await fetch(`${window.API_BASE_URL}courses/create-course`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            name: newName,
                            description: newDesc,
                            tags: newTags,
                            is_public: newIsPublic,
                            is_content_public: newIsContentPublic
                        })
                    });
                    if (!res.ok) throw new Error('Ошибка создания');
                    const data = await res.json();
                    course.id = data.id;
                    course.name = newName;
                    course.description = newDesc;
                    course.tags = newTags;
                    course.is_public = newIsPublic;
                    course.is_content_public = newIsContentPublic;
                    originalCourses.push({ ...course });
                    renderCourses();
                    showMessage('Курс создан');
                } catch (err) {
                    showMessage(err.message, true);
                }
            }
        });

        cancelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (course.id) {
                const orig = originalCourses.find(c => c.id === course.id);
                if (orig) Object.assign(course, orig);
                renderCourses();
            } else {
                const idx = courses.findIndex(c => c.id === null && c === course);
                if (idx !== -1) courses.splice(idx, 1);
                renderCourses();
            }
        });

        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!course.id) {
                const idx = courses.findIndex(c => c.id === null && c === course);
                if (idx !== -1) courses.splice(idx, 1);
                renderCourses();
                return;
            }
            if (!confirm('Удалить курс? Все разделы и материалы будут удалены.')) return;
            try {
                const res = await fetch(`${window.API_BASE_URL}courses/${course.id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (!res.ok) throw new Error('Ошибка удаления');
                const idx = courses.findIndex(c => c.id === course.id);
                if (idx !== -1) courses.splice(idx, 1);
                originalCourses = originalCourses.filter(c => c.id !== course.id);
                renderCourses();
                showMessage('Курс удалён');
            } catch (err) {
                showMessage(err.message, true);
            }
        });
    }

    function addCourse() {
        const newCourse = {
            id: null,
            name: '',
            description: '',
            tags: [],
            is_public: true,
            is_content_public: true
        };
        courses.unshift(newCourse);
        renderCourses();
        setTimeout(() => {
            const newCard = container.querySelector('.list-group-item:first-child');
            const editTrigger = newCard?.querySelector('.edit-course-trigger');
            if (editTrigger) editTrigger.click();
        }, 50);
    }

    addBtn.addEventListener('click', addCourse);
    loadCourses();
})();