(function() {
    const topicId = window.TOPIC_ID;
    const container = document.getElementById('blocksList');
    const addBtn = document.getElementById('addBlockBtn');
    const saveBtn = document.getElementById('saveBlocksBtn');

    let blocks = [];
    let originalBlocks = [];
    let hasUnsaved = false;

    window.addEventListener('beforeunload', (e) => {
        if (hasUnsaved) e.preventDefault(), e.returnValue = '';
    });

    async function loadBlocks() {
        try {
            const res = await fetch(`${window.API_BASE_URL}topics/get-raw-content/${topicId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error();
            const data = await res.json();
            blocks = (data && Array.isArray(data.blocks)) ? data.blocks.map(b => ({
                type: b.type,
                raw_content: b.raw_content,
                isExpanded: true
            })) : [];
            originalBlocks = JSON.parse(JSON.stringify(blocks));
            renderBlocks();
            hasUnsaved = false;
        } catch (err) {
            console.error(err);
            blocks = [];
            originalBlocks = [];
            renderBlocks();
        }
    }

    function renderBlocks() {
        container.innerHTML = '';
        blocks.forEach((block, idx) => {
            const card = document.createElement('div');
            card.className = 'card mb-3 bg-secondary border-0 shadow-sm';
            card.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center bg-secondary">
                    <div class="d-flex align-items-center gap-2 flex-grow-1">
                        <button class="btn btn-sm btn-outline-secondary toggle-expand" data-idx="${idx}">${block.isExpanded ? '−' : '+'}</button>
                        <select class="form-select form-select-sm block-type" data-idx="${idx}" style="width: 120px;">
                            <option value="markdown" ${block.type === 'markdown' ? 'selected' : ''}>Markdown</option>
                            <option value="uml" ${block.type === 'uml' ? 'selected' : ''}>UML</option>
                            <option value="latex" ${block.type === 'latex' ? 'selected' : ''}>LaTeX</option>
                        </select>
                        <button class="btn btn-sm btn-outline-danger delete-block" data-idx="${idx}">🗑️</button>
                    </div>
                </div>
                <div class="card-body block-content" style="display: ${block.isExpanded ? 'block' : 'none'};">
                    <textarea class="form-control block-textarea" rows="6" data-idx="${idx}" placeholder="Содержимое блока...">${escapeHtml(block.raw_content)}</textarea>
                </div>
            `;
            container.appendChild(card);
        });
        attachEvents();
//        window.initAutoResize(container);
    }

    function attachEvents() {
        document.querySelectorAll('.block-type').forEach(sel => {
            sel.removeEventListener('change', handleTypeChange);
            sel.addEventListener('change', handleTypeChange);
        });
        document.querySelectorAll('.block-textarea').forEach(ta => {
            ta.removeEventListener('input', handleContentChange);
            ta.addEventListener('input', handleContentChange);
        });
        document.querySelectorAll('.toggle-expand').forEach(btn => {
            btn.removeEventListener('click', handleToggle);
            btn.addEventListener('click', handleToggle);
        });
        document.querySelectorAll('.delete-block').forEach(btn => {
            btn.removeEventListener('click', handleDelete);
            btn.addEventListener('click', handleDelete);
        });
    }

    function handleTypeChange(e) {
        const idx = parseInt(e.target.dataset.idx);
        blocks[idx].type = e.target.value;
        markUnsaved();
    }

    function handleContentChange(e) {
        const idx = parseInt(e.target.dataset.idx);
        blocks[idx].raw_content = e.target.value;
        markUnsaved();
    }

    function handleToggle(e) {
        const idx = parseInt(e.target.dataset.idx);
        blocks[idx].isExpanded = !blocks[idx].isExpanded;
        renderBlocks();
    }

    function handleDelete(e) {
        const idx = parseInt(e.target.dataset.idx);
        blocks.splice(idx, 1);
        renderBlocks();
        markUnsaved();
    }

    function addBlock() {
        blocks.push({
            type: 'markdown',
            raw_content: '',
            isExpanded: true
        });
        renderBlocks();
        markUnsaved();
    }

    addBtn.addEventListener('click', addBlock);

    function markUnsaved() {
        const currentData = blocks.map(b => ({ type: b.type, raw_content: b.raw_content }));
        const originalData = originalBlocks.map(b => ({ type: b.type, raw_content: b.raw_content }));
        hasUnsaved = JSON.stringify(currentData) !== JSON.stringify(originalData);
    }

    async function saveBlocks() {
        saveBtn.disabled = true;
        try {
            const payload = { blocks: blocks.map(b => ({ type: b.type, raw_content: b.raw_content })) };
            const res = await fetch(`${window.API_BASE_URL}topics/put-content/${topicId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error('Ошибка сохранения контента');
            await loadBlocks();
            alert('Блоки сохранены');
        } catch (err) {
            alert(err.message);
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
    window.updateCourseBreadcrumb(window.COURSE_ID);
    window.updateSectionBreadcrumb(window.SECTION_ID);
    window.updateTopicBreadcrumb(window.TOPIC_ID);
})();