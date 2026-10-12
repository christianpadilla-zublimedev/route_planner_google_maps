from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    google_maps_api_key = fields.Char(
        string="Google Maps API Key",
        config_parameter="route_planner.google_maps_api_key",
    )

    google_maps_routes_api_key = fields.Char(
        string="Google Maps Routes API Key",
        config_parameter="route_planner.google_maps_routes_api_key",
    )

    google_maps_geocoding_api_key = fields.Char(
        string="Google Maps Geocoding API Key",
        config_parameter="route_planner.google_maps_geocoding_api_key",
    )