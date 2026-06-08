// static/course_creation/sections.js
(function() {
    const courseId = window.COURSE_ID;
    const container = document.getElementById('sectionsList');
    const addBtn = document.getElementById('addSectionBtn');

    let sections = [];
    let originalSections = [];

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
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="text-danger">Ошибка загрузки разделов: ${err.message}</div>`;
            sections = [];
            originalSections = [];
            renderSections();
        }
    }

    function renderSections() {
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
        if (placeholder) {
            window.initTagManager(placeholder, sec.tags);
        }

        const nameInput = card.querySelector('.section-name-edit');
        const descTextarea = card.querySelector('.section-description-edit');
        const saveBtn = card.querySelector('.save-section-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-section');

        if (descTextarea) {
            descTextarea.addEventListener('input', function() { autosize(this); });
            autosize(descTextarea);
        }

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            if (!newName) {
                window.showToast('Название раздела не может быть пустым', 'danger');
                return;
            }
            const newDesc = descTextarea.value.trim();
            const newTags = [...sec.tags];

            if (sec.id) {
                try {
                    const res = await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ name: newName, description: newDesc, tags: newTags })
                    });
                    if (!res.ok) throw new Error('Ошибка обновления');
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
                } catch (err) {
                    window.showToast(err.message, 'danger');
                }
            } else {
                try {
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
                    if (!res.ok) throw new Error('Ошибка создания раздела');
                    const data = await res.json();
                    sec.id = data.id;
                    sec.name = newName;
                    sec.description = newDesc;
                    sec.tags = newTags;
                    originalSections.push({ ...sec });
                    renderSections();
                    window.showToast('Раздел создан');
                } catch (err) {
                    window.showToast(err.message, 'danger');
                }
            }
        });

        cancelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
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
        });

        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (sec.id) {
                if (!confirm('Удалить раздел? Все темы внутри будут также удалены.')) return;
                try {
                    const res = await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                        method: 'DELETE',
                        credentials: 'include'
                    });
                    if (!res.ok) throw new Error('Ошибка удаления');
                    const index = sections.findIndex(s => s.id === sec.id);
                    if (index !== -1) sections.splice(index, 1);
                    originalSections = originalSections.filter(s => s.id !== sec.id);
                    renderSections();
                    window.showToast('Раздел удалён');
                } catch (err) {
                    window.showToast(err.message, 'danger');
                }
            } else {
                const index = sections.findIndex(s => s.id === null && s === sec);
                if (index !== -1) sections.splice(index, 1);
                renderSections();
            }
        });
    }

    function addSection() {
        const newOrder = sections.length + 1;
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
    if (typeof window.updateCourseBreadcrumb === 'function') window.updateCourseBreadcrumb(window.COURSE_ID);
})();