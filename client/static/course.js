// static/course.js
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const courseTitleHeader = document.getElementById('courseTitleHeader');
        const sectionList = document.getElementById('sectionList');
        const topicContent = document.getElementById('topicContent');
        const checkYourselfBtn = document.getElementById('checkYourselfBtn');
        const enrollBtn = document.getElementById('enrollBtn');
        const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
        const courseSidebar = document.getElementById('courseSidebar');
        const mainContent = document.getElementById('mainContent');
        const courseNameMain = document.getElementById('courseNameMain');

        let currentCourse = null;
        let currentTopicId = null;
        let currentTopicName = '';
        let currentEnrollmentState = null;
        const renderedCache = new Map();

        function escapeHtml(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        async function renderMarkdown(mdText) {
            if (!mdText) return '';
            const html = await marked.parse(mdText);
            return html;
        }

        function prepareLatexBlock(content) {
            if (!content) return '';
            if (content.includes('$$') || content.includes('\\[') || content.includes('\\(')) {
                return content;
            }
            return `\\[ ${content} \\]`;
        }

        async function fetchCourseState() {
            if (!window.COURSE_ID) return 'enrollable';
            const isAuth = window.Auth && window.Auth.isAuthenticated();
            if (!isAuth) return 'enrollable';

            try {
                const followedResp = await fetch(`${window.API_BASE_URL}courses/followed-courses`, {
                    credentials: 'include'
                });
                if (followedResp.ok) {
                    const followedData = await followedResp.json();
                    const followedCourses = Array.isArray(followedData) ? followedData : (followedData.courses || []);
                    const isEnrolled = followedCourses.some(c => c.id === window.COURSE_ID);
                    if (isEnrolled) return 'enrolled';
                }

                const profileResp = await fetch(`${window.API_BASE_URL}users/profile`, {credentials: 'include'});
                if (profileResp.ok) {
                    const profile = await profileResp.json();
                    const courseResp = await fetch(`${window.API_BASE_URL}courses/${window.COURSE_ID}`, {credentials: 'include'});
                    if (courseResp.ok) {
                        const course = await courseResp.json();
                        if (course.professor_id === profile.id) {
                            return 'controlled';
                        }
                    }
                }

                const controlledResp = await fetch(`${window.API_BASE_URL}courses/controlled-courses`, {
                    credentials: 'include'
                });
                if (controlledResp.ok) {
                    const controlledData = await controlledResp.json();
                    const controlledCourses = Array.isArray(controlledData) ? controlledData : (controlledData.courses || []);
                    const isControlled = controlledCourses.some(c => c.id === window.COURSE_ID);
                    if (isControlled) return 'controlled';
                }
            } catch (err) {
                console.warn('Ошибка получения статуса курса', err);
            }
            return 'enrollable';
        }

        async function updateEnrollButton() {
            if (!enrollBtn) return;
            const state = await fetchCourseState();
            currentEnrollmentState = state;

            if (!window.Auth || !window.Auth.isAuthenticated()) {
                enrollBtn.style.display = 'block';
                enrollBtn.textContent = 'Войдите, чтобы записаться';
                enrollBtn.disabled = false;
                enrollBtn.onclick = () => {
                    if (window.AuthModal && window.AuthModal.open) window.AuthModal.open();
                    else window.showToast('Необходимо войти в систему', 'danger');
                };
                return;
            }

            if (state === 'controlled') {
                enrollBtn.style.display = 'none';
            } else if (state === 'enrolled') {
                enrollBtn.style.display = 'block';
                enrollBtn.textContent = 'Отписаться от курса';
                enrollBtn.onclick = () => handleUnenroll();
                enrollBtn.disabled = false;
            } else {
                enrollBtn.style.display = 'block';
                enrollBtn.textContent = 'Записаться на курс';
                enrollBtn.onclick = () => handleEnroll();
                enrollBtn.disabled = false;
            }
        }

        async function handleEnroll() {
            if (!window.COURSE_ID) return;
            try {
                const resp = await fetch(`${window.API_BASE_URL}users/enroll?course_id=${window.COURSE_ID}`, {
                    method: 'POST',
                    credentials: 'include'
                });
                const isAuth = window.Auth && window.Auth.isAuthenticated();
                if (resp.ok) {
                    window.showToast('Вы успешно записались на курс!');
                    await updateEnrollButton();
                    if (currentCourse) showCourseDescription();
                    await buildSidebar();
                } else if (resp.status === 409) {
                    window.showToast('Вы уже записаны на этот курс', 'danger');
                    await updateEnrollButton();
                } else if (resp.status === 403) {
                    window.showAccessDenied(topicContent, 'Доступ к этой теме ограничен. Запишитесь на курс, чтобы просматривать материалы.', false);
                    window.showToast('Вы не записаны на этот курс. Пожалуйста, запишитесь, чтобы просматривать темы.', 'warning');
                } else if (resp.status === 401 || !isAuth) {
                    window.showAccessDenied(topicContent, 'Для просмотра этой темы необходимо войти в систему.', true);
                    window.showToast('Пожалуйста, войдите, чтобы получить доступ к содержимому курса.', 'danger');
                } else if (resp.status === 404) {
                    window.showToast('Курс не найден', 'danger');
                } else if (resp.status === 422) {
                    window.showToast('Ошибка валидации параметров', 'danger');
                } else {
                    window.showToast('Не удалось записаться на курс', 'danger');
                }
            } catch (err) {
                console.error(err);
                window.showToast('Ошибка при записи', 'danger');
            }
        }

        async function handleUnenroll() {
            if (!window.COURSE_ID) return;
            if (!confirm('Вы уверены, что хотите отписаться от курса?')) return;
            try {
                const resp = await fetch(`${window.API_BASE_URL}users/unenroll?course_id=${window.COURSE_ID}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (resp.ok) {
                    window.showToast('Вы отписались от курса');
                    setTimeout(() => location.reload(), 1000); // даём время увидеть тост
                } else if (resp.status === 404) {
                    window.showToast('Курс не найден', 'danger');
                } else if (resp.status === 422) {
                    window.showToast('Ошибка валидации', 'danger');
                } else {
                    window.showToast('Не удалось отписаться', 'danger');
                }
            } catch (err) {
                console.error(err);
                window.showToast('Ошибка при отписке', 'danger');
            }
        }

        let sidebarVisible = true;

        function applySidebarState() {
            const courseSidebar = document.getElementById('courseSidebar');
            const mainContent = document.getElementById('mainContent');
            const toggleBtn = document.getElementById('toggleSidebarBtn');
            if (!courseSidebar || !mainContent) return;

            if (sidebarVisible) {
                courseSidebar.classList.remove('d-none');
                mainContent.classList.remove('col-md-12', 'col-lg-12');
                mainContent.classList.add('col-md-9', 'col-lg-10');
            } else {
                courseSidebar.classList.add('d-none');
                mainContent.classList.remove('col-md-9', 'col-lg-10');
                mainContent.classList.add('col-md-12', 'col-lg-12');
            }
            if (toggleBtn) toggleBtn.innerHTML = sidebarVisible ? '◀' : '☰';
        }

        function toggleSidebar() {
            sidebarVisible = !sidebarVisible;
            applySidebarState();
        }

        function initSidebar() {
            sidebarVisible = true;
            applySidebarState();
        }

        async function fetchSectionsWithTopics() {
            try {
                const url = `${window.API_BASE_URL}sections/by_course/${window.COURSE_ID}`;
                const resp = await fetch(url, {credentials: 'include'});
                if (!resp.ok) {
                    const isAuth = window.Auth && window.Auth.isAuthenticated();
                    if (resp.status === 401 || !isAuth) {
                        window.showAccessDenied(topicContent, 'Для просмотра этой темы необходимо войти в систему.', true);
                        window.showToast('Пожалуйста, войдите, чтобы получить доступ к содержимому курса.', 'danger');
                    } else {
                        window.showAccessDenied(topicContent, 'Доступ к этой теме ограничен. Запишитесь на курс, чтобы просматривать материалы.', false);
                        window.showToast('Вы не записаны на этот курс. Пожалуйста, запишитесь, чтобы просматривать темы.', 'warning');
                    }
                    if (resp.status === 404) throw new Error('Курс не найден');
                    throw new Error(`HTTP ${resp.status}`);
                }
                const data = await resp.json();
                const sections = Array.isArray(data) ? data : (data.sections || []);
                sections.sort((a, b) => a.order_number - b.order_number);

                for (const section of sections) {
                    const topicsUrl = `${window.API_BASE_URL}topics/by-section/${section.id}`;
                    const topicsResp = await fetch(topicsUrl, {credentials: 'include'});
                    if (topicsResp.ok) {
                        const topicsData = await topicsResp.json();
                        let topics = Array.isArray(topicsData) ? topicsData : (topicsData.topics || []);
                        topics.sort((a, b) => a.order_number - b.order_number);
                        section.topics = topics;
                    } else {
                        section.topics = [];
                    }
                }
                return sections;
            } catch (err) {
                console.error('Ошибка загрузки разделов:', err);
                return [];
            }
        }

        async function showCourseDescription() {
            if (!currentCourse) {
                topicContent.innerHTML = '<p class="text-muted">Информация о курсе загружается...</p>';
                return;
            }
            const sections = await fetchSectionsWithTopics();

            let html = `
                <div class="course-description-card mb-4">
                    <div class="mb-2">
                        <strong>Преподаватель:</strong> 
                        ${escapeHtml([currentCourse.professor_surname, currentCourse.professor_name, currentCourse.professor_patronymic].filter(p => p).join(' ') || '—')}
                    </div>
                    <p>${escapeHtml(currentCourse.description || 'Описание отсутствует')}</p>
                </div>
            `;

            if (!sections.length) {
                html += '<div class="alert alert-secondary bg-transparent border-0 text-secondary">В курсе пока нет разделов.</div>';
            } else {
                for (const section of sections) {
                    const sectionId = section.id;
                    const sectionName = escapeHtml(section.name);
                    const sectionDesc = escapeHtml(section.description || '');
                    let topicsHtml = '';
                    if (section.topics && section.topics.length) {
                        topicsHtml = '<ul class="topics-list-simple list-unstyled mt-2 mb-0">';
                        for (const topic of section.topics) {
                            topicsHtml += `
                                <li>
                                    <a href="#" class="topic-link-main" data-topic-id="${topic.id}">
                                        ${escapeHtml(topic.name)}
                                    </a>
                                </li>
                            `;
                        }
                        topicsHtml += '</ul>';
                    } else {
                        topicsHtml = '<p class="text-muted small mt-2 mb-0">Нет тем</p>';
                    }

                    html += `
                        <div class="section-card" data-section-id="${sectionId}">
                            <div class="d-flex align-items-center p-3 section-header-clickable" style="cursor: pointer;">
                                <span class="toggle-icon me-2" style="font-size: 1rem;">▼</span>
                                <h3 class="section-title mb-0">${sectionName}</h3>
                            </div>
                            <div class="section-body">
                                <div class="section-description">${sectionDesc || '<em class="text-secondary">Описание отсутствует</em>'}</div>
                                <div class="section-topics-wrapper">
                                    ${topicsHtml}
                                </div>
                            </div>
                        </div>
                    `;
                }
            }

            topicContent.innerHTML = html;

            document.querySelectorAll('.section-header-clickable').forEach(header => {
                const sectionCard = header.closest('.section-card');
                const body = sectionCard.querySelector('.section-body');
                const icon = header.querySelector('.toggle-icon');

                header.addEventListener('click', () => {
                    if (body.style.display === 'none') {
                        body.style.display = 'block';
                        icon.textContent = '▼';
                    } else {
                        body.style.display = 'none';
                        icon.textContent = '▶';
                    }
                });
            });

            document.querySelectorAll('.topic-link-main').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const topicId = link.dataset.topicId;
                    const topicName = link.textContent.trim();
                    displayTopic(topicId, topicName);
                });
            });

            currentTopicId = null;
            window.activeTopicId = null;
            if (window.Notes && window.Notes.onTopicChanged) window.Notes.onTopicChanged(null);
        }

        async function displayTopic(topicId, topicName) {
            if (!topicId) return;
            topicContent.innerHTML = '<div class="text-muted">Загрузка...</div>';
            currentTopicId = topicId;
            currentTopicName = topicName;
            window.activeTopicId = topicId;

            if (window.Notes && window.Notes.onTopicChanged) {
                window.Notes.onTopicChanged(topicId);
            }

            if (renderedCache.has(topicId)) {
                await renderTopicContent(renderedCache.get(topicId));
                return;
            }

            try {
                const url = `${window.API_BASE_URL}topics/${topicId}`;
                const resp = await fetch(url, {credentials: 'include'});
                if (!resp.ok) {
                    const isAuth = window.Auth && window.Auth.isAuthenticated();
                    if (resp.status === 401 || !isAuth) {
                        window.showAccessDenied(topicContent, 'Для просмотра этой темы необходимо войти в систему.', true);
                        window.showToast('Пожалуйста, войдите, чтобы получить доступ к содержимому курса.', 'danger');
                    } else {
                        window.showAccessDenied(topicContent, 'Доступ к этой теме ограничен. Запишитесь на курс, чтобы просматривать материалы.', false);
                        window.showToast('Вы не записаны на этот курс. Пожалуйста, запишитесь, чтобы просматривать темы.', 'warning');
                    }
                    return;
                }
                const topicData = await resp.json();
                const renderedContent = topicData.rendered_content || [];
                renderedCache.set(topicId, renderedContent);
                await renderTopicContent(renderedContent);
            } catch (err) {
                console.error('Ошибка загрузки темы:', err);
                topicContent.innerHTML = '<p class="text-muted">Содержимое темы недоступно.</p>';
            }
        }

        async function renderTopicContent(blocks) {
            let html = '<div class="topic-blocks">';
            for (const block of blocks) {
                let blockHtml = '';
                try {
                    let blockType = block.type;
                    if (blockType === 'uml') blockType = 'plantuml';

                    let rawContent = '';
                    if (blockType === 'files') {
                        rawContent = null;
                    } else {
                        if (Array.isArray(block.content)) rawContent = block.content[0] || '';
                        else rawContent = block.content || '';
                    }

                    if (blockType === 'markdown') {
                        blockHtml = await renderMarkdown(rawContent);
                    } else if (blockType === 'latex') {
                        const latexSource = prepareLatexBlock(rawContent);
                        blockHtml = `<div class="latex-block">${latexSource}</div>`;
                    } else if (blockType === 'plantuml' || blockType === 'image') {
                        if (rawContent && typeof rawContent === 'string' && rawContent.length > 0) {
                            const imgUrl = `${window.API_BASE_URL}topics/get-resource/${currentTopicId}/${encodeURIComponent(rawContent)}`;
                            blockHtml = `<div class="text-center"><img src="${imgUrl}" class="img-fluid" alt="Изображение" style="max-width: 100%;"></div>`;
                        } else {
                            blockHtml = '<div class="alert alert-warning">Изображение не найдено</div>';
                        }
                    } else if (blockType === 'files') {
                        const files = block.content || [];
                        if (!files.length) {
                            blockHtml = '<div class="alert alert-secondary">Нет файлов</div>';
                        } else {
                            let items = '';
                            for (const file of files) {
                                const filename = escapeHtml(file.original_filename);
                                const downloadUrl = `${window.API_BASE_URL}topics/get-resource/${currentTopicId}/${encodeURIComponent(file.server_filename)}`;
                                items += `<li><a href="${downloadUrl}" download>${filename}</a></li>`;
                            }
                            blockHtml = `<ul class="file-list mb-0">${items}</ul>`;
                        }
                    } else {
                        blockHtml = `<pre>${escapeHtml(rawContent)}</pre>`;
                    }
                } catch (err) {
                    blockHtml = `<div class="alert alert-danger">Ошибка рендеринга: ${escapeHtml(err.message)}</div>`;
                }
                html += `<div class="topic-block topic-block-type-${block.type}">${blockHtml}</div>`;
                html += '<hr>';
            }
            html += '<button class="btn btn-accent mt-3" id="checkYourselfBtn">Проверить Себя</button>';
            html += '</div>';
            topicContent.innerHTML = html;

            const dynamicBtn = document.getElementById('checkYourselfBtn');
            if (dynamicBtn) {
                dynamicBtn.addEventListener('click', () => {
                    if (currentTopicId) {
                        window.showToast(`Функция «Проверить себя» для темы "${currentTopicName}" в разработке.`, 'warning');
                    } else {
                        window.showToast('Сначала выберите тему.', 'warning');
                    }
                });
            }

            if (window.MathJax) await MathJax.typesetPromise();
        }

        async function buildSidebar() {
            if (!sectionList) return;
            sectionList.innerHTML = '<li class="section-item text-muted">Загрузка...</li>';
            try {
                const url = `${window.API_BASE_URL}sections/by_course/${window.COURSE_ID}`;
                const resp = await fetch(url, {credentials: 'include'});
                if (!resp.ok) {
                    const isAuth = window.Auth && window.Auth.isAuthenticated();
                    if (resp.status === 401 || !isAuth) {
                        window.showAccessDenied(topicContent, 'Для просмотра этой темы необходимо войти в систему.', true);
                        window.showToast('Пожалуйста, войдите, чтобы получить доступ к содержимому курса.', 'danger');
                    } else {
                        window.showAccessDenied(topicContent, 'Доступ к этой теме ограничен. Запишитесь на курс, чтобы просматривать материалы.', false);
                        window.showToast('Вы не записаны на этот курс. Пожалуйста, запишитесь, чтобы просматривать темы.', 'warning');
                    }
                    if (resp.status === 404) {
                        sectionList.innerHTML = '<li class="section-item text-muted">Курс не найден.</li>';
                        return;
                    }
                    throw new Error(`HTTP ${resp.status}`);
                }
                const data = await resp.json();
                const sections = Array.isArray(data) ? data : (data.sections || []);
                if (!sections.length) {
                    sectionList.innerHTML = '<li class="section-item text-muted">В курсе нет разделов.</li>';
                    return;
                }
                sections.sort((a, b) => a.order_number - b.order_number);
                sectionList.innerHTML = '';
                for (const section of sections) {
                    const li = document.createElement('li');
                    li.className = 'section-item section-item p-0';
                    const toggle = document.createElement('div');
                    toggle.className = 'section-toggle';
                    toggle.innerHTML = `<span class="toggle-icon">▶</span><span>${escapeHtml(section.name)}</span>`;
                    toggle.style.cursor = 'pointer';
                    const topicsContainer = document.createElement('div');
                    topicsContainer.className = 'section-topics';
                    topicsContainer.style.display = 'none';
                    let expanded = false;

                    try {
                        const topicsUrl = `${window.API_BASE_URL}topics/by-section/${section.id}`;
                        const topicsResp = await fetch(topicsUrl, {credentials: 'include'});
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

                    const sectionToggleHandler = () => {
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
                const resp = await fetch(url, {credentials: 'include'});
                if (!resp.ok) {
                    const isAuth = window.Auth && window.Auth.isAuthenticated();
                    if (resp.status === 401 || !isAuth) {
                        throw new Error('Для просмотра курса необходимо войти.');
                    } else {
                        throw new Error('Вы не записаны на этот курс. Запишитесь, чтобы увидеть содержимое.');
                    }
                }
                currentCourse = await resp.json();
                courseTitleHeader.textContent = escapeHtml(currentCourse.name);
                if (courseNameMain) courseNameMain.textContent = escapeHtml(currentCourse.name);
                showCourseDescription();
                await buildSidebar();
                await updateEnrollButton();
            } catch (err) {
                console.error(err);
                courseTitleHeader.textContent = 'Курс не найден';
                window.showAccessDenied(topicContent, err.message, false);
                window.showToast(err.message, 'danger');
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
            setupCourseTitleClick();
            if (toggleSidebarBtn) {
                toggleSidebarBtn.addEventListener('click', toggleSidebar);
                initSidebar();
            }

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
                }, 800);
            }
        }

        init();
    });
})();

// Плавающее окно конспекта (без изменений)
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const win = document.getElementById('floatingWindow');
        const tabBtn = document.getElementById('floatingTabButton');
        const closeBtn = document.getElementById('closeWindowBtn');
        const saveBtn = document.getElementById('saveConspectBtn');
        const deleteBtn = document.getElementById('deleteConspectBtn');
        const textarea = win?.querySelector('.conspect-content');
        const header = document.getElementById('windowHeader');

        if (!win) return;

        let isOpen = false;
        let currentNoteId = null;

        function getContainerBounds() {
            const mainContent = document.querySelector('.main-content');
            if (!mainContent) return {
                left: 20,
                top: 20,
                right: window.innerWidth - 20,
                bottom: window.innerHeight - 20
            };
            const rect = mainContent.getBoundingClientRect();
            return {left: rect.left + 10, top: rect.top + 10, right: rect.right - 10, bottom: rect.bottom - 10};
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
                const {left, top, width, height} = JSON.parse(saved);
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
                window.showToast('Сначала выберите тему', 'warning');
                return;
            }
            const content = textarea.value;
            try {
                const result = await window.Notes.saveNote(topicId, content, currentNoteId);
                currentNoteId = result.noteId;
                window.showToast('Конспект сохранён');
            } catch (err) {
                // ошибка уже обработана в Notes.saveNote
            }
        }

        async function deleteCurrentNote() {
            if (!currentNoteId) {
                window.showToast('Нет конспекта для удаления', 'warning');
                return;
            }
            if (!confirm('Вы уверены, что хотите удалить этот конспект?')) return;
            try {
                await window.Notes.deleteNote(currentNoteId);
                textarea.value = '';
                currentNoteId = null;
            } catch (err) {
                // ошибка уже обработана
            }
        }

        function openWin() {
            win.style.display = 'flex';
            isOpen = true;
            loadWinState();
            applyClampedPosition();
            loadNoteForCurrentTopic();
        }

        function closeWin() {
            win.style.display = 'none';
            isOpen = false;
        }

        function toggleWin() {
            isOpen ? closeWin() : openWin();
        }

        window.Notes = window.Notes || {};
        window.Notes.onTopicChanged = function (topicId) {
            if (isOpen) loadNoteForCurrentTopic();
        };
        window.loadNoteForCurrentTopic = loadNoteForCurrentTopic;

        tabBtn?.addEventListener('click', toggleWin);
        closeBtn?.addEventListener('click', closeWin);
        saveBtn?.addEventListener('click', saveCurrentNote);
        if (deleteBtn) deleteBtn.addEventListener('click', deleteCurrentNote);

        win.style.display = 'none';
        isOpen = false;
    });
})();