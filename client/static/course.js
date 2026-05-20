// ========== ОСНОВНАЯ ЛОГИКА ОТОБРАЖЕНИЯ КУРСА ==========
(function() {
    const courseTitleHeader = document.getElementById('courseTitleHeader');
    const sectionList = document.getElementById('sectionList');
    const topicContent = document.getElementById('topicContent');
    const checkYourselfBtn = document.getElementById('checkYourselfBtn');

    let currentCourse = null;
    let currentTopicId = null;
    const renderedCache = new Map();

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Описание курса
    function showCourseDescription() {
        if (!currentCourse) {
            topicContent.innerHTML = '<p class="text-muted">Информация о курсе загружается...</p>';
            return;
        }
        const html = `
            <div class="course-description-block">
                <h2>${escapeHtml(currentCourse.name)}</h2>
                <p>${escapeHtml(currentCourse.description || 'Описание отсутствует')}</p>
            </div>
        `;
        topicContent.innerHTML = html;
        currentTopicId = null;
        window.activeTopicId = null;
        document.querySelectorAll('.topic-link').forEach(link => link.classList.remove('active'));
    }

    // Описание раздела
    function showSectionDescription(sectionId, sectionName, sectionDescription) {
        const html = `
            <div class="section-description-block">
                <h2>${escapeHtml(sectionName)}</h2>
                <p>${escapeHtml(sectionDescription || 'Описание отсутствует')}</p>
            </div>
        `;
        topicContent.innerHTML = html;
        currentTopicId = null;
        window.activeTopicId = null;
        document.querySelectorAll('.topic-link').forEach(link => link.classList.remove('active'));
    }

    // Загрузка и отображение темы
    async function displayTopic(topicId, topicName) {
        if (!topicId) return;
        topicContent.innerHTML = '<div class="text-muted">Загрузка...</div>';
        currentTopicId = topicId;
        window.activeTopicId = topicId;

        if (renderedCache.has(topicId)) {
            renderTopicContent(renderedCache.get(topicId));
            return;
        }

        try {
            const url = `${window.API_BASE_URL}topics/${topicId}/rendered`;
            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    topicContent.innerHTML = '<p class="text-danger">Для просмотра этой темы необходимо <a href="/">войти в систему</a>.</p>';
                    return;
                }
                throw new Error(`HTTP ${resp.status}`);
            }
            const data = await resp.json();
            renderedCache.set(topicId, data);
            renderTopicContent(data);
        } catch (err) {
            console.error('Ошибка загрузки темы:', err);
            topicContent.innerHTML = '<p class="text-muted">Содержимое темы временно недоступно.</p>';
        }
    }

    function renderTopicContent(contentData) {
        if (!contentData || !contentData.blocks || contentData.blocks.length === 0) {
            topicContent.innerHTML = '<p class="text-muted">Тема не содержит контента.</p>';
            return;
        }
        let html = '<div class="topic-blocks">';
        for (const block of contentData.blocks) {
            let blockHtml = block.rendered_content || '<p class="text-muted">(пустой блок)</p>';
            html += `<div class="topic-block topic-block-type-${block.type}">${blockHtml}</div>`;
        }
        html += '</div>';
        topicContent.innerHTML = html;

        if (window.MathJax) MathJax.typesetPromise && MathJax.typesetPromise();
        if (window.mermaid) mermaid.init && mermaid.init(undefined, document.querySelectorAll('.topic-block-type-uml'));
    }

    // Построение бокового меню
    async function buildSidebar() {
        if (!sectionList) return;
        sectionList.innerHTML = '<li class="list-group-item text-muted">Загрузка...</li>';

        try {
            const url = `${window.API_BASE_URL}sections/by_course/${window.COURSE_ID}`;
            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    sectionList.innerHTML = '<li class="list-group-item text-danger">Для просмотра содержания курса необходимо <a href="/">войти</a>.</li>';
                    return;
                }
                throw new Error(`Sections HTTP ${resp.status}`);
            }
            const sections = await resp.json();
            if (!sections || sections.length === 0) {
                sectionList.innerHTML = '<li class="list-group-item text-muted">В курсе пока нет разделов.</li>';
                return;
            }

            sections.sort((a, b) => a.order_number - b.order_number);
            sectionList.innerHTML = '';

            for (const section of sections) {
                const li = document.createElement('li');
                li.className = 'list-group-item section-item p-0';

                const toggle = document.createElement('div');
                toggle.className = 'section-toggle';
                toggle.innerHTML = `<span class="toggle-icon">▼</span><span>${escapeHtml(section.name)}</span>`;
                toggle.style.cursor = 'pointer';

                const topicsContainer = document.createElement('div');
                topicsContainer.className = 'section-topics';
                topicsContainer.style.display = 'block';

                // Загружаем темы раздела
                try {
                    const topicsUrl = `${window.API_BASE_URL}topics/by-section/${section.id}`;
                    const topicsResp = await fetch(topicsUrl, { credentials: 'include' });
                    if (!topicsResp.ok) {
                        if (topicsResp.status === 401 || topicsResp.status === 403) {
                            topicsContainer.innerHTML = '<div class="text-danger small p-2">Недостаточно прав для загрузки тем</div>';
                        } else {
                            topicsContainer.innerHTML = '<div class="text-muted small p-2">Ошибка загрузки тем</div>';
                        }
                    } else {
                        const data = await topicsResp.json();
                        const topics = data.topics || [];
                        topics.sort((a, b) => a.order_number - b.order_number);
                        if (topics.length === 0) {
                            topicsContainer.innerHTML = '<div class="text-muted small p-2">Нет тем</div>';
                        } else {
                            const ul = document.createElement('ul');
                            ul.className = 'list-unstyled mb-0';
                            for (const topic of topics) {
                                const liTopic = document.createElement('li');
                                const link = document.createElement('a');
                                link.href = '#';
                                link.className = 'topic-link';
                                link.dataset.topicId = topic.id;
                                link.textContent = topic.name;
                                link.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    document.querySelectorAll('.topic-link').forEach(l => l.classList.remove('active'));
                                    link.classList.add('active');
                                    displayTopic(topic.id, topic.name);
                                });
                                liTopic.appendChild(link);
                                ul.appendChild(liTopic);
                            }
                            topicsContainer.appendChild(ul);
                        }
                    }
                } catch (err) {
                    console.error(`Ошибка тем раздела ${section.id}:`, err);
                    topicsContainer.innerHTML = '<div class="text-muted small p-2">Темы недоступны</div>';
                }

                // Обработчик клика по разделу: показать описание раздела и переключить сворачивание
                let expanded = true;
                const sectionToggleHandler = () => {
                    showSectionDescription(section.id, section.name, section.description);
                    expanded = !expanded;
                    topicsContainer.style.display = expanded ? 'block' : 'none';
                    const icon = toggle.querySelector('.toggle-icon');
                    if (icon) icon.textContent = expanded ? '▼' : '▶';
                };
                toggle.addEventListener('click', sectionToggleHandler);

                li.appendChild(toggle);
                li.appendChild(topicsContainer);
                sectionList.appendChild(li);
            }
        } catch (err) {
            console.error('Ошибка загрузки разделов:', err);
            sectionList.innerHTML = '<li class="list-group-item text-muted">Не удалось загрузить разделы</li>';
        }
    }

    async function loadCourseInfo() {
        if (!courseTitleHeader) return;
        courseTitleHeader.textContent = 'Загрузка...';
        try {
            const url = `${window.API_BASE_URL}courses/${window.COURSE_ID}`;
            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    topicContent.innerHTML = '<div class="alert alert-warning">Для просмотра этого курса необходимо <a href="/">войти в систему</a>.</div>';
                    courseTitleHeader.textContent = 'Доступ ограничен';
                    if (sectionList) sectionList.innerHTML = '<li class="list-group-item text-muted">Содержимое курса недоступно</li>';
                    return;
                }
                throw new Error(`Course HTTP ${resp.status}`);
            }
            currentCourse = await resp.json();
            courseTitleHeader.textContent = escapeHtml(currentCourse.name);
            // После успешной загрузки курса показываем его описание и пытаемся загрузить разделы
            showCourseDescription();
            await buildSidebar();  // бэкенд сам решит, можно ли показывать разделы
        } catch (err) {
            console.error('Ошибка загрузки курса:', err);
            courseTitleHeader.textContent = 'Курс не найден';
            topicContent.innerHTML = '<p class="text-muted">Не удалось загрузить курс. Попробуйте позже.</p>';
        }
    }

    function setupCheckYourself() {
        if (!checkYourselfBtn) return;
        checkYourselfBtn.addEventListener('click', () => {
            if (currentTopicId) {
                alert(`Функция «Проверить себя» для темы ID: ${currentTopicId} в разработке.`);
            } else {
                alert('Сначала выберите тему из меню.');
            }
        });
    }

    function setupCourseTitleClick() {
        if (!courseTitleHeader) return;
        courseTitleHeader.style.cursor = 'pointer';
        courseTitleHeader.addEventListener('click', () => {
            if (currentCourse) {
                showCourseDescription();
                document.querySelectorAll('.topic-link').forEach(link => link.classList.remove('active'));
            }
        });
    }

    async function init() {
        if (!window.COURSE_ID) {
            console.error('COURSE_ID не задан');
            return;
        }
        await loadCourseInfo();
        setupCheckYourself();
        setupCourseTitleClick();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

// ========== ПЛАВАЮЩЕЕ ОКНО КОНСПЕКТА ==========
(function() {
    const win = document.getElementById('floatingWindow');
    const tabBtn = document.getElementById('floatingTabButton');
    const closeBtn = document.getElementById('closeWindowBtn');
    const saveBtn = document.getElementById('saveConspectBtn');
    const textarea = win?.querySelector('.conspect-content');
    const header = document.getElementById('windowHeader');
    if (!win || !tabBtn) return;

    let isOpen = false;

    function getContainerBounds() {
        const mainContent = document.querySelector('.main-content');
        if (!mainContent) return { left: 20, top: 20, right: window.innerWidth - 20, bottom: window.innerHeight - 20 };
        const rect = mainContent.getBoundingClientRect();
        return {
            left: rect.left + 10,
            top: rect.top + 10,
            right: rect.right - 10,
            bottom: rect.bottom - 10
        };
    }

    function getStorageKey() {
        let course = window.COURSE_ID;
        let topic = window.activeTopicId;
        return course && topic ? `conspect_${course}_${topic}` : null;
    }
    function loadConspect() {
        let key = getStorageKey();
        if (key && textarea) textarea.value = localStorage.getItem(key) || '';
    }
    function saveConspect() {
        let key = getStorageKey();
        if (key && textarea) localStorage.setItem(key, textarea.value);
        if (saveBtn) {
            saveBtn.textContent = '✓';
            setTimeout(() => { saveBtn.textContent = 'Сохранить'; }, 600);
        }
    }

    function saveWinState() {
        let left = parseFloat(win.style.left);
        let top = parseFloat(win.style.top);
        let width = win.offsetWidth;
        let height = win.offsetHeight;
        if (!isNaN(left) && !isNaN(top))
            localStorage.setItem('conspect_window', JSON.stringify({ left, top, width, height }));
    }
    function loadWinState() {
        let saved = localStorage.getItem('conspect_window');
        if (saved) {
            let { left, top, width, height } = JSON.parse(saved);
            if (left) win.style.left = left + 'px';
            if (top) win.style.top = top + 'px';
            if (width && width >= 200) win.style.width = width + 'px';
            if (height && height >= 150) win.style.height = height + 'px';
        } else {
            let bounds = getContainerBounds();
            let width = 320, height = 280;
            win.style.width = width + 'px';
            win.style.height = height + 'px';
            win.style.left = (bounds.right - width - 20) + 'px';
            win.style.top = (bounds.bottom - height - 20) + 'px';
            win.style.right = 'auto';
            win.style.bottom = 'auto';
        }
    }

    function clampPosition(left, top, width, height) {
        let bounds = getContainerBounds();
        return {
            left: Math.min(bounds.right - width, Math.max(bounds.left, left)),
            top: Math.min(bounds.bottom - height, Math.max(bounds.top, top))
        };
    }
    function applyClampedPosition() {
        let left = parseFloat(win.style.left);
        let top = parseFloat(win.style.top);
        let width = win.offsetWidth;
        let height = win.offsetHeight;
        let clamped = clampPosition(left, top, width, height);
        if (clamped.left !== left) win.style.left = clamped.left + 'px';
        if (clamped.top !== top) win.style.top = clamped.top + 'px';
    }

    // DRAG
    let dragging = false;
    let dragStartX = 0, dragStartY = 0, dragStartLeft = 0, dragStartTop = 0;
    function onMouseMove(e) {
        if (!dragging) return;
        let newLeft = dragStartLeft + (e.clientX - dragStartX);
        let newTop = dragStartTop + (e.clientY - dragStartY);
        let width = win.offsetWidth;
        let height = win.offsetHeight;
        let clamped = clampPosition(newLeft, newTop, width, height);
        win.style.left = clamped.left + 'px';
        win.style.top = clamped.top + 'px';
        win.style.right = 'auto';
        win.style.bottom = 'auto';
    }
    function onMouseUp() {
        if (dragging) saveWinState();
        dragging = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.body.style.userSelect = '';
    }
    if (header) {
        header.addEventListener('mousedown', (e) => {
            if (e.target.closest('.btn-close-window') || e.target.closest('.btn-save-conspect')) return;
            dragging = true;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            dragStartLeft = parseFloat(win.style.left);
            dragStartTop = parseFloat(win.style.top);
            if (isNaN(dragStartLeft)) dragStartLeft = 20;
            if (isNaN(dragStartTop)) dragStartTop = 20;
            document.body.style.userSelect = 'none';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            e.preventDefault();
        });
    }

    // RESIZE
    const directions = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
    let resizing = false;
    let resizeDir = null;
    let resizeStartX = 0, resizeStartY = 0;
    let resizeStartWidth = 0, resizeStartHeight = 0;
    let resizeStartLeft = 0, resizeStartTop = 0;

    function startResize(e, dir) {
        e.stopPropagation();
        resizing = true;
        resizeDir = dir;
        resizeStartX = e.clientX;
        resizeStartY = e.clientY;
        resizeStartWidth = win.offsetWidth;
        resizeStartHeight = win.offsetHeight;
        resizeStartLeft = parseFloat(win.style.left);
        resizeStartTop = parseFloat(win.style.top);
        if (isNaN(resizeStartLeft)) resizeStartLeft = 20;
        if (isNaN(resizeStartTop)) resizeStartTop = 20;
        document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', onResizeMove);
        document.addEventListener('mouseup', stopResize);
        e.preventDefault();
    }
    function onResizeMove(e) {
        if (!resizing) return;
        let dx = e.clientX - resizeStartX;
        let dy = e.clientY - resizeStartY;
        let newWidth = resizeStartWidth;
        let newHeight = resizeStartHeight;
        let newLeft = resizeStartLeft;
        let newTop = resizeStartTop;

        const minW = 200, minH = 150;
        const maxW = window.innerWidth * 0.9;
        const maxH = window.innerHeight * 0.9;

        if (resizeDir.includes('e')) newWidth = Math.min(maxW, Math.max(minW, resizeStartWidth + dx));
        if (resizeDir.includes('w')) {
            let possibleWidth = resizeStartWidth - dx;
            if (possibleWidth >= minW && possibleWidth <= maxW) {
                newWidth = possibleWidth;
                newLeft = resizeStartLeft + dx;
            }
        }
        if (resizeDir.includes('s')) newHeight = Math.min(maxH, Math.max(minH, resizeStartHeight + dy));
        if (resizeDir.includes('n')) {
            let possibleHeight = resizeStartHeight - dy;
            if (possibleHeight >= minH && possibleHeight <= maxH) {
                newHeight = possibleHeight;
                newTop = resizeStartTop + dy;
            }
        }

        let bounds = getContainerBounds();
        win.style.width = newWidth + 'px';
        win.style.height = newHeight + 'px';
        let finalLeft = newLeft;
        let finalTop = newTop;
        if (finalLeft < bounds.left) finalLeft = bounds.left;
        if (finalTop < bounds.top) finalTop = bounds.top;
        if (finalLeft + newWidth > bounds.right) finalLeft = bounds.right - newWidth;
        if (finalTop + newHeight > bounds.bottom) finalTop = bounds.bottom - newHeight;
        win.style.left = finalLeft + 'px';
        win.style.top = finalTop + 'px';
    }
    function stopResize() {
        if (resizing) saveWinState();
        resizing = false;
        document.removeEventListener('mousemove', onResizeMove);
        document.removeEventListener('mouseup', stopResize);
        document.body.style.userSelect = '';
    }

    directions.forEach(dir => {
        let handle = win.querySelector(`.resize-handle.${dir}`);
        if (!handle) {
            handle = document.createElement('div');
            handle.className = `resize-handle ${dir}`;
            win.appendChild(handle);
        }
        handle.addEventListener('mousedown', (e) => startResize(e, dir));
    });

    function openWin() {
        win.style.display = 'flex';
        isOpen = true;
        loadWinState();
        loadConspect();
        applyClampedPosition();
    }
    function closeWin() {
        win.style.display = 'none';
        isOpen = false;
    }
    function toggleWin() { isOpen ? closeWin() : openWin(); }

    tabBtn.addEventListener('click', toggleWin);
    if (closeBtn) closeBtn.addEventListener('click', closeWin);
    if (saveBtn) saveBtn.addEventListener('click', saveConspect);

    if (textarea) textarea.addEventListener('input', () => {}); // можно добавить автосохранение

    let oldShow = window.showTopicContent;
    if (oldShow) {
        window.showTopicContent = async function(sid, tid) {
            await oldShow(sid, tid);
            if (isOpen) loadConspect();
        };
    } else {
        setInterval(() => { if (isOpen && window.activeTopicId) loadConspect(); }, 500);
    }

    window.addEventListener('resize', () => {
        if (isOpen) applyClampedPosition();
    });

    win.style.display = 'none';
    isOpen = false;
})();