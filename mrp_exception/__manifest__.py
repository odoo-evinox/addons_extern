# Copyright 2011 Akretion, Sodexis
# Copyright 2018 Akretion
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Mrp Exception",
    "summary": "Custom exceptions on mrp production",
    "version": "14.0.1.0.1",
    "category": "Generic Modules/Mrp",
    "author": "Akretion, "
    "Sodexis, "
    "Camptocamp, "
    "Odoo Community Association (OCA)",
    "depends": ["mrp", "nexterp_stock_exception"],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "wizard/mrp_exception_confirm_view.xml",
        "views/mrp_view.xml",
    ],
}
