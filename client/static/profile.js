(function(){
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;

    logoutBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        const logoutUrl = 'http://localhost:8080/readme/v1/auth/logout';

        try {
            const response = await fetch(logoutUrl, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                const data = await response.json().catch(() => null);
                const msg = data?.detail || `Ошибка сервера (${response.status})`;
                throw new Error(msg);
            }

            // Очищаем только флаг loggedIn
            localStorage.removeItem('loggedIn');

            // Перенаправляем на главную
            window.location.href = '/';

        } catch (error) {
            console.error('Ошибка выхода:', error);
            localStorage.removeItem('loggedIn');
            alert('Не удалось выполнить выход корректно, но вы будете перенаправлены на главную.');
            window.location.href = '/';
        }
    });
})();