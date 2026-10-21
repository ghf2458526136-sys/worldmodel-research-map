/* 做法扩散时间线：独立覆盖层，不改主画布 */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const laneColor = {};
  (DATA.lanes || []).forEach(l => { laneColor[l.name] = l.color || "#6b7280"; });
  const nodes = (DATA.nodes || []).filter(n => (n.concepts || []).length);

  // 每个做法 -> 使用它的论文（按日期）
  const groups = {};
  nodes.forEach(n => (n.concepts || []).forEach(c => {
    (groups[c] = groups[c] || []).push(n);
  }));
  const rows = Object.keys(groups)
    .map(c => ({ c, list: groups[c].slice().sort((a, b) => a.date < b.date ? -1 : 1) }))
    .filter(r => r.list.length >= 2)
    .sort((a, b) => b.list.length - a.list.length || (a.list[0].date < b.list[0].date ? -1 : 1));

  const md = s => { const p = String(s).split("-"); return +p[0] * 12 + (+p[1] - 1); };
  let lo = 1e9, hi = -1e9;
  rows.forEach(r => r.list.forEach(n => { const m = md(n.date); lo = Math.min(lo, m); hi = Math.max(hi, m); }));
  const span = Math.max(1, hi - lo);

  const ROW = 26, PADL = 210, PADR = 36, PADT = 26, PADB = 30;
  const W = 1400;
  const PW = W - PADL - PADR;
  const H = PADT + rows.length * ROW + PADB;
  const x = n => PADL + (md(n.date) - lo) / span * PW;

  const el = (t, a) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };

  function build() {
    const wrap = document.createElement("div");
    wrap.className = "ct-wrap";
    const svg = el("svg", { class: "ct-svg", width: "100%", viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMinYMin meet" });

    const step = span > 24 ? 6 : 3;
    for (let m = lo - (lo % step); m <= hi; m += step) {
      const px = PADL + (m - lo) / span * PW;
      if (px < PADL - 1) continue;
      svg.appendChild(el("line", { x1: px, y1: PADT - 8, x2: px, y2: H - PADB + 4, stroke: "#eef2f7", "stroke-width": 1 }));
      const t = el("text", { class: "ct-tick", x: px, y: H - PADB + 18, "text-anchor": "middle" });
      t.textContent = `${Math.floor(m / 12)}-${String(m % 12 + 1).padStart(2, "0")}`;
      svg.appendChild(t);
    }

    rows.forEach((r, i) => {
      const y = PADT + i * ROW + ROW / 2;
      const lab = el("text", { class: "ct-lab", x: PADL - 14, y: y + 4, "text-anchor": "end" });
      lab.textContent = r.c;
      svg.appendChild(lab);
      const cnt = el("text", { class: "ct-cnt", x: 8, y: y + 4 });
      cnt.textContent = r.list.length + " 篇";
      svg.appendChild(cnt);

      const pts = r.list.map(n => ({ n, px: x(n), y }));
      svg.appendChild(el("line", {
        x1: pts[0].px, y1: y, x2: pts[pts.length - 1].px, y2: y,
        stroke: "#dbe3ee", "stroke-width": 1.5, "stroke-dasharray": "2 3"
      }));
      pts.forEach((p, j) => {
        const first = j === 0;
        const col = laneColor[p.n.lane] || "#6b7280";
        const dot = el("circle", {
          class: "ct-dot", cx: p.px, cy: y, r: first ? 6 : 4.2,
          fill: first ? col : "#fff", stroke: col, "stroke-width": first ? 2 : 1.8
        });
        dot.addEventListener("mouseenter", ev => {
          tip.innerHTML = `<b>${p.n.title}</b><br>${p.n.date} · ${p.n.lane}${first ? " · 图谱内首见" : ""}`;
          tip.style.display = "block";
          tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - 360) + "px";
          tip.style.top = (ev.clientY + 16) + "px";
        });
        dot.addEventListener("mouseleave", () => { tip.style.display = "none"; });
        dot.addEventListener("click", () => { close(); if (window.focusNode) focusNode(p.n.id); if (window.openPanel) openPanel(p.n); });
        svg.appendChild(dot);
      });
    });
    wrap.appendChild(svg);
    var lg = document.createElement("div"); lg.className = "ct-legend";
    Object.keys(laneColor).forEach(function (k) { var d = document.createElement("span"); d.className = "ct-lg"; var i = document.createElement("i"); i.style.background = laneColor[k]; d.appendChild(i); d.appendChild(document.createTextNode(k)); lg.appendChild(d); });
    wrap.insertBefore(lg, svg);
    return wrap;
  }

  const ov = document.createElement("div"); ov.id = "ct-ov";
  const head = document.createElement("div"); head.className = "ct-head";
  head.innerHTML = `<h2>做法扩散</h2><span class="sub">横轴为时间，一行一种做法，点越大越早；颜色代表泳道，空心点为后续采用者</span>`;
  const closeBtn = document.createElement("button"); closeBtn.className = "ct-close"; closeBtn.textContent = "×";
  head.appendChild(closeBtn);
  ov.appendChild(head);
  const tip = document.createElement("div"); tip.className = "ct-tip";

  function open() { ov.classList.add("on"); if (!ov.dataset.built) { ov.appendChild(build()); ov.dataset.built = "1"; } }
  function close() { ov.classList.remove("on"); tip.style.display = "none"; }
  closeBtn.onclick = close;
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
  ov.addEventListener("click", e => { if (e.target === ov) close(); });

  const btn = document.createElement("button");
  btn.id = "ct-btn"; btn.textContent = "做法扩散";
  btn.onclick = open;
  const play = document.getElementById("play");
  if (play && play.parentNode) play.parentNode.insertBefore(btn, play.nextSibling);
  document.body.appendChild(ov);
  document.body.appendChild(tip);
})();
