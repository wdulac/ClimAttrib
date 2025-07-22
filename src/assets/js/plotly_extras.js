// Namespace for interaction with dash clientside callbacks
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    plotly_extras: {
        // Look out for .plotly-notifier and move it into .user-select-none.svg-container
        hookPlotlyNotifier: function (containerId) {
    
        if (!(typeof containerId === 'string' || containerId instanceof String)) {
                    containerId = JSON.stringify(containerId, Object.keys(containerId).sort());
        };

        const parent = document.getElementById(containerId);
        if (!parent) return;
    
        const observer = new MutationObserver(() => {
          const container = parent.querySelector('.user-select-none.svg-container');
          const notifier = document.querySelector('.plotly-notifier');
          if (container && notifier && !container.contains(notifier)) {
            container.appendChild(notifier);
            observer.disconnect();
          }
        });
    
        observer.observe(document.body, { childList: true });
        }
    }
});


// ###### Global functions for fullscreen support ######

// Adding a fullscreen button to the mode bar
function addFullscreenButton() {
    const modeBars = document.querySelectorAll(".modebar-container");
    for (let i = 0; i < modeBars.length; i++) {
        const modeBarGroups = modeBars[i].querySelectorAll(".modebar-group");
        const modeBarBtns = modeBarGroups[modeBarGroups.length - 1].querySelectorAll(".modebar-btn");

        if (modeBarBtns[modeBarBtns.length - 1].getAttribute('data-title') !== 'Fullscreen') {
            const aTag = document.createElement('a');
            aTag.classList.add("modebar-btn", "custom-modebar-btn");
            aTag.setAttribute("rel", "tooltip");
            aTag.setAttribute("data-title", "Fullscreen");
            aTag.setAttribute("onClick", "fullscreen(this);");
            const iTag = document.createElement('i');
            iTag.className = 'fa-solid fa-maximize';
            aTag.appendChild(iTag);
            modeBarGroups[modeBarGroups.length - 1].appendChild(aTag);
        }
    }
}

// Fullscreen implementation
function fullscreen(el) {
    const graphContainer = el.closest('.dash-graph');
    const plot = graphContainer.querySelector('.js-plotly-plot');

    // Fonction pour passer en plein écran
    async function enterFullscreen() {
        if (graphContainer.requestFullscreen) {
            await graphContainer.requestFullscreen();
        } else if (graphContainer.webkitRequestFullscreen) {
            await graphContainer.webkitRequestFullscreen();
        } else if (graphContainer.mozRequestFullScreen) {
            await graphContainer.mozRequestFullScreen();
        } else if (graphContainer.msRequestFullscreen) {
            await graphContainer.msRequestFullscreen();
        }
    }

    // Fonction pour sortir du plein écran
    async function exitFullscreen() {
        if (document.exitFullscreen) {
            await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            await document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            await document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
            await document.msExitFullscreen();
        }
    }

    // Redimensionne le plot pour remplir son conteneur
    function resizePlotToContainer() {
        if (!plot) return;
        const containerRect = graphContainer.getBoundingClientRect();
        Plotly.relayout(plot, {
            autosize: true,
            width: containerRect.width,
            height: containerRect.height
        });
    }

    // Restaure la taille initiale stockée dans layout.meta
    function restoreInitialSize() {
        if (!plot) return;
        const meta = plot.layout.meta || {};
        const initialWidth = meta.initial_width || 800;
        const initialHeight = meta.initial_height || 600;
        Plotly.relayout(plot, {
            autosize: false,
            width: initialWidth,
            height: initialHeight
        });
    }

    if (document.fullscreenElement === graphContainer) {
        // Si on est déjà en plein écran sur ce graph, on sort du plein écran
        exitFullscreen().then(() => {
            restoreInitialSize();
        });
    } else {
        // Sinon on entre en plein écran
        enterFullscreen().then(() => {
            resizePlotToContainer();
        });
    }
}

// ###### Global functions for graph data CSV download ######

// Adding the download button to the modebar
function addDownloadButton() {
    const modeBars = document.querySelectorAll(".modebar-container");
    for (let i = 0; i < modeBars.length; i++) {
        const modeBarGroups = modeBars[i].querySelectorAll(".modebar-group");
        const modeBarBtns = modeBarGroups[modeBarGroups.length - 1].querySelectorAll(".modebar-btn");

        // On évite de le rajouter plusieurs fois
        const alreadyAdded = Array.from(modeBarBtns).some(btn => btn.getAttribute('data-title') === 'Download CSV');
        if (alreadyAdded) continue;

        const aTag = document.createElement('a');
        aTag.classList.add("modebar-btn", "custom-modebar-btn");
        aTag.setAttribute("rel", "tooltip");
        aTag.setAttribute("data-title", "Download CSV");
        aTag.setAttribute("onClick", "downloadCSV(this);");
        const iTag = document.createElement('i');
        iTag.className = 'fa-solid fa-file-arrow-down';
        aTag.appendChild(iTag);
        modeBarGroups[modeBarGroups.length - 1].appendChild(aTag);
    }
}

// Requesting and downloading CSV data from the server
function downloadCSV(el) {
    const graphContainer = el.closest('.dash-graph');
    const plot = graphContainer.querySelector('.js-plotly-plot');

    if (!plot || !plot.layout || !plot.layout.meta) {
        alert("No data available for download.");
        return;
    }

    const vars = plot.layout.meta.variables;
    const taskId = plot.layout.meta.task_id;

    fetch(`/download_csv?task_id=${taskId}&variables=${vars}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to download CSV");
    
            const disposition = response.headers.get("Content-Disposition");
            let filename = "data.csv";  // default filename
    
            if (disposition && disposition.includes("filename=")) {
                const match = disposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) {
                    filename = match[1];
                }
            }
    
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => alert("Erreur téléchargement : " + err.message));
}



// Export into plotlyExtras namespace for calling in init.js
window.plotlyExtras = {
  addFullscreenButton,
  addDownloadButton
};