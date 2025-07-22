// TODO Find a cleaner way to add these buttons
window.fetch = new Proxy(window.fetch, {
  apply(fetch, that, args) {
    const result = fetch.apply(that, args);
    result.then((response) => {
      if (args[0] == '/_dash-update-component') {
        setTimeout(() => {
          if (window.plotlyExtras) {
            window.plotlyExtras.addFullscreenButton();
            window.plotlyExtras.addDownloadButton();
          }
        }, 500);
      }
    });
    return result;
  }
});


// Gestion de la sortie de plein écran
document.addEventListener("fullscreenchange", function () {
  const fullElement = document.fullscreenElement;
  if (!fullElement && window._previousFullscreenGraph) {
    const plot = window._previousFullscreenGraph.querySelector('.js-plotly-plot');
    if (plot && plot.layout && plot.layout.meta) {
      const meta = plot.layout.meta;
      const initialWidth = meta.initial_width || 800;
      const initialHeight = meta.initial_height || 600;
      Plotly.relayout(plot, {
        autosize: false,
        width: initialWidth,
        height: initialHeight
      });
    }
    window._previousFullscreenGraph = null;
  } else {
    window._previousFullscreenGraph = fullElement;
  }
});