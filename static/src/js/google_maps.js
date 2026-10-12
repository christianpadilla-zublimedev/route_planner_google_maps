/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class GoogleRouteMapWidget extends Component {

    static template = "route_planner.GoogleRouteMapWidget";

    static props = {
        ...standardFieldProps,
    };

    setup() {

        this.mapContainer = useRef("map");
        this.map = null;
        this.routePolyline = null;
        this.markers = [];

        onMounted(() => {

            setTimeout(() => {
                this.initMap();
            }, 500);

        });

        onWillUnmount(() => {

            if (this.routePolyline) {
                this.routePolyline.setMap(null);
                this.routePolyline = null;
            }

            this.markers.forEach((marker) => {
                marker.setMap(null);
            });

            this.markers = [];

            if (this.map) {
                this.map = null;
            }

        });
    }


    async initMap() {

        console.log("GOOGLE ROUTE MAP INIT");

        const container = this.mapContainer.el;

        if (!container) {

            console.log("NO GOOGLE MAP CONTAINER");

            return;
        }


        /*
         * ==========================================
         * MISMO HACK DE RENDERIZADO DE ODOO
         * ==========================================
         */

        container.innerHTML = "";

        container.removeAttribute("class");
        container.className = "google-route-map-container";

        container.style.width = "1260px";
        container.style.height = "500px";


        /*
         * ==========================================
         * OBTENER API KEY DESDE TU ENDPOINT
         * ==========================================
         */

        let apiKey;

        try {

            const response = await fetch(
                "/route_planner/google_maps_api_key",
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );


            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );

            }


            const data = await response.json();

            apiKey = data.api_key;


        } catch (error) {

            console.error(
                "ERROR OBTENIENDO GOOGLE MAPS API KEY:",
                error
            );

            return;
        }


        if (!apiKey) {

            console.error(
                "NO GOOGLE MAPS JAVASCRIPT API KEY"
            );

            return;
        }


        console.log(
            "GOOGLE MAPS API KEY OBTENIDA"
        );


        /*
         * ==========================================
         * CARGAR GOOGLE MAPS
         * ==========================================
         */

        try {

            await this.loadGoogleMaps(apiKey);

        } catch (error) {

            console.error(
                "ERROR CARGANDO GOOGLE MAPS:",
                error
            );

            return;
        }


        /*
         * ==========================================
         * CREAR MAPA
         * ==========================================
         */

        const originLatitude = parseFloat(
            this.props.record.data.origin_latitude
        );

        const originLongitude = parseFloat(
            this.props.record.data.origin_longitude
        );


        let center = {
            lat: 20.6597,
            lng: -103.3496,
        };


        if (
            Number.isFinite(originLatitude) &&
            Number.isFinite(originLongitude)
        ) {

            center = {
                lat: originLatitude,
                lng: originLongitude,
            };

        }


        this.map = new google.maps.Map(
            container,
            {
                center: center,
                zoom: 12,
                mapTypeControl: true,
                streetViewControl: true,
                fullscreenControl: true,
            }
        );


        console.log(
            "GOOGLE MAP CREATED"
        );


        /*
         * ==========================================
         * MARCADORES
         * ==========================================
         */

        this.addMarkers();


        /*
         * ==========================================
         * RUTA
         * ==========================================
         */

        await this.drawRoute();


        /*
         * ==========================================
         * FORZAR REDIBUJADO
         * ==========================================
         */

        setTimeout(() => {

            if (!this.map) {
                return;
            }

            google.maps.event.trigger(
                this.map,
                "resize"
            );

        }, 300);

    }


    async loadGoogleMaps(apiKey) {

        /*
         * ==========================================
         * GOOGLE YA CARGADO
         * ==========================================
         */

        if (
            window.google &&
            window.google.maps &&
            window.google.maps.importLibrary
        ) {

            return;

        }


        /*
         * ==========================================
         * CARGA YA EN PROCESO
         * ==========================================
         */

        if (window.routePlannerGoogleMapsPromise) {

            return window.routePlannerGoogleMapsPromise;

        }


        /*
         * ==========================================
         * CARGAR SCRIPT
         * ==========================================
         */

        window.routePlannerGoogleMapsPromise =
            new Promise((resolve, reject) => {

                const callbackName =
                    "__routePlannerGoogleMapsLoaded";


                window[callbackName] = () => {

                    delete window[callbackName];

                    resolve();

                };


                const script =
                    document.createElement("script");


                script.src =
                    "https://maps.googleapis.com/maps/api/js"
                    + "?key=" + encodeURIComponent(apiKey)
                    + "&loading=async"
                    + "&libraries=geometry"
                    + "&callback=" + callbackName;


                script.async = true;
                script.defer = true;


                script.onerror = () => {

                    delete window[callbackName];

                    window.routePlannerGoogleMapsPromise = null;

                    reject(
                        new Error(
                            "No se pudo cargar Google Maps JavaScript API."
                        )
                    );

                };


                document.head.appendChild(script);

            });


        return window.routePlannerGoogleMapsPromise;
    }


    addMarkers() {

        const orders =
            this.props.record.data.line_ids.records;


        /*
         * ==========================================
         * PEDIDOS
         * ==========================================
         */

        orders.forEach((order) => {

            const latitude =
                parseFloat(order.data.latitude);

            const longitude =
                parseFloat(order.data.longitude);


            const name =
                order.data.display_order_name;


            if (
                !Number.isFinite(latitude) ||
                !Number.isFinite(longitude)
            ) {

                console.log(
                    "PEDIDO SIN COORDENADAS:",
                    order.data.sale_order_id
                );

                return;
            }


            const marker =
                new google.maps.Marker({

                    position: {
                        lat: latitude,
                        lng: longitude,
                    },

                    map: this.map,

                    title: name,

                });


            const infoWindow =
                new google.maps.InfoWindow({

                    content: `
                        <strong>${name}</strong>
                        <br>
                        Latitud: ${latitude}
                        <br>
                        Longitud: ${longitude}
                    `,

                });


            marker.addListener(
                "click",
                () => {

                    infoWindow.open({
                        map: this.map,
                        anchor: marker,
                    });

                }
            );


            this.markers.push(marker);

        });


        /*
         * ==========================================
         * ORIGEN
         * ==========================================
         */

        const originLatitude =
            parseFloat(
                this.props.record.data.origin_latitude
            );

        const originLongitude =
            parseFloat(
                this.props.record.data.origin_longitude
            );


        const companyName =
            this.props.record.data.company_name;


        if (
            Number.isFinite(originLatitude) &&
            Number.isFinite(originLongitude)
        ) {

            const originMarker =
                new google.maps.Marker({

                    position: {
                        lat: originLatitude,
                        lng: originLongitude,
                    },

                    map: this.map,

                    title: companyName,

                });


            const originInfo =
                new google.maps.InfoWindow({

                    content: `
                        <strong>${companyName}</strong>
                        <br>
                        Latitud: ${originLatitude}
                        <br>
                        Longitud: ${originLongitude}
                    `,

                });


            originMarker.addListener(
                "click",
                () => {

                    originInfo.open({
                        map: this.map,
                        anchor: originMarker,
                    });

                }
            );


            this.markers.push(originMarker);

        }

    }


    async drawRoute() {

        const encodedPolyline =
            this.props.record.data.route_polyline;


        if (!encodedPolyline) {

            console.log(
                "NO HAY ROUTE POLYLINE"
            );

            return;
        }


        console.log(
            "DRAWING GOOGLE ROUTE"
        );


        /*
         * ==========================================
         * GEOMETRY LIBRARY
         * ==========================================
         */

        const {
            encoding
        } = await google.maps.importLibrary(
            "geometry"
        );


        /*
         * ==========================================
         * DECODIFICAR POLYLINE
         * ==========================================
         */

        const path =
            encoding.decodePath(
                encodedPolyline
            );


        if (!path.length) {

            console.log(
                "POLYLINE VACÍA"
            );

            return;
        }


        /*
         * ==========================================
         * DIBUJAR RUTA
         * ==========================================
         */

        this.routePolyline =
            new google.maps.Polyline({

                path: path,

                geodesic: true,

                strokeColor: "#1565C0",

                strokeOpacity: 1.0,

                strokeWeight: 5,

                map: this.map,

            });


        /*
         * ==========================================
         * AJUSTAR MAPA A LA RUTA
         * ==========================================
         */

        const bounds =
            new google.maps.LatLngBounds();


        path.forEach((point) => {

            bounds.extend(point);

        });


        this.map.fitBounds(bounds);


        console.log(
            "GOOGLE ROUTE DRAWN"
        );

    }

}


registry.category("fields").add(
    "google_route_map",
    {
        component: GoogleRouteMapWidget,
    }
);