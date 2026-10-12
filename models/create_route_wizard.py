from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreateRouteWizard(models.TransientModel):
    _name = "route.planner.create.wizard"
    _description = "Create Route Wizard"

    name = fields.Char(
        string="Route Name",
        readonly=True,
        default="Automatic",
    )

    order_count = fields.Integer(
        string="Orders",
        compute="_compute_order_count",
    )

    @api.depends_context("active_ids")
    def _compute_order_count(self):
        active_ids = self.env.context.get("active_ids", [])

        for wizard in self:
            wizard.order_count = len(active_ids)

    def action_create_route(self):

        sale_orders = self.env["sale.order"].browse(
            self.env.context.get("active_ids", [])
        )

        for order in sale_orders:
            partner = order.partner_id

            if not partner.route_latitude or not partner.route_longitude:
                raise UserError(_(
                    "The customer '%s' does not have coordinates configured.\n\n"
                    "Please capture the customer's location before creating the route."
                ) % partner.display_name)

        route = self.env["route.planner"].create({})

        for order in sale_orders:

            self.env["route.planner.line"].create({
                "route_id": route.id,
                "sale_order_id": order.id,
            })

        return {
            "type": "ir.actions.act_window",
            "res_model": "route.planner",
            "res_id": route.id,
            "view_mode": "form",
        }