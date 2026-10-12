from odoo import api, fields, models


class RoutePlannerLine(models.Model):
    _name = "route.planner.line"
    _description = "Route Planner Line"
    _order = "sequence, id"

    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    route_id = fields.Many2one(
        "route.planner",
        string="Route",
        required=True,
        ondelete="cascade",
    )

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Orden de venta",
        required=True,
    )

    display_order_name = fields.Char(
        string="Orden de venta (para mostrar)",
        readonly=True,
    )

    partner_id = fields.Many2one(
        related="sale_order_id.partner_id",
        string="Cliente",
        store=True,
        readonly=True,
    )

    state = fields.Selection(
        related="sale_order_id.state",
        string="Estado de la Orden",
        store=True,
        readonly=True,
    )

    latitude = fields.Char(
        string="Latitude",
    )

    longitude = fields.Char(
        string="Longitude",
    )


    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            sale_order_id = vals.get("sale_order_id")

            if sale_order_id:

                sale_order = self.env["sale.order"].browse(sale_order_id)

                partner = sale_order.partner_id

                vals["display_order_name"] = sale_order.name

                vals["latitude"] = partner.route_latitude
                vals["longitude"] = partner.route_longitude

        return super().create(vals_list)