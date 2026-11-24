const filter = document.querySelector('.project-filter');
const buttons = [...filter.querySelectorAll('button[data-filter]')];
const projects = [...document.querySelectorAll('#project-list > li')];
const count = filter.querySelector('.project-count');

function showCategory(category) {
  let visible = 0;
  for (const project of projects) {
    const matches = category === 'all' || project.dataset.category === category;
    project.hidden = !matches;
    if (matches) visible += 1;
  }
  for (const button of buttons) {
    button.setAttribute('aria-pressed', String(button.dataset.filter === category));
  }
  count.textContent = `${visible} 个项目`;
}

for (const button of buttons) {
  button.addEventListener('click', () => showCategory(button.dataset.filter));
}
showCategory('all');
filter.hidden = false;
