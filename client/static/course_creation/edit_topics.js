// static/course_creation/edit_topics.js
(function() {
    const courseId = window.COURSE_ID;
    const sectionId = window.SECTION_ID;
    const container = document.getElementById('topicsList');
    const addBtn = document.getElementById('addTopicBtn');

    let topics = [];
    let originalTopics = [];

    function showMessage(text, isError = false) {
        const msgDiv = document.getElementById('toastMessage') || (() => {
            const div = document.createElement('div');
            div.id = 'toastMessage';
            div.style.position = 'fixed';
            div.style.bottom = '20px';
            div.style.right = '20px';
            div.style.zIndex = '9999';
            div.style.padding = '12px 20px';
            div.style.borderRadius = '8px';
            div.style.backgroundColor = isError ? '#dc3545' : '#198754';
            div.style.color = 'white';
            div.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
            document.body.appendChild(div);
            return div;
        })();
        msgDiv.textContent = text;
        msgDiv.style.backgroundColor = isError ? '#dc3545' : '#198754';
        msgDiv.style.opacity = '1';
        setTimeout(() => {
            msgDiv.style.opacity = '0';
            setTimeout(() => msgDiv.remove(), 300);
        }, 2000);
    }

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
                order_number: t.order_number
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
                    <strong>${escapeHtml(topic.name)}</strong>
                    <span class="text-secondary edit-topic-trigger" data-id="${topic.id}" style="cursor: pointer;">✎ редактировать</span>
                </div>
            `;

            const editTrigger = card.querySelector('.edit-topic-trigger');
            editTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                openEditMode(topic);
            });

            // Переход к блокам только при клике на саму карточку (не на кнопку)
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
        card.innerHTML = `
            <div class="p-2">
                <div class="mb-3">
                    <label class="form-label">Название темы</label>
                    <input type="text" class="form-control topic-name-edit" value="${escapeHtml(topic.name)}" placeholder="Введите название темы">
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

        const nameInput = card.querySelector('.topic-name-edit');
        const saveBtn = card.querySelector('.save-topic-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-topic');

        saveBtn.addEventListener('click', async () => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            if (!newName) {
                showMessage('Название темы не может быть пустым', true);
                return;
            }
            if (topic.id) {
                try {
                    const params = new URLSearchParams();
                    params.append('name', newName);
                    const url = `${window.API_BASE_URL}topics/${topic.id}?${params.toString()}`;
                    const res = await fetch(url, { method: 'PUT', credentials: 'include' });
                    if (!res.ok) throw new Error('Ошибка обновления');
                    topic.name = newName;
                    const orig = originalTopics.find(t => t.id === topic.id);
                    if (orig) orig.name = newName;
                    renderTopics();
                    showMessage('Тема обновлена');
                } catch (err) {
                    showMessage(err.message, true);
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
                            section_id: sectionId
                        })
                    });
                    if (!res.ok) throw new Error('Ошибка создания темы');
                    const data = await res.json();
                    topic.id = data.id;
                    topic.name = newName;
                    originalTopics.push({ ...topic });
                    renderTopics();
                    showMessage('Тема создана');
                } catch (err) {
                    showMessage(err.message, true);
                }
            }
        });

        cancelBtn.addEventListener('click', () => {
            e.stopPropagation();
            if (topic.id) {
                const orig = originalTopics.find(t => t.id === topic.id);
                if (orig) topic.name = orig.name;
                renderTopics();
            } else {
                const idx = topics.findIndex(t => t.id === null && t === topic);
                if (idx !== -1) topics.splice(idx, 1);
                renderTopics();
            }
        });

        delBtn.addEventListener('click', async () => {
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
                    showMessage('Тема удалена');
                } catch (err) {
                    showMessage(err.message, true);
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
            order_number: newOrder
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
    window.updateCourseBreadcrumb(window.COURSE_ID);
    window.updateSectionBreadcrumb(window.SECTION_ID);
})();