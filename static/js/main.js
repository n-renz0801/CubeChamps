let solverCount = 0;

function addSolver() {
  solverCount++;

  const tbody = document.getElementById("table-body");
  const row = document.createElement("tr");

  row.innerHTML = `
    <td class="rank"></td>
    <td contenteditable="true" class="solver-name">Solver ${solverCount}</td>

    <td><div class="cell"><input type="text" class="solve" placeholder=" "></div></td>
    <td><div class="cell"><input type="text" class="solve" placeholder=" "></div></td>
    <td><div class="cell"><input type="text" class="solve" placeholder=" "></div></td>
    <td><div class="cell"><input type="text" class="solve" placeholder=" "></div></td>
    <td><div class="cell"><input type="text" class="solve" placeholder=" "></div></td>

    <td class="average">-</td>
    <td class="best-value">-</td>
  `;

  const nameCell = row.querySelector(".solver-name");

  nameCell.addEventListener("blur", () => {
    const name = nameCell.textContent.trim();

    if (name === "") {
      const confirmDelete = confirm("Delete this solver?");
      if (confirmDelete) {
        row.remove();
        sortTable();
      } else {
        nameCell.textContent = `Solver ${solverCount}`;
      }
    }
  });

  tbody.appendChild(row);

  const inputs = row.querySelectorAll(".solve");

  inputs.forEach((input, index) => {
    input.addEventListener("blur", () => {
      formatInput(input);
      calculateRow(row);
      sortTable();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();

        const next = inputs[index + 1];
        if (next) {
          next.focus();
        } else {
          input.blur();
        }
      }
    });
  });

  sortTable();
}

function formatInput(input) {
  let val = input.value.trim().toUpperCase();

  if (val === "") return;

  if (val === "DNF") {
    input.value = "DNF";
    return;
  }

  let num = parseFloat(val);
  if (!isNaN(num)) {
    input.value = num.toFixed(2);
  } else {
    input.value = "";
  }
}

function calculateRow(row) {
  const inputs = row.querySelectorAll(".solve");
  const avgCell = row.querySelector(".average");
  const bestCell = row.querySelector(".best-value");

  let values = [];
  let dnfCount = 0;

  // reset classes
  inputs.forEach((input) => {
    input.parentElement.classList.remove("best", "worst");
  });

  // collect values
  inputs.forEach((input) => {
    let val = input.value.trim().toUpperCase();

    if (val === "DNF") {
      values.push("DNF");
      dnfCount++;
    } else {
      let num = parseFloat(val);
      if (!isNaN(num)) {
        values.push(num);
      }
    }
  });

  if (values.length === 0) {
    avgCell.textContent = "-";
    bestCell.textContent = "-";
    return;
  }

  // BEST VALUE
  let numeric = values.filter((v) => v !== "DNF");

  if (numeric.length > 0) {
    let best = Math.min(...numeric);
    bestCell.textContent = best.toFixed(2);
  } else {
    bestCell.textContent = "DNF";
  }

  // AVERAGE
  if (values.length === 5) {
    if (dnfCount >= 2) {
      avgCell.textContent = "DNF";
    } else {
      let processed = values.map((v) => (v === "DNF" ? Infinity : v));
      processed.sort((a, b) => a - b);

      processed.shift();
      processed.pop();

      if (processed.includes(Infinity)) {
        avgCell.textContent = "DNF";
      } else {
        let avg = processed.reduce((a, b) => a + b, 0) / 3;
        avgCell.textContent = avg.toFixed(2);
      }
    }
  } else {
    avgCell.textContent = "-";
  }

  // 👇 BEST & WORST MARKING
  // 👇 BEST & WORST MARKING (STRICT SINGLE HIGHLIGHT BOTH)

  if (numeric.length > 0) {
    let best = Math.min(...numeric);
    let worst = values.includes("DNF") ? "DNF" : Math.max(...numeric);

    let bestUsed = false;
    let worstUsed = false;

    inputs.forEach((input) => {
      let wrapper = input.parentElement;
      let val = input.value.trim().toUpperCase();

      if (val === "") return;

      let num = parseFloat(val);

      // RESET already handled above

      // 🔴 WORST (ONLY ONE, even for multiple DNFs)
      if (val === "DNF") {
        if (worst === "DNF" && !worstUsed) {
          wrapper.classList.add("worst");
          worstUsed = true;
        }
        return;
      }

      if (!isNaN(num)) {
        // 🔴 WORST number (only first match)
        if (num === worst && !worstUsed) {
          wrapper.classList.add("worst");
          worstUsed = true;
        }

        // 🟢 BEST number (only first match)
        if (num === best && !bestUsed) {
          wrapper.classList.add("best");
          bestUsed = true;
        }
      }
    });
  }
}

function getSolveCount(row) {
  const inputs = row.querySelectorAll(".solve");
  let count = 0;

  inputs.forEach((input) => {
    if (input.value.trim() !== "") count++;
  });

  return count;
}

function getAverage(row) {
  const avg = row.querySelector(".average").textContent;

  if (avg === "-" || avg === "DNF") return Infinity;
  return parseFloat(avg);
}

function sortTable() {
  const tbody = document.getElementById("table-body");
  const rows = Array.from(tbody.querySelectorAll("tr"));

  rows.sort((a, b) => {
    let countA = getSolveCount(a);
    let countB = getSolveCount(b);

    if (countA !== countB) {
      return countB - countA;
    }

    if (countA === 5 && countB === 5) {
      return getAverage(a) - getAverage(b);
    }

    return 0;
  });

  rows.forEach((row, index) => {
    const rankCell = row.querySelector(".rank");

    rankCell.textContent = index + 1;

    // reset class first
    rankCell.classList.remove("top3");

    // apply top 3 styling
    if (index < 3) {
      rankCell.classList.add("top3");
    }

    tbody.appendChild(row);
  });
}
