// static/course_creation/created_courses.js
(function() {
    const container = document.getElementById('coursesList');
    const addBtn = document.getElementById('addCourseBtn');
    const PAGE_SIZE = 9;

    let courses = [];
    let originalCourses = [];
    let currentPage = 1;
    let totalPages = 1;
    let isLoading = false;
    let pagination = null;

    let selectedIconFile = null;
    let currentEditingCourseId = null;
    let hasUnsavedChanges = false;
    let originalEditingData = null;

    function markUnsaved(unsaved) {
        if (unsaved === hasUnsavedChanges) return;
        hasUnsavedChanges = unsaved;
        const titleEl = document.querySelector('title');
        if (titleEl) {
            let baseTitle = titleEl.textContent.replace(/^\*\s*/, '');
            titleEl.textContent = unsaved ? `* ${baseTitle}` : baseTitle;
        }
    }

    function setupNavigationGuard() {
        window.addEventListener('beforeunload', (e) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = 'Есть несохранённые изменения. Вы уверены, что хотите покинуть страницу?';
                return e.returnValue;
            }
        });
        document.body.addEventListener('click', async (e) => {
            let target = e.target.closest('a');
            if (!target) return;
            const href = target.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:')) return;
            if (hasUnsavedChanges) {
                e.preventDefault();
                if (confirm('Есть несохранённые изменения. Вы действительно хотите покинуть страницу? Все несохранённые изменения будут потеряны.')) {
                    markUnsaved(false);
                    window.location.href = href;
                }
            }
        });
    }

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

    async function loadCourses(page = 1) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-accent" role="status"></div></div>';
        try {
            const url = `${window.API_BASE_URL}courses/controlled-courses?page=${page}&records_per_page=${PAGE_SIZE}`;
            const res = await fetch(url, { credentials: 'include' });
            if (res.status === 401 || res.status === 403) {
                window.showAccessDenied(container, 'Доступ запрещён. Только для преподавателей и администраторов.', true, pagination);
                isLoading = false;
                return;
            }
            if (!res.ok) {
                if (res.status === 422) throw new Error('Ошибка валидации параметров');
                throw new Error(`HTTP ${res.status}`);
            }
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
            const hasNext = coursesArray.length === PAGE_SIZE;
            totalPages = hasNext ? page + 1 : page;
            if (pagination) {
                pagination.setTotalPages(totalPages);
                pagination.setPage(page, true);
            }
            if (addBtn) addBtn.disabled = false;
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="text-danger">Ошибка загрузки курсов: ${err.message}</div>`;
            courses = [];
            originalCourses = [];
            renderCourses();
            if (addBtn) addBtn.disabled = true;
            if (pagination) pagination.hide();
        } finally {
            isLoading = false;
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
        if (currentEditingCourseId && currentEditingCourseId !== course.id && hasUnsavedChanges) {
            if (!confirm('Есть несохранённые изменения. Закрыть без сохранения?')) return;
        }
        currentEditingCourseId = course.id;
        originalEditingData = {
            name: course.name,
            description: course.description,
            tags: [...course.tags],
            is_public: course.is_public,
            is_content_public: course.is_content_public
        };
        markUnsaved(false);

        selectedIconFile = null;
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
                
                <div class="mb-3">
                    <label class="form-label">Иконка курса</label>
                    <div class="d-flex align-items-center gap-3">
                        <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                             class="current-course-icon"
                             width="64" height="64"
                             style="object-fit: cover;">
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
        let tagManager = null;
        if (placeholder) {
            tagManager = window.initTagManager(placeholder, course.tags);
            const interval = setInterval(() => {
                if (tagManager && currentEditingCourseId === course.id) {
                    const currentTags = tagManager.tags;
                    if (JSON.stringify(currentTags) !== JSON.stringify(originalEditingData.tags)) {
                        markUnsaved(true);
                    } else {
                        const nameChanged = card.querySelector('.course-name-edit').value.trim() !== originalEditingData.name;
                        const descChanged = card.querySelector('.course-description-edit').value.trim() !== originalEditingData.description;
                        const isPublicChanged = card.querySelector('.course-is-public-edit').value === 'true' !== originalEditingData.is_public;
                        const isContentPublicChanged = card.querySelector('.course-is-content-public-edit').value === 'true' !== originalEditingData.is_content_public;
                        if (!nameChanged && !descChanged && !isPublicChanged && !isContentPublicChanged && !selectedIconFile) {
                            markUnsaved(false);
                        } else {
                            markUnsaved(true);
                        }
                    }
                } else {
                    clearInterval(interval);
                }
            }, 500);
        }

        const nameInput = card.querySelector('.course-name-edit');
        const descTextarea = card.querySelector('.course-description-edit');
        const isPublicSelect = card.querySelector('.course-is-public-edit');
        const isContentPublicSelect = card.querySelector('.course-is-content-public-edit');
        const saveBtn = card.querySelector('.save-course-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-course');

        const selectIconBtn = card.querySelector('.select-icon-btn');
        const fileInput = card.querySelector(`#iconFileInput-${course.id}`);
        const filenameSpan = card.querySelector('.icon-filename');
        const previewImg = card.querySelector('.current-course-icon');

        function checkChanges() {
            if (currentEditingCourseId !== course.id) return;
            const nameChanged = nameInput.value.trim() !== originalEditingData.name;
            const descChanged = descTextarea.value.trim() !== originalEditingData.description;
            const isPublicChanged = isPublicSelect.value === 'true' !== originalEditingData.is_public;
            const isContentPublicChanged = isContentPublicSelect.value === 'true' !== originalEditingData.is_content_public;
            let tagsChanged = false;
            if (tagManager) {
                tagsChanged = JSON.stringify(tagManager.tags) !== JSON.stringify(originalEditingData.tags);
            }
            const iconChanged = selectedIconFile !== null;
            if (nameChanged || descChanged || isPublicChanged || isContentPublicChanged || tagsChanged || iconChanged) {
                markUnsaved(true);
            } else {
                markUnsaved(false);
            }
        }

        nameInput.addEventListener('input', checkChanges);
        descTextarea.addEventListener('input', checkChanges);
        isPublicSelect.addEventListener('change', checkChanges);
        isContentPublicSelect.addEventListener('change', checkChanges);

        selectIconBtn.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                selectedIconFile = fileInput.files[0];
                filenameSpan.textContent = selectedIconFile.name;
                const reader = new FileReader();
                reader.onload = (e) => {
                    if (previewImg) previewImg.src = e.target.result;
                };
                reader.readAsDataURL(selectedIconFile);
                checkChanges();
            } else {
                selectedIconFile = null;
                filenameSpan.textContent = '';
                checkChanges();
            }
        });

        if (descTextarea) {
            descTextarea.addEventListener('input', function() { autosize(this); });
            autosize(descTextarea);
        }

        async function performSave() {
            const newName = nameInput.value.trim();
            if (!newName) throw new Error('Название курса не может быть пустым');
            const newDesc = descTextarea.value.trim();
            const newIsPublic = isPublicSelect.value === 'true';
            const newIsContentPublic = isContentPublicSelect.value === 'true';
            const newTags = tagManager ? tagManager.tags : [...course.tags];

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
                if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                if (!res.ok) {
                    if (res.status === 404) throw new Error('Курс не найден');
                    if (res.status === 409) throw new Error('Конфликт уровней публичности курса');
                    if (res.status === 422) throw new Error('Ошибка валидации данных');
                    throw new Error('Ошибка обновления курса');
                }
                course.name = newName;
                course.description = newDesc;
                course.tags = newTags;
                course.is_public = newIsPublic;
                course.is_content_public = newIsContentPublic;
                const orig = originalCourses.find(c => c.id === course.id);
                if (orig) Object.assign(orig, course);
            } else {
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
                if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                if (!res.ok) {
                    if (res.status === 409) throw new Error('Конфликт уровней публичности');
                    if (res.status === 422) throw new Error('Ошибка валидации данных');
                    throw new Error('Ошибка создания курса');
                }
                const data = await res.json();
                course.id = data.id;
                course.name = newName;
                course.description = newDesc;
                course.tags = newTags;
                course.is_public = newIsPublic;
                course.is_content_public = newIsContentPublic;
                originalCourses.push({ ...course });
            }

            if (selectedIconFile) {
                const formData = new FormData();
                formData.append('icon_file', selectedIconFile);
                const iconRes = await fetch(`${window.API_BASE_URL}courses/${course.id}/icon`, {
                    method: 'POST',
                    credentials: 'include',
                    body: formData
                });
                if (iconRes.status === 401 || iconRes.status === 403) throw new Error('unauthorized');
                if (!iconRes.ok) {
                    if (iconRes.status === 404) throw new Error('Курс не найден');
                    if (iconRes.status === 415) throw new Error('Некорректный тип файла');
                    throw new Error('Не удалось загрузить иконку курса');
                }
                selectedIconFile = null;
            }

            renderCourses();
            window.showToast(course.id ? 'Курс обновлён' : 'Курс создан');
            markUnsaved(false);
            currentEditingCourseId = null;
        }

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            saveBtn.disabled = true;
            saveBtn.textContent = 'Сохранение...';
            try {
                await performSave();
            } catch (err) {
                if (err.message === 'unauthorized') {
                    window.Auth.retryAfterLogin(performSave);
                } else {
                    window.showToast(err.message, 'danger');
                }
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Сохранить курс';
            }
        });

        cancelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (hasUnsavedChanges && !confirm('Есть несохранённые изменения. Отменить без сохранения?')) return;
            if (course.id) {
                const orig = originalCourses.find(c => c.id === course.id);
                if (orig) Object.assign(course, orig);
                renderCourses();
            } else {
                const idx = courses.findIndex(c => c.id === null && c === course);
                if (idx !== -1) courses.splice(idx, 1);
                renderCourses();
            }
            currentEditingCourseId = null;
            markUnsaved(false);
        });

        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!course.id) {
                const idx = courses.findIndex(c => c.id === null && c === course);
                if (idx !== -1) courses.splice(idx, 1);
                renderCourses();
                currentEditingCourseId = null;
                markUnsaved(false);
                return;
            }
            if (!confirm('Удалить курс? Все разделы и материалы будут удалены.')) return;

            const performDelete = async () => {
                const res = await fetch(`${window.API_BASE_URL}courses/${course.id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                if (!res.ok) {
                    if (res.status === 404) throw new Error('Курс не найден');
                    throw new Error('Ошибка удаления');
                }
                const idx = courses.findIndex(c => c.id === course.id);
                if (idx !== -1) courses.splice(idx, 1);
                originalCourses = originalCourses.filter(c => c.id !== course.id);
                renderCourses();
                window.showToast('Курс удалён');
                currentEditingCourseId = null;
                markUnsaved(false);
            };

            try {
                await performDelete();
            } catch (err) {
                if (err.message === 'unauthorized') {
                    window.Auth.retryAfterLogin(performDelete);
                } else {
                    window.showToast(err.message, 'danger');
                }
            }
        });
    }

    function addCourse() {
        if (currentEditingCourseId && hasUnsavedChanges) {
            if (!confirm('Есть несохранённые изменения. Закрыть без сохранения?')) return;
        }
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

    const paginationContainer = document.getElementById('paginationContainer');
    if (paginationContainer) {
        pagination = new Pagination(paginationContainer, (page) => loadCourses(page), {
            pageSize: PAGE_SIZE,
            autoHide: true
        });
    }

    addBtn.addEventListener('click', addCourse);
    loadCourses(1);
    setupNavigationGuard();
})();