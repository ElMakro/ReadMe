// static/admin/courses.js
(function() {
    const container = document.getElementById('coursesList');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');

    let currentPage = 1;
    const limit = 9;
    let totalPages = 1;
    let isLoading = false;
    let currentUserRole = null;

    function hidePagination() {
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
        if (pageInfoSpan) pageInfoSpan.style.display = 'none';
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function truncateWords(text, wordLimit) {
        if (!text) return '';
        const words = text.trim().split(/\s+/);
        if (words.length <= wordLimit) return text;
        return words.slice(0, wordLimit).join(' ') + '…';
    }

    function adjustIconHeights() {
        const cards = document.querySelectorAll('#coursesList .list-group-item');
        cards.forEach(card => {
            const icon = card.querySelector('img:first-child');
            const textBlock = card.querySelector('.flex-grow-1');
            if (icon && textBlock && icon.style.display !== 'none') {
                const textHeight = textBlock.offsetHeight;
                icon.style.width = textHeight + 'px';
                icon.style.height = textHeight + 'px';
                icon.style.objectFit = 'cover';
                icon.style.borderRadius = '16px';
                icon.style.flexShrink = '0';
            }
        });
    }

    function scheduleIconAdjustment() {
        const imgs = document.querySelectorAll('#coursesList img');
        let pending = imgs.length;
        if (pending === 0) {
            setTimeout(adjustIconHeights, 50);
            return;
        }
        function done() {
            pending--;
            if (pending === 0) {
                setTimeout(adjustIconHeights, 50);
            }
        }
        imgs.forEach(img => {
            if (img.complete) done();
            else {
                img.addEventListener('load', done);
                img.addEventListener('error', done);
            }
        });
    }

    function renderCourses(coursesArray) {
        if (!coursesArray.length) {
            container.innerHTML = '<p class="text-muted text-center mt-4">Курсы не найдены</p>';
            return;
        }
        container.innerHTML = '';
        coursesArray.forEach(course => {
            const card = document.createElement('div');
            card.className = 'list-group-item list-group-item-action border mb-2 rounded';
            card.style.cursor = 'pointer';
            card.setAttribute('data-course-id', course.id);

            const shortDescription = truncateWords(course.description || '', 15);

            card.innerHTML = `
                <div class="course-item-container">
                    <div class="course-item-info">
                        <div class="d-flex align-items-start gap-3">
                            <img src="${window.API_BASE_URL}courses/${course.id}/icon" class="course-thumb">
                            <div class="course-details">
                                <strong class="course-name">${escapeHtml(course.name)}</strong>
                                ${shortDescription ? `<div class="text-secondary small mt-1">${escapeHtml(shortDescription)}</div>` : ''}
                                ${course.tags && course.tags.length ? `<div class="small text-muted mt-1">Теги: ${course.tags.map(t => escapeHtml(t)).join(', ')}</div>` : ''}
                                <div class="small text-muted mt-1">
                                    ${course.is_public ? 'Публичный' : 'Закрытый'} |
                                    ${course.is_content_public ? 'Контент открыт' : 'Контент скрыт'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            card.addEventListener('click', () => {
                window.location.href = `/admin/course/${course.id}/users`;
            });

            container.appendChild(card);
        });
        scheduleIconAdjustment();
    }

    async function checkUserRole() {
        try {
            const resp = await fetch(`${window.API_BASE_URL}users/profile`, { credentials: 'include' });
            if (resp.ok) {
                const profile = await resp.json();
                currentUserRole = profile.role;

                if (currentUserRole === 'student') {
                    window.showAccessDenied(container, 'Управление курсами доступно только администраторам и преподавателям.', false);
                    hidePagination();
                    return false;
                }
                return true;
            } else if (resp.status === 401) {
                window.showAccessDenied(container, 'Необходимо войти в систему для просмотра этой страницы.', true);
                hidePagination();
                return false;
            } else {
                throw new Error('Не удалось получить профиль');
            }
        } catch (err) {
            window.showAccessDenied(container, `Ошибка авторизации: ${err.message}.`, true);
            hidePagination();
            return false;
        }
    }

    async function loadCourses(page) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';
        try {
            let url;
            if (currentUserRole === 'professor') {
                url = `${window.API_BASE_URL}courses/controlled-courses?page=${page}&records_per_page=${limit}`;
            } else {
                url = `${window.API_BASE_URL}courses/search?criteria=name_prefix&value=&page=${page}&records_per_page=${limit}`;
            }

            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) throw new Error('Доступ запрещён');
                if (resp.status === 400) throw new Error('Неправильный критерий поиска');
                if (resp.status === 422) throw new Error('Ошибка валидации параметров');
                throw new Error(`HTTP ${resp.status}`);
            }

            const coursesData = await resp.json();
            const coursesArray = Array.isArray(coursesData) ? coursesData : (coursesData.items || []);

            renderCourses(coursesArray);
            const hasNext = coursesArray.length === limit;
            totalPages = hasNext ? page + 1 : page;
            updatePagination(page, totalPages);
        } catch (err) {
            window.showAccessDenied(container, err.message, err.message.includes('Доступ запрещён') || err.message.includes('авторизации'));
            hidePagination();
        } finally {
            isLoading = false;
        }
    }

    function updatePagination(page, total) {
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= total;
        if (pageInfoSpan) pageInfoSpan.textContent = `Страница ${page} из ${total}`;
        currentPage = page;
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1 && !isLoading) loadCourses(currentPage - 1);
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentPage < totalPages && !isLoading) loadCourses(currentPage + 1);
        });
    }

    async function init() {
        const hasAccess = await checkUserRole();
        if (hasAccess) {
            loadCourses(1);
        }
    }

    init();

    window.addEventListener('resize', () => {
        scheduleIconAdjustment();
    });
})();