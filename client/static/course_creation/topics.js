// static/course_creation/topics.js
(function() {
    const courseId = window.COURSE_ID;
    const sectionId = window.SECTION_ID;
    const container = document.getElementById('topicsList');
    const addBtn = document.getElementById('addTopicBtn');

    let topics = [];
    let originalTopics = [];

    async function loadTopics() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/by-section/${sectionId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            let topicsArray = (data && Array.isArray(data.topics)) ? data.topics : (Array.isArray(data) ? data : []);
            topics = topicsArray.map(t => ({
                id: t.id,
                name: t.name,
                order_number: t.order_number,
                tags: t.tags || []
            }));
            topics.sort((a,b) => a.order_number - b.order_number);
            originalTopics = JSON.parse(JSON.stringify(topics));
            renderTopics();
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="text-danger">Ошибка загрузки тем: ${err.message}</div>`;
            topics = [];
            originalTopics = [];
            renderTopics();
        }
    }

    function renderTopics() {
        container.innerHTML = '';
        topics.forEach((topic) => {
            const card = document.createElement('div');
            card.className = 'list-group-item list-group-item-action border mb-2 rounded';
            card.style.cursor = 'pointer';
            card.setAttribute('data-topic-id', topic.id);

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${escapeHtml(topic.name)}</strong>
                        ${topic.tags && topic.tags.length ? `<div class="small text-muted mt-1">Теги: ${topic.tags.map(t => escapeHtml(t)).join(' ')}</div>` : ''}
                    </div>
                    <span class="text-secondary edit-topic-trigger" data-id="${topic.id}" style="cursor: pointer;">✎ редактировать</span>
                </div>
            `;

            const editTrigger = card.querySelector('.edit-topic-trigger');
            editTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                openEditMode(topic);
            });

            card.addEventListener('click', (e) => {
                if (card.querySelector('.save-topic-edit, .cancel-edit, .delete-topic')) {
                    e.stopPropagation();
                    return;
                }
                window.location.href = `/course/${courseId}/section/${sectionId}/topic/${topic.id}/blocks`;
            });

            container.appendChild(card);
        });
    }

    function openEditMode(topic) {
        const card = container.querySelector(`.list-group-item[data-topic-id="${topic.id}"]`);
        if (!card) return;

        card.style.cursor = 'default';
        const placeholderId = `tagsManagerPlaceholder-${topic.id || 'new'}`;
        card.innerHTML = `
            <div class="p-2">
                <div class="mb-3">
                    <label class="form-label">Название темы</label>
                    <input type="text" class="form-control topic-name-edit" value="${escapeHtml(topic.name)}" placeholder="Введите название темы">
                </div>
                <div class="mb-3">
                    <label class="form-label">Теги</label>
                    <div id="${placeholderId}"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <button class="btn btn-danger delete-topic">Удалить тему</button>
                    <div>
                        <button class="btn btn-outline-secondary cancel-edit me-2">Отмена</button>
                        <button class="btn btn-accent save-topic-edit">Сохранить изменения</button>
                    </div>
                </div>
            </div>
        `;

        const placeholder = card.querySelector(`#${placeholderId}`);
        if (placeholder) {
            window.initTagManager(placeholder, topic.tags);
        }

        const nameInput = card.querySelector('.topic-name-edit');
        const saveBtn = card.querySelector('.save-topic-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-topic');

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            if (!newName) {
                window.showToast('Название темы не может быть пустым', 'danger');
                return;
            }
            const newTags = [...topic.tags];

            if (topic.id) {
                try {
                    const updateBody = {};
                    if (newName !== topic.name) updateBody.name = newName;
                    if (JSON.stringify(newTags) !== JSON.stringify(topic.tags)) updateBody.tags = newTags;

                    const res = await fetch(`${window.API_BASE_URL}topics/${topic.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify(updateBody)
                    });
                    if (!res.ok) {
                        let errorMsg = 'Ошибка обновления темы';
                        if (res.status === 422) {
                            const errData = await res.json().catch(() => null);
                            errorMsg = errData?.detail || 'Неверный формат данных';
                        }
                        throw new Error(errorMsg);
                    }
                    topic.name = newName;
                    topic.tags = newTags;
                    const orig = originalTopics.find(t => t.id === topic.id);
                    if (orig) {
                        orig.name = newName;
                        orig.tags = newTags;
                    }
                    renderTopics();
                    window.showToast('Тема обновлена');
                } catch (err) {
                    window.showToast(err.message, 'danger');
                }
            } else {
                try {
                    const res = await fetch(`${window.API_BASE_URL}topics/create-topic`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            name: newName,
                            order_number: topic.order_number,
                            section_id: sectionId,
                            tags: newTags,
                            raw_content: []
                        })
                    });
                    if (!res.ok) throw new Error('Ошибка создания темы');
                    const data = await res.json();
                    topic.id = data.id;
                    topic.name = newName;
                    topic.tags = newTags;
                    originalTopics.push({ ...topic });
                    renderTopics();
                    window.showToast('Тема создана');
                } catch (err) {
                    window.showToast(err.message, 'danger');
                }
            }
        });

        cancelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (topic.id) {
                const orig = originalTopics.find(t => t.id === topic.id);
                if (orig) {
                    topic.name = orig.name;
                    topic.tags = [...orig.tags];
                }
                renderTopics();
            } else {
                const idx = topics.findIndex(t => t.id === null && t === topic);
                if (idx !== -1) topics.splice(idx, 1);
                renderTopics();
            }
        });

        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (topic.id) {
                if (!confirm('Удалить тему? Все блоки внутри будут удалены.')) return;
                try {
                    const res = await fetch(`${window.API_BASE_URL}topics/${topic.id}`, {
                        method: 'DELETE',
                        credentials: 'include'
                    });
                    if (!res.ok) throw new Error('Ошибка удаления');
                    const index = topics.findIndex(t => t.id === topic.id);
                    if (index !== -1) topics.splice(index, 1);
                    originalTopics = originalTopics.filter(t => t.id !== topic.id);
                    renderTopics();
                    window.showToast('Тема удалена');
                } catch (err) {
                    window.showToast(err.message, 'danger');
                }
            } else {
                const index = topics.findIndex(t => t.id === null && t === topic);
                if (index !== -1) topics.splice(index, 1);
                renderTopics();
            }
        });
    }

    function addTopic() {
        const newOrder = topics.length + 1;
        const newTopic = {
            id: null,
            name: '',
            order_number: newOrder,
            tags: []
        };
        topics.push(newTopic);
        renderTopics();
        setTimeout(() => {
            const newCard = container.querySelector(`.list-group-item:last-child`);
            const editTrigger = newCard?.querySelector('.edit-topic-trigger');
            if (editTrigger) editTrigger.click();
        }, 50);
    }

    addBtn.addEventListener('click', addTopic);

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadTopics();
    if (typeof window.updateCourseBreadcrumb === 'function') window.updateCourseBreadcrumb(window.COURSE_ID);
    if (typeof window.updateSectionBreadcrumb === 'function') window.updateSectionBreadcrumb(window.SECTION_ID);
})();