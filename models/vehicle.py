from odoo import fields, models


class RouteVehicle(models.Model):
    _name = "route.vehicle"
    _description = "Vehicle"
    _order = "id desc"


    name = fields.Char(
        string="Name",
        required=True,
    )

    plate = fields.Char(
        string="License Plate",
        required=True,
    )


    vehicle_type = fields.Selection(
        [
            ("motorcycle", "Motorcycle"),
            ("car", "Car"),
            ("pickup", "Pickup Truck"),
            ("truck", "Truck"),
            ("torton", "Torton"),
            ("trailer", "Trailer"),
            ("drone", "Drone"),
            ("helicopter", "Helicopter"),
            ("airplane", "Airplane"),
        ],
        string="Vehicle Type",
        required=True,
    )


    photo = fields.Image(
        string="Photo",
    )


    capacity_kg = fields.Float(
        string="Capacity (kg)",
    )