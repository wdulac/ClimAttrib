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
      controls.forEach((btn, idx) => {
        if (slideIndex === 0) {
          // Slide 0 → on ajoute les classes d’animation
          if (idx === 0) {
            btn.classList.add("bounce-down");
          } else if (idx === 1) {
            btn.classList.add("bounce-up");
          }
        } else {
          // Sur les autres slides → on retire
          btn.classList.remove("bounce-down");
          btn.classList.remove("bounce-up");
        }
      });
      return null;  // dcc.Store n’a pas besoin de vraie valeur ici
    }
  }
});