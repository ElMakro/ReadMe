// static/edit-topics.js
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
        if (hasUnsaved) e.preventDefault(), e.returnValue = '';
    });

    async function loadTopics() {
        try {
            const res = await fetch(`${window.API_BASE_URL}sections/${sectionId}/topics`, { credentials: 'include' });
            if (!res.ok) throw new Error();
            const data = await res.json();
            topics = data.map(t => ({ id: t.id, title: t.title, isNew: false }));
            originalTopics = JSON.parse(JSON.stringify(topics));
            renderTopics();
            hasUnsaved = false;
        } catch {
            topics = [];
            originalTopics = [];
            renderTopics();
        }
    }

    function renderTopics() {
        container.innerHTML = '';
        topics.forEach((topic, idx) => {
            const div = document.createElement('div');
            div.className = 'mb-2 d-flex align-items-center gap-2';
            div.innerHTML = `
                <input type="text" class="form-control topic-title" value="${escapeHtml(topic.title)}" data-idx="${idx}" placeholder="Название темы">
                <button class="btn btn-sm btn-outline-danger delete-topic" data-idx="${idx}">🗑️</button>
            `;
            container.appendChild(div);
        });

        document.querySelectorAll('.topic-title').forEach(inp => {
            inp.addEventListener('input', (e) => {
                const idx = parseInt(e.target.dataset.idx);
                topics[idx].title = e.target.value;
                markUnsaved();
            });
        });

        document.querySelectorAll('.delete-topic').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(btn.dataset.idx);
                topics.splice(idx, 1);
                renderTopics();
                markUnsaved();
            });
        });
    }

    function addTopic() {
        topics.push({ id: null, title: '', isNew: true });
        renderTopics();
        markUnsaved();
    }

    addBtn.addEventListener('click', addTopic);

    function markUnsaved() {
        hasUnsaved = JSON.stringify(topics) !== JSON.stringify(originalTopics);
    }

    async function saveTopics() {
        const newTopics = topics.filter(t => t.isNew && t.title.trim());
        const existing = topics.filter(t => !t.isNew);
        saveBtn.disabled = true;
        try {
            for (const tp of newTopics) {
                const res = await fetch(`${window.API_BASE_URL}sections/${sectionId}/topics`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ title: tp.title })
                });
                if (!res.ok) throw new Error();
                const data = await res.json();
                tp.id = data.id;
                tp.isNew = false;
            }
            for (const tp of existing) {
                const orig = originalTopics.find(o => o.id === tp.id);
                if (orig && orig.title !== tp.title) {
                    await fetch(`${window.API_BASE_URL}topics/${tp.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ title: tp.title })
                    });
                }
            }
            await loadTopics();
            alert('Темы сохранены');
        } catch (err) {
            alert('Ошибка сохранения тем');
        } finally {
            saveBtn.disabled = false;
        }
    }

    saveBtn.addEventListener('click', saveTopics);

    // клик по названию темы → переход к блокам
    container.addEventListener('click', (e) => {
        const input = e.target.closest('.topic-title');
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

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadTopics();
})();