(() => {
  const year = new Date().getFullYear();
  document.querySelectorAll("[data-year]").forEach(node => { node.textContent = year; });
  const content = window.SITE_CONTENT;
  if (content) {
    document.querySelectorAll("[data-site-name]").forEach(node => { node.textContent = content.name; });
    document.querySelectorAll("[data-site-intro]").forEach(node => { node.textContent = content.intro; });
    document.querySelectorAll("[data-film-title]").forEach(node => { node.textContent = content.film.title; });
    document.querySelectorAll("[data-film-description]").forEach(node => { node.textContent = content.film.description; });
  }
})();
