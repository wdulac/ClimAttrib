window.dash_clientside = Object.assign({}, window.dash_clientside, {
  carousel: {
    blockSwiper: function (id) {
      const el = document.getElementById(id);
      if (!el) return window.dash_clientside.no_update;

      // Stop propagation of drag events inside plotly zone
      ["mousedown", "touchstart"].forEach(evt =>
        el.addEventListener(evt, e => e.stopPropagation(), { passive: true })
      );

      return null;
    }
  }
});