(function() {
    // ========== ДЕМО-КНОПКИ (фильтры, пагинация) ==========
    function showFiltersAlert() { alert('Фильтры курсов (демо)'); }
    function showPrevPageAlert() { alert('Предыдущая страница (демо)'); }
    function showNextPageAlert() { alert('Следующая страница (демо)'); }

    const filtersBtn = document.getElementById('filtersBtn');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (filtersBtn) filtersBtn.addEventListener('click', showFiltersAlert);
    if (prevBtn) prevBtn.addEventListener('click', showPrevPageAlert);
    if (nextBtn) nextBtn.addEventListener('click', showNextPageAlert);

    // ========== ПОИСК ПО КУРСАМ ==========
    const searchInput = document.getElementById('searchInput');
    const courseCards = document.querySelectorAll('.course-card');

    function filterCourses(query) {
        courseCards.forEach(function(card) {
            const titleElem = card.querySelector('.course-number');
            if (titleElem) {
                const title = titleElem.textContent.toLowerCase();
                const parentCol = card.closest('.col');
                if (query === '' || title.includes(query)) {
                    parentCol.style.display = '';
                } else {
                    parentCol.style.display = 'none';
                }
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', function(event) {
            const query = event.target.value.toLowerCase().trim();
            filterCourses(query);
        });
    }
})();