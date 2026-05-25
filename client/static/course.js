// static/course.js
(function() {
    const courseTitleHeader = document.getElementById('courseTitleHeader');
    const sectionList = document.getElementById('sectionList');
    const topicContent = document.getElementById('topicContent');
    const checkYourselfBtn = document.getElementById('checkYourselfBtn');

    let currentCourse = null;
    let currentTopicId = null;
    let currentTopicName = '';
    const renderedCache = new Map();

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function showCourseDescription() {
        if (!currentCourse) {
            topicContent.innerHTML = '<p class="text-muted">Информация о курсе загружается...</p>';
            return;
        }
        topicContent.innerHTML = `
            <div class="course-description-block">
                <h2>${escapeHtml(currentCourse.name)}</h2>
                <p>${escapeHtml(currentCourse.description || 'Описание отсутствует')}</p>
            </div>
        `;
        currentTopicId = null;
        window.activeTopicId = null;
        document.querySelectorAll('.topic-link').forEach(link => link.classList.remove('active'));
        // При возврате к описанию курса — скрываем/очищаем конспект (опционально)
        if (window.Notes && window.Notes.onTopicChanged) {
            window.Notes.onTopicChanged(null);
        }
    }

    async function displayTopic(topicId, topicName) {
        if (!topicId) return;
        topicContent.innerHTML = '<div class="text-muted">Загрузка...</div>';
        currentTopicId = topicId;
        currentTopicName = topicName;
        window.activeTopicId = topicId;

        // Уведомляем плавающее окно о смене темы (если окно открыто)
        if (window.Notes && window.Notes.onTopicChanged) {
            window.Notes.onTopicChanged(topicId);
        } else {
            // fallback для совместимости: если окно открыто, загружаем заметку через глобальный метод
            if (window.floatingWindowOpen && window.loadNoteForCurrentTopic) {
                window.loadNoteForCurrentTopic();
            }
        }

        if (renderedCache.has(topicId)) {
            renderTopicContent(renderedCache.get(topicId));
            return;
        }

        try {
            const url = `${window.API_BASE_URL}topics/get-rendered-content/${topicId}`;
            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    topicContent.innerHTML = '<p class="text-danger">Для просмотра этой темы необходимо <a href="/">войти</a>.</p>';
                    return;
                }
                throw new Error(`HTTP ${resp.status}`);
            }
            const data = await resp.json();
            renderedCache.set(topicId, data);
            renderTopicContent(data);
        } catch (err) {
            console.error('Ошибка загрузки темы:', err);
            topicContent.innerHTML = '<p class="text-muted">Содержимое темы недоступно.</p>';
        }
    }

    function renderTopicContent(contentData) {
        let blocks = [];
        if (Array.isArray(contentData)) {
            blocks = contentData;
        } else if (contentData && Array.isArray(contentData.blocks)) {
            blocks = contentData.blocks;
        } else if (contentData && typeof contentData === 'object') {
            const possibleKeys = ['items', 'data', 'content'];
            for (const key of possibleKeys) {
                if (Array.isArray(contentData[key])) {
                    blocks = contentData[key];
                    break;
                }
            }
        }

        if (!blocks.length) {
            topicContent.innerHTML = '<p class="text-muted">Тема не содержит контента.</p>';
            return;
        }

        let html = '<div class="topic-blocks">';
        for (const block of blocks) {
            let blockHtml = block.rendered_content || block.content || block.html || '';
            if (!blockHtml) {
                blockHtml = '<p class="text-muted">(пустой блок)</p>';
            }
            const blockType = block.type || 'markdown';
            html += `<div class="topic-block topic-block-type-${blockType}">${blockHtml}</div>`;
        }
        html += '</div>';
        topicContent.innerHTML = html;

        if (window.MathJax) {
            MathJax.typesetPromise?.();
        }
        if (window.mermaid) {
            mermaid.init?.(undefined, document.querySelectorAll('.topic-block-type-uml'));
        }
    }

    async function buildSidebar() {
        if (!sectionList) return;
        sectionList.innerHTML = '<li class="list-group-item text-muted">Загрузка...</li>';
        try {
            const url = `${window.API_BASE_URL}sections/by_course/${window.COURSE_ID}`;
            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) throw new Error(`Sections HTTP ${resp.status}`);
            const sections = await resp.json();
            if (!sections?.length) {
                sectionList.innerHTML = '<li class="list-group-item text-muted">В курсе нет разделов.</li>';
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

                try {
                    const topicsUrl = `${window.API_BASE_URL}topics/by-section/${section.id}`;
                    const topicsResp = await fetch(topicsUrl, { credentials: 'include' });
                    if (!topicsResp.ok) throw new Error();
                    const data = await topicsResp.json();
                    const topics = Array.isArray(data) ? data : (data.topics || []);
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
                } catch (err) {
                    console.error(`Ошибка загрузки тем для раздела ${section.id}:`, err);
                    topicsContainer.innerHTML = '<div class="text-danger small p-2">Ошибка загрузки тем</div>';
                }

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

    function showSectionDescription(sectionId, sectionName, sectionDescription) {
        topicContent.innerHTML = `
            <div class="section-description-block">
                <h2>${escapeHtml(sectionName)}</h2>
                <p>${escapeHtml(sectionDescription || 'Описание отсутствует')}</p>
            </div>
        `;
        currentTopicId = null;
        window.activeTopicId = null;
        document.querySelectorAll('.topic-link').forEach(link => link.classList.remove('active'));
        if (window.Notes && window.Notes.onTopicChanged) {
            window.Notes.onTopicChanged(null);
        }
    }

    async function loadCourseInfo() {
        if (!courseTitleHeader) return;
        courseTitleHeader.textContent = 'Загрузка...';
        try {
            const url = `${window.API_BASE_URL}courses/${window.COURSE_ID}`;
            const resp = await fetch(url, { credentials: 'include' });
            if (!resp.ok) throw new Error(`Course HTTP ${resp.status}`);
            currentCourse = await resp.json();
            courseTitleHeader.textContent = escapeHtml(currentCourse.name);
            showCourseDescription();
            await buildSidebar();
        } catch (err) {
            console.error(err);
            courseTitleHeader.textContent = 'Курс не найден';
            topicContent.innerHTML = '<p class="text-muted">Не удалось загрузить курс.</p>';
        }
    }

    function setupCheckYourself() {
        if (checkYourselfBtn) {
            checkYourselfBtn.addEventListener('click', () => {
                if (currentTopicId) {
                    alert(`Функция «Проверить себя» для темы "${currentTopicName}" в разработке.`);
                } else {
                    alert('Сначала выберите тему.');
                }
            });
        }
    }

    function setupCourseTitleClick() {
        if (courseTitleHeader) {
            courseTitleHeader.style.cursor = 'pointer';
            courseTitleHeader.addEventListener('click', () => {
                if (currentCourse) showCourseDescription();
            });
        }
    }

    async function init() {
        if (!window.COURSE_ID) {
            console.error('COURSE_ID не задан');
            return;
        }
        await loadCourseInfo();
        setupCheckYourself();
        setupCourseTitleClick();

        const urlParams = new URLSearchParams(window.location.search);
        const topicId = urlParams.get('topic');
        if (topicId) {
            setTimeout(() => {
                const topicLink = document.querySelector(`.topic-link[data-topic-id="${topicId}"]`);
                if (topicLink) {
                    const sectionItem = topicLink.closest('.section-item');
                    const topicsContainer = sectionItem?.querySelector('.section-topics');
                    if (topicsContainer && topicsContainer.style.display === 'none') {
                        const toggle = sectionItem.querySelector('.section-toggle');
                        if (toggle) toggle.click();
                    }
                    topicLink.click();
                } else {
                    console.warn(`Topic ${topicId} not found`);
                }
            }, 500);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

// ========== Плавающее окно конспекта ==========
(function() {
    const win = document.getElementById('floatingWindow');
    const tabBtn = document.getElementById('floatingTabButton');
    const closeBtn = document.getElementById('closeWindowBtn');
    const saveBtn = document.getElementById('saveConspectBtn');
    const deleteBtn = document.getElementById('deleteConspectBtn'); // новая кнопка
    const textarea = win?.querySelector('.conspect-content');
    const header = document.getElementById('windowHeader');

    let isOpen = false;
    let currentNoteId = null;

    // --- Вспомогательные функции окна (перетаскивание, ресайз, сохранение состояния) ---
    function getContainerBounds() {
        const mainContent = document.querySelector('.main-content');
        if (!mainContent) return { left: 20, top: 20, right: window.innerWidth - 20, bottom: window.innerHeight - 20 };
        const rect = mainContent.getBoundingClientRect();
        return { left: rect.left + 10, top: rect.top + 10, right: rect.right - 10, bottom: rect.bottom - 10 };
    }

    function clampPosition(left, top, width, height) {
        const bounds = getContainerBounds();
        return {
            left: Math.min(bounds.right - width, Math.max(bounds.left, left)),
            top: Math.min(bounds.bottom - height, Math.max(bounds.top, top))
        };
    }

    function loadWinState() {
        const saved = localStorage.getItem('conspect_window');
        if (saved) {
            const { left, top, width, height } = JSON.parse(saved);
            if (left) win.style.left = left + 'px';
            if (top) win.style.top = top + 'px';
            if (width && width >= 200) win.style.width = width + 'px';
            if (height && height >= 150) win.style.height = height + 'px';
        } else {
            const bounds = getContainerBounds();
            const width = 320, height = 280;
            win.style.width = width + 'px';
            win.style.height = height + 'px';
            win.style.left = (bounds.right - width - 20) + 'px';
            win.style.top = (bounds.bottom - height - 20) + 'px';
        }
        win.style.right = 'auto';
        win.style.bottom = 'auto';
    }

    function applyClampedPosition() {
        const left = parseFloat(win.style.left);
        const top = parseFloat(win.style.top);
        const width = win.offsetWidth;
        const height = win.offsetHeight;
        const clamped = clampPosition(left, top, width, height);
        if (clamped.left !== left) win.style.left = clamped.left + 'px';
        if (clamped.top !== top) win.style.top = clamped.top + 'px';
    }

    // Drag and drop
    let dragging = false;
    let dragStartX = 0, dragStartY = 0, dragStartLeft = 0, dragStartTop = 0;
    function onMouseMove(e) {
        if (!dragging) return;
        let newLeft = dragStartLeft + (e.clientX - dragStartX);
        let newTop = dragStartTop + (e.clientY - dragStartY);
        const width = win.offsetWidth;
        const height = win.offsetHeight;
        const clamped = clampPosition(newLeft, newTop, width, height);
        win.style.left = clamped.left + 'px';
        win.style.top = clamped.top + 'px';
    }
    function onMouseUp() {
        if (dragging) {
            localStorage.setItem('conspect_window', JSON.stringify({
                left: parseFloat(win.style.left),
                top: parseFloat(win.style.top),
                width: win.offsetWidth,
                height: win.offsetHeight
            }));
        }
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
            dragStartLeft = parseFloat(win.style.left) || 20;
            dragStartTop = parseFloat(win.style.top) || 20;
            document.body.style.userSelect = 'none';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            e.preventDefault();
        });
    }

    // --- Работа с конспектом через window.Notes ---
    async function loadNoteForCurrentTopic() {
        const topicId = window.activeTopicId;
        if (!topicId) {
            if (textarea) textarea.value = '';
            currentNoteId = null;
            return;
        }
        try {
            const note = await window.Notes.loadNoteForTopic(topicId);
            if (note) {
                textarea.value = note.content || '';
                currentNoteId = note.id;
            } else {
                textarea.value = '';
                currentNoteId = null;
            }
        } catch (err) {
            console.warn('Ошибка загрузки конспекта:', err);
            textarea.value = '';
            currentNoteId = null;
        }
    }

    async function saveCurrentNote() {
        const topicId = window.activeTopicId;
        if (!topicId) {
            window.Notes.showMessage('Сначала выберите тему', true);
            return;
        }
        const content = textarea.value;
        try {
            const result = await window.Notes.saveNote(topicId, content, currentNoteId);
            currentNoteId = result.noteId;
            window.Notes.showMessage('Конспект сохранён');
        } catch (err) {
            // сообщение уже показано внутри Notes.saveNote
        }
    }

    async function deleteCurrentNote() {
        if (!currentNoteId) {
            window.Notes.showMessage('Нет конспекта для удаления', true);
            return;
        }
        if (!confirm('Вы уверены, что хотите удалить этот конспект?')) return;
        try {
            await window.Notes.deleteNote(currentNoteId);
            textarea.value = '';
            currentNoteId = null;
        } catch (err) {
            // ошибка уже показана
        }
    }

    function openWin() {
        win.style.display = 'flex';
        isOpen = true;
        loadWinState();
        applyClampedPosition();
        loadNoteForCurrentTopic();
    }
    function closeWin() { win.style.display = 'none'; isOpen = false; }
    function toggleWin() { isOpen ? closeWin() : openWin(); }

    window.Notes = window.Notes || {};
    window.Notes.onTopicChanged = function(topicId) {
        if (isOpen) {
            loadNoteForCurrentTopic();
        }
    };

    window.loadNoteForCurrentTopic = loadNoteForCurrentTopic;

    tabBtn?.addEventListener('click', toggleWin);
    closeBtn?.addEventListener('click', closeWin);
    saveBtn?.addEventListener('click', saveCurrentNote);
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteCurrentNote);
    }

    // Стартовое состояние – окно скрыто
    win.style.display = 'none';
    isOpen = false;
})();