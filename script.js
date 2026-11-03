const STORAGE_KEY = "studyData";

function createDefaultData() {
    return {
        subjects: {},
        streak: 0,
        lastDate: null
    };
}

function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function normaliseEntries(value) {
    if (!isRecord(value)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(value)
            .filter(([key, amount]) =>
                key.trim().length > 0 &&
                Number.isFinite(amount) &&
                amount >= 0
            )
            .map(([key, amount]) => [key.trim().slice(0, 100), amount])
    );
}

function sanitiseData(value) {
    const data = createDefaultData();

    if (!isRecord(value)) {
        return data;
    }

    if (isRecord(value.subjects)) {
        for (const [subjectName, subjectValue] of Object.entries(value.subjects)) {
            const subject = subjectName.trim().slice(0, 100);
            if (!subject || !isRecord(subjectValue)) {
                continue;
            }

            data.subjects[subject] = {
                history: normaliseEntries(subjectValue.history),
                targets: normaliseEntries(subjectValue.targets)
            };
        }
    }

    if (Number.isFinite(value.streak) && value.streak >= 0) {
        data.streak = Math.floor(value.streak);
    }

    if (typeof value.lastDate === "string" && value.lastDate.length <= 100) {
        data.lastDate = value.lastDate;
    }

    return data;
}

function getElement(id) {
    return typeof document === "undefined" ? null : document.getElementById(id);
}

function setStatus(message, type = "error") {
    const status = getElement("statusMessage");
    if (!status) {
        return;
    }

    status.textContent = message;
    status.dataset.type = type;
}

function getData() {
    if (typeof localStorage === "undefined") {
        return createDefaultData();
    }

    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        const data = sanitiseData(stored ? JSON.parse(stored) : null);
        if (!stored) {
            saveData(data);
        }
        return data;
    } catch (error) {
        setStatus("Saved study data could not be read. A new empty plan is being used.");
        return createDefaultData();
    }
}

function saveData(data) {
    if (typeof localStorage === "undefined") {
        return false;
    }

    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sanitiseData(data)));
        return true;
    } catch (error) {
        setStatus("Study data could not be saved. Check available browser storage.");
        return false;
    }
}

function getToday() {
    return new Date().toDateString();
}

function getSubjectEntries(data) {
    return Object.entries(data.subjects);
}

function calculateTotals(data) {
    let totalStudy = 0;
    let totalTarget = 0;
    const allDays = new Set();
    const subjectTotals = {};

    for (const [subject, values] of getSubjectEntries(data)) {
        subjectTotals[subject] = 0;
        for (const [day, amount] of Object.entries(values.history)) {
            totalStudy += amount;
            subjectTotals[subject] += amount;
            totalTarget += values.targets[day] || 0;
            allDays.add(day);
        }
    }

    return { totalStudy, totalTarget, allDays, subjectTotals };
}

function loadTodayPage() {
    const subjectSelect = getElement("subjectSelect");
    if (!subjectSelect) {
        return;
    }

    const data = getData();
    if (Object.keys(data.subjects).length === 0) {
        data.subjects["General Study"] = { history: {}, targets: {} };
        saveData(data);
    }

    subjectSelect.replaceChildren();
    for (const subject of Object.keys(data.subjects)) {
        const option = document.createElement("option");
        option.value = subject;
        option.textContent = subject;
        subjectSelect.appendChild(option);
    }

    loadTodaySummary();
}

function saveTodayData() {
    const subjectSelect = getElement("subjectSelect");
    const targetInput = getElement("todayTarget");
    const actualInput = getElement("actualStudy");
    if (!subjectSelect || !targetInput || !actualInput) {
        return false;
    }

    const subject = subjectSelect.value.trim();
    const target = Number(targetInput.value);
    const actual = Number(actualInput.value);

    if (!subject || !Number.isFinite(target) || target < 0 ||
        !Number.isFinite(actual) || actual < 0) {
        setStatus("Enter non-negative numbers for both target and actual study.");
        return false;
    }

    const data = getData();
    const today = getToday();
    if (!data.subjects[subject]) {
        data.subjects[subject] = { history: {}, targets: {} };
    }

    data.subjects[subject].targets[today] = target;
    data.subjects[subject].history[today] = actual;

    if (data.lastDate !== today) {
        data.streak = actual >= 0.8 * target ? data.streak + 1 : 0;
        data.lastDate = today;
    }

    if (!saveData(data)) {
        return false;
    }

    setStatus("Today's study data was saved.", "success");
    loadTodaySummary();
    return true;
}

function loadTodaySummary() {
    const subjectSelect = getElement("subjectSelect");
    if (!subjectSelect) {
        return;
    }

    const data = getData();
    const today = getToday();
    const subject = subjectSelect.value;
    const values = data.subjects[subject] || { history: {}, targets: {} };
    const target = values.targets[today] || 0;
    const actual = values.history[today] || 0;
    const completion = target ? ((actual / target) * 100).toFixed(1) : "0";

    const summary = {
        summaryTarget: target,
        summaryActual: actual,
        summaryCompletion: `${completion}%`,
        summaryDifference: target - actual
    };
    for (const [id, value] of Object.entries(summary)) {
        const element = getElement(id);
        if (element) {
            element.textContent = value;
        }
    }
}

function loadHomePage() {
    const data = getData();
    const today = getToday();
    let todayTarget = 0;
    const tasks = [];

    for (const [subject, values] of getSubjectEntries(data)) {
        const target = values.targets[today];
        if (target !== undefined) {
            todayTarget += target;
            tasks.push(`${subject} (${target})`);
        }
    }

    const streak = getElement("streakValue");
    const target = getElement("todayTarget");
    const list = getElement("todayTasks");
    if (streak) {
        streak.textContent = `${data.streak} days`;
    }
    if (target) {
        target.textContent = todayTarget ? todayTarget : "No target set";
    }
    if (!list) {
        return;
    }

    list.replaceChildren();
    if (tasks.length === 0) {
        const item = document.createElement("li");
        item.textContent = "No tasks added";
        list.appendChild(item);
        return;
    }

    for (const task of tasks) {
        const item = document.createElement("li");
        item.textContent = task;
        list.appendChild(item);
    }
}

function loadProgressPage() {
    const data = getData();
    const { totalStudy, totalTarget, subjectTotals } = calculateTotals(data);
    const subjectDiv = getElement("subjectProgress");

    if (subjectDiv) {
        subjectDiv.replaceChildren();
        for (const [subject, study] of Object.entries(subjectTotals)) {
            const target = data.subjects[subject].targets;
            const subjectTarget = Object.values(target).reduce((sum, amount) => sum + amount, 0);
            const percent = subjectTarget ? ((study / subjectTarget) * 100).toFixed(1) : "0";
            const paragraph = document.createElement("p");
            const strong = document.createElement("strong");
            strong.textContent = `${subject}:`;
            paragraph.append(strong, ` ${study} / ${subjectTarget} (${percent}%)`);
            subjectDiv.appendChild(paragraph);
        }
    }

    const values = {
        totalStudy,
        totalTarget,
        overallCompletion: totalTarget ? `${((totalStudy / totalTarget) * 100).toFixed(1)}%` : "0%"
    };
    for (const [id, value] of Object.entries(values)) {
        const element = getElement(id);
        if (element) {
            element.textContent = value;
        }
    }
}

function loadIdealPage() {
    const data = getData();
    const today = getToday();
    let yourToday = 0;
    let idealToday = 0;
    let yourTotal = 0;
    let idealTotal = 0;

    for (const values of Object.values(data.subjects)) {
        for (const [day, target] of Object.entries(values.targets)) {
            idealTotal += target;
            yourTotal += values.history[day] || 0;
        }
        idealToday += values.targets[today] || 0;
        yourToday += values.history[today] || 0;
    }

    const values = {
        idealToday,
        yourToday,
        todayGap: idealToday - yourToday,
        idealTotal,
        yourTotal,
        totalGap: idealTotal - yourTotal,
        interpretationText: yourTotal >= idealTotal
            ? "You are matching or exceeding the ideal learning pace."
            : "You are behind the ideal learning pace. Improve consistency."
    };
    for (const [id, value] of Object.entries(values)) {
        const element = getElement(id);
        if (element) {
            element.textContent = value;
        }
    }
}

function loadAnalysisPage() {
    const data = getData();
    const { totalStudy, totalTarget, subjectTotals, allDays } = calculateTotals(data);
    const subjects = Object.entries(subjectTotals);
    const strongest = subjects.length ? subjects.reduce((a, b) => a[1] >= b[1] ? a : b)[0] : "-";
    const weakest = subjects.length ? subjects.reduce((a, b) => a[1] <= b[1] ? a : b)[0] : "-";
    const values = {
        analysisTotalStudy: totalStudy,
        analysisTotalTarget: totalTarget,
        analysisCompletion: totalTarget ? `${((totalStudy / totalTarget) * 100).toFixed(1)}%` : "0%",
        analysisStreak: data.streak,
        analysisAverage: allDays.size ? (totalStudy / allDays.size).toFixed(2) : "0",
        strongestSubject: strongest,
        weakestSubject: weakest,
        reflectionText: data.streak >= 3
            ? "You show good consistency. Keep maintaining your streak."
            : "Your consistency needs improvement. Try to meet daily targets."
    };
    for (const [id, value] of Object.entries(values)) {
        const element = getElement(id);
        if (element) {
            element.textContent = value;
        }
    }
}

function loadForecastPage() {
    const data = getData();
    const { totalStudy, totalTarget, allDays } = calculateTotals(data);
    const remaining = Math.max(totalTarget - totalStudy, 0);
    const average = allDays.size ? totalStudy / allDays.size : 0;
    const daysNeeded = average ? Math.ceil(remaining / average) : 0;
    const values = {
        completedStudy: totalStudy,
        requiredStudy: totalTarget,
        remainingStudy: remaining,
        averageDaily: average.toFixed(2),
        totalDays: allDays.size,
        estimatedDays: daysNeeded > 0 ? `${daysNeeded} days` : "Not enough data"
    };
    for (const [id, value] of Object.entries(values)) {
        const element = getElement(id);
        if (element) {
            element.textContent = value;
        }
    }
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
    const initialData = getData();
    if (Object.keys(initialData.subjects).length === 0) {
        initialData.subjects["General Study"] = { history: {}, targets: {} };
        saveData(initialData);
    }
}

if (typeof module !== "undefined") {
    module.exports = {
        calculateTotals,
        createDefaultData,
        sanitiseData
    };
}
