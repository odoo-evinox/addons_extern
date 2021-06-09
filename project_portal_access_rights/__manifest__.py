# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Projects Portal Access Rights",
    "summary": "Add portal access rights to all project types",
    "version": "14.0.1.0.0",
    "development_status": "Mature",
    "category": "Security",
    "website": "https://nexterp.ro",
    "author": "NextERP Romania SRL",
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "depends": [
        "project",
    ],
}
