const filter = document.querySelector('.project-filter');
const buttons = [...filter.querySelectorAll('button[data-filter]')];
const list = document.querySelector('#project-list');
const status = filter.querySelector('[role="status"]');

function showCategory(category) {
  let visible = 0;
  for (const project of list.children) {
    project.hidden = category !== 'all' && project.dataset.category !== category;
    if (!project.hidden) visible += 1;
  }
  for (const button of buttons) {
    button.setAttribute('aria-pressed', String(button.dataset.filter === category));
  }
  status.textContent = `${visible} 个项目`;
}

for (const button of buttons) {
  button.addEventListener('click', () => showCategory(button.dataset.filter));
}
showCategory('all');
filter.hidden = false;
