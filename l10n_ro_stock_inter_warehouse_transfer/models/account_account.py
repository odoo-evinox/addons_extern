# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class Account(models.Model):
    _name = "account.account"
    _inherit = ["account.account", "l10n.ro.mixin", "search.parent.mixin"]
