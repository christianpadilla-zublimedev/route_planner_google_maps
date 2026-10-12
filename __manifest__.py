{
    "name": "Route Planner",
    "summary": "Delivery Route Planner",
    "description": """
Route planner for Sale Orders
""",
    "version": "19.0.1.0.0",
    "author": "Ing. Christian Padilla",
    "maintainer": "Ing. Christian Padilla",
    "license": "LGPL-3",
    "category": "Inventory",
    "depends": [
        "sale_management",
        "stock",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        'views/res_config_settings_views.xml',
        "data/route_sequence.xml",
        'views/res_partner_views.xml',
        "views/vehicle_views.xml",
        "views/route_planner_reports.xml",
        "views/route_planner_views.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",
        "views/create_route_wizard_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "route_planner/static/lib/leaflet/leaflet.css",
            "route_planner/static/lib/leaflet/leaflet.js",
            'route_planner/static/src/js/google_maps.js',
            "route_planner/static/src/js/route_map_widget.js",
            "route_planner/static/src/xml/route_map_widget.xml",
            "route_planner/static/src/xml/google_maps.xml",
            "route_planner/static/src/css/route_map_widget.css",
        ],
    },
    "installable": True,
    "application": True,
}