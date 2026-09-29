const state = {
  cases: [],
  q: "",
  category: "all",
  risk: "all",
  evidence: "all",
  severities: new Set(),
  sort: "index"
};

const categoryLabels = {
  all: "全部案例",
  money: "消费与财务",
  work: "职场与学习",
  tools: "工具与效率",
  privacy: "信息与隐私",
  health: "健康误区",
  decisions: "低效决策",
  relationships: "关系与沟通"
};

const riskLabels = {
  money: "钱",
  time: "时间",
  opportunity: "机会",
  privacy: "隐私",
  health: "健康",
  legal: "法律",
  reputation: "声誉"
};

const severityLabels = { critical: "严重", high: "高", medium: "中", low: "低" };
let lastFocusedElement = null;
const severityRank = { critical: 4, high: 3, medium: 2, low: 1 };
const evidenceRank = { A: 3, B: 2, C: 1 };

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHTML(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeHref(url = "") {
  return /^https?:\/\//i.test(url) ? url : "";
}

function formatDate(date = "") {
  return date.replaceAll("-", ".");
}

function filteredCases() {
  const query = state.q.trim().toLowerCase();
  const result = state.cases.filter((item) => {
    const haystack = [
      item.title, item.summary, item.category, item.wrong_advice,
      item.scenario, item.why_attractive, ...(item.tags || []), ...(item.risk_type || [])
    ].join(" ").toLowerCase();
    const matchesQuery = !query || haystack.includes(query);
    const matchesCategory = state.category === "all" || item.category_key === state.category;
    const matchesRisk = state.risk === "all" || item.risk_type.includes(state.risk);
    const matchesEvidence = state.evidence === "all" || item.evidence_grade === state.evidence;
    const matchesSeverity = state.severities.size === 0 || state.severities.has(item.severity);
    return matchesQuery && matchesCategory && matchesRisk && matchesEvidence && matchesSeverity;
  });

  return result.sort((a, b) => {
    if (state.sort === "severity") return severityRank[b.severity] - severityRank[a.severity] || b.score.low_value_index - a.score.low_value_index;
    if (state.sort === "newest") return b.updated_at.localeCompare(a.updated_at) || b.score.low_value_index - a.score.low_value_index;
    if (state.sort === "evidence") return evidenceRank[b.evidence_grade] - evidenceRank[a.evidence_grade] || b.score.low_value_index - a.score.low_value_index;
    return b.score.low_value_index - a.score.low_value_index;
  });
}

function setStats() {
  const categories = new Set(state.cases.map((item) => item.category_key));
  const reviewed = state.cases.filter((item) => ["A", "B"].includes(item.evidence_grade)).length;
  const maxIndex = Math.max(...state.cases.map((item) => item.score.low_value_index), 0);
  const latest = [...state.cases].sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0]?.updated_at || "—";
  $("#statCases").textContent = state.cases.length;
  $("#statCategories").textContent = categories.size;
  $("#statReviewed").textContent = reviewed;
  $("#statUpdated").textContent = latest === "—" ? latest : formatDate(latest);
  $("#heroIndex").textContent = maxIndex;
}

function setFilters() {
  const categoryCounts = state.cases.reduce((acc, item) => {
    acc[item.category_key] = (acc[item.category_key] || 0) + 1;
    return acc;
  }, {});
  $("#categoryFilters").innerHTML = Object.entries(categoryLabels).map(([key, label]) => `
    <button class="filter-chip ${state.category === key ? "active" : ""}" type="button" data-category="${key}">
      <span>${escapeHTML(label)}</span><small>${key === "all" ? state.cases.length : categoryCounts[key] || 0}</small>
    </button>
  `).join("");
  $("#riskFilters").innerHTML = Object.entries(riskLabels).map(([key, label]) => `
    <button class="filter-chip ${state.risk === key ? "active" : ""}" type="button" data-risk="${key}">
      <span>${escapeHTML(label)}</span><small>${state.cases.filter((item) => item.risk_type.includes(key)).length}</small>
    </button>
  `).join("");
  $$("[data-category]").forEach((button) => button.addEventListener("click", () => {
    state.category = button.dataset.category;
    syncUrl(); render();
  }));
  $$("[data-risk]").forEach((button) => button.addEventListener("click", () => {
    state.risk = state.risk === button.dataset.risk ? "all" : button.dataset.risk;
    syncUrl(); render();
  }));
}

function caseBadge(item) {
  return `<span class="case-grade grade-${escapeHTML(item.evidence_grade)}" title="证据等级 ${escapeHTML(item.evidence_grade)}">${escapeHTML(item.evidence_grade)}</span>`;
}

function renderFeatured() {
  const featured = [...state.cases].sort((a, b) => b.score.low_value_index - a.score.low_value_index).slice(0, 2);
  $("#featuredGrid").innerHTML = featured.map((item) => `
    <article class="featured-card" data-open-case="${escapeHTML(item.slug)}" tabindex="0" role="button" aria-label="查看 ${escapeHTML(item.title)}">
      <div>
        <div class="featured-top"><span>${escapeHTML(item.id)} / ${escapeHTML(item.category)}</span>${caseBadge(item)}</div>
        <h3>${escapeHTML(item.title)}</h3>
        <p>${escapeHTML(item.summary)}</p>
      </div>
      <div class="featured-footer"><span class="index-label">INDEX <strong>${item.score.low_value_index}</strong></span><span class="featured-arrow">↗</span></div>
    </article>
  `).join("");
  bindOpenCase();
}

function renderList() {
  const items = filteredCases();
  $("#resultCount").textContent = `${items.length} 条结果`;
  $("#emptyState").hidden = items.length !== 0;
  $("#caseList").innerHTML = items.map((item) => `
    <article class="case-row" data-open-case="${escapeHTML(item.slug)}" tabindex="0" role="button" aria-label="查看 ${escapeHTML(item.title)}">
      <span class="case-id">${escapeHTML(item.id)}</span>
      <div><h3>${escapeHTML(item.title)}</h3><p>${escapeHTML(item.summary)}</p><div class="case-mobile-meta"><span class="mobile-index">指数 ${item.score.low_value_index}</span><span>${escapeHTML(severityLabels[item.severity] || item.severity)}风险</span><span>${escapeHTML(item.evidence_grade)} 级</span></div></div>
      <div class="case-meta"><strong>${item.score.low_value_index}</strong>低性价比指数</div>
      <div class="case-meta"><strong>${escapeHTML(item.evidence_grade)}</strong>证据等级</div>
      <span class="case-arrow">›</span>
    </article>
  `).join("");
  bindOpenCase();
}

function render() {
  setFilters();
  $$("#evidenceFilters .segment").forEach((button) => button.classList.toggle("active", button.dataset.value === state.evidence));
  renderList();
  renderFeatured();
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  if (state.category !== "all") params.set("category", state.category);
  if (state.risk !== "all") params.set("risk", state.risk);
  if (state.evidence !== "all") params.set("evidence", state.evidence);
  if (state.severities.size) params.set("severity", [...state.severities].join(","));
  if (state.sort !== "index") params.set("sort", state.sort);
  const next = `${location.pathname}${params.toString() ? `?${params}` : ""}${location.hash}`;
  history.replaceState({}, "", next);
}

function readUrl() {
  const params = new URLSearchParams(location.search);
  state.q = params.get("q") || "";
  state.category = params.get("category") || "all";
  state.risk = params.get("risk") || "all";
  state.evidence = params.get("evidence") || "all";
  state.sort = params.get("sort") || "index";
  state.severities = new Set((params.get("severity") || "").split(",").filter(Boolean));
  $("#searchInput").value = state.q;
  $("#sortSelect").value = state.sort;
  $$("[data-severity]").forEach((input) => { input.checked = state.severities.has(input.value); });
  $$("#evidenceFilters .segment").forEach((button) => button.classList.toggle("active", button.dataset.value === state.evidence));
}

function detailMarkup(item) {
  const evidence = (item.evidence || []).map((source) => {
    const href = safeHref(source.url);
    const sourceTitle = href ? `<a href="${escapeHTML(href)}" target="_blank" rel="noreferrer">打开来源 ↗</a>` : `<span>匿名复盘记录</span>`;
    return `<div class="evidence-item"><strong><span class="case-grade grade-${escapeHTML(source.grade)}">${escapeHTML(source.grade)}</span> ${escapeHTML(source.title)}</strong><small>${escapeHTML(source.note || "")}</small>${sourceTitle}</div>`;
  }).join("");
  const costs = Object.entries(item.hidden_costs || {}).filter(([, value]) => value).map(([key, value]) => `<div><span>${escapeHTML({money:"钱",time:"时间",opportunity:"机会",other:"其他"}[key] || key)}</span><p>${escapeHTML(value)}</p></div>`).join("");
  const stopLoss = (item.stop_loss || []).map((text) => `<li>${escapeHTML(text)}</li>`).join("");
  const checklist = (item.decision_checklist || []).map((text) => `<li>${escapeHTML(text)}</li>`).join("");
  const mechanism = (item.failure_mechanism || []).map((text) => `<li>${escapeHTML(text)}</li>`).join("");
  const related = (item.related_cases || []).map((slug) => {
    const relatedItem = state.cases.find((candidate) => candidate.slug === slug);
    return relatedItem ? `<button class="related-pill" type="button" data-open-case="${escapeHTML(slug)}">${escapeHTML(relatedItem.id)} ${escapeHTML(relatedItem.title)}</button>` : "";
  }).join("");
  return `
    <div class="detail-kicker"><span>${escapeHTML(item.id)} / ${escapeHTML(item.category)}</span><span>${formatDate(item.updated_at)}</span></div>
    <h2 class="detail-title" id="detailTitle">${escapeHTML(item.title)}</h2>
    <p class="detail-summary">${escapeHTML(item.summary)}</p>
    <div class="detail-alert">${escapeHTML(item.warning)}</div>
    <div class="detail-score"><strong>${item.score.low_value_index}</strong><span>低性价比指数<br>越高代表隐藏成本越重、回头路越窄。</span>${caseBadge(item)}</div>
    <details class="collapsible"><summary>查看“看起来很合理”的错误建议</summary><p>${escapeHTML(item.wrong_advice)}</p></details>
    <div class="detail-section"><h4>场景 / CONTEXT</h4><p>${escapeHTML(item.scenario)}</p></div>
    <div class="detail-section"><h4>为什么会被吸引 / ATTRACTION</h4><p>${escapeHTML(item.why_attractive)}</p></div>
    <div class="detail-section"><h4>隐藏成本 / HIDDEN COSTS</h4><div class="cost-grid">${costs}</div></div>
    <div class="detail-section"><h4>失败机制 / FAILURE MODE</h4><ul>${mechanism}</ul></div>
    <div class="detail-section"><h4>证据 / EVIDENCE</h4>${evidence}</div>
    <div class="detail-section"><h4>何时止损 / STOP-LOSS</h4><ol>${stopLoss}</ol></div>
    <div class="detail-section"><h4>更稳替代 / SAFER ALTERNATIVE</h4><p>${escapeHTML(item.safer_alternative)}</p></div>
    <div class="detail-section"><h4>决策前自检 / CHECKLIST</h4><ul>${checklist}</ul></div>
    <div class="detail-section"><h4>相关案例 / RELATED</h4><div class="detail-related">${related || "<span class=\"muted\">暂无</span>"}</div></div>
  `;
}

function openCase(slug, updateHash = true) {
  const item = state.cases.find((candidate) => candidate.slug === slug);
  if (!item) return;
  lastFocusedElement = document.activeElement;
  $("#drawerContent").innerHTML = detailMarkup(item);
  $("#detailDrawer").classList.add("open");
  $("#detailDrawer").setAttribute("aria-hidden", "false");
  $("#detailDrawer").setAttribute("aria-modal", "true");
  $("#drawerBackdrop").hidden = false;
  document.body.style.overflow = "hidden";
  if (updateHash) history.replaceState({}, "", `${location.pathname}${location.search}#case=${encodeURIComponent(slug)}`);
  $("#closeDrawer").focus();
  $$("[data-open-case]", $("#drawerContent")).forEach((button) => button.addEventListener("click", () => openCase(button.dataset.openCase)));
}

function closeCase(clearHash = true) {
  $("#detailDrawer").classList.remove("open");
  $("#detailDrawer").setAttribute("aria-hidden", "true");
  $("#detailDrawer").setAttribute("aria-modal", "false");
  $("#drawerBackdrop").hidden = true;
  document.body.style.overflow = "";
  if (clearHash) history.replaceState({}, "", `${location.pathname}${location.search}`);
  if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
}

function bindOpenCase() {
  $$('[data-open-case]').forEach((element) => {
    if (element.dataset.bound) return;
    element.dataset.bound = "1";
    element.addEventListener("click", () => openCase(element.dataset.openCase));
    element.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openCase(element.dataset.openCase); }
    });
  });
}

function bindControls() {
  $("#searchInput").addEventListener("input", (event) => { state.q = event.target.value; syncUrl(); render(); });
  $("#sortSelect").addEventListener("change", (event) => { state.sort = event.target.value; syncUrl(); render(); });
  $("#resetFilters").addEventListener("click", () => {
    state.q = ""; state.category = "all"; state.risk = "all"; state.evidence = "all"; state.sort = "index"; state.severities.clear();
    $("#searchInput").value = ""; $("#sortSelect").value = "index"; $$("[data-severity]").forEach((input) => input.checked = false);
    syncUrl(); render();
  });
  $$("[data-severity]").forEach((input) => input.addEventListener("change", () => {
    input.checked ? state.severities.add(input.value) : state.severities.delete(input.value);
    syncUrl(); render();
  }));
  $$("#evidenceFilters .segment").forEach((button) => button.addEventListener("click", () => {
    state.evidence = button.dataset.value; $$("#evidenceFilters .segment").forEach((item) => item.classList.toggle("active", item === button)); syncUrl(); render();
  }));
  $("#closeDrawer").addEventListener("click", () => closeCase());
  $("#drawerBackdrop").addEventListener("click", () => closeCase());
  $("#printButton")?.addEventListener("click", () => window.print());
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement?.tagName !== "INPUT") { event.preventDefault(); $("#searchInput").focus(); }
    if (event.key === "Escape") closeCase();
  });
  window.addEventListener("hashchange", () => {
    const match = location.hash.match(/^#case=(.+)$/);
    if (match) openCase(decodeURIComponent(match[1]), false); else closeCase(false);
  });
}

async function init() {
  try {
    const response = await fetch("data/cases.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.cases = await response.json();
    readUrl();
    setStats();
    bindControls();
    render();
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch((error) => console.warn("service worker registration skipped", error));
    const match = location.hash.match(/^#case=(.+)$/);
    if (match) openCase(decodeURIComponent(match[1]), false);
  } catch (error) {
    console.error(error);
    $("#caseList").innerHTML = `<div class="empty-state"><strong>数据加载失败。</strong><p>请通过本地 HTTP 服务打开，例如 <code>python -m http.server 4173</code>。</p></div>`;
  }
}

init();