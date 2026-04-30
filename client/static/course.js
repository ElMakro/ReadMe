(function() {
    // ========== ТЕМА (ваш существующий код) ==========
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    const htmlElement = document.documentElement;

    function setTheme(newTheme) {
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeButton(newTheme);
    }

    function updateThemeButton(theme) {
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Свет';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Тьма';
        }
    }

    function toggleTheme() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }

    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

    // ========== ВХОД ==========
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            if (window.AuthModal && typeof window.AuthModal.open === 'function') {
                window.AuthModal.open();
            } else {
                console.error('AuthModal не готов');
            }
        });
    }

    // ========== АККОРДЕОН И ПЕРЕКЛЮЧЕНИЕ КОНТЕНТА ==========
    const sectionList = document.getElementById('sectionList');
    const sectionContainers = document.querySelectorAll('.section-container');

    function showSection(sectionId) {
        sectionContainers.forEach(div => div.style.display = 'none');
        const target = document.getElementById('content-' + sectionId);
        if (target) target.style.display = 'block';
    }

    function scrollToTopic(topicId) {
        const topicElement = document.getElementById(topicId);
        if (topicElement) {
            topicElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    if (sectionList) {
        sectionList.addEventListener('click', (e) => {
            const toggle = e.target.closest('.section-toggle');
            const topicLink = e.target.closest('.topic-link');

            if (toggle) {
                e.preventDefault();
                const targetId = toggle.dataset.target;
                const topicsUl = document.getElementById('topics-' + targetId);
                const icon = toggle.querySelector('.toggle-icon');

                if (topicsUl) {
                    if (topicsUl.style.display === 'none' || topicsUl.style.display === '') {
                        topicsUl.style.display = 'block';
                        if (icon) icon.textContent = '▼';
                    } else {
                        topicsUl.style.display = 'none';
                        if (icon) icon.textContent = '▶';
                    }
                }
                showSection(targetId);
                document.querySelectorAll('.section-toggle').forEach(el => el.classList.remove('active'));
                toggle.classList.add('active');
                document.querySelectorAll('.topic-link').forEach(el => el.classList.remove('active'));
            }

            if (topicLink) {
                e.preventDefault();
                const contentId = topicLink.dataset.content;
                const parentSection = topicLink.closest('.section-item').querySelector('.section-toggle');
                if (parentSection) {
                    const sectionId = parentSection.dataset.target;
                    showSection(sectionId);
                    document.querySelectorAll('.section-toggle').forEach(el => el.classList.remove('active'));
                    parentSection.classList.add('active');
                }
                document.querySelectorAll('.topic-link').forEach(el => el.classList.remove('active'));
                topicLink.classList.add('active');
                scrollToTopic(contentId);
            }
        });
    }

    // Начальное состояние
    const defaultSectionToggle = document.querySelector('.section-toggle[data-target="section1"]');
    if (defaultSectionToggle) {
        defaultSectionToggle.classList.add('active');
        const topicsUl = document.getElementById('topics-section1');
        if (topicsUl) {
            topicsUl.style.display = 'block';
            const icon = defaultSectionToggle.querySelector('.toggle-icon');
            if (icon) icon.textContent = '▼';
        }
        showSection('section1');
    }
})();

// ========== Плавающий Конспект ==========
(function initFloatingFeatures() {
    const win = document.getElementById('floatingWindow');
    const header = document.getElementById('windowHeader');
    const closeBtn = document.getElementById('closeWindowBtn');
    const tabBtn = document.getElementById('floatingTabButton');

    if (!win || !header || !tabBtn) return;

    // 1. Открыть окно по клику на кнопку
    tabBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (win.style.display === 'none' || win.style.display === '') {
            win.style.display = 'block';
            // корректируем позицию, чтобы не вылезало
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

    // 2. Закрыть окно
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            win.style.display = 'none';
        });
    }

    // 3. Перетаскивание окна (если работает старый код - не трогаем, но добавим свой)
    // Удалим старые события, если они есть, чтобы не было дублей
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

    // 4. Перетаскивание кнопки (только вертикаль)
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

    // Touch-события
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

    // При ресайзе корректируем кнопку
    window.addEventListener('resize', () => {
        let top = getBtnTop();
        const maxTop = window.innerHeight - tabBtn.offsetHeight;
        if (top > maxTop) tabBtn.style.top = maxTop + 'px';
        if (top < 0) tabBtn.style.top = '0px';
    });

    // 5. Изменение размеров окна (ресайз)
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

            // Минимальные размеры
            newWidth = Math.max(200, newWidth);
            newHeight = Math.max(150, newHeight);

            // Чтобы окно не вылезало за правый и нижний края
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