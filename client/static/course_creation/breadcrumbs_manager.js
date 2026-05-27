// static/course_creation/api_helpers.js
(function() {
    const API_BASE_URL = window.API_BASE_URL || '';

    async function fetchJson(url, fallback = null) {
        try {
            const res = await fetch(url, { credentials: 'include' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.warn(`Fetch error: ${url}`, err);
            return fallback;
        }
    }

    // ----- Основные геттеры -----
    window.getCourseName = async (courseId) => {
        if (!courseId) return null;
        const course = await fetchJson(`${API_BASE_URL}courses/${courseId}`);
        return course?.name || null;
    };

    window.getSectionName = async (sectionId) => {
        if (!sectionId) return null;
        const section = await fetchJson(`${API_BASE_URL}sections/${sectionId}`);
        return section?.name || null;
    };

    window.getTopicName = async (topicId) => {
        if (!topicId) return null;
        const topic = await fetchJson(`${API_BASE_URL}topics/${topicId}`);
        return topic?.name || null;
    };

    // ----- Функции для обновления хлебных крошек (опционально, на основе геттеров) -----
    window.updateCourseBreadcrumb = async (courseId) => {
        const name = await window.getCourseName(courseId);
        const el = document.getElementById('courseTitleBreadcrumb');
        if (!el) return;
        const link = el.querySelector('a');
        if (link) link.textContent = name || 'Курс';
        else el.textContent = name || 'Курс';
    };

    window.updateSectionBreadcrumb = async (sectionId) => {
        const name = await window.getSectionName(sectionId);
        const el = document.getElementById('sectionTitleBreadcrumb');
        if (!el) return;
        const link = el.querySelector('a');
        if (link) link.textContent = name || 'Раздел';
        else el.textContent = name || 'Раздел';
    };

    window.updateTopicBreadcrumb = async (topicId) => {
        const name = await window.getTopicName(topicId);
        const el = document.getElementById('topicTitleBreadcrumb');
        if (!el) return;
        const link = el.querySelector('a');
        if (link) link.textContent = name || 'Тема';
        else el.textContent = name || 'Тема';
    };
})();
