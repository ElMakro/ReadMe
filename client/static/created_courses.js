(function() {
        const container = document.getElementById('createdCoursesList');

        async function loadCreatedCourses() {
            try {
                const response = await fetch('/api/courses/created', {
                    credentials: 'include'
                });
                if (!response.ok) throw new Error('Ошибка загрузки');
                const courses = await response.json();

                if (!courses.length) {
                    container.innerHTML = '<div class="text-muted">У вас пока нет созданных курсов.</div>';
                    return;
                }

                container.innerHTML = '';
                courses.forEach(course => {
                    const courseLink = document.createElement('a');
                    courseLink.href = `/course/${course.id}/sections`;
                    courseLink.className = 'list-group-item list-group-item-action bg-primary text-primary border mb-2 rounded';
                    courseLink.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <strong>${escapeHtml(course.title)}</strong>
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