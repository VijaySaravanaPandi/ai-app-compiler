// Examples dictionary for prompt chips
const EXAMPLES = {
  crm: "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
  blog: "Build a personal blog with login, admin dashboard to manage posts, public reading view, comment section for users, and categorisation of posts.",
  ecommerce: "Build an e-commerce platform with catalog, shopping cart, user checkout, order management, payment integration, and a merchant admin dashboard.",
  booking: "Build a clinic booking system where patients can search doctors, schedule appointments, see dynamic pricing, and admins can manage slots."
};

// Global application state
let currentCompileState = null;
let currentRequestId = null;
let pollIntervalId = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  const promptInput = document.getElementById("prompt-input");
  const charCounter = document.getElementById("char-counter");

  // Character counter listener
  promptInput.addEventListener("input", () => {
    const len = promptInput.value.length;
    charCounter.textContent = `${len} / 2000`;
  });

  // Example chip listeners
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const type = chip.getAttribute("data-example");
      if (EXAMPLES[type]) {
        promptInput.value = EXAMPLES[type];
        charCounter.textContent = `${EXAMPLES[type].length} / 2000`;
        promptInput.focus();
      }
    });
  });
});

// Switch visible schema tabs
function switchTab(tabName, element) {
  // Remove active class from all tabs
  document.querySelectorAll(".tab").forEach(tab => tab.classList.remove("active"));
  
  // Add active class to clicked tab
  if (element) {
    element.classList.add("active");
  } else {
    const tabEl = document.querySelector(`.tab[data-tab="${tabName}"]`);
    if (tabEl) tabEl.classList.add("active");
  }

  // Display the relevant data in the JSON viewer
  const outputEl = document.getElementById("json-output");
  if (!currentCompileState) {
    outputEl.textContent = "No data compiled yet.";
    return;
  }

  let dataToShow = null;
  if (tabName === "raw") {
    dataToShow = currentCompileState;
  } else {
    dataToShow = currentCompileState[tabName];
  }

  if (dataToShow === undefined || dataToShow === null) {
    outputEl.textContent = `No ${tabName} data was generated for this app or it is empty.`;
  } else {
    outputEl.innerHTML = syntaxHighlight(dataToShow);
  }
}

// Copy current tab JSON to clipboard
function copyJSON() {
  const outputEl = document.getElementById("json-output");
  const text = outputEl.textContent;
  
  navigator.clipboard.writeText(text).then(() => {
    const copyBtn = document.getElementById("copy-btn");
    const originalText = copyBtn.textContent;
    copyBtn.textContent = "✅ Copied!";
    setTimeout(() => {
      copyBtn.textContent = originalText;
    }, 2000);
  }).catch(err => {
    console.error("Failed to copy text: ", err);
  });
}

// Start compilation process
function startCompile() {
  const promptInput = document.getElementById("prompt-input");
  const compileBtn = document.getElementById("compile-btn");
  const prompt = promptInput.value.trim();

  if (!prompt) {
    alert("Please enter a description for your application.");
    return;
  }

  // Reset UI elements
  document.getElementById("progress-area").removeAttribute("hidden");
  document.getElementById("clarification-area").setAttribute("hidden", "true");
  document.getElementById("error-area").setAttribute("hidden", "true");
  document.getElementById("result-area").setAttribute("hidden", "true");
  document.getElementById("download-btn").setAttribute("hidden", "true");

  // Disable inputs
  promptInput.disabled = true;
  compileBtn.disabled = true;
  compileBtn.querySelector(".compile-btn-text").setAttribute("hidden", "true");
  compileBtn.querySelector(".compile-btn-spinner").removeAttribute("hidden");

  // Reset tracker visual classes
  for (let i = 0; i <= 5; i++) {
    const ts = document.getElementById(`ts-${i}`);
    if (ts) {
      ts.classList.remove("active", "done");
    }
  }

  // Trigger async compilation
  fetch("/compile/async", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt })
  })
  .then(res => {
    if (!res.ok) throw new Error(`Server returned status code: ${res.status}`);
    return res.json();
  })
  .then(data => {
    currentRequestId = data.request_id;
    startPolling(currentRequestId);
  })
  .catch(err => {
    showCompilationError([err.message]);
    resetCompileButton();
  });
}

// Poll status of the compilation request
function startPolling(requestId) {
  if (pollIntervalId) clearInterval(pollIntervalId);

  pollIntervalId = setInterval(() => {
    fetch(`/compile/status/${requestId}`)
    .then(res => {
      if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
      return res.json();
    })
    .then(state => {
      updateProgressBar(state);

      if (state.status === "complete") {
        clearInterval(pollIntervalId);
        showCompilationResult(state);
        resetCompileButton();
      } else if (state.status === "needs_clarification") {
        clearInterval(pollIntervalId);
        showClarificationQuestions(state.clarification_questions || []);
        resetCompileButton();
      } else if (state.status === "failed") {
        clearInterval(pollIntervalId);
        const errorMessages = (state.validation_issues || [])
          .map(i => `[${i.severity.toUpperCase()}] ${i.layer}: ${i.message}`);
        showCompilationError(errorMessages.length > 0 ? errorMessages : ["Pipeline execution failed due to an internal error."]);
        resetCompileButton();
      }
    })
    .catch(err => {
      clearInterval(pollIntervalId);
      showCompilationError([err.message]);
      resetCompileButton();
    });
  }, 1200);
}

// Update the progress bar and tracker stages
function updateProgressBar(state) {
  const progressFill = document.getElementById("progress-fill");
  const progressPct = document.getElementById("progress-pct");
  const progressStageName = document.getElementById("progress-stage-name");

  // Map state statuses to visual percentages and stages
  const statusConfig = {
    "pending": { pct: 5, stage: 0, label: "Clarifying details..." },
    "intent_done": { pct: 20, stage: 1, label: "Extracting intent schemas..." },
    "architecture_done": { pct: 40, stage: 2, label: "Designing application architecture..." },
    "schemas_done": { pct: 60, stage: 3, label: "Generating component schemas..." },
    "refined": { pct: 75, stage: 3, label: "Refining schemas for consistency..." },
    "validated": { pct: 85, stage: 4, label: "Validating schema layers..." },
    "repaired": { pct: 90, stage: 4, label: "Repairing validation failures..." },
    "codegen_done": { pct: 95, stage: 5, label: "Generating application files..." },
    "complete": { pct: 100, stage: 5, label: "Compilation complete!" }
  };

  const config = statusConfig[state.status] || { pct: 0, stage: 0, label: "Processing..." };
  
  progressFill.style.width = `${config.pct}%`;
  progressPct.textContent = `${config.pct}%`;
  progressStageName.textContent = config.label;

  // Visual feedback on steps
  for (let i = 0; i <= 5; i++) {
    const ts = document.getElementById(`ts-${i}`);
    if (!ts) continue;

    if (i < config.stage) {
      ts.classList.remove("active");
      ts.classList.add("done");
    } else if (i === config.stage) {
      ts.classList.remove("done");
      ts.classList.add("active");
    } else {
      ts.classList.remove("active", "done");
    }
  }
}

// Show validation or connection errors
function showCompilationError(errors) {
  const errorArea = document.getElementById("error-area");
  const errorList = document.getElementById("error-list");
  
  errorList.innerHTML = "";
  errors.forEach(err => {
    const li = document.createElement("li");
    li.textContent = err;
    errorList.appendChild(li);
  });

  errorArea.removeAttribute("hidden");
}

// Show clarification questions to the user
function showClarificationQuestions(questions) {
  const clarifArea = document.getElementById("clarification-area");
  const clarifList = document.getElementById("clarif-questions");

  clarifList.innerHTML = "";
  questions.forEach(q => {
    const li = document.createElement("li");
    li.textContent = q;
    clarifList.appendChild(li);
  });

  clarifArea.removeAttribute("hidden");
}

// Render compilation result
function showCompilationResult(state) {
  currentCompileState = state;

  const resultArea = document.getElementById("result-area");
  const statusText = document.getElementById("result-status-text");
  const downloadBtn = document.getElementById("download-btn");
  const statsBar = document.getElementById("stats-bar");

  statusText.textContent = "Compiled successfully";
  
  if (state.generated_app_path) {
    downloadBtn.removeAttribute("hidden");
  }

  // Display stats
  const repairAttempts = state.repair_log ? state.repair_log.length : 0;
  const issuesFound = state.validation_issues ? state.validation_issues.length : 0;
  
  let statsHTML = `
    <div class="stat">Status: <strong>${state.status}</strong></div>
    <div class="stat">Issues Repaired: <strong>${repairAttempts}</strong></div>
    <div class="stat">Remaining Issues: <strong>${issuesFound}</strong></div>
  `;

  if (state.created_at) {
    const duration = Math.round((new Date() - new Date(state.created_at)) / 1000);
    statsHTML += `<div class="stat">Time Elapsed: <strong>${duration}s</strong></div>`;
  }

  statsBar.innerHTML = statsHTML;

  // Show the result area and switch to the Intent tab
  resultArea.removeAttribute("hidden");
  switchTab("intent");
}

// Reset compilation button state
function resetCompileButton() {
  const promptInput = document.getElementById("prompt-input");
  const compileBtn = document.getElementById("compile-btn");

  promptInput.disabled = false;
  compileBtn.disabled = false;
  compileBtn.querySelector(".compile-btn-text").removeAttribute("hidden");
  compileBtn.querySelector(".compile-btn-spinner").setAttribute("hidden", "true");
}

// Download the generated code .zip file
function downloadApp() {
  if (!currentRequestId) return;
  window.location.href = `/apps/${currentRequestId}/download`;
}

// Syntax highlighting for JSON output
function syntaxHighlight(json) {
  if (typeof json !== "string") {
    json = JSON.stringify(json, null, 2);
  }
  
  // Escape HTML tags to prevent XSS/rendering issues
  json = json.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  
  // Regex parsing of JSON tokens to insert colorizing spans
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
    let cls = "number";
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = "key";
      } else {
        cls = "string";
      }
    } else if (/true|false/.test(match)) {
      cls = "bool";
    } else if (/null/.test(match)) {
      cls = "null";
    }
    return `<span class="json-${cls}">${match}</span>`;
  });
}
