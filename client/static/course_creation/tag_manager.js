// static/course_creation/tag_manager.js
(function() {
    // Вспомогательная функция для экранирования HTML
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    class TagManager {
        constructor(container, tagsArray, options = {}) {
            this.container = container;        // DOM-элемент, куда будет помещён UI
            this.tags = tagsArray;              // ссылка на массив тегов (будет изменяться)
            this.deleteMode = false;
            this.inputField = null;
            this.deleteModeBtn = null;
            this.tagsContainer = null;

            this.render();
        }

        render() {
            // Очищаем контейнер и создаём структуру
            this.container.innerHTML = `
                <div class="d-flex gap-2 mb-2">
                    <input type="text" class="form-control form-control-sm tag-input" placeholder="Название тега + Enter" style="width: auto; flex-grow: 1;">
                    <button class="btn btn-sm btn-outline-danger delete-mode-tag-btn" type="button">Удалить теги</button>
                </div>
                <div class="tag-chips-container d-flex flex-wrap"></div>
            `;

            this.inputField = this.container.querySelector('.tag-input');
            this.deleteModeBtn = this.container.querySelector('.delete-mode-tag-btn');
            this.tagsContainer = this.container.querySelector('.tag-chips-container');

            // Обработчики событий
            this.inputField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addTag();
                }
            });

            this.deleteModeBtn.addEventListener('click', () => {
                this.deleteMode = !this.deleteMode;
                this.deleteModeBtn.textContent = this.deleteMode ? 'Готово' : 'Удалить теги';
                this.renderTags();
            });

            this.renderTags();
        }

        addTag() {
            let newTag = this.inputField.value.trim();
            if (newTag === '') return;
            this.tags.push(newTag);
            this.inputField.value = '';
            this.renderTags();
        }

        renderTags() {
            this.tagsContainer.innerHTML = '';
            this.tags.forEach((tag, idx) => {
                const chip = document.createElement('span');
                chip.className = 'badge bg-secondary me-1 mb-1 p-2';
                chip.style.fontSize = '0.9rem';
                if (this.deleteMode) {
                    chip.innerHTML = `${escapeHtml(tag)} <span class="remove-tag-btn ms-1" data-tag-idx="${idx}" style="cursor:pointer; font-weight:bold;">&times;</span>`;
                } else {
                    chip.textContent = tag;
                }
                this.tagsContainer.appendChild(chip);
            });

            if (this.deleteMode) {
                this.tagsContainer.querySelectorAll('.remove-tag-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const idx = parseInt(btn.dataset.tagIdx);
                        this.tags.splice(idx, 1);
                        this.renderTags();
                    });
                });
            }
        }

        // Если нужно принудительно обновить теги извне
        setTags(newTags) {
            this.tags.length = 0;
            this.tags.push(...newTags);
            this.renderTags();
        }
    }

    // Глобальная функция для удобного создания менеджера тегов
    window.initTagManager = (container, tagsArray) => {
        return new TagManager(container, tagsArray);
    };
})();