# Copyright 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
{
    "name": "SFTP Server",
    "summary": "Base implementation for SFTP Server",
    "version": "14.0.1.0.0",
    "category": "Localisation",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "views/sftp_server_view.xml",
        "security/sftp_server_security.xml",
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {
        "python": [
            "paramiko",
        ]
    },
}
