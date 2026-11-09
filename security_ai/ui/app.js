(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const state = {snapshot: null, selected: null, historyKey: "", report: null,
    evidence: null, pendingJob: null};
  const labels = {
    completed: "Completed", partial: "Partial", failed: "Failed", cancelled: "Cancelled",
    rejected: "Rejected", running: "Running", ready: "Ready"
  };
  const classes = {completed: "good", partial: "warn", failed: "bad", cancelled: "warn",
    rejected: "bad", running: "active", ready: ""};
  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function badge(status, text) {
    return element("span", text || labels[status] || status, "badge " + (classes[status] || ""));
  }
  function date(value) {
    return value ? new Date(value).toLocaleString([], {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
    }) : "Not started";
  }
  async function api(path, options = {}) {
    const response = await fetch(path, options);
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "Request failed");
    return body;
  }
  function showError(message) {
    $("request-error").textContent = message;
    $("request-error").hidden = !message;
  }
  function renderProject(project) {
    if ($("roadmap-list").children.length) return;
    const names = {lab: "Ready", engine: "HTTP ready", model: "Next",
      dashboard: "Local UI", training: "Not started", pilot: "Not started"};
    for (const phase of project.phases) {
      const item = element("li", undefined, "phase " + phase.status);
      const top = element("div", undefined, "phase-top");
      top.append(element("span", phase.title, "phase-title"),
        badge(phase.status === "ready" ? "completed" : phase.status === "partial" ? "partial" : "ready",
          names[phase.id] || phase.status));
      item.append(top, element("p", phase.detail));
      $("roadmap-list").append(item);
    }
    $("next-step").textContent = project.next_step;
  }
  function renderJob(snapshot) {
    const job = snapshot.jobs[snapshot.jobs.length - 1];
    const active = Boolean(snapshot.active_job);
    $("run-button").disabled = active;
    $("fixture").disabled = active;
    $("request-limit").disabled = active;
    $("cancel-button").hidden = !active;
    if (!job) return;
    $("run-status").textContent = labels[job.status] || job.status;
    $("run-status").className = "badge " + (classes[job.status] || "");
    $("run-message").textContent = active
      ? "Assessing " + (job.current_fixture || "controlled") + " lab · " +
        job.runs.length + " of " + job.total_runs + " reports saved."
      : (labels[job.status] || job.status) + " · " + job.runs.length + " of " +
        job.total_runs + " reports saved. Only the selected lab scenario was assessed.";
    $("run-count").textContent = job.current_fixture ? job.current_fixture + " lab" : "Preparing";
    const currentEvents = job.events.filter(event => event.fixture === job.current_fixture);
    const reached = new Set(currentEvents.map(event => event.stage));
    document.querySelectorAll("[data-stage]").forEach(node => {
      const stage = node.dataset.stage;
      node.classList.toggle("seen", reached.has(stage));
      node.classList.toggle("current", active && job.stage === stage);
    });
    const log = $("event-log");
    const signature = job.id + ":" + job.events.length + ":" + job.status;
    if (log.dataset.signature !== signature) {
      log.dataset.signature = signature;
      log.replaceChildren();
      for (const event of job.events.slice(-30)) {
        const item = element("li");
        const time = new Date(event.at).toLocaleTimeString([], {hour12:false});
        const detail = event.method
          ? event.method + " " + event.path + " → " + event.status + " · " + event.actor
          : event.message || (event.stage === "finished" ? "Report saved · " + event.status
            : ({validate:"Validate authorization", prepare:"Prepare test sessions",
              collect:"Collect observations", verify:"Verify independent controls",
              report:"Export sanitized report"}[event.stage] || event.stage));
        item.append(element("span", time, "event-time"), element("span", detail));
        log.append(item);
      }
      if (!log.children.length) log.append(element("li", "Preparing the local lab…", "empty-event"));
      log.scrollTop = log.scrollHeight;
    }
  }
  function renderHistory(snapshot) {
    const key = JSON.stringify(snapshot.reports) + state.selected +
      JSON.stringify(snapshot.jobs.map(job => job.runs));
    if (key === state.historyKey) return;
    state.historyKey = key;
    const history = $("history");
    history.replaceChildren();
    $("empty-history").hidden = snapshot.reports.length > 0;
    $("history-count").textContent = snapshot.reports.length + " saved";
    const fixtureNames = new Map();
    for (const job of snapshot.jobs) for (const run of job.runs)
      fixtureNames.set(run.assessment_id, run.fixture);
    for (const report of snapshot.reports) {
      const row = element("tr");
      if (report.assessment_id === state.selected) row.className = "selected-row";
      const name = element("td");
      const fixture = fixtureNames.get(report.assessment_id);
      name.append(element("span", fixture ? fixture + " invoice lab" : "Invoice assessment", "assessment-label"),
        element("span", date(report.finished_at), "assessment-time"));
      const status = element("td"); status.append(badge(report.status));
      const action = element("td");
      const review = element("button", "Review", "review-button");
      review.type = "button";
      review.setAttribute("aria-label", "Review assessment " + report.assessment_id);
      review.addEventListener("click", () => selectReport(report.assessment_id));
      action.append(review);
      row.append(name, status, element("td", String(report.findings)),
        element("td", String(report.requests)), action);
      history.append(row);
    }
  }
  function setTab(name) {
    for (const tab of document.querySelectorAll("[data-tab]")) {
      const selected = tab.dataset.tab === name;
      tab.classList.toggle("active", selected);
      tab.setAttribute("aria-selected", String(selected));
      $(tab.dataset.tab + "-panel").hidden = !selected;
    }
  }
  function renderReport() {
    const report = state.report;
    $("report-placeholder").hidden = true;
    $("report-content").hidden = false;
    $("report-status").hidden = false;
    $("report-status").textContent = labels[report.status] || report.status;
    $("report-status").className = "badge " + (classes[report.status] || "");
    $("report-target").textContent = report.target_url || "No target tested";
    $("report-date").textContent = date(report.finished_at);
    $("report-summary").replaceChildren();
    for (const [value, label] of [[report.findings.length, "Confirmed findings"],
      [report.usage.requests, "Requests"], [report.usage.duration_seconds.toFixed(2) + "s", "Elapsed"],
      [report.usage.model_tokens, "Model tokens"]]) {
      const metric = element("div");
      metric.append(element("div", String(value), "summary-value"), element("div", label, "summary-label"));
      $("report-summary").append(metric);
    }
    const incomplete = report.status !== "completed";
    $("report-outcome").className = "outcome" + (incomplete ? " incomplete" : "");
    $("report-outcome").textContent = incomplete
      ? "Assessment incomplete. An empty finding list is not a clean result; review coverage and errors."
      : report.findings.length ? "Confirmed behavior supported by independent controls."
        : "No confirmed findings in this tested scenario. Review coverage before drawing conclusions.";
    $("finding-list").replaceChildren();
    for (const finding of report.findings) {
      const card = element("div", undefined, "finding");
      card.append(badge("partial", finding.severity), badge("completed", finding.verification),
        element("h3", finding.title), element("p", finding.observed_behavior));
      $("finding-list").append(card);
    }
    const evidence = $("evidence-panel");
    evidence.replaceChildren(element("p", "Sanitized tool observations. Credentials and session values are omitted.", "evidence-intro"));
    for (const observation of state.evidence.observations || []) {
      const detail = element("details");
      detail.append(element("summary", observation.request.method + " " +
        new URL(observation.request.url).pathname + " · " + observation.request.actor +
        " · HTTP " + observation.response.status),
        element("pre", JSON.stringify(observation, null, 2)));
      evidence.append(detail);
    }
    if (!(state.evidence.observations || []).length) evidence.append(element("p", "No target observations were recorded."));
    const fix = $("fix-panel");
    fix.replaceChildren();
    for (const finding of report.findings)
      fix.append(element("h3", finding.title), element("p", finding.recommendation));
    if (!report.findings.length) fix.append(element("p", incomplete
      ? "No verified fix can be recommended from this incomplete assessment."
      : "No fix was proposed for this scenario. No confirmed vulnerability was reported."));
    const coverage = $("coverage-panel");
    coverage.replaceChildren();
    for (const check of report.coverage.checks) {
      const item = element("div", undefined, "coverage-item");
      item.append(badge(check.status === "tested" ? "completed" : "partial", check.status),
        element("p", check.detail));
      coverage.append(item);
    }
    const limits = element("ul", undefined, "limit-list");
    for (const limit of report.coverage.limitations) limits.append(element("li", limit));
    coverage.append(limits);
    for (const error of report.errors) coverage.append(element("p", error.code + ": " + error.message, "coverage-item"));
    const base = "/api/reports/" + encodeURIComponent(report.assessment_id);
    $("download-report").href = base + "/report/download";
    $("download-evidence").href = base + "/evidence/download";
  }
  async function selectReport(identifier) {
    const previous = state.selected;
    state.selected = identifier;
    try {
      const base = "/api/reports/" + encodeURIComponent(identifier);
      const [report, evidence] = await Promise.all([api(base + "/report"), api(base + "/evidence")]);
      if (state.selected !== identifier) return;
      state.report = report; state.evidence = evidence;
      renderReport();
      if (state.snapshot) renderHistory(state.snapshot);
    } catch (error) {
      state.selected = previous;
      showError(error.message);
    }
  }
  async function refresh() {
    try {
      const snapshot = await api("/api/state");
      state.snapshot = snapshot;
      if ($("request-error").textContent.startsWith("Dashboard connection:")) showError("");
      $("connection-state").textContent = "Local engine · AI not connected";
      renderProject(snapshot.project);
      renderJob(snapshot);
      renderHistory(snapshot);
      const pending = snapshot.jobs.find(job => job.id === state.pendingJob);
      if (pending?.runs.length) {
        state.pendingJob = null;
        await selectReport(pending.runs[0].assessment_id);
      } else if (!state.selected && snapshot.reports.length) {
        await selectReport(snapshot.reports[0].assessment_id);
      }
    } catch (error) {
      $("connection-state").textContent = "Disconnected · check terminal";
      showError("Dashboard connection: " + error.message);
    }
  }
  async function mutate(path, body) {
    if (!state.snapshot) throw new Error("Wait for the dashboard to connect.");
    return api(path, {method:"POST", headers:{"Content-Type":"application/json",
      "X-Dashboard-Token":state.snapshot.csrf_token}, body:JSON.stringify(body)});
  }
  $("run-form").addEventListener("submit", async event => {
    event.preventDefault();
    showError("");
    $("run-button").disabled = true;
    try {
      const job = await mutate("/api/jobs", {fixture:$("fixture").value,
        max_requests:Number($("request-limit").value)});
      state.pendingJob = job.job_id;
      await refresh();
    } catch (error) { showError(error.message); $("run-button").disabled = false; }
  });
  $("cancel-button").addEventListener("click", async () => {
    try {
      if (state.snapshot?.active_job) {
        await mutate("/api/jobs/" + state.snapshot.active_job + "/cancel", {});
        $("run-message").textContent = "Cancellation requested; the worker is stopping.";
      }
    } catch (error) { showError(error.message); }
  });
  document.querySelectorAll("[data-tab]").forEach(tab =>
    tab.addEventListener("click", () => setTab(tab.dataset.tab)));
  (async function poll() {
    await refresh();
    setTimeout(poll, state.snapshot?.active_job ? 350 : 1800);
  })();
})();
