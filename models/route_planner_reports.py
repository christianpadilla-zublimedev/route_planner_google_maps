# -*- coding: utf-8 -*-

from odoo import fields, models


class RoutePlannerReport(models.Model):
    _name = "route.planner.report"
    _description = "Reporte Financiero de Rutas"
    _auto = False
    _rec_name = "route_id"
    _order = "route_date desc, route_id desc"

    route_id = fields.Many2one(
        "route.planner",
        string="Ruta",
        readonly=True,
    )

    route_date = fields.Date(
        string="Fecha",
        readonly=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Entregado por",
        readonly=True,
    )

    vehicle_id = fields.Many2one(
        "route.vehicle",
        string="Vehículo",
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        readonly=True,
    )

    order_count = fields.Integer(
        string="Cantidad de pedidos",
        readonly=True,
    )

    shipment_total = fields.Monetary(
        string="Total del embarque",
        currency_field="currency_id",
        readonly=True,
    )

    fuel_expense = fields.Monetary(
        string="Costo de combustible",
        currency_field="currency_id",
        readonly=True,
    )

    fuel_percentage = fields.Float(
        string="Impacto de combustible (%)",
        readonly=True,
    )

    notes = fields.Text(
        string="Nota",
        readonly=True,
    )

    route_distance_km = fields.Float(
        string="Distancia (km)",
        readonly=True,
    )

    route_duration_hours = fields.Float(
        string="Duración (horas)",
        readonly=True,
    )

    @property
    def _table_query(self):
        return """
            SELECT
                r.id AS id,

                r.id AS route_id,
                r.route_date AS route_date,
                r.user_id AS user_id,
                r.vehicle_id AS vehicle_id,
                r.company_id AS company_id,

                c.currency_id AS currency_id,

                COUNT(DISTINCT l.id) AS order_count,

                COALESCE(
                    SUM(so.amount_total),
                    0.0
                ) AS shipment_total,

                COALESCE(
                    r.fuel_expense,
                    0.0
                ) AS fuel_expense,

                CASE
                    WHEN COALESCE(SUM(so.amount_total), 0.0) > 0
                    THEN (
                        COALESCE(r.fuel_expense, 0.0)
                        / SUM(so.amount_total)
                    ) * 100.0
                    ELSE 0.0
                END AS fuel_percentage,

                r.notes AS notes,

                r.route_distance_km AS route_distance_km,

                r.route_duration_hours AS route_duration_hours

            FROM route_planner r

            LEFT JOIN route_planner_line l
                ON l.route_id = r.id

            LEFT JOIN sale_order so
                ON so.id = l.sale_order_id

            LEFT JOIN res_company c
                ON c.id = r.company_id

            WHERE r.state = 'done'

            GROUP BY
                r.id,
                r.route_date,
                r.user_id,
                r.vehicle_id,
                r.company_id,
                c.currency_id,
                r.fuel_expense,
                r.notes,
                r.route_distance_km,
                r.route_duration_hours
        """