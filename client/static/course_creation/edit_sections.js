// static/course_creation/edit_sections.js
(function() {
    const courseId = window.COURSE_ID;
    const container = document.getElementById('sectionsList');
    const addBtn = document.getElementById('addSectionBtn');
    const saveBtn = document.getElementById('saveSectionsBtn');
    const breadcrumbCourse = document.getElementById('courseTitleBreadcrumb')

    let sections = [];           // текущий список разделов на форме
    let originalSections = [];   // копия при загрузке для отслеживания удалений
    let hasUnsavedChanges = false;

    // Загрузка названия курса
    async function loadCourseTitle() {
        if (!breadcrumbCourse) return;
        try {
            const res = await fetch(`${window.API_BASE_URL}courses/${courseId}`, {
                credentials: 'include'
            });
            if (res.ok) {
                const course = await res.json();
                if (course && course.name) {
                    breadcrumbCourse.textContent = course.name;
                }
            }
        } catch (err) {
            console.warn('Не удалось загрузить название курса:', err);
        }
    }

    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    async function loadSections() {
        try {
            const res = await fetch(`${window.API_BASE_URL}sections/by_course/${courseId}`, {
                credentials: 'include'
            });
            if (!res.ok) {
                let errorMsg = `HTTP ${res.status}`;
                try {
                    const errData = await res.json();
                    errorMsg = errData.detail || errorMsg;
                } catch(e) {}
                throw new Error(errorMsg);
            }
            const data = await res.json();
            // Защита от null или отсутствия поля sections
            sections = (data && Array.isArray(data.sections)) ? data.sections.map(s => ({
                id: s.id,
                name: s.name,
                description: s.description || '',
                order_number: s.order_number,
                isNew: false
            })) : [];
            sections.sort((a,b) => a.order_number - b.order_number);
            originalSections = JSON.parse(JSON.stringify(sections));
            renderSections();
            hasUnsavedChanges = false;
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
        sections.forEach((sec, idx) => {
            const div = document.createElement('div');
            div.className = 'card mb-3 bg-secondary border-0 shadow-sm';
            div.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <input type="text" class="form-control section-name mb-2" value="${escapeHtml(sec.name)}" data-idx="${idx}" placeholder="Название раздела" style="flex: 1;">
                        <button class="btn btn-sm btn-outline-danger delete-section ms-2" data-idx="${idx}">🗑️</button>
                    </div>
                    <textarea class="form-control section-description" rows="2" data-idx="${idx}" placeholder="Описание раздела (необязательно)">${escapeHtml(sec.description)}</textarea>
                </div>
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
        document.querySelectorAll('.section-description').forEach(ta => {
            ta.removeEventListener('input', handleDescChange);
            ta.addEventListener('input', handleDescChange);
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

    function handleDescChange(e) {
        const idx = parseInt(e.target.dataset.idx);
        sections[idx].description = e.target.value;
        markUnsaved();
    }

    function handleDelete(e) {
        const idx = parseInt(e.target.dataset.idx);
        sections.splice(idx, 1);
        // перенумеровать порядок
        sections.forEach((sec, i) => sec.order_number = i + 1);
        renderSections();
        markUnsaved();
    }

    function addSection() {
        const newOrder = sections.length + 1;
        sections.push({
            id: null,
            name: '',
            description: '',
            order_number: newOrder,
            isNew: true
        });
        renderSections();
        markUnsaved();
    }

    addBtn.addEventListener('click', addSection);

    function markUnsaved() {
        // Просто сравниваем строковые представления для упрощения
        const currentStr = JSON.stringify(sections.map(s => ({ id: s.id, name: s.name, desc: s.description, order: s.order_number })));
        const origStr = JSON.stringify(originalSections.map(s => ({ id: s.id, name: s.name, desc: s.description, order: s.order_number })));
        hasUnsavedChanges = currentStr !== origStr;
    }

    async function saveSections() {
        saveBtn.disabled = true;
        try {
            // 1. Удалить разделы, которых нет в текущем списке
            const currentIds = sections.filter(s => s.id !== null).map(s => s.id);
            const toDelete = originalSections.filter(orig => !currentIds.includes(orig.id));
            for (const del of toDelete) {
                const res = await fetch(`${window.API_BASE_URL}sections/${del.id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (!res.ok) throw new Error(`Ошибка удаления раздела ${del.id}`);
            }

            // 2. Создать новые разделы
            for (const sec of sections.filter(s => s.id === null && s.name.trim() !== '')) {
                const res = await fetch(`${window.API_BASE_URL}sections/create-section`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: sec.name,
                        description: sec.description,
                        order_number: sec.order_number,
                        course_id: courseId
                    })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Ошибка создания раздела');
                }
                // id получим при перезагрузке
            }

            // 3. Обновить существующие разделы (все, у которых есть id)
            for (const sec of sections.filter(s => s.id !== null)) {
                const payload = {
                    name: sec.name,
                    description: sec.description,
                    order_number: sec.order_number
                };
                const res = await fetch(`${window.API_BASE_URL}sections/${sec.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || `Ошибка обновления раздела ${sec.id}`);
                }
            }

            // 4. Перезагрузить список с сервера
            await loadSections();
            alert('Разделы успешно сохранены');
        } catch (err) {
            alert('Ошибка сохранения: ' + err.message);
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

    // Клик по названию раздела (только для существующих) → переход к темам
    container.addEventListener('click', (e) => {
        const nameInput = e.target.closest('.section-name');
        if (!nameInput) return;
        const idx = parseInt(nameInput.dataset.idx);
        const section = sections[idx];
        if (section.id) {
            if (hasUnsavedChanges && !confirm('Есть несохранённые изменения. Перейти всё равно?')) return;
            window.location.href = `/course/${courseId}/section/${section.id}/topics`;
        } else {
            alert('Сначала сохраните раздел');
        }
    });

    loadCourseTitle();
    loadSections();
})();