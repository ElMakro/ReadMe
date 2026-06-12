// static/course_creation/sections.js
(function() {
    const courseId = window.COURSE_ID;
    const container = document.getElementById('sectionsList');
    const addBtn = document.getElementById('addSectionBtn');

    let sections = [];
    let originalSections = [];

    let hasUnsavedChanges = false;
    let currentEditingSectionId = null;
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

    function truncateWords(text, wordLimit) {
        if (!text) return '';
        const words = text.trim().split(/\s+/);
        if (words.length <= wordLimit) return text;
        return words.slice(0, wordLimit).join(' ') + '...';
    }

    async function loadSections() {
        try {
            const res = await fetch(`${window.API_BASE_URL}sections/by_course/${courseId}`, {
                credentials: 'include'
            });
            if (res.status === 401 || res.status === 403) {
                window.showAccessDenied(container, 'Вы не авторизованы или недостаточно прав для редактирования курса.');
                return;
            }
            if (!res.ok) {
                if (res.status === 404) throw new Error('Курс не найден');
                if (res.status === 422) throw new Error('Ошибка валидации');
                throw new Error(`HTTP ${res.status}`);
            }
            const data = await res.json();
            let sectionsArray = Array.isArray(data) ? data : (data.items || data.sections || []);
            sections = sectionsArray.map(s => ({
                id: s.id,
                name: s.name,
                description: s.description || '',
                order_number: s.order_number,
                tags: s.tags || []
            }));
            sections.sort((a,b) => a.order_number - b.order_number);
            originalSections = JSON.parse(JSON.stringify(sections));
            renderSections();
            if (addBtn) addBtn.disabled = false;
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="text-danger">Ошибка загрузки разделов: ${err.message}</div>`;
            sections = [];
            originalSections = [];
            renderSections();
            if (addBtn) addBtn.disabled = true;
        }
    }

    function renderSections() {
        if (currentEditingSectionId) {
            currentEditingSectionId = null;
            originalEditingData = null;
            markUnsaved(false);
        }
        container.innerHTML = '';
        sections.forEach((sec) => {
            const card = document.createElement('div');
            card.className = 'list-group-item list-group-item-action border mb-2 rounded';
            card.style.cursor = 'pointer';
            card.setAttribute('data-section-id', sec.id);

            const shortDescription = truncateWords(sec.description, 15);

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <strong>${escapeHtml(sec.name)}</strong>
                        ${shortDescription ? `<div class="text-secondary small mt-1">${escapeHtml(shortDescription)}</div>` : ''}
                        ${sec.tags && sec.tags.length ? `<div class="small text-muted mt-1">Теги: ${sec.tags.map(t => escapeHtml(t)).join(' ')}</div>` : ''}
                    </div>
                    <span class="text-secondary edit-section-trigger" data-id="${sec.id}" style="cursor: pointer;">✎ редактировать</span>
                </div>
            `;

            const editTrigger = card.querySelector('.edit-section-trigger');
            editTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                if (currentEditingSectionId && currentEditingSectionId !== sec.id && hasUnsavedChanges) {
                    if (!confirm('Есть несохранённые изменения. Закрыть без сохранения?')) return;
                }
                openEditMode(sec);
            });

            card.addEventListener('click', (e) => {
                if (card.querySelector('.save-section-edit, .cancel-edit, .delete-section')) {
                    e.stopPropagation();
                    return;
                }
                window.location.href = `/course/${courseId}/section/${sec.id}/topics`;
            });

            container.appendChild(card);
        });
    }

    function openEditMode(sec) {
        currentEditingSectionId = sec.id;
        originalEditingData = {
            name: sec.name,
            description: sec.description,
            tags: [...sec.tags]
        };
        markUnsaved(false);

        const card = container.querySelector(`.list-group-item[data-section-id="${sec.id}"]`);
        if (!card) return;

        card.style.cursor = 'default';
        const placeholderId = `tagsManagerPlaceholder-${sec.id || 'new'}`;
        card.innerHTML = `
            <div class="p-2">
                <div class="mb-3">
                    <label class="form-label">Название раздела</label>
                    <input type="text" class="form-control section-name-edit" value="${escapeHtml(sec.name)}" placeholder="Введите название раздела">
                </div>
                <div class="mb-3">
                    <label class="form-label">Описание раздела</label>
                    <textarea class="form-control section-description-edit" placeholder="Введите описание раздела">${escapeHtml(sec.description)}</textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label">Теги</label>
                    <div id="${placeholderId}"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <button class="btn btn-danger delete-section">Удалить раздел</button>
                    <div>
                        <button class="btn btn-outline-secondary cancel-edit me-2">Отмена</button>
                        <button class="btn btn-accent save-section-edit">Сохранить раздел</button>
                    </div>
                </div>
            </div>
        `;

        const placeholder = card.querySelector(`#${placeholderId}`);
        let tagManager = null;
        if (placeholder) {
            tagManager = window.initTagManager(placeholder, sec.tags);
        }

        const nameInput = card.querySelector('.section-name-edit');
        const descTextarea = card.querySelector('.section-description-edit');
        const saveBtn = card.querySelector('.save-section-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-section');

        function checkChanges() {
            if (currentEditingSectionId !== sec.id) return;
            const nameChanged = nameInput.value.trim() !== originalEditingData.name;
            const descChanged = descTextarea.value.trim() !== originalEditingData.description;
            let tagsChanged = false;
            if (tagManager) {
                tagsChanged = JSON.stringify(tagManager.tags) !== JSON.stringify(originalEditingData.tags);
            }
            if (nameChanged || descChanged || tagsChanged) {
                markUnsaved(true);
            } else {
                markUnsaved(false);
            }
        }

        nameInput.addEventListener('input', checkChanges);
        descTextarea.addEventListener('input', checkChanges);
        if (tagManager) {
            const interval = setInterval(() => {
                if (tagManager && currentEditingSectionId === sec.id) {
                    checkChanges();
                } else {
                    clearInterval(interval);
                }
            }, 500);
        }

        if (descTextarea) {
            descTextarea.addEventListener('input', function() { autosize(this); });
            autosize(descTextarea);
        }

        const performUpdate = async () => {
            const newName = nameInput.value.trim();
            if (!newName) throw new Error('Название раздела не может быть пустым');
            const newDesc = descTextarea.value.trim();
            const newTags = tagManager ? tagManager.tags : sec.tags;

            if (sec.id) {
                const res = await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ name: newName, description: newDesc, tags: newTags })
                });
                if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                if (!res.ok) {
                    if (res.status === 404) throw new Error('Раздел не найден');
                    if (res.status === 422) throw new Error('Ошибка валидации данных');
                    throw new Error('Ошибка обновления');
                }
                sec.name = newName;
                sec.description = newDesc;
                sec.tags = newTags;
                const orig = originalSections.find(s => s.id === sec.id);
                if (orig) {
                    orig.name = newName;
                    orig.description = newDesc;
                    orig.tags = newTags;
                }
                renderSections();
                window.showToast('Раздел обновлён');
                currentEditingSectionId = null;
                markUnsaved(false);
            } else {
                const res = await fetch(`${window.API_BASE_URL}sections/create-section`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: newName,
                        description: newDesc,
                        order_number: sec.order_number,
                        course_id: courseId,
                        tags: newTags
                    })
                });
                if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                if (!res.ok) {
                    if (res.status === 404) throw new Error('Курс не найден');
                    if (res.status === 409) throw new Error('Раздел с таким порядковым номером уже существует');
                    if (res.status === 422) throw new Error('Ошибка валидации');
                    throw new Error('Ошибка создания раздела');
                }
                const data = await res.json();
                sec.id = data.id;
                sec.name = newName;
                sec.description = newDesc;
                sec.tags = newTags;
                originalSections.push({ ...sec });
                renderSections();
                window.showToast('Раздел создан');
                currentEditingSectionId = null;
                markUnsaved(false);
            }
        };

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            saveBtn.disabled = true;
            saveBtn.textContent = 'Сохранение...';
            try {
                await performUpdate();
            } catch (err) {
                if (err.message === 'unauthorized') {
                    window.Auth.retryAfterLogin(performUpdate);
                } else {
                    window.showToast(err.message, 'danger');
                }
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Сохранить раздел';
            }
        });

        cancelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (hasUnsavedChanges && !confirm('Есть несохранённые изменения. Отменить без сохранения?')) return;
            if (sec.id) {
                const orig = originalSections.find(s => s.id === sec.id);
                if (orig) {
                    sec.name = orig.name;
                    sec.description = orig.description;
                    sec.tags = [...orig.tags];
                }
                renderSections();
            } else {
                const idx = sections.findIndex(s => s.id === null && s === sec);
                if (idx !== -1) sections.splice(idx, 1);
                renderSections();
            }
            currentEditingSectionId = null;
            markUnsaved(false);
        });

        const performDelete = async () => {
            const res = await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
            if (!res.ok) {
                if (res.status === 404) throw new Error('Раздел не найден');
                throw new Error('Ошибка удаления');
            }
            const index = sections.findIndex(s => s.id === sec.id);
            if (index !== -1) sections.splice(index, 1);
            originalSections = originalSections.filter(s => s.id !== sec.id);
            renderSections();
            window.showToast('Раздел удалён');
            currentEditingSectionId = null;
            markUnsaved(false);
        };

        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (sec.id) {
                if (!confirm('Удалить раздел? Все темы внутри будут также удалены.')) return;
                try {
                    await performDelete();
                } catch (err) {
                    if (err.message === 'unauthorized') {
                        window.Auth.retryAfterLogin(performDelete);
                    } else {
                        window.showToast(err.message, 'danger');
                    }
                }
            } else {
                const index = sections.findIndex(s => s.id === null && s === sec);
                if (index !== -1) sections.splice(index, 1);
                renderSections();
                currentEditingSectionId = null;
                markUnsaved(false);
            }
        });
    }

    function addSection() {
        if (currentEditingSectionId && hasUnsavedChanges) {
            if (!confirm('Есть несохранённые изменения. Закрыть без сохранения?')) return;
        }
        // FIX: правильный расчёт order_number
        const maxOrder = sections.reduce((max, s) => Math.max(max, s.order_number), 0);
        const newOrder = maxOrder + 1;
        const newSection = {
            id: null,
            name: '',
            description: '',
            order_number: newOrder,
            tags: []
        };
        sections.push(newSection);
        renderSections();
        setTimeout(() => {
            const newCard = container.querySelector(`.list-group-item:last-child`);
            const editTrigger = newCard?.querySelector('.edit-section-trigger');
            if (editTrigger) editTrigger.click();
        }, 50);
    }

    addBtn.addEventListener('click', addSection);

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadSections();
    setupNavigationGuard();
    if (typeof window.updateCourseBreadcrumb === 'function') window.updateCourseBreadcrumb(window.COURSE_ID);
})();