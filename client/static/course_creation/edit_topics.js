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
            const res = await fetch(`${window.API_BASE_URL}topics/by-section/${sectionId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error();
            const data = await res.json();   // { topics: [...], total }
            topics = (data.topics || []).map(t => ({
                id: t.id,
                name: t.name,
                order_number: t.order_number,
                isNew: false
            }));
            topics.sort((a,b) => a.order_number - b.order_number);
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
                <input type="text" class="form-control topic-name" value="${escapeHtml(topic.name)}" data-idx="${idx}" placeholder="Название темы">
                <button class="btn btn-sm btn-outline-danger delete-topic" data-idx="${idx}">🗑️</button>
            `;
            container.appendChild(div);
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
            for (const tp of topics.filter(t => t.isNew && t.name.trim())) {
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
                if (!res.ok) throw new Error('Ошибка создания темы');
                const data = await res.json();
                tp.id = data.id;
                tp.isNew = false;
            }
            for (const tp of topics.filter(t => !t.isNew)) {
                const orig = originalTopics.find(o => o.id === tp.id);
                if (orig && (orig.name !== tp.name || orig.order_number !== tp.order_number)) {
                    let url = `${window.API_BASE_URL}topics/${tp.id}?`;
                    const params = new URLSearchParams();
                    if (tp.name !== orig.name) params.append('name', tp.name);
                    if (tp.order_number !== orig.order_number) params.append('order_number', tp.order_number);
                    if (params.toString()) {
                        url += params.toString();
                        await fetch(url, { method: 'PUT', credentials: 'include' });
                    }
                }
            }
            await loadTopics();
            alert('Темы сохранены');
        } catch (err) {
            alert('Ошибка сохранения тем: ' + err.message);
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
})();