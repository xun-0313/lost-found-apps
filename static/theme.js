document.addEventListener('DOMContentLoaded', () => {
  const html = document.documentElement;
  const toggleBtn = document.getElementById('theme-toggle');
  const savedTheme = localStorage.getItem('theme') || 'light';

  if (savedTheme === 'dark') {
    html.classList.add('dark');
    if (toggleBtn) toggleBtn.textContent = '🌞 淺色模式';
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      html.classList.toggle('dark');
      const isDark = html.classList.contains('dark');
      toggleBtn.textContent = isDark ? '🌞 淺色模式' : '🌙 深色模式';
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
  }
});