(function() {
    // ========== 1. ПАРАМЕТРЫ КУРСА ==========
    const totalSections = 3;
    const topicsPerSection = 2;

    // ========== 2. ГЕНЕРАЦИЯ ДАННЫХ КУРСА ==========
    const demoContent = `
        <h2>Демо-тема</h2>
        <ul>
            <li>Высокий Уровень Вовлечения Представителей Целевой Аудитории Является Четким Доказательством Простого Факта: Синтетическое Тестирование Требует Определения И Уточнения Первоочередных Требований.</li>
            <li>Имеется Спорная Точка Зрения, Гласящая Примерно Следующее: Сторонники Тоталитаризма В Науке, Превозмогая Сложившуюся Непростую Экономическую Ситуацию, Преданы Социально-Демократической Анафеме.</li>
        </ul>
        <p><a href="/">Пример ссылки в контенте (переход на главную страницу)</a></p>
    `;

    function generateCourseData(sectionsCount, topicsCount) {
        const sections = [];
        for (let s = 1; s <= sectionsCount; s++) {
            const sectionId = `section${s}`;
            const topics = [];
            for (let t = 1; t <= topicsCount; t++) {
                const topicId = `topic${s}-${t}`;
                topics.push({
                    id: topicId,
                    title: `Тема ${s}.${t}`,
                    content: demoContent
                });
            }
            sections.push({
                id: sectionId,
                title: `Раздел ${s}`,
                topics: topics
            });
        }
        return { sections };
    }

    const courseData = generateCourseData(totalSections, topicsPerSection);

    // ========== 3. ГЕНЕРАЦИЯ МЕНЮ И УПРАВЛЕНИЕ КОНТЕНТОМ ==========
    const sectionList = document.getElementById('sectionList');
    const topicContent = document.getElementById('topicContent');

    let activeSectionId = null;
    let activeTopicId = null;

    function renderMenu() {
        if (!sectionList) return;
        sectionList.innerHTML = '';

        courseData.sections.forEach(section => {
            const sectionItem = document.createElement('li');
            sectionItem.className = 'list-group-item section-item';
            sectionItem.dataset.sectionId = section.id;

            const toggleLink = document.createElement('a');
            toggleLink.href = '#';
            toggleLink.className = 'section-toggle';
            toggleLink.dataset.target = section.id;
            toggleLink.innerHTML = `<span class="toggle-icon">▶</span> ${section.title}`;

            const topicsUl = document.createElement('ul');
            topicsUl.className = 'list-unstyled ps-4 mt-2 section-topics';
            topicsUl.id = `topics-${section.id}`;
            topicsUl.style.display = 'none';

            section.topics.forEach(topic => {
                const topicLi = document.createElement('li');
                const topicLink = document.createElement('a');
                topicLink.href = '#';
                topicLink.className = 'topic-link';
                topicLink.dataset.sectionId = section.id;
                topicLink.dataset.topicId = topic.id;
                topicLink.textContent = topic.title;
                topicLi.appendChild(topicLink);
                topicsUl.appendChild(topicLi);
            });

            sectionItem.appendChild(toggleLink);
            sectionItem.appendChild(topicsUl);
            sectionList.appendChild(sectionItem);
        });
    }

    function showTopicContent(sectionId, topicId) {
        const section = courseData.sections.find(s => s.id === sectionId);
        if (!section) return;
        const topic = section.topics.find(t => t.id === topicId);
        if (!topic) return;

        topicContent.innerHTML = topic.content;
        activeSectionId = sectionId;
        activeTopicId = topicId;
        updateActiveMenuState();
    }

    function updateActiveMenuState() {
        document.querySelectorAll('.section-toggle').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.topic-link').forEach(el => el.classList.remove('active'));

        if (activeSectionId) {
            const sectionToggle = document.querySelector(`.section-toggle[data-target="${activeSectionId}"]`);
            if (sectionToggle) sectionToggle.classList.add('active');
        }
        if (activeTopicId && activeSectionId) {
            const topicLink = document.querySelector(`.topic-link[data-section-id="${activeSectionId}"][data-topic-id="${activeTopicId}"]`);
            if (topicLink) topicLink.classList.add('active');
        }
    }

    if (sectionList) {
        sectionList.addEventListener('click', (e) => {
            const toggle = e.target.closest('.section-toggle');
            const topicLink = e.target.closest('.topic-link');

            if (toggle) {
                e.preventDefault();
                const sectionId = toggle.dataset.target;
                const topicsUl = document.getElementById(`topics-${sectionId}`);
                const icon = toggle.querySelector('.toggle-icon');

                if (topicsUl) {
                    const isHidden = topicsUl.style.display === 'none' || topicsUl.style.display === '';
                    topicsUl.style.display = isHidden ? 'block' : 'none';
                    if (icon) icon.textContent = isHidden ? '▼' : '▶';
                }
            }

            if (topicLink) {
                e.preventDefault();
                const sectionId = topicLink.dataset.sectionId;
                const topicId = topicLink.dataset.topicId;
                showTopicContent(sectionId, topicId);
            }
        });
    }

    function initCourseView() {
        renderMenu();
        if (courseData.sections.length > 0) {
            const firstSection = courseData.sections[0];
            if (firstSection.topics.length > 0) {
                const firstTopic = firstSection.topics[0];
                const topicsUl = document.getElementById(`topics-${firstSection.id}`);
                if (topicsUl) topicsUl.style.display = 'block';
                const toggle = document.querySelector(`.section-toggle[data-target="${firstSection.id}"]`);
                if (toggle) {
                    const icon = toggle.querySelector('.toggle-icon');
                    if (icon) icon.textContent = '▼';
                }
                showTopicContent(firstSection.id, firstTopic.id);
            } else {
                activeSectionId = firstSection.id;
                updateActiveMenuState();
            }
        }
    }

    initCourseView();
})();

// ========== ПЛАВАЮЩИЙ КОНСПЕКТ ==========
(function initFloatingFeatures() {
    const win = document.getElementById('floatingWindow');
    const header = document.getElementById('windowHeader');
    const closeBtn = document.getElementById('closeWindowBtn');
    const tabBtn = document.getElementById('floatingTabButton');

    if (!win || !header || !tabBtn) return;

    tabBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (win.style.display === 'none' || win.style.display === '') {
            win.style.display = 'block';
            const rect = win.getBoundingClientRect();
            const maxX = window.innerWidth - rect.width;
            const maxY = window.innerHeight - rect.height;
            let left = parseInt(win.style.left) || 100;
            let top = parseInt(win.style.top) || 100;
            left = Math.min(Math.max(0, left), maxX);
            top = Math.min(Math.max(0, top), maxY);
            win.style.left = left + 'px';
            win.style.top = top + 'px';
        }
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => { win.style.display = 'none'; });
    }

    let isDraggingWin = false;
    let startX, startY, startLeft, startTop;
    function onMouseDown(e) {
        if (!header.contains(e.target)) return;
        isDraggingWin = true;
        startX = e.clientX;
        startY = e.clientY;
        startLeft = parseInt(win.style.left) || 0;
        startTop = parseInt(win.style.top) || 0;
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        e.preventDefault();
    }
    function onMouseMove(e) {
        if (!isDraggingWin) return;
        let newLeft = startLeft + (e.clientX - startX);
        let newTop = startTop + (e.clientY - startY);
        const maxX = window.innerWidth - win.offsetWidth;
        const maxY = window.innerHeight - win.offsetHeight;
        newLeft = Math.min(Math.max(0, newLeft), maxX);
        newTop = Math.min(Math.max(0, newTop), maxY);
        win.style.left = newLeft + 'px';
        win.style.top = newTop + 'px';
    }
    function onMouseUp() {
        isDraggingWin = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }
    header.addEventListener('mousedown', onMouseDown);

    let isDraggingBtn = false;
    let btnStartY, btnStartTop;
    function getBtnTop() {
        let top = parseFloat(window.getComputedStyle(tabBtn).top);
        return isNaN(top) ? tabBtn.getBoundingClientRect().top : top;
    }
    function onBtnMouseDown(e) {
        isDraggingBtn = true;
        btnStartTop = getBtnTop();
        btnStartY = e.clientY;
        document.addEventListener('mousemove', onBtnMouseMove);
        document.addEventListener('mouseup', onBtnMouseUp);
        e.preventDefault();
        e.stopPropagation();
    }
    function onBtnMouseMove(e) {
        if (!isDraggingBtn) return;
        let dy = e.clientY - btnStartY;
        let newTop = btnStartTop + dy;
        const btnHeight = tabBtn.offsetHeight;
        newTop = Math.min(Math.max(0, newTop), window.innerHeight - btnHeight);
        tabBtn.style.top = newTop + 'px';
    }
    function onBtnMouseUp() {
        isDraggingBtn = false;
        document.removeEventListener('mousemove', onBtnMouseMove);
        document.removeEventListener('mouseup', onBtnMouseUp);
    }
    tabBtn.addEventListener('mousedown', onBtnMouseDown);

    function onBtnTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        btnStartTop = getBtnTop();
        btnStartY = touch.clientY;
        isDraggingBtn = true;
        document.addEventListener('touchmove', onBtnTouchMove);
        document.addEventListener('touchend', onBtnTouchEnd);
    }
    function onBtnTouchMove(e) {
        if (!isDraggingBtn) return;
        e.preventDefault();
        const touch = e.touches[0];
        let dy = touch.clientY - btnStartY;
        let newTop = btnStartTop + dy;
        const btnHeight = tabBtn.offsetHeight;
        newTop = Math.min(Math.max(0, newTop), window.innerHeight - btnHeight);
        tabBtn.style.top = newTop + 'px';
    }
    function onBtnTouchEnd() {
        isDraggingBtn = false;
        document.removeEventListener('touchmove', onBtnTouchMove);
        document.removeEventListener('touchend', onBtnTouchEnd);
    }
    tabBtn.addEventListener('touchstart', onBtnTouchStart);

    window.addEventListener('resize', () => {
        let top = getBtnTop();
        const maxTop = window.innerHeight - tabBtn.offsetHeight;
        if (top > maxTop) tabBtn.style.top = maxTop + 'px';
        if (top < 0) tabBtn.style.top = '0px';
    });

    const resizeHandle = document.getElementById('resizeHandle');
    if (resizeHandle) {
        let isResizing = false;
        let startResizeX, startResizeY, startWidth, startHeight;

        function onResizeMouseDown(e) {
            e.preventDefault();
            e.stopPropagation();
            isResizing = true;
            startResizeX = e.clientX;
            startResizeY = e.clientY;
            startWidth = win.offsetWidth;
            startHeight = win.offsetHeight;
            document.addEventListener('mousemove', onResizeMouseMove);
            document.addEventListener('mouseup', onResizeMouseUp);
        }

        function onResizeMouseMove(e) {
            if (!isResizing) return;
            const deltaX = e.clientX - startResizeX;
            const deltaY = e.clientY - startResizeY;
            let newWidth = startWidth + deltaX;
            let newHeight = startHeight + deltaY;
            newWidth = Math.max(200, newWidth);
            newHeight = Math.max(150, newHeight);
            const rect = win.getBoundingClientRect();
            const maxWidth = window.innerWidth - rect.left;
            const maxHeight = window.innerHeight - rect.top;
            newWidth = Math.min(newWidth, maxWidth);
            newHeight = Math.min(newHeight, maxHeight);
            win.style.width = newWidth + 'px';
            win.style.height = newHeight + 'px';
        }

        function onResizeMouseUp() {
            isResizing = false;
            document.removeEventListener('mousemove', onResizeMouseMove);
            document.removeEventListener('mouseup', onResizeMouseUp);
        }

        resizeHandle.addEventListener('mousedown', onResizeMouseDown);
    }
})();