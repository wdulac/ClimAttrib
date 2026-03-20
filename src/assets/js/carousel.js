window.dash_clientside = Object.assign({}, window.dash_clientside, {
  carousel: {
    // Prevent swiping interaction with the carousel when dragging the mouse
    // to zoom in on an arbitrary element identified by id.
    blockSwiper: function (id) {

      if (!(typeof id === 'string' || id instanceof String)) {
                  id = JSON.stringify(id, Object.keys(id).sort());
      };

      const el = document.getElementById(id);
      if (!el) return window.dash_clientside.no_update;

      ["mousedown", "touchstart"].forEach(evt =>
        el.addEventListener(evt, e => e.stopPropagation(), { passive: true })
      );

      return null;
    },

    toggleBounce: function(slideIndex) {
      const controls = document.querySelectorAll(".mantine-Carousel-control");
    
      controls.forEach((btn) => {
        if (slideIndex === 0) {
          if (btn.dataset.type === "next") {
            btn.classList.add("bounce-up");
          }
        } else {
          btn.classList.remove("bounce-up");
        }
      });
    
      return null;
    },

    showHint: function(slideIndex) {
      const nextBtn = document.querySelector(
        '.mantine-Carousel-control[data-type="next"]'
      );
    
      if (!nextBtn) return null;
    
      nextBtn.style.position = "relative";
    
      let hint = nextBtn.querySelector(".carousel-hint");
    
      // nettoyer tout timer précédent
      if (nextBtn._hintTimeout) {
        clearTimeout(nextBtn._hintTimeout);
        nextBtn._hintTimeout = null;
      }
    
      if (slideIndex === 0) {
    
        // créer si absent (mais invisible)
        if (!hint) {
          hint = document.createElement("div");
          hint.className = "carousel-hint";
          hint.textContent = "Click below to see more";
          nextBtn.appendChild(hint);
        }
    
        // apparition synchronisée avec le bounce (~9s)
        nextBtn._hintTimeout = setTimeout(() => {
          if (hint) {
            hint.classList.add("visible");
          }
        }, 9000); // à ajuster si besoin
    
      } else {
        // fade-out + cleanup
        if (hint) {
          hint.classList.remove("visible");
    
          setTimeout(() => {
            if (hint && hint.parentNode) {
              hint.parentNode.removeChild(hint);
            }
          }, 400);
        }
      }
    
      return null;
    },

    addTooltips: function(containerId) {
      const labels = ["Summary", "Probability", "Intensity"];
      const parent = document.getElementById(containerId);
      if (!parent) return null;

      const indicators = parent.querySelectorAll(".dmc-indicator");
      if (!indicators.length) {
          return false; // pas encore rendus
      }
      indicators.forEach((el, i) => {
          el.setAttribute("title", labels[i] || `Slide ${i + 1}`);
      });
      return true;
    }
  }
});