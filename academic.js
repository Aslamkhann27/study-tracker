/* Phase 2 academic frontend. Uses the authenticated api()/apiList() helpers from script.js. */
(() => {
    "use strict";

    const $ = (id) => document.getElementById(id);
    const message = (id, text, error = false) => {
        const node = $(id);
        if (!node) return;
        node.textContent = text;
        node.classList.toggle("error", error);
        node.classList.toggle("success", !error && Boolean(text));
    };
    const make = (tag, text, className) => {
        const node = document.createElement(tag);
        if (text !== undefined && text !== null) node.textContent = text;
        if (className) node.className = className;
        return node;
    };
    const addOption = (select, value, label) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    };

    async function initProfile() {
        try {
            const profile = await api("/profile/");
            ["course", "branch", "academic_session", "semester", "daily_available_hours"].forEach((key) => {
                if ($(key) && profile[key] !== undefined && profile[key] !== null) $(key).value = profile[key];
            });
        } catch (error) {
            message("profileMessage", error.message, true);
        }
        $("profileForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = {
                course: $("course").value.trim(),
                branch: $("branch").value.trim(),
                academic_session: $("academic_session").value.trim(),
                semester: Number($("semester").value),
                daily_available_hours: Number($("daily_available_hours").value)
            };
            const button = $("profileSave");
            button.disabled = true;
            try {
                await api("/profile/", { method: "PUT", body: JSON.stringify(payload) });
                message("profileMessage", "Academic profile saved successfully.");
            } catch (error) {
                message("profileMessage", error.message, true);
            } finally {
                button.disabled = false;
            }
        });
    }

    async function fillSubjectSelect(select, emptyLabel = "Select a subject") {
        const subjects = await apiList("/subjects/");
        select.innerHTML = "";
        addOption(select, "", emptyLabel);
        subjects.forEach((subject) => addOption(select, subject.id, subject.name));
        return subjects;
    }

    async function initSyllabus() {
        const subjectSelect = $("syllabusSubject");
        const chapterSelect = $("chapterSelect");
        let subjects = await fillSubjectSelect(subjectSelect);
        if (!subjects.length) {
            message("syllabusSubjectMessage", "Add a subject from the Today page before creating chapters.", true);
        }

        async function loadChapters(preferredId = "") {
            const subjectId = subjectSelect.value;
            chapterSelect.innerHTML = "";
            $("chapterList").replaceChildren();
            $("topicList").replaceChildren();
            addOption(chapterSelect, "", "Select a chapter");
            if (!subjectId) return;
            const chapters = await apiList("/chapters/?subject=" + encodeURIComponent(subjectId));
            chapters.forEach((chapter) => addOption(chapterSelect, chapter.id, chapter.title));
            if (preferredId && chapters.some((item) => String(item.id) === String(preferredId))) {
                chapterSelect.value = String(preferredId);
            }
            chapters.forEach((chapter) => {
                const row = make("div", null, "list-row");
                const details = make("div");
                details.append(make("strong", chapter.title));
                details.append(make("small", (chapter.topic_count ?? 0) + " topics"));
                row.append(details);
                const remove = make("button", "Delete", "danger-button compact-button");
                remove.type = "button";
                remove.addEventListener("click", async () => {
                    if (!confirm("Delete this chapter and its topics?")) return;
                    try {
                        await api("/chapters/" + chapter.id + "/", { method: "DELETE" });
                        await loadChapters();
                        message("chapterMessage", "Chapter deleted.");
                    } catch (error) {
                        message("chapterMessage", error.message, true);
                    }
                });
                row.append(remove);
                $("chapterList").append(row);
            });
            await loadTopics();
        }

        async function loadTopics() {
            const chapterId = chapterSelect.value;
            const box = $("topicList");
            box.replaceChildren();
            if (!chapterId) return;
            const topics = await apiList("/topics/?chapter=" + encodeURIComponent(chapterId));
            if (!topics.length) {
                box.append(make("p", "No topics added to this chapter yet."));
                return;
            }
            topics.forEach((topic) => {
                const row = make("div", null, "list-row topic-row");
                const details = make("div");
                details.append(make("strong", topic.title));
                if (topic.description) details.append(make("small", topic.description));
                row.append(details);
                const status = document.createElement("select");
                status.setAttribute("aria-label", "Status for " + topic.title);
                [
                    ["not_started", "Not Started"],
                    ["in_progress", "In Progress"],
                    ["completed", "Completed"],
                    ["needs_revision", "Needs Revision"]
                ].forEach(([value, label]) => addOption(status, value, label));
                status.value = topic.status;
                status.addEventListener("change", async () => {
                    status.disabled = true;
                    try {
                        await api("/topics/" + topic.id + "/", {
                            method: "PATCH", body: JSON.stringify({ status: status.value })
                        });
                        message("topicMessage", "Topic status updated.");
                    } catch (error) {
                        status.value = topic.status;
                        message("topicMessage", error.message, true);
                    } finally {
                        status.disabled = false;
                    }
                });
                row.append(status);
                const remove = make("button", "Delete", "danger-button compact-button");
                remove.type = "button";
                remove.addEventListener("click", async () => {
                    if (!confirm("Delete this topic?")) return;
                    try {
                        await api("/topics/" + topic.id + "/", { method: "DELETE" });
                        await loadTopics();
                        message("topicMessage", "Topic deleted.");
                    } catch (error) {
                        message("topicMessage", error.message, true);
                    }
                });
                row.append(remove);
                box.append(row);
            });
        }

        subjectSelect.addEventListener("change", () => loadChapters());
        chapterSelect.addEventListener("change", loadTopics);
        $("chapterForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!subjectSelect.value) return message("chapterMessage", "Select a subject first.", true);
            const payload = {
                subject: Number(subjectSelect.value),
                title: $("chapterTitle").value.trim(),
                description: $("chapterDescription").value.trim(),
                order: Number($("chapterOrder").value || 0)
            };
            try {
                const created = await api("/chapters/", { method: "POST", body: JSON.stringify(payload) });
                $("chapterForm").reset();
                $("chapterOrder").value = "0";
                await loadChapters(created.id);
                message("chapterMessage", "Chapter added.");
            } catch (error) {
                message("chapterMessage", error.message, true);
            }
        });
        $("topicForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!chapterSelect.value) return message("topicMessage", "Select a chapter first.", true);
            const payload = {
                chapter: Number(chapterSelect.value),
                title: $("topicTitle").value.trim(),
                description: $("topicDescription").value.trim(),
                order: Number($("topicOrder").value || 0)
            };
            try {
                await api("/topics/", { method: "POST", body: JSON.stringify(payload) });
                $("topicForm").reset();
                $("topicOrder").value = "0";
                await loadTopics();
                message("topicMessage", "Topic added.");
            } catch (error) {
                message("topicMessage", error.message, true);
            }
        });
        await loadChapters();
    }

    async function initExams() {
        await fillSubjectSelect($("examSubject"));
        async function loadExams() {
            const filter = $("examFilter").value;
            const path = "/exams/" + (filter === "all" ? "" : "?upcoming=" + filter);
            const exams = await apiList(path);
            const box = $("examList");
            box.replaceChildren();
            if (!exams.length) {
                box.append(make("p", "No exams found for this filter."));
                return;
            }
            exams.sort((a, b) => a.exam_date.localeCompare(b.exam_date));
            exams.forEach((exam) => {
                const row = make("article", null, "list-row exam-row");
                const details = make("div");
                details.append(make("strong", exam.title));
                details.append(make("small", (exam.subject_name || "Subject") + " • " + exam.exam_date));
                details.append(make("span", "Priority: " + exam.priority, "priority priority-" + exam.priority));
                if (exam.description) details.append(make("p", exam.description));
                row.append(details);
                const remove = make("button", "Delete", "danger-button compact-button");
                remove.type = "button";
                remove.addEventListener("click", async () => {
                    if (!confirm("Delete this exam?")) return;
                    try {
                        await api("/exams/" + exam.id + "/", { method: "DELETE" });
                        await loadExams();
                        message("examMessage", "Exam deleted.");
                    } catch (error) {
                        message("examMessage", error.message, true);
                    }
                });
                row.append(remove);
                box.append(row);
            });
        }

        $("examForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = {
                title: $("examTitle").value.trim(),
                subject: Number($("examSubject").value),
                exam_date: $("examDate").value,
                priority: $("examPriority").value,
                description: $("examDescription").value.trim()
            };
            try {
                await api("/exams/", { method: "POST", body: JSON.stringify(payload) });
                $("examForm").reset();
                $("examPriority").value = "medium";
                await loadExams();
                message("examMessage", "Exam added successfully.");
            } catch (error) {
                message("examMessage", error.message, true);
            }
        });
        $("examFilter").addEventListener("change", loadExams);
        await loadExams();
    }

    // Called by script.js both on initial page load and after a successful login.
    window.studyTrackerAcademicInit = async () => {
        const page = location.pathname.split("/").pop();
        const init = {
            "profile.html": initProfile,
            "syllabus.html": initSyllabus,
            "exams.html": initExams
        }[page];
        if (!init) return;
        const target = page === "profile.html" ? "profileMessage"
            : page === "syllabus.html" ? "chapterMessage" : "examMessage";
        try {
            await init();
        } catch (error) {
            message(target, error.message || "Unable to load this page.", true);
        }
    };
})();
