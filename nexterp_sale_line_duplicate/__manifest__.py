# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
{
    "name": "Sale Order Line Duplicate",
    "summary": "Sale Order Line Duplicate",
    "version": "14.0.1.0.0",
    "category": "Sale",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
    ],
    "data": [
        "views/sale_view.xml",
        "wizard/sale_line_duplicate_view.xml",
        "security/ir.model.access.csv",
    ],
}
