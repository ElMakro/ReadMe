(function() {
    const courseId = window.COURSE_ID;
    const container = document.getElementById('sectionsList');
    const addBtn = document.getElementById('addSectionBtn');
    const saveBtn = document.getElementById('saveSectionsBtn');

    let sections = [];
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
            const data = await res.json();   // { sections: [...], total }
            sections = (data.sections || []).map(s => ({
                id: s.id,
                name: s.name,
                order_number: s.order_number,
                isNew: false
            }));
            sections.sort((a,b) => a.order_number - b.order_number);
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
                <input type="text" class="form-control section-name" value="${escapeHtml(sec.name)}" data-idx="${idx}" placeholder="Название раздела">
                <button class="btn btn-sm btn-outline-danger delete-section" data-idx="${idx}">🗑️</button>
            `;
            container.appendChild(div);
        });
        attachEvents();
    }

    function attachEvents() {
        document.querySelectorAll('.section-name').forEach(inp => {
            inp.removeEventListener('input', handleNameChange);
            inp.addEventListener('input', handleNameChange);
        });
        document.querySelectorAll('.delete-section').forEach(btn => {
            btn.removeEventListener('click', handleDelete);
            btn.addEventListener('click', handleDelete);
        });
    }

    function handleNameChange(e) {
        const idx = parseInt(e.target.dataset.idx);
        sections[idx].name = e.target.value;
        markUnsaved();
    }

    function handleDelete(e) {
        const idx = parseInt(e.target.dataset.idx);
        sections.splice(idx, 1);
        sections.forEach((sec, i) => sec.order_number = i + 1);
        renderSections();
        markUnsaved();
    }

    function addSection() {
        const newOrder = sections.length + 1;
        sections.push({
            id: null,
            name: '',
            order_number: newOrder,
            isNew: true
        });
        renderSections();
        markUnsaved();
    }

    addBtn.addEventListener('click', addSection);

    function markUnsaved() {
        const currentStr = JSON.stringify(sections.map(s => ({ id: s.id, name: s.name, order: s.order_number })));
        const origStr = JSON.stringify(originalSections.map(s => ({ id: s.id, name: s.name, order: s.order_number })));
        hasUnsavedChanges = currentStr !== origStr;
    }

    async function saveSections() {
        saveBtn.disabled = true;
        try {
            // Создание новых разделов
            for (const sec of sections.filter(s => s.isNew && s.name.trim())) {
                const res = await fetch(`${window.API_BASE_URL}sections/create-section`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: sec.name,
                        description: "",
                        order_number: sec.order_number,
                        course_id: courseId
                    })
                });
                if (!res.ok) throw new Error('Ошибка создания раздела');
                const data = await res.json();
                sec.id = data.id;
                sec.isNew = false;
            }
            // Обновление существующих
            for (const sec of sections.filter(s => !s.isNew)) {
                const orig = originalSections.find(o => o.id === sec.id);
                if (orig && (orig.name !== sec.name || orig.order_number !== sec.order_number)) {
                    await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            name: sec.name,
                            order_number: sec.order_number
                        })
                    });
                }
            }
            await loadSections();
            alert('Разделы сохранены');
        } catch (err) {
            alert(err.message);
        } finally {
            saveBtn.disabled = false;
        }
    }

    saveBtn.addEventListener('click', saveSections);

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    container.addEventListener('click', (e) => {
        const input = e.target.closest('.section-name');
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