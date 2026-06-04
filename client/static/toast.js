// static/toast.js
(function() {
    window.showToast = function(message, type = 'success') {
        // Удаляем предыдущий тост, если он есть
        const existing = document.querySelector('.toast-notification');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Автоматическое исчезновение через 3 секунды
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };
})();