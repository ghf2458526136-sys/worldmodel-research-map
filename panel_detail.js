/* panel_detail.js — 详情面板「机制详解」折叠块
 *
 * 用法：  renderDetail(document.getElementById("pbody"), n.detail)
 * 可选依赖：window.katex（缺失时公式退回 <code> 原文，不报错）
 * 全局污染：只挂 window.renderDetail 一个函数
 */
(function (global) {
  "use strict";

  var SECTIONS = [
    { key: "position", label: "定位",           type: "text" },
    { key: "io",       label: "输入输出",        type: "text" },
    { key: "steps",    label: "做法步骤",        type: "steps" },
    { key: "formulas", label: "关键公式",        type: "formulas" },
    { key: "train",    label: "训练与推理",      type: "text" },
    { key: "diff",     label: "与已有做法的差别", type: "text" },
    { key: "limits",   label: "代价与局限",      type: "text" }
  ];

  var pending = [];   // katex 尚未就绪时先记下节点，load 后再升级

  function el(tag, cls, text) {
    var d = document.createElement(tag);
    if (cls) d.className = cls;
    if (text != null) d.textContent = text;
    return d;
  }

  function textOf(v) {
    return typeof v === "string" ? v.trim() : "";
  }

  function stepList(v) {
    if (!Array.isArray(v)) return [];
    var out = [];
    for (var i = 0; i < v.length; i++) {
      var s = textOf(v[i]);
      if (s) out.push(s);
    }
    return out;
  }

  function formulaList(v) {
    if (!Array.isArray(v)) return [];
    var out = [];
    for (var i = 0; i < v.length; i++) {
      var f = v[i], tex = "", cap = "";
      if (typeof f === "string") {
        tex = f.trim();
      } else if (f && typeof f === "object") {
        tex = textOf(f.tex);
        cap = textOf(f.caption);
      }
      if (tex) out.push({ tex: tex, caption: cap });
    }
    return out;
  }

  /* ---------- 公式：katex 优先，<code> 兜底 ---------- */

  function fallback(node, tex) {
    node.textContent = "";
    node.appendChild(el("code", "pd-code", tex));
    node.setAttribute("data-tex", tex);
    pending.push({ node: node, tex: tex });
  }

  function typeset(node, tex) {
    var k = global.katex;
    if (k && typeof k.render === "function") {
      try {
        node.textContent = "";
        k.render(tex, node, { displayMode: true, throwOnError: false });
        node.removeAttribute("data-tex");
        return true;
      } catch (e) {
        /* 落到 fallback，不让单个坏式拖垮整块 */
      }
    }
    fallback(node, tex);
    return false;
  }

  function upgrade() {
    var k = global.katex;
    if (!k || typeof k.render !== "function") return;
    var rest = [];
    for (var i = 0; i < pending.length; i++) {
      var it = pending[i];
      if (!it.node || !it.node.isConnected) continue;
      if (!typeset(it.node, it.tex)) rest.push(it);
    }
    pending = rest;
  }

  if (!global.katex && typeof global.addEventListener === "function") {
    global.addEventListener("load", upgrade, { once: true });
  }

  /* ---------- 各节渲染 ---------- */

  function renderText(sec, value) {
    var t = textOf(value);
    if (!t) return false;
    sec.appendChild(el("p", "pd-p", t));
    return true;
  }

  function renderSteps(sec, value) {
    var steps = stepList(value);
    if (!steps.length) return false;
    var ol = el("ol", "pd-steps");
    for (var i = 0; i < steps.length; i++) {
      var li = el("li", "pd-step");
      var num = el("span", "pd-num", String(i + 1));
      num.setAttribute("aria-hidden", "true");
      li.appendChild(num);
      li.appendChild(el("span", "pd-step-text", steps[i]));
      ol.appendChild(li);
    }
    sec.appendChild(ol);
    return true;
  }

  function renderFormulas(sec, value) {
    var list = formulaList(value);
    if (!list.length) return false;
    for (var i = 0; i < list.length; i++) {
      var fig = el("figure", "pd-fig");
      var box = el("div", "pd-tex");
      typeset(box, list[i].tex);
      fig.appendChild(box);
      if (list[i].caption) fig.appendChild(el("figcaption", "pd-cap", list[i].caption));
      sec.appendChild(fig);
    }
    return true;
  }

  /* ---------- 主入口 ---------- */

  function renderDetail(container, detail) {
    if (!container || !detail || typeof detail !== "object") return null;

    var wrap = el("div", "pd");
    var body = el("div", "pd-body");
    var bodyId = "pd-body-" + Math.random().toString(36).slice(2, 8);
    body.id = bodyId;
    body.hidden = true;

    var filled = 0;
    for (var i = 0; i < SECTIONS.length; i++) {
      var cfg = SECTIONS[i];
      var sec = el("section", "pd-sec");
      var ok;
      if (cfg.type === "steps")          ok = renderSteps(sec, detail[cfg.key]);
      else if (cfg.type === "formulas")  ok = renderFormulas(sec, detail[cfg.key]);
      else                               ok = renderText(sec, detail[cfg.key]);
      if (!ok) continue;
      var h = el("h4", "pd-h", cfg.label);
      sec.insertBefore(h, sec.firstChild);
      body.appendChild(sec);
      filled++;
    }

    // 没取到摘要时给个来源提示，别让人以为是论文原文
    if (detail.has_abstract === false && filled) {
      body.appendChild(el("p", "pd-note", "该条未取到 arXiv 摘要，以上依据已知机制摘要整理"));
    }

    if (!filled) return null;

    var btn = el("button", "pd-toggle", "▶ 机制详解");
    btn.type = "button";
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", bodyId);

    btn.onclick = function () {
      var wasOpen = !body.hidden;
      body.hidden = wasOpen;
      btn.textContent = wasOpen ? "▶ 机制详解" : "▼ 机制详解";
      btn.setAttribute("aria-expanded", wasOpen ? "false" : "true");
      btn.classList.toggle("on", !wasOpen);
      if (!wasOpen) upgrade();
    };

    wrap.appendChild(btn);
    wrap.appendChild(body);
    container.appendChild(wrap);
    return wrap;
  }

  global.renderDetail = renderDetail;
})(window);
