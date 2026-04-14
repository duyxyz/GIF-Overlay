document.addEventListener('DOMContentLoaded', () => {
    initTheme();
});

function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    let isDark;

    if (savedTheme) {
        isDark = savedTheme === 'dark';
    } else {
        isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    document.documentElement.classList.toggle('dark-mode', isDark);
    updateThemeIcon(isDark);
}

function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
    const sun = document.querySelector('.sun-icon');
    const moon = document.querySelector('.moon-icon');
    if (sun) sun.style.display = isDark ? 'none' : 'block';
    if (moon) moon.style.display = isDark ? 'block' : 'none';
}

// Attach event listener (an toàn hơn onclick inline)
document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }
});