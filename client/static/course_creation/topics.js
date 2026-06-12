// static/course_creation/topics.js
(function () {
    const courseId = window.COURSE_ID;
    const sectionId = window.SECTION_ID;
    const container = document.getElementById('topicsList');
    const addBtn = document.getElementById('addTopicBtn');
    const saveAllBtn = document.getElementById('saveAllBtn');

    const ICONS_BASE_PATH = '/static/images/';

    let topics = [];
    let originalTopics = [];

    let currentEditingTopicId = null;
    let currentEditingOriginalData = null;
    let hasUnsavedChanges = false;

    if (!window.tagManagerInstances) window.tagManagerInstances = new Map();

    function updateUnsavedFlag(unsaved) {
        hasUnsavedChanges = unsaved;
        const titleEl = document.querySelector('title');
        if (titleEl) {
            let baseTitle = titleEl.textContent.replace(/^\*\s*/, '');
            titleEl.textContent = unsaved ? `* ${baseTitle}` : baseTitle;
        }
    }

    async function confirmDiscardChanges() {
        if (!hasUnsavedChanges) return true;
        return confirm('Есть несохранённые изменения. Вы действительно хотите закрыть редактор? Все несохранённые изменения будут потеряны.');
    }

    async function closeCurrentEdit(force = false) {
        if (!currentEditingTopicId) return true;
        if (!force && hasUnsavedChanges) {
            if (!await confirmDiscardChanges()) return false;
        }
        const card = container.querySelector(`.list-group-item[data-topic-id="${currentEditingTopicId}"]`);
        if (card && card.classList.contains('in-edit-mode')) {
            renderTopics();
        }
        currentEditingTopicId = null;
        currentEditingOriginalData = null;
        updateUnsavedFlag(false);
        return true;
    }

    function setupNavigationGuard() {
        window.addEventListener('beforeunload', (e) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = 'Есть несохранённые изменения. Вы уверены, что хотите покинуть страницу?';
                return e.returnValue;
            }
        });

        document.body.addEventListener('click', async (e) => {
            let target = e.target.closest('a');
            if (!target) return;
            const href = target.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:')) return;
            if (hasUnsavedChanges) {
                e.preventDefault();
                const ok = await confirmDiscardChanges();
                if (ok) {
                    updateUnsavedFlag(false);
                    window.location.href = href;
                }
            }
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Функция для получения HTML с изображением SVG-иконки
    function getBlockIcon(type) {
        let fileName = '';
        switch (type) {
            case 'files':
                fileName = 'File.svg';
                break;
            case 'latex':
                fileName = 'LaTeX.svg';
                break;
            case 'markdown':
                fileName = 'Markdown.svg';
                break;
            case 'plantuml':
                fileName = 'UML.svg';
                break;
            default:
                fileName = 'Markdown.svg'; // иконка по умолчанию
        }
        // Возвращаем <img> с классом для стилизации
        return `<img src="${ICONS_BASE_PATH}${fileName}" class="block-icon-img" alt="${type} icon">`;
    }

    function truncateText(text, maxLength = 80) {
        if (!text) return '';
        if (typeof text !== 'string') {
            if (Array.isArray(text)) return `${text.length} файл(ов)`;
            return '';
        }
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    function autosize(textarea, maxHeight = 800) {
        if (!textarea) return;
        textarea.style.height = 'auto';
        const scrollHeight = textarea.scrollHeight;
        if (scrollHeight > maxHeight) {
            textarea.style.height = maxHeight + 'px';
            textarea.style.overflowY = 'auto';
        } else {
            textarea.style.height = scrollHeight + 'px';
            textarea.style.overflowY = 'hidden';
        }
    }

    async function validateLatexWithMathJax(latexString) {
        if (!window.MathJax) return true;
        if (!latexString || latexString.trim() === '') return true;
        try {
            await window.MathJax.tex2chtmlPromise(latexString, {display: true});
            return true;
        } catch (err) {
            let errorMsg = err.message || err.toString();
            if (errorMsg.includes('\n')) errorMsg = errorMsg.split('\n')[0];
            throw new Error(`LaTeX ошибка: ${errorMsg}`);
        }
    }

    function validatePlantUml(umlCode) {
        if (!umlCode || umlCode.trim() === '') return true;
        if (!umlCode.includes('@startuml')) {
            throw new Error('Диаграмма PlantUML должна начинаться с @startuml');
        }
        if (!umlCode.includes('@enduml')) {
            throw new Error('Диаграмма PlantUML должна заканчиваться @enduml');
        }
        let balance = 0;
        let inString = false;
        for (let i = 0; i < umlCode.length; i++) {
            const ch = umlCode[i];
            if (ch === '"' && (i === 0 || umlCode[i - 1] !== '\\')) {
                inString = !inString;
                continue;
            }
            if (inString) continue;
            if (ch === '{') balance++;
            else if (ch === '}') balance--;
            if (balance < 0) throw new Error('Незакрытая фигурная скобка }');
        }
        if (balance !== 0) throw new Error('Не все фигурные скобки закрыты');
        return true;
    }

    async function validateBlock(type, rawContent) {
        if (type === 'markdown') {
            if (typeof marked === 'undefined') return true;
            try {
                await marked.parse(rawContent || '');
                return true;
            } catch (err) {
                throw new Error(`Markdown ошибка: ${err.message}`);
            }
        } else if (type === 'plantuml') {
            return validatePlantUml(rawContent);
        } else if (type === 'latex') {
            if (rawContent) {
                let balance = 0;
                for (let ch of rawContent) {
                    if (ch === '{') balance++;
                    else if (ch === '}') balance--;
                    if (balance < 0) throw new Error('Незакрытая фигурная скобка }');
                }
                if (balance !== 0) throw new Error('Не закрыты все фигурные скобки');
            }
            return true;
        }
        return true;
    }

    async function uploadFileToServer(topicId, blockNumber, fileNumber, file) {
        const formData = new FormData();
        formData.append('resource', file);
        const url = `${window.API_BASE_URL}topics/upload-resource/${topicId}/${blockNumber}/${fileNumber}`;
        const resp = await fetch(url, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        if (!resp.ok) {
            let errorMsg = 'Ошибка загрузки файла';
            if (resp.status === 400) {
                const errData = await resp.json().catch(() => null);
                errorMsg = errData?.detail || 'Тип блока не поддерживает файлы';
            } else if (resp.status === 401 || resp.status === 403) {
                errorMsg = 'Доступ запрещён';
            } else if (resp.status === 404) {
                errorMsg = 'Блок или позиция файла не найдены';
            } else if (resp.status === 409) {
                errorMsg = 'Имя файла не совпадает с заявленным в теме';
            } else if (resp.status === 422) {
                errorMsg = 'Ошибка валидации';
            }
            throw new Error(errorMsg);
        }
        return await resp.json();
    }

    async function loadTopics() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/by-section/${sectionId}`, {
                credentials: 'include'
            });
            if (res.status === 401 || res.status === 403) {
                window.showAccessDenied(container, 'Вы не авторизованы или недостаточно прав для редактирования тем.');
                return;
            }
            if (!res.ok) {
                if (res.status === 404) throw new Error('Раздел не найден');
                if (res.status === 422) throw new Error('Ошибка валидации');
                throw new Error(`HTTP ${res.status}`);
            }
            const data = await res.json();
            let topicsArray = (data && Array.isArray(data.topics)) ? data.topics : (Array.isArray(data) ? data : []);
            topics = topicsArray.map(t => ({
                id: t.id,
                name: t.name,
                order_number: t.order_number,
                tags: t.tags || [],
                raw_content: t.raw_content || []
            }));
            topics.sort((a, b) => a.order_number - b.order_number);
            originalTopics = JSON.parse(JSON.stringify(topics));
            renderTopics();
            if (addBtn) addBtn.disabled = false;
            if (saveAllBtn) saveAllBtn.disabled = false;
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="text-danger">Ошибка загрузки тем: ${err.message}</div>`;
            topics = [];
            originalTopics = [];
            renderTopics();
            if (addBtn) addBtn.disabled = true;
            if (saveAllBtn) saveAllBtn.disabled = true;
        }
    }

    function renderTopics() {
        if (currentEditingTopicId) {
            currentEditingTopicId = null;
            currentEditingOriginalData = null;
            updateUnsavedFlag(false);
        }
        container.innerHTML = '';
        topics.forEach((topic) => {
            const card = document.createElement('div');
            card.className = 'list-group-item list-group-item-action border mb-2 rounded';
            card.style.cursor = 'pointer';
            card.setAttribute('data-topic-id', topic.id);

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${escapeHtml(topic.name)}</strong>
                        ${topic.tags && topic.tags.length ? `<div class="small text-muted mt-1">Теги: ${topic.tags.map(t => escapeHtml(t)).join(' ')}</div>` : ''}
                    </div>
                    <span class="text-secondary edit-topic-trigger" data-id="${topic.id}" style="cursor: pointer;">✎ редактировать</span>
                </div>
            `;

            const editTrigger = card.querySelector('.edit-topic-trigger');
            editTrigger.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (currentEditingTopicId && currentEditingTopicId !== topic.id) {
                    const closed = await closeCurrentEdit();
                    if (!closed) return;
                }
                openEditMode(topic);
            });

            container.appendChild(card);
        });
    }

    function openEditMode(topic) {
        if (currentEditingTopicId && currentEditingTopicId !== topic.id) {
            closeCurrentEdit(true);
        }

        currentEditingTopicId = topic.id;
        currentEditingOriginalData = {
            name: topic.name,
            tags: [...topic.tags],
            raw_content: JSON.parse(JSON.stringify(topic.raw_content))
        };
        updateUnsavedFlag(false);

        const card = container.querySelector(`.list-group-item[data-topic-id="${topic.id}"]`);
        if (!card) return;
        card.classList.add('in-edit-mode');
        card.style.cursor = 'default';

        const placeholderId = `tagsManagerPlaceholder-${topic.id || 'new'}`;
        const blocksContainerId = `blocksContainer-${topic.id || 'new'}`;

        card.innerHTML = `
            <div class="p-2">
                <div class="mb-3">
                    <label class="form-label">Название темы</label>
                    <input type="text" class="form-control topic-name-edit" value="${escapeHtml(topic.name)}" placeholder="Введите название темы">
                </div>
                <div class="mb-3">
                    <label class="form-label">Теги</label>
                    <div id="${placeholderId}"></div>
                </div>
                <hr>
                <div class="mb-3">
                    <label class="form-label fw-bold">Блоки темы</label>
                    <div id="${blocksContainerId}" class="mb-3"></div>
                    <button class="btn btn-sm btn-outline-accent add-block-btn">+ Добавить блок</button>
                </div>
                <div class="d-flex justify-content-between align-items-center mt-3">
                    <button class="btn btn-danger delete-topic">Удалить тему</button>
                    <div>
                        <button class="btn btn-outline-secondary cancel-edit me-2">Отмена</button>
                        <button class="btn btn-accent save-topic-edit">Сохранить тему</button>
                    </div>
                </div>
            </div>
        `;

        const placeholder = card.querySelector(`#${placeholderId}`);
        let tagManager = null;
        if (placeholder) {
            tagManager = window.initTagManager(placeholder, topic.tags);
            window.tagManagerInstances.set(placeholderId, tagManager);
        }

        const blocksContainer = card.querySelector(`#${blocksContainerId}`);
        let blocks = topic.raw_content ? JSON.parse(JSON.stringify(topic.raw_content)) : [];
        let originalBlocks = JSON.parse(JSON.stringify(blocks));
        card._blocks = blocks;

        function markUnsaved() {
            if (currentEditingTopicId !== topic.id) return;
            const nameInput = card.querySelector('.topic-name-edit');
            if (!nameInput) return;
            const newName = nameInput.value.trim();
            const nameChanged = newName !== currentEditingOriginalData.name;

            let newTags = tagManager ? tagManager.tags : topic.tags;
            const tagsChanged = JSON.stringify(newTags) !== JSON.stringify(currentEditingOriginalData.tags);

            let blocksChanged = false;
            if (blocks) {
                const blocksToCompare = blocks.map(b => {
                    if (b.type === 'files') return {type: 'files', content: b.content || []};
                    else {
                        let content = Array.isArray(b.content) ? b.content : [b.content || ''];
                        return {type: b.type, content};
                    }
                });
                blocksChanged = JSON.stringify(blocksToCompare) !== JSON.stringify(currentEditingOriginalData.raw_content);
            }
            updateUnsavedFlag(nameChanged || tagsChanged || blocksChanged);
        }

        const nameInput = card.querySelector('.topic-name-edit');
        nameInput.addEventListener('input', markUnsaved);

        if (tagManager) {
            const interval = setInterval(() => {
                if (tagManager && currentEditingTopicId === topic.id) markUnsaved();
                else clearInterval(interval);
            }, 500);
        }

        function renderBlocks() {
            if (!blocksContainer) return;
            blocksContainer.innerHTML = '';
            blocks.forEach((block, idx) => {
                const blockCard = document.createElement('div');
                blockCard.className = 'list-group-item list-group-item-action border mb-2 rounded';
                blockCard.style.cursor = 'pointer';

                if (!block.isEditing) {
                    const typeLabel = {
                        'markdown': 'Markdown',
                        'plantuml': 'UML',
                        'latex': 'LaTeX',
                        'files': 'Файлы'
                    }[block.type] || block.type;
                    let preview = '';
                    if (block.type === 'files') {
                        const files = block.content || [];
                        preview = files.length ? `${files.length} файл(ов)` : '(пустой блок)';
                    } else {
                        const raw = Array.isArray(block.content) ? block.content[0] : block.content;
                        preview = truncateText(raw, 100);
                    }
                    blockCard.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start p-2">
                            <div class="flex-grow-1">
                                <span class="block-icon">${getBlockIcon(block.type)}</span> <strong>${escapeHtml(typeLabel)}</strong>
                                <div class="small text-muted">${escapeHtml(preview)}</div>
                            </div>
                            <span class="text-secondary edit-block-trigger" data-idx="${idx}" style="cursor: pointer;">✎ редактировать</span>
                        </div>
                    `;
                    const editTrigger = blockCard.querySelector('.edit-block-trigger');
                    editTrigger.addEventListener('click', (e) => {
                        e.stopPropagation();
                        block.isEditing = true;
                        renderBlocks();
                    });
                } else {
                    if (block.type === 'files') {
                        const files = block.content || [];
                        const hiddenFileInput = document.createElement('input');
                        hiddenFileInput.type = 'file';
                        hiddenFileInput.style.display = 'none';

                        blockCard.innerHTML = `
                            <div class="p-2">
                                <div class="mb-3 d-flex align-items-center gap-2">
                                    <span class="block-icon">${getBlockIcon('files')}</span>
                                    <select class="form-select block-type-edit flex-grow-1" data-idx="${idx}">
                                        <option value="markdown">Markdown</option>
                                        <option value="plantuml">UML</option>
                                        <option value="latex">LaTeX</option>
                                        <option value="files" selected>Файлы</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Файлы</label>
                                    <div class="files-list mb-2">
                                        ${files.map((file, fIdx) => `
                                            <div class="file-item d-flex justify-content-between align-items-center mb-1 p-2 border rounded">
                                                <span>${escapeHtml(file.original_filename)}</span>
                                                <button type="button" class="btn btn-sm btn-outline-danger remove-file-btn" data-file-idx="${fIdx}">Удалить</button>
                                            </div>
                                        `).join('')}
                                    </div>
                                    <button class="btn btn-sm btn-outline-accent mt-2 add-file-btn">+ Добавить файл</button>
                                </div>
                                <div class="d-flex justify-content-between align-items-center mt-2">
                                    <button class="btn btn-danger delete-block-btn" data-idx="${idx}">Удалить блок</button>
                                    <div>
                                        <button class="btn btn-outline-secondary cancel-block-edit me-2" data-idx="${idx}">Отмена</button>
                                        <button class="btn btn-accent save-block-edit" data-idx="${idx}">Сохранить</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        blockCard.appendChild(hiddenFileInput);

                        const typeSelect = blockCard.querySelector('.block-type-edit');
                        const deleteBlockBtn = blockCard.querySelector('.delete-block-btn');
                        const cancelBtn = blockCard.querySelector('.cancel-block-edit');
                        const saveBtn = blockCard.querySelector('.save-block-edit');
                        const addFileBtn = blockCard.querySelector('.add-file-btn');

                        // Обновление иконки при смене типа
                        typeSelect.addEventListener('change', async (e) => {
                            const newType = e.target.value;
                            const iconSpan = blockCard.querySelector('.block-icon');
                            if (iconSpan) iconSpan.innerHTML = getBlockIcon(newType);
                            if (newType !== 'files') {
                                block.type = newType;
                                block.content = [''];
                                block.isEditing = true;
                                renderBlocks();
                                markUnsaved();
                            }
                        });

                        const removeButtons = blockCard.querySelectorAll('.remove-file-btn');
                        removeButtons.forEach(btn => {
                            btn.addEventListener('click', async (e) => {
                                const fileIdx = parseInt(btn.dataset.fileIdx);
                                block.content.splice(fileIdx, 1);
                                renderBlocks();
                                markUnsaved();
                                window.showToast('Файл удалён локально', 'info');
                            });
                        });

                        addFileBtn.addEventListener('click', async () => {
                            hiddenFileInput.click();
                        });

                        hiddenFileInput.addEventListener('change', async () => {
                            const file = hiddenFileInput.files[0];
                            if (!file) return;
                            addFileBtn.disabled = true;
                            addFileBtn.textContent = 'Загрузка...';
                            try {
                                if (!block.content) block.content = [];
                                block.content.push({
                                    original_filename: file.name,
                                    server_filename: null,
                                    _file: file
                                });
                                renderBlocks();
                                markUnsaved();
                                window.showToast(`Файл "${file.name}" будет загружен при сохранении темы`, 'info');
                            } catch (err) {
                                window.showToast(err.message, 'danger');
                            } finally {
                                addFileBtn.disabled = false;
                                addFileBtn.textContent = '+ Добавить файл';
                                hiddenFileInput.value = '';
                            }
                        });

                        saveBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            block.isEditing = false;
                            renderBlocks();
                            markUnsaved();
                            window.showToast('Изменения блока сохранены локально', 'info');
                        });

                        cancelBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const orig = originalBlocks[idx];
                            if (orig) {
                                block.type = orig.type;
                                block.content = orig.content;
                            }
                            block.isEditing = false;
                            renderBlocks();
                            markUnsaved();
                        });

                        deleteBlockBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            if (confirm('Удалить этот блок?')) {
                                blocks.splice(idx, 1);
                                renderBlocks();
                                markUnsaved();
                                window.showToast('Блок удалён локально', 'info');
                            }
                        });
                    } else {
                        let currentRaw = '';
                        if (Array.isArray(block.content)) currentRaw = block.content[0] || '';
                        else currentRaw = block.content || '';
                        blockCard.innerHTML = `
                            <div class="p-2">
                                <div class="mb-3 d-flex align-items-center gap-2">
                                    <span class="block-icon" id="type-icon-${idx}">${getBlockIcon(block.type)}</span>
                                    <select class="form-select block-type-edit flex-grow-1" data-idx="${idx}">
                                        <option value="markdown" ${block.type === 'markdown' ? 'selected' : ''}>Markdown</option>
                                        <option value="plantuml" ${block.type === 'plantuml' ? 'selected' : ''}>UML</option>
                                        <option value="latex" ${block.type === 'latex' ? 'selected' : ''}>LaTeX</option>
                                        <option value="files" ${block.type === 'files' ? 'selected' : ''}>Файлы</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Содержимое</label>
                                    <textarea class="form-control block-content-edit" data-idx="${idx}" placeholder="Введите содержимое блока">${escapeHtml(currentRaw)}</textarea>
                                </div>
                                <div class="d-flex justify-content-between align-items-center">
                                    <button class="btn btn-danger delete-block-btn" data-idx="${idx}">Удалить блок</button>
                                    <div>
                                        <button class="btn btn-outline-secondary cancel-block-edit me-2" data-idx="${idx}">Отмена</button>
                                        <button class="btn btn-accent save-block-edit" data-idx="${idx}">Сохранить</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        const typeSelect = blockCard.querySelector('.block-type-edit');
                        const contentTextarea = blockCard.querySelector('.block-content-edit');
                        const saveBtn = blockCard.querySelector('.save-block-edit');
                        const cancelBtn = blockCard.querySelector('.cancel-block-edit');
                        const deleteBtn = blockCard.querySelector('.delete-block-btn');

                        if (contentTextarea) {
                            contentTextarea.addEventListener('input', function () {
                                autosize(this, 800);
                            });
                            setTimeout(() => autosize(contentTextarea, 800), 20);
                        }

                        // Обновление иконки при смене типа
                        typeSelect.addEventListener('change', async (e) => {
                            const newType = e.target.value;
                            const iconSpan = blockCard.querySelector(`#type-icon-${idx}`);
                            if (iconSpan) iconSpan.innerHTML = getBlockIcon(newType);
                            if (newType === 'files') {
                                block.type = newType;
                                block.content = [];
                                renderBlocks();
                                markUnsaved();
                            } else {
                                const currentValue = contentTextarea ? contentTextarea.value : (Array.isArray(block.content) ? block.content[0] || '' : block.content || '');
                                block.type = newType;
                                block.content = [currentValue];
                                renderBlocks();
                                markUnsaved();
                            }
                        });

                        if (contentTextarea) {
                            contentTextarea.addEventListener('input', (e) => {
                                block.content = [e.target.value];
                                markUnsaved();
                            });
                        }

                        saveBtn.addEventListener('click', async (e) => {
                            e.stopPropagation();
                            if (saveBtn.disabled) return;
                            saveBtn.disabled = true;
                            try {
                                const newType = typeSelect.value;
                                let rawValue = contentTextarea.value;
                                if (newType !== 'files') {
                                    await validateBlock(newType, rawValue);
                                    block.type = newType;
                                    block.content = [rawValue];
                                }
                                block.isEditing = false;
                                renderBlocks();
                                markUnsaved();
                                window.showToast('Изменения сохранены локально', 'info');
                            } catch (err) {
                                window.showToast(err.message, 'danger');
                            } finally {
                                saveBtn.disabled = false;
                            }
                        });

                        cancelBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const orig = originalBlocks[idx];
                            if (orig) {
                                block.type = orig.type;
                                block.content = orig.content;
                            }
                            block.isEditing = false;
                            renderBlocks();
                            markUnsaved();
                        });

                        deleteBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            if (confirm('Удалить этот блок?')) {
                                blocks.splice(idx, 1);
                                renderBlocks();
                                markUnsaved();
                                window.showToast('Блок удалён локально', 'info');
                            }
                        });
                    }
                }
                blocksContainer.appendChild(blockCard);
            });
        }

        function addBlock() {
            blocks.push({
                type: 'markdown',
                content: [''],
                isEditing: true
            });
            renderBlocks();
            markUnsaved();
        }

        const addBlockBtn = card.querySelector('.add-block-btn');
        addBlockBtn.addEventListener('click', addBlock);
        renderBlocks();

        const saveBtn = card.querySelector('.save-topic-edit');
        const cancelBtn = card.querySelector('.cancel-edit');
        const delBtn = card.querySelector('.delete-topic');

        saveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const newName = nameInput.value.trim();
            if (!newName) {
                window.showToast('Название темы не может быть пустым', 'danger');
                return;
            }
            const newTags = tagManager ? tagManager.tags : topic.tags;
            const rawContentForFirstPut = blocks.map(b => {
                if (b.type === 'files') {
                    return {type: 'files', content: b.content || []};
                } else {
                    let arr = Array.isArray(b.content) ? b.content : [b.content || ''];
                    return {type: b.type, content: arr};
                }
            });

            const performSave = async () => {
                let savedTopicId = topic.id;
                if (topic.id) {
                    const res = await fetch(`${window.API_BASE_URL}topics/${topic.id}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        credentials: 'include',
                        body: JSON.stringify({name: newName, tags: newTags, raw_content: rawContentForFirstPut})
                    });
                    if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                    if (!res.ok) {
                        let errorMsg = 'Ошибка обновления темы';
                        if (res.status === 404) errorMsg = 'Тема не найдена';
                        else if (res.status === 409) errorMsg = 'Тема с таким порядковым номером уже существует';
                        else if (res.status === 400) {
                            const errData = await res.json().catch(() => null);
                            // FIX: преобразуем массив ошибок в читаемую строку
                            if (errData && Array.isArray(errData)) {
                                errorMsg = errData.map(e => `Блок ${e.block_index}: ${e.error}`).join('; ');
                            } else if (errData?.detail) {
                                errorMsg = errData.detail;
                            } else {
                                errorMsg = 'Ошибка компиляции контента';
                            }
                        } else if (res.status === 422) errorMsg = 'Ошибка валидации данных';
                        throw new Error(errorMsg);
                    }
                    savedTopicId = topic.id;
                } else {
                    const res = await fetch(`${window.API_BASE_URL}topics/create-topic`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        credentials: 'include',
                        body: JSON.stringify({
                            name: newName,
                            order_number: topic.order_number,
                            section_id: sectionId,
                            tags: newTags,
                            raw_content: rawContentForFirstPut
                        })
                    });
                    if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                    if (!res.ok) {
                        let errorMsg = 'Ошибка создания темы';
                        if (res.status === 404) errorMsg = 'Раздел не найден';
                        else if (res.status === 409) errorMsg = 'Тема с таким порядковым номером уже существует';
                        else if (res.status === 400) {
                            const errData = await res.json().catch(() => null);
                            // FIX: преобразуем массив ошибок в читаемую строку
                            if (errData && Array.isArray(errData)) {
                                errorMsg = errData.map(e => `Блок ${e.block_index}: ${e.error}`).join('; ');
                            } else if (errData?.detail) {
                                errorMsg = errData.detail;
                            } else {
                                errorMsg = 'Ошибка компиляции контента';
                            }
                        } else if (res.status === 422) errorMsg = 'Ошибка валидации данных';
                        throw new Error(errorMsg);
                    }
                    const data = await res.json();
                    savedTopicId = data.id;
                    topic.id = savedTopicId;
                }

                let filesUploaded = false;
                const blocksWithFiles = blocks.map((b, idx) => ({block: b, blockIdx: idx}));
                for (const {block, blockIdx} of blocksWithFiles) {
                    if (block.type === 'files' && block.content) {
                        for (let fileIdx = 0; fileIdx < block.content.length; fileIdx++) {
                            const fileItem = block.content[fileIdx];
                            if (fileItem._file) {
                                filesUploaded = true;
                                try {
                                    const uploaded = await uploadFileToServer(savedTopicId, blockIdx + 1, fileIdx + 1, fileItem._file);
                                    block.content[fileIdx] = uploaded;
                                    delete fileItem._file;
                                    window.showToast(`Файл "${uploaded.original_filename}" загружен`, 'success');
                                } catch (err) {
                                    window.showToast(`Ошибка загрузки файла ${fileItem.original_filename}: ${err.message}`, 'danger');
                                }
                            }
                        }
                    }
                }

                if (filesUploaded) {
                    const finalRawContent = blocks.map(b => {
                        if (b.type === 'files') return {type: 'files', content: b.content || []};
                        else {
                            let arr = Array.isArray(b.content) ? b.content : [b.content || ''];
                            return {type: b.type, content: arr};
                        }
                    });
                    await fetch(`${window.API_BASE_URL}topics/${savedTopicId}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        credentials: 'include',
                        body: JSON.stringify({raw_content: finalRawContent})
                    });
                    // FIX: обновляем локальный topic.raw_content после загрузки файлов
                    topic.raw_content = finalRawContent;
                } else {
                    topic.raw_content = rawContentForFirstPut;
                }

                topic.name = newName;
                topic.tags = newTags;

                const origIndex = originalTopics.findIndex(t => t.id === topic.id);
                if (origIndex !== -1) originalTopics[origIndex] = JSON.parse(JSON.stringify(topic));
                else originalTopics.push(JSON.parse(JSON.stringify(topic)));

                currentEditingTopicId = null;
                currentEditingOriginalData = null;
                updateUnsavedFlag(false);
                renderTopics();
                window.showToast(topic.id ? 'Тема обновлена' : 'Тема создана');
            };

            saveBtn.disabled = true;
            saveBtn.textContent = 'Сохранение...';

            try {
                await performSave();
            } catch (err) {
                if (err.message === 'unauthorized') {
                    window.Auth.retryAfterLogin(performSave);
                } else {
                    window.showToast(err.message, 'danger');
                }
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Сохранить тему';
            }
        });

        cancelBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (hasUnsavedChanges && !await confirmDiscardChanges()) return;
            await closeCurrentEdit(true);
        });

        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (hasUnsavedChanges && !await confirmDiscardChanges()) return;
            if (!topic.id) {
                const idx = topics.findIndex(t => t.id === null && t === topic);
                if (idx !== -1) topics.splice(idx, 1);
                renderTopics();
                return;
            }
            if (!confirm('Удалить тему? Все блоки и загруженные файлы будут удалены.')) return;

            const performDelete = async () => {
                const res = await fetch(`${window.API_BASE_URL}topics/${topic.id}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                if (res.status === 401 || res.status === 403) throw new Error('unauthorized');
                if (!res.ok) {
                    if (res.status === 404) throw new Error('Тема не найдена');
                    throw new Error('Ошибка удаления');
                }
                const idx = topics.findIndex(t => t.id === topic.id);
                if (idx !== -1) topics.splice(idx, 1);
                originalTopics = originalTopics.filter(t => t.id !== topic.id);
                renderTopics();
                window.showToast('Тема удалена');
            };

            try {
                await performDelete();
            } catch (err) {
                if (err.message === 'unauthorized') {
                    window.Auth.retryAfterLogin(performDelete);
                } else {
                    window.showToast(err.message, 'danger');
                }
            }
        });
    }

    function addTopic() {
        if (currentEditingTopicId) {
            closeCurrentEdit().then(closed => {
                if (closed) doAddTopic();
            });
        } else {
            doAddTopic();
        }
    }

    function doAddTopic() {
        const newOrder = topics.length + 1;
        const newTopic = {
            id: null,
            name: '',
            order_number: newOrder,
            tags: [],
            raw_content: []
        };
        topics.push(newTopic);
        renderTopics();
        setTimeout(() => {
            const newCard = container.querySelector(`.list-group-item:last-child`);
            const editTrigger = newCard?.querySelector('.edit-topic-trigger');
            if (editTrigger) editTrigger.click();
        }, 50);
    }

    addBtn.addEventListener('click', addTopic);
    if (saveAllBtn) saveAllBtn.style.display = 'none';
    loadTopics();
    setupNavigationGuard();

    if (typeof window.updateCourseBreadcrumb === 'function') window.updateCourseBreadcrumb(window.COURSE_ID);
    if (typeof window.updateSectionBreadcrumb === 'function') window.updateSectionBreadcrumb(window.SECTION_ID);
})();