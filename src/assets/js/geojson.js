// Functions passed as argument in Python through dash_extensions.javascript.Namespace
window.dashExtensions = Object.assign({}, window.dashExtensions, {
    geojson: {
        colorCell: function(feature, context){
            const selected = context.hideout.selected;
            const id = feature.properties.cell_id;
            if (id === selected) {
                return {
                    color: "#FF0000",
                    weight: 0.5,
                    fillOpacity: 0.3
                };
            }
            return {
                color: "#066e91",
                weight: 0.5,
                fillOpacity: 0.1
            };
        },
        zoomFilter: function(feature, context) {
            const zoom = context.hideout.zoom || 0;
            const threshold = context.hideout.zoom_threshold || 6;
            return zoom >= threshold;
        }
    }
})

// Clientside Callbacks related functions
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        // Updates both GeoJSON's hideout prop with the selected cell's ID (used by colorCell)
        // and the 'selected-point' dcc.Store with the grid point coordinates.
        // Handles clearing out both elements when zooming-out.   
        select_point: function(clickData, zoom, hideout) {

            if (zoom < hideout.zoom_threshold) {
                return [
                    { ...hideout, selected: null},
                    null
                ];
            }

            if (!clickData) {
                return [
                    window.dash_clientside.no_update,
                    window.dash_clientside.no_update
                ];
            }
            
            const lat = clickData.properties.lat;
            const lon = clickData.properties.lon;
            const id = clickData.properties.cell_id;

            return [
                {...hideout, selected: id},
                JSON.stringify([lat, lon])
            ];
        },
        // Updates GeoJSON's hideout prop with current zoom-level (used by zoomFilter)
        update_zoom: function(zoom, hideout) {
            // Clone hideout object as to not replace in-place (which doesn't trigger the filter)
            hideout.zoom = zoom;

            return { ...hideout };
        },
        updateGridTiles: function(bounds) {

                    if (!bounds) return window.dash_clientside.no_update;

                    const url = `/grid_dynamic?bounds=${JSON.stringify(bounds)}`;
                    fetch(url).then(r => r.json()).then(data => {
                        const layer = window.dash_leaflet.get("geojson");
                        if (layer) {
                            layer.clearLayers();
                            layer.addData(data);
                        }
                    });
                    return window.dash_clientside.no_update;
                }
    }
});