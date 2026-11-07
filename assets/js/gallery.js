// Screenshot gallery: clicking a picture in a `.shots` grid opens it full screen over the page
// instead of the bare PNG. X (top right), Esc or a click on the dark backdrop closes it; the arrows,
// the arrow keys or a swipe go through the other pictures in the same grid. Without JavaScript the
// links still open the image itself.
(() => {
  const css = `
    .lb { position: fixed; inset: 0; z-index: 100; display: flex; flex-direction: column; align-items: center;
          justify-content: center; gap: 12px; padding: 56px 16px 20px; background: rgba(10, 9, 15, 0.97);
          opacity: 0; transition: opacity 0.18s; }
    .lb.open { opacity: 1; }
    .lb[hidden] { display: none; }
    .lb img { max-width: 100%; max-height: calc(100vh - 140px); object-fit: contain; border-radius: 8px;
              box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6); user-select: none; -webkit-user-drag: none; }
    .lb figcaption { color: var(--text, #ece8f4); text-align: center; max-width: 900px; font-size: 0.95rem; }
    .lb .lb-count { color: var(--muted, #a49cb8); font-size: 0.8rem; margin-left: 8px; white-space: nowrap; }
    .lb button { position: absolute; display: grid; place-items: center; border: 1px solid var(--line, #3a3450);
                 background: rgba(36, 32, 51, 0.85); color: var(--text, #ece8f4); cursor: pointer;
                 border-radius: 50%; width: 48px; height: 48px; font: 28px/1 var(--sans, sans-serif); }
    .lb button:hover, .lb button:focus-visible { border-color: var(--accent, #f4a53a); color: var(--accent, #f4a53a); outline: none; }
    .lb .lb-close { top: 12px; right: 12px; }
    .lb .lb-prev { left: 12px; top: 50%; transform: translateY(-50%); }
    .lb .lb-next { right: 12px; top: 50%; transform: translateY(-50%); }
    .lb.single .lb-prev, .lb.single .lb-next { display: none; }
    @media (max-width: 600px) {
      .lb .lb-prev, .lb .lb-next { top: auto; bottom: 14px; transform: none; width: 44px; height: 44px; }
      .lb { padding-bottom: 72px; }
    }
    body.lb-lock { overflow: hidden; }
  `;
  document.head.appendChild(Object.assign(document.createElement("style"), { textContent: css }));

  const box = document.createElement("div");
  box.className = "lb";
  box.hidden = true;
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", "Screenshot");
  box.innerHTML = `
    <button class="lb-close" type="button" aria-label="Close">&times;</button>
    <button class="lb-prev" type="button" aria-label="Previous screenshot">&#8249;</button>
    <figure style="margin:0;display:flex;flex-direction:column;align-items:center;gap:12px">
      <img alt="">
      <figcaption><span class="lb-text"></span><span class="lb-count"></span></figcaption>
    </figure>
    <button class="lb-next" type="button" aria-label="Next screenshot">&#8250;</button>`;
  document.body.appendChild(box);
  const img = box.querySelector("img");
  const text = box.querySelector(".lb-text");
  const count = box.querySelector(".lb-count");

  let items = [];          // the links of the grid that was clicked
  let index = 0;
  let opener = null;       // focus goes back here on close

  function show(i) {
    index = (i + items.length) % items.length;
    const a = items[index];
    const thumb = a.querySelector("img");
    img.src = a.href;
    img.alt = thumb ? thumb.alt : "";
    const cap = a.closest("figure")?.querySelector("figcaption");
    text.textContent = cap ? cap.textContent : img.alt;
    count.textContent = items.length > 1 ? `${index + 1} / ${items.length}` : "";
    // fetch the neighbours so the arrows feel instant
    for (const d of [1, -1]) new Image().src = items[(index + d + items.length) % items.length].href;
  }

  function open(link) {
    items = [...link.closest(".shots").querySelectorAll("a[href]")];
    opener = link;
    box.classList.toggle("single", items.length < 2);
    show(items.indexOf(link));
    box.hidden = false;
    document.body.classList.add("lb-lock");
    requestAnimationFrame(() => box.classList.add("open"));
    box.querySelector(".lb-close").focus();
  }

  function close() {
    box.classList.remove("open");
    document.body.classList.remove("lb-lock");
    setTimeout(() => { box.hidden = true; img.removeAttribute("src"); }, 180);
    opener?.focus();
  }

  document.querySelectorAll(".shots a[href]").forEach((a) => {
    a.addEventListener("click", (e) => {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;   // new tab still works
      e.preventDefault();
      open(a);
    });
  });

  box.querySelector(".lb-close").addEventListener("click", close);
  box.querySelector(".lb-prev").addEventListener("click", () => show(index - 1));
  box.querySelector(".lb-next").addEventListener("click", () => show(index + 1));
  box.addEventListener("click", (e) => { if (e.target === box) close(); });
  document.addEventListener("keydown", (e) => {
    if (box.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") show(index - 1);
    else if (e.key === "ArrowRight") show(index + 1);
  });

  // swipe left / right on phones
  let x0 = null;
  box.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  box.addEventListener("touchend", (e) => {
    if (x0 === null || items.length < 2) return;
    const dx = e.changedTouches[0].clientX - x0;
    x0 = null;
    if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
  });
})();
