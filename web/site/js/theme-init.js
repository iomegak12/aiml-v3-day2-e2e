/* Classic (non-module) script loaded first in <head>: apply the saved NetCore theme before
   the first paint, so dark-mode users never see a light flash. Logic lives in theme.js;
   this file only mirrors its storage key and theme ids. */
(function () {
  try {
    var saved = window.localStorage.getItem("netcore-tac-theme");
    if (saved === "netcore-light" || saved === "netcore-dark") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (e) {
    /* storage blocked: keep the default from the markup */
  }
})();
