from odoo import http
from odoo.http import request


class RoutePlannerController(http.Controller):

    @http.route(
        "/route_planner/google_maps_api_key",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def google_maps_api_key(self):
        api_key = request.env["ir.config_parameter"].sudo().get_param(
            "route_planner.google_maps_api_key",
            default="",
        )

        return request.make_json_response({
            "api_key": api_key,
        })
