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
              <button type="button" class="btn btn-outline-secondary flex-fill" id="${PREFIX}showLoginBtn">Вход</button>
              <button type="button" class="btn btn-outline-secondary flex-fill" id="${PREFIX}showRegBtn">Регистрация</button>
            </div>
            <button type="submit" class="btn-login w-100" id="${PREFIX}submitBtn">Войти</button>
          </form>
        </div>
      </div>
    </div>
  `;

  let currentMode = 'login';
  document.body.insertAdjacentHTML('beforeend', template);

  // Получаем элементы
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

  // Закрытие по оверлею и кнопке
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });
  closeBtn.addEventListener('click', closeModal);

  function switchToLogin() {
    // Показываем поля входа, скрываем регистрацию
    loginFields.style.display = 'block';
    regFields.style.display = 'none';

    // Включаем поля входа
    loginNickname.required = true;
    loginPassword.required = true;
    loginNickname.disabled = false;
    loginPassword.disabled = false;

    // Отключаем и снимаем required с полей регистрации
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
    // Скрываем вход, показываем регистрацию
    loginFields.style.display = 'none';
    regFields.style.display = 'block';

    // Отключаем поля входа
    loginNickname.required = false;
    loginPassword.required = false;
    loginNickname.disabled = true;
    loginPassword.disabled = true;

    // Включаем поля регистрации
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

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    if (currentMode === 'login') {
      // Достаточно, что поля входа уже enabled и required
      if (loginNickname.value.trim() === '' || loginPassword.value.trim() === '') {
        alert('Заполните никнейм и пароль');
        return;
      }
      alert(`Привет, ${loginNickname.value}!`);
    } else {
      // Проверки для регистрации
      if (regNickname.value.trim() === '' || regPassword.value.trim() === '') {
        alert('Заполните обязательные поля');
        return;
      }
      if (regPassword.value !== regConfirm.value) {
        alert('Пароли не совпадают!');
        return;
      }
      alert(`Пользователь ${regNickname.value} создан!`);
    }

    closeModal();
  });

  // Экспорт API
  window.AuthModal = { open: openModal, close: closeModal };
})();