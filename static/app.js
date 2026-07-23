const state = {
    people: [],
    selected: null,
    dashboard: null,
    filters: { query: "", department: "", status: "" },
};

const elements = {
    metrics: document.querySelector("#metrics"),
    departmentChart: document.querySelector("#departmentChart"),
    upcomingList: document.querySelector("#upcomingList"),
    asOfDate: document.querySelector("#asOfDate"),
    peopleTable: document.querySelector("#peopleTable"),
    emptyState: document.querySelector("#emptyState"),
    personPanel: document.querySelector("#personPanel"),
    searchInput: document.querySelector("#searchInput"),
    departmentFilter: document.querySelector("#departmentFilter"),
    statusFilter: document.querySelector("#statusFilter"),
    dialog: document.querySelector("#personDialog"),
    form: document.querySelector("#personForm"),
    dialogTitle: document.querySelector("#dialogTitle"),
    timeOffEditor: document.querySelector("#timeOffEditor"),
    toast: document.querySelector("#toast"),
    dataStatus: document.querySelector("#dataStatus"),
};

function node(tag, className = "", text = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
}

async function request(path, options = {}) {
    const response = await fetch(path, {
        ...options,
        headers: options.body ? { "Content-Type": "application/json" } : {},
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The request could not be completed.");
    return payload;
}

function showToast(message, error = false) {
    elements.toast.textContent = message;
    elements.toast.classList.toggle("error", error);
    elements.toast.hidden = false;
    window.clearTimeout(showToast.timeout);
    showToast.timeout = window.setTimeout(() => {
        elements.toast.hidden = true;
    }, 3200);
}

function formatDate(value, options = {}) {
    if (!value) return "Not set";
    return new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: options.short ? "short" : "long",
        day: "numeric",
        timeZone: "UTC",
    }).format(new Date(`${value}T00:00:00Z`));
}

function initials(person) {
    return `${person.first_name?.[0] || ""}${person.last_name?.[0] || ""}`.toUpperCase();
}

function statusClass(value) {
    return value.toLowerCase().replaceAll(" ", "-");
}

function metricCard(label, value, detail) {
    const card = node("article", "metric-card");
    card.append(node("span", "", label), node("strong", "", String(value)), node("small", "", detail));
    return card;
}

function renderDashboard() {
    const data = state.dashboard;
    if (!data) return;
    const summary = data.summary;
    elements.metrics.replaceChildren(
        metricCard("People", summary.total || 0, "Across all departments"),
        metricCard("Active", summary.active || 0, "Available roster"),
        metricCard("On leave", summary.on_leave || 0, "Current status"),
        metricCard("Avg. capacity", `${summary.average_capacity || 0}h`, "Per person each week"),
    );
    elements.asOfDate.textContent = `As of ${formatDate(data.as_of)}`;

    const maximum = Math.max(...data.departments.map((item) => item.value), 1);
    const bars = data.departments.map((item) => {
        const row = node("div", "bar-row");
        const label = node("span", "", item.label);
        const track = node("div", "bar-track");
        const fill = node("div", "bar-fill");
        fill.style.width = `${(item.value / maximum) * 100}%`;
        track.append(fill);
        row.append(label, track, node("strong", "", String(item.value)));
        return row;
    });
    elements.departmentChart.replaceChildren(...bars);

    if (!data.upcoming_time_off.length) {
        elements.upcomingList.replaceChildren(node("p", "muted", "No scheduled time off in the next 30 days."));
        return;
    }
    elements.upcomingList.replaceChildren(...data.upcoming_time_off.slice(0, 5).map((item) => {
        const row = node("button", "schedule-item");
        row.type = "button";
        row.dataset.personId = item.person_id;
        row.append(
            node("strong", "", item.person_name),
            node("span", `status-pill ${statusClass(item.status)}`, item.status),
            node("small", "", `${item.category} | ${formatDate(item.start_date, { short: true })} to ${formatDate(item.end_date, { short: true })}`),
        );
        return row;
    }));
}

function renderPeople() {
    elements.emptyState.hidden = state.people.length > 0;
    elements.peopleTable.replaceChildren(...state.people.map((person) => {
        const row = node("tr", person.id === state.selected?.id ? "selected" : "");
        row.dataset.personId = person.id;

        const identityCell = node("td");
        const identity = node("div", "person-cell");
        const avatar = node("span", "avatar", initials(person));
        const names = node("div");
        names.append(node("strong", "", person.full_name), node("small", "", person.job_title));
        identity.append(avatar, names);
        identityCell.append(identity);

        const department = node("td", "", person.department);
        const mode = node("td", "", person.work_mode);
        const capacity = node("td", "", `${person.weekly_capacity}h / week`);
        const status = node("td");
        status.append(node("span", `status-pill ${statusClass(person.status)}`, person.status));
        row.append(identityCell, department, mode, capacity, status);
        return row;
    }));
}

function detailItem(label, value) {
    const item = node("div", "detail-item");
    item.append(node("span", "", label), node("strong", "", value || "Not set"));
    return item;
}

function renderPerson() {
    const person = state.selected;
    if (!person) return;

    const header = node("div", "profile-header");
    const identity = node("div", "profile-identity");
    const names = node("div");
    names.append(node("h3", "", person.full_name), node("p", "", person.job_title));
    identity.append(node("span", "avatar", initials(person)), names);
    const actions = node("div", "profile-actions");
    const edit = node("button", "button secondary", "Edit");
    edit.type = "button";
    edit.dataset.action = "edit";
    const remove = node("button", "button danger", "Remove");
    remove.type = "button";
    remove.dataset.action = "remove";
    actions.append(edit, remove);
    header.append(identity, actions);

    const body = node("div", "profile-body");
    const details = node("div", "detail-grid");
    details.append(
        detailItem("Department", person.department),
        detailItem("Status", person.status),
        detailItem("Email", person.email),
        detailItem("Location", person.location),
        detailItem("Work mode", person.work_mode),
        detailItem("Employment", person.employment_type),
        detailItem("Start date", formatDate(person.start_date, { short: true })),
        detailItem("Capacity", `${person.weekly_capacity} hours / week`),
    );
    body.append(details);

    const skills = node("section", "detail-section");
    skills.append(node("h4", "", "Skills"));
    const tags = node("div", "tag-list");
    const skillValues = person.skills_list.length ? person.skills_list : ["No skills listed"];
    tags.append(...skillValues.map((value) => node("span", "skill-tag", value)));
    skills.append(tags);
    body.append(skills);

    const timeOff = node("section", "detail-section");
    timeOff.append(node("h4", "", "Time off"));
    const list = node("div", "time-off-list");
    if (person.time_off.length) {
        list.append(...person.time_off.map((period) => {
            const item = node("div", "time-off-item");
            item.append(
                node("strong", "", period.category),
                node("span", `status-pill ${statusClass(period.status)}`, period.status),
                node("small", "", `${formatDate(period.start_date, { short: true })} to ${formatDate(period.end_date, { short: true })}`),
            );
            return item;
        }));
    } else {
        list.append(node("p", "muted", "No time off recorded."));
    }
    timeOff.append(list);
    body.append(timeOff);

    if (person.notes) {
        const notes = node("section", "detail-section");
        notes.append(node("h4", "", "Notes"), node("p", "muted", person.notes));
        body.append(notes);
    }

    elements.personPanel.replaceChildren(header, body);
    renderPeople();
}

async function selectPerson(personId) {
    const payload = await request(`/api/people/${personId}`);
    state.selected = payload.person;
    renderPerson();
}

async function loadDashboard() {
    state.dashboard = await request("/api/dashboard");
    renderDashboard();
}

async function loadPeople(preferredId = state.selected?.id) {
    const params = new URLSearchParams(state.filters);
    const payload = await request(`/api/people?${params}`);
    state.people = payload.people;
    renderPeople();
    const available = state.people.find((person) => person.id === preferredId);
    if (available) await selectPerson(available.id);
    else if (state.people.length) await selectPerson(state.people[0].id);
    else {
        state.selected = null;
        elements.personPanel.replaceChildren(node("div", "panel-placeholder", "No matching profile selected."));
    }
}

async function refreshAll(preferredId) {
    elements.dataStatus.textContent = "Refreshing...";
    await Promise.all([loadDashboard(), loadPeople(preferredId)]);
    elements.dataStatus.textContent = "Demo data";
}

function addTimeOffRow(period = {}) {
    const row = node("div", "time-off-row");

    const categoryLabel = node("label", "", "Category");
    const category = node("select", "time-off-category");
    ["Vacation", "Personal", "Medical", "Other"].forEach((value) => {
        const option = node("option", "", value);
        option.selected = value === (period.category || "Vacation");
        category.append(option);
    });
    categoryLabel.append(category);

    const startLabel = node("label", "", "Start date");
    const start = node("input", "time-off-start");
    start.type = "date";
    start.required = true;
    start.value = period.start_date || "";
    startLabel.append(start);

    const endLabel = node("label", "", "End date");
    const end = node("input", "time-off-end");
    end.type = "date";
    end.required = true;
    end.value = period.end_date || "";
    endLabel.append(end);

    const statusLabel = node("label", "", "Status");
    const status = node("select", "time-off-status");
    ["Pending", "Approved", "Declined"].forEach((value) => {
        const option = node("option", "", value);
        option.selected = value === (period.status || "Pending");
        status.append(option);
    });
    statusLabel.append(status);

    const remove = node("button", "button danger remove-period", "X");
    remove.type = "button";
    remove.setAttribute("aria-label", "Remove time off period");
    row.append(categoryLabel, startLabel, endLabel, statusLabel, remove);
    elements.timeOffEditor.append(row);
}

function openPersonForm(person = null) {
    elements.form.reset();
    elements.timeOffEditor.replaceChildren();
    elements.dialogTitle.textContent = person ? "Edit person" : "Add person";
    elements.form.elements.id.value = person?.id || "";
    if (person) {
        [
            "first_name", "last_name", "email", "job_title", "department", "employment_type",
            "work_mode", "location", "status", "start_date", "weekly_capacity", "skills", "notes",
        ].forEach((field) => {
            elements.form.elements[field].value = person[field] ?? "";
        });
        person.time_off.forEach(addTimeOffRow);
    } else {
        elements.form.elements.department.value = "Product";
        elements.form.elements.employment_type.value = "Full-time";
        elements.form.elements.work_mode.value = "Hybrid";
        elements.form.elements.location.value = "Central Hub";
        elements.form.elements.status.value = "Active";
        elements.form.elements.weekly_capacity.value = "40";
        elements.form.elements.start_date.value = new Date().toISOString().slice(0, 10);
    }
    elements.dialog.showModal();
}

function collectForm() {
    const formData = new FormData(elements.form);
    const payload = Object.fromEntries(formData.entries());
    payload.weekly_capacity = Number(payload.weekly_capacity);
    payload.time_off = [...elements.timeOffEditor.querySelectorAll(".time-off-row")].map((row) => ({
        category: row.querySelector(".time-off-category").value,
        start_date: row.querySelector(".time-off-start").value,
        end_date: row.querySelector(".time-off-end").value,
        status: row.querySelector(".time-off-status").value,
    }));
    delete payload.id;
    return payload;
}

elements.peopleTable.addEventListener("click", (event) => {
    const row = event.target.closest("tr[data-person-id]");
    if (row) selectPerson(Number(row.dataset.personId)).catch((error) => showToast(error.message, true));
});

elements.upcomingList.addEventListener("click", (event) => {
    const item = event.target.closest("[data-person-id]");
    if (item) selectPerson(Number(item.dataset.personId)).catch((error) => showToast(error.message, true));
});

elements.personPanel.addEventListener("click", async (event) => {
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (action === "edit") openPersonForm(state.selected);
    if (action === "remove" && state.selected) {
        const confirmed = window.confirm(`Remove ${state.selected.full_name} from this demo?`);
        if (!confirmed) return;
        try {
            await request(`/api/people/${state.selected.id}`, { method: "DELETE" });
            state.selected = null;
            await refreshAll();
            showToast("Demo record removed.");
        } catch (error) {
            showToast(error.message, true);
        }
    }
});

let searchTimer;
elements.searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
        state.filters.query = elements.searchInput.value.trim();
        loadPeople().catch((error) => showToast(error.message, true));
    }, 220);
});

[elements.departmentFilter, elements.statusFilter].forEach((filter) => {
    filter.addEventListener("change", () => {
        state.filters.department = elements.departmentFilter.value;
        state.filters.status = elements.statusFilter.value;
        loadPeople().catch((error) => showToast(error.message, true));
    });
});

document.querySelector("#refreshButton").addEventListener("click", () => {
    refreshAll().then(() => showToast("Dashboard refreshed.")).catch((error) => showToast(error.message, true));
});
document.querySelector("#addButton").addEventListener("click", () => openPersonForm());
document.querySelector("#addTimeOffButton").addEventListener("click", () => addTimeOffRow());
document.querySelector("#closeDialogButton").addEventListener("click", () => elements.dialog.close());
document.querySelector("#cancelButton").addEventListener("click", () => elements.dialog.close());

elements.timeOffEditor.addEventListener("click", (event) => {
    const button = event.target.closest(".remove-period");
    if (button) button.closest(".time-off-row").remove();
});

elements.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!elements.form.reportValidity()) return;
    const id = Number(elements.form.elements.id.value || 0);
    try {
        const payload = await request(id ? `/api/people/${id}` : "/api/people", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(collectForm()),
        });
        elements.dialog.close();
        await refreshAll(payload.person.id);
        showToast(id ? "Demo record updated." : "Demo record created.");
    } catch (error) {
        showToast(error.message, true);
    }
});

refreshAll().catch((error) => {
    elements.dataStatus.textContent = "Unavailable";
    showToast(error.message, true);
});
