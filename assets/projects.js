const filter = document.querySelector('.project-filter');
const buttons = [...filter.querySelectorAll('button[data-filter]')];
const groups = [...document.querySelectorAll('#project-list > [data-category]')];
const status = filter.querySelector('[role="status"]');

function showCategory(category) {
  let visible = 0;
  for (const group of groups) {
    group.hidden = category !== 'all' && group.dataset.category !== category;
    if (!group.hidden) visible += group.querySelectorAll('li').length;
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
