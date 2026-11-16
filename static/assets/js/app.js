/* Bakgomong: DOM enhancement only. Every page has its own actual HTML file and page structure.
 * This is not secure authentication, payment processing, or backend authorisation.
 */
(() => {
  "use strict";
 
  const DEFAULT = window.BAKGOMONG_SAMPLE;
  const CFG = window.BAKGOMONG_CONFIG || {};
  const KEY = "bakgomong-model-frontend-demo-v2",
    WHO = "bakgomong-preview-persona";

  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));
  

  function renderShell() {
    
    $("#open-sidebar")?.addEventListener("click", () => {
      $("#sidebar")?.classList.add("open");
      $("#sidebar-overlay").hidden = false;
    });
    let close = () => {
      $("#sidebar")?.classList.remove("open");
      if ($("#sidebar-overlay")) $("#sidebar-overlay").hidden = true;
    };
    $("#close-sidebar")?.addEventListener("click", close);
    $("#sidebar-overlay")?.addEventListener("click", close);
    
    
  }

  
  renderShell();
  // setupDownloads();
  
})();
