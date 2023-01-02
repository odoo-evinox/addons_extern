# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax", "l10n.ro.mixin", "search.parent.mixin"]
