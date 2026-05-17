(function() {
    const container = document.getElementById('createdCoursesList');

    function truncateWords(text, wordLimit) {
        if (!text) return '';
        const words = text.trim().split(/\s+/);
        if (words.length <= wordLimit) return text;
        return words.slice(0, wordLimit).join(' ') + '...';
    }

    async function loadCreatedCourses() {
        try {
            const response = await fetch(`${window.API_BASE_URL}courses/controlled-courses`, {
                credentials: 'include'
            });
            if (!response.ok) {
                if (response.status === 401) {
                    container.innerHTML = '<div class="text-danger">Необходимо авторизоваться</div>';
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            const courses = Array.isArray(data) ? data : (data.courses || []);

            if (!courses.length) {
                container.innerHTML = '<div class="text-muted">У вас пока нет созданных курсов.</div>';
                return;
            }

            container.innerHTML = '';
            courses.forEach(course => {
                const courseLink = document.createElement('a');
                courseLink.href = `/course/${course.id}/edit`;
                // Убраны bg-primary и text-primary, оставлены стандартные классы списка
                courseLink.className = 'list-group-item list-group-item-action border mb-2 rounded';

                const shortDescription = truncateWords(course.description, 15);
                courseLink.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${escapeHtml(course.name)}</strong>
                            ${shortDescription ? `<div class="text-secondary small mt-1">${escapeHtml(shortDescription)}</div>` : ''}
                        </div>
                        <span class="text-secondary">✎ редактировать</span>
                    </div>
                `;
                container.appendChild(courseLink);
            });
        } catch (err) {
            console.error(err);
            container.innerHTML = '<div class="text-danger">Не удалось загрузить курсы. Попробуйте позже.</div>';
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadCreatedCourses();
})();