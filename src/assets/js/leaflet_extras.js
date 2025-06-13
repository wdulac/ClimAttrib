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