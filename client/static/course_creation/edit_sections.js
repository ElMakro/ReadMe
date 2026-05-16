// static/edit-sections.js
(function() {
    const courseId = window.COURSE_ID;
    const container = document.getElementById('sectionsList');
    const addBtn = document.getElementById('addSectionBtn');
    const saveBtn = document.getElementById('saveSectionsBtn');

    let sections = [];           // каждый: { id, title, isNew }
    let originalSections = [];
    let hasUnsavedChanges = false;

    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) e.preventDefault(), e.returnValue = '';
    });

    async function loadSections() {
        try {
            const res = await fetch(`${window.API_BASE_URL}sections/by_course/${courseId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error();
            const data = await res.json();   // { sections: [...] }
            sections = data.sections.map(s => ({ id: s.id, title: s.title, isNew: false }));
            originalSections = JSON.parse(JSON.stringify(sections));
            renderSections();
            hasUnsavedChanges = false;
        } catch (err) {
            console.error(err);
            sections = [];
            originalSections = [];
            renderSections();
        }
    }

    function renderSections() {
        container.innerHTML = '';
        sections.forEach((sec, idx) => {
            const div = document.createElement('div');
            div.className = 'mb-2 d-flex align-items-center gap-2';
            div.innerHTML = `
                <input type="text" class="form-control section-title" value="${escapeHtml(sec.title)}" data-idx="${idx}" placeholder="Название раздела">
                <button class="btn btn-sm btn-outline-danger delete-section" data-idx="${idx}">🗑️</button>
            `;
            container.appendChild(div);
        });
        attachEvents();
    }

    function attachEvents() {
        document.querySelectorAll('.section-title').forEach(inp => {
            inp.removeEventListener('input', handleTitleChange);
            inp.addEventListener('input', handleTitleChange);
        });
        document.querySelectorAll('.delete-section').forEach(btn => {
            btn.removeEventListener('click', handleDelete);
            btn.addEventListener('click', handleDelete);
        });
    }

    function handleTitleChange(e) {
        const idx = parseInt(e.target.dataset.idx);
        sections[idx].title = e.target.value;
        markUnsaved();
    }
    function handleDelete(e) {
        const idx = parseInt(e.target.dataset.idx);
        sections.splice(idx, 1);
        renderSections();
        markUnsaved();
    }

    function addSection() {
        sections.push({ id: null, title: '', isNew: true });
        renderSections();
        markUnsaved();
    }

    addBtn.addEventListener('click', addSection);

    function markUnsaved() {
        hasUnsavedChanges = JSON.stringify(sections) !== JSON.stringify(originalSections);
    }

    async function saveSections() {
        saveBtn.disabled = true;
        try {
            // 1. Создаём новые разделы (те, у которых isNew)
            for (const sec of sections.filter(s => s.isNew && s.title.trim())) {
                const order = sections.length; // упрощённо
                const res = await fetch(`${window.API_BASE_URL}sections/create-section`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        course_id: courseId,
                        title: sec.title,
                        order_number: order
                    })
                });
                if (!res.ok) throw new Error('Ошибка создания раздела');
                const data = await res.json();
                sec.id = data.id;
                sec.isNew = false;
            }
            // 2. Обновляем существующие (изменившие название)
            for (const sec of sections.filter(s => !s.isNew)) {
                const orig = originalSections.find(o => o.id === sec.id);
                if (orig && orig.title !== sec.title) {
                    await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ title: sec.title })
                    });
                }
            }
            // Перезагружаем актуальный список
            await loadSections();
            alert('Разделы сохранены');
        } catch (err) {
            alert(err.message);
        } finally {
            saveBtn.disabled = false;
        }
    }

    saveBtn.addEventListener('click', saveSections);

    function escapeHtml(str) { ... }

    // Клик по заголовку раздела – переход к темам (если раздел уже сохранён)
    container.addEventListener('click', (e) => {
        const input = e.target.closest('.section-title');
        if (!input) return;
        const idx = parseInt(input.dataset.idx);
        const section = sections[idx];
        if (section.id) {
            if (hasUnsavedChanges && !confirm('Есть несохранённые изменения. Перейти всё равно?')) return;
            window.location.href = `/course/${courseId}/section/${section.id}/topics`;
        } else {
            alert('Сначала сохраните раздел');
        }
    });

    loadSections();
})();