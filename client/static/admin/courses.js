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
            container.innerHTML = '<p class="text-muted text-center">Курсы не найдены</p>';
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
                            <img src="${window.API_BASE_URL}courses/${course.id}/icon"
                                 class="course-thumb">
                            <div class="course-details">
                                <strong class="course-name">${escapeHtml(course.name)}</strong>
                                ${shortDescription ? `<div class="text-secondary small mt-1">${escapeHtml(shortDescription)}</div>` : ''}
                                ${course.tags && course.tags.length ? `<div class="small text-muted mt-1">Теги: ${course.tags.map(t => escapeHtml(t)).join(' ')}</div>` : ''}
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

    async function loadCourses(page) {
        if (isLoading) return;
        isLoading = true;
        container.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-accent"></div></div>';
        try {
            const params = new URLSearchParams({
                criteria: 'name_prefix',
                value: '',
                page: page,
                records_per_page: limit
            });
            const resp = await fetch(`${window.API_BASE_URL}courses/search?${params}`, { credentials: 'include' });
            if (!resp.ok) throw new Error('Ошибка загрузки курсов');
            const coursesData = await resp.json();
            const coursesArray = Array.isArray(coursesData) ? coursesData : (coursesData.items || []);
            renderCourses(coursesArray);
            const hasNext = coursesArray.length === limit;
            totalPages = hasNext ? page + 1 : page;
            updatePagination(page, totalPages);
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
        } finally {
            isLoading = false;
        }
    }

    function updatePagination(page, total) {
        prevBtn.disabled = page <= 1;
        nextBtn.disabled = page >= total;
        pageInfoSpan.textContent = `Страница ${page} из ${total}`;
        currentPage = page;
    }

    prevBtn.addEventListener('click', () => {
        if (currentPage > 1 && !isLoading) loadCourses(currentPage - 1);
    });
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages && !isLoading) loadCourses(currentPage + 1);
    });

    loadCourses(1);

    window.addEventListener('resize', () => {
        scheduleIconAdjustment();
    });
})();