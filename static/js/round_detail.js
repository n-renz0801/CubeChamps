const previousNames = {};

/* =========================
   RANKING
========================= */
function updateRanks() {
  const rows = document.querySelectorAll("#solves-body tr");

  rows.forEach((row, index) => {
    const rankCell = row.querySelector(".rank-cell");
    if (rankCell) rankCell.innerText = index + 1;
  });
}

/* =========================
   FORMATTERS
========================= */
function formatTimeDisplay(value) {
  if (value === null || value === undefined || value === "") return "";

  value = value.toString().trim().toUpperCase();

  if (value === "DNF" || value === "DNS") return value;

  const plus2 = value.match(/^(\d+(\.\d+)?)\+2$/);
  if (plus2) {
    const num = parseFloat(plus2[1]);
    return num.toFixed(2) + "+2";
  }

  const num = parseFloat(value);
  if (!isNaN(num)) return num.toFixed(2);

  return value;
}

function formatResult(value) {
  if (value === null || value === undefined) return "-";
  if (value === "DNF") return "DNF";

  const num = parseFloat(value);
  return isNaN(num) ? "-" : num.toFixed(2);
}

/* =========================
   VALIDATION
========================= */
function isValidTime(value) {
  if (!value) return true;

  value = value.trim().toUpperCase();

  if (value === "DNF" || value === "DNS") return true;
  if (/^\d+(\.\d+)?\+2$/.test(value)) return true;
  if (/^\d+(\.\d+)?$/.test(value)) return true;

  return false;
}

/* =========================
   NORMALIZER
========================= */
function normalize(val) {
  if (!val) return null;

  val = val.trim().toUpperCase();

  if (val === "DNF" || val === "DNS") return val;

  const plus2 = val.match(/^(\d+(\.\d+)?)\+2$/);
  if (plus2) return parseFloat(plus2[1]) + 2;

  const num = parseFloat(val);
  return isNaN(num) ? null : num;
}

/* =========================
   PARSE FOR SORTING
========================= */
function parseTime(value) {
  if (!value) return null;

  value = value.toString().trim().toUpperCase();

  if (value === "DNF" || value === "DNS") return Infinity;

  const plus2 = value.match(/^(\d+(\.\d+)?)\+2$/);
  if (plus2) return parseFloat(plus2[1]) + 2;

  const num = parseFloat(value);
  return isNaN(num) ? null : num;
}

/* =========================
   STATS
========================= */
function getStats(row) {
  const inputs = row.querySelectorAll('input[data-field^="attempt"]');

  let times = [];
  let specialCount = 0;

  inputs.forEach((inp) => {
    const val = inp.value.trim().toUpperCase();

    if (val === "DNF" || val === "DNS") {
      specialCount++;
      return;
    }

    const parsed = parseTime(val);
    if (typeof parsed === "number" && !isNaN(parsed)) {
      times.push(parsed);
    }
  });

  let avg = null;

  if (specialCount >= 2) {
    avg = "DNF";
  } else if (times.length >= 3) {
    const sorted = [...times].sort((a, b) => a - b);

    const middle = specialCount === 1 ? sorted.slice(1) : sorted.slice(1, -1);

    if (middle.length > 0) {
      avg = middle.reduce((a, b) => a + b, 0) / middle.length;
    }
  }

  return {
    validCount: times.length,
    avg,
  };
}

/* =========================
   REORDER TABLE
========================= */
function reorderTable() {
  const tbody = document.getElementById("solves-body");
  const rows = Array.from(tbody.querySelectorAll("tr"));

  rows.sort((a, b) => {
    const A = getStats(a);
    const B = getStats(b);

    if (B.validCount !== A.validCount) {
      return B.validCount - A.validCount;
    }

    if (A.avg === "DNF" && B.avg !== "DNF") return 1;
    if (B.avg === "DNF" && A.avg !== "DNF") return -1;

    if (A.avg === null && B.avg === null) return 0;
    if (A.avg === null) return 1;
    if (B.avg === null) return -1;

    return A.avg - B.avg;
  });

  rows.forEach((row) => tbody.appendChild(row));
  updateRanks();
}

/* =========================
   DELETE ROW
========================= */
function deleteSolve(row) {
  const solveId = row.dataset.solveId;

  fetch(`/solve/${solveId}/delete`, {
    method: "POST",
  });

  row.remove();
  reorderTable();
}

/* =========================
   INIT
========================= */
window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".solve-input").forEach((inp) => {
    inp.dataset.lastValid = inp.value;
  });

  reorderTable();
});

/* =========================
   INPUT HANDLER
========================= */
document.querySelectorAll(".solve-input").forEach((input) => {
  input.addEventListener("blur", function () {
    const row = this.closest("tr");
    const solveId = row.dataset.solveId;
    const field = this.dataset.field;

    const nameInput = row.querySelector('[data-field="name"]');

    /* NAME DELETE */
    if (field === "name") {
      const current = nameInput.value.trim();

      if (current === "") {
        const confirmDelete = confirm("Remove this player from this round?");
        if (!confirmDelete) {
          this.value = previousNames[solveId] || "";
          return;
        }

        deleteSolve(row);
        return;
      }

      previousNames[solveId] = current;
    }

    /* VALIDATION */
    for (let inp of row.querySelectorAll(".solve-input")) {
      if (inp.dataset.field === "name") continue;

      if (!isValidTime(inp.value)) {
        alert("Invalid input! Use number, DNF, DNS, or 12.34+2");

        inp.value = inp.dataset.lastValid || "";
        inp.focus();
        return;
      }

      inp.dataset.lastValid = inp.value;

      // 🔥 FORMAT INPUT HERE
      inp.value = formatTimeDisplay(inp.value);
    }

    /* CLEAN DATA */
    const data = {
      name: nameInput.value.trim(),

      attempt1: normalize(row.querySelector('[data-field="attempt1"]').value),
      attempt2: normalize(row.querySelector('[data-field="attempt2"]').value),
      attempt3: normalize(row.querySelector('[data-field="attempt3"]').value),
      attempt4: normalize(row.querySelector('[data-field="attempt4"]').value),
      attempt5: normalize(row.querySelector('[data-field="attempt5"]').value),
    };

    /* SAVE */
    fetch(`/solve/${solveId}/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then((res) => res.json())
      .then((result) => {
        row.querySelector(".avg-cell").innerText = formatResult(result.average);

        row.querySelector(".best-cell").innerText = formatResult(result.best);

        reorderTable();
      });
  });
});
