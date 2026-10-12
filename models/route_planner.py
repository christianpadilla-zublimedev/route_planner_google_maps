import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

class RoutePlanner(models.Model):
    _name = "route.planner"
    _description = "Route Planner"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]


    name = fields.Char(
        string="Route",
        required=True,
        readonly=True,
        copy=False,
        default="New",
    )




    whatsapp_link = fields.Char(
        string="Link de WhatsApp",
        readonly=True,
        copy=True,
    )
    


    route_distance_km = fields.Float(
        string="Distancia (km)",
        readonly=True,
        tracking=True,
    )

    route_duration_hours = fields.Float(
        string="Duración (horas)",
        readonly=True,
        tracking=True,
    )


    route_flexibility = fields.Float(
        string="Flexibilidad de la ruta (horas)",
        default=0.0,
        tracking=True,
    )


    route_polyline = fields.Text(
        string="Route Polyline",
        readonly=True,
    )


    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
    )


    state = fields.Selection(
        [
            ("draft", "En Plan de entrega"),
            ("planned", "En Transito"),
            ("done", "Finalizada"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )


    line_ids = fields.One2many(
        "route.planner.line",
        "route_id",
        string="Ordenes",
        tracking=True,
    )


    route_date = fields.Date(
        string="Fecha de la Ruta",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )


    company_id = fields.Many2one(
        "res.company",
        string="Origen de entregas",
        default=lambda self: self.env.company,
        required=True,
        tracking=True,
    )


    # Coordenadas de origen de la empresa
    origin_latitude = fields.Char(
        string="Origen: Latitud",
        related="company_id.route_latitude",
        readonly=True,
        tracking=True,
    )

    origin_longitude = fields.Char(
        string="Origen: Longitud",
        related="company_id.route_longitude",
        readonly=True,
        tracking=True,
    )


    company_name = fields.Char(
        string="Empresa",
        readonly=True,
    )


    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Almacén",
        readonly=True,
    )


    user_id = fields.Many2one(
        "res.users",
        string="Conductor",
        tracking=True,
    )


    # NUEVO: Vehículo asignado a la ruta
    vehicle_id = fields.Many2one(
        "route.vehicle",
        string="Vehículo",
        tracking=True,
    )


    # NUEVO: Gasto combustible
    fuel_expense = fields.Monetary(
        string="Gasto de Combustible",
        currency_field="currency_id",
        tracking=True,
    )


    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )


    notes = fields.Text(
        string="Notes",
    )


    map_view = fields.Char(
        string="Map",
        default="",
    )



    route_polyline = fields.Text(
        string="Route Polyline",
        readonly=True,
    )



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "route.planner"
                ) or "New"

            company_id = vals.get("company_id") or self.env.company.id
            company = self.env["res.company"].browse(company_id)
            vals["company_name"] = company.name

        return super().create(vals_list)


    def _get_total_weight_kg(self):
        self.ensure_one()

        total_weight = 0.0

        for route_line in self.line_ids:
            sale_order = route_line.sale_order_id

            for order_line in sale_order.order_line:
                if order_line.display_type:
                    continue

                product = order_line.product_id

                if not product or not product.weight:
                    continue

                quantity = order_line.product_uom._compute_quantity(
                    order_line.product_uom_qty,
                    product.uom_id,
                )

                total_weight += product.weight * quantity

        return total_weight


    def _validate_start_route(self):
        for route in self:
            if not route.user_id:
                raise UserError(
                    "Debe seleccionar un conductor antes de cambiar "
                    "la ruta a En Tránsito."
                )

            if not route.vehicle_id:
                raise UserError(
                    "Debe seleccionar un vehículo antes de cambiar "
                    "la ruta a En Tránsito."
                )

            vehicle_capacity = route.vehicle_id.capacity_kg

            if vehicle_capacity <= 0:
                raise UserError(
                    "El vehículo seleccionado no tiene una capacidad "
                    "de carga válida configurada."
                )

            total_weight = route._get_total_weight_kg()

            if total_weight > vehicle_capacity:
                excess_weight = total_weight - vehicle_capacity

                raise UserError(
                    "La carga sobrepasa la capacidad del vehículo.\n\n"
                    "Peso total de la carga: %.2f kg\n"
                    "Capacidad del vehículo: %.2f kg\n"
                    "Exceso de carga: %.2f kg\n\n"
                    "Quite uno o más pedidos o reduzca las cantidades "
                    "antes de iniciar la ruta."
                    % (
                        total_weight,
                        vehicle_capacity,
                        excess_weight,
                    )
                )


    def write(self, vals):
        if "company_id" in vals:
            company = self.env["res.company"].browse(
                vals["company_id"]
            )
            vals["company_name"] = company.name

        result = super().write(vals)

        if vals.get("state") == "planned":
            self._validate_start_route()

        return result




    def action_calculate_route(self):
        self.ensure_one()

        # ==========================================
        # GOOGLE ROUTES API KEY
        # ==========================================

        api_key = self.env["ir.config_parameter"].sudo().get_param(
            "route_planner.google_maps_routes_api_key"
        )

        if not api_key:
            raise UserError(
                "No está configurada la Google Maps Routes API Key."
            )

        # ==========================================
        # ORIGEN
        # ==========================================

        if not self.origin_latitude or not self.origin_longitude:
            raise UserError(
                "La ruta no tiene coordenadas de origen."
            )

        try:
            origin_latitude = float(self.origin_latitude)
            origin_longitude = float(self.origin_longitude)
        except (TypeError, ValueError):
            raise UserError(
                "Las coordenadas de origen no son válidas:\n"
                "Latitud: %s\n"
                "Longitud: %s"
                % (
                    self.origin_latitude,
                    self.origin_longitude,
                )
            )

        origin = {
            "location": {
                "latLng": {
                    "latitude": origin_latitude,
                    "longitude": origin_longitude,
                }
            }
        }

        # ==========================================
        # PEDIDOS
        # ==========================================

        lines = self.line_ids.sorted(
            key=lambda line: line.sequence
        )

        if not lines:
            raise UserError(
                "La ruta no tiene pedidos."
            )

        # ==========================================
        # VALIDAR COORDENADAS DE PEDIDOS
        # ==========================================

        for line in lines:

            if not line.latitude or not line.longitude:
                raise UserError(
                    "El pedido %s no tiene coordenadas."
                    % (
                        line.display_order_name
                        or line.sale_order_id.display_name
                    )
                )

            try:
                float(line.latitude)
                float(line.longitude)
            except (TypeError, ValueError):
                raise UserError(
                    "Las coordenadas del pedido %s no son válidas.\n"
                    "Latitud: %s\n"
                    "Longitud: %s"
                    % (
                        line.display_order_name
                        or line.sale_order_id.display_name,
                        line.latitude,
                        line.longitude,
                    )
                )

        # ==========================================
        # DESTINO
        #
        # El destino final es nuevamente la empresa.
        # ==========================================

        destination = {
            "location": {
                "latLng": {
                    "latitude": origin_latitude,
                    "longitude": origin_longitude,
                }
            }
        }

        # ==========================================
        # INTERMEDIOS
        #
        # Todos los pedidos según sequence.
        # ==========================================

        intermediates = []

        for line in lines:

            intermediates.append({
                "location": {
                    "latLng": {
                        "latitude": float(line.latitude),
                        "longitude": float(line.longitude),
                    }
                }
            })

        # ==========================================
        # GOOGLE ROUTES API
        # ==========================================

        url = (
            "https://routes.googleapis.com/"
            "directions/v2:computeRoutes"
        )

        payload = {
            "origin": origin,
            "destination": destination,
            "intermediates": intermediates,
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
            "computeAlternativeRoutes": False,
            "languageCode": "es-MX",
            "units": "METRIC",
        }

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "routes.distanceMeters,"
                "routes.duration,"
                "routes.polyline.encodedPolyline"
            ),
        }

        # ==========================================
        # LLAMADA
        # ==========================================

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )

        except requests.RequestException as error:
            raise UserError(
                "Error conectando con Google Routes API:\n\n%s"
                % error
            )

        # ==========================================
        # RESPUESTA HTTP
        # ==========================================

        if response.status_code != 200:
            raise UserError(
                "Google Routes API devolvió un error.\n\n"
                "HTTP: %s\n\n"
                "%s"
                % (
                    response.status_code,
                    response.text,
                )
            )

        # ==========================================
        # JSON
        # ==========================================

        try:
            result = response.json()

        except ValueError:
            raise UserError(
                "Google Routes API no devolvió un JSON válido.\n\n"
                "%s"
                % response.text
            )

        # ==========================================
        # RUTAS
        # ==========================================

        routes = result.get("routes", [])

        if not routes:
            raise UserError(
                "Google Routes API no devolvió ninguna ruta.\n\n"
                "Respuesta:\n%s"
                % result
            )

        route = routes[0]

        # ==========================================
        # RESULTADO
        # ==========================================

        distance = route.get("distanceMeters")

        duration = route.get("duration")

        polyline = (
            route.get("polyline", {})
            .get("encodedPolyline")
        )

        if not polyline:
            raise UserError(
                "Google calculó la ruta pero no devolvió "
                "la polyline.\n\n"
                "Respuesta:\n%s"
                % result
            )

        # ==========================================
        # GUARDAR POLYLINE
        # ==========================================

        self.write({
            "route_polyline": polyline,
            "route_distance_km": (distance or 0) / 1000,
            "route_duration_hours": (
                int(duration.rstrip("s")) / 3600
                + self.route_flexibility
                if duration
                else 0
            ),
        })

        # ==========================================
        # FINAL
        # ==========================================

        return True


    
    def action_generate_link(self):
        self.ensure_one()

        if not self.route_polyline:
            raise UserError(
                "No se ha calculado la ruta. "
                "Primero calcula la ruta para poder generar el enlace de la ruta en el mapa."
            )

        if not self.origin_latitude or not self.origin_longitude:
            raise UserError(
                "La ruta no tiene coordenadas de origen."
            )

        lines = self.line_ids.sorted(key=lambda line: line.sequence)

        if not lines:
            raise UserError(
                "La ruta no tiene pedidos."
            )

        waypoints = []

        for line in lines:
            if not line.latitude or not line.longitude:
                raise UserError(
                    "El pedido %s no tiene coordenadas."
                    % (
                        line.display_order_name
                        or line.sale_order_id.display_name
                    )
                )

            waypoints.append(
                f"{line.latitude},{line.longitude}"
            )

        origin = f"{self.origin_latitude},{self.origin_longitude}"

        # Google Maps Directions:
        # Origen -> pedidos en sequence -> regreso al origen
        params = [
            "api=1",
            f"origin={origin}",
            f"destination={origin}",
            f"waypoints={'|'.join(waypoints)}",
            "travelmode=driving",
        ]

        self.whatsapp_link = (
            "https://www.google.com/maps/dir/?"
            + "&".join(params)
        )

        return True




    