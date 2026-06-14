// static/pagination.js
class Pagination {
    constructor(container, onPageChange, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;
        this.onPageChange = onPageChange;
        this.currentPage = options.currentPage || 1;
        this.totalPages = options.totalPages || 1;
        this.pageSize = options.pageSize || 9;
        this.autoHide = options.autoHide !== false;
        this.template = options.template || `
            <div class="pagination d-flex justify-content-center gap-2 mt-4">
                <button class="btn btn-outline-secondary pagination-prev">← Пред.</button>
                <span class="pagination-info mx-3 align-self-center">Страница ${this.currentPage} из ${this.totalPages}</span>
                <button class="btn btn-outline-secondary pagination-next">След. →</button>
            </div>
        `;

        this.element = null;
        this.init();
    }

    init() {
        if (!this.container) return;
        this.render();
        this.bindEvents();
        this.updateVisibility();
    }

    render() {
        this.element = document.createElement('div');
        this.element.innerHTML = this.template.trim();
        this.container.appendChild(this.element);

        this.prevBtn = this.element.querySelector('.pagination-prev');
        this.nextBtn = this.element.querySelector('.pagination-next');
        this.infoSpan = this.element.querySelector('.pagination-info');
    }

    bindEvents() {
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.setPage(this.currentPage - 1);
                }
            });
        }
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => {
                if (this.currentPage < this.totalPages) {
                    this.setPage(this.currentPage + 1);
                }
            });
        }
    }

    setPage(page, silent = false) {
        if (page < 1 || page > this.totalPages) return;
        if (this.currentPage === page) return;
        this.currentPage = page;
        this.updateUI();
        if (!silent && typeof this.onPageChange === 'function') {
            this.onPageChange(this.currentPage);
        }
    }

    setTotalPages(total) {
        this.totalPages = total;
        if (this.currentPage > this.totalPages) {
            this.currentPage = this.totalPages;
        }
        this.updateUI();
        this.updateVisibility();
    }

    updateUI() {
        if (this.infoSpan) {
            this.infoSpan.textContent = `Страница ${this.currentPage} из ${this.totalPages}`;
        }
        if (this.prevBtn) {
            this.prevBtn.disabled = this.currentPage <= 1;
        }
        if (this.nextBtn) {
            this.nextBtn.disabled = this.currentPage >= this.totalPages;
        }
    }

    updateVisibility() {
        if (!this.autoHide) return;
        if (this.totalPages <= 1) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        if (this.element) this.element.style.display = '';
    }

    hide() {
        if (this.element) this.element.style.display = 'none';
    }

    destroy() {
        if (this.element) this.element.remove();
        this.prevBtn = null;
        this.nextBtn = null;
        this.infoSpan = null;
        this.element = null;
    }
}

window.Pagination = Pagination;