const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadFrontend() {
    const sandbox = {
        window: {},
        document: {
            addEventListener() {},
            querySelector() { return null; },
            getElementById() { return null; }
        },
        localStorage: {
            getItem() { return null; },
            setItem() {},
            removeItem() {}
        },
        fetch: async () => {
            throw new Error("network not expected in utility tests");
        },
        console
    };
    vm.runInNewContext(fs.readFileSync("script.js", "utf8"), sandbox, {
        filename: "script.js"
    });
    return sandbox.window.studyTracker;
}

test("formats local dates without UTC day shifts", () => {
    const frontend = loadFrontend();
    assert.match(frontend.todayISO(), /^\d{4}-\d{2}-\d{2}$/);
    assert.equal(frontend.displayDate("2026-11-04"), "Wed Nov 04 2026");
});
