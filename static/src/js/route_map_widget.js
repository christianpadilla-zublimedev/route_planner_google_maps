/** @odoo-module SIN GOOGLE **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class RouteMapWidget extends Component {

    static template = "route_planner.RouteMapWidget";

    static props = {
        ...standardFieldProps,
    };


    setup() {

        this.mapContainer = useRef("map");
        this.map = null;

        onMounted(() => {
            setTimeout(() => {
                this.initMap();
            }, 500);
        });

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });

    }


    initMap() {

        console.log("ROUTE MAP INIT");

        const container = this.mapContainer.el;

        if (!container) {
            console.log("NO CONTAINER");
            return;
        }


        if (container._leaflet_id) {
            delete container._leaflet_id;
        }

        container.innerHTML = "";

        container.removeAttribute("class");
        container.className = "leaflet-container";


        container.style.width = "1260px";
        container.style.height = "500px";


        this.map = L.map(container)
            .setView(
                [20.6597, -103.3496],
                12
            );


        console.log("MAP CREATED");


        L.tileLayer(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
            }
        ).addTo(this.map);


        const orders = this.props.record.data.line_ids.records;


        orders.forEach((order) => {

            const latitude = parseFloat(order.data.latitude);
            const longitude = parseFloat(order.data.longitude);

            const name = order.data.display_order_name;

            if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
                console.log(
                    "PEDIDO SIN COORDENADAS:",
                    order.data.sale_order_id
                );
                return;
            }


            const popupContent = `
                <strong>${name}</strong>
                <br>
                Latitud: ${latitude}
                <br>
                Longitud: ${longitude}
            `;


            L.marker([latitude, longitude])
                .addTo(this.map)
                .bindPopup(popupContent);

        });


        const originLatitude = parseFloat(
            this.props.record.data.origin_latitude
        );

        const originLongitude = parseFloat(
            this.props.record.data.origin_longitude
        );

        const companyName = this.props.record.data.company_name;


        if (
            Number.isFinite(originLatitude) &&
            Number.isFinite(originLongitude)
        ) {

            const originPopup = `
                <strong>${companyName}</strong>
                <br>
                Latitud: ${originLatitude}
                <br>
                Longitud: ${originLongitude}
            `;


            L.marker([originLatitude, originLongitude])
                .addTo(this.map)
                .bindPopup(originPopup);

        }


        this.map.invalidateSize(true);

    }

}


registry.category("fields").add(
    "route_map",
    {
        component: RouteMapWidget,
    }
);