function setLandingLanguage(lang) {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const value = I18N[lang][el.dataset.i18n];
    if (value) el.textContent = value;
  });
  document.getElementById('langText').textContent = I18N[lang].lang_code;
  try { localStorage.setItem('sage_lang', lang); } catch {}
}
function applyLandingTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.querySelector('.icon-moon').style.display = theme === 'dark' ? 'none' : 'inline-block';
  document.querySelector('.icon-sun').style.display = theme === 'dark' ? 'inline-block' : 'none';
  try { localStorage.setItem('sage_theme', theme); } catch {}
}
let language = 'tr';
let theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
try { language = localStorage.getItem('sage_lang') === 'en' ? 'en' : 'tr'; theme = localStorage.getItem('sage_theme') || theme; } catch {}
setLandingLanguage(language);
applyLandingTheme(theme);
document.getElementById('btnLang').addEventListener('click', () => setLandingLanguage(document.documentElement.lang === 'tr' ? 'en' : 'tr'));
document.getElementById('btnThemeToggle').addEventListener('click', () => applyLandingTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
