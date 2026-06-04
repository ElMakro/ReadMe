// static/course_creation/blocks.js
(function() {
    const topicId = window.TOPIC_ID;
    const container = document.getElementById('blocksList');
    const addBtn = document.getElementById('addBlockBtn');

    let blocks = [];
    let originalBlocks = [];

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Проверка LaTeX формулы через MathJax
    async function validateLatexWithMathJax(latexString) {
        if (!window.MathJax) {
            console.warn('MathJax not loaded, skipping LaTeX validation');
            return true;
        }
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
        } else if (type === 'uml') {
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

    function truncateText(text, maxLength = 80) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    async function loadBlocks() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/${topicId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const topicData = await res.json();
            blocks = topicData.raw_content || [];
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
                    'uml': 'UML',
                    'latex': 'LaTeX'
                }[block.type] || block.type;
                const preview = truncateText(block.raw_content, 100);
                card.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong>${escapeHtml(typeLabel)}</strong>
                            <div class="small text-muted">${escapeHtml(preview) || '(пустой блок)'}</div>
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
                card.innerHTML = `
                    <div class="p-2">
                        <div class="mb-3">
                            <label class="form-label">Тип блока</label>
                            <select class="form-select block-type-edit" data-idx="${idx}">
                                <option value="markdown" ${block.type === 'markdown' ? 'selected' : ''}>Markdown</option>
                                <option value="uml" ${block.type === 'uml' ? 'selected' : ''}>UML</option>
                                <option value="latex" ${block.type === 'latex' ? 'selected' : ''}>LaTeX</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Содержимое</label>
                            <textarea class="form-control block-content-edit" rows="6" data-idx="${idx}">${escapeHtml(block.raw_content)}</textarea>
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

                typeSelect.addEventListener('change', (e) => {
                    block.type = e.target.value;
                });
                contentTextarea.addEventListener('input', (e) => {
                    block.raw_content = e.target.value;
                });
                saveBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (saveBtn.disabled) return;
                    saveBtn.disabled = true;
                    try {
                        const newType = typeSelect.value;
                        const newRaw = contentTextarea.value;
                        await validateBlock(newType, newRaw);
                        block.type = newType;
                        block.raw_content = newRaw;
                        await saveAllBlocksToServer();
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
                        block.raw_content = orig.raw_content;
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
        const payload = blocks.map(b => ({ type: b.type, raw_content: b.raw_content }));
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
            raw_content: '',
            isEditing: true
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
    window.updateCourseBreadcrumb(window.COURSE_ID);
    window.updateSectionBreadcrumb(window.SECTION_ID);
    window.updateTopicBreadcrumb(window.TOPIC_ID);
})();