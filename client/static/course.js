(function() {
    const courseId = window.COURSE_ID;
    const sectionList = document.getElementById('sectionList');
    const topicContent = document.getElementById('topicContent');
    const checkYourselfBtn = document.getElementById('checkYourselfBtn');

    let sectionsData = [];
    let activeTopicId = null;
    let activeSectionId = null;

    async function loadCourseStructure() {
        try {
            // 1. Разделы курса
            const sectionsResp = await fetch(`${window.API_BASE_URL}sections/by_course/${courseId}`, {
                credentials: 'include'
            });
            if (!sectionsResp.ok) throw new Error('Не удалось загрузить разделы');
            const sectionsDataResp = await sectionsResp.json();
            let sections = sectionsDataResp.sections || [];
            sections.sort((a,b) => a.order_number - b.order_number);

            sectionsData = [];
            for (const section of sections) {
                const topicsResp = await fetch(`${window.API_BASE_URL}topics/by-section/${section.id}`, {
                    credentials: 'include'
                });
                if (!topicsResp.ok) throw new Error(`Ошибка загрузки тем раздела ${section.id}`);
                const topicsData = await topicsResp.json();
                let topics = topicsData.topics || [];
                topics.sort((a,b) => a.order_number - b.order_number);
                sectionsData.push({
                    id: section.id,
                    name: section.name,
                    order_number: section.order_number,
                    topics: topics.map(t => ({ id: t.id, name: t.name, order_number: t.order_number }))
                });
            }
            renderMenu();
            if (sectionsData.length && sectionsData[0].topics.length) {
                const firstSection = sectionsData[0];
                const firstTopic = firstSection.topics[0];
                showTopicContent(firstSection.id, firstTopic.id);
                toggleSection(firstSection.id, true);
            } else {
                topicContent.innerHTML = '<p class="text-muted">Курс пока пуст. Добавьте разделы и темы.</p>';
            }
        } catch (err) {
            console.error(err);
            topicContent.innerHTML = '<p class="text-danger">Ошибка загрузки курса. Попробуйте позже.</p>';
        }
    }

    function renderMenu() {
        if (!sectionList) return;
        sectionList.innerHTML = '';
        sectionsData.forEach(section => {
            const sectionItem = document.createElement('li');
            sectionItem.className = 'list-group-item section-item';
            sectionItem.dataset.sectionId = section.id;

            const toggleLink = document.createElement('a');
            toggleLink.href = '#';
            toggleLink.className = 'section-toggle';
            toggleLink.dataset.target = section.id;
            toggleLink.innerHTML = `<span class="toggle-icon">▶</span> ${escapeHtml(section.name)}`;

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
                topicLink.textContent = topic.name;
                topicLi.appendChild(topicLink);
                topicsUl.appendChild(topicLi);
            });

            sectionItem.appendChild(toggleLink);
            sectionItem.appendChild(topicsUl);
            sectionList.appendChild(sectionItem);
        });

        document.querySelectorAll('.section-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sid = btn.dataset.target;
                const topicsUl = document.getElementById(`topics-${sid}`);
                const icon = btn.querySelector('.toggle-icon');
                const isHidden = topicsUl.style.display === 'none' || topicsUl.style.display === '';
                topicsUl.style.display = isHidden ? 'block' : 'none';
                icon.textContent = isHidden ? '▼' : '▶';
            });
        });

        document.querySelectorAll('.topic-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sid = link.dataset.sectionId;
                const tid = link.dataset.topicId;
                showTopicContent(sid, tid);
            });
        });
    }

    function toggleSection(sectionId, expand) {
        const topicsUl = document.getElementById(`topics-${sectionId}`);
        const toggle = document.querySelector(`.section-toggle[data-target="${sectionId}"]`);
        if (topicsUl && toggle) {
            topicsUl.style.display = expand ? 'block' : 'none';
            const icon = toggle.querySelector('.toggle-icon');
            if (icon) icon.textContent = expand ? '▼' : '▶';
        }
    }

    async function showTopicContent(sectionId, topicId) {
        activeSectionId = sectionId;
        activeTopicId = topicId;
        updateActiveMenuState();

        try {
            const resp = await fetch(`${window.API_BASE_URL}topics/get-rendered-content/${topicId}`, {
                credentials: 'include'
            });
            if (!resp.ok) throw new Error('Не удалось загрузить содержимое темы');
            const data = await resp.json();   // { blocks: [{type, rendered_content}] }
            const blocks = data.blocks || [];
            let html = '';
            for (const block of blocks) {
                if (block.type === 'markdown') {
                    html += `<div class="markdown-block">${block.rendered_content}</div>`;
                } else if (block.type === 'uml') {
                    html += `<div class="uml-block"><pre>${escapeHtml(block.rendered_content)}</pre></div>`;
                } else if (block.type === 'latex') {
                    html += `<div class="latex-block">${block.rendered_content}</div>`;
                } else {
                    html += `<div>${escapeHtml(block.rendered_content)}</div>`;
                }
            }
            topicContent.innerHTML = html || '<p class="text-muted">Нет содержимого</p>';
        } catch (err) {
            console.error(err);
            topicContent.innerHTML = '<p class="text-danger">Ошибка загрузки содержимого темы</p>';
        }
    }

    function updateActiveMenuState() {
        document.querySelectorAll('.section-toggle').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.topic-link').forEach(el => el.classList.remove('active'));
        if (activeSectionId) {
            const toggle = document.querySelector(`.section-toggle[data-target="${activeSectionId}"]`);
            if (toggle) toggle.classList.add('active');
        }
        if (activeTopicId && activeSectionId) {
            const link = document.querySelector(`.topic-link[data-section-id="${activeSectionId}"][data-topic-id="${activeTopicId}"]`);
            if (link) link.classList.add('active');
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    if (checkYourselfBtn) {
        checkYourselfBtn.addEventListener('click', () => {
            alert('Функция в разработке');
        });
    }

    loadCourseStructure();
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