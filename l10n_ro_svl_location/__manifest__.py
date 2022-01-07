# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "Stock Valuation Layer Location",
    "version": "14.0.1.0.1",
    "depends": ["l10n_ro_stock_account"],
    "description": """Stock Valuation Layer computations based on location""",
    "data": [
        "views/stock_valuation_layer_views.xml",
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
