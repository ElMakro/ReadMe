(function() {
    const courseId = window.COURSE_ID;
    const sectionList = document.getElementById('sectionList');
    const topicContent = document.getElementById('topicContent');
    const checkYourselfBtn = document.getElementById('checkYourselfBtn');

    let sectionsData = [];
    let activeTopicId = null;
    let activeSectionId = null;
    window.activeSectionId = null;
    window.activeTopicId = null;

    (async function setPageTitle() {
        const courseName = await window.getCourseName(courseId);
        if (courseName) {
            document.title = `${courseName} — ReadMe`;
        }
    })();

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
            setTimeout(() => { saveBtn.textContent = '💾'; }, 600);
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

    // --- DRAG (без задержки) ---
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

    // --- RESIZE (8 направлений) ---
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

        // Ограничение по контейнеру
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

    // Создаём ручки ресайза, если их нет
    directions.forEach(dir => {
        let handle = win.querySelector(`.resize-handle.${dir}`);
        if (!handle) {
            handle = document.createElement('div');
            handle.className = `resize-handle ${dir}`;
            win.appendChild(handle);
        }
        handle.addEventListener('mousedown', (e) => startResize(e, dir));
    });

    // --- Открытие / закрытие ---
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

    // Авто-сохранение при вводе (по желанию)
    if (textarea) textarea.addEventListener('input', () => {}); // пусто, можно раскомментировать saveConspect()

    // Следим за сменой темы
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