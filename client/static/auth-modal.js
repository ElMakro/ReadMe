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
            <!-- Поля для входа -->
            <div id="${PREFIX}loginFields">
              <div class="mb-3">
                <input type="text" class="form-control" placeholder="Никнейм" id="${PREFIX}loginNickname" required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Пароль" id="${PREFIX}loginPassword" required>
              </div>
            </div>
            <!-- Поля для регистрации (изначально скрыты и отключены) -->
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
              <button type="button" class="btn btn-outline-secondary flex-fill" id="${PREFIX}showLoginBtn"  style="display: none;">Ко входу</button>
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
  }

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
  closeBtn.addEventListener('click', closeModal);

  function switchToLogin() {
    loginFields.style.display = 'block';
    regFields.style.display = 'none';
    showLoginBtn.style.display = 'none';
    showRegBtn.style.display = 'block'

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
  }

  showLoginBtn.addEventListener('click', switchToLogin);
  showRegBtn.addEventListener('click', switchToReg);

  form.addEventListener('submit', async (e) => {
      e.preventDefault();

      submitBtn.disabled = true;

      const existingError = document.getElementById(`${PREFIX}error`);
      if (existingError) existingError.remove();

      let url, payload;
      main_auth_url = 'http://localhost:8080/readme/v1/'
      if (currentMode === 'login') {
        if (loginNickname.value.trim() === '' || loginPassword.value.trim() === '') {
          showError('Заполните никнейм и пароль');
          resetButton();
          return;
        }
        url = `${main_auth_url}auth/login`;
        payload = {
          nickname: loginNickname.value.trim(),
          password: loginPassword.value
        };
      } else {
        if (regNickname.value.trim() === '' || regPassword.value.trim() === '') {
          showError('Заполните обязательные поля');
          resetButton();
          return;
        }
        if (regPassword.value !== regConfirm.value) {
          showError('Пароли не совпадают');
          resetButton();
          return;
        }
        if (loginPassword.value.trim().length < 8 ||
            regPassword.value.trim().length < 8 ||
            regConfirm.value.trim().length < 8) {
            showError('Длина пароля должна быть не менее 8 символов')
            resetButton();
            return;
        }
        url = `${main_auth_url}auth/reg`;
        payload = {
          nickname: regNickname.value.trim(),
          email: regEmail.value.trim() || undefined,
          password: regPassword.value
        };
      }

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload)
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
          const errorMessage = data?.detail
            ? (Array.isArray(data.detail)
                ? data.detail.map(e => e.msg).join(', ')
                : data.detail)
            : `Ошибка сервера (${response.status})`;
          throw new Error(errorMessage);
        }

        if (currentMode === 'login') {
          console.log('Вход выполнен:', data);
          closeModal();
          window.dispatchEvent(new CustomEvent('auth-changed', { detail: { loggedIn: true, user: data } }));
        } else {
          console.log('Регистрация успешна:', data);
          switchToLogin();
          loginNickname.value = regNickname.value;
          showError('Регистрация прошла успешно! Теперь войдите.', 'success');
          form.reset();
        }
      } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message);
      }

      function showError(message, type = 'danger') {
        const old = document.getElementById(`${PREFIX}error`);
        if (old) old.remove();
        const div = document.createElement('div');
        div.id = `${PREFIX}error`;
        div.className = `alert alert-${type} mt-2`;
        div.textContent = message;
        form.appendChild(div);
      }
    });

  window.AuthModal = { open: openModal, close: closeModal };
})();
