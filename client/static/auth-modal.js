// static/auth-modal.js
(function () {
    const PREFIX = 'auth-modal-';

    function getErrorMessage(data, defaultMsg) {
        if (!data) return defaultMsg;
        if (typeof data.detail === 'string') return data.detail;
        if (Array.isArray(data.detail) && data.detail[0]?.msg) {
            return data.detail.map(e => e.msg).join(', ');
        }
        if (data.message) return data.message;
        if (data.error) return data.error;
        return defaultMsg;
    }

    function validateNickname(nickname) {
        if (!nickname || nickname.length < 4) return 'Никнейм должен содержать не менее 4 символов.';
        if (nickname.length > 32) return 'Никнейм не может быть длиннее 32 символов.';
        const nicknameRegex = /^[A-Za-z0-9_\-\.!@#$%^&*()+=?<>]+$/;
        if (!nicknameRegex.test(nickname)) {
            return 'Никнейм может содержать только латинские буквы, цифры и символы: _ - . ! @ # $ % ^ & * ( ) + = ? < >';
        }
        return null;
    }

    function validateEmail(email) {
        if (!email) return 'Email обязателен.';
        const emailRegex = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
        if (!emailRegex.test(email)) return 'Введите корректный email (например, user@example.com).';
        return null;
    }

    function validatePassword(password, isRegistration = true) {
        if (!password) return 'Пароль обязателен.';
        if (password.length < 8) return 'Пароль должен быть не менее 8 символов.';
        if (isRegistration && password.length > 64) return 'Пароль не может быть длиннее 64 символов.';
        return null;
    }

    const template = `
    <div class="modal-overlay" id="${PREFIX}overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h3 id="${PREFIX}title">Вход</h3>
          <button class="modal-close" id="${PREFIX}close">&times;</button>
        </div>
        <div class="modal-body">
          <form id="${PREFIX}form" novalidate>
            <div id="${PREFIX}loginFields">
              <div class="mb-3">
                <input type="text" class="form-control" placeholder="Никнейм" id="${PREFIX}loginNickname" autocomplete="username" required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Пароль" id="${PREFIX}loginPassword" autocomplete="current-password" required>
              </div>
            </div>
            <div id="${PREFIX}regFields" style="display: none;">
              <div class="mb-3">
                <input type="text" class="form-control" placeholder="Никнейм" id="${PREFIX}regNickname" disabled required>
              </div>
              <div class="mb-3">
                <input type="email" class="form-control" placeholder="Email *" id="${PREFIX}regEmail" disabled required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Пароль" id="${PREFIX}regPassword" disabled required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Подтвердите пароль" id="${PREFIX}regConfirm" disabled required>
              </div>
              <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="${PREFIX}regConsent" disabled>
                <label class="form-check-label" for="${PREFIX}regConsent">
                  Я соглашаюсь с <a href="/policy" target="_blank">политикой конфиденциальности</a>
                </label>
              </div>
            </div>

            <div class="d-flex gap-2 mb-3">
              <button type="button" class="btn btn-outline-secondary flex-fill" id="${PREFIX}showLoginBtn" style="display: none;">Ко входу</button>
              <button type="button" class="btn btn-outline-secondary flex-fill" id="${PREFIX}showRegBtn">К регистрации</button>
            </div>
            <button type="submit" class="btn-login w-100" id="${PREFIX}submitBtn">Войти</button>
          </form>
        </div>
      </div>
    </div>
  `;

    let currentMode = 'login';
    document.body.insertAdjacentHTML('beforeend', template);

    const overlay = document.getElementById(`${PREFIX}overlay`);
    const closeBtn = document.getElementById(`${PREFIX}close`);
    const loginFields = document.getElementById(`${PREFIX}loginFields`);
    const regFields = document.getElementById(`${PREFIX}regFields`);
    const modalTitle = document.getElementById(`${PREFIX}title`);
    const submitBtn = document.getElementById(`${PREFIX}submitBtn`);
    const showLoginBtn = document.getElementById(`${PREFIX}showLoginBtn`);
    const showRegBtn = document.getElementById(`${PREFIX}showRegBtn`);
    const form = document.getElementById(`${PREFIX}form`);

    const loginNickname = document.getElementById(`${PREFIX}loginNickname`);
    const loginPassword = document.getElementById(`${PREFIX}loginPassword`);
    const regNickname = document.getElementById(`${PREFIX}regNickname`);
    const regEmail = document.getElementById(`${PREFIX}regEmail`);
    const regPassword = document.getElementById(`${PREFIX}regPassword`);
    const regConfirm = document.getElementById(`${PREFIX}regConfirm`);
    const regConsent = document.getElementById(`${PREFIX}regConsent`);

    async function fillSavedCredentials() {
        if (!window.PasswordCredential || !navigator.credentials) return;
        try {
            const credential = await navigator.credentials.get({
                password: true,
                mediation: 'optional'
            });
            if (credential && credential.type === 'password') {
                loginNickname.value = credential.id;
                loginPassword.value = credential.password;
            }
        } catch (err) {
            console.warn('Credentials error:', err);
        }
    }

    async function savePasswordWithAPI(nickname, password) {
        if (!window.PasswordCredential || !navigator.credentials) {
            console.warn('Credential Management API не поддерживается');
            return;
        }
        try {
            const cred = new PasswordCredential({
                id: nickname,
                password: password,
                name: nickname,
            });
            cred.idName = 'nickname';
            cred.passwordName = 'password';
            await navigator.credentials.store(cred);
        } catch (err) {
            console.warn('Не удалось сохранить пароль:', err);
        }
    }

    async function openModal() {
        overlay.classList.add('active');
        switchToLogin();
        fillSavedCredentials();
        setTimeout(() => loginNickname.focus(), 50);
    }

    function closeModal() {
        overlay.classList.remove('active');
        form.reset();
        removeError();
        submitBtn.disabled = false;
    }

    closeBtn.addEventListener('click', closeModal);

    function switchToLogin() {
        loginFields.style.display = 'block';
        regFields.style.display = 'none';
        showLoginBtn.style.display = 'none';
        showRegBtn.style.display = 'block';

        loginNickname.required = true;
        loginPassword.required = true;
        loginNickname.disabled = false;
        loginPassword.disabled = false;

        regNickname.required = false;
        regEmail.required = false;
        regPassword.required = false;
        regConfirm.required = false;
        regConsent.required = false;
        regNickname.disabled = true;
        regEmail.disabled = true;
        regPassword.disabled = true;
        regConfirm.disabled = true;
        regConsent.disabled = true;

        modalTitle.textContent = 'Вход';
        submitBtn.textContent = 'Войти';
        currentMode = 'login';

        submitBtn.disabled = false;
        removeError();
    }

    function switchToReg() {
        loginFields.style.display = 'none';
        regFields.style.display = 'block';
        showRegBtn.style.display = 'none';
        showLoginBtn.style.display = 'block';

        loginNickname.required = false;
        loginPassword.required = false;
        loginNickname.disabled = true;
        loginPassword.disabled = true;

        regNickname.required = true;
        regEmail.required = true;
        regPassword.required = true;
        regConfirm.required = true;
        regConsent.required = true;
        regNickname.disabled = false;
        regEmail.disabled = false;
        regPassword.disabled = false;
        regConfirm.disabled = false;
        regConsent.disabled = false;

        modalTitle.textContent = 'Регистрация';
        submitBtn.textContent = 'Зарегистрироваться';
        currentMode = 'reg';

        submitBtn.disabled = false;
        removeError();
    }

    showLoginBtn.addEventListener('click', switchToLogin);
    showRegBtn.addEventListener('click', switchToReg);

    async function fetchProfile() {
        const profileUrl = `${window.API_BASE_URL}users/profile`;
        const response = await fetch(profileUrl, {
            method: 'GET',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'}
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || 'Не удалось получить профиль');
        }
        return response.json();
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;
        removeError();

        try {
            if (currentMode === 'login') {
                const nickname = loginNickname.value.trim();
                const password = loginPassword.value;

                const nicknameErr = validateNickname(nickname);
                if (nicknameErr) throw new Error(nicknameErr);
                const passwordErr = validatePassword(password, false);
                if (passwordErr) throw new Error(passwordErr);

                const loginResponse = await fetch(`${window.API_BASE_URL}auth/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({nickname, password})
                });

                if (!loginResponse.ok) {
                    let errorData = null;
                    try {
                        errorData = await loginResponse.json();
                    } catch (e) {}
                    let errorMessage;
                    switch (loginResponse.status) {
                        case 401:
                            errorMessage = 'Неверный никнейм или пароль.';
                            break;
                        case 403:
                            errorMessage = 'Доступ запрещён. Проверьте данные.';
                            break;
                        case 500:
                            errorMessage = 'Ошибка на сервере. Попробуйте позже.';
                            break;
                        case 502:
                        case 503:
                        case 504:
                            errorMessage = 'Сервер временно недоступен. Повторите попытку.';
                            break;
                        default:
                            errorMessage = getErrorMessage(errorData, `Ошибка входа (${loginResponse.status})`);
                    }
                    throw new Error(errorMessage);
                }

                const userProfile = await fetchProfile();
                window.AppState.currentUser = userProfile;
                window.dispatchEvent(new CustomEvent('auth-changed', {detail: {user: userProfile}}));
                await savePasswordWithAPI(nickname, password);
                closeModal();
                location.reload();
            } else {
                const nickname = regNickname.value.trim();
                const email = regEmail.value.trim();
                const password = regPassword.value;
                const confirm = regConfirm.value;
                const consent = regConsent.checked;

                const nicknameErr = validateNickname(nickname);
                if (nicknameErr) throw new Error(nicknameErr);
                const emailErr = validateEmail(email);
                if (emailErr) throw new Error(emailErr);
                const passwordErr = validatePassword(password, true);
                if (passwordErr) throw new Error(passwordErr);
                if (password !== confirm) throw new Error('Пароли не совпадают.');
                if (!consent) throw new Error('Необходимо согласие с политикой конфиденциальности.');

                const regResponse = await fetch(`${window.API_BASE_URL}auth/reg`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({nickname, email, password})
                });

                if (!regResponse.ok) {
                    let errorData = null;
                    try {
                        errorData = await regResponse.json();
                    } catch (e) {}
                    let errorMessage;
                    switch (regResponse.status) {
                        case 400:
                            errorMessage = getErrorMessage(errorData, 'Некорректные данные. Проверьте поля.');
                            break;
                        case 409:
                            errorMessage = 'Пользователь с таким никнеймом или email уже существует.';
                            break;
                        case 422:
                            errorMessage = getErrorMessage(errorData, 'Ошибка валидации. Проверьте все поля.');
                            break;
                        case 500:
                            errorMessage = 'Ошибка на сервере. Попробуйте позже.';
                            break;
                        default:
                            errorMessage = getErrorMessage(errorData, `Ошибка регистрации (${regResponse.status})`);
                    }
                    throw new Error(errorMessage);
                }

                const loginResponse = await fetch(`${window.API_BASE_URL}auth/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({nickname, password})
                });

                if (!loginResponse.ok) {
                    throw new Error('Регистрация успешна, но не удалось войти автоматически. Попробуйте войти вручную.');
                }

                const userProfile = await fetchProfile();
                window.AppState.currentUser = userProfile;
                window.dispatchEvent(new CustomEvent('auth-changed', {detail: {user: userProfile}}));
                await savePasswordWithAPI(nickname, password);
                closeModal();
                location.reload();
            }
        } catch (error) {
            console.error('Ошибка:', error);
            let userMessage = error.message;
            if (error.name === 'TypeError' && (error.message.includes('fetch') || error.message.includes('network'))) {
                userMessage = 'Нет соединения с сервером. Проверьте интернет.';
            } else if (error.name === 'AbortError') {
                userMessage = 'Запрос прерван. Повторите попытку.';
            }
            showError(userMessage);
        } finally {
            submitBtn.disabled = false;
        }
    });

    function showError(message, type = 'danger') {
        const old = document.getElementById(`${PREFIX}error`);
        if (old) old.remove();
        const div = document.createElement('div');
        div.id = `${PREFIX}error`;
        div.className = `alert alert-${type} mt-2`;
        div.textContent = message;
        form.appendChild(div);
    }

    function removeError() {
        const err = document.getElementById(`${PREFIX}error`);
        if (err) err.remove();
    }

    window.AuthModal = {open: openModal, close: closeModal};
})();