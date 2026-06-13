// static/notes.js
(function () {
    const API_BASE = window.API_BASE_URL || '';

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
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) throw new Error('Для работы с заметками необходимо войти в систему.');
                throw new Error(`HTTP ${resp.status}`);
            }
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
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({note_id: noteId, topic_id: topicId, name, content})
                });
                if (!resp.ok) {
                    if (resp.status === 401 || resp.status === 403) throw new Error('Для работы с заметками необходимо войти в систему.');
                    if (resp.status === 409) throw new Error('Конспект не принадлежит вам или уже изменён');
                    throw new Error(`Update failed: ${resp.status}`);
                }
                return {success: true, noteId};
            } else {
                const resp = await fetch(`${API_BASE}notes/create-note`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({topic_id: topicId, name, content})
                });
                if (!resp.ok) {
                    if (resp.status === 401 || resp.status === 403) throw new Error('Для работы с заметками необходимо войти в систему.');
                    // FIX: более понятное сообщение для 409
                    if (resp.status === 409) throw new Error('Конспект для этой темы уже существует');
                    throw new Error(`Create failed: ${resp.status}`);
                }
                const data = await resp.json();
                return {success: true, noteId: data.id};
            }
        } catch (err) {
            console.error('saveNote error:', err);
            window.showToast('Не удалось сохранить конспект: ' + err.message, 'danger');
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
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) throw new Error('Доступ запрещён');
                if (resp.status === 404) throw new Error('Конспект не найден');
                throw new Error(`Delete failed: ${resp.status}`);
            }
            window.showToast('Конспект удалён');
            return true;
        } catch (err) {
            console.error('deleteNote error:', err);
            window.showToast('Ошибка удаления конспекта: ' + err.message, 'danger');
            throw err;
        }
    }

    async function getMyNotes(page = 1, perPage = 9) {
        const url = `${API_BASE}notes/my-notes?page=${page}&records_per_page=${perPage}`;
        const resp = await fetch(url, {credentials: 'include'});
        if (!resp.ok) {
            if (resp.status === 401 || resp.status === 403) throw new Error('Для работы с заметками необходимо войти в систему.');
            if (resp.status === 422) throw new Error('Ошибка валидации параметров');
            throw new Error(`HTTP ${resp.status}`);
        }
        const data = await resp.json();
        return Array.isArray(data) ? data : [];
    }

    async function getCourseIdByTopicId(topicId) {
        try {
            const resp = await fetch(`${API_BASE}topics/${topicId}`, {
                credentials: 'include'
            });
            if (!resp.ok) {
                if (resp.status === 404) return null;
                throw new Error(`HTTP ${resp.status}`);
            }
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
        let pagination = null;
        const perPage = 9;

        async function loadNotes(page) {
            container.innerHTML = '<div class="text-muted text-center py-4">Загрузка...</div>';
            try {
                const notes = await getMyNotes(page, perPage);
                if (!notes.length) {
                    container.innerHTML = '<div class="text-muted text-center py-4">У вас пока нет сохранённых конспектов.</div>';
                    if (pagination) pagination.hide();
                    return;
                }
                renderNotes(notes);
                const hasNext = notes.length === perPage;
                const total = hasNext ? page + 1 : page;
                if (pagination) {
                    pagination.setTotalPages(total);
                    pagination.setPage(page, true);
                }
            } catch (err) {
                if (err.message === 'Доступ запрещён') {
                    window.showAccessDenied(container, err.message, true, pagination);
                } else {
                    container.innerHTML = `<div class="text-danger text-center py-4">${err.message}</div>`;
                    if (pagination) pagination.hide();
                }
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
                        window.showToast('Не удалось определить курс для этой темы', 'danger');
                    }
                });

                const deleteBtn = card.querySelector('.delete-note-btn');
                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm('Удалить этот конспект?')) {
                        await deleteNote(note.id);
                        loadNotes(pagination?.currentPage || 1);
                    }
                });

                container.appendChild(card);
            }
        }

        const paginationContainer = document.getElementById('paginationContainer');
        if (paginationContainer) {
            pagination = new Pagination(paginationContainer, (page) => loadNotes(page), {pageSize: perPage});
        }
        await loadNotes(1);
    }

    window.Notes = {
        loadNoteForTopic,
        saveNote,
        deleteNote,
        getMyNotes,
        initMyNotesPage,
        onTopicChanged: null
    };

    if (document.getElementById('notesList')) {
        document.addEventListener('DOMContentLoaded', () => {
            window.Notes.initMyNotesPage();
        });
    }
})();