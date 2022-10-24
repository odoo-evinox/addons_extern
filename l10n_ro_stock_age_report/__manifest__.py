# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Romania - Stock Aged Report",
    "version": "14.0.1.0.0",
    "category": "Localization",
    "summary": "Romania - Stock Aged Report",
    "author": "NextERP Romania," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-romania",
    "depends": ["l10n_ro_stock_account"],
    "license": "AGPL-3",
    "data": [
        "wizard/stock_age_report.xml",
        "security/ir.model.access.csv",        
    ],
    "installable": True,
    "maintainers": ["feketemihai", "mcojocaru"],
}
