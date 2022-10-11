# Copyright 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
{
    "name": "Base CSV Export",
    "summary": "Base implementation for CSV Export",
    "version": "14.0.1.0.0",
    "category": "Base",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    # "external_dependencies": {
    #    "python": [
    #        "unicodecsv",
    #    ]
    # },
}
