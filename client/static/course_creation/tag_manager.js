// static/course_creation/tag_manager.js
(function() {
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    class TagManager {
        constructor(container, tagsArray, options = {}) {
            this.container = container;
            this.tags = tagsArray;
            this.deleteMode = false;
            this.inputField = null;
            this.deleteModeBtn = null;
            this.tagsContainer = null;

            this.render();
        }

        render() {
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

            // FIX: ограничение длины тега
            if (newTag.length > 30) {
                window.showToast('Тег не может быть длиннее 30 символов', 'warning');
                return;
            }

            // FIX: проверка на уникальность (регистронезависимо)
            const lowerNewTag = newTag.toLowerCase();
            if (this.tags.some(tag => tag.toLowerCase() === lowerNewTag)) {
                window.showToast('Такой тег уже существует', 'warning');
                return;
            }

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

        setTags(newTags) {
            this.tags.length = 0;
            this.tags.push(...newTags);
            this.renderTags();
        }
    }

    window.initTagManager = (container, tagsArray) => {
        return new TagManager(container, tagsArray);
    };
})();