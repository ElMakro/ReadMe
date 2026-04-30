document.addEventListener('DOMContentLoaded', () => {
    const windowEl = document.getElementById('floatingWindow');
    const headerEl = document.getElementById('windowHeader');
    const closeBtn = document.getElementById('closeWindowBtn');
    const buttonEl = document.getElementById('draggableButton');

    // ---- 1. Окно: перетаскивание и показ/скрытие (без изменений) ----
    let isDraggingWindow = false;
    let winStartX, winStartY, winInitialLeft, winInitialTop;

    function correctWindowPosition() {
        const rect = windowEl.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;
        let left = parseInt(windowEl.style.left);
        let top = parseInt(windowEl.style.top);
        if (isNaN(left)) left = 100;
        if (isNaN(top)) top = 100;
        left = Math.min(Math.max(0, left), maxX);
        top = Math.min(Math.max(0, top), maxY);
        windowEl.style.left = left + 'px';
        windowEl.style.top = top + 'px';
    }

    function showWindow() {
        if (windowEl.style.display === 'none' || windowEl.style.display === '') {
            windowEl.style.display = 'block';
            correctWindowPosition();
        }
    }
    function hideWindow() { windowEl.style.display = 'none'; }

    closeBtn.addEventListener('click', hideWindow);
    buttonEl.addEventListener('click', (e) => {
        showWindow();
        e.stopPropagation();
    });

    // перетаскивание окна мышью
    function onWinMouseDown(e) {
        if (!headerEl.contains(e.target)) return;
        isDraggingWindow = true;
        const cs = window.getComputedStyle(windowEl);
        winInitialLeft = parseInt(cs.left);
        winInitialTop = parseInt(cs.top);
        winStartX = e.clientX;
        winStartY = e.clientY;
        document.addEventListener('mousemove', onWinMouseMove);
        document.addEventListener('mouseup', onWinMouseUp);
        e.preventDefault();
    }
    function onWinMouseMove(e) {
        if (!isDraggingWindow) return;
        let left = winInitialLeft + (e.clientX - winStartX);
        let top = winInitialTop + (e.clientY - winStartY);
        const maxX = window.innerWidth - windowEl.offsetWidth;
        const maxY = window.innerHeight - windowEl.offsetHeight;
        left = Math.min(Math.max(0, left), maxX);
        top = Math.min(Math.max(0, top), maxY);
        windowEl.style.left = left + 'px';
        windowEl.style.top = top + 'px';
    }
    function onWinMouseUp() {
        isDraggingWindow = false;
        document.removeEventListener('mousemove', onWinMouseMove);
        document.removeEventListener('mouseup', onWinMouseUp);
    }
    headerEl.addEventListener('mousedown', onWinMouseDown);

    // touch для окна
    function onWinTouchStart(e) {
        if (!headerEl.contains(e.target)) return;
        e.preventDefault();
        const touch = e.touches[0];
        const cs = window.getComputedStyle(windowEl);
        winInitialLeft = parseInt(cs.left);
        winInitialTop = parseInt(cs.top);
        winStartX = touch.clientX;
        winStartY = touch.clientY;
        isDraggingWindow = true;
        document.addEventListener('touchmove', onWinTouchMove);
        document.addEventListener('touchend', onWinTouchEnd);
    }
    function onWinTouchMove(e) {
        if (!isDraggingWindow) return;
        e.preventDefault();
        const touch = e.touches[0];
        let left = winInitialLeft + (touch.clientX - winStartX);
        let top = winInitialTop + (touch.clientY - winStartY);
        const maxX = window.innerWidth - windowEl.offsetWidth;
        const maxY = window.innerHeight - windowEl.offsetHeight;
        left = Math.min(Math.max(0, left), maxX);
        top = Math.min(Math.max(0, top), maxY);
        windowEl.style.left = left + 'px';
        windowEl.style.top = top + 'px';
    }
    function onWinTouchEnd() {
        isDraggingWindow = false;
        document.removeEventListener('touchmove', onWinTouchMove);
        document.removeEventListener('touchend', onWinTouchEnd);
    }
    headerEl.addEventListener('touchstart', onWinTouchStart);

    // ---- 2. Перетаскивание кнопки ТОЛЬКО ПО ВЕРТИКАЛИ (привязана к правому краю) ----
    let isDraggingButton = false;
    let btnStartY, btnInitialTop;      // горизонталь не нужна
    // ширина кнопки известна, right всегда -40px (половина ширины) – менять не будем

    // Получить текущее значение top в пикселях (учитывая, что может быть в %)
    function getButtonTop() {
        let top = parseFloat(window.getComputedStyle(buttonEl).top);
        if (isNaN(top)) {
            // если top задан в процентах (например, 50%), пересчитаем в px
            const rect = buttonEl.getBoundingClientRect();
            top = rect.top;
        }
        return top;
    }

    function onButtonMouseDown(e) {
        isDraggingButton = true;
        btnInitialTop = getButtonTop();
        btnStartY = e.clientY;
        document.addEventListener('mousemove', onButtonMouseMove);
        document.addEventListener('mouseup', onButtonMouseUp);
        e.preventDefault();
        e.stopPropagation();
    }

    function onButtonMouseMove(e) {
        if (!isDraggingButton) return;
        let dy = e.clientY - btnStartY;
        let newTop = btnInitialTop + dy;
        // ограничиваем, чтобы кнопка не уходила за экран
        const btnHeight = buttonEl.offsetHeight;
        const minTop = 0;
        const maxTop = window.innerHeight - btnHeight;
        newTop = Math.min(Math.max(minTop, newTop), maxTop);
        buttonEl.style.top = newTop + 'px';
        // !!! right не трогаем, остаётся -40px (или то значение, которое в CSS)
        // Если при перетаскивании CSS-правило right сбрасывается, зафиксируем:
        buttonEl.style.right = '-40px';   // половина ширины (80/2)
    }

    function onButtonMouseUp() {
        isDraggingButton = false;
        document.removeEventListener('mousemove', onButtonMouseMove);
        document.removeEventListener('mouseup', onButtonMouseUp);
    }

    // touch-версия
    function onButtonTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        btnInitialTop = getButtonTop();
        btnStartY = touch.clientY;
        isDraggingButton = true;
        document.addEventListener('touchmove', onButtonTouchMove);
        document.addEventListener('touchend', onButtonTouchEnd);
    }

    function onButtonTouchMove(e) {
        if (!isDraggingButton) return;
        e.preventDefault();
        const touch = e.touches[0];
        let dy = touch.clientY - btnStartY;
        let newTop = btnInitialTop + dy;
        const btnHeight = buttonEl.offsetHeight;
        const minTop = 0;
        const maxTop = window.innerHeight - btnHeight;
        newTop = Math.min(Math.max(minTop, newTop), maxTop);
        buttonEl.style.top = newTop + 'px';
        buttonEl.style.right = '-40px';
    }

    function onButtonTouchEnd() {
        isDraggingButton = false;
        document.removeEventListener('touchmove', onButtonTouchMove);
        document.removeEventListener('touchend', onButtonTouchEnd);
    }

    buttonEl.addEventListener('mousedown', onButtonMouseDown);
    buttonEl.addEventListener('touchstart', onButtonTouchStart);

    // При изменении размера окна корректируем положение кнопки (чтобы не уползла за границы)
    window.addEventListener('resize', () => {
        if (windowEl.style.display !== 'none') correctWindowPosition();
        // поправить top кнопки, если ушла за границы
        const btnTop = getButtonTop();
        const btnHeight = buttonEl.offsetHeight;
        const maxTop = window.innerHeight - btnHeight;
        if (btnTop > maxTop) buttonEl.style.top = maxTop + 'px';
        if (btnTop < 0) buttonEl.style.top = '0px';
        // зафиксировать right
        buttonEl.style.right = '-40px';
    });
});