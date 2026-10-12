from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    route_latitude = fields.Char(
        string="Latitud",
        help="Latitude used by Route Planner.",
    )

    route_longitude = fields.Char(
        string="Longitud",
        help="Longitude used by Route Planner.",
    )