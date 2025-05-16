//Script to show Plotly graph to fullscreen mode
//Dependence on Font Awesome icons
//Author: Dhirendra Kumar
//Created: 26-Nov-2024
//Adapted to fixed size figures: 16-May-2025
//By: William Dulac

function addToModbar() {
    const modeBars = document.querySelectorAll(".modebar-container");
    for(let i=0; i<modeBars.length; i++) {
        const modeBarGroups = modeBars[i].querySelectorAll(".modebar-group");
        const modeBarBtns = modeBarGroups[modeBarGroups.length - 1].querySelectorAll(".modebar-btn");

        if (modeBarBtns[modeBarBtns.length - 1].getAttribute('data-title') !== 'Fullscreen') {
            const aTag = document.createElement('a');
            aTag.className = "modebar-btn";
            aTag.setAttribute("rel", "tooltip");
            aTag.setAttribute("data-title", "Fullscreen");
            aTag.setAttribute("style", "color:gray");
            aTag.setAttribute("onClick", "fullscreen(this);");
            const iTag = document.createElement('i');
            iTag.className = 'fa-solid fa-maximize';
            aTag.appendChild(iTag);
            modeBarGroups[modeBarGroups.length - 1].appendChild(aTag);
        }
    }
}


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
            resizePlotToContainer()
        });
    }
}


window.fetch = new Proxy(window.fetch, {
    apply(fetch, that, args) {
        // Forward function call to the original fetch
        const result = fetch.apply(that, args);

        // Do whatever you want with the resulting Promise
        result.then((response) => {
            if (args[0] == '/_dash-update-component') {
                setTimeout(addToModbar, 200)
            }})
        return result
        }
})