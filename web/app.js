"use strict";

const PYODIDE_BASE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
const PACKAGE_FILES = ["__init__.py", "models.py", "engine.py", "agents.py"];

const analyzeButton = document.getElementById("analyze-button");
const form = document.getElementById("review-form");
const runtimeStatus = document.getElementById("runtime-status");
const emptyState = document.getElementById("empty-state");
const resultContent = document.getElementById("result-content");
const resultBadge = document.getElementById("result-badge");
const alertsContainer = document.getElementById("alerts");

let pyodideRuntime = null;

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("theme", theme);
}

function initTheme() {
  const saved = localStorage.getItem("theme");
  const preferredDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  setTheme(saved || (preferredDark ? "dark" : "light"));
}

document.getElementById("theme-toggle").addEventListener("click", () => {
  setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
});

document.getElementById("example-button").addEventListener("click", () => {
  document.getElementById("case-id").value = "CASE-EXAMPLE";
  document.getElementById("primary-metric").value = "26";
  document.getElementById("secondary-metric").value = "12";
  document.getElementById("status-flag").value = "EQUIVOCAL";
  document.getElementById("is-stat").checked = false;
});

function setBadge(status) {
  resultBadge.className = "badge";
  if (status === "CONCORDANT_NORMAL") {
    resultBadge.classList.add("ok");
    resultBadge.textContent = "No rule flags";
  } else if (status === "CRITICAL_ACTION_REQUIRED") {
    resultBadge.classList.add("critical");
    resultBadge.textContent = "Priority flag";
  } else {
    resultBadge.classList.add("warn");
    resultBadge.textContent = "Review flags";
  }
}

function renderResult(result) {
  emptyState.hidden = true;
  resultContent.hidden = false;
  document.getElementById("overall-status").textContent = result.overall_status;
  document.getElementById("alert-count").textContent = String(result.total_alerts);
  document.getElementById("result-case").textContent = result.case_id;
  document.getElementById("reference-note").textContent = result.guideline_standard;
  setBadge(result.overall_status);

  alertsContainer.replaceChildren();
  if (!result.alerts.length) {
    const card = document.createElement("div");
    card.className = "alert-card";
    const heading = document.createElement("h3");
    heading.textContent = "No configured rule flags";
    const body = document.createElement("p");
    body.textContent = "The supplied values did not trigger the project demonstration rules.";
    card.append(heading, body);
    alertsContainer.append(card);
    return;
  }

  for (const alert of result.alerts) {
    const card = document.createElement("article");
    card.className = "alert-card";

    const heading = document.createElement("h3");
    heading.textContent = `${alert.urgency} · ${alert.title}`;

    const finding = document.createElement("p");
    finding.textContent = alert.clinical_finding;

    const recommendation = document.createElement("p");
    recommendation.textContent = alert.actionable_recommendation;

    card.append(heading, finding, recommendation);
    alertsContainer.append(card);
  }
}

async function loadPackageFiles(pyodide) {
  const packagePath = "/home/pyodide/clonality_hematology_agent";
  pyodide.FS.mkdirTree(packagePath);

  for (const filename of PACKAGE_FILES) {
    const response = await fetch(`./clonality_hematology_agent/${filename}`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`Could not load Python source: ${filename}`);
    }
    pyodide.FS.writeFile(`${packagePath}/${filename}`, await response.text());
  }

  pyodide.runPython(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
from clonality_hematology_agent.agents import ClonoCoordinator
from clonality_hematology_agent.models import ClinicalCasePayload
`);
}

async function initPython() {
  try {
    runtimeStatus.textContent = "Loading Python runtime…";
    pyodideRuntime = await loadPyodide({ indexURL: PYODIDE_BASE });
    await loadPackageFiles(pyodideRuntime);
    analyzeButton.disabled = false;
    runtimeStatus.textContent = "Python ready · inputs are processed locally in this page.";
  } catch (error) {
    console.error(error);
    runtimeStatus.textContent =
      "Python runtime failed to load. Check your network connection and reload.";
    resultBadge.className = "badge critical";
    resultBadge.textContent = "Runtime error";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!pyodideRuntime) return;

  const caseId = document.getElementById("case-id").value.trim();
  const primary = Number(document.getElementById("primary-metric").value);
  const secondary = Number(document.getElementById("secondary-metric").value);
  const statusFlag = document.getElementById("status-flag").value.trim();
  const isStat = document.getElementById("is-stat").checked;

  if (!caseId || !statusFlag || !Number.isFinite(primary) || !Number.isFinite(secondary)) {
    runtimeStatus.textContent = "Enter a case ID, status descriptor, and finite numeric values.";
    return;
  }

  analyzeButton.disabled = true;
  runtimeStatus.textContent = "Running Python rules…";

  try {
    pyodideRuntime.globals.set("ui_case_id", caseId);
    pyodideRuntime.globals.set("ui_primary", primary);
    pyodideRuntime.globals.set("ui_secondary", secondary);
    pyodideRuntime.globals.set("ui_status", statusFlag);
    pyodideRuntime.globals.set("ui_is_stat", isStat);

    const resultJson = pyodideRuntime.runPython(`
import json
_case = ClinicalCasePayload(
    case_id=str(ui_case_id),
    patient_synthetic_id="BROWSER-LOCAL",
    primary_metric=float(ui_primary),
    secondary_metric=float(ui_secondary),
    status_flag=str(ui_status),
    is_stat=bool(ui_is_stat),
)
json.dumps(ClonoCoordinator().process_case(_case))
`);
    renderResult(JSON.parse(resultJson));
    runtimeStatus.textContent = "Review complete.";
  } catch (error) {
    console.error(error);
    runtimeStatus.textContent = `Could not run review: ${error.message || error}`;
    resultBadge.className = "badge critical";
    resultBadge.textContent = "Input error";
  } finally {
    analyzeButton.disabled = false;
  }
});

initTheme();
initPython();
