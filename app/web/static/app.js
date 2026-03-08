/*
Author: Antonio Corona
Date: 2026-03-07

JavaScript Utilities – Schedule Viewer UI Logic

Purpose:
    Provides client-side behavior for (Maverick Scheduler web pages):
    - Schedule Viewer table switching
    - Config export/save flow

Responsibilities:
    - Manage Schedule Viewer table/tab switching
    - Persist selected viewer mode across page reloads
    - Handle Config Editor save/export interactions
    - Trigger browser download/save behavior for working_config data
    - Display save success/failure confirmation messages

Architectural Role (MVC):
    - Acts on the View side of MVC
    - Enhances the HTML templates with interactive browser behavior
    - Communicates with Controller routes through fetch requests
*/

// app/web/static/app.js

// Wait for the HTML document to fully load before attaching listeners.
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Schedule Viewer table switching logic.
  initViewerTables();

  // Initialize Config Editor export/save logic.
  initConfigExport();
});

/*
===============================================================================
Schedule Viewer Behavior
===============================================================================
*/

/**
 * Initializes the Schedule Viewer tab/table display behavior.
 *
 * Responsibilities:
 *   - Switch between different schedule table panels
 *   - Keep only one panel visible at a time
 *   - Reset the opposite menu when one selector is used
 *   - Save the current viewer mode in localStorage
 *   - Restore the previously selected mode on page reload
 *
 * This function safely exits on pages that do not contain viewer elements.
 */
function initViewerTables() {


  // ------------------------------------------------------------
  // 1. Element References
  // ------------------------------------------------------------

  // All table panels that may be shown/hidden
  const panels = document.querySelectorAll(".tab-panel");

  // Dropdown selectors used to choose display modes.
  const selects = document.querySelectorAll(".mode-select");
 
  // Individual dropdown references 
  const masterMenu = document.getElementById("master_menu");
  const filterMenu = document.getElementById("filter_menu");

  // If this page doesn't include the viewer table UI, do nothing.
  if (!panels.length || !selects.length) return;

  
  // ------------------------------------------------------------
  // 2. Helper Functions
  // ------------------------------------------------------------

  /**
   * Hides all table panels.
   * Ensures only one view is visible at a time.
   */  
  function hideAllPanels() {
    panels.forEach((panel) => {
      panel.style.display = "none";
    });
  }

  /**
   * Displays a specific panel by key.
   */
  function showPanel(panelKey) {
    // panelKey matches values like "master-room-table"
    const el = document.getElementById(`tab-${panelKey}`);
    if (el) el.style.display = "";
  }

  /**
   * Resets the opposite dropdown to its placeholder.
   *
   * If user selects from Master dropdown,
   * Filter dropdown resets to index 0 
   */
  function resetOtherMenu(activeGroup) {
    // If user chose from master menu, reset filter menu to placeholder (and vice versa)
    if (activeGroup === "master" && filterMenu) {
      filterMenu.selectedIndex = 0;
    }

    if (activeGroup === "filter" && masterMenu) {
      masterMenu.selectedIndex = 0;
    }
  }


  // ------------------------------------------------------------
  // 3. Initial State
  // ------------------------------------------------------------

  // Start with all panels hidden until a selection is made/restored.
  hideAllPanels();


  // ------------------------------------------------------------
  // 4. Dropdown Change Event Handling
  // ------------------------------------------------------------

  // Attach change listeners to each mode selector.
  selects.forEach((sel) => {
    sel.addEventListener("change", () => {
      const panelKey = sel.value;                 // e.g. "master-room-table"
      const group = sel.dataset.group || "";      // "master" or "filter"

      // Hide all panels before showing selected one
      hideAllPanels();

      // Show selected panel
      showPanel(panelKey);

      // Reset opposite dropdown
      resetOtherMenu(group);

      // Store the current viewer state so it can be restored later.
      try {
        localStorage.setItem("viewerTableMode", panelKey);
        localStorage.setItem("viewerTableGroup", group);
      } catch {
        // Ignore storage errors silently
      }
    });
  });

  // Attempt to restore the previously selected viewer state.
  try {
    const savedKey = localStorage.getItem("viewerTableMode");
    const savedGroup = localStorage.getItem("viewerTableGroup");
    
    if (savedKey) {
      hideAllPanels();
      showPanel(savedKey);

      // Set dropdown to match saved selection
      if (savedGroup === "master" && masterMenu) masterMenu.value = savedKey;
      if (savedGroup === "filter" && filterMenu) filterMenu.value = savedKey;

      resetOtherMenu(savedGroup);
    }
  } catch {
    // Ignore storage retrieval errors
  }
}


/*
===============================================================================
Config Editor Save / Export Behavior
===============================================================================
*/

/**
 * Initializes Config Editor export behavior for the Save button.
 *
 * Responsibilities:
 *   - Intercepts Save form submission
 *   - Sends current export filename to the backend
 *   - Requests the current working configuration as a downloadable blob
 *   - Opens a browser save dialog when supported
 *   - Falls back to standard file download when necessary
 *   - Displays success or failure feedback to the user
 *
 * This function safely exits on pages that do not contain export elements.
 */
function initConfigExport() {
  // Export form in the Config Editor page.
  const form = document.getElementById("export-config-form");

  // Input field where the suggested filename is shown/edited.
  const filenameInput = document.getElementById("export_filename");

  // UI area where save success/failure messages are displayed.
  const confirmation = document.getElementById("save-confirmation");

  // If this is not the Config Editor page, stop here.
  if (!form || !filenameInput || !confirmation) return;

  /**
   * Displays a status message below the Save form.
   */
  function showMessage(message, isError = false) {
    confirmation.textContent = message;
    confirmation.style.display = "block";
    confirmation.className = isError ? "msg error" : "msg success";
  }

  /**
   * Requests an export blob from the backend.
   *
   * Flow:
   *   - Sends the requested filename to /config/export
   *   - Receives the current working config as JSON data
   *   - Returns the blob plus final filename chosen by the server
   *
   * @param {string} filename - Filename requested by the user.
   * @returns {Promise<{blob: Blob, filename: string}>}
   */
  async function fetchExportBlob(filename) {
    const formData = new FormData();
    formData.append("filename", filename);

    const response = await fetch("/config/export", {
      method: "POST",
      body: formData,
    });

    // If export fails, surface the server's error message.
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Export failed.");
    }

    // Read the returned file payload as a blob.
    const blob = await response.blob();

    // Prefer the server-confirmed filename if present.
    const serverFilename =
      response.headers.get("X-Export-Filename") || filename;

    return { blob, filename: serverFilename };
  }

  /**
   * Uses the File System Access API to open a native browser save dialog.
   *
   * This best matches the Sprint 2 user story because it lets the user:
   *   - Confirm the filename
   *   - Confirm the save location
   *
   * @param {Blob} blob - File data to write.
   * @param {string} filename - Suggested filename for the save dialog.
   */
  async function saveWithPicker(blob, filename) {
    const handle = await window.showSaveFilePicker({
      suggestedName: filename,
      types: [
        {
          description: "JSON Files",
          accept: {
            "application/json": [".json"],
          },
        },
      ],
    });

    const writable = await handle.createWritable();
    await writable.write(blob);
    await writable.close();
  }

  /**
   * Fallback download behavior for browsers that do not support
   * showSaveFilePicker().
   *
   * This triggers a normal download using an invisible anchor element.
   *
   * @param {Blob} blob - File data to download.
   * @param {string} filename - Suggested filename for download.
   */
  function fallbackDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  // Handle Save button submission.
  form.addEventListener("submit", async (event) => {
    // Prevent normal form submission so JavaScript can control the export flow.
    event.preventDefault();

    // Use the entered filename or fall back to the default export name.
    const requestedName = (filenameInput.value || "").trim() || "new_config_file.json";

    try {
      // Request the downloadable config data from the backend.
      const { blob, filename } = await fetchExportBlob(requestedName);

      // Keep the input synchronized with the server-confirmed filename.
      filenameInput.value = filename;

      // Use native save picker when available for filename/location confirmation.
      if ("showSaveFilePicker" in window) {
        await saveWithPicker(blob, filename);
      } else {
        // Otherwise fall back to a normal browser download.
        fallbackDownload(blob, filename);
      }

      // Notify the user that the save/export completed successfully.
      showMessage(`Configuration saved successfully as ${filename}.`);
    } catch (error) {
      // Show an error message if anything goes wrong during export.
      showMessage(error.message || "Save failed.", true);
    }
  });
}