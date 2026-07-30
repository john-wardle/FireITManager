const cacheKey = "fireit-mobile-cache-v1";
const pendingKey = "fireit-mobile-pending-v1";

const state = {
    online: false,
    incident: null,
    camps: [],
    devices: [],
    links: [],
    templates: [],
    runs: [],
    pending: [],
    activeView: "overview",
    activeRunId: null,
    searchText: ""
};

const guides = [
    {
        title: "Link Outage",
        body: "Scope the outage, check power and cable path, verify VLAN or route, then record workaround or escalation."
    },
    {
        title: "Slow Network",
        body: "Separate LAN symptoms from WAN symptoms, check load sources, retest after each change, and record measured impact."
    },
    {
        title: "No Internet",
        body: "Confirm scope, check upstream WAN or satellite, verify local DNS/DHCP/gateway, then record vendor or escalation status."
    }
];

const docs = [
    {
        title: "Daily Health Handoff",
        body: "Record WAN state, critical device state, user symptoms, open blockers, and next operational-period follow-up."
    },
    {
        title: "Backup / Export",
        body: "Run the local export, verify the file exists, record the storage location, and keep a transfer copy when demobilizing."
    },
    {
        title: "Demobilization",
        body: "Confirm inventory, teardown sequence, retained services, final export, and receiving party for equipment and records."
    }
];

const contacts = [
    {
        title: "ITSS Lead",
        body: "Use the assigned incident ITSS lead or local-admin user until incident-local authentication is added."
    },
    {
        title: "COML / COMT",
        body: "Coordinate radio cache, communications dependencies, and shared power/network paths through the assigned COML or COMT."
    },
    {
        title: "Logistics",
        body: "Escalate power, workspace, cabling safety, supplies, and equipment movement through logistics."
    }
];

document.addEventListener("DOMContentLoaded", async () => {
    bindNavigation();
    bindActions();
    loadLocalState();
    render();
    await refreshData();
    window.setInterval(refreshData, 30000);

    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/mobile/service-worker.js").catch(() => {});
    }

    window.addEventListener("online", () => {
        setOnlineState(true);
        syncPendingRuns();
    });
    window.addEventListener("offline", () => setOnlineState(false));
});

function bindNavigation() {
    document.querySelectorAll(".tab").forEach((button) => {
        button.addEventListener("click", () => {
            state.activeView = button.dataset.view;
            render();
        });
    });
}

function bindActions() {
    document.getElementById("refresh-button").addEventListener("click", refreshData);
    document.getElementById("sync-button").addEventListener("click", syncPendingRuns);
    document.getElementById("global-search").addEventListener("input", (event) => {
        state.searchText = event.target.value;
        renderSearch();
    });
}

async function refreshData() {
    try {
        const [health, incident, camps, devices, links, templates, runs] = await Promise.all([
            readJson("/health"),
            readJson("/api/incident-summary", true),
            readJson("/api/camps"),
            readJson("/api/devices"),
            readJson("/api/links"),
            readJson("/api/checklist-templates"),
            readJson("/api/checklist-runs")
        ]);

        state.incident = incident;
        state.camps = camps;
        state.devices = devices;
        state.links = links;
        state.templates = templates.filter((item) => item.status !== "archived" && item.status !== "disabled");
        state.runs = mergeLocalRuns(runs, state.runs);
        setOnlineState(health.status === "Healthy");
        saveLocalState();
        render();
        await syncPendingRuns();
    } catch (error) {
        setOnlineState(false);
        showToast("Using cached field data.");
        render();
    }
}

async function readJson(path, allowNotFound = false) {
    const response = await fetch(path, { cache: "no-store" });
    if (allowNotFound && response.status === 404) {
        return null;
    }

    if (!response.ok) {
        throw new Error(`${path} failed with ${response.status}`);
    }

    return response.json();
}

function setOnlineState(isOnline) {
    state.online = isOnline && navigator.onLine !== false;
    const pill = document.getElementById("connection-pill");
    const text = document.getElementById("connection-text");
    pill.classList.toggle("online", state.online && state.pending.length === 0);
    pill.classList.toggle("pending", state.online && state.pending.length > 0);
    pill.classList.toggle("offline", !state.online);
    text.textContent = !state.online
        ? "Offline"
        : state.pending.length > 0
            ? `${state.pending.length} pending`
            : "Online";
}

function loadLocalState() {
    const cached = parseJson(localStorage.getItem(cacheKey), null);
    if (cached) {
        state.incident = cached.incident ?? null;
        state.camps = cached.camps ?? [];
        state.devices = cached.devices ?? [];
        state.links = cached.links ?? [];
        state.templates = cached.templates ?? [];
        state.runs = cached.runs ?? [];
    }

    state.pending = parseJson(localStorage.getItem(pendingKey), []);
}

function saveLocalState() {
    localStorage.setItem(cacheKey, JSON.stringify({
        incident: state.incident,
        camps: state.camps,
        devices: state.devices,
        links: state.links,
        templates: state.templates,
        runs: state.runs,
        cachedAtUtc: new Date().toISOString()
    }));
    localStorage.setItem(pendingKey, JSON.stringify(state.pending));
    setOnlineState(state.online);
}

function render() {
    renderNavigation();
    renderIncident();
    renderOverview();
    renderSearch();
    renderTemplates();
    renderRuns();
    renderGuides();
}

function renderNavigation() {
    document.querySelectorAll(".tab").forEach((button) => {
        button.classList.toggle("active", button.dataset.view === state.activeView);
    });
    document.querySelectorAll(".view").forEach((view) => {
        view.classList.toggle("active", view.id === `view-${state.activeView}`);
    });
}

function renderIncident() {
    const title = document.getElementById("incident-title");
    title.textContent = state.incident
        ? `${state.incident.incidentNumber || "Incident"} - ${state.incident.name || "Unnamed"}`
        : "Incident Field Tool";
}

function renderOverview() {
    document.getElementById("camp-count").textContent = state.camps.length.toString();
    document.getElementById("device-count").textContent = state.devices.length.toString();
    document.getElementById("link-count").textContent = state.links.length.toString();
    document.getElementById("open-run-count").textContent = state.runs.filter((run) => !isComplete(run.status)).length.toString();

    const campList = document.getElementById("camp-list");
    campList.innerHTML = state.camps.length === 0
        ? emptyText("No camps loaded.")
        : state.camps.map((camp) => listItem(
            camp.name ?? camp.title ?? camp.id,
            camp.status,
            joinDetails([camp.campType, camp.addressOrDirections, camp.notes])
        )).join("");

    const linkList = document.getElementById("link-status-list");
    linkList.innerHTML = state.links.length === 0
        ? emptyText("No links loaded.")
        : state.links.slice(0, 10).map((link) => listItem(
            link.label || `${link.sourceRef || "Source"} -> ${link.destinationRef || "Destination"}`,
            link.status,
            joinDetails([link.linkCategory, link.linkType, link.notes])
        )).join("");

    const deviceList = document.getElementById("device-list");
    deviceList.innerHTML = state.devices.length === 0
        ? emptyText("No devices loaded.")
        : state.devices.slice(0, 24).map((device) => listItem(
            device.hostname || device.id,
            device.status,
            joinDetails([device.deviceType, device.manufacturer, device.model, device.serialNumber, device.assetId, device.notes])
        )).join("");
}

function renderSearch() {
    const input = document.getElementById("global-search");
    if (document.activeElement !== input) {
        input.value = state.searchText;
    }

    const target = document.getElementById("search-results");
    const text = state.searchText.trim().toLowerCase();
    if (!text) {
        target.innerHTML = emptyText("Enter search text to find incident records.");
        return;
    }

    const items = []
        .concat(state.camps.map((item) => searchResult("Camp", item.name, item.status, item)))
        .concat(state.devices.map((item) => searchResult("Device", item.hostname, item.status, item)))
        .concat(state.links.map((item) => searchResult("Link", item.label || `${item.sourceRef} -> ${item.destinationRef}`, item.status, item)))
        .concat(state.templates.map((item) => searchResult("Checklist", item.title, item.status, item)));

    const matches = items.filter((item) => item.search.includes(text)).slice(0, 50);
    target.innerHTML = matches.length === 0
        ? emptyText("No matching incident records.")
        : matches.map((item) => listItem(`${item.type}: ${item.title}`, item.status, item.detail)).join("");
}

function renderTemplates() {
    document.getElementById("template-count").textContent = `${state.templates.length} available`;
    const target = document.getElementById("template-list");

    target.innerHTML = state.templates.length === 0
        ? emptyText("No checklist templates loaded.")
        : state.templates.map((template) => {
            const steps = normalizeSteps(template.steps);
            return `
                <article class="template-item">
                    <div>
                        <div class="list-title">
                            <span>${escapeHtml(template.title)}</span>
                            ${badge(template.status)}
                        </div>
                        <p class="detail-text">${escapeHtml(joinDetails([template.templateType, template.versionLabel, `${steps.length} steps`]))}</p>
                    </div>
                    <div class="template-actions">
                        <button class="primary" type="button" data-start-template="${escapeHtml(template.id)}">Start Run</button>
                    </div>
                </article>`;
        }).join("");

    target.querySelectorAll("[data-start-template]").forEach((button) => {
        button.addEventListener("click", () => startRun(button.dataset.startTemplate));
    });
}

function renderRuns() {
    const runList = document.getElementById("run-list");
    const ordered = [...state.runs].sort((left, right) =>
        (right.updatedAtUtc || right.startedAtUtc || "").localeCompare(left.updatedAtUtc || left.startedAtUtc || ""));

    runList.innerHTML = ordered.length === 0
        ? emptyText("No checklist runs started.")
        : ordered.map((run) => {
            const template = findTemplate(run.templateId);
            const steps = normalizeSteps(run.steps);
            const done = steps.filter((step) => step.completed).length;
            return `
                <article class="run-item">
                    <div class="list-title">
                        <span>${escapeHtml(template?.title ?? run.templateId)}</span>
                        ${badge(run.status)}
                    </div>
                    <p class="detail-text">${done} of ${steps.length} steps complete | Version ${run.version ?? 1}</p>
                    <div class="run-actions">
                        <button type="button" data-open-run="${escapeHtml(run.id)}">Open</button>
                    </div>
                </article>`;
        }).join("");

    runList.querySelectorAll("[data-open-run]").forEach((button) => {
        button.addEventListener("click", () => {
            state.activeRunId = button.dataset.openRun;
            renderRunDetail();
        });
    });

    renderRunDetail();
}

function renderRunDetail() {
    const target = document.getElementById("run-detail");
    const run = state.runs.find((item) => item.id === state.activeRunId) ?? state.runs[0];
    if (!run) {
        target.classList.add("hidden");
        target.innerHTML = "";
        return;
    }

    state.activeRunId = run.id;
    target.classList.remove("hidden");
    const template = findTemplate(run.templateId);
    const steps = normalizeSteps(run.steps);
    const done = steps.filter((step) => step.completed).length;

    target.innerHTML = `
        <div class="section-heading">
            <div>
                <h2>${escapeHtml(template?.title ?? run.templateId)}</h2>
                <span class="muted">${done} of ${steps.length} steps complete</span>
            </div>
            ${badge(run.status)}
        </div>
        <label class="field-label" for="run-notes">Run notes</label>
        <textarea id="run-notes">${escapeHtml(run.notes ?? "")}</textarea>
        <div class="step-list">
            ${steps.map((step, index) => renderStep(step, index)).join("")}
        </div>
        <div class="run-actions">
            <button id="save-run-button" class="primary" type="button">Save Progress</button>
            <button id="complete-run-button" class="danger" type="button">Complete And Sync</button>
        </div>`;

    target.querySelector("#run-notes").addEventListener("input", (event) => {
        run.notes = event.target.value;
        touchRun(run, false);
    });
    target.querySelectorAll("[data-step-check]").forEach((input) => {
        input.addEventListener("change", () => {
            const step = steps[Number(input.dataset.stepCheck)];
            step.completed = input.checked;
            step.completedAtUtc = input.checked ? new Date().toISOString() : null;
            run.steps = steps;
            touchRun(run, false);
            renderRuns();
        });
    });
    target.querySelectorAll("[data-step-note]").forEach((input) => {
        input.addEventListener("input", () => {
            steps[Number(input.dataset.stepNote)].notes = input.value;
            run.steps = steps;
            touchRun(run, false);
        });
    });
    target.querySelectorAll("[data-step-blocker]").forEach((input) => {
        input.addEventListener("change", () => {
            steps[Number(input.dataset.stepBlocker)].blocked = input.checked;
            run.status = input.checked ? "blocked" : deriveRunStatus(steps);
            run.steps = steps;
            touchRun(run, false);
            renderRuns();
        });
    });
    target.querySelectorAll("[data-step-followup]").forEach((input) => {
        input.addEventListener("input", () => {
            steps[Number(input.dataset.stepFollowup)].followUpTask = input.value;
            run.steps = steps;
            touchRun(run, false);
        });
    });
    target.querySelectorAll("[data-step-photo]").forEach((input) => {
        input.addEventListener("change", () => attachPhotos(run, steps, Number(input.dataset.stepPhoto), input.files));
    });
    target.querySelector("#save-run-button").addEventListener("click", () => saveRun(run, false));
    target.querySelector("#complete-run-button").addEventListener("click", () => saveRun(run, true));
}

function renderStep(step, index) {
    const photos = Array.isArray(step.photos) ? step.photos : [];
    return `
        <article class="step-item">
            <div class="step-header">
                <input class="step-check" type="checkbox" ${step.completed ? "checked" : ""} data-step-check="${index}" aria-label="Complete step">
                <div>
                    <h3>${escapeHtml(step.title || `Step ${index + 1}`)}</h3>
                    <div class="step-meta">
                        ${step.expectedResult ? `<p><strong>Expected:</strong> ${escapeHtml(step.expectedResult)}</p>` : ""}
                        ${step.troubleshootingHint ? `<p><strong>Hint:</strong> ${escapeHtml(step.troubleshootingHint)}</p>` : ""}
                        ${step.requiredNote ? `<p class="muted">Note required</p>` : ""}
                        ${step.requiredPhoto ? `<p class="muted">Photo required</p>` : ""}
                    </div>
                </div>
            </div>
            <label class="field-label" for="step-note-${index}">Step notes</label>
            <textarea id="step-note-${index}" data-step-note="${index}">${escapeHtml(step.notes ?? "")}</textarea>
            <label class="inline-toggle">
                <input type="checkbox" ${step.blocked ? "checked" : ""} data-step-blocker="${index}">
                Blocker
            </label>
            <label class="field-label" for="step-followup-${index}">Follow-up task</label>
            <input id="step-followup-${index}" class="field-input" type="text" value="${escapeHtml(step.followUpTask ?? "")}" data-step-followup="${index}">
            <label class="field-label" for="step-photo-${index}">Photo attachment</label>
            <input id="step-photo-${index}" class="field-input" type="file" accept="image/*" capture="environment" multiple data-step-photo="${index}">
            <div class="photo-list">${photos.length === 0 ? "No photos attached" : photos.map((photo) => escapeHtml(photo.name)).join(", ")}</div>
        </article>`;
}

function renderGuides() {
    document.getElementById("guide-list").innerHTML = guides.map(renderGuide).join("");
    document.getElementById("doc-list").innerHTML = docs.map(renderGuide).join("");
    document.getElementById("contact-list").innerHTML = contacts.map(renderGuide).join("");
}

function renderGuide(item) {
    return `
        <article class="list-item">
            <h3>${escapeHtml(item.title)}</h3>
            <p class="detail-text">${escapeHtml(item.body)}</p>
        </article>`;
}

async function startRun(templateId) {
    const template = findTemplate(templateId);
    if (!template) {
        showToast("Template is not available.");
        return;
    }

    const run = {
        id: crypto.randomUUID(),
        incidentId: state.incident?.id ?? "local",
        templateId: template.id,
        status: "in-progress",
        targetType: "",
        targetId: null,
        assigneePersonId: null,
        startedAtUtc: new Date().toISOString(),
        completedAtUtc: null,
        steps: normalizeSteps(template.steps),
        notes: "",
        createdAtUtc: new Date().toISOString(),
        updatedAtUtc: new Date().toISOString(),
        version: 1,
        localOnly: true
    };

    state.runs.unshift(run);
    state.activeRunId = run.id;
    state.activeView = "active";
    queueCreate(run);
    saveLocalState();
    render();
    showToast("Checklist run started.");

    if (state.online) {
        await syncPendingRuns();
    }
}

async function saveRun(run, complete) {
    const steps = normalizeSteps(run.steps);
    run.status = complete ? "completed" : deriveRunStatus(steps);
    run.completedAtUtc = complete ? new Date().toISOString() : null;
    touchRun(run, true);
    queueProgress(run);
    saveLocalState();
    renderRuns();

    if (state.online) {
        await syncPendingRuns();
    } else {
        showToast("Saved locally. Sync will retry when connected.");
    }
}

function touchRun(run, rerender) {
    run.updatedAtUtc = new Date().toISOString();
    const index = state.runs.findIndex((item) => item.id === run.id);
    if (index >= 0) {
        state.runs[index] = run;
    }

    saveLocalState();
    if (rerender) {
        renderRuns();
    }
}

function queueCreate(run) {
    if (!state.pending.some((item) => item.kind === "create" && item.id === run.id)) {
        state.pending.push({ kind: "create", id: run.id });
    }
    queueProgress(run);
}

function queueProgress(run) {
    state.pending = state.pending.filter((item) => !(item.kind === "progress" && item.id === run.id));
    state.pending.push({ kind: "progress", id: run.id });
}

async function syncPendingRuns() {
    if (!state.online || state.pending.length === 0) {
        saveLocalState();
        return;
    }

    const remaining = [];
    for (const item of state.pending) {
        const run = state.runs.find((candidate) => candidate.id === item.id);
        if (!run) {
            continue;
        }

        try {
            if (item.kind === "create") {
                const saved = await postJson("/api/checklist-runs", {
                    id: run.id,
                    templateId: run.templateId,
                    status: run.status,
                    targetType: run.targetType,
                    targetId: run.targetId,
                    assigneePersonId: run.assigneePersonId,
                    startedAtUtc: run.startedAtUtc,
                    completedAtUtc: run.completedAtUtc,
                    notes: run.notes
                });
                applySavedRun(saved);
            } else {
                const saved = await putJson(`/api/checklist-runs/${encodeURIComponent(run.id)}/progress`, {
                    status: run.status,
                    steps: normalizeSteps(run.steps),
                    notes: run.notes,
                    completedAtUtc: run.completedAtUtc,
                    expectedVersion: run.version
                });
                applySavedRun(saved);
            }
        } catch (error) {
            remaining.push(item);
        }
    }

    state.pending = remaining;
    saveLocalState();
    render();
    showToast(state.pending.length === 0 ? "Mobile work synced." : "Some mobile work is still pending.");
}

async function postJson(path, body) {
    return sendJson("POST", path, body);
}

async function putJson(path, body) {
    return sendJson("PUT", path, body);
}

async function sendJson(method, path, body) {
    const response = await fetch(path, {
        method,
        headers: {
            "Content-Type": "application/json",
            "X-FireIT-User": "mobile-field-user"
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(`${method} ${path} failed with ${response.status}`);
    }

    return response.json();
}

function applySavedRun(saved) {
    const run = { ...saved, localOnly: false };
    const index = state.runs.findIndex((item) => item.id === run.id);
    if (index >= 0) {
        state.runs[index] = run;
    } else {
        state.runs.unshift(run);
    }
}

async function attachPhotos(run, steps, index, files) {
    const step = steps[index];
    step.photos = Array.isArray(step.photos) ? step.photos : [];
    for (const file of Array.from(files ?? [])) {
        step.photos.push(await readPhoto(file));
    }

    run.steps = steps;
    touchRun(run, true);
}

function readPhoto(file) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve({
            name: file.name,
            type: file.type,
            size: file.size,
            capturedAtUtc: new Date().toISOString(),
            dataUrl: reader.result
        });
        reader.readAsDataURL(file);
    });
}

function normalizeSteps(steps) {
    const source = Array.isArray(steps)
        ? steps
        : Array.isArray(steps?.steps)
            ? steps.steps
            : [];

    return source.map((step, index) => ({
        id: step.id ?? `step-${index + 1}`,
        title: step.title ?? `Step ${index + 1}`,
        expectedResult: step.expectedResult ?? step.expected_result ?? "",
        troubleshootingHint: step.troubleshootingHint ?? step.troubleshooting_hint ?? "",
        requiredNote: Boolean(step.requiredNote ?? step.required_note),
        requiredPhoto: Boolean(step.requiredPhoto ?? step.required_photo),
        completed: Boolean(step.completed),
        completedAtUtc: step.completedAtUtc ?? step.completed_at_utc ?? null,
        completedBy: step.completedBy ?? step.completed_by ?? "",
        notes: step.notes ?? "",
        blocked: Boolean(step.blocked),
        followUpTask: step.followUpTask ?? step.follow_up_task ?? "",
        photos: Array.isArray(step.photos) ? step.photos : []
    }));
}

function deriveRunStatus(steps) {
    if (steps.some((step) => step.blocked)) {
        return "blocked";
    }

    return steps.length > 0 && steps.every((step) => step.completed)
        ? "completed"
        : "in-progress";
}

function mergeLocalRuns(serverRuns, currentRuns) {
    const byId = new Map();
    serverRuns.forEach((run) => byId.set(run.id, { ...run, localOnly: false }));
    currentRuns.filter((run) => run.localOnly || state.pending.some((item) => item.id === run.id))
        .forEach((run) => byId.set(run.id, run));
    return Array.from(byId.values());
}

function findTemplate(id) {
    return state.templates.find((template) => template.id === id);
}

function isComplete(status) {
    return ["complete", "completed", "done"].includes((status ?? "").toLowerCase());
}

function searchResult(type, title, status, item) {
    return {
        type,
        title: title || item.id,
        status: status || "unknown",
        detail: joinDetails(Object.values(item).filter((value) => typeof value === "string")),
        search: Object.values(item)
            .flatMap((value) => Array.isArray(value) ? value : [value])
            .filter((value) => value !== null && value !== undefined)
            .join(" ")
            .toLowerCase()
    };
}

function listItem(title, status, detail) {
    return `
        <article class="list-item">
            <div class="list-title">
                <span>${escapeHtml(title || "Untitled")}</span>
                ${badge(status)}
            </div>
            ${detail ? `<p class="detail-text">${escapeHtml(detail)}</p>` : ""}
        </article>`;
}

function badge(status) {
    const value = (status || "unknown").toString();
    return `<span class="status-badge ${escapeHtml(value.toLowerCase())}">${escapeHtml(value)}</span>`;
}

function emptyText(text) {
    return `<p class="detail-text">${escapeHtml(text)}</p>`;
}

function joinDetails(values) {
    return values.filter((value) => value !== null && value !== undefined && value.toString().trim() !== "")
        .map((value) => value.toString().trim())
        .join(" | ");
}

function parseJson(value, fallback) {
    try {
        return value ? JSON.parse(value) : fallback;
    } catch {
        return fallback;
    }
}

function escapeHtml(value) {
    return (value ?? "").toString()
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

let toastTimer;
function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.remove("hidden");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.add("hidden"), 2800);
}
