/* =========================
   UPDATE RANK NUMBERS
========================= */
function updateRanks() {
  const tbody = document.getElementById("solves-body");
  const rows = tbody.querySelectorAll("tr");

  rows.forEach((row, index) => {
    const rankCell = row.querySelector(".rank-cell");
    if (rankCell) {
      rankCell.innerText = index + 1;
    }
  });
}

/* =========================
   REORDER TABLE (LEADERBOARD LOGIC)
========================= */
function reorderTable() {
  const tbody = document.getElementById("solves-body");
  const rows = Array.from(tbody.querySelectorAll("tr"));

  function getStats(row) {
    const inputs = row.querySelectorAll("input[data-field]");
    const times = [];

    inputs.forEach((inp) => {
      const field = inp.dataset.field;

      if (field.startsWith("attempt")) {
        const val = parseFloat(inp.value);
        if (!isNaN(val)) times.push(val);
      }
    });

    const validCount = times.length;

    let avg = null;
    if (times.length >= 3) {
      const sorted = [...times].sort((a, b) => a - b);
      const middle = sorted.slice(1, -1);
      avg = middle.reduce((a, b) => a + b, 0) / middle.length;
    }

    return { validCount, avg };
  }

  rows.sort((a, b) => {
    const A = getStats(a);
    const B = getStats(b);

    // 1st: more solves
    if (B.validCount !== A.validCount) {
      return B.validCount - A.validCount;
    }

    // 2nd: lower average wins
    if (A.avg === null && B.avg === null) return 0;
    if (A.avg === null) return 1;
    if (B.avg === null) return -1;

    return A.avg - B.avg;
  });

  rows.forEach((row) => tbody.appendChild(row));

  updateRanks();
}

/* =========================
   STORE ORIGINAL NAME (FOR CANCEL RESTORE)
========================= */
document
  .querySelectorAll(".solve-input[data-field='name']")
  .forEach((input) => {
    input.addEventListener("focus", function () {
      this.dataset.originalValue = this.value;
    });
  });

/* =========================
   AUTO SAVE + DELETE LOGIC
========================= */
document.querySelectorAll(".solve-input").forEach((input) => {
  input.addEventListener("blur", function () {
    const row = this.closest("tr");
    const solveId = row.dataset.solveId;

    const nameInput = row.querySelector('[data-field="name"]');
    const nameValue = nameInput.value.trim();

    // 🔥 DELETE IF NAME IS EMPTY
    if (nameValue === "") {
      const confirmDelete = confirm("Remove this player from the round?");

      if (!confirmDelete) {
        // ❌ restore original name
        nameInput.value = nameInput.dataset.originalValue || "";
        return;
      }

      fetch(`/solve/${solveId}/delete`, {
        method: "POST",
      }).then(() => {
        // 🔥 INSTANT UI REMOVE
        row.remove();

        reorderTable();
      });

      return;
    }

    // OTHERWISE → UPDATE
    const data = {
      name: nameValue,

      attempt1: row.querySelector('[data-field="attempt1"]').value || null,
      attempt2: row.querySelector('[data-field="attempt2"]').value || null,
      attempt3: row.querySelector('[data-field="attempt3"]').value || null,
      attempt4: row.querySelector('[data-field="attempt4"]').value || null,
      attempt5: row.querySelector('[data-field="attempt5"]').value || null,
    };

    fetch(`/solve/${solveId}/update`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then((res) => res.json())
      .then((result) => {
        row.querySelector(".avg-cell").innerText =
          result.average !== null ? result.average : "-";

        row.querySelector(".best-cell").innerText =
          result.best !== null ? result.best : "-";

        reorderTable();
      });
  });
});

/* =========================
   INITIAL LOAD FIX
========================= */
window.addEventListener("DOMContentLoaded", () => {
  reorderTable();
});
