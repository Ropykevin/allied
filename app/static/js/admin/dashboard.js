/** Admin dashboard helpers */
(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    var bars = document.querySelectorAll("[data-trend-bar]");
    var max = 0;
    bars.forEach(function (bar) {
      max = Math.max(max, Number(bar.getAttribute("data-value") || 0));
    });
    bars.forEach(function (bar) {
      var value = Number(bar.getAttribute("data-value") || 0);
      var pct = max ? Math.max(8, (value / max) * 100) : 8;
      bar.style.height = pct + "%";
    });
  });
})();
