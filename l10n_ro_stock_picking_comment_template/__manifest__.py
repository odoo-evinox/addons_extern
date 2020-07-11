# Copyright 2020 NextERP Romania SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Romania - Stock Picking Comment Template",
    "category": "Localization",
    "depends": ["stock", 
                "purchase_stock", 
                "stock_picking_comment_template",
                "l10n_ro_stock_account", # normaly is not neccesary, but without it is giving error at stock_location_view.xml import  
                ],
    "data": ["data/l10n_ro_stock_picking_comment_template.xml",
             "views/stock_location_view.xml",
             "views/stock_picking_view.xml",
             ],
    "license": "AGPL-3",
    "version": "13.0.1.0.0",
    "author": "NextERP Romania," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-romania",
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
}
