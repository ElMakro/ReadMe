// static/notes.js
(function() {
    const API_BASE = window.API_BASE_URL || '';

    function showMessage(text, isError = false) {
        const existing = document.getElementById('notesToast');
        if (existing) existing.remove();
        const div = document.createElement('div');
        div.id = 'notesToast';
        div.textContent = text;
        div.style.position = 'fixed';
        div.style.bottom = '20px';
        div.style.left = '50%';
        div.style.transform = 'translateX(-50%)';
        div.style.backgroundColor = isError ? '#dc3545' : '#28a745';
        div.style.color = 'white';
        div.style.padding = '8px 16px';
        div.style.borderRadius = '8px';
        div.style.zIndex = 10000;
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 2500);
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function loadNoteForTopic(topicId) {
        if (!topicId) return null;
        try {
            const resp = await fetch(`${API_BASE}notes/get-note-for-topic/${topicId}`, {
                credentials: 'include'
            });
            if (resp.status === 204) return null;
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return await resp.json();
        } catch (err) {
            console.warn('loadNoteForTopic error:', err);
            return null;
        }
    }

    async function saveNote(topicId, content, noteId = null, name = 'Конспект') {
        if (!topicId) throw new Error('topicId required');
        try {
            if (noteId) {
                const resp = await fetch(`${API_BASE}notes/update-note`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ note_id: noteId, topic_id: topicId, name, content })
                });
                if (!resp.ok) throw new Error(`Update failed: ${resp.status}`);
                return { success: true, noteId };
            } else {
                const resp = await fetch(`${API_BASE}notes/create-note`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ topic_id: topicId, name, content })
                });
                if (!resp.ok) throw new Error(`Create failed: ${resp.status}`);
                const data = await resp.json();
                return { success: true, noteId: data.id };
            }
        } catch (err) {
            console.error('saveNote error:', err);
            showMessage('Не удалось сохранить конспект: ' + err.message, true);
            throw err;
        }
    }

    async function deleteNote(noteId) {
        if (!noteId) throw new Error('noteId required');
        try {
            const resp = await fetch(`${API_BASE}notes/delete-note/${noteId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            if (!resp.ok) throw new Error(`Delete failed: ${resp.status}`);
            showMessage('Конспект удалён');
            return true;
        } catch (err) {
            console.error('deleteNote error:', err);
            showMessage('Ошибка удаления конспекта', true);
            throw err;
        }
    }

    async function getMyNotes(page = 1, perPage = 10) {
        const url = `${API_BASE}notes/my-notes?page=${page}&records_per_page=${perPage}`;
        const resp = await fetch(url, { credentials: 'include' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        return Array.isArray(data) ? data : [];
    }

    async function getCourseIdByTopicId(topicId) {
        try {
            const resp = await fetch(`${API_BASE}topics/${topicId}`, {
                credentials: 'include'
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const topic = await resp.json();
            return topic.course_id;
        } catch (err) {
            console.error('getCourseIdByTopicId error:', err);
            return null;
        }
    }

    async function initMyNotesPage() {
        const container = document.getElementById('notesList');
        if (!container) return;
        const prevBtn = document.getElementById('prevNotesPage');
        const nextBtn = document.getElementById('nextNotesPage');
        const pageInfoSpan = document.getElementById('notesPageInfo');
        const paginationDiv = document.getElementById('notesPagination');

        let currentPage = 1;
        const perPage = 10;
        let totalPages = 0;

        async function loadNotes(page) {
            container.innerHTML = '<div class="text-muted text-center py-4">Загрузка...</div>';
            try {
                const notes = await getMyNotes(page, perPage);
                if (!notes.length) {
                    container.innerHTML = '<div class="text-muted text-center py-4">У вас пока нет сохранённых конспектов.</div>';
                    if (paginationDiv) paginationDiv.style.display = 'none';
                    return;
                }
                const hasNext = notes.length === perPage;
                totalPages = hasNext ? page + 1 : page;
                renderNotes(notes);
                updatePagination(page, totalPages);
                if (paginationDiv) paginationDiv.style.display = 'flex';
            } catch (err) {
                console.error(err);
                container.innerHTML = '<div class="text-danger text-center py-4">Ошибка загрузки заметок</div>';
                if (paginationDiv) paginationDiv.style.display = 'none';
            }
        }

        function renderNotes(notes) {
            container.innerHTML = '';
            for (const note of notes) {
                const topicId = note.topic_id;
                const card = document.createElement('div');
                card.className = 'list-group-item list-group-item-action border mb-2 rounded';
                card.style.cursor = 'pointer';
                card.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${escapeHtml(note.name)}</strong>
                            <div class="small text-muted">Тема: ${escapeHtml(note.topic_name)}</div>
                        </div>
                        <button class="btn btn-sm btn-outline-danger delete-note-btn" data-id="${note.id}" style="padding: 2px 8px;">Удалить</button>
                    </div>
                    <div class="small text-secondary mt-1">${escapeHtml(note.content.substring(0, 100))}${note.content.length > 100 ? '…' : ''}</div>
                `;

                card.addEventListener('click', async (e) => {
                    if (e.target.classList.contains('delete-note-btn')) return;
                    let courseId = note.course_id;
                    if (!courseId) {
                        courseId = await getCourseIdByTopicId(topicId);
                    }
                    if (courseId) {
                        window.location.href = `/course/${courseId}?topic=${topicId}`;
                    } else {
                        showMessage('Не удалось определить курс для этой темы', true);
                    }
                });

                const deleteBtn = card.querySelector('.delete-note-btn');
                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm('Удалить этот конспект?')) {
                        await deleteNote(note.id);
                        loadNotes(currentPage);
                    }
                });

                container.appendChild(card);
            }
        }

        function updatePagination(page, total) {
            if (prevBtn) prevBtn.disabled = page <= 1;
            if (nextBtn) nextBtn.disabled = page >= total;
            if (pageInfoSpan) pageInfoSpan.textContent = `Страница ${page} из ${total}`;
            currentPage = page;
        }

        if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1) loadNotes(currentPage - 1); });
        if (nextBtn) nextBtn.addEventListener('click', () => { if (currentPage < totalPages) loadNotes(currentPage + 1); });

        await loadNotes(1);
    }

    window.Notes = {
        loadNoteForTopic,
        saveNote,
        deleteNote,
        getMyNotes,
        initMyNotesPage,
        showMessage,
        escapeHtml,
        onTopicChanged: null
    };

    if (document.getElementById('notesList')) {
        document.addEventListener('DOMContentLoaded', () => {
            window.Notes.initMyNotesPage();
        });
    }
})();