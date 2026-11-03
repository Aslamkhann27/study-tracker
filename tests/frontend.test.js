const test = require("node:test");
const assert = require("node:assert/strict");

const {
    calculateTotals,
    createDefaultData,
    sanitiseData
} = require("../script.js");

test("sanitises malformed and unsafe persisted values", () => {
    const data = sanitiseData({
        streak: 2.9,
        lastDate: "Wed Nov 04 2026",
        subjects: {
            "  Mathematics  ": {
                history: {
                    "day-1": 3,
                    "invalid": -1,
                    "nan": Number.NaN
                },
                targets: {
                    "day-1": 4
                }
            },
            "": {
                history: {},
                targets: {}
            }
        }
    });

    assert.deepEqual(data, {
        streak: 2,
        lastDate: "Wed Nov 04 2026",
        subjects: {
            Mathematics: {
                history: { "day-1": 3 },
                targets: { "day-1": 4 }
            }
        }
    });
});

test("returns safe defaults for malformed storage payloads", () => {
    assert.deepEqual(sanitiseData("{not-json}"), createDefaultData());
    assert.deepEqual(sanitiseData(null), createDefaultData());
});

test("calculates totals across subjects and tracked days", () => {
    const data = sanitiseData({
        subjects: {
            Math: {
                history: { Monday: 2, Tuesday: 3 },
                targets: { Monday: 4, Tuesday: 4 }
            },
            Science: {
                history: { Monday: 1 },
                targets: { Monday: 2 }
            }
        }
    });

    const totals = calculateTotals(data);
    assert.equal(totals.totalStudy, 6);
    assert.equal(totals.totalTarget, 10);
    assert.deepEqual([...totals.allDays].sort(), ["Monday", "Tuesday"]);
    assert.deepEqual(totals.subjectTotals, { Math: 5, Science: 1 });
});
