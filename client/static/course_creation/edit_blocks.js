// static/edit-blocks.js
(function() {
    const topicId = window.TOPIC_ID;
    const container = document.getElementById('blocksList');
    const addBtn = document.getElementById('addBlockBtn');
    const saveBtn = document.getElementById('saveBlocksBtn');

    let blocks = [];        // { id, title, block_type, content, isNew, isExpanded }
    let originalBlocks = [];
    let hasUnsaved = false;

    window.addEventListener('beforeunload', (e) => {
        if (hasUnsaved) e.preventDefault(), e.returnValue = '';
    });

    async function loadBlocks() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/${topicId}/blocks`, { credentials: 'include' });
            if (!res.ok) throw new Error();
            const data = await res.json();
            blocks = data.map(b => ({
                id: b.id,
                title: b.title,
                block_type: b.block_type || 'md',
                content: b.content || '',
                isNew: false,
                isExpanded: false
            }));
            originalBlocks = JSON.parse(JSON.stringify(blocks));
            renderBlocks();
            hasUnsaved = false;
        } catch {
            blocks = [];
            originalBlocks = [];
            renderBlocks();
        }
    }

    function renderBlocks() {
        container.innerHTML = '';
        blocks.forEach((block, idx) => {
            const card = document.createElement('div');
            card.className = 'card mb-3 bg-primary border';
            card.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center bg-secondary">
                    <div class="d-flex align-items-center gap-2 flex-grow-1">
                        <button class="btn btn-sm btn-outline-secondary toggle-expand" data-idx="${idx}">${block.isExpanded ? '−' : '+'}</button>
                        <input type="text" class="form-control form-control-sm block-title" value="${escapeHtml(block.title)}" placeholder="Название блока" data-idx="${idx}" style="width: 200px;">
                        <select class="form-select form-select-sm block-type" data-idx="${idx}" style="width: 120px;">
                            <option value="md" ${block.block_type === 'md' ? 'selected' : ''}>MD</option>
                            <option value="uml" ${block.block_type === 'uml' ? 'selected' : ''}>UML</option>
                            <option value="latex" ${block.block_type === 'latex' ? 'selected' : ''}>LaTeX</option>
                        </select>
                        <button class="btn btn-sm btn-outline-danger delete-block" data-idx="${idx}">🗑️</button>
                    </div>
                </div>
                <div class="card-body block-content" style="display: ${block.isExpanded ? 'block' : 'none'};">
                    <textarea class="form-control block-textarea" rows="5" data-idx="${idx}" placeholder="Содержимое блока...">${escapeHtml(block.content)}</textarea>
                </div>
            `;
            container.appendChild(card);
        });

        // Обработчики
        document.querySelectorAll('.block-title').forEach(inp => {
            inp.addEventListener('input', (e) => {
                const idx = parseInt(e.target.dataset.idx);
                blocks[idx].title = e.target.value;
                markUnsaved();
            });
        });
        document.querySelectorAll('.block-type').forEach(sel => {
            sel.addEventListener('change', (e) => {
                const idx = parseInt(e.target.dataset.idx);
                blocks[idx].block_type = e.target.value;
                markUnsaved();
            });
        });
        document.querySelectorAll('.block-textarea').forEach(ta => {
            ta.addEventListener('input', (e) => {
                const idx = parseInt(e.target.dataset.idx);
                blocks[idx].content = e.target.value;
                markUnsaved();
            });
        });
        document.querySelectorAll('.toggle-expand').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(btn.dataset.idx);
                blocks[idx].isExpanded = !blocks[idx].isExpanded;
                renderBlocks();
            });
        });
        document.querySelectorAll('.delete-block').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(btn.dataset.idx);
                blocks.splice(idx, 1);
                renderBlocks();
                markUnsaved();
            });
        });
    }

    function addBlock() {
        blocks.push({
            id: null,
            title: '',
            block_type: 'md',
            content: '',
            isNew: true,
            isExpanded: true
        });
        renderBlocks();
        markUnsaved();
    }

    addBtn.addEventListener('click', addBlock);

    function markUnsaved() {
        const currentCopy = blocks.map(b => ({
            id: b.id, title: b.title, block_type: b.block_type, content: b.content, isNew: b.isNew
        }));
        const origCopy = originalBlocks.map(b => ({
            id: b.id, title: b.title, block_type: b.block_type, content: b.content, isNew: b.isNew
        }));
        hasUnsaved = JSON.stringify(currentCopy) !== JSON.stringify(origCopy);
    }

    async function saveBlocks() {
        const newBlocks = blocks.filter(b => b.isNew && b.title.trim());
        const existing = blocks.filter(b => !b.isNew);
        saveBtn.disabled = true;
        try {
            for (const bl of newBlocks) {
                const res = await fetch(`${window.API_BASE_URL}topics/${topicId}/blocks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        title: bl.title,
                        block_type: bl.block_type,
                        content: bl.content
                    })
                });
                if (!res.ok) throw new Error();
                const data = await res.json();
                bl.id = data.id;
                bl.isNew = false;
            }
            for (const bl of existing) {
                const orig = originalBlocks.find(o => o.id === bl.id);
                if (orig && (orig.title !== bl.title || orig.block_type !== bl.block_type || orig.content !== bl.content)) {
                    await fetch(`${window.API_BASE_URL}blocks/${bl.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            title: bl.title,
                            block_type: bl.block_type,
                            content: bl.content
                        })
                    });
                }
            }
            await loadBlocks();
            alert('Блоки сохранены');
        } catch (err) {
            alert('Ошибка сохранения блоков');
        } finally {
            saveBtn.disabled = false;
        }
    }

    saveBtn.addEventListener('click', saveBlocks);

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadBlocks();
})();