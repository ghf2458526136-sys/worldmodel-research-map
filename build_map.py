"""Research map: each lane (route) gets its own time axis."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import yaml

LABEL_W = 214
PLOT_W = 2100
CARD_W = 248
CARD_H = 100
ROW_H = 116
LANE_PAD = 34
AXIS_H = 30
LANE_GAP = 22
TOP_PAD = 26

LANE_COLORS = ["#4a6cf7", "#0f9d76", "#c2740e", "#8b5cf6", "#d0326b", "#0e7c86", "#5b6472"]
BADGE = {"需训": "#d0326b", "免训": "#0f9d76", "推理期技巧": "#c2740e", "不适用": "#6b7280"}


def parse_day(v):
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


def month_start(d):
    return date(d.year, d.month, 1)


def month_end(d):
    if d.month == 12:
        return date(d.year, 12, 31)
    return date(d.year, d.month + 1, 1) - timedelta(days=1)


def next_month(d):
    return date(d.year + (d.month // 12), d.month % 12 + 1, 1)


def months(a, b):
    out, cur = [], month_start(a)
    while cur <= b:
        out.append(cur)
        cur = next_month(cur)
    return out


def load(path):
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    nodes = doc["nodes"]
    lanes = doc.get("lanes") or []
    order = [l["name"] for l in lanes]
    color = {l["name"]: l.get("color") for l in lanes}
    for n in nodes:
        if n["lane"] not in order:
            order.append(n["lane"])
    return nodes, order, color


def layout(nodes, order, color):
    """同一泳道共用一条紧凑时间轴：按日期排位次，不留空月；分支各占一行。"""
    by_lane = defaultdict(list)
    for n in nodes:
        by_lane[n["lane"]].append(n)

    lane_meta, node_out = [], []
    top = TOP_PAD
    STEP = CARD_W + 26
    width = LABEL_W + 900

    for li, lane in enumerate(order):
        items = by_lane.get(lane, [])
        if not items:
            continue

        by_date = sorted(items, key=lambda n: (parse_day(n["date"]), n["title"]))
        branches = []
        for n in by_date:
            b = n.get("branch") or ""
            if b not in branches:
                branches.append(b)

        # 按月分列：只保留有论文的月份，同月同列，重月横向微错开
        mkeys = []
        for n in by_date:
            d = parse_day(n["date"])
            k = (d.year, d.month)
            if k not in mkeys:
                mkeys.append(k)
        col = {k: i for i, k in enumerate(mkeys)}

        # 同月同分支的多篇纵向摞起来：列位不变，行内下移
        branch_slot = {}          # 每个分支最多摞几层
        placed = {}
        rough = {}
        max_right = LABEL_W
        for n in by_date:
            d = parse_day(n["date"])
            k = (d.year, d.month)
            bi = branches.index(n.get("branch") or "")
            rough.setdefault((bi, k), []).append(n)
        for (bi, k), group in rough.items():
            branch_slot[bi] = max(branch_slot.get(bi, 1), len(group))
            for g, n in enumerate(group):
                x = LABEL_W + col[k] * STEP
                placed[n["id"]] = (x, g)

        # 分支纵向偏移：按每支实际摞的层数累加
        btop, acc = {}, 0
        for bi, b in enumerate(branches):
            btop[bi] = top + LANE_PAD + acc * (CARD_H + 14) + bi * 26
            acc += branch_slot.get(bi, 1)

        for n in by_date:
            x, g = placed[n["id"]]
            bi = branches.index(n.get("branch") or "")
            placed[n["id"]] = (x, btop[bi] + g * (CARD_H + 14))
            max_right = max(max_right, x + CARD_W)

        years, prev = [], None
        for k in mkeys:
            if prev is None or k[0] != prev:
                years.append({"x": LABEL_W + col[k] * STEP - 14, "label": str(k[0])})
            prev = k[0]

        plot_w = max(420, max_right - LABEL_W + 30)
        height = (max(placed[n["id"]][1] for n in items) + CARD_H + 30) - top
        width = max(width, LABEL_W + plot_w + 70)

        lane_meta.append({
            "name": lane,
            "color": color.get(lane) or LANE_COLORS[li % len(LANE_COLORS)],
            "top": top, "height": height, "plotW": plot_w,
            "count": len(items), "years": years,
            "branches": [{"name": b, "y": btop[i], "count": sum(1 for n in by_date if (n.get("branch") or "") == b)}
                         for i, b in enumerate(branches)],
        })

        for n in items:
            x, y = placed[n["id"]]
            node_out.append({
                "id": n["id"], "title": n["title"], "date": n["date"],
                "precision": n.get("precision") or "day",
                "lane": lane, "branch": n.get("branch") or "",
                "arxiv": n.get("arxiv") or "", "venue": n.get("venue") or "",
                "training": n.get("training") or "", "status": n.get("status") or "",
                "one_liner": n.get("one_liner") or "", "mechanism": n.get("mechanism") or "",
                "tags": n.get("tags") or [], "explain": n.get("explain") or "",
                "key_numbers": n.get("key_numbers") or [],
                "self_measured": n.get("self_measured") or [],
                "media": n.get("media") or [], "links": n.get("links") or [],
                "note": n.get("note") or "", "parent": n.get("parent"),
                "link_strength": n.get("link_strength") or "",
                "key": bool(n.get("key")),
                "x": round(x, 1), "y": y,
            })

        top += height + LANE_GAP

    pos = {n["id"]: n for n in node_out}
    for n in node_out:
        p = n.get("parent")
        if p and p in pos:
            src = pos[p]
            n["sx"] = src["x"] + CARD_W
            n["sy"] = src["y"] + CARD_H / 2
            n["cross"] = src["lane"] != n["lane"]
        else:
            n["sx"] = None

    return {
        "nodes": node_out, "lanes": lane_meta,
        "width": width, "height": top + 30,
        "labelW": LABEL_W, "plotW": PLOT_W,
        "card": {"w": CARD_W, "h": CARD_H},
        "badge": BADGE,
        "init": {"scale": 1.0, "tx": 8, "ty": 8},
    }


def validate(data, out_dir, prefix):
    missing = []
    for n in data["nodes"]:
        for m in n["media"]:
            p = (out_dir / (prefix + m)).resolve()
            if not p.exists():
                missing.append(f"{n['id']}: {prefix}{m}")
    return missing


HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root{
    --ink:#16191D; --ink2:#4A5563; --muted:#6B7686; --line:#E6EBF1; --line2:#D5DEE8;
    --bg:#FAFBFC; --card:#ffffff; --band-a:#FFFFFF; --band-b:#F2F6FA;
    --grid:#EFF2F6; --grid-major:#DCE3EC; --accent:#1F6FEB;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);
    font-family:"Microsoft YaHei","PingFang SC","Noto Sans SC",system-ui,sans-serif;}
  header{position:fixed;inset:0 0 auto 0;height:64px;display:flex;align-items:center;gap:16px;
    padding:0 20px;background:rgba(255,255,255,.96);border-bottom:1px solid var(--line);z-index:20}
  header h1{font-size:19px;margin:0;font-weight:700;letter-spacing:.3px;white-space:nowrap}
  #q{height:38px;width:300px;border:1px solid var(--line);border-radius:10px;padding:0 12px;
    font-size:14px;background:#fff;color:var(--ink);outline:none}
  #q:focus{border-color:#4a6cf7;box-shadow:0 0 0 3px rgba(74,108,247,.12)}
  #play{height:38px;padding:0 16px;border:1px solid var(--line);border-radius:10px;background:#fff;
    font-size:14px;cursor:pointer;color:var(--ink2);white-space:nowrap}
  #play:hover{border-color:#4a6cf7;color:#4a6cf7}
  .hint{font-size:12.5px;color:var(--muted);margin-left:auto;white-space:nowrap}
  #stage{position:fixed;inset:64px 0 0 0;overflow:hidden;cursor:grab}
  #stage.drag{cursor:grabbing}
  svg{width:100%;height:100%;display:block}
  .lane-box{stroke:#E2E9F1;stroke-width:1}
  .lane-name{font-size:24px;font-weight:700}
  .lane-count{font-size:13px;fill:var(--muted)}
  .branch{font-size:14px;fill:#4b5563}
  .tick{stroke:#e8ecf3;stroke-width:1}
  .tick.major{stroke:#cfd6e2}
  .year-sep{stroke:#c9d3e0;stroke-width:1.2;stroke-dasharray:4 4}
  .year-label{font-size:14px;font-weight:700;opacity:.85}
  .keyring{animation:kge 2.6s ease-in-out infinite}
  @keyframes kge{0%,100%{opacity:.92}50%{opacity:.2}}
  .key-star{font-size:15px;font-weight:700}
  .year-sep{stroke:#B9C4D2;stroke-width:1.3;stroke-dasharray:5 5}
  .year-label{font-size:15px;font-weight:700;letter-spacing:.04em}
  .tick-label-old{font-size:13px;fill:#8b95a5}
  .tick-label.major{fill:#4b5563;font-weight:600}
  .axis-line{stroke:#dfe5ee;stroke-width:1}
  .link{fill:none;stroke:#c7d0dd;stroke-width:1.6}
  .link.cross{stroke-dasharray:4 5;stroke:#d5dbe6;stroke-width:1.2}
  .card{cursor:pointer}
  .bg{fill:var(--card);stroke:#dfe5ee;stroke-width:1;filter:url(#sh)}
  .card:hover .bg{stroke:#4a6cf7;stroke-width:1.8}
  .card.dim{opacity:.16}
  .card.active .bg{stroke:#111827;stroke-width:2}
  .t-title{font-size:19px;font-weight:600;fill:var(--ink)}
  .t-date{font-size:13px;fill:#8b95a5}
  .badge-t{font-size:11.5px;font-weight:600}
  .tag-t{font-size:10.5px;font-weight:600}
  #panel{position:fixed;top:64px;right:0;bottom:0;width:430px;background:#fff;border-left:1px solid var(--line);
    transform:translateX(100%);transition:transform .22s ease;z-index:30;display:flex;flex-direction:column}
  #panel.open{transform:none;box-shadow:-8px 0 30px rgba(15,23,42,.08)}
  #phead{padding:18px 20px 12px;border-bottom:1px solid var(--line)}
  #phead .t{font-size:18px;font-weight:700;line-height:1.35}
  #phead .m{font-size:12.5px;color:var(--muted);margin-top:6px}
  #pclose{position:absolute;top:14px;right:14px;border:0;background:#f3f4f6;border-radius:8px;
    width:30px;height:30px;font-size:16px;cursor:pointer;color:#6b7280}
  .body{overflow:auto;padding:16px 20px 40px}
  .lab{font-size:12px;font-weight:700;color:#4a6cf7;letter-spacing:.6px;margin:18px 0 8px}
  .lab:first-child{margin-top:0}
  .xbtn{margin:2px 0 10px;padding:8px 14px;border:1px solid var(--accent);background:#fff;
    color:var(--accent);border-radius:9px;font-size:13.5px;font-weight:600;cursor:pointer}
  .xbtn:hover{background:var(--accent-weak)}
  .explain{font-size:15px;line-height:1.95;color:var(--ink2);background:#F7FAFF;
    border-left:4px solid var(--accent);border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:14px}
  .body p{margin:0;font-size:13.5px;line-height:1.75;color:var(--ink2)}
  .body ul{margin:0;padding-left:18px}
  .body li{font-size:13px;line-height:1.9;color:var(--ink2)}
  .chips{display:flex;flex-wrap:wrap;gap:7px}
  .chip{font-size:12.5px;background:#f3f6fd;border:1px solid #e3ebfb;color:#3155c6;border-radius:8px;padding:4px 9px}
  .chip.self{background:#fff7ed;border-color:#fde5c9;color:#a35a09}
  video,img{width:100%;border-radius:10px;border:1px solid var(--line);margin:6px 0;background:#000}
  a{color:#3155c6;font-size:13px;word-break:break-all}
  #dock{position:fixed;right:18px;bottom:18px;display:flex;flex-direction:column;gap:8px;z-index:25}
  #dock button{width:40px;height:40px;border:1px solid var(--line);background:#fff;border-radius:11px;
    font-size:17px;cursor:pointer;color:var(--ink2);box-shadow:0 2px 8px rgba(15,23,42,.06)}
  #dock button:hover{border-color:#4a6cf7;color:#4a6cf7}
  #legend{position:fixed;left:16px;bottom:16px;background:#fff;border:1px solid var(--line);border-radius:12px;
    padding:9px 12px;font-size:12.5px;z-index:25;box-shadow:0 2px 10px rgba(15,23,42,.06);max-width:230px}
  #legend .hd{display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:600;color:var(--ink2)}
  #legend .hd span{margin-left:auto;color:var(--muted);font-weight:400}
  #legend .row{display:flex;align-items:center;gap:8px;padding:3px 0;cursor:pointer;user-select:none}
  #legend .row.off{opacity:.32}
  #legend i{width:11px;height:11px;border-radius:3px;display:inline-block}
  #legend .n{margin-left:auto;color:var(--muted);font-size:11.5px}
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <input id="q" placeholder="搜索标题 / 机制 / 一句话">
  <button id="play">按时间播放</button>
  <span class="hint">滚轮缩放 · 拖拽平移 · 双击全览 · 点卡片看详情 · 每条路线独立时间轴 · 绿色标签=免训 · 连线为机制同构非引用</span>
</header>
<div id="stage">
  <svg id="svg"><defs>
    <filter id="sh" x="-30%" y="-30%" width="180%" height="180%">
      <feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.10"/>
    </filter>
  </defs><g id="vp"></g></svg>
</div>
<aside id="panel"><div id="phead"><div class="t"></div><div class="m"></div>
  <button id="pclose">×</button></div><div class="body" id="pbody"></div></aside>
<div id="dock">
  <button id="zin" title="放大">+</button>
  <button id="zout" title="缩小">−</button>
  <button id="zreset" title="回到起点">⌂</button>
  <button id="zfit" title="全览">⛶</button>
</div>
<div id="legend"></div>
<script>
window.BADGE = __BADGE__;
const DATA = __DATA__;
const svg = document.getElementById("svg"), vp = document.getElementById("vp");
let scale = 1, tx = 0, ty = 0;

function el(tag, attrs, parent){
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for(const [k,v] of Object.entries(attrs || {})){
    if(v == null) continue;
    n.setAttribute(k, v);
  }
  (parent || vp).appendChild(n);
  return n;
}
function apply(){ vp.setAttribute("transform", `translate(${tx},${ty}) scale(${scale})`); }
function resetView(){ scale = DATA.init.scale; tx = DATA.init.tx; ty = DATA.init.ty; apply(); }
function fitAll(){
  const w = svg.clientWidth, h = svg.clientHeight;
  scale = Math.min((w - 60) / DATA.width, (h - 40) / DATA.height, 1.2);
  tx = Math.max(16, (w - DATA.width * scale) / 2);
  ty = 14; apply();
}
function hexA(hex, a){
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`;
}

function build(){
  const laneColor = {};
  DATA.lanes.forEach(l => laneColor[l.name] = l.color);

  DATA.lanes.forEach((l, li) => {
    el("rect", {class:"lane-box", x:8, y:l.top-10, width:DATA.labelW + l.plotW + 24, height:l.height+8, rx:14,
      fill: (li % 2 ? "var(--band-b)" : "var(--band-a)")});
    el("rect", {x:9, y:l.top-6, width:5, height:l.height-4, rx:2.5, fill:l.color, opacity:.9});
    el("text", {class:"lane-name", x:26, y:l.top+16, fill:l.color}).textContent = l.name;
    el("text", {class:"lane-count", x:26, y:l.top+34}).textContent = l.count + " 篇";
  });

  // 每条分支 = 一条紧凑时间轴：卡片按日期连续排，跨年画分隔线
  // 泳道级年份分隔线（同一大分类内跨分支对齐）
  // 泳道级年份分隔线（同一大分类内跨分支对齐）
  // 泳道级年份分隔线（同一大分类内跨分支对齐）
  // 泳道级年份分隔线（同一大分类内跨分支对齐）
  DATA.lanes.forEach(l => {
    l.years.forEach(y => {
      el("line", {class:"year-sep", x1:y.x, y1:l.top - 2, x2:y.x, y2:l.top + l.height - 6});
      const t = el("text", {class:"year-label", x:y.x + 6, y:l.top + 16, fill:l.color});
      t.textContent = y.label;
    });
    l.branches.forEach(b => {
      const baseY = b.y + DATA.card.h + 16;
      el("line", {class:"axis-line", x1:DATA.labelW - 14, y1:baseY,
        x2:DATA.labelW + l.plotW - 10, y2:baseY});
      if(b.name){
        el("circle", {cx:30, cy:b.y + 30, r:3.4, fill:l.color, opacity:.75});
        el("text", {class:"branch", x:40, y:b.y + 34}).textContent = b.name;
      }
    });
  });

  const pos = {};
  DATA.nodes.forEach(n => pos[n.id] = n);
  DATA.nodes.forEach(n => {
    if(n.sx == null) return;
    const x1 = n.sx, y1 = n.sy, x2 = n.x, y2 = n.y + DATA.card.h/2;
    const mid = (x1 + x2) / 2;
    el("path", {d:`M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`, class: n.cross ? "link cross" : "link"});
    el("circle", {cx:x1, cy:y1, r:2.6, fill:"#c7d0dd"});
  });

  DATA.nodes.forEach(n => {
    const g = el("g", {class:"card", "data-id":n.id, transform:`translate(${n.x},${n.y})`});
    el("rect", {class:"bg", width:DATA.card.w, height:DATA.card.h, rx:12}, g);
    if(n.key){
      el("rect", {class:"keyring", x:-4, y:-4, width:DATA.card.w+8, height:DATA.card.h+8, rx:15,
        fill:"none", stroke:laneColor[n.lane] || "#333", "stroke-width":2.4}, g);
    }
    el("rect", {class:"stripe", width:5, height:DATA.card.h-16, x:1.5, y:8,
      fill:laneColor[n.lane] || "#888", rx:2.5, opacity:.9}, g);

    // 右上角：免训标记（绿）优先，其次论文特征标签（泳道色）
    const FREE = {"免训": "免训", "推理期技巧": "推理期"};
    let tagW = 0;
    const tagList = (FREE[n.training] ? [{t: FREE[n.training], free: true}] : [])
      .concat((n.tags || []).map(t => ({t, free: false})));
    if(tagList.length){
      let xRight = DATA.card.w - 10;
      tagList.slice(0, 3).forEach(o => {
        const w = o.t.length * 10.5 + 12;
        if(xRight - w < 12) return;
        el("rect", {x: xRight - w, y: 9, width: w, height: 17, rx: 8,
          fill: o.free ? "#0E9F6E" : (laneColor[n.lane] || "#6b7280"),
          opacity: o.free ? 1 : .12}, g);
        const tx = el("text", {x: xRight - w + 6, y: 21.5, class: "tag-t",
          fill: o.free ? "#ffffff" : (laneColor[n.lane] || "#6b7280")}, g);
        tx.textContent = o.t;
        xRight -= w + 5;
      });
      tagW = DATA.card.w - xRight;
    }
    const t1 = el("text", {class:"t-title", x:15, y:50}, g);
    t1.textContent = n.title;
    const maxW = DATA.card.w - 24;
    while(t1.textContent.length > 4 && t1.getComputedTextLength() > maxW){
      t1.textContent = t1.textContent.slice(0, -2) + "…";
    }
    const t2 = el("text", {class:"t-date", x:15, y:DATA.card.h - 14}, g);
    t2.textContent = n.date.slice(0, 7) + (n.precision === "month" || n.precision === "unknown" ? "" : "-" + n.date.slice(8, 10));
    g.addEventListener("click", ev => { ev.stopPropagation(); openPanel(n); });
  });
}

function openPanel(n){
  document.querySelectorAll(".card.active").forEach(c => c.classList.remove("active"));
  const cur = document.querySelector(`.card[data-id="${n.id}"]`);
  if(cur) cur.classList.add("active");
  const panel = document.getElementById("panel");
  panel.querySelector("#phead .t").textContent = n.title;
  const meta = [n.date, n.precision === "month" ? "日期只到月" : "", n.training, n.status, n.lane + " / " + (n.branch || "主支")]
    .filter(Boolean).join(" · ");
  panel.querySelector("#phead .m").textContent = meta;

  const b = document.getElementById("pbody");
  b.innerHTML = "";
  const add = (cls, text) => { const d = document.createElement("div"); d.className = cls; d.textContent = text; b.appendChild(d); };
  if(n.explain){
    const btn = document.createElement("button");
    btn.className = "xbtn";
    btn.textContent = "▶ 直白讲解";
    const box = document.createElement("div");
    box.className = "explain";
    box.textContent = n.explain;
    box.style.display = "none";
    btn.onclick = () => {
      const open = box.style.display !== "none";
      box.style.display = open ? "none" : "block";
      btn.textContent = open ? "▶ 直白讲解" : "▼ 收起讲解";
    };
    b.appendChild(btn);
    b.appendChild(box);
  }
  if(n.one_liner){ add("lab", "一句话"); add("p", n.one_liner); }
  if(n.mechanism){ add("lab", "机制"); add("p", n.mechanism); }
  if(n.key_numbers && n.key_numbers.length){
    add("lab", "关键数字");
    const c = document.createElement("div"); c.className = "chips";
    n.key_numbers.forEach(k => { const s = document.createElement("span"); s.className = "chip"; s.textContent = k; c.appendChild(s); });
    b.appendChild(c);
  }
  if(n.self_measured && n.self_measured.length){
    add("lab", "我们自测（非论文指标）");
    const c = document.createElement("div"); c.className = "chips";
    n.self_measured.forEach(k => { const s = document.createElement("span"); s.className = "chip self"; s.textContent = k; c.appendChild(s); });
    b.appendChild(c);
  }
  if(n.media && n.media.length){
    add("lab", "素材");
    n.media.forEach(m => {
      const src = DATA.prefix + m;
      if(/\.(mp4|webm|mov)$/i.test(m)){
        const v = document.createElement("video");
        v.src = src; v.controls = true; v.muted = true; v.playsInline = true; v.preload = "metadata";
        b.appendChild(v);
      } else {
        const img = document.createElement("img"); img.src = src; img.loading = "lazy";
        b.appendChild(img);
      }
    });
  }
  if(n.links && n.links.length){
    add("lab", "链接");
    n.links.forEach(u => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.textContent = u; b.appendChild(a); b.appendChild(document.createElement("br")); });
  }
  if(n.note){ add("lab", "备注"); add("p", n.note); }
  panel.classList.add("open");
}
document.getElementById("pclose").onclick = () => document.getElementById("panel").classList.remove("open");

let lastX = 0, lastY = 0, dragging = false;
svg.addEventListener("mousedown", ev => { dragging = true; lastX = ev.clientX; lastY = ev.clientY; document.getElementById("stage").classList.add("drag"); });
window.addEventListener("mouseup", () => { dragging = false; document.getElementById("stage").classList.remove("drag"); });
window.addEventListener("mousemove", ev => {
  if(!dragging) return;
  tx += ev.clientX - lastX; ty += ev.clientY - lastY;
  lastX = ev.clientX; lastY = ev.clientY; apply();
});
svg.addEventListener("wheel", ev => {
  ev.preventDefault();
  const r = svg.getBoundingClientRect();
  const mx = ev.clientX - r.left, my = ev.clientY - r.top;
  const k = ev.deltaY < 0 ? 1.12 : 1/1.12;
  const ns = Math.min(3, Math.max(0.12, scale * k));
  tx = mx - (mx - tx) * (ns / scale);
  ty = my - (my - ty) * (ns / scale);
  scale = ns; apply();
}, {passive:false});
svg.addEventListener("dblclick", fitAll);
document.getElementById("zin").onclick = () => { scale = Math.min(3, scale*1.2); apply(); };
document.getElementById("zout").onclick = () => { scale = Math.max(0.12, scale/1.2); apply(); };
document.getElementById("zreset").onclick = resetView;
document.getElementById("zfit").onclick = fitAll;

document.getElementById("q").addEventListener("input", ev => {
  const q = ev.target.value.trim().toLowerCase();
  document.querySelectorAll(".card").forEach(c => {
    const n = DATA.nodes.find(x => x.id === c.dataset.id);
    const hay = (n.title + " " + n.mechanism + " " + n.one_liner + " " + n.lane + " " + n.branch).toLowerCase();
    c.classList.toggle("dim", !!q && !hay.includes(q));
  });
});

const legend = document.getElementById("legend");
const hd = document.createElement("div");
hd.className = "hd";
hd.innerHTML = "图例 <span>−</span>";
legend.appendChild(hd);
const rows = document.createElement("div");
rows.style.display = "none";
legend.appendChild(rows);
hd.querySelector("span").textContent = "+";
hd.onclick = () => { rows.style.display = rows.style.display === "none" ? "" : "none"; hd.querySelector("span").textContent = rows.style.display === "none" ? "+" : "−"; };
DATA.lanes.forEach(l => {
  const row = document.createElement("div");
  row.className = "row";
  row.innerHTML = `<i style="background:${l.color}"></i><span>${l.name}</span><span class="n">${l.count}</span>`;
  row.onclick = () => {
    row.classList.toggle("off");
    const off = row.classList.contains("off");
    document.querySelectorAll(".card").forEach(c => {
      const n = DATA.nodes.find(x => x.id === c.dataset.id);
      if(n.lane === l.name) c.style.display = off ? "none" : "";
    });
  };
  rows.appendChild(row);
});

let playing = null;
document.getElementById("play").onclick = () => {
  if(playing){ clearInterval(playing); playing = null; return; }
  const order = [...DATA.nodes].sort((a,b) => a.date.localeCompare(b.date));
  let i = 0;
  playing = setInterval(() => {
    if(i >= order.length){ clearInterval(playing); playing = null; return; }
    const n = order[i++];
    openPanel(n);
    document.querySelectorAll(".card.active").forEach(c => c.classList.remove("active"));
    const cur = document.querySelector(`.card[data-id="${n.id}"]`);
    if(cur) cur.classList.add("active");
  }, 900);
};

build();
resetView();
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) < 4:
        raise SystemExit("用法: build_map.py data.yaml out.html TITLE [media_prefix]")
    src, out, title = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    prefix = sys.argv[4] if len(sys.argv) > 4 else ""
    nodes, order, color = load(src)
    data = layout(nodes, order, color)
    data["prefix"] = prefix
    missing = validate(data, out.parent, prefix)
    html = HTML.replace("__TITLE__", title)
    html = html.replace("__BADGE__", json.dumps(BADGE, ensure_ascii=False))
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.name}  nodes={len(data['nodes'])} lanes={len(data['lanes'])} size={int(data['width'])}x{int(data['height'])}")
    if missing:
        print("缺素材：")
        for m in missing:
            print("  -", m)
    else:
        print("素材全部存在")


if __name__ == "__main__":
    main()
