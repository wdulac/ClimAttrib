window.dashExtensions = Object.assign({}, window.dashExtensions, {
    geojson: {
        colorCell: function(feature, context){
            const selected = context.hideout.selected;
            const id = feature.properties.cell_id;
            if (id === selected) {
                return {
                    color: "#FF0000",
                    weight: 1,
                    fillOpacity: 0.5
                };
            }
            return {
                color: "#066e91",
                weight: 0.5,
                fillOpacity: 0.1
            };
        }
    }
})


window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        select_point: function(clickData) {
            if (!clickData) {
                return window.dash_clientside.no_update;
            }
            const lat = clickData.properties.lat;
            const lon = clickData.properties.lon;
            const id = clickData.properties.cell_id;
            return [
                { selected: id },
                JSON.stringify([lat, lon])
            ];
        }
    }
});