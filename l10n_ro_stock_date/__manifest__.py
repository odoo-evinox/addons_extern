# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "Stock Processing Date",
    "version": "14.0.1.2.0",
    "depends": ["nexterp_stock_date", "stock_account"],
    "description": """Stock Accounting Date""",
    "data": [
        "views/stock_picking_views.xml",
     ],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "contact@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "OPL-1",
}
