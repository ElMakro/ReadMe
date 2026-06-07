// static/course_creation/blocks.js
(function() {
    const topicId = window.TOPIC_ID;
    const container = document.getElementById('blocksList');
    const addBtn = document.getElementById('addBlockBtn');

    let blocks = [];
    let originalBlocks = [];

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

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function validateLatexWithMathJax(latexString) {
        if (!window.MathJax) return true;
        if (!latexString || latexString.trim() === '') return true;
        try {
            await window.MathJax.tex2chtmlPromise(latexString, { display: true });
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
            if (ch === '"' && (i === 0 || umlCode[i-1] !== '\\')) {
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
        } else if (type === 'files') {
            return true;
        }
        return true;
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

    // Исправленная функция загрузки файла на сервер (без внутренних +1)
    async function uploadFileToServer(blockNumber, fileNumber, file) {
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
            } else if (resp.status === 404) {
                errorMsg = 'Блок или позиция файла не найдены';
            } else if (resp.status === 409) {
                errorMsg = 'Имя файла не совпадает с заявленным в теме';
            }
            throw new Error(errorMsg);
        }
        return await resp.json();
    }

    async function loadBlocks() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/${topicId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const topicData = await res.json();
            let rawBlocks = topicData.raw_content || [];
            blocks = rawBlocks.map(b => {
                let newBlock = { ...b };
                if (newBlock.raw_content !== undefined && newBlock.content === undefined) {
                    newBlock.content = newBlock.raw_content;
                    delete newBlock.raw_content;
                }
                if (newBlock.type === 'uml') newBlock.type = 'plantuml';
                if (newBlock.type === 'files' && !Array.isArray(newBlock.content)) {
                    newBlock.content = [];
                }
                return newBlock;
            });
            originalBlocks = JSON.parse(JSON.stringify(blocks));
            renderBlocks();
        } catch (err) {
            console.error(err);
            blocks = [];
            originalBlocks = [];
            renderBlocks();
            window.showToast('Ошибка загрузки блоков', 'danger');
        }
    }

    function renderBlocks() {
        container.innerHTML = '';
        blocks.forEach((block, idx) => {
            const card = document.createElement('div');
            card.className = 'list-group-item list-group-item-action border mb-2 rounded';
            card.setAttribute('data-block-idx', idx);
            card.style.cursor = 'pointer';

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
                card.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong>${escapeHtml(typeLabel)}</strong>
                            <div class="small text-muted">${escapeHtml(preview)}</div>
                        </div>
                        <span class="text-secondary edit-block-trigger" data-idx="${idx}" style="cursor: pointer;">✎ редактировать</span>
                    </div>
                `;
                const editTrigger = card.querySelector('.edit-block-trigger');
                editTrigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openEditMode(idx);
                });
                card.addEventListener('click', () => openEditMode(idx));
            } else {
                // Режим редактирования
                if (block.type === 'files') {
                    const files = block.content || [];
                    const hiddenFileInput = document.createElement('input');
                    hiddenFileInput.type = 'file';
                    hiddenFileInput.style.display = 'none';

                    card.innerHTML = `
                        <div class="p-2">
                            <div class="mb-3">
                                <label class="form-label">Тип блока</label>
                                <select class="form-select block-type-edit" data-idx="${idx}">
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
                                    <button class="btn btn-outline-secondary cancel-edit-btn me-2" data-idx="${idx}">Отмена</button>
                                    <button class="btn btn-accent save-edit-btn" data-idx="${idx}">Сохранить</button>
                                </div>
                            </div>
                        </div>
                    `;
                    card.appendChild(hiddenFileInput);

                    const typeSelect = card.querySelector('.block-type-edit');
                    const deleteBlockBtn = card.querySelector('.delete-block-btn');
                    const cancelBtn = card.querySelector('.cancel-edit-btn');
                    const saveBtn = card.querySelector('.save-edit-btn');
                    const addFileBtn = card.querySelector('.add-file-btn');

                    typeSelect.addEventListener('change', async (e) => {
                        const newType = e.target.value;
                        if (newType !== 'files') {
                            if (block.isNew) {
                                await saveAllBlocksToServer();
                                block.isNew = false;
                            }
                            block.type = newType;
                            block.content = [''];
                            block.isEditing = true;
                            renderBlocks();
                        }
                    });

                    // Удаление файла с сохранением на сервере
                    const removeButtons = card.querySelectorAll('.remove-file-btn');
                    removeButtons.forEach(btn => {
                        btn.addEventListener('click', async (e) => {
                            const fileIdx = parseInt(btn.dataset.fileIdx);
                            block.content.splice(fileIdx, 1);
                            await saveAllBlocksToServer();
                            renderBlocks();
                            window.showToast('Файл удалён', 'success');
                        });
                    });

                    // Добавление файла — двухэтапное сохранение
                    addFileBtn.addEventListener('click', async () => {
                        hiddenFileInput.click();
                    });

                    hiddenFileInput.addEventListener('change', async () => {
                        const file = hiddenFileInput.files[0];
                        if (!file) return;

                        addFileBtn.disabled = true;
                        addFileBtn.textContent = 'Загрузка...';

                        try {
                            // 1. Добавляем временную запись файла в локальный блок
                            if (!block.content) block.content = [];
                            const tempFileItem = {
                                original_filename: file.name,
                                server_filename: null
                            };
                            const newFileIndex = block.content.length;
                            block.content.push(tempFileItem);

                            // 2. Сохраняем блок на сервер (метаданные файла)
                            await saveAllBlocksToServer();
                            block.isNew = false;

                            // 3. Загружаем реальный файл (нумерация с 1)
                            const blockNumber = idx + 1;
                            const fileNumber = newFileIndex + 1;
                            const uploaded = await uploadFileToServer(blockNumber, fileNumber, file);

                            // 4. Обновляем запись о файле
                            block.content[newFileIndex] = uploaded;

                            // 5. Сохраняем блок ещё раз
                            await saveAllBlocksToServer();

                            renderBlocks();
                            window.showToast(`Файл "${uploaded.original_filename}" загружен`, 'success');
                        } catch (err) {
                            // Удаляем временную запись при ошибке
                            if (block.content.length > 0 && block.content[block.content.length-1].server_filename === null) {
                                block.content.pop();
                            }
                            window.showToast(err.message, 'danger');
                        } finally {
                            addFileBtn.disabled = false;
                            addFileBtn.textContent = '+ Добавить файл';
                            hiddenFileInput.value = '';
                        }
                    });

                    saveBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (saveBtn.disabled) return;
                        saveBtn.disabled = true;
                        try {
                            await saveAllBlocksToServer();
                            block.isNew = false;
                            block.isEditing = false;
                            renderBlocks();
                            window.showToast('Блок сохранён');
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
                    });

                    deleteBlockBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (confirm('Удалить этот блок?')) {
                            blocks.splice(idx, 1);
                            await saveAllBlocksToServer();
                            originalBlocks = JSON.parse(JSON.stringify(blocks));
                            renderBlocks();
                            window.showToast('Блок удалён');
                        }
                    });
                } else {
                    // Редактор для markdown / plantuml / latex
                    let currentRaw = '';
                    if (Array.isArray(block.content)) currentRaw = block.content[0] || '';
                    else currentRaw = block.content || '';
                    card.innerHTML = `
                        <div class="p-2">
                            <div class="mb-3">
                                <label class="form-label">Тип блока</label>
                                <select class="form-select block-type-edit" data-idx="${idx}">
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
                                    <button class="btn btn-outline-secondary cancel-edit-btn me-2" data-idx="${idx}">Отмена</button>
                                    <button class="btn btn-accent save-edit-btn" data-idx="${idx}">Сохранить</button>
                                </div>
                            </div>
                        </div>
                    `;
                    const typeSelect = card.querySelector('.block-type-edit');
                    const contentTextarea = card.querySelector('.block-content-edit');
                    const saveBtn = card.querySelector('.save-edit-btn');
                    const cancelBtn = card.querySelector('.cancel-edit-btn');
                    const deleteBtn = card.querySelector('.delete-block-btn');

                    if (contentTextarea) {
                        contentTextarea.addEventListener('input', function() { autosize(this, 800); });
                        setTimeout(() => autosize(contentTextarea, 800), 20);
                    }

                    typeSelect.addEventListener('change', async (e) => {
                        const newType = e.target.value;
                        if (newType === 'files') {
                            if (block.isNew) {
                                await saveAllBlocksToServer();
                                block.isNew = false;
                            }
                            block.type = newType;
                            block.content = [];
                            renderBlocks();
                        } else {
                            block.type = newType;
                            block.content = [''];
                            renderBlocks();
                        }
                    });

                    if (contentTextarea) {
                        contentTextarea.addEventListener('input', (e) => {
                            block.content = [e.target.value];
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
                            } else {
                                block.type = 'files';
                                if (!block.content) block.content = [];
                            }
                            await saveAllBlocksToServer();
                            block.isNew = false;
                            block.isEditing = false;
                            renderBlocks();
                            window.showToast('Блок сохранён');
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
                    });

                    deleteBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (confirm('Удалить этот блок?')) {
                            blocks.splice(idx, 1);
                            await saveAllBlocksToServer();
                            originalBlocks = JSON.parse(JSON.stringify(blocks));
                            renderBlocks();
                            window.showToast('Блок удалён');
                        }
                    });
                }
            }
            container.appendChild(card);
        });
    }

    function openEditMode(idx) {
        const editingIdx = blocks.findIndex(b => b.isEditing);
        if (editingIdx !== -1 && editingIdx !== idx) {
            if (confirm('Сначала завершите редактирование текущего блока?')) return;
        }
        blocks[idx].isEditing = true;
        renderBlocks();
    }

    async function saveAllBlocksToServer() {
        const payload = blocks.map(b => {
            if (b.type === 'files') {
                return { type: 'files', content: b.content || [] };
            } else {
                let rawArray = [];
                if (Array.isArray(b.content)) rawArray = b.content;
                else rawArray = [b.content || ''];
                return { type: b.type, content: rawArray };
            }
        });
        const updatePayload = { raw_content: payload };
        const res = await fetch(`${window.API_BASE_URL}topics/${topicId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(updatePayload)
        });
        if (!res.ok) {
            let errMsg = 'Ошибка сохранения';
            if (res.status === 400) {
                const errData = await res.json().catch(() => null);
                errMsg = errData?.detail || 'Ошибка компиляции контента';
            }
            throw new Error(errMsg);
        }
        originalBlocks = JSON.parse(JSON.stringify(blocks));
    }

    function addBlock() {
        blocks.push({
            type: 'markdown',
            content: [''],
            isEditing: true,
            isNew: true
        });
        renderBlocks();
    }

    addBtn.addEventListener('click', addBlock);

    window.addEventListener('beforeunload', (e) => {
        if (blocks.some(b => b.isEditing)) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    loadBlocks();
    if (typeof window.updateCourseBreadcrumb === 'function') window.updateCourseBreadcrumb(window.COURSE_ID);
    if (typeof window.updateSectionBreadcrumb === 'function') window.updateSectionBreadcrumb(window.SECTION_ID);
    if (typeof window.updateTopicBreadcrumb === 'function') window.updateTopicBreadcrumb(window.TOPIC_ID);
})();