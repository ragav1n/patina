// Boots Pyodide, loads the real patina engine (numpy/Pillow/pillow-heif +
// the patina wheel), and wires it to the file picker / preset UI.
// Everything after the first successful load runs with zero network access,
// see sw.js for the offline caching strategy.

const statusEl = document.getElementById("status");
const fileInput = document.getElementById("fileInput");
const fileLabelText = document.getElementById("fileLabelText");
const presetTrigger = document.getElementById("presetTrigger");
const presetTriggerText = document.getElementById("presetTriggerText");
const presetDesc = document.getElementById("presetDesc");
const presetSheet = document.getElementById("presetSheet");
const presetSheetBackdrop = document.getElementById("presetSheetBackdrop");
const presetList = document.getElementById("presetList");
const preview = document.getElementById("preview");
const previewFrame = document.getElementById("previewFrame");
const downloadLink = document.getElementById("downloadLink");
const saveHint = document.getElementById("saveHint");

let presetPairs = [];
let selectedPreset = null;

const CHECK_SVG = `<svg class="check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>`;

function setState(state, message) {
  document.body.dataset.state = state;
  if (message) statusEl.textContent = message;
}

const BRIDGE_SRC = `
import io
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
register_heif_opener()
from patina import render, presets

def process(data, preset_name):
    img = Image.open(io.BytesIO(bytes(data)))
    img = ImageOps.exif_transpose(img).convert("RGB")
    out = render.render_frame(img, presets.PRESETS[preset_name])
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=92)
    return buf.getvalue()

def preset_list():
    return [[name, p.get("description", "")] for name, p in sorted(presets.PRESETS.items())]
`;

async function initPyodide() {
  // pkg/manifest.json is written by the deploy workflow right after it builds
  // the wheel, so this never needs to track the patina version by hand.
  const pkgManifest = await fetch("./pkg/manifest.json").then((r) => r.json());
  const pyodide = await loadPyodide({ indexURL: "./vendor/pyodide/" });
  await pyodide.loadPackage(["numpy", "Pillow", "pillow-heif"]);
  await pyodide.loadPackage(`./pkg/${pkgManifest.wheel}`);
  await pyodide.runPythonAsync(BRIDGE_SRC);
  return pyodide;
}

function populatePresets(pairs) {
  presetPairs = pairs;
  presetList.querySelectorAll(".preset-option").forEach((el) => el.remove());

  for (const [name, desc] of pairs) {
    const row = document.createElement("div");
    row.className = "preset-option";
    row.id = `preset-option-${name}`;
    row.setAttribute("role", "option");
    row.dataset.name = name;
    row.tabIndex = -1;
    row.innerHTML = `
      <span class="preset-option-text">
        <span class="preset-option-name">${name.replace(/_/g, " ")}</span>
        <span class="preset-option-desc">${desc}</span>
      </span>
      ${CHECK_SVG}
    `;
    row.addEventListener("click", () => {
      selectPreset(name);
      closeSheet();
    });
    presetList.appendChild(row);
  }

  const defaultName = pairs.some(([name]) => name === "flash_night") ? "flash_night" : pairs[0]?.[0];
  selectPreset(defaultName);
  presetTrigger.disabled = false;
}

function selectPreset(name) {
  selectedPreset = name;
  const pair = presetPairs.find(([n]) => n === name);
  presetTriggerText.textContent = name.replace(/_/g, " ");
  presetDesc.textContent = pair?.[1] || "";
  presetList.querySelectorAll(".preset-option").forEach((el) => {
    el.setAttribute("aria-selected", String(el.dataset.name === name));
    el.tabIndex = el.dataset.name === name ? 0 : -1;
  });
}

function openSheet() {
  presetSheet.hidden = false;
  requestAnimationFrame(() => presetSheet.classList.add("open"));
  presetTrigger.setAttribute("aria-expanded", "true");
  const selectedRow = presetList.querySelector('[aria-selected="true"]');
  (selectedRow || presetList).focus();
}

function closeSheet() {
  presetSheet.classList.remove("open");
  presetTrigger.setAttribute("aria-expanded", "false");
  presetTrigger.focus();
  setTimeout(() => { presetSheet.hidden = true; }, 250);
}

presetTrigger.addEventListener("click", openSheet);
presetSheetBackdrop.addEventListener("click", closeSheet);

presetList.addEventListener("keydown", (event) => {
  const rows = Array.from(presetList.querySelectorAll(".preset-option"));
  const current = document.activeElement.closest?.(".preset-option");
  const index = rows.indexOf(current);

  if (event.key === "Escape") {
    event.preventDefault();
    closeSheet();
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    (rows[index + 1] || rows[0])?.focus();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    (rows[index - 1] || rows[rows.length - 1])?.focus();
  } else if (event.key === "Enter" || event.key === " ") {
    if (current) {
      event.preventDefault();
      selectPreset(current.dataset.name);
      closeSheet();
    }
  }
});

const pyodideReady = (async () => {
  try {
    const pyodide = await initPyodide();
    const pairs = pyodide.globals.get("preset_list")().toJs();
    populatePresets(pairs);
    setState("ready", "Ready. Pick a photo to start.");
    return pyodide;
  } catch (err) {
    setState("error", "Couldn't load the engine: " + err);
    throw err;
  }
})();

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  downloadLink.style.display = "none";
  saveHint.style.display = "none";
  previewFrame.style.display = "none";
  fileLabelText.textContent = file.name;
  setState("loading", "Warming up the engine (first time only)...");

  let pyodide;
  try {
    pyodide = await pyodideReady;
  } catch {
    return; // error already shown
  }

  setState("processing", "Developing the photo...");
  try {
    const buf = new Uint8Array(await file.arrayBuffer());
    const preset = selectedPreset;
    let result = pyodide.globals.get("process")(buf, preset);
    if (result && typeof result.toJs === "function") result = result.toJs();

    const blob = new Blob([result], { type: "image/jpeg" });
    const url = URL.createObjectURL(blob);

    preview.src = url;
    previewFrame.style.display = "block";

    const base = file.name.replace(/\.[^.]+$/, "");
    downloadLink.href = url;
    downloadLink.download = `${base}_${preset}.jpg`;
    downloadLink.style.display = "block";
    saveHint.style.display = "block";

    setState("done", "Done.");
  } catch (err) {
    setState("error", "Couldn't process that photo: " + err);
  }
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((err) => {
      console.warn("service worker registration failed", err);
    });
  });
}
