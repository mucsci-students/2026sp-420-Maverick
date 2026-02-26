/*
Author:
Date: 2026-02-25

JavaScript Utilities – Schedule Viewer UI Logic

Purpose:
    Provides client-side behavior for the Schedule Viewer page.

Design Notes:
    - Panels are identified using the class "tab-panel".
    - Each dropdown option corresponds to a panel with id:
          tab-<value>
    - Dropdowns are grouped using data-group:
          "master" or "filter"
    - When one dropdown is used, the other resets to its placeholder.
    - localStorage persistence is optional and safely wrapped in try/catch.
*/

// app/web/static/app.js

document.addEventListener("DOMContentLoaded", () => {

  // ------------------------------------------------------------
  // 1. Element References
  // ------------------------------------------------------------

  // All table panels that may be shown/hidden
  const panels = document.querySelectorAll(".tab-panel");

  // All dropdowns controlling table mode
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

  // On initial page load, hide all panels
  // (both dropdowns default to placeholder state)
  hideAllPanels();


  // ------------------------------------------------------------
  // 4. Dropdown Change Event Handling
  // ------------------------------------------------------------

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

      // Optional: remember last selection
      try {
        localStorage.setItem("viewerTableMode", panelKey);
        localStorage.setItem("viewerTableGroup", group);
      } catch {
        // Ignore storage errors silently
      }
    });
  });

  // Optional: restore last selection 
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
});
