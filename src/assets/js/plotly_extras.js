// plotly_extras.js

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
        },

        // Add our custom buttons to the modebar of a plotly plot (1 call per plot)
        addButtonsToModebar: function(containerId) {

            if (!(typeof containerId === 'string' || containerId instanceof String)) {
                containerId = JSON.stringify(containerId, Object.keys(containerId).sort());
            }
            const parent = document.getElementById(containerId);
            if (!parent) return null;
        
            // Function to add buttons once modebar exists
            function tryAddButtons() {
                const modebars = parent.querySelectorAll('.modebar-container');
                if (modebars.length === 0) {
                    // modebar not yet present, wait for it with MutationObserver
                    return false;
                }
                // Call your existing global functions scoped to this container
                addCustomModebarGroup(parent);
                return true;
            }
        
            // Try once immediately
            if (tryAddButtons()) {
                return null; // buttons added
            }
        
            // If not added, observe for modebar insertion
            const observer = new MutationObserver((mutations, obs) => {
                if (tryAddButtons()) {
                    obs.disconnect();
                }
            });
        
            observer.observe(parent, { childList: true, subtree: true });
        
            return null;
        }
    }
});

// ---------- Plotly Buttons Management ----------

// Generic function to create a new modebar button
function createModebarButton(title, iconClass, onClickHandler) {
    const btn = document.createElement("button");
    btn.classList.add("modebar-btn", "custom-modebar-btn");
    btn.setAttribute("type", "button");
    btn.setAttribute("rel", "tooltip");
    btn.setAttribute("data-title", title);

    btn.addEventListener("click", function () {
        onClickHandler(btn);
    });

    const icon = document.createElement("i");
    icon.className = iconClass;
    btn.appendChild(icon);

    return btn;
}

// Create a new modebar button group for our custom buttons
function addCustomModebarGroup(container = document) {

    const modebars = container.querySelectorAll(".modebar");

    for (const modebar of modebars) {

        if (modebar.querySelector(".modebar-group.custom-modebar-group")) {
            continue;
        }

        const group = document.createElement("div");
        group.classList.add("modebar-group", "custom-modebar-group");

        const fullscreenBtn = createModebarButton(
            "Fullscreen",
            "fa-solid fa-maximize",
            fullscreen
        );

        const downloadBtn = createModebarButton(
            "Download CSV",
            "fa-solid fa-file-arrow-down",
            downloadCSV
        );

        group.appendChild(fullscreenBtn);
        group.appendChild(downloadBtn);

        modebar.appendChild(group);
    }
}

// ---------- Fullscreen functionality ----------

function fullscreen(el) {
    const graphContainer = el.closest('.dash-graph');
    const plot = graphContainer.querySelector('.js-plotly-plot');

    async function enterFullscreen() {
        if (graphContainer.requestFullscreen) await graphContainer.requestFullscreen();
        else if (graphContainer.webkitRequestFullscreen) await graphContainer.webkitRequestFullscreen();
        else if (graphContainer.mozRequestFullScreen) await graphContainer.mozRequestFullScreen();
        else if (graphContainer.msRequestFullscreen) await graphContainer.msRequestFullscreen();
    }

    async function exitFullscreen() {
        if (document.exitFullscreen) await document.exitFullscreen();
        else if (document.webkitExitFullscreen) await document.webkitExitFullscreen();
        else if (document.mozCancelFullScreen) await document.mozCancelFullScreen();
        else if (document.msExitFullscreen) await document.msExitFullscreen();
    }

    function resizePlotToContainer() {
        if (!plot) return;
        const containerRect = graphContainer.getBoundingClientRect();
        Plotly.relayout(plot, {
            autosize: true,
            width: containerRect.width,
            height: containerRect.height
        });
    }

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
        exitFullscreen().then(() => restoreInitialSize());
    } else {
        enterFullscreen().then(() => resizePlotToContainer());
    }
}

// Handle exiting fullscreen event and restore original plot size
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

// ---------- CSV Download functionality ----------

function downloadCSV(el) {
    const graphContainer = el.closest('.dash-graph');
    const plot = graphContainer.querySelector('.js-plotly-plot');

    if (!plot || !plot.layout || !plot.layout.meta) {
        alert("No data available for download.");
        return;
    }

    const vars = plot.layout.meta.variables;
    const cacheKey = plot.layout.meta.key;

    fetch(`/eventtest/api/download_csv?key=${cacheKey}&variables=${vars}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to download CSV");

            const disposition = response.headers.get("Content-Disposition");
            let filename = "data.csv";

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
        .catch(err => alert("Download error: " + err.message));
}