(function() {
    const titleInput = document.getElementById('courseTitle');
    const descInput = document.getElementById('courseDescription');
    const saveBtn = document.getElementById('saveCourseBtn');
    let isSaved = false;

    window.addEventListener('beforeunload', (e) => {
        if (!isSaved && (titleInput.value.trim() !== '' || (descInput && descInput.value.trim() !== ''))) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    saveBtn.addEventListener('click', async () => {
        const name = titleInput.value.trim();
        if (!name) {
            alert('Введите название курса');
            return;
        }

        // Получаем описание (если поле есть)
        const description = descInput ? descInput.value.trim() : "";

        saveBtn.disabled = true;
        try {
            const response = await fetch(`${window.API_BASE_URL}courses/create-course`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    name: name,
                    description: description,
                    is_open: true
                })
            });
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'Ошибка создания курса');
            }
            const data = await response.json();   // { id: "uuid" }
            isSaved = true;
            window.location.href = `/course/${data.id}/sections`;
        } catch (err) {
            alert(err.message);
            saveBtn.disabled = false;
        }
    });

    // Добавить в create_course.js после получения элементов
    function autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    descInput.addEventListener('input', function() { autoResize(this); });
    // Вызвать один раз при загрузке
    autoResize(descInput);
})();