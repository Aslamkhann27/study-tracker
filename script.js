/* ---------------------------------------------------------
   INITIAL SETUP
--------------------------------------------------------- */

if (!localStorage.getItem("studyData")) {
    localStorage.setItem("studyData", JSON.stringify({
        subjects: {},
        streak: 0,
        lastDate: null
    }));
}

function getData() {
    return JSON.parse(localStorage.getItem("studyData"));
}

function saveData(data) {
    localStorage.setItem("studyData", JSON.stringify(data));
}

function getToday() {
    return new Date().toDateString();
}

function getOrCreateSubject(data, subject) {
    if (!data.subjects[subject]) {
        data.subjects[subject] = { history: {}, targets: {} };
    }
    return data.subjects[subject];
}

/* ---------------------------------------------------------
   TODAY PAGE
--------------------------------------------------------- */

function loadTodayPage() {
    const data = getData();
    const subjectSelect = document.getElementById("subjectSelect");
    subjectSelect.innerHTML = "";

    for (const subject of Object.keys(data.subjects).sort((a, b) => a.localeCompare(b))) {
        const option = document.createElement("option");
        option.value = subject;
        option.textContent = subject;
        subjectSelect.appendChild(option);
    }

    if (subjectSelect.options.length === 0) {
        getOrCreateSubject(data, "General Study");
        saveData(data);
        loadTodayPage();
        return;
    }

    loadTodaySummary();
}

function addSubject() {
    const input = document.getElementById("newSubjectName");
    const message = document.getElementById("subjectMessage");
    const subject = input.value.trim();

    if (!subject) {
        message.textContent = "Enter a subject name first.";
        return;
    }

    const data = getData();
    const existingSubject = Object.keys(data.subjects).find(
        name => name.toLocaleLowerCase() === subject.toLocaleLowerCase()
    );

    if (existingSubject) {
        message.textContent = "That subject is already in your list.";
        return;
    }

    getOrCreateSubject(data, subject);
    saveData(data);

    loadTodayPage();
    document.getElementById("subjectSelect").value = subject;
    loadTodaySummary();

    input.value = "";
    message.textContent = subject + " added successfully.";
}

function saveTodayData() {
    const data = getData();
    const subject = document.getElementById("subjectSelect").value;
    const targetInput = document.getElementById("todayTarget");
    const actualInput = document.getElementById("actualStudy");
    const target = Number(targetInput.value);
    const actual = Number(actualInput.value);
    const message = document.getElementById("saveMessage");

    if (!subject) {
        message.textContent = "Add or select a subject before saving.";
        return;
    }

    if (targetInput.value.trim() === "" || !Number.isFinite(target) || target <= 0) {
        message.textContent = "Enter a target greater than zero.";
        targetInput.focus();
        return;
    }

    if (actualInput.value.trim() === "" || !Number.isFinite(actual) || actual < 0) {
        message.textContent = "Enter a valid study amount (zero or more).";
        actualInput.focus();
        return;
    }

    const today = getToday();
    const subjectData = getOrCreateSubject(data, subject);
    subjectData.targets[today] = target;
    subjectData.history[today] = actual;

    // Update the streak at most once per calendar day.
    if (data.lastDate !== today) {
        data.streak = actual >= 0.8 * target ? data.streak + 1 : 0;
        data.lastDate = today;
    }

    saveData(data);
    loadTodaySummary();
    message.textContent = "Today's study data saved.";
}

function loadTodaySummary() {
    const data = getData();
    const today = getToday();
    const subjectSelect = document.getElementById("subjectSelect");
    const subject = subjectSelect.value;
    const target = data.subjects[subject]?.targets[today] ?? 0;
    const actual = data.subjects[subject]?.history[today] ?? 0;
    const completion = target > 0 ? ((actual / target) * 100).toFixed(1) : "0.0";
    const difference = target - actual;

    document.getElementById("summaryTarget").textContent = target;
    document.getElementById("summaryActual").textContent = actual;
    document.getElementById("summaryCompletion").textContent = completion + "%";
    document.getElementById("summaryDifference").textContent = difference.toFixed(2);
}

/* ---------------------------------------------------------
   HOME PAGE
--------------------------------------------------------- */

function loadHomePage() {
    const data = getData();
    const today = getToday();
    let todayTarget = 0;
    const tasks = [];

    for (const subject in data.subjects) {
        const target = data.subjects[subject].targets[today];
        if (target) {
            todayTarget += target;
            tasks.push(subject + " (" + target + ")");
        }
    }

    document.getElementById("streakValue").textContent = data.streak + " days";
    document.getElementById("todayTarget").textContent = todayTarget || "No target set";

    const list = document.getElementById("todayTasks");
    list.innerHTML = "";

    if (tasks.length === 0) {
        const item = document.createElement("li");
        item.textContent = "No tasks added";
        list.appendChild(item);
        return;
    }

    tasks.forEach(task => {
        const item = document.createElement("li");
        item.textContent = task;
        list.appendChild(item);
    });
}

/* ---------------------------------------------------------
   PROGRESS PAGE
--------------------------------------------------------- */

function loadProgressPage() {
    const data = getData();
    let totalStudy = 0;
    let totalTarget = 0;

    const subjectDiv = document.getElementById("subjectProgress");
    subjectDiv.innerHTML = "";

    for (const subject in data.subjects) {
        let subStudy = 0;
        let subTarget = 0;

        for (const day in data.subjects[subject].history) {
            subStudy += data.subjects[subject].history[day];
            subTarget += data.subjects[subject].targets[day] || 0;
        }

        totalStudy += subStudy;
        totalTarget += subTarget;

        const percent = subTarget ? ((subStudy / subTarget) * 100).toFixed(1) : "0.0";
        const row = document.createElement("p");
        const label = document.createElement("strong");
        label.textContent = subject + ": ";
        row.append(label, document.createTextNode(subStudy + " / " + subTarget + " (" + percent + "%)"));
        subjectDiv.appendChild(row);
    }

    document.getElementById("totalStudy").textContent = totalStudy;
    document.getElementById("totalTarget").textContent = totalTarget;
    document.getElementById("overallCompletion").textContent =
        totalTarget ? ((totalStudy / totalTarget) * 100).toFixed(1) + "%" : "0%";
}

/* ---------------------------------------------------------
   IDEAL STUDENT PAGE
--------------------------------------------------------- */

function loadIdealPage() {
    const data = getData();
    const today = getToday();
    let yourToday = 0;
    let idealToday = 0;
    let yourTotal = 0;
    let idealTotal = 0;

    for (const subject in data.subjects) {
        for (const day in data.subjects[subject].targets) {
            idealTotal += data.subjects[subject].targets[day];
            yourTotal += data.subjects[subject].history[day] || 0;
        }

        idealToday += data.subjects[subject].targets[today] || 0;
        yourToday += data.subjects[subject].history[today] || 0;
    }

    document.getElementById("idealToday").textContent = idealToday;
    document.getElementById("yourToday").textContent = yourToday;
    document.getElementById("todayGap").textContent = idealToday - yourToday;
    document.getElementById("idealTotal").textContent = idealTotal;
    document.getElementById("yourTotal").textContent = yourTotal;
    document.getElementById("totalGap").textContent = idealTotal - yourTotal;
    document.getElementById("interpretationText").textContent =
        yourTotal >= idealTotal
            ? "You are matching or exceeding the ideal learning pace."
            : "You are behind the ideal learning pace. Improve consistency.";
}

/* ---------------------------------------------------------
   ANALYSIS PAGE
--------------------------------------------------------- */

function loadAnalysisPage() {
    const data = getData();
    let totalStudy = 0;
    let totalTarget = 0;
    const subjectTotals = {};

    for (const subject in data.subjects) {
        subjectTotals[subject] = 0;
        for (const day in data.subjects[subject].history) {
            const studied = data.subjects[subject].history[day] || 0;
            totalStudy += studied;
            subjectTotals[subject] += studied;
            totalTarget += data.subjects[subject].targets[day] || 0;
        }
    }

    let strongest = "-";
    let weakest = "-";
    let max = -1;
    let min = Infinity;

    for (const subject in subjectTotals) {
        if (subjectTotals[subject] > max) {
            max = subjectTotals[subject];
            strongest = subject;
        }
        if (subjectTotals[subject] < min) {
            min = subjectTotals[subject];
            weakest = subject;
        }
    }

    document.getElementById("analysisTotalStudy").textContent = totalStudy;
    document.getElementById("analysisTotalTarget").textContent = totalTarget;
    document.getElementById("analysisCompletion").textContent =
        totalTarget ? ((totalStudy / totalTarget) * 100).toFixed(1) + "%" : "0%";
    document.getElementById("analysisStreak").textContent = data.streak;

    const daysTracked = new Set();
    for (const subject in data.subjects) {
        Object.keys(data.subjects[subject].history).forEach(day => daysTracked.add(day));
    }

    document.getElementById("analysisAverage").textContent =
        daysTracked.size ? (totalStudy / daysTracked.size).toFixed(2) : "0";
    document.getElementById("strongestSubject").textContent = strongest;
    document.getElementById("weakestSubject").textContent = weakest;
    document.getElementById("reflectionText").textContent =
        data.streak >= 3
            ? "You show good consistency. Keep maintaining your streak."
            : "Your consistency needs improvement. Try to meet daily targets.";
}

/* ---------------------------------------------------------
   FORECAST PAGE
--------------------------------------------------------- */

function loadForecastPage() {
    const data = getData();
    let totalStudy = 0;
    let totalTarget = 0;
    const allDays = new Set();

    for (const subject in data.subjects) {
        for (const day in data.subjects[subject].history) {
            totalStudy += data.subjects[subject].history[day];
            totalTarget += data.subjects[subject].targets[day] || 0;
            allDays.add(day);
        }
    }

    const remaining = totalTarget - totalStudy;
    const average = allDays.size ? totalStudy / allDays.size : 0;
    const daysNeeded = average > 0 ? Math.ceil(remaining / average) : 0;

    document.getElementById("completedStudy").textContent = totalStudy;
    document.getElementById("requiredStudy").textContent = totalTarget;
    document.getElementById("remainingStudy").textContent = remaining;
    document.getElementById("averageDaily").textContent = average.toFixed(2);
    document.getElementById("totalDays").textContent = allDays.size;
    document.getElementById("estimatedDays").textContent =
        daysNeeded > 0 ? daysNeeded + " days" : "Not enough data";
}
