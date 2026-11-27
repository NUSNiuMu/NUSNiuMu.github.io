// Project pages: table-of-contents scrollspy and an image lightbox.

// ---- Scrollspy ----
const toc = document.querySelector('.toc');
if (toc) {
  const links = [...toc.querySelectorAll('a[href^="#"]')];
  const setCurrent = (active) => {
    for (const link of links) {
      link.classList.toggle('target-current', link === active);
      if (link === active) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    }
  };

  if (CSS.supports('scroll-target-group: auto')) {
    // Native :target-current styles the link; mirror it to aria-current for assistive tech.
    const sync = () => setCurrent(toc.querySelector('a:target-current'));
    sync();
    // scrollend is not fired everywhere for programmatic jumps; debounce scroll as well.
    let timer;
    document.addEventListener('scroll', () => { clearTimeout(timer); timer = setTimeout(sync, 150); }, { passive: true });
    document.addEventListener('scrollend', sync);
  } else {
    const byId = new Map(links.map((link) => [decodeURIComponent(link.hash.slice(1)), link]));
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) setCurrent(byId.get(entry.target.id));
      }
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
    for (const id of byId.keys()) {
      const section = document.getElementById(id);
      if (section) observer.observe(section);
    }
  }
}

// ---- Lightbox for figure images that link to their full-size file ----
const imageLinks = [...document.querySelectorAll('a.screenshot-link')].filter((a) =>
  /\.(webp|png|jpe?g|gif|svg)$/i.test(new URL(a.href).pathname) && a.querySelector('img'));

if (imageLinks.length && 'showModal' in HTMLDialogElement.prototype) {
  const dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.setAttribute('closedby', 'any');
  dialog.setAttribute('aria-labelledby', 'lightbox-title');
  dialog.innerHTML = `
    <div class="lightbox-bar">
      <h1 id="lightbox-title" class="lightbox-title"></h1>
      <a class="lightbox-open" target="_blank" rel="noopener">原图</a>
      <form method="dialog"><button class="lightbox-close" autofocus>关闭</button></form>
    </div>
    <img class="lightbox-image" alt="">`;
  document.body.append(dialog);
  const title = dialog.querySelector('.lightbox-title');
  const image = dialog.querySelector('.lightbox-image');
  const open = dialog.querySelector('.lightbox-open');

  // Light-dismiss fallback where <dialog closedby> is unsupported (Safari).
  if (!('closedBy' in HTMLDialogElement.prototype)) {
    const outside = (e) => {
      const r = image.getBoundingClientRect();
      const bar = dialog.querySelector('.lightbox-bar').getBoundingClientRect();
      const inRect = (rect) => e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom;
      return !inRect(r) && !inRect(bar);
    };
    let pressedOutside = false;
    dialog.addEventListener('pointerdown', (e) => { pressedOutside = outside(e); });
    dialog.addEventListener('pointerup', (e) => { if (pressedOutside && outside(e)) dialog.close(); });
  }

  dialog.addEventListener('close', () => { image.removeAttribute('src'); });

  for (const link of imageLinks) {
    link.addEventListener('click', (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const thumb = link.querySelector('img');
      const figure = link.closest('figure');
      const heading = figure?.querySelector('.insight-media-title');
      title.textContent = heading?.textContent.trim() || thumb.alt.slice(0, 60) || '图片';
      image.alt = thumb.alt;
      image.src = link.href;
      open.href = link.href;
      dialog.showModal();
    });
  }
}
