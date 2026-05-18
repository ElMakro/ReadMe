// static/course_creation/course_form.js
(function() {
    const courseId = window.COURSE_ID;
    const titleInput = document.getElementById('courseTitle');
    const descInput = document.getElementById('courseDescription');
    const isPublicSelect = document.getElementById('isPublic');
    const isContentPublicSelect = document.getElementById('isContentPublic');
    const saveBtn = document.getElementById('saveCourseBtn');
    const deleteBtn = document.getElementById('deleteCourseBtn');
    const loadingMsg = document.getElementById('loadingMessage');

    let isSaved = false;
    let originalData = null;

    // Предотвращаем случайный уход со страницы при несохранённых изменениях
    window.addEventListener('beforeunload', (e) => {
        if (!isSaved && hasUnsavedChanges()) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    // Функция сравнения текущих данных с оригиналом
    function hasUnsavedChanges() {
        if (!originalData) return false;
        const current = {
            name: titleInput.value.trim(),
            description: descInput.value.trim(),
            is_public: isPublicSelect.value === 'true',
            is_content_public: isContentPublicSelect.value === 'true'
        };
        return JSON.stringify(current) !== JSON.stringify(originalData);
    }

    // Загрузка данных курса при редактировании
    async function loadCourseData() {
        if (!courseId) return;
        loadingMsg.style.display = 'block';
        try {
            const response = await fetch(`${window.API_BASE_URL}courses/${courseId}`, {
                credentials: 'include'
            });
            if (!response.ok) {
                if (response.status === 404) throw new Error('Курс не найден');
                throw new Error(`Ошибка загрузки: ${response.status}`);
            }
            const course = await response.json();
            // Защита от null
            if (course) {
                titleInput.value = course.name || '';
                descInput.value = course.description || '';
                isPublicSelect.value = course.is_public ? 'true' : 'false';
                isContentPublicSelect.value = course.is_content_public ? 'true' : 'false';
                originalData = {
                    name: course.name || '',
                    description: course.description || '',
                    is_public: course.is_public,
                    is_content_public: course.is_content_public
                };
                deleteBtn.style.display = 'inline-block';
            } else {
                throw new Error('Пустой ответ от сервера');
            }
        } catch (err) {
            alert('Не удалось загрузить данные курса: ' + err.message);
            console.error(err);
        } finally {
            loadingMsg.style.display = 'none';
        }
    }

    // Сохранение (создание или обновление)
    async function saveCourse() {
        const name = titleInput.value.trim();
        if (!name) {
            alert('Введите название курса');
            return;
        }

        const description = descInput.value.trim();
        const is_public = isPublicSelect.value === 'true';
        const is_content_public = isContentPublicSelect.value === 'true';
        const payload = { name, description, is_public, is_content_public };
        saveBtn.disabled = true;

        try {
            let response;
            if (courseId) {
                // Редактирование – PUT
                response = await fetch(`${window.API_BASE_URL}courses/${courseId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
            } else {
                // Создание – POST
                response = await fetch(`${window.API_BASE_URL}courses/create-course`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
            }

            if (!response.ok) {
                let errorMsg = 'Ошибка сохранения курса';
                try {
                    const errData = await response.json();
                    errorMsg = errData.detail || errorMsg;
                } catch (_) {}
                throw new Error(errorMsg);
            }

            isSaved = true;

            // Обработка ответа: для PUT (204) тела нет, для POST (201) есть JSON с id
            if (response.status === 204) {
                // Редактирование – перенаправляем на страницу разделов
                window.location.href = `/course/${courseId}/sections`;
            } else {
                const data = await response.json();
                const redirectCourseId = courseId || data.id;
                window.location.href = `/course/${redirectCourseId}/sections`;
            }
        } catch (err) {
            alert(err.message);
            saveBtn.disabled = false;
        }
    }

    // Удаление курса
    async function deleteCourse() {
        if (!courseId) return;
        if (!confirm('Вы уверены, что хотите удалить курс? Это действие необратимо.')) return;

        deleteBtn.disabled = true;
        try {
            const response = await fetch(`${window.API_BASE_URL}courses/${courseId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            if (!response.ok) {
                let errorMsg = 'Ошибка удаления курса';
                try {
                    const errData = await response.json();
                    errorMsg = errData.detail || errorMsg;
                } catch (_) {}
                throw new Error(errorMsg);
            }
            isSaved = true;
            window.location.href = '/created-courses';
        } catch (err) {
            alert(err.message);
            deleteBtn.disabled = false;
        }
    }

    // Автоматическое изменение высоты textarea
    function autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    // Инициализация
    if (descInput) {
        descInput.addEventListener('input', function() { autoResize(this); });
        autoResize(descInput);
    }

    saveBtn.addEventListener('click', saveCourse);
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteCourse);
    }

    // Если редактируем существующий курс – загружаем данные
    if (courseId) {
        loadCourseData();
    } else {
        // Для нового курса оригинальные данные – пустая форма
        originalData = {
            name: '',
            description: '',
            is_public: true,
            is_content_public: true
        };
        deleteBtn.style.display = 'none';
    }
})();