from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    route_latitude = fields.Char(
        string="Latitude",
        help="Latitude used by Route Planner.",
    )

    route_longitude = fields.Char(
        string="Longitude",
        help="Longitude used by Route Planner.",
    )