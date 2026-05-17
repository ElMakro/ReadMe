// static/my-courses.js
(function() {
    const grid = document.getElementById('myCoursesGrid');

    async function fetchMyCourses() {
        try {
            const response = await fetch(`${window.API_BASE_URL}courses/followed-courses`, {
                credentials: 'include'
            });
            if (!response.ok) throw new Error('Не удалось загрузить курсы');
            const courses = await response.json();
            renderCourses(courses);
        } catch (error) {
            console.error(error);
            grid.innerHTML = '<div class="col-12 text-center text-danger">Ошибка загрузки курсов</div>';
        }
    }

    function renderCourses(courses) {
        if (!courses.length) {
            grid.innerHTML = '<div class="col-12 text-center">Вы пока не записались ни на один курс. Пора это исправить!</div>';
            return;
        }
        grid.innerHTML = '';
        courses.forEach(course => {
            const col = document.createElement('div');
            col.className = 'col';
            col.innerHTML = `
                <div class="course-card">
                    <a href="/course/${course.id}/sections" class="stretched-link text-decoration-none">
                        <h5 class="course-title">${escapeHtml(course.title)}</h5>
                        <p class="course-description">Курс ID: ${course.id}</p>
                    </a>
                </div>
            `;
            grid.appendChild(col);
        });
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    fetchMyCourses();
})();