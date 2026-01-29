/*********************************************************
  INITIAL SETUP – CREATE DATA IF NOT EXISTS
*********************************************************/

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

/*********************************************************
  TODAY PAGE LOGIC (INPUT PAGE)
*********************************************************/

function loadTodayPage() {
    const data = getData();
    const subjectSelect = document.getElementById("subjectSelect");
    subjectSelect.innerHTML = "";

    // Load subjects
    for (let subject in data.subjects) {
        let option = document.createElement("option");
        option.value = subject;
        option.textContent = subject;
        subjectSelect.appendChild(option);
    }

    // If no subject exists, create one example
    if (subjectSelect.options.length === 0) {
        data.subjects["General Study"] = { history: {}, targets: {} };
        saveData(data);
        loadTodayPage();
        return;
    }

    loadTodaySummary();
}

function saveTodayData() {
    const data = getData();
    const subject = document.getElementById("subjectSelect").value;
    const target = Number(document.getElementById("todayTarget").value);
    const actual = Number(document.getElementById("actualStudy").value);
    const today = getToday();

    if (!data.subjects[subject]) {
        data.subjects[subject] = { history: {}, targets: {} };
    }

    data.subjects[subject].targets[today] = target;
    data.subjects[subject].history[today] = actual;

    // STREAK LOGIC
    if (data.lastDate !== today) {
        if (actual >= 0.8 * target) {
            data.streak += 1;
        } else {
            data.streak = 0;
        }
        data.lastDate = today;
    }

    saveData(data);
    loadTodaySummary();
}

function loadTodaySummary() {
    const data = getData();
    const today = getToday();
    const subject = document.getElementById("subjectSelect").value;

    const target = data.subjects[subject]?.targets[today] || 0;
    const actual = data.subjects[subject]?.history[today] || 0;
    const completion = target ? ((actual / target) * 100).toFixed(1) : 0;
    const difference = target - actual;

    document.getElementById("summaryTarget").textContent = target;
    document.getElementById("summaryActual").textContent = actual;
    document.getElementById("summaryCompletion").textContent = completion + "%";
    document.getElementById("summaryDifference").textContent = difference;
}

/*********************************************************
  HOME PAGE LOGIC
*********************************************************/

function loadHomePage() {
    const data = getData();
    const today = getToday();

    let todayTarget = 0;
    let tasks = [];

    for (let subject in data.subjects) {
        let target = data.subjects[subject].targets[today];
        if (target) {
            todayTarget += target;
            tasks.push(subject + " (" + target + ")");
        }
    }

    document.getElementById("streakValue").textContent = data.streak + " days";
    document.getElementById("todayTarget").textContent =
        todayTarget ? todayTarget : "No target set";

    const list = document.getElementById("todayTasks");
    list.innerHTML = "";

    if (tasks.length === 0) {
        list.innerHTML = "<li>No tasks added</li>";
    } else {
        tasks.forEach(task => {
            let li = document.createElement("li");
            li.textContent = task;
            list.appendChild(li);
        });
    }
}

/*********************************************************
  PROGRESS PAGE LOGIC
*********************************************************/

function loadProgressPage() {
    const data = getData();

    let totalStudy = 0;
    let totalTarget = 0;

    const subjectDiv = document.getElementById("subjectProgress");
    subjectDiv.innerHTML = "";

    for (let subject in data.subjects) {
        let subStudy = 0;
        let subTarget = 0;

        for (let day in data.subjects[subject].history) {
            subStudy += data.subjects[subject].history[day];
            subTarget += data.subjects[subject].targets[day] || 0;
        }

        totalStudy += subStudy;
        totalTarget += subTarget;

        let percent = subTarget ? ((subStudy / subTarget) * 100).toFixed(1) : 0;

        subjectDiv.innerHTML += `
            <p><strong>${subject}:</strong> ${subStudy} / ${subTarget} (${percent}%)</p>
        `;
    }

    document.getElementById("totalStudy").textContent = totalStudy;
    document.getElementById("totalTarget").textContent = totalTarget;
    document.getElementById("overallCompletion").textContent =
        totalTarget ? ((totalStudy / totalTarget) * 100).toFixed(1) + "%" : "0%";
}

/*********************************************************
  IDEAL STUDENT PAGE LOGIC
*********************************************************/

function loadIdealPage() {
    const data = getData();
    const today = getToday();

    let yourToday = 0;
    let idealToday = 0;
    let yourTotal = 0;
    let idealTotal = 0;

    for (let subject in data.subjects) {
        for (let day in data.subjects[subject].targets) {
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

/*********************************************************
  ANALYSIS PAGE LOGIC
*********************************************************/

function loadAnalysisPage() {
    const data = getData();

    let totalStudy = 0;
    let totalTarget = 0;
    let subjectTotals = {};

    for (let subject in data.subjects) {
        subjectTotals[subject] = 0;
        for (let day in data.subjects[subject].history) {
            totalStudy += data.subjects[subject].history[day];
            subjectTotals[subject] += data.subjects[subject].history[day];
            totalTarget += data.subjects[subject].targets[day] || 0;
        }
    }

    let strongest = "-";
    let weakest = "-";
    let max = -1, min = Infinity;

    for (let s in subjectTotals) {
        if (subjectTotals[s] > max) {
            max = subjectTotals[s];
            strongest = s;
        }
        if (subjectTotals[s] < min) {
            min = subjectTotals[s];
            weakest = s;
        }
    }

    document.getElementById("analysisTotalStudy").textContent = totalStudy;
    document.getElementById("analysisTotalTarget").textContent = totalTarget;
    document.getElementById("analysisCompletion").textContent =
        totalTarget ? ((totalStudy / totalTarget) * 100).toFixed(1) + "%" : "0%";

    document.getElementById("analysisStreak").textContent = data.streak;

    const daysTracked = Object.values(data.subjects)[0]
        ? Object.keys(Object.values(data.subjects)[0].history).length
        : 0;

    document.getElementById("analysisAverage").textContent =
        daysTracked ? (totalStudy / daysTracked).toFixed(2) : 0;

    document.getElementById("strongestSubject").textContent = strongest;
    document.getElementById("weakestSubject").textContent = weakest;

    document.getElementById("reflectionText").textContent =
        data.streak >= 3
            ? "You show good consistency. Keep maintaining your streak."
            : "Your consistency needs improvement. Try to meet daily targets.";
}

/*********************************************************
  FORECAST PAGE LOGIC
*********************************************************/

function loadForecastPage() {
    const data = getData();

    let totalStudy = 0;
    let totalTarget = 0;
    let allDays = new Set();

    for (let subject in data.subjects) {
        for (let day in data.subjects[subject].history) {
            totalStudy += data.subjects[subject].history[day];
            totalTarget += data.subjects[subject].targets[day] || 0;
            allDays.add(day);
        }
    }

    let remaining = totalTarget - totalStudy;
    let average = allDays.size ? (totalStudy / allDays.size) : 0;
    let daysNeeded = average ? Math.ceil(remaining / average) : 0;

    document.getElementById("completedStudy").textContent = totalStudy;
    document.getElementById("requiredStudy").textContent = totalTarget;
    document.getElementById("remainingStudy").textContent = remaining;
    document.getElementById("averageDaily").textContent = average.toFixed(2);
    document.getElementById("totalDays").textContent = allDays.size;
    document.getElementById("estimatedDays").textContent =
        daysNeeded > 0 ? daysNeeded + " days" : "Not enough data";
}
/********************************************************/