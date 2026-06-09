// static/course_creation/created_courses.js
(function() {
    const container = document.getElementById('coursesList');
    const addBtn = document.getElementById('addCourseBtn');

    let courses = [];
    let originalCourses = [];

    // Временное хранилище выбранного файла иконки для редактируемого курса
    let selectedIconFile = null;
    let currentEditingCourseId = null;

    function autosize(textarea) {
        textarea.style.height = 'auto';
        const maxHeight = 200;
        const newHeight = Math.min(textarea.scrollHeight, maxHeight);
        textarea.style.height = newHeight + 'px';
        textarea.style.overflowY = (textarea.scrollHeight > maxHeight) ? 'auto' : 'hidden';
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
                <div class="course-item-container">
                    <div class="course-item-info">
                        <div class="d-flex align-items-start gap-3">
                            <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                                 class="course-thumb">
                            <div class="course-details">
                                <strong class="course-name">${escapeHtml(course.name)}</strong>
                                ${shortDescription ? `<div class="text-secondary small mt-1">${escapeHtml(shortDescription)}</div>` : ''}
                                ${course.tags && course.tags.length ? `<div class="small text-muted mt-1">Теги: ${course.tags.map(t => escapeHtml(t)).join(' ')}</div>` : ''}
                                <div class="small text-muted mt-1">
                                    ${course.is_public ? 'Публичный' : 'Закрытый'} |
                                    ${course.is_content_public ? 'Контент открыт' : 'Контент скрыт'}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="course-item-actions">
                        <span class="text-secondary edit-course-trigger">✎ редактировать</span>
                    </div>
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
        selectedIconFile = null;
        currentEditingCourseId = course.id;
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
                    <textarea class="form-control course-description-edit" placeholder="Введите описание курса">${escapeHtml(course.description || '')}</textarea>
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
                
                <!-- Блок выбора иконки курса (одна кнопка, загрузка при сохранении) -->
                <div class="mb-3">
                    <label class="form-label">Иконка курса</label>
                    <div class="d-flex align-items-center gap-3">
                        <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                             class="current-course-icon rounded"
                             width="64" height="64"
                             style="object-fit: cover; border-radius: 16px;"
                        <div>
                            <button type="button" class="btn btn-outline-accent select-icon-btn">Выбрать файл</button>
                            <span class="ms-2 text-muted icon-filename"></span>
                        </div>
                        <input type="file" class="d-none" id="iconFileInput-${course.id}" accept="image/*">
                    </div>
                </div>

                <div class="d-flex justify-content-between align-items-center mt-3">
                    <button class="btn btn-danger delete-course">Удалить курс</button>
                    <div>
                        <button class="btn btn-outline-secondary cancel-edit me-2">Отмена</button>
                        <button class="btn btn-accent save-course-edit">Сохранить курс</button>
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
        const descTextarea = card.querySelector('.course-description-edit');
        const isPublicSelect = card.querySelector('.course-is-public-edit');
        const isContentPublicSelect = card.querySelector('.course-is-content-public-edit');
        const saveBtn = card.querySelector('.save-course-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-course');

        // Элементы для иконки
        const selectIconBtn = card.querySelector('.select-icon-btn');
        const fileInput = card.querySelector(`#iconFileInput-${course.id}`);
        const filenameSpan = card.querySelector('.icon-filename');
        const previewImg = card.querySelector('.current-course-icon');

        selectIconBtn.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                selectedIconFile = fileInput.files[0];
                filenameSpan.textContent = selectedIconFile.name;
                // Показать превью
                const reader = new FileReader();
                reader.onload = (e) => {
                    if (previewImg) previewImg.src = e.target.result;
                };
                reader.readAsDataURL(selectedIconFile);
            } else {
                selectedIconFile = null;
                filenameSpan.textContent = '';
            }
        });

        if (descTextarea) {
            descTextarea.addEventListener('input', function() { autosize(this); });
            autosize(descTextarea);
        }

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            if (!newName) {
                window.showToast('Название курса не может быть пустым', 'danger');
                return;
            }
            const newDesc = descTextarea.value.trim();
            const newIsPublic = isPublicSelect.value === 'true';
            const newIsContentPublic = isContentPublicSelect.value === 'true';
            const newTags = [...course.tags];

            try {
                // 1. Обновляем основные данные курса
                if (course.id) {
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
                    if (!res.ok) throw new Error('Ошибка обновления курса');
                    // Обновляем локальный объект
                    course.name = newName;
                    course.description = newDesc;
                    course.tags = newTags;
                    course.is_public = newIsPublic;
                    course.is_content_public = newIsContentPublic;
                    const orig = originalCourses.find(c => c.id === course.id);
                    if (orig) Object.assign(orig, course);
                } else {
                    // Создание нового курса
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
                    if (!res.ok) throw new Error('Ошибка создания курса');
                    const data = await res.json();
                    course.id = data.id;
                    course.name = newName;
                    course.description = newDesc;
                    course.tags = newTags;
                    course.is_public = newIsPublic;
                    course.is_content_public = newIsContentPublic;
                    originalCourses.push({ ...course });
                }

                // 2. Если выбран файл иконки, загружаем его
                if (selectedIconFile) {
                    const formData = new FormData();
                    formData.append('icon_file', selectedIconFile);
                    const iconRes = await fetch(`${window.API_BASE_URL}courses/${course.id}/icon`, {
                        method: 'POST',
                        credentials: 'include',
                        body: formData
                    });
                    if (!iconRes.ok) {
                        throw new Error('Не удалось загрузить иконку курса');
                    }
                }

                renderCourses();
                window.showToast(course.id ? 'Курс обновлён' : 'Курс создан');
            } catch (err) {
                window.showToast(err.message, 'danger');
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
                window.showToast('Курс удалён');
            } catch (err) {
                window.showToast(err.message, 'danger');
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
        courses.push(newCourse);
        renderCourses();
        setTimeout(() => {
            const newCard = container.querySelector('.list-group-item:last-child');
            const editTrigger = newCard?.querySelector('.edit-course-trigger');
            if (editTrigger) editTrigger.click();
        }, 50);
    }

    addBtn.addEventListener('click', addCourse);
    loadCourses();
})();