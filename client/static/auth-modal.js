(function () {
  const PREFIX = 'auth-modal-';

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
                <input type="text" class="form-control" placeholder="Никнейм" id="${PREFIX}loginNickname" required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Пароль" id="${PREFIX}loginPassword" required>
              </div>
            </div>
            <div id="${PREFIX}regFields" style="display: none;">
              <div class="mb-3">
                <input type="text" class="form-control" placeholder="Никнейм" id="${PREFIX}regNickname" disabled required>
              </div>
              <div class="mb-3">
                <input type="email" class="form-control" placeholder="Email" id="${PREFIX}regEmail" disabled>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Пароль" id="${PREFIX}regPassword" disabled required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Подтвердите пароль" id="${PREFIX}regConfirm" disabled required>
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

  function openModal() {
    overlay.classList.add('active');
    switchToLogin();
  }

  function closeModal() {
    overlay.classList.remove('active');
    form.reset();
    removeError();
    submitBtn.disabled = false;
  }

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
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
    regPassword.required = false;
    regConfirm.required = false;
    regNickname.disabled = true;
    regEmail.disabled = true;
    regPassword.disabled = true;
    regConfirm.disabled = true;

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
    regPassword.required = true;
    regConfirm.required = true;
    regNickname.disabled = false;
    regEmail.disabled = false;
    regPassword.disabled = false;
    regConfirm.disabled = false;

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
      headers: { 'Content-Type': 'application/json' }
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

    let url, payload;

    try {
      if (currentMode === 'login') {
        const nickname = loginNickname.value.trim();
        const password = loginPassword.value;

        if (!nickname || !password) {
          throw new Error('Заполните никнейм и пароль');
        }
        if (password.length < 8) {
          throw new Error('Длина пароля должна быть не менее 8 символов');
        }

        url = `${window.API_BASE_URL}auth/login`;
        payload = { nickname, password };

        const loginResponse = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload)
        });

        if (!loginResponse.ok) {
          const errorData = await loginResponse.json().catch(() => null);
          const errorMessage = errorData?.detail
            ? (Array.isArray(errorData.detail) ? errorData.detail.map(e => e.msg).join(', ') : errorData.detail)
            : `Ошибка сервера (${loginResponse.status})`;
          throw new Error(errorMessage);
        }

        // После успешного входа получаем профиль пользователя
        const userProfile = await fetchProfile();
        window.AppState.currentUser = userProfile;
        window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: userProfile } }));
        closeModal();
      }
      else { // регистрация
        const nickname = regNickname.value.trim();
        const email = regEmail.value.trim() || undefined;
        const password = regPassword.value;
        const confirm = regConfirm.value;

        if (!nickname || !password) {
          throw new Error('Заполните обязательные поля');
        }
        if (password !== confirm) {
          throw new Error('Пароли не совпадают');
        }
        if (password.length < 8) {
          throw new Error('Длина пароля должна быть не менее 8 символов');
        }

        url = `${window.API_BASE_URL}auth/reg`;
        payload = { nickname, email, password };

        const regResponse = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload)
        });

        if (!regResponse.ok) {
          const errorData = await regResponse.json().catch(() => null);
          const errorMessage = errorData?.detail
            ? (Array.isArray(errorData.detail) ? errorData.detail.map(e => e.msg).join(', ') : errorData.detail)
            : `Ошибка сервера (${regResponse.status})`;
          throw new Error(errorMessage);
        }

        // Регистрация успешна, переключаем на форму входа
        switchToLogin();
        loginNickname.value = nickname;
        showError('Регистрация прошла успешно! Теперь войдите.', 'success');
        form.reset();
      }
    } catch (error) {
      console.error('Ошибка:', error);
      showError(error.message);
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

  window.AuthModal = { open: openModal, close: closeModal };
})();