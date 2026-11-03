/* Study Tracker frontend: Django REST API integration */
const API_BASE = (window.STUDY_API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");
const ACCESS_KEY = "studyAccessToken";
const REFRESH_KEY = "studyRefreshToken";

function getAccessToken() { return localStorage.getItem(ACCESS_KEY); }
function setTokens(data) {
    localStorage.setItem(ACCESS_KEY, data.access);
    if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
}
function clearTokens() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
}
async function refreshAccessToken() {
    const refresh = localStorage.getItem(REFRESH_KEY);
    if (!refresh) return false;
    try {
        const response = await fetch(API_BASE + "/auth/token/refresh/", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh })
        });
        if (!response.ok) throw new Error("Session expired");
        const data = await response.json();
        localStorage.setItem(ACCESS_KEY, data.access);
        if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
        return true;
    } catch (_) { clearTokens(); return false; }
}
async function api(path, options = {}, retry = true) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (getAccessToken()) headers.Authorization = "Bearer " + getAccessToken();
    const response = await fetch(API_BASE + path, { ...options, headers });
    if (response.status === 401 && retry && await refreshAccessToken()) return api(path, options, false);
    if (!response.ok) {
        let detail = "Request failed (" + response.status + ")";
        try {
            const body = await response.json();
            detail = Object.entries(body).map(([key, value]) =>
                key + ": " + (Array.isArray(value) ? value.join(" ") : typeof value === "object" ? JSON.stringify(value) : value)
            ).join(" | ") || detail;
        } catch (_) {}
        throw new Error(detail);
    }
    if (response.status === 204) return null;
    return response.json();
}
async function apiList(path) {
    const data = await api(path);
    return Array.isArray(data) ? data : (data.results || []);
}
function todayISO() {
    const now = new Date();
    return [now.getFullYear(), String(now.getMonth()+1).padStart(2,"0"), String(now.getDate()).padStart(2,"0")].join("-");
}
function displayDate(iso) {
    const [y,m,d] = iso.split("-").map(Number);
    return new Date(y, m-1, d).toDateString();
}
function getToday() { return displayDate(todayISO()); }

let currentDashboard = null;
async function loadStudyData() {
    const [subjects, entries, dashboard] = await Promise.all([
        apiList("/subjects/"), apiList("/entries/"), api("/dashboard/")
    ]);
    currentDashboard = dashboard;
    const data = { subjects: {}, streak: dashboard.streak || 0, lastDate: null };
    subjects.forEach(subject => data.subjects[subject.name] = { id: subject.id, history: {}, targets: {} });
    entries.forEach(entry => {
        const name = entry.subject_name || (subjects.find(s => s.id === entry.subject)?.name);
        if (!name) return;
        if (!data.subjects[name]) data.subjects[name] = { id: entry.subject, history: {}, targets: {} };
        const day = displayDate(entry.study_date);
        data.subjects[name].history[day] = Number(entry.actual_hours);
        data.subjects[name].targets[day] = Number(entry.target_hours);
    });
    return data;
}
function showStatus(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    if (element) { element.textContent = message; element.style.color = isError ? "#b91c1c" : "#15803d"; }
}
function mountAccountUI() {
    const nav = document.querySelector("nav");
    if (!nav || document.getElementById("accountPanel")) return;
    const panel = document.createElement("div");
    panel.id = "accountPanel";
    panel.innerHTML = `
      <div class="account-actions">
        <span id="accountStatus">Not signed in</span>
        <button type="button" id="showLogin">Log in</button>
        <button type="button" id="showRegister">Create account</button>
        <button type="button" id="logoutButton" hidden>Log out</button>
      </div>
      <form id="authForm" class="auth-form" hidden>
        <h3 id="authHeading">Log in to Study Tracker</h3>
        <label for="authUsername">Username</label><input id="authUsername" autocomplete="username" required>
        <label for="authEmail">Email (registration only)</label><input id="authEmail" type="email" autocomplete="email">
        <label for="authPassword">Password</label><input id="authPassword" type="password" autocomplete="current-password" minlength="8" required>
        <button id="authSubmit" type="submit">Log in</button>
        <button id="authCancel" type="button" class="secondary-button">Cancel</button>
        <p id="authMessage" role="status" aria-live="polite"></p>
      </form>`;
    nav.insertAdjacentElement("afterend", panel);
    let mode = "login";
    const form = document.getElementById("authForm");
    function setMode(next) {
        mode = next;
        form.hidden = false;
        document.getElementById("authHeading").textContent = next === "login" ? "Log in to Study Tracker" : "Create your account";
        document.getElementById("authEmail").hidden = next === "login";
        document.getElementById("authEmail").required = next === "register";
        document.getElementById("authSubmit").textContent = next === "login" ? "Log in" : "Create account";
        showStatus("authMessage", "");
    }
    document.getElementById("showLogin").onclick = () => setMode("login");
    document.getElementById("showRegister").onclick = () => setMode("register");
    document.getElementById("authCancel").onclick = () => { form.hidden = true; };
    document.getElementById("logoutButton").onclick = () => {
        clearTokens(); updateAccountUI(); location.reload();
    };
    form.addEventListener("submit", async event => {
        event.preventDefault();
        const username = document.getElementById("authUsername").value.trim();
        const password = document.getElementById("authPassword").value;
        const email = document.getElementById("authEmail").value.trim();
        const submit = document.getElementById("authSubmit");
        submit.disabled = true;
        try {
            if (mode === "register") {
                await api("/auth/register/", { method: "POST", body: JSON.stringify({ username, email, password }) });
            }
            const tokens = await fetch(API_BASE + "/auth/token/", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            if (!tokens.ok) throw new Error(mode === "register" ? "Account created. Please log in." : "Invalid username or password.");
            setTokens(await tokens.json());
            showStatus("authMessage", "Signed in successfully.");
            updateAccountUI();
            await loadCurrentPage();
            form.hidden = true;
        } catch (error) { showStatus("authMessage", error.message, true); }
        finally { submit.disabled = false; }
    });
    updateAccountUI();
}
function updateAccountUI() {
    const signedIn = Boolean(getAccessToken());
    const status = document.getElementById("accountStatus");
    if (status) status.textContent = signedIn ? "Signed in" : "Not signed in";
    const login = document.getElementById("showLogin");
    const register = document.getElementById("showRegister");
    const logout = document.getElementById("logoutButton");
    if (login) login.hidden = signedIn;
    if (register) register.hidden = signedIn;
    if (logout) logout.hidden = !signedIn;
}
async function requireLogin() {
    if (!getAccessToken() && !await refreshAccessToken()) {
        const status = document.getElementById("accountStatus");
        if (status) status.textContent = "Please log in to load your study data.";
        const form = document.getElementById("authForm");
        if (form) form.hidden = false;
        return false;
    }
    updateAccountUI();
    return true;
}
async function loadCurrentPage() {
    if (!await requireLogin()) return;
    const page = location.pathname.split("/").pop() || "index.html";
    const loaders = {
        "index.html": loadHomePage, "today.html": loadTodayPage,
        "progress.html": loadProgressPage, "ideal.html": loadIdealPage,
        "analysis.html": loadAnalysisPage, "forecast.html": loadForecastPage
    };
    if (loaders[page]) await loaders[page]();
}

/* TODAY */
async function loadTodayPage() {
    try {
        const data = await loadStudyData();
        const select = document.getElementById("subjectSelect");
        if (!select) return;
        const previous = select.value;
        select.innerHTML = "";
        Object.keys(data.subjects).sort((a,b)=>a.localeCompare(b)).forEach(name => {
            const option = document.createElement("option");
            option.value = name; option.textContent = name; select.appendChild(option);
        });
        if (!select.options.length) {
            const created = await api("/subjects/", { method: "POST", body: JSON.stringify({ name: "General Study" }) });
            const option = document.createElement("option");
            option.value = created.name; option.textContent = created.name; select.appendChild(option);
        } else if (previous && data.subjects[previous]) select.value = previous;
        await loadTodaySummary();
    } catch (error) { showStatus("subjectMessage", error.message, true); }
}
async function addSubject() {
    const input = document.getElementById("newSubjectName");
    const name = input.value.trim();
    if (!name) return showStatus("subjectMessage", "Enter a subject name first.", true);
    try {
        await api("/subjects/", { method: "POST", body: JSON.stringify({ name }) });
        input.value = ""; showStatus("subjectMessage", name + " added successfully.");
        await loadTodayPage();
        document.getElementById("subjectSelect").value = name;
        await loadTodaySummary();
    } catch (error) { showStatus("subjectMessage", error.message, true); }
}
async function saveTodayData() {
    const name = document.getElementById("subjectSelect").value;
    const targetInput = document.getElementById("todayTarget");
    const actualInput = document.getElementById("actualStudy");
    const target = Number(targetInput.value), actual = Number(actualInput.value);
    if (!name) return showStatus("saveMessage", "Add or select a subject before saving.", true);
    if (!targetInput.value.trim() || !Number.isFinite(target) || target <= 0)
        return showStatus("saveMessage", "Enter a target greater than zero.", true);
    if (!actualInput.value.trim() || !Number.isFinite(actual) || actual < 0)
        return showStatus("saveMessage", "Enter a valid study amount (zero or more).", true);
    try {
        const subjects = await apiList("/subjects/");
        const subject = subjects.find(item => item.name === name);
        if (!subject) throw new Error("Selected subject was not found. Refresh and try again.");
        const today = todayISO();
        const entries = await apiList("/entries/?study_date=" + today);
        const existing = entries.find(entry => entry.subject === subject.id && entry.study_date === today);
        const payload = { subject: subject.id, study_date: today, target_hours: target, actual_hours: actual };
        await api(existing ? "/entries/" + existing.id + "/" : "/entries/", {
            method: existing ? "PATCH" : "POST", body: JSON.stringify(payload)
        });
        showStatus("saveMessage", "Today's study data saved.");
        await loadTodaySummary();
    } catch (error) { showStatus("saveMessage", error.message, true); }
}
async function loadTodaySummary() {
    if (!getAccessToken()) return;
    try {
        const select = document.getElementById("subjectSelect");
        if (!select) return;
        const name = select.value;
        const subjects = await apiList("/subjects/");
        const subject = subjects.find(item => item.name === name);
        const entries = subject ? await apiList("/entries/?study_date=" + todayISO()) : [];
        const entry = entries.find(item => item.subject === subject?.id);
        const target = Number(entry?.target_hours || 0), actual = Number(entry?.actual_hours || 0);
        document.getElementById("summaryTarget").textContent = target;
        document.getElementById("summaryActual").textContent = actual;
        document.getElementById("summaryCompletion").textContent = (target ? actual / target * 100 : 0).toFixed(1) + "%";
        document.getElementById("summaryDifference").textContent = (target - actual).toFixed(2);
        if (document.getElementById("todayTarget")) document.getElementById("todayTarget").value = target || "";
        if (document.getElementById("actualStudy")) document.getElementById("actualStudy").value = entry ? actual : "";
    } catch (error) { showStatus("saveMessage", error.message, true); }
}

/* HOME */
async function loadHomePage() {
    try {
        const dashboard = await api("/dashboard/");
        document.getElementById("streakValue").textContent = dashboard.streak + " days";
        document.getElementById("todayTarget").textContent = dashboard.today.target_hours || "No target set";
        const list = document.getElementById("todayTasks");
        list.innerHTML = "";
        const entries = await apiList("/entries/?study_date=" + todayISO());
        const subjects = dashboard.subjects || [];
        entries.forEach(entry => {
            const subject = subjects.find(item => item.id === entry.subject);
            const li = document.createElement("li");
            li.textContent = (subject?.name || entry.subject_name || "Subject") + " (" + entry.target_hours + ")";
            list.appendChild(li);
        });
        if (!list.children.length) list.innerHTML = "<li>No tasks added</li>";
    } catch (error) { showStatus("accountStatus", error.message, true); }
}

/* SHARED ANALYTICS */
async function getAnalyticsData() {
    const [subjects, entries, dashboard] = await Promise.all([
        apiList("/subjects/"), apiList("/entries/"), api("/dashboard/")
    ]);
    const totals = { study: 0, target: 0, bySubject: {}, days: new Set(), todayStudy: 0, todayTarget: 0 };
    subjects.forEach(subject => totals.bySubject[subject.name] = { study: 0, target: 0 });
    entries.forEach(entry => {
        const name = subjects.find(s => s.id === entry.subject)?.name || entry.subject_name || "Other";
        const actual = Number(entry.actual_hours), target = Number(entry.target_hours);
        totals.study += actual; totals.target += target;
        if (!totals.bySubject[name]) totals.bySubject[name] = { study: 0, target: 0 };
        totals.bySubject[name].study += actual; totals.bySubject[name].target += target;
        totals.days.add(entry.study_date);
        if (entry.study_date === todayISO()) { totals.todayStudy += actual; totals.todayTarget += target; }
    });
    totals.streak = dashboard.streak || 0;
    return totals;
}
async function loadProgressPage() {
    try {
        const d = await getAnalyticsData();
        document.getElementById("totalStudy").textContent = d.study;
        document.getElementById("totalTarget").textContent = d.target;
        document.getElementById("overallCompletion").textContent = (d.target ? d.study/d.target*100 : 0).toFixed(1) + "%";
        const box = document.getElementById("subjectProgress"); box.innerHTML = "";
        Object.entries(d.bySubject).forEach(([name, values]) => {
            const row = document.createElement("p");
            const strong = document.createElement("strong"); strong.textContent = name + ": ";
            row.append(strong, document.createTextNode(values.study + " / " + values.target + " (" + (values.target ? values.study/values.target*100 : 0).toFixed(1) + "%)"));
            box.appendChild(row);
        });
        if (!box.children.length) box.textContent = "No data available";
    } catch (e) { showStatus("accountStatus", e.message, true); }
}
async function loadIdealPage() {
    try {
        const d = await getAnalyticsData();
        document.getElementById("idealToday").textContent = d.todayTarget;
        document.getElementById("yourToday").textContent = d.todayStudy;
        document.getElementById("todayGap").textContent = d.todayTarget - d.todayStudy;
        document.getElementById("idealTotal").textContent = d.target;
        document.getElementById("yourTotal").textContent = d.study;
        document.getElementById("totalGap").textContent = d.target - d.study;
        document.getElementById("interpretationText").textContent = d.study >= d.target
            ? "You are matching or exceeding the ideal learning pace."
            : "You are behind the ideal learning pace. Improve consistency.";
    } catch (e) { showStatus("accountStatus", e.message, true); }
}
async function loadAnalysisPage() {
    try {
        const d = await getAnalyticsData();
        const values = Object.entries(d.bySubject);
        const strongest = values.length ? values.reduce((a,b)=>b[1].study>a[1].study?b:a)[0] : "-";
        const weakest = values.length ? values.reduce((a,b)=>b[1].study<a[1].study?b:a)[0] : "-";
        document.getElementById("analysisTotalStudy").textContent = d.study;
        document.getElementById("analysisTotalTarget").textContent = d.target;
        document.getElementById("analysisCompletion").textContent = (d.target ? d.study/d.target*100 : 0).toFixed(1) + "%";
        document.getElementById("analysisStreak").textContent = d.streak;
        document.getElementById("analysisAverage").textContent = (d.days.size ? d.study/d.days.size : 0).toFixed(2);
        document.getElementById("strongestSubject").textContent = strongest;
        document.getElementById("weakestSubject").textContent = weakest;
        document.getElementById("reflectionText").textContent = d.streak >= 3
            ? "You show good consistency. Keep maintaining your streak."
            : "Your consistency needs improvement. Try to meet daily targets.";
    } catch (e) { showStatus("accountStatus", e.message, true); }
}
async function loadForecastPage() {
    try {
        const d = await getAnalyticsData();
        const remaining = d.target - d.study, average = d.days.size ? d.study/d.days.size : 0;
        document.getElementById("completedStudy").textContent = d.study;
        document.getElementById("requiredStudy").textContent = d.target;
        document.getElementById("remainingStudy").textContent = remaining;
        document.getElementById("averageDaily").textContent = average.toFixed(2);
        document.getElementById("totalDays").textContent = d.days.size;
        document.getElementById("estimatedDays").textContent = remaining <= 0 ? "Completed" : average > 0 ? Math.ceil(remaining/average) + " days" : "Not enough data";
    } catch (e) { showStatus("accountStatus", e.message, true); }
}

document.addEventListener("DOMContentLoaded", () => {
    mountAccountUI();
    loadCurrentPage();
});
