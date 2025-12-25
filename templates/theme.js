const toggleBtn = document.getElementById('theme-toggle');
const body = document.body;

// 初始化主題
if (localStorage.getItem('theme') === 'dark') {
  body.classList.add('dark');
  toggleBtn.textContent = '🌞 淺色模式';
}

toggleBtn.addEventListener('click', () => {
  body.classList.toggle('dark');
  const isDark = body.classList.contains('dark');
  toggleBtn.textContent = isDark ? '🌞 淺色模式' : '🌙 深色模式';
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
});