/* Click an artwork to see it larger. Esc or click anywhere to close.
   ~40 lines, no dependencies. Remove the <script> tag to disable. */

(function () {
  var pieces = document.querySelectorAll(".piece img");
  if (!pieces.length) return;

  var box = document.createElement("figure");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", "Enlarged artwork");
  box.innerHTML =
    '<button class="lightbox__close" type="button" aria-label="Close">&times;</button>' +
    '<div><img alt=""><figcaption></figcaption></div>';
  document.body.appendChild(box);

  var img = box.querySelector("img");
  var cap = box.querySelector("figcaption");
  var lastFocused = null;

  function open(source) {
    lastFocused = document.activeElement;
    img.src = source.currentSrc || source.src;
    img.alt = source.alt;
    var fig = source.closest(".piece");
    var c = fig && fig.querySelector("figcaption");
    cap.innerHTML = c ? c.innerHTML : "";
    box.setAttribute("open-state", "on");
    box.querySelector(".lightbox__close").focus();
  }

  function close() {
    box.removeAttribute("open-state");
    img.removeAttribute("src");
    if (lastFocused) lastFocused.focus();
  }

  pieces.forEach(function (el) {
    el.addEventListener("click", function () { open(el); });
  });

  box.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && box.hasAttribute("open-state")) close();
  });
})();
