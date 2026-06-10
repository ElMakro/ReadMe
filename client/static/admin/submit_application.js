// static/admin/submit_application.js
(function() {
    const form = document.getElementById('applicationForm');
    const submitBtn = document.getElementById('submitBtn');
    const alertContainer = document.getElementById('alertContainer');
    const formBlock = document.getElementById('formBlock');
    const successBlock = document.getElementById('successBlock');

    const API_BASE = window.API_BASE_URL ? window.API_BASE_URL.replace(/\/$/, '') : 'http://localhost:8080/api/v1';
    const SECRET_LINK = window.SECRET_LINK;

    if (!SECRET_LINK) {
        console.error('SECRET_LINK не передан');
        if (alertContainer) {
            alertContainer.innerHTML = '<div class="alert alert-danger">Ошибка: ссылка для подачи заявки некорректна. Обратитесь к администратору.</div>';
        }
    }

    function clearAlertsAndValidation() {
        alertContainer.innerHTML = '';
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    async function submitApplication(event) {
        event.preventDefault();
        clearAlertsAndValidation();

        const nameInput = document.getElementById('name');
        const surnameInput = document.getElementById('surname');
        const patronymicInput = document.getElementById('patronymic');

        let isValid = true;
        if (!nameInput.value.trim()) {
            nameInput.classList.add('is-invalid');
            isValid = false;
        }
        if (!surnameInput.value.trim()) {
            surnameInput.classList.add('is-invalid');
            isValid = false;
        }
        if (!patronymicInput.value.trim()) {
            patronymicInput.classList.add('is-invalid');
            isValid = false;
        }
        if (!isValid) {
            window.showToast('Пожалуйста, заполните все обязательные поля.', 'danger');
            return;
        }

        if (!SECRET_LINK) {
            window.showToast('Ссылка для подачи заявки недоступна. Обратитесь к администратору.', 'danger');
            return;
        }

        const payload = {
            name: nameInput.value.trim(),
            surname: surnameInput.value.trim(),
            patronymic: patronymicInput.value.trim()
        };

        const sendRequest = async () => {
            const url = `${API_BASE}/users/submit-professor-application/${SECRET_LINK}`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload)
            });
            if (response.status === 201) {
                formBlock.style.display = 'none';
                successBlock.style.display = 'block';
                return;
            }
            let errorMessage = 'Произошла ошибка при отправке заявки.';
            if (response.status === 403) {
                errorMessage = 'Вы уже являетесь преподавателем. Подача повторной заявки невозможна.';
            } else if (response.status === 409) {
                const errorData = await response.json().catch(() => ({}));
                errorMessage = errorData.detail || 'Вы уже подали заявку на роль преподавателя. Ожидайте рассмотрения.';
            } else if (response.status === 401) {
                throw new Error('unauthorized');
            } else if (response.status === 404) {
                errorMessage = 'Неверная ссылка для подачи заявки. Обратитесь к администратору.';
            } else {
                const errorData = await response.json().catch(() => ({}));
                errorMessage = errorData.detail || errorMessage;
            }
            window.showToast(errorMessage, 'danger');
        };

        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Отправка...';

        try {
            await sendRequest();
        } catch (err) {
            if (err.message === 'unauthorized') {
                window.Auth.retryAfterLogin(sendRequest);
            } else {
                window.showToast(err.message, 'danger');
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Отправить заявку';
        }
    }

    if (form) form.addEventListener('submit', submitApplication);
})();