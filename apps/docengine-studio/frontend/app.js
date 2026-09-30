/* DocEngine Studio - vanilla-JS ESM single page app.
 *
 * Rules inherited from the repository's own UX requirements
 * (docs/DOCENGINE_UI_DESIGN_2026-09-30.md):
 *   - never show simulated progress; only real upstream stages
 *   - never invent document codes, verdicts or counts in the client
 *   - lane results are labelled official vs advisory
 *   - a FAILed document is never presented as a deliverable
 */

const state = { view: "overview", me: null, health: null, registry: [], certificates: [], questionnaires: [], search: "" };

async function api(path, opts = {}) {
  const res = await fetch(path, { credentials: "same-origin", headers: { "Content-Type": "application/json" }, ...opts });
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { raw: text }; }
  if (!res.ok) {
    const d = body && (body.detail || body.error) ? (body.detail || body.error) : res.statusText;
    const err = new Error(typeof d === "string" ? d : JSON.stringify(d));
    err.status = res.status; err.body = body;
    throw err;
  }
  return body;
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function toast(msg, kind) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast show" + (kind === "err" ? " err" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.className = "toast"; }, 5000);
}

const can = (cap) => !!(state.me && state.me.capabilities && state.me.capabilities.includes(cap));

function fmtTime(ts) {
  if (!ts && ts !== 0) return "-";
  const d = typeof ts === "number" ? new Date(ts * 1000) : new Date(ts);
  return isNaN(d) ? String(ts) : d.toISOString().replace("T", " ").slice(0, 19) + "Z";
}

const chipLane = (l) => `<span class="chip ${l === "official" ? "official" : "advisory"}">${esc(l)}</span>`;
const chipStatus = (s) => `<span class="chip ${esc(s)}">${esc(s)}</span>`;
const chipBool = (b) => `<span class="chip ${b ? "pass" : ""}">${b ? "yes" : "no"}</span>`;
const kpi = (n, l) => `<div class="card kpi"><div class="n">${esc(n)}</div><div class="l">${esc(l)}</div></div>`;

const STAGES = ["queued", "generate", "regulatory-check", "bilingual-check", "qa-audit", "format", "done"];

/* ------------------------------------------------------------------ nav */

function renderNav() {
  const items = [
    ["overview", "Overview", null],
    ["registry", "Registry", state.registry.length || null],
    ["author", "Author", null],
    ["certificates", "Certificates", state.certificates.length || null],
    ["assistant", "Assistant", null],
    ["audit", "Audit", null],
    ["routing", "Routing", null],
    ["clients", "Clients", null],
  ];
  document.getElementById("nav").innerHTML = items
    .map(([key, label, count]) => `<button data-nav="${key}" class="${state.view === key ? "active" : ""}">${esc(label)}${count ? `<span class="count">${count}</span>` : ""}</button>`)
    .join("");
  document.querySelectorAll("#nav button").forEach((b) => b.addEventListener("click", () => go(b.dataset.nav)));
}

function go(view) {
  state.view = VIEWS[view] ? view : "overview";
  document.getElementById("view-title").textContent = VIEWS[state.view].title;
  renderNav();
  VIEWS[state.view].render();
}

const setView = (html) => { document.getElementById("view").innerHTML = html; };
const loading = (label) => setView(`<div class="empty">Loading ${esc(label)}...</div>`);
const errBanner = (e, title) => `<div class="banner danger"><span class="b-ico">x</span><div><b>${esc(title || "Request failed")}</b><div class="s">${esc(e.message || e)}</div></div></div>`;

/* ------------------------------------------------------------------ views */

async function renderOverview() {
  loading("overview");
  try { state.health = await api("/api/health"); } catch (e) { setView(errBanner(e, "Studio gateway unreachable")); return; }
  const h = state.health, de = h.docengine || {};
  const lanes = [
    ["Official lane (RAGFlow)", h.official_lane, "Verified certificates and official retrieval"],
    ["Advisory lane (Letta)", h.advisory_lane, "Conversational and knowledge questions"],
    ["DocEngine upstream", de.ok, de.engine || de.error || "not reachable"],
    ["Model provider", h.model_provider_ready, h.model_provider_ready ? "configured" : "not configured - AI functions disabled"],
  ];
  setView(`
    <div class="grid cols-4">
      ${kpi(state.registry.length, "Registry documents")}
      ${kpi(state.certificates.length, "Verified certificates")}
      ${kpi((h.audit && h.audit.events) || 0, "Audit events")}
      ${kpi(h.audit && h.audit.ok ? "PASS" : "FAIL", "Audit chain")}
    </div>
    <div class="card"><header><h2>Service status</h2></header><div class="body"><div class="list">
      ${lanes.map(([name, ok, detail]) => `<div class="item"><span class="chip ${ok ? "pass" : "fail"}">${ok ? "up" : "down"}</span><div class="grow"><div class="t">${esc(name)}</div><div class="s">${esc(detail)}</div></div></div>`).join("")}
    </div></div></div>
    <div class="banner"><span class="b-ico">i</span><div>Official intents resolve through the RAGFlow lane and <b>fail closed</b> - with no verified evidence the request is refused rather than answered from an advisory source. Approvals and signatures are human-only and are never exposed over MCP.</div></div>`);
}

async function renderRegistry() {
  loading("registry");
  try { state.registry = (await api("/api/registry?limit=200")).documents || []; } catch (e) { setView(errBanner(e)); return; }
  const q = state.search.toLowerCase();
  const rows = state.registry.filter((d) => !q || [d.title, d.id, d.doc_type].filter(Boolean).some((v) => String(v).toLowerCase().includes(q)));
  setView(`
    <div class="card"><header><h2>Registry (${rows.length})</h2>${can("qms.author") ? '<button class="btn sm" id="new-doc">New document</button>' : ""}</header>
    <div class="body" style="padding:0">
      <table><thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Lang</th><th>Status</th><th>Updated</th></tr></thead><tbody>
        ${rows.length ? rows.map((d) => `<tr data-doc="${esc(d.id)}" style="cursor:pointer"><td class="mono">${esc(d.id)}</td><td>${esc(d.title)}</td><td>${esc(d.doc_type || "-")}</td><td>${esc(d.language || "-")}</td><td>${chipStatus(d.status)}</td><td class="mono">${esc(fmtTime(d.updated_at))}</td></tr>`).join("") : '<tr><td colspan="6" class="empty">No documents yet.</td></tr>'}
      </tbody></table>
    </div></div>`);
  const nb = document.getElementById("new-doc");
  if (nb) nb.addEventListener("click", newDocument);
  document.querySelectorAll("tr[data-doc]").forEach((tr) => tr.addEventListener("click", () => openDocument(tr.dataset.doc)));
}

function newDocument() {
  const title = prompt("Document title:");
  if (!title) return;
  const doc_type = prompt("Document type (sop, coa, spec, protocol, report):", "sop") || "sop";
  api("/api/registry", { method: "POST", body: JSON.stringify({ title, doc_type }) })
    .then(() => { toast("Document created"); renderRegistry(); })
    .catch((e) => toast("Create failed: " + e.message, "err"));
}

const FLOW = { draft: ["in_review"], in_review: ["draft", "approved"], approved: ["effective", "superseded"], effective: ["superseded"], superseded: [] };

async function openDocument(docId) {
  const doc = state.registry.find((d) => d.id === docId);
  if (!doc) return;
  let decisions = { approvals: [], signatures: [] };
  try { decisions = await api(`/api/registry/${docId}/approvals`); } catch { /* optional */ }
  const next = FLOW[doc.status] || [];
  const modal = document.createElement("div");
  modal.className = "modal";
  const history = decisions.approvals.map((a) => `<div class="item"><span class="pill">approval</span><div class="grow"><div class="t">${esc(a.decision)}</div><div class="s">${esc(a.actor)} - ${esc(a.role || "")} - ${esc(fmtTime(a.created_at))}</div></div></div>`)
    .concat(decisions.signatures.map((s) => `<div class="item"><span class="pill">signature</span><div class="grow"><div class="t">${esc(s.meaning)}</div><div class="s">${esc(s.actor)} - ${esc(fmtTime(s.created_at))}</div></div></div>`));
  modal.innerHTML = `
    <div class="sheet">
      <header><h3>${esc(doc.title)}</h3>${chipStatus(doc.status)}</header>
      <div class="body">
        <div class="row">
          <div><span class="hint">ID</span><div class="mono">${esc(doc.id)}</div></div>
          <div><span class="hint">Type</span><div>${esc(doc.doc_type || "-")}</div></div>
          <div><span class="hint">Language</span><div>${esc(doc.language || "-")}</div></div>
          <div><span class="hint">Owner</span><div>${esc(doc.owner || "-")}</div></div>
        </div>
        <div><span class="hint">Lifecycle</span><div class="row">${next.length ? next.map((s) => `<button class="btn sec sm" data-status="${s}">Move to ${s}</button>`).join("") : '<span class="hint">Terminal state</span>'}</div></div>
        <div><span class="hint">Approvals &amp; signatures</span><div class="list">${history.length ? history.join("") : '<span class="hint">None recorded.</span>'}</div></div>
        <div><span class="hint">Decision</span><div class="row">
          <input id="approval-comment" placeholder="Comment (recorded in the audit trail)">
          ${can("qms.approve") ? '<button class="btn" id="do-approve">Approve</button><button class="btn sec" id="do-reject">Reject</button>' : ""}
          ${can("qms.sign") ? '<button class="btn sec" id="do-sign">Sign</button>' : ""}
        </div></div>
      </div>
      <footer><button class="btn sec" id="close-modal">Close</button></footer>
    </div>`;
  document.body.appendChild(modal);
  const close = () => modal.remove();
  modal.querySelector("#close-modal").addEventListener("click", close);
  modal.addEventListener("click", (e) => { if (e.target === modal) close(); });
  modal.querySelectorAll("[data-status]").forEach((b) => b.addEventListener("click", () => {
    api(`/api/registry/${docId}/status`, { method: "POST", body: JSON.stringify({ status: b.dataset.status }) })
      .then(() => { toast("Status updated"); close(); renderRegistry(); })
      .catch((e) => toast(e.message, "err"));
  }));
  const approve = modal.querySelector("#do-approve");
  if (approve) approve.addEventListener("click", () => decide(docId, "approved", modal));
  const reject = modal.querySelector("#do-reject");
  if (reject) reject.addEventListener("click", () => decide(docId, "rejected", modal));
  const sign = modal.querySelector("#do-sign");
  if (sign) sign.addEventListener("click", () => {
    const meaning = prompt("Signature meaning (recorded verbatim):", "Reviewed and approved");
    if (!meaning) return;
    api(`/api/registry/${docId}/signatures`, { method: "POST", body: JSON.stringify({ meaning }) })
      .then(() => { toast("Signature recorded"); close(); openDocument(docId); })
      .catch((e) => toast(e.message, "err"));
  });
}

function decide(docId, decision, modal) {
  const comment = (modal.querySelector("#approval-comment") || {}).value || "";
  api(`/api/registry/${docId}/approvals`, { method: "POST", body: JSON.stringify({ decision, comment }) })
    .then(() => { toast("Decision recorded: " + decision); modal.remove(); renderRegistry(); })
    .catch((e) => toast(e.message, "err"));
}

/* ---------------------------------------------------------------- author */

async function renderAuthor() {
  loading("question banks");
  try { state.questionnaires = (await api("/api/questionnaires")).questionnaires || []; } catch (e) { setView(errBanner(e, "Question banks unavailable")); return; }
  setView(`
    <div class="split">
      <div class="card"><header><h2>Author a controlled document</h2></header><div class="body">
        <label class="field"><span>Question bank</span><select id="qkey">${state.questionnaires.map((q) => `<option value="${esc(q.key)}">${esc(q.title || q.key)}</option>`).join("")}</select></label>
        <div class="row">
          <label class="field"><span>Title (MK)</span><input id="title_mk" placeholder="Наслов"></label>
          <label class="field"><span>Title (EN)</span><input id="title_en" placeholder="Title"></label>
        </div>
        <div class="row">
          <label class="field"><span>Document code</span><input id="code" placeholder="PP-QC-SOP-001"></label>
          <label class="field"><span>Version</span><input id="version" value="1.0"></label>
        </div>
        <label class="field"><span>Answers (JSON)</span><textarea id="answers" placeholder='{"purpose":"..."}'></textarea></label>
        <div class="row">
          <button class="btn" id="run-wf">Generate document</button>
          ${can("qms.build") ? '<button class="btn sec" id="run-build">Build from Markdown</button>' : ""}
        </div>
        <div class="hint">The engine refuses to return a document that fails verification. A refusal is shown with its verification report - never as a deliverable.</div>
      </div></div>
      <div class="card"><header><h2>Pipeline</h2></header><div class="body">
        <div class="steps" id="steps">${STAGES.map((s) => `<div class="step" data-stage="${s}"><div class="s-label">${s}</div></div>`).join("")}</div>
        <div id="wf-result" style="margin-top:14px"></div>
      </div></div>
    </div>`);
  document.getElementById("run-wf").addEventListener("click", runWorkflow);
  const rb = document.getElementById("run-build");
  if (rb) rb.addEventListener("click", openBuild);
}

function markStage(stage, status, detail) {
  const el = document.querySelector(`[data-stage="${stage}"]`);
  if (!el) return;
  el.className = "step " + status;
  if (detail) {
    if (!el.querySelector(".s-time")) el.insertAdjacentHTML("beforeend", '<span class="s-time"></span>');
    el.querySelector(".s-time").textContent = detail;
  }
}

async function runWorkflow() {
  const meta = { title_mk: document.getElementById("title_mk").value.trim(), title_en: document.getElementById("title_en").value.trim(), code: document.getElementById("code").value.trim(), version: document.getElementById("version").value.trim() || "1.0" };
  if (!meta.title_mk || !meta.title_en || !meta.code) { toast("Title (MK), Title (EN) and code are required", "err"); return; }
  let answers = {};
  const raw = document.getElementById("answers").value.trim();
  if (raw) { try { answers = JSON.parse(raw); } catch { toast("Answers must be valid JSON", "err"); return; } }
  document.querySelectorAll(".step").forEach((s) => (s.className = "step"));
  let job;
  try { job = await api("/api/workflows", { method: "POST", body: JSON.stringify({ questionnaire: document.getElementById("qkey").value, answers, meta }) }); }
  catch (e) { toast("Workflow start failed: " + e.message, "err"); return; }
  markStage("queued", "done", new Date().toISOString().slice(11, 19));
  pollWorkflow(job.job_id);
}

async function pollWorkflow(jobId) {
  const out = document.getElementById("wf-result");
  let last = "";
  const tick = async () => {
    let job;
    try { job = await api(`/api/workflows/${jobId}`); }
    catch (e) { out.innerHTML = errBanner(e, "Polling failed"); return; }
    const stage = job.stage || job.status || "queued";
    if (stage !== last) {
      if (last) markStage(last, "done");
      markStage(stage, "active");
      last = stage;
    }
    if (job.status === "failed" || job.error) {
      markStage(stage, "failed");
      out.innerHTML = `<div class="banner danger"><span class="b-ico">!</span><div><b>Generation failed</b><div class="s">${esc(job.error || "unknown error")}</div></div></div>`;
      return;
    }
    if (job.status === "done" || job.status === "completed" || stage === "done") {
      markStage("done", "done");
      out.innerHTML = `<div class="banner ok"><span class="b-ico">ok</span><div><b>Document verified and registered.</b> Job <code>${esc(jobId)}</code></div></div>`;
      return;
    }
    out.innerHTML = `<div class="pre">${esc(JSON.stringify(job, null, 2))}</div>`;
    setTimeout(tick, 2500);
  };
  tick();
}

function openBuild() {
  const modal = document.createElement("div");
  modal.className = "modal";
  modal.innerHTML = `
    <div class="sheet"><header><h3>Build from Markdown</h3></header><div class="body">
      <label class="field"><span>Markdown (bilingual, engine canon)</span><textarea id="md" style="min-height:220px" placeholder="# Наслов"></textarea></label>
      <label class="field"><span>Output name</span><input id="out_name" value="document"></label>
      <div id="build-out"></div>
    </div><footer><button class="btn sec" id="b-close">Close</button><button class="btn" id="b-run">Build</button></footer></div>`;
  document.body.appendChild(modal);
  modal.querySelector("#b-close").addEventListener("click", () => modal.remove());
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });
  modal.querySelector("#b-run").addEventListener("click", async () => {
    const out = modal.querySelector("#build-out");
    out.innerHTML = '<div class="hint">Building...</div>';
    try {
      const res = await api("/api/build", { method: "POST", body: JSON.stringify({ markdown: modal.querySelector("#md").value, out_name: modal.querySelector("#out_name").value || "document" }) });
      out.innerHTML = res.ok === false
        ? `<div class="banner danger"><span class="b-ico">!</span><div><b>Verification failed - the engine refused this document.</b><div class="pre" style="margin-top:8px">${esc(JSON.stringify(res.verify, null, 2))}</div></div></div>`
        : `<div class="banner ok"><span class="b-ico">ok</span><div>Verified. <code>${esc(res.document_id || "")}</code></div></div>`;
    } catch (e) { out.innerHTML = errBanner(e); }
  });
}

/* ------------------------------------------------------------ certificates */

async function renderCertificates() {
  loading("certificates");
  try { state.certificates = (await api("/api/certificates")).documents || []; } catch (e) { setView(errBanner(e, "DocEngine registry unavailable")); return; }
  const rows = state.certificates.map((d) => `<tr><td class="mono">${esc(d.id)}</td><td>${esc(d.code || d.title_en || d.title_mk || "-")}</td><td>${esc(d.doctype || "-")}</td><td>${chipBool(!!d.verify)}</td><td class="num">${esc(d.bytes || "-")}</td><td><a class="btn sec sm" href="/api/certificates/${esc(d.id)}/pdf" target="_blank" rel="noopener">PDF</a> <a class="btn sec sm" href="/api/certificates/${esc(d.id)}/download">DOCX</a></td></tr>`).join("");
  setView(`
    <div class="banner"><span class="b-ico">i</span><div>Only documents that passed verification exist here - the engine deletes anything that fails <code>pp_verify</code>.</div></div>
    <div class="card"><header><h2>Engine registry (${state.certificates.length})</h2></header><div class="body" style="padding:0">
      <table><thead><tr><th>ID</th><th>Code / title</th><th>Type</th><th>Verified</th><th>Bytes</th><th></th></tr></thead><tbody>
        ${rows || '<tr><td colspan="6" class="empty">No verified documents in the engine registry.</td></tr>'}
      </tbody></table>
    </div></div>`);
}

/* ---------------------------------------------------------------- assistant */

async function renderAssistant() {
  setView(`
    <div class="split">
      <div class="card"><header><h2>Ask the document engine</h2></header><div class="body">
        <label class="field"><span>Intent</span><select id="intent">
          <option value="official_evidence">Official evidence (RAGFlow, fail-closed)</option>
          <option value="coa_lookup">Certificate lookup (RAGFlow, fail-closed)</option>
          <option value="qa_query">QMS knowledge question (Letta, advisory)</option>
          <option value="assistant_chat">Assistant chat (Letta, advisory)</option>
          <option value="summarisation">Summarise (Letta, advisory)</option>
        </select></label>
        <label class="field"><span>Question</span><textarea id="question" style="min-height:100px" placeholder="Ask a question..."></textarea></label>
        <div class="row"><button class="btn" id="ask">Ask</button></div>
      </div></div>
      <div class="card"><header><h2>Answer</h2></header><div class="body" id="answer"><div class="hint">Answers are labelled with the lane that produced them.</div></div></div>
    </div>`);
  document.getElementById("ask").addEventListener("click", doAsk);
}

async function doAsk() {
  const question = document.getElementById("question").value.trim();
  const intent = document.getElementById("intent").value;
  const out = document.getElementById("answer");
  if (question.length < 3) { toast("Enter a question", "err"); return; }
  out.innerHTML = '<div class="hint">Resolving lane...</div>';
  try {
    const res = await api("/api/ask", { method: "POST", body: JSON.stringify({ question, intent }) });
    out.innerHTML = `
      <div style="margin-bottom:10px">${chipLane(res.lane_label)} <span class="pill">${esc(res.intent)}</span> <span class="hint">${esc(res.elapsed)}s</span></div>
      ${res.advisory ? '<div class="banner warn" style="margin-bottom:10px"><span class="b-ico">!</span><div>Advisory answer - not verified evidence. Do not use for a controlled record.</div></div>' : ""}
      <div class="pre">${esc(res.answer)}</div>
      ${res.citations && res.citations.length ? `<div style="margin-top:10px"><span class="hint">Citations</span><div class="list">${res.citations.map((c) => `<div class="item"><div class="grow"><div class="t">${esc(c.source || "n/a")}</div><div class="s">${esc(c.dataset || "")} ${esc(c.similarity != null ? "sim " + c.similarity : "")}</div></div></div>`).join("")}</div></div>` : ""}`;
  } catch (e) {
    const refused = e.status === 503;
    out.innerHTML = `<div class="banner ${refused ? "warn" : "danger"}"><span class="b-ico">${refused ? "!" : "x"}</span><div><b>${refused ? "Lane refused to answer" : "Request failed"}</b><div class="s">${esc(e.message)}</div>${refused ? '<div class="hint">Official intents fail closed: no verified evidence means no answer, and the refusal is audited.</div>' : ""}</div></div>`;
  }
}

/* -------------------------------------------------------------------- audit */

async function renderAudit() {
  loading("audit trail");
  let data;
  try { data = await api("/api/audit?limit=100"); } catch (e) { setView(errBanner(e)); return; }
  const chain = data.chain || {};
  setView(`
    <div class="banner ${chain.ok ? "ok" : "danger"}"><span class="b-ico">${chain.ok ? "ok" : "!"}</span><div><b>Hash chain ${chain.ok ? "intact" : "BROKEN at seq " + chain.broken_at}</b><div class="s">${esc(chain.events)} events${chain.head ? " - head " + esc(chain.head.slice(0, 24)) + "..." : ""}</div></div></div>
    <div class="card"><header><h2>Recent events</h2></header><div class="body" style="padding:0">
      <table><thead><tr><th>Seq</th><th>Event</th><th>Actor</th><th>Hash</th><th>Time</th></tr></thead><tbody>
        ${(data.events || []).map((e) => `<tr><td class="num">${esc(e.seq)}</td><td>${esc(e.event)}</td><td class="mono">${esc(e.actor || "-")}</td><td class="mono">${esc((e.hash || "").slice(0, 16))}</td><td class="mono">${esc(fmtTime(e.created_at))}</td></tr>`).join("")}
      </tbody></table>
    </div></div>`);
}

/* ------------------------------------------------------------------ routing */

async function renderRouting() {
  loading("routing");
  let lanes, models;
  try { [lanes, models] = await Promise.all([api("/api/routing/lanes"), api("/api/routing/models")]); } catch (e) { setView(errBanner(e)); return; }
  setView(`
    <div class="split">
      <div class="card"><header><h2>Retrieval lanes</h2></header><div class="body" style="padding:0">
        <table><thead><tr><th>Intent</th><th>Lane</th><th>Fail closed</th><th>Rationale</th></tr></thead><tbody>
          ${lanes.routes.map((r) => `<tr><td>${esc(r.intent)}</td><td>${r.lane === "ragflow" ? chipLane("official") : chipLane("advisory")}</td><td>${chipBool(!!r.fail_closed)}</td><td class="s">${esc(r.rationale || "")}</td></tr>`).join("")}
        </tbody></table>
      </div></div>
      <div class="card"><header><h2>Model routing</h2></header><div class="body" style="padding:0">
        <table><thead><tr><th>Function</th><th>Provider</th><th>Model</th><th>Temp</th></tr></thead><tbody>
          ${models.routes.map((r) => `<tr><td>${esc(r.fn)}</td><td><span class="chip ${r.provider === "moonshot" ? "draft" : "approved"}">${esc(r.provider)}</span></td><td class="mono">${esc(r.model)}</td><td class="num">${esc(r.temperature)}</td></tr>`).join("")}
        </tbody></table>
      </div></div>
    </div>
    <div class="banner"><span class="b-ico">i</span><div><b>Producer / checker separation.</b> Authoring functions run on Moonshot; verification functions run on DeepSeek at temperature 0. A checker function can never be moved to the producer provider, and an official intent can never be demoted to the advisory lane.</div></div>`);
}

/* ------------------------------------------------------------------ clients */

async function renderClients() {
  loading("machine clients");
  let scopes;
  try { scopes = await api("/api/machine-scopes"); } catch (e) { setView(errBanner(e)); return; }
  setView(`
    <div class="card"><header><h2>Register a machine client</h2></header><div class="body">
      <label class="field"><span>Name</span><input id="c-name" placeholder="ragflow-ingest"></label>
      <div><span class="hint">Scopes</span><div class="row" id="scope-list">${scopes.scopes.map((s) => `<label class="chip"><input type="checkbox" value="${esc(s)}" style="width:auto;margin-right:5px">${esc(s)}</label>`).join("")}</div></div>
      <div class="row"><button class="btn" id="c-create">Create client</button></div>
      <div class="banner"><span class="b-ico">i</span><div>Machine clients authenticate with client credentials and act with <b>capability scopes only</b> - never a role. They cannot approve or sign. The secret is shown once.</div></div>
      <div id="c-out"></div>
    </div></div>`);
  document.getElementById("c-create").addEventListener("click", async () => {
    const name = document.getElementById("c-name").value.trim();
    const chosen = Array.from(document.querySelectorAll("#scope-list input:checked")).map((i) => i.value);
    if (!name || !chosen.length) { toast("Name and at least one scope are required", "err"); return; }
    try {
      const res = await api("/api/clients", { method: "POST", body: JSON.stringify({ name, scopes: chosen }) });
      document.getElementById("c-out").innerHTML = `<div class="banner ok"><span class="b-ico">ok</span><div><b>Client created.</b> Copy the secret now - it is stored only as a hash.<div class="pre" style="margin-top:8px">client_id: ${esc(res.client_id)}\nclient_secret: ${esc(res.client_secret)}\nscopes: ${esc((res.scopes || []).join(", "))}</div></div></div>`;
    } catch (e) { toast(e.message, "err"); }
  });
}

/* --------------------------------------------------------------- bootstrap */

const VIEWS = {
  overview: { title: "Overview", render: renderOverview },
  registry: { title: "Document Registry", render: renderRegistry },
  author: { title: "Author Document", render: renderAuthor },
  certificates: { title: "Certificates", render: renderCertificates },
  assistant: { title: "Knowledge Assistant", render: renderAssistant },
  audit: { title: "Audit Trail", render: renderAudit },
  routing: { title: "Routing & Models", render: renderRouting },
  clients: { title: "Machine Clients", render: renderClients },
};

async function boot() {
  try { state.me = await api("/api/me"); }
  catch (e) {
    if (e.status === 401) return renderLogin(e);
    document.getElementById("view").innerHTML = errBanner(e, "Studio unavailable");
    return;
  }
  return enterStudio();
}

/* Login gate: the studio key is exchanged for a signed HttpOnly cookie. */
function renderLogin(lastError) {
  setView(`
    <div class="card" style="max-width:440px;margin:60px auto">
      <header><h2>Sign in</h2></header>
      <div class="body">
        <p class="hint">${esc(lastError && lastError.message ? lastError.message : "Authentication required.")}</p>
        <label class="field"><span>Studio key</span><input id="login-key" type="password" autocomplete="current-password" placeholder="studio key"></label>
        <div class="row" style="margin-top:12px"><button class="btn" id="login-go">Sign in</button></div>
        <div id="login-err" class="hint" style="color:#a12a2a"></div>
      </div>
    </div>`);
  const go = async () => {
    const key = document.getElementById("login-key").value;
    if (!key) return;
    try {
      await api("/api/session", { method: "POST", body: JSON.stringify({ key }) });
      state.me = await api("/api/me");
      enterStudio();
    } catch (err) {
      document.getElementById("login-err").textContent = err.status === 401 ? "Invalid key." : err.message;
    }
  };
  document.getElementById("login-go").addEventListener("click", go);
  document.getElementById("login-key").addEventListener("keydown", (ev) => { if (ev.key === "Enter") go(); });
}

async function enterStudio() {
  const conn = document.getElementById("conn");
  conn.textContent = state.me.name + " (" + (state.me.role || state.me.kind) + ")";
  conn.className = "conn ok";
  document.getElementById("me-btn").addEventListener("click", () => toast("kind=" + state.me.kind + " role=" + (state.me.role || "-") + " capabilities=" + state.me.capabilities.join(", ")));
  try {
    const [reg, certs] = await Promise.all([api("/api/registry?limit=200"), api("/api/certificates").catch(() => ({ documents: [] }))]);
    state.registry = reg.documents || [];
    state.certificates = certs.documents || [];
  } catch { /* views surface their own errors */ }
  const h = await api("/api/health").catch(() => null);
  if (h) document.getElementById("lane-badge").innerHTML = `<span class="dot ${h.official_lane ? "on" : "off"}"></span>official <span class="dot ${h.advisory_lane ? "on" : "off"}"></span>advisory`;
  document.getElementById("global-search").addEventListener("input", (e) => {
    state.search = e.target.value;
    if (state.view !== "registry") go("registry"); else renderRegistry();
  });
  go("overview");
}

document.addEventListener("DOMContentLoaded", boot);
if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
