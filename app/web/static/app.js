/*
Author: Antonio Corona, Ian Swartz
Date: 2026-03-08

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
 * Initializes the Schedule Viewer tab and entity-filter behavior.
 *
 * Responsibilities:
 *   - Switch between schedule table panels
 *   - Keep only one panel visible at a time
 *   - Reset the opposite selector when one menu is used
 *   - Support entity-specific filtering for rooms, labs, and faculty
 *   - Save the current table mode and filter selections in localStorage
 *   - Restore the previous viewer state on page reload
 *   - Clear all active viewer selections when requested
 *
 * Notes:
 *   - This function safely exits on pages that do not include
 *     the viewer table UI.
 *   - Entity filters are only applied within their matching
 *     filtered schedule views.
 */
function initViewerTables() {


  // ------------------------------------------------------------
  // 1. Element References
  // ------------------------------------------------------------

  // All tab panels used by the viewer.
  const panels = document.querySelectorAll(".tab-panel");

  // Dropdown selectors used to choose display modes.
  const selects = document.querySelectorAll(".mode-select");
 
  /**
   * Individual viewer control references.
   *
   * masterMenu:
   *   Dropdown for selecting standard table views.
   *
   * filterMenu:
   *   Dropdown for selecting filtered table views.
   *
   * clearBtn:
   *   Button used to reset all current viewer selections.
   */
  const masterMenu = document.getElementById("master_menu");
  const filterMenu = document.getElementById("filter_menu");
  const clearBtn = document.getElementById("clear_filters");


  // ===============================
  // Schedule Viewer Filtering Logic
  // ===============================
  
  /**
   * CLIENT-SIDE FILTERING LOGIC
   *
   * Controls visibility of grouped tables based on dropdown selection.
   *
   * Depends on:
   * - viewer.html structure (IDs + data-entity attributes)
   * - backend grouping keys from schedule_service.py
   *
   * Flow:
   * 1. User selects value from dropdown
   * 2. Matching group (data-entity) is shown
   * 3. All others are hidden
   *
   * If filtering breaks:
   * - Check HTML IDs
   * - Check data-entity values
   * - Check backend grouping output
   */
  // Room filter controls
  const roomFilterSelect = document.getElementById("room_filter_select");
  const roomGroups = document.querySelectorAll(".room-filter-group");
  const roomEmpty = document.getElementById("room_filter_empty");

  // Lab filter controls
  const labFilterSelect = document.getElementById("lab_filter_select");
  const labGroups = document.querySelectorAll(".lab-filter-group");
  const labEmpty = document.getElementById("lab_filter_empty");

  // Faculty filter controls
  const facultyFilterSelect = document.getElementById("faculty_filter_select");
  const facultyGroups = document.querySelectorAll(".faculty-filter-group");
  const facultyEmpty = document.getElementById("faculty_filter_empty");

  // If this page doesn't include the viewer table UI, do nothing.
  if (!panels.length || !selects.length) return;

  
  // ------------------------------------------------------------
  // 2. Helper Functions
  // ------------------------------------------------------------

  /**
   * Hides all schedule viewer panels.
   *
   * Used before showing a newly selected panel so that only one
   * schedule table view remains visible at a time.
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

  // Hides all entity-specific result groups for a given filter section.
  function hideGroups(groups, emptyMessage) {
    groups.forEach((group) => {
      group.style.display = "none";
    });

    if (emptyMessage) {
      emptyMessage.style.display = "none";
    }
  }

  // Applies an entity-specific filter to a group collection.
  function applyEntityFilter(selectedValue, groups, emptyMessage) {
    let foundMatch = false;

    groups.forEach((group) => {
      const entityName = group.dataset.entity || "";
      const isMatch = entityName === selectedValue;

      group.style.display = isMatch ? "" : "none";

      if (isMatch) {
        foundMatch = true;
      }
    });

    if (emptyMessage) {
      emptyMessage.style.display =
        selectedValue && !foundMatch ? "" : "none";
    }
  }

  /**
   * Hides all room, lab, and faculty filtered result groups.
   *
   * This is used when switching between schedule table modes
   * so that stale filtered results do not remain visible.
   */
  function hideAllEntityGroups() {
    hideGroups(roomGroups, roomEmpty);
    hideGroups(labGroups, labEmpty);
    hideGroups(facultyGroups, facultyEmpty);
  }

  // Automatically selects the first real option in a dropdown.
  function autoSelectFirstOption(selectEl) {
    if (!selectEl) return;

    if (!selectEl.value && selectEl.options.length > 1) {
      selectEl.selectedIndex = 1;
    }
  }

  /**
   * Clears all current viewer selections and stored viewer state.
   *
   * Responsibilities:
   *   - Hides all table panels
   *   - Hides all filtered entity groups
   *   - Resets all dropdown menus to their default placeholder options
   *   - Removes saved viewer state from localStorage
   *
   * This supports the "Show Schedule / Clear" behavior in the UI.
   */
  function clearViewerSelections() {
    hideAllPanels();
    hideAllEntityGroups();

    if (masterMenu) masterMenu.selectedIndex = 0;
    if (filterMenu) filterMenu.selectedIndex = 0;

    if (roomFilterSelect) roomFilterSelect.selectedIndex = 0;
    if (labFilterSelect) labFilterSelect.selectedIndex = 0;
    if (facultyFilterSelect) facultyFilterSelect.selectedIndex = 0;

    try {
      localStorage.removeItem("viewerTableMode");
      localStorage.removeItem("viewerTableGroup");
      localStorage.removeItem("viewerRoomFilter");
      localStorage.removeItem("viewerLabFilter");
      localStorage.removeItem("viewerFacultyFilter");
    } catch {
      // Ignore storage errors
    }
  }

  /**
   * Applies behavior specific to the currently selected panel.
   *
   * Parameters:
   *   panelKey (string):
   *     The identifier for the active panel.
   *
   * Responsibilities:
   *   - Hides all entity groups before applying a new filter
   *   - Auto-selects the first available dropdown option
   *   - Applies the corresponding room/lab/faculty filter
   *   - Saves the active entity filter to localStorage
   *
   * This function is used when switching into one of the
   * filtered schedule views.
   */
  function handlePanelSpecificBehavior(panelKey) {
    hideAllEntityGroups();

    if (panelKey === "filter-by-room-table") {
      autoSelectFirstOption(roomFilterSelect);
      applyEntityFilter(roomFilterSelect?.value, roomGroups, roomEmpty);

      try {
        localStorage.setItem("viewerRoomFilter", roomFilterSelect?.value || "");
      } catch {}
    }

    if (panelKey === "filter-by-lab-table") {
      autoSelectFirstOption(labFilterSelect);
      applyEntityFilter(labFilterSelect?.value, labGroups, labEmpty);

      try {
        localStorage.setItem("viewerLabFilter", labFilterSelect?.value || "");
      } catch {}
    }

    if (panelKey === "filter-by-faculty-table") {
      autoSelectFirstOption(facultyFilterSelect);
      applyEntityFilter(facultyFilterSelect?.value, facultyGroups, facultyEmpty);

      try {
        localStorage.setItem("viewerFacultyFilter", facultyFilterSelect?.value || "");
      } catch {}
    }
  }


  // ------------------------------------------------------------
  // 3. Initial State
  // ------------------------------------------------------------

  // Start with all panels hidden until a selection is made/restored.
  hideAllPanels();
  hideAllEntityGroups();


  // ------------------------------------------------------------
  // 4. Main Dropdown Handling
  // ------------------------------------------------------------

  /**
   * Attach change listeners to all top-level mode selectors.
   *
   * When the user changes a viewer mode:
   *   - Hide all panels
   *   - Show the selected panel
   *   - Reset the opposite dropdown
   *   - Apply any panel-specific filter behavior
   *   - Save the new mode in localStorage
   */
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

      // Handles the specific behavior for the panels
      handlePanelSpecificBehavior(panelKey);

      // Store the current viewer state so it can be restored later.
      try {
        localStorage.setItem("viewerTableMode", panelKey);
        localStorage.setItem("viewerTableGroup", group);
      } catch {
        // Ignore storage errors silently
      }
    });
  });


  // ------------------------------------------------------------
  // 5. Individual Entity Dropdown Handlers
  // ------------------------------------------------------------

  /**
   * Attach room filter listener.
   *
   * Shows only the selected room group and saves the room selection.
   */
  if (roomFilterSelect) {
    roomFilterSelect.addEventListener("change", () => {
      applyEntityFilter(roomFilterSelect.value, roomGroups, roomEmpty);

      try {
        localStorage.setItem("viewerRoomFilter", roomFilterSelect.value);
      } catch {}
    });
  }

  /**
   * Attach lab filter listener.
   *
   * Shows only the selected lab group and saves the lab selection.
   */
  if (labFilterSelect) {
    labFilterSelect.addEventListener("change", () => {
      applyEntityFilter(labFilterSelect.value, labGroups, labEmpty);

      try {
        localStorage.setItem("viewerLabFilter", labFilterSelect.value);
      } catch {}
    });
  }

  /**
   * Attach faculty filter listener.
   *
   * Shows only the selected faculty group and saves the faculty selection.
   */
  if (facultyFilterSelect) {
    facultyFilterSelect.addEventListener("change", () => {
      applyEntityFilter(facultyFilterSelect.value, facultyGroups, facultyEmpty);

      try {
        localStorage.setItem("viewerFacultyFilter", facultyFilterSelect.value);
      } catch {}
    });
  }


  // ------------------------------------------------------------
  // 6. Clear Button
  // ------------------------------------------------------------

  /**
   * Attach clear button behavior.
   *
   * Resets all visible panels, active filters, and saved viewer state.
   */
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      clearViewerSelections();
    });
  }


  // ------------------------------------------------------------
  // 7. Restore Prior State
  // ------------------------------------------------------------

  /**
   * Restore the viewer mode and entity filter selections from localStorage.
   *
   * Responsibilities:
   *   - Restore the last selected panel
   *   - Restore the matching top-level dropdown value
   *   - Reapply any saved room, lab, or faculty filter
   *   - Fallback to the first valid option if the saved value no longer exists
   *
   * This improves usability by preserving the user's prior viewer state
   * across page refreshes.
   */
  try {
    const savedKey = localStorage.getItem("viewerTableMode");
    const savedGroup = localStorage.getItem("viewerTableGroup");
    const savedRoom = localStorage.getItem("viewerRoomFilter");
    const savedLab = localStorage.getItem("viewerLabFilter");
    const savedFaculty = localStorage.getItem("viewerFacultyFilter");

    if (savedKey) {
      hideAllPanels();
      showPanel(savedKey);

      // Set dropdown to match saved selection
      if (savedGroup === "master" && masterMenu) masterMenu.value = savedKey;
      if (savedGroup === "filter" && filterMenu) filterMenu.value = savedKey;

      resetOtherMenu(savedGroup);

      if (savedKey === "filter-by-room-table" && roomFilterSelect) {
        if (
          savedRoom &&
          Array.from(roomFilterSelect.options).some((opt) => opt.value === savedRoom)
        ) {
          roomFilterSelect.value = savedRoom;
        } else {
          autoSelectFirstOption(roomFilterSelect);
        }

        applyEntityFilter(roomFilterSelect.value, roomGroups, roomEmpty);
      }

      if (savedKey === "filter-by-lab-table" && labFilterSelect) {
        if (
          savedLab &&
          Array.from(labFilterSelect.options).some((opt) => opt.value === savedLab)
        ) {
          labFilterSelect.value = savedLab;
        } else {
          autoSelectFirstOption(labFilterSelect);
        }

        applyEntityFilter(labFilterSelect.value, labGroups, labEmpty);
      }

      if (savedKey === "filter-by-faculty-table" && facultyFilterSelect) {
        if (
          savedFaculty &&
          Array.from(facultyFilterSelect.options).some((opt) => opt.value === savedFaculty)
        ) {
          facultyFilterSelect.value = savedFaculty;
        } else {
          autoSelectFirstOption(facultyFilterSelect);
        }

        applyEntityFilter(facultyFilterSelect.value, facultyGroups, facultyEmpty);
      }
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

// starts the generation process
async function startGenerationProgress() {
  const form = document.getElementById("generate");
  const barObject = document.getElementById("is-progress-bar-hidden");
  const progressBar = document.getElementById("progress-bar");

  barObject.style.display = "block";
  progressBar.value = 0;
  progress_bar_current_progress = 0;
  updateProgressUI(0);

  await fetch("/run/reset", {
    method: "POST",
    redirect: "manual",
  });

  const res = await fetch("/run/generate", {
    method: "POST",
    body: new FormData(form),
  });

  if (!res.ok) {
    console.error("Generation failed");
    return;
  }

  checkGenerationProgress();
}

// keeps track of the current progress of the progress bar
let progress_bar_current_progress = 0;

// Continuously checks for updates to the progress bar
async function checkGenerationProgress() {

    try {
        // Gets the current progress from the session
        const res = await fetch("/run/progress");
        const data = await res.json();

        // console.log("data received:", data)

        // if the generation is still in progress or the progress bar has to catch up
        if (data.progress < 100 || progress_bar_current_progress < 100) {
          
            // Periodically checks for schedule progress updates
            incrementProgressBar(data.progress)

            // determines how often to check for updates/speed of the progress bar
            setTimeout(() => checkGenerationProgress(data.progress), 250);
        } else {
              incrementProgressBar(100)

              progress_bar_current_progress = 0;

              // Redirects the user to the viewer page after a very short period
              const completeRes = await fetch("/run/complete", {
                method: "POST",
              });

              if (!completeRes.ok) {
                console.error("Generation completed, but results could not be saved.");
                return;
              }

              setTimeout(() => (window.location.href = "/viewer"), 1200);
        }
    // Catches any error thay may be thrown
    } catch (err) {
        console.error("Generation failed:", err);
    }
}

// increments the progress bar by a given % until it reaches the current progress
function incrementProgressBar(progress) {
    let distance = progress - progress_bar_current_progress
    let progress_speed_default = 1;
  

    // changes the speed of the progress bar based on how far away it is from the current progress
    if (distance <= 10) {
      progress_speed_default = 1;

    } else if (distance <= 20) {
      progress_speed_default = 2;

    } else if (distance <= 30) {
      progress_speed_default = 3
    }


    if (progress_bar_current_progress < progress) {
      progress_bar_current_progress += progress_speed_default;
      updateProgressUI(progress_bar_current_progress)
    }

}

// updates the progress bar and percent loaded with the given value
function updateProgressUI(current_progress) {
  const progress_bar = document.getElementById("progress-bar");
  const percentage_loaded = document.getElementById("percentage-loaded");

  progress_bar.value = progress_bar_current_progress;
  percentage_loaded.innerHTML = current_progress + "%";

  progress_bar_flavor_text(current_progress);
}

// changes the flavor-text to show the appropriate message based on percentage loaded
function progress_bar_flavor_text(progress) {
    const flavor_text = document.getElementById("flavor-text"); 

      if (progress == 0){
          flavor_text.innerHTML = "Please wait";

      } else if (progress == 25) {
          flavor_text.innerHTML = "About a quarter of the way there"

      } else if (progress == 50) {
          flavor_text.innerHTML = "Halfway there"

      } else if (progress == 75) {
          flavor_text.innerHTML = "Nearly there"

      } else if (progress == 100) {
          flavor_text.innerHTML = "Generation completed. Redirecting to viewer..."
      }

}