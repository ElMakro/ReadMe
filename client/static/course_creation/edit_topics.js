// static/course_creation/edit_topics.js (обновлённый)
(function() {
    const courseId = window.COURSE_ID;
    const sectionId = window.SECTION_ID;
    const container = document.getElementById('topicsList');
    const addBtn = document.getElementById('addTopicBtn');
    const saveBtn = document.getElementById('saveTopicsBtn');

    let topics = [];
    let originalTopics = [];
    let hasUnsaved = false;

    window.addEventListener('beforeunload', (e) => {
        if (hasUnsaved) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    async function loadTopics() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/by-section/${sectionId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            topics = (data && Array.isArray(data.topics)) ? data.topics.map(t => ({
                id: t.id,
                name: t.name,
                order_number: t.order_number,
                isNew: false
            })) : [];
            topics.sort((a,b) => a.order_number - b.order_number);
            originalTopics = JSON.parse(JSON.stringify(topics));
            renderTopics();
            hasUnsaved = false;
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
        topics.forEach((topic, idx) => {
            const card = document.createElement('div');
            card.className = 'card mb-3 bg-secondary border-0 shadow-sm';
            card.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start gap-2">
                        <input type="text" class="form-control topic-name flex-grow-1" value="${escapeHtml(topic.name)}" data-idx="${idx}" placeholder="Название темы">
                        <button class="btn btn-sm btn-outline-danger delete-topic" data-idx="${idx}">🗑️</button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
        attachEvents();
    }

    function attachEvents() {
        document.querySelectorAll('.topic-name').forEach(inp => {
            inp.removeEventListener('input', handleNameChange);
            inp.addEventListener('input', handleNameChange);
        });
        document.querySelectorAll('.delete-topic').forEach(btn => {
            btn.removeEventListener('click', handleDelete);
            btn.addEventListener('click', handleDelete);
        });
    }

    function handleNameChange(e) {
        const idx = parseInt(e.target.dataset.idx);
        topics[idx].name = e.target.value;
        markUnsaved();
    }

    function handleDelete(e) {
        const idx = parseInt(e.target.dataset.idx);
        topics.splice(idx, 1);
        topics.forEach((t, i) => t.order_number = i + 1);
        renderTopics();
        markUnsaved();
    }

    function addTopic() {
        const newOrder = topics.length + 1;
        topics.push({
            id: null,
            name: '',
            order_number: newOrder,
            isNew: true
        });
        renderTopics();
        markUnsaved();
    }

    addBtn.addEventListener('click', addTopic);

    function markUnsaved() {
        const currentStr = JSON.stringify(topics.map(t => ({ id: t.id, name: t.name, order: t.order_number })));
        const origStr = JSON.stringify(originalTopics.map(t => ({ id: t.id, name: t.name, order: t.order_number })));
        hasUnsaved = currentStr !== origStr;
    }

    async function saveTopics() {
        saveBtn.disabled = true;
        try {
            // 1. Удаление
            const currentIds = topics.filter(t => t.id !== null).map(t => t.id);
            const toDelete = originalTopics.filter(orig => !currentIds.includes(orig.id));
            for (const del of toDelete) {
                const res = await fetch(`${window.API_BASE_URL}topics/${del.id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (!res.ok) throw new Error(`Ошибка удаления темы ${del.id}`);
            }

            // 2. Создание
            for (const tp of topics.filter(t => t.id === null && t.name.trim() !== '')) {
                const res = await fetch(`${window.API_BASE_URL}topics/create-topic`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: tp.name,
                        order_number: tp.order_number,
                        section_id: sectionId
                    })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Ошибка создания темы');
                }
            }

            // 3. Обновление
            for (const tp of topics.filter(t => t.id !== null)) {
                const params = new URLSearchParams();
                if (tp.name) params.append('name', tp.name);
                if (tp.order_number !== undefined) params.append('order_number', tp.order_number);
                const url = `${window.API_BASE_URL}topics/${tp.id}?${params.toString()}`;
                const res = await fetch(url, { method: 'PUT', credentials: 'include' });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || `Ошибка обновления темы ${tp.id}`);
                }
            }

            await loadTopics();
            alert('Темы успешно сохранены');
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
        } finally {
            saveBtn.disabled = false;
        }
    }

    saveBtn.addEventListener('click', saveTopics);

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Переход к редактированию блоков при клике на название темы (на любом месте карточки, но именно по полю ввода)
    container.addEventListener('click', (e) => {
        const input = e.target.closest('.topic-name');
        if (!input) return;
        const idx = parseInt(input.dataset.idx);
        const topicId = topics[idx].id;
        if (topicId) {
            if (hasUnsaved && !confirm('Есть несохранённые изменения. Продолжить?')) return;
            window.location.href = `/course/${courseId}/section/${sectionId}/topic/${topicId}/blocks`;
        } else {
            alert('Сначала сохраните тему');
        }
    });

    loadTopics();
    window.updateCourseBreadcrumb(window.COURSE_ID);
    window.updateSectionBreadcrumb(window.SECTION_ID);
})();